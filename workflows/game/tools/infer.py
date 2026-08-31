"""GAME 主唱 MIDI worker。stdout 仅 JSONL。"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from protocol import emit, fail, load_request, require_file  # noqa: E402


def _count_notes(midi_path: Path) -> int:
    try:
        import pretty_midi

        midi = pretty_midi.PrettyMIDI(str(midi_path))
        return sum(len(inst.notes) for inst in midi.instruments)
    except Exception:
        return -1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    request = load_request(args.request)
    emit(request, "started", {"workflow": "game"})

    audio = Path(request["inputs"]["audio"])
    midi_out = Path(request["outputs"]["midi"])
    require_file(audio, request, what="lead 音频")
    params = request.get("params") or {}
    checkpoint = Path(params.get("checkpoint") or "")
    vendor = Path(params.get("vendor") or os.environ.get("POLYSCRIBE_VENDOR", "") ) / "game"
    if params.get("vendor"):
        vendor = Path(params["vendor"])
    language = params.get("language") or "zh"
    infer_py = vendor / "infer.py"
    if not infer_py.is_file():
        fail(request, f"GAME vendor 缺少 infer.py: {infer_py}")
    if not checkpoint.is_file():
        fail(request, f"GAME checkpoint 不存在: {checkpoint}")

    work = Path(request["work_dir"])
    work.mkdir(parents=True, exist_ok=True)
    emit(request, "progress", {"message": "GAME extract", "language": language})
    command = [
        sys.executable,
        str(infer_py),
        "extract",
        str(audio),
        "-m",
        str(checkpoint),
        "-l",
        str(language),
        "--output-formats",
        "mid",
        "--output-dir",
        str(work),
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(vendor), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        command,
        cwd=str(vendor),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    if completed.returncode != 0:
        fail(
            request,
            f"GAME 退出码 {completed.returncode}: {(completed.stderr or completed.stdout)[-2000:]}",
        )

    produced = work / f"{audio.stem}.mid"
    if not produced.is_file():
        mids = list(work.glob("*.mid"))
        if len(mids) == 1:
            produced = mids[0]
        elif not mids:
            fail(request, "GAME 未生成 MIDI")
        else:
            produced = max(mids, key=lambda p: p.stat().st_mtime)
    midi_out.parent.mkdir(parents=True, exist_ok=True)
    if produced.resolve() != midi_out.resolve():
        shutil.copy2(produced, midi_out)
    require_file(midi_out, request, what="GAME MIDI")
    emit(
        request,
        "succeeded",
        {
            "midi": str(midi_out),
            "language": language,
            "note_count": _count_notes(midi_out),
            "vendor_commit": _vendor_commit(vendor),
        },
    )


def _vendor_commit(vendor: Path) -> str | None:
    marker = vendor / "POLYSCRIBE_VENDOR.json"
    if marker.is_file():
        import json

        try:
            return json.loads(marker.read_text(encoding="utf-8")).get("commit")
        except json.JSONDecodeError:
            return None
    return None


if __name__ == "__main__":
    main()
