"""请求 JSON 构造。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from polyscribe_core.constants import SCHEMA_VERSION
from polyscribe_core.io import write_json
from polyscribe_core.schema import validate_document


def write_request(
    dest: Path,
    *,
    job_id: str,
    stage_id: str,
    workflow: str,
    params: dict[str, Any],
    inputs: dict[str, str],
    outputs: dict[str, str],
    work_dir: Path,
) -> dict[str, Any]:
    document = {
        "schema_version": SCHEMA_VERSION,
        "job_id": job_id,
        "stage_id": stage_id,
        "workflow": workflow,
        "params": params,
        "inputs": inputs,
        "outputs": outputs,
        "work_dir": str(work_dir.resolve()),
    }
    validate_document("request", document)
    write_json(dest, document)
    return document
