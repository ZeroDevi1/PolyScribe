"""路径解析：CLI 参数 > 环境变量 > 仓库默认值。"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ENV_ROOT = "POLYSCRIBE_ROOT"
ENV_JOBS = "POLYSCRIBE_JOBS"
ENV_VENDOR = "POLYSCRIBE_VENDOR"
ENV_ASSETS = "POLYSCRIBE_ASSETS"


def _this_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


@dataclass(frozen=True)
class Layout:
    root: Path
    jobs: Path
    vendor: Path
    assets: Path
    contracts: Path
    workflows: Path
    resources: Path

    @property
    def schemas(self) -> Path:
        return self.contracts / "schemas"

    def workflow_dir(self, name: str) -> Path:
        return self.workflows / name

    def workflow_venv_python(self, name: str) -> Path:
        base = self.workflow_dir(name) / ".venv"
        windows = base / "Scripts" / "python.exe"
        if windows.exists() or os.name == "nt":
            return windows
        return base / "bin" / "python"

    def workflow_infer(self, name: str) -> Path:
        return self.workflow_dir(name) / "tools" / "infer.py"


def resolve_layout(
    *,
    root: str | Path | None = None,
    jobs: str | Path | None = None,
    vendor: str | Path | None = None,
    assets: str | Path | None = None,
) -> Layout:
    resolved_root = normalize_path(root or os.environ.get(ENV_ROOT) or _this_repo_root())
    return Layout(
        root=resolved_root,
        jobs=normalize_path(jobs or os.environ.get(ENV_JOBS) or (resolved_root / "jobs")),
        vendor=normalize_path(
            vendor or os.environ.get(ENV_VENDOR) or (resolved_root / "vendor")
        ),
        assets=normalize_path(
            assets or os.environ.get(ENV_ASSETS) or (resolved_root / "assets")
        ),
        contracts=resolved_root / "contracts",
        workflows=resolved_root / "workflows",
        resources=resolved_root / "resources",
    )
