"""Workflow worker 共用的 JSONL 协议（不依赖 polyscribe_core）。"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"


def load_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def emit(request: dict[str, Any], event_type: str, payload: dict[str, Any] | None = None) -> None:
    event = {
        "schema_version": SCHEMA_VERSION,
        "job_id": request["job_id"],
        "stage_id": request["stage_id"],
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "payload": payload or {},
    }
    sys.stdout.write(json.dumps(event, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def fail(request: dict[str, Any], message: str, *, error_type: str = "worker_error") -> None:
    emit(request, "failed", {"error_type": error_type, "message": message})
    print(message, file=sys.stderr)
    raise SystemExit(1)


def require_file(path: Path, request: dict[str, Any], *, what: str) -> None:
    if not path.is_file() or path.stat().st_size <= 0:
        fail(request, f"{what} 无效或不存在: {path}", error_type="artifact_error")
