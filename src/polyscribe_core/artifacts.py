"""产物记录辅助。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from polyscribe_core.errors import ArtifactError
from polyscribe_core.io import sha256_file


def require_nonempty_file(path: Path, *, allow_empty: bool = False) -> None:
    if not path.is_file():
        raise ArtifactError(f"产物不存在: {path}")
    if not allow_empty and path.stat().st_size <= 0:
        raise ArtifactError(f"产物为空文件（禁止假成功）: {path}")


def artifact_record(
    *,
    artifact_id: str,
    kind: str,
    role: str,
    path: Path,
    producer_stage: str,
    metadata: dict[str, Any] | None = None,
    confidence: float | None = None,
    allow_empty: bool = False,
) -> dict[str, Any]:
    require_nonempty_file(path, allow_empty=allow_empty)
    return {
        "id": artifact_id,
        "kind": kind,
        "role": role,
        "path": str(path.resolve()),
        "sha256": sha256_file(path) if path.stat().st_size else None,
        "producer_stage": producer_stage,
        "confidence": confidence,
        "metadata": metadata or {},
    }
