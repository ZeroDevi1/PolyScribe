"""第一版串行 GPU 编排：normalize → muscriptor → separation → GAME → Basic Pitch。"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from polyscribe_cli.bootstrap import find_game_checkpoint
from polyscribe_core.artifacts import artifact_record
from polyscribe_core.audio import normalize_wav, probe_duration_seconds
from polyscribe_core.chords import export_chords_from_midi
from polyscribe_core.constants import (
    DEFAULT_CHANNELS,
    DEFAULT_SAMPLE_RATE,
    GAME_LANGUAGE,
    KARAOKE_SEP_MODEL,
    MUSCRIPTOR_MODEL,
    VOCAL_SEP_MODEL,
)
from polyscribe_core.env import nvidia_gpu_name
from polyscribe_core.errors import ArtifactError, PianoTrackNotFoundError, PolyscribeError, WorkerError
from polyscribe_core.events import EventLog, make_event
from polyscribe_core.io import sha256_file
from polyscribe_core.job import Job, add_artifact, add_warning, create_job, set_status, upsert_stage
from polyscribe_core.midi_piano import extract_piano_midi
from polyscribe_core.paths import Layout, normalize_path
from polyscribe_core.request import write_request
from polyscribe_core.runner import run_workflow_infer, tee_stderr, write_log
from polyscribe_core.timeutil import utc_now


def process_audio(
    layout: Layout,
    audio: Path,
    *,
    targets: list[str],
    job_id: str | None = None,
) -> Job:
    source = normalize_path(audio)
    duration = probe_duration_seconds(source)
    job = create_job(
        layout,
        source,
        job_id=job_id,
        duration_seconds=duration,
        gpu=nvidia_gpu_name(),
    )
    events = EventLog(job.events_path)
    manifest = job.load_manifest()
    set_status(manifest, "running")
    job.save_manifest(manifest)
    wanted = set(targets)
    try:
        wav = _stage_normalize(job, events, source)
        if wanted & {"piano", "chords"}:
            full_midi = _stage_muscriptor(job, events, wav)
            if "chords" in wanted:
                _export_chords(job, events, full_midi, duration)
            if "piano" in wanted:
                _export_piano(job, events, wav, full_midi)
        if wanted & {"vocal", "harmony"}:
            stems = _stage_separation(job, events, wav)
            if "vocal" in wanted:
                _stage_game(job, events, layout, Path(stems["lead"]))
            if "harmony" in wanted:
                _stage_basic_pitch(job, events, Path(stems["backing"]))
        manifest = job.load_manifest()
        set_status(manifest, "succeeded")
        job.save_manifest(manifest)
        events.append(make_event(job_id=job.job_id, stage_id="export", event_type="succeeded", payload={}))
        sys.stderr.write(f"job succeeded: {job.root}\n")
        return job
    except PolyscribeError as exc:
        _fail_job(job, events, exc)
        raise SystemExit(1) from exc
    except Exception as exc:
        wrapped = WorkerError(str(exc))
        _fail_job(job, events, wrapped)
        raise SystemExit(1) from exc


def _fail_job(job: Job, events: EventLog, exc: PolyscribeError) -> None:
    manifest = job.load_manifest()
    set_status(manifest, "failed")
    add_warning(manifest, exc.message)
    job.save_manifest(manifest)
    events.append(
        make_event(
            job_id=job.job_id,
            stage_id="process",
            event_type="failed",
            payload={"error_type": exc.error_type, "message": exc.message, "details": exc.details},
        )
    )
    sys.stderr.write(f"job failed: {exc.message}\n")


def _begin_stage(job: Job, stage_id: str, workflow: str | None, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "workflow": workflow,
        "status": "running",
        "started_at": utc_now(),
        "finished_at": None,
        "duration_seconds": None,
        "params": params,
        "vendor_commit": None,
        "package_version": None,
        "weight_sha256": None,
        "input_artifact_ids": [],
        "output_artifact_ids": [],
        "exit_code": None,
        "error_type": None,
        "log_path": str(job.log_file(stage_id).resolve()),
        "peak_vram_mb": None,
        "peak_memory_mb": None,
        "cache_key": None,
        "cache_hit": False,
    }


def _finish_stage(stage: dict[str, Any], *, started: float, exit_code: int, status: str) -> None:
    stage["finished_at"] = utc_now()
    stage["duration_seconds"] = round(time.perf_counter() - started, 3)
    stage["exit_code"] = exit_code
    stage["status"] = status


def _run_worker(
    job: Job,
    events: EventLog,
    *,
    stage_id: str,
    workflow: str,
    params: dict[str, Any],
    inputs: dict[str, str],
    outputs: dict[str, str],
    work_dir: Path,
) -> dict[str, Any]:
    request_path = job.request_file(stage_id)
    write_request(
        request_path,
        job_id=job.job_id,
        stage_id=stage_id,
        workflow=workflow,
        params=params,
        inputs=inputs,
        outputs=outputs,
        work_dir=work_dir,
    )
    stage = _begin_stage(job, stage_id, workflow, params)
    events.append(make_event(job_id=job.job_id, stage_id=stage_id, event_type="started", payload={"workflow": workflow}))
    started = time.perf_counter()
    result = run_workflow_infer(job.layout, workflow, request_path)
    write_log(job.log_file(stage_id), result)
    tee_stderr(result.stderr)
    worker_events = events.extend_jsonl(result.stdout)
    if result.returncode != 0:
        _finish_stage(stage, started=started, exit_code=result.returncode, status="failed")
        stage["error_type"] = "worker_nonzero_exit"
        manifest = job.load_manifest()
        upsert_stage(manifest, stage)
        job.save_manifest(manifest)
        raise WorkerError(
            f"{workflow}/{stage_id} 退出码 {result.returncode}",
            details={"log": str(job.log_file(stage_id)), "stderr_tail": result.stderr[-2000:]},
        )
    payload = _last_payload(worker_events, "succeeded")
    _finish_stage(stage, started=started, exit_code=0, status="succeeded")
    if payload.get("package_version"):
        stage["package_version"] = payload["package_version"]
    if payload.get("weight_sha256"):
        stage["weight_sha256"] = payload["weight_sha256"]
    if payload.get("vendor_commit"):
        stage["vendor_commit"] = payload["vendor_commit"]
    manifest = job.load_manifest()
    upsert_stage(manifest, stage)
    job.save_manifest(manifest)
    return payload


def _last_payload(events: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
    for event in reversed(events):
        if event.get("event_type") == event_type:
            payload = event.get("payload") or {}
            if isinstance(payload, dict):
                return payload
    return {}


def _stage_normalize(job: Job, events: EventLog, source: Path) -> Path:
    dest = job.stage_dir("normalize") / "audio.wav"
    stage = _begin_stage(
        job,
        "normalize",
        None,
        {"sample_rate": DEFAULT_SAMPLE_RATE, "channels": DEFAULT_CHANNELS},
    )
    events.append(make_event(job_id=job.job_id, stage_id="normalize", event_type="started", payload={}))
    started = time.perf_counter()
    normalize_wav(source, dest)
    _finish_stage(stage, started=started, exit_code=0, status="succeeded")
    record = artifact_record(
        artifact_id="normalized-wav",
        kind="audio",
        role="audio.normalized",
        path=dest,
        producer_stage="normalize",
        metadata={"sample_rate": DEFAULT_SAMPLE_RATE, "channels": DEFAULT_CHANNELS},
        confidence=None,
    )
    stage["output_artifact_ids"] = [record["id"]]
    manifest = job.load_manifest()
    upsert_stage(manifest, stage)
    add_artifact(manifest, record)
    job.save_manifest(manifest)
    return dest


def _stage_muscriptor(
    job: Job,
    events: EventLog,
    wav: Path,
    *,
    instruments: str | None = None,
    output_name: str = "full.mid",
    stage_id: str = "muscriptor",
) -> Path:
    work = job.stage_dir("transcription")
    midi_path = work / output_name
    params: dict[str, Any] = {"model": MUSCRIPTOR_MODEL}
    if instruments:
        params["instruments"] = instruments
    payload = _run_worker(
        job,
        events,
        stage_id=stage_id,
        workflow="muscriptor",
        params=params,
        inputs={"audio": str(wav)},
        outputs={"midi": str(midi_path)},
        work_dir=work,
    )
    if not midi_path.is_file() or midi_path.stat().st_size <= 0:
        raise ArtifactError("MuScriptor 未写出非空 MIDI")
    artifact_id = "muscriptor-piano-conditioned" if instruments else "muscriptor-full-midi"
    role = "transcription.piano_conditioned" if instruments else "transcription.full"
    record = artifact_record(
        artifact_id=artifact_id,
        kind="midi",
        role=role,
        path=midi_path,
        producer_stage=stage_id,
        metadata={
            "model": MUSCRIPTOR_MODEL,
            "instruments": instruments,
            "package_version": payload.get("package_version"),
        },
        confidence=None,
    )
    manifest = job.load_manifest()
    add_artifact(manifest, record)
    job.save_manifest(manifest)
    return midi_path


def _export_piano(job: Job, events: EventLog, wav: Path, full_midi: Path) -> None:
    dest = job.output_dir("instruments") / "piano.mid"
    stage = _begin_stage(job, "piano_extract", None, {"source": "muscriptor-full-midi"})
    started = time.perf_counter()
    events.append(make_event(job_id=job.job_id, stage_id="piano_extract", event_type="started", payload={}))
    source = full_midi
    conditioned = False
    try:
        stats = extract_piano_midi(source, dest)
    except PianoTrackNotFoundError:
        events.append(
            make_event(
                job_id=job.job_id,
                stage_id="piano_extract",
                event_type="warning",
                payload={"message": "完整混音无钢琴轨，改用 --instruments acoustic_piano 再转录"},
            )
        )
        source = _stage_muscriptor(
            job,
            events,
            wav,
            instruments="acoustic_piano",
            output_name="piano_conditioned.mid",
            stage_id="muscriptor_piano",
        )
        conditioned = True
        stats = extract_piano_midi(source, dest)
    _finish_stage(stage, started=started, exit_code=0, status="succeeded")
    record = artifact_record(
        artifact_id="piano-midi-primary",
        kind="midi",
        role="instrument.piano.primary",
        path=dest,
        producer_stage="piano_extract",
        metadata={
            "model": MUSCRIPTOR_MODEL,
            "instrument": "acoustic_piano",
            "conditioned": conditioned,
            **stats,
        },
        confidence=None,
    )
    stage["output_artifact_ids"] = [record["id"]]
    manifest = job.load_manifest()
    upsert_stage(manifest, stage)
    add_artifact(manifest, record)
    if conditioned:
        add_warning(
            manifest,
            "完整混音未检出钢琴轨；piano.mid 来自 MuScriptor instrument-conditioned acoustic_piano，没有用吉他等其他乐器顶替",
            stage_id="piano_extract",
        )
    job.save_manifest(manifest)


def _export_chords(job: Job, events: EventLog, full_midi: Path, duration: float) -> None:
    json_path = job.output_dir("harmony") / "chords.json"
    midi_path = job.output_dir("harmony") / "chords.mid"
    stage_dir = job.stage_dir("chord")
    stage = _begin_stage(job, "chord_export", "chord", {"source": "muscriptor-full-midi"})
    started = time.perf_counter()
    events.append(make_event(job_id=job.job_id, stage_id="chord_export", event_type="started", payload={}))
    document, warnings = export_chords_from_midi(
        full_midi,
        json_path,
        midi_path,
        end_time=duration,
    )
    # 无 marker 视为失败：不能用空时间线冒充成功
    if not document["segments"]:
        _finish_stage(stage, started=started, exit_code=1, status="failed")
        stage["error_type"] = "chord_markers_missing"
        manifest = job.load_manifest()
        upsert_stage(manifest, stage)
        for item in warnings:
            add_warning(manifest, item, stage_id="chord_export")
        job.save_manifest(manifest)
        raise ArtifactError("无法生成和弦时间线")
    _finish_stage(stage, started=started, exit_code=0, status="succeeded")
    json_art = artifact_record(
        artifact_id="chords-json",
        kind="json",
        role="harmony.chords.timeline",
        path=json_path,
        producer_stage="chord_export",
        metadata={"producer": document.get("producer"), "segments": len(document["segments"])},
        confidence=None,
    )
    midi_art = artifact_record(
        artifact_id="chords-midi",
        kind="midi",
        role="harmony.chords.midi",
        path=midi_path,
        producer_stage="chord_export",
        metadata={"producer": document.get("producer")},
        confidence=None,
    )
    stage["output_artifact_ids"] = [json_art["id"], midi_art["id"]]
    manifest = job.load_manifest()
    upsert_stage(manifest, stage)
    add_artifact(manifest, json_art)
    add_artifact(manifest, midi_art)
    for item in warnings:
        add_warning(manifest, item, stage_id="chord_export")
    # 保留一份到 stages/chord
    (stage_dir / "chords.json").write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
    job.save_manifest(manifest)


def _stage_separation(job: Job, events: EventLog, wav: Path) -> dict[str, str]:
    work = job.stage_dir("separation")
    vocals = work / "vocals.wav"
    instrumental = work / "instrumental.wav"
    lead = work / "lead.wav"
    backing = work / "backing.wav"
    payload = _run_worker(
        job,
        events,
        stage_id="separation",
        workflow="separation",
        params={
            "vocal_model": VOCAL_SEP_MODEL,
            "karaoke_model": KARAOKE_SEP_MODEL,
        },
        inputs={"audio": str(wav)},
        outputs={
            "vocals": str(vocals),
            "instrumental": str(instrumental),
            "lead": str(lead),
            "backing": str(backing),
        },
        work_dir=work,
    )
    for path in (vocals, lead, backing):
        if not path.is_file() or path.stat().st_size <= 0:
            raise ArtifactError(f"分离产物无效: {path}")
    manifest = job.load_manifest()
    for artifact_id, role, path in (
        ("vocals-wav", "audio.vocals", vocals),
        ("instrumental-wav", "audio.instrumental", instrumental),
        ("lead-wav", "audio.lead_vocal", lead),
        ("backing-wav", "audio.backing_vocal", backing),
    ):
        if path.is_file() and path.stat().st_size > 0:
            add_artifact(
                manifest,
                artifact_record(
                    artifact_id=artifact_id,
                    kind="audio",
                    role=role,
                    path=path,
                    producer_stage="separation",
                    metadata={"vocal_model": VOCAL_SEP_MODEL, "karaoke_model": KARAOKE_SEP_MODEL},
                    confidence=None,
                ),
            )
    job.save_manifest(manifest)
    return {
        "vocals": str(vocals),
        "instrumental": str(instrumental),
        "lead": str(lead),
        "backing": str(backing),
        **{k: str(v) for k, v in payload.items() if isinstance(v, str)},
    }


def _stage_game(job: Job, events: EventLog, layout: Layout, lead: Path) -> None:
    checkpoint = find_game_checkpoint(layout)
    if checkpoint is None:
        raise WorkerError("未找到 GAME Medium 权重，请先 bootstrap")
    work = job.stage_dir("vocal")
    raw_midi = work / "game.mid"
    dest = job.output_dir("vocals") / "vocal.mid"
    payload = _run_worker(
        job,
        events,
        stage_id="game",
        workflow="game",
        params={
            "language": GAME_LANGUAGE,
            "checkpoint": str(checkpoint),
            "vendor": str(layout.vendor / "game"),
        },
        inputs={"audio": str(lead)},
        outputs={"midi": str(raw_midi)},
        work_dir=work,
    )
    if not raw_midi.is_file() or raw_midi.stat().st_size <= 0:
        raise ArtifactError("GAME 未写出非空 MIDI")
    dest.write_bytes(raw_midi.read_bytes())
    record = artifact_record(
        artifact_id="vocal-midi",
        kind="midi",
        role="vocals.lead",
        path=dest,
        producer_stage="game",
        metadata={
            "model": "GAME-1.0-medium",
            "language": GAME_LANGUAGE,
            "checkpoint_sha256": sha256_file(checkpoint),
            "note_count": payload.get("note_count"),
        },
        confidence=None,
    )
    manifest = job.load_manifest()
    add_artifact(manifest, record)
    job.save_manifest(manifest)


def _stage_basic_pitch(job: Job, events: EventLog, backing: Path) -> None:
    work = job.stage_dir("harmony")
    raw_midi = work / "basic_pitch.mid"
    dest = job.output_dir("vocals") / "harmony.mid"
    payload = _run_worker(
        job,
        events,
        stage_id="basic_pitch",
        workflow="basic_pitch",
        params={},
        inputs={"audio": str(backing)},
        outputs={"midi": str(raw_midi)},
        work_dir=work,
    )
    if not raw_midi.is_file() or raw_midi.stat().st_size <= 0:
        raise ArtifactError("Basic Pitch 未写出 MIDI")
    dest.write_bytes(raw_midi.read_bytes())
    note_count = int(payload.get("note_count") or 0)
    record = artifact_record(
        artifact_id="harmony-midi",
        kind="midi",
        role="vocals.harmony.simplified",
        path=dest,
        producer_stage="basic_pitch",
        metadata={
            "model": "basic-pitch",
            "note_count": note_count,
            "simplification": "backing-stem-multipitch-no-voice-assignment",
        },
        confidence=None,
        allow_empty=False,
    )
    manifest = job.load_manifest()
    add_artifact(manifest, record)
    if note_count <= 0:
        add_warning(
            manifest,
            "Backing 几乎无音符，已写出空的 harmony.mid（简化和声路线，不做声部分配）",
            stage_id="basic_pitch",
        )
    job.save_manifest(manifest)
