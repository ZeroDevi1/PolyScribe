"""准备 vendor、隔离 uv 环境与 GAME 权重。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from polyscribe_core.constants import GAME_REPO_URL, GAME_WEIGHTS_ARCHIVE, GAME_WEIGHTS_URL
from polyscribe_core.errors import BootstrapError
from polyscribe_core.io import sha256_file, write_json
from polyscribe_core.paths import Layout

WORKFLOW_PYTHON = {
    "separation": "3.12",
    "muscriptor": "3.12",
    "game": "3.12",
    "basic_pitch": "3.10",
}


def _uv() -> str:
    path = shutil.which("uv")
    if not path:
        raise BootstrapError("未找到 uv，请先安装 https://docs.astral.sh/uv/")
    return path


def _run(command: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    completed = subprocess.run(command, cwd=cwd, env=merged)
    if completed.returncode != 0:
        raise BootstrapError(f"命令失败 ({completed.returncode}): {' '.join(command)}")


def _torch_backend_env() -> dict[str, str]:
    if os.name == "nt":
        return {"UV_TORCH_BACKEND": "cu128"}
    return {}


def _force_cuda_torch(venv_python: Path) -> None:
    """已安装的 CPU torch 会被 uv 视为满足依赖，必须先卸再装 CUDA wheel。"""
    uv = _uv()
    subprocess.run(
        [
            uv,
            "pip",
            "uninstall",
            "-y",
            "--python",
            str(venv_python),
            "torch",
            "torchvision",
            "torchaudio",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    _run(
        [
            uv,
            "pip",
            "install",
            "--python",
            str(venv_python),
            "torch",
            "torchaudio",
            "torchvision",
            "--torch-backend",
            "cu128",
        ],
        env=_torch_backend_env(),
    )


def bootstrap_workflows(layout: Layout, names: list[str]) -> None:
    layout.vendor.mkdir(parents=True, exist_ok=True)
    layout.assets.mkdir(parents=True, exist_ok=True)
    layout.jobs.mkdir(parents=True, exist_ok=True)
    if "game" in names:
        _sync_game_vendor(layout)
        _download_game_weights(layout)
    for name in names:
        _sync_workflow_env(layout, name)
    sys.stderr.write("bootstrap 完成\n")


def _sync_workflow_env(layout: Layout, name: str) -> None:
    uv = _uv()
    workflow = layout.workflow_dir(name)
    pyproject = workflow / "pyproject.toml"
    if not pyproject.is_file():
        raise BootstrapError(f"缺少 {pyproject}")
    python = WORKFLOW_PYTHON[name]
    env = _torch_backend_env() if name != "basic_pitch" else {}
    _run(
        [uv, "sync", "--python", python, "--directory", str(workflow)],
        env=env,
    )
    venv_python = layout.workflow_venv_python(name)
    if name == "game":
        requirements = layout.vendor / "game" / "requirements.txt"
        if requirements.is_file():
            _run(
                [uv, "pip", "install", "--python", str(venv_python), "-r", str(requirements)],
            )
    if name in {"muscriptor", "game", "separation"} and os.name == "nt":
        _force_cuda_torch(venv_python)


def _sync_game_vendor(layout: Layout) -> None:
    dest = layout.vendor / "game"
    git = shutil.which("git")
    if not git:
        raise BootstrapError("GAME vendor 需要 git")
    if (dest / ".git").is_dir():
        _run([git, "fetch", "--depth", "1", "origin"], cwd=dest)
        return
    if dest.exists():
        shutil.rmtree(dest)
    _run([git, "clone", "--depth", "1", GAME_REPO_URL, str(dest)])
    commit = subprocess.run(
        [git, "rev-parse", "HEAD"],
        cwd=dest,
        capture_output=True,
        text=True,
        check=False,
    )
    write_json(
        dest / "POLYSCRIBE_VENDOR.json",
        {"repo": GAME_REPO_URL, "commit": (commit.stdout or "").strip()},
    )


def _download_game_weights(layout: Layout) -> Path:
    dest_dir = layout.assets / "game"
    dest_dir.mkdir(parents=True, exist_ok=True)
    archive = dest_dir / GAME_WEIGHTS_ARCHIVE
    if not archive.is_file():
        sys.stderr.write(f"下载 {GAME_WEIGHTS_URL}\n")
        urllib.request.urlretrieve(GAME_WEIGHTS_URL, archive)
    digest = sha256_file(archive)
    write_json(dest_dir / "GAME-1.0-medium.sha256.json", {"sha256": digest, "url": GAME_WEIGHTS_URL})
    extract_dir = dest_dir / "GAME-1.0-medium"
    if not _find_game_checkpoint(extract_dir):
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(extract_dir)
    checkpoint = _find_game_checkpoint(extract_dir)
    if checkpoint is None:
        raise BootstrapError(f"GAME zip 中未找到 .pt/.ckpt: {archive}")
    return checkpoint


def find_game_checkpoint(layout: Layout) -> Path | None:
    return _find_game_checkpoint(layout.assets / "game" / "GAME-1.0-medium")


def _find_game_checkpoint(root: Path) -> Path | None:
    if not root.exists():
        return None
    candidates = list(root.rglob("*.pt")) + list(root.rglob("*.ckpt"))
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]
