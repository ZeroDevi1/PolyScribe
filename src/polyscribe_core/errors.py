"""领域错误：失败必须暴露，禁止假成功。"""

from __future__ import annotations


class PolyscribeError(Exception):
    error_type = "polyscribe_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ArtifactError(PolyscribeError):
    error_type = "artifact_error"


class PianoTrackNotFoundError(ArtifactError):
    error_type = "piano_track_not_found"


class WorkerError(PolyscribeError):
    error_type = "worker_error"


class BootstrapError(PolyscribeError):
    error_type = "bootstrap_error"


class DependencyError(PolyscribeError):
    error_type = "dependency_error"
