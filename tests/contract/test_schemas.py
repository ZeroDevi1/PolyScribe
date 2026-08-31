from __future__ import annotations

from pathlib import Path

import pytest
from jsonschema.exceptions import ValidationError

from polyscribe_core.constants import SCHEMA_VERSION
from polyscribe_core.paths import resolve_layout
from polyscribe_core.schema import validate_document


def test_event_schema_accepts_minimal_event() -> None:
    validate_document(
        "event",
        {
            "schema_version": SCHEMA_VERSION,
            "job_id": "job-1",
            "stage_id": "muscriptor",
            "event_type": "started",
            "timestamp": "2026-08-31T00:00:00Z",
            "payload": {},
        },
    )


def test_chords_schema_accepts_contract_example() -> None:
    validate_document(
        "chords",
        {
            "schema_version": SCHEMA_VERSION,
            "timebase": "seconds",
            "producer": "muscriptor-btc",
            "segments": [
                {
                    "start": 0.0,
                    "end": 4.0,
                    "label": "C:maj7",
                    "raw_label": "C:maj7",
                    "confidence": None,
                }
            ],
        },
    )


def test_event_schema_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        validate_document(
            "event",
            {
                "schema_version": SCHEMA_VERSION,
                "job_id": "job-1",
                "stage_id": "x",
                "event_type": "not-a-type",
                "timestamp": "2026-08-31T00:00:00Z",
                "payload": {},
            },
        )


def test_schema_files_exist() -> None:
    layout = resolve_layout()
    for name in ("event", "request", "artifact", "error", "chords"):
        assert (layout.schemas / f"{name}.schema.json").is_file()
