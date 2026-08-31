"""音频探测与规范化（ffmpeg/ffprobe，不引入重型音频库）。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from polyscribe_core.constants import DEFAULT_CHANNELS, DEFAULT_SAMPLE_RATE
from polyscribe_core.errors import DependencyError


def require_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        raise DependencyError("ffmpeg 未安装或不在 PATH 中")
    return path


def require_ffprobe() -> str:
    path = shutil.which("ffprobe")
    if not path:
        raise DependencyError("ffprobe 未安装或不在 PATH 中")
    return path


def probe_duration_seconds(path: Path) -> float:
    ffprobe = require_ffprobe()
    completed = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    text = completed.stdout.strip()
    if not text:
        raise DependencyError(f"ffprobe 未能读取时长: {path}")
    return float(text)


def normalize_wav(
    source: Path,
    dest: Path,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    channels: int = DEFAULT_CHANNELS,
) -> Path:
    ffmpeg = require_ffmpeg()
    dest.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-i",
        str(source),
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-c:a",
        "pcm_s16le",
        str(dest),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise DependencyError(
            "ffmpeg 规范化失败",
            details={"stderr": completed.stderr[-4000:], "exit_code": completed.returncode},
        )
    if not dest.is_file() or dest.stat().st_size <= 0:
        raise DependencyError(f"规范化输出无效: {dest}")
    return dest
