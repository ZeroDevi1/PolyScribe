"""子进程 worker：stdout 只应是 JSONL，诊断在 stderr。"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from polyscribe_core.errors import WorkerError
from polyscribe_core.paths import Layout


@dataclass
class WorkerResult:
    returncode: int
    stdout: str
    stderr: str


def workflow_python(layout: Layout, workflow: str) -> Path:
    python = layout.workflow_venv_python(workflow)
    if not python.is_file():
        raise WorkerError(
            f"workflow {workflow} 的虚拟环境不存在: {python}。请先运行 polyscribe bootstrap"
        )
    return python


def run_workflow_infer(
    layout: Layout,
    workflow: str,
    request_path: Path,
    *,
    extra_env: dict[str, str] | None = None,
    cwd: Path | None = None,
) -> WorkerResult:
    python = workflow_python(layout, workflow)
    infer = layout.workflow_infer(workflow)
    if not infer.is_file():
        raise WorkerError(f"缺少 worker 入口: {infer}")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["POLYSCRIBE_ROOT"] = str(layout.root)
    env["POLYSCRIBE_VENDOR"] = str(layout.vendor)
    env["POLYSCRIBE_ASSETS"] = str(layout.assets)
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [str(python), str(infer), "--request", str(request_path)],
        cwd=str(cwd or layout.workflow_dir(workflow)),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return WorkerResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def write_log(path: Path, result: WorkerResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    parts = [
        f"returncode={result.returncode}\n",
        "----- stdout -----\n",
        result.stdout,
        "\n----- stderr -----\n",
        result.stderr,
    ]
    path.write_text("".join(parts), encoding="utf-8")


def tee_stderr(text: str) -> None:
    if text:
        sys.stderr.write(text)
        if not text.endswith("\n"):
            sys.stderr.write("\n")
        sys.stderr.flush()
