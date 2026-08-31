"""任务目录与 manifest。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from polyscribe_core.constants import SCHEMA_VERSION
from polyscribe_core.io import read_json, sha256_file, write_json
from polyscribe_core.paths import Layout, normalize_path
from polyscribe_core.timeutil import git_commit, utc_now

STAGE_DIRS = (
    "normalize",
    "separation",
    "transcription",
    "chord",
    "vocal",
    "harmony",
    "score",
)

OUTPUT_DIRS = ("audio", "instruments", "vocals", "harmony", "score")


@dataclass
class Job:
    job_id: str
    root: Path
    layout: Layout

    @property
    def requests(self) -> Path:
        return self.root / "requests"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def stages(self) -> Path:
        return self.root / "stages"

    @property
    def output(self) -> Path:
        return self.root / "output"

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def events_path(self) -> Path:
        return self.root / "events.jsonl"

    def stage_dir(self, name: str) -> Path:
        path = self.stages / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def output_dir(self, name: str) -> Path:
        path = self.output / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def log_file(self, stage_id: str) -> Path:
        return self.logs / f"{stage_id}.log"

    def request_file(self, stage_id: str) -> Path:
        return self.requests / f"{stage_id}.json"

    def load_manifest(self) -> dict[str, Any]:
        return read_json(self.manifest_path)

    def save_manifest(self, manifest: dict[str, Any]) -> None:
        write_json(self.manifest_path, manifest)


def _ensure_job_tree(root: Path) -> None:
    for rel in ("input", "requests", "logs"):
        (root / rel).mkdir(parents=True, exist_ok=True)
    for name in STAGE_DIRS:
        (root / "stages" / name).mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_DIRS:
        (root / "output" / name).mkdir(parents=True, exist_ok=True)
    events = root / "events.jsonl"
    if not events.exists():
        events.write_text("", encoding="utf-8")


def create_job(
    layout: Layout,
    source: Path,
    *,
    job_id: str | None = None,
    mode: str = "transcribe",
    duration_seconds: float | None = None,
    gpu: str | None = None,
) -> Job:
    resolved_source = normalize_path(source)
    ident = job_id or str(uuid.uuid4())
    root = layout.jobs / ident
    _ensure_job_tree(root)
    job = Job(job_id=ident, root=root, layout=layout)
    digest = sha256_file(resolved_source)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "job_id": ident,
        "mode": mode,
        "status": "pending",
        "created_at": utc_now(),
        "input_mode": "reference",
        "input": {
            "path": str(resolved_source),
            "sha256": digest,
            "duration_seconds": duration_seconds,
        },
        "environment": {
            "os": "Windows",
            "gpu": gpu,
            "polyscribe_commit": git_commit(layout.root),
        },
        "stages": [],
        "artifacts": [],
        "warnings": [],
    }
    job.save_manifest(manifest)
    return job


def set_status(manifest: dict[str, Any], status: str) -> None:
    manifest["status"] = status


def upsert_stage(manifest: dict[str, Any], stage: dict[str, Any]) -> None:
    stages = manifest.setdefault("stages", [])
    for index, existing in enumerate(stages):
        if existing.get("stage_id") == stage["stage_id"]:
            stages[index] = stage
            return
    stages.append(stage)


def add_artifact(manifest: dict[str, Any], artifact: dict[str, Any]) -> None:
    artifacts = manifest.setdefault("artifacts", [])
    artifacts[:] = [item for item in artifacts if item.get("id") != artifact["id"]]
    artifacts.append(artifact)


def add_warning(manifest: dict[str, Any], message: str, *, stage_id: str | None = None) -> None:
    warnings = manifest.setdefault("warnings", [])
    warnings.append({"message": message, "stage_id": stage_id, "at": utc_now()})
