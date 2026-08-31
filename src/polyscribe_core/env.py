"""本机环境探测（doctor 只读）。"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def which(name: str) -> str | None:
    return shutil.which(name)


def command_ok(command: list[str]) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        return False, str(exc)
    text = (completed.stdout or completed.stderr or "").strip()
    return completed.returncode == 0, text.splitlines()[0] if text else ""


def nvidia_gpu_name() -> str | None:
    if not which("nvidia-smi"):
        return None
    ok, line = command_ok(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"]
    )
    if not ok or not line:
        return None
    return line.strip()


def huggingface_token_present() -> bool:
    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        return True
    hf_home = Path(os.environ.get("HF_HOME") or (Path.home() / ".cache" / "huggingface"))
    for name in ("token", "stored_tokens"):
        candidate = hf_home / name
        if candidate.is_file() and candidate.stat().st_size > 0:
            return True
    return False


def disk_free_gb(path: Path) -> float | None:
    try:
        path.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(path)
    except OSError:
        return None
    return usage.free / (1024**3)
