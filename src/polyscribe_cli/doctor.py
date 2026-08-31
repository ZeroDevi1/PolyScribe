"""只读诊断。"""

from __future__ import annotations

import sys

from polyscribe_cli.bootstrap import WORKFLOW_PYTHON, find_game_checkpoint
from polyscribe_core.env import disk_free_gb, huggingface_token_present, nvidia_gpu_name, which
from polyscribe_core.paths import Layout


def run_doctor(layout: Layout, workflows: list[str]) -> bool:
    ok = True

    def check(label: str, passed: bool, hint: str) -> None:
        nonlocal ok
        mark = "OK" if passed else "MISSING"
        sys.stderr.write(f"[{mark}] {label}\n")
        if not passed:
            sys.stderr.write(f"       {hint}\n")
            ok = False

    check("uv", which("uv") is not None, "安装 uv: https://docs.astral.sh/uv/")
    check("ffmpeg", which("ffmpeg") is not None, "安装 ffmpeg 并加入 PATH")
    check("ffprobe", which("ffprobe") is not None, "安装 ffmpeg（含 ffprobe）")
    gpu = nvidia_gpu_name()
    check("nvidia-smi / GPU", gpu is not None, "需要 NVIDIA 驱动；目标验证机为 RTX 5060 8GB")
    if gpu:
        sys.stderr.write(f"       GPU: {gpu}\n")
    check(
        "Hugging Face token",
        huggingface_token_present(),
        "运行 hf auth login，并在 https://huggingface.co/MuScriptor/muscriptor-medium 接受 CC BY-NC",
    )
    free = disk_free_gb(layout.assets)
    check(
        "磁盘空间 (assets)",
        free is None or free >= 8,
        f"建议至少 8GB 空闲，当前约 {free:.1f}GB" if free is not None else "无法检测磁盘",
    )

    for name in workflows:
        pyproject = layout.workflow_dir(name) / "pyproject.toml"
        check(
            f"{name} pyproject.toml",
            pyproject.is_file(),
            f"缺少 {pyproject}",
        )
        venv_python = layout.workflow_venv_python(name)
        check(
            f"{name} venv ({WORKFLOW_PYTHON[name]})",
            venv_python.is_file(),
            f"运行: uv run polyscribe bootstrap --workflows {name}",
        )

    if "game" in workflows:
        vendor = layout.vendor / "game" / "infer.py"
        check("GAME vendor", vendor.is_file(), "bootstrap 会 clone https://github.com/openvpi/GAME")
        ckpt = find_game_checkpoint(layout)
        check(
            "GAME Medium 权重",
            ckpt is not None,
            "bootstrap 会下载 GAME-1.0-medium.zip（CC BY-NC-SA 4.0）",
        )
        if ckpt:
            sys.stderr.write(f"       checkpoint: {ckpt}\n")

    sys.stderr.write("doctor 只报告问题，不会下载模型或登录 Hugging Face。\n")
    return ok
