"""Worker JSONL 事件。"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, TextIO

from polyscribe_core.constants import SCHEMA_VERSION
from polyscribe_core.timeutil import utc_now


EVENT_TYPES = frozenset(
    {"started", "progress", "artifact", "warning", "succeeded", "failed"}
)


def make_event(
    *,
    job_id: str,
    stage_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if event_type not in EVENT_TYPES:
        raise ValueError(f"unknown event_type: {event_type}")
    return {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "stage_id": stage_id,
        "event_type": event_type,
        "timestamp": utc_now(),
        "payload": payload or {},
    }


def dumps_event(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False)


class EventLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(dumps_event(event) + "\n")

    def extend_jsonl(self, text: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                print(f"skip non-JSONL stdout: {line[:200]}", file=sys.stderr)
                continue
            if not isinstance(event, dict) or "event_type" not in event:
                print(f"skip non-event stdout: {line[:200]}", file=sys.stderr)
                continue
            events.append(event)
            self.append(event)
        return events


def emit_stdout(event: dict[str, Any], stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    target.write(dumps_event(event) + "\n")
    target.flush()
