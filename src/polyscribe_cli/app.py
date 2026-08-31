"""CLI 入口。"""

from __future__ import annotations

from pathlib import Path

import typer

from polyscribe_cli.bootstrap import bootstrap_workflows
from polyscribe_cli.doctor import run_doctor
from polyscribe_cli.process import process_audio
from polyscribe_core.constants import TARGETS, WORKFLOWS
from polyscribe_core.paths import resolve_layout
from polyscribe_core.runner import run_workflow_infer, tee_stderr

app = typer.Typer(no_args_is_help=True, add_completion=False, pretty_exceptions_enable=False)
worker_app = typer.Typer(no_args_is_help=True, add_completion=False)
app.add_typer(worker_app, name="worker")


def _parse_csv(value: str, allowed: tuple[str, ...]) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    unknown = [item for item in items if item not in allowed]
    if unknown:
        raise typer.BadParameter(f"未知项 {unknown}；允许: {', '.join(allowed)}")
    return items


@app.command()
def bootstrap(
    workflows: str = typer.Option(
        ",".join(WORKFLOWS),
        help="逗号分隔的 workflow 列表",
    ),
) -> None:
    """准备隔离 uv 环境、GAME vendor 与权重。"""
    names = _parse_csv(workflows, WORKFLOWS)
    layout = resolve_layout()
    bootstrap_workflows(layout, names)


@app.command()
def doctor(
    workflows: str = typer.Option(
        ",".join(WORKFLOWS),
        help="逗号分隔的 workflow 列表",
    ),
) -> None:
    """只读诊断：缺项给出修复建议，不下载、不改环境。"""
    names = _parse_csv(workflows, WORKFLOWS)
    layout = resolve_layout()
    ok = run_doctor(layout, names)
    raise typer.Exit(code=0 if ok else 1)


@app.command("process")
def process_cmd(
    audio: Path = typer.Argument(..., exists=True, readable=True, resolve_path=True),
    targets: str = typer.Option(
        "piano,vocal,harmony,chords",
        help="逗号分隔目标: piano,vocal,harmony,chords",
    ),
    job_id: str | None = typer.Option(None, help="可选固定 job id"),
) -> None:
    """对一首音频跑第一版 MIDI 流水线。"""
    selected = _parse_csv(targets, TARGETS)
    layout = resolve_layout()
    job = process_audio(layout, audio, targets=selected, job_id=job_id)
    typer.echo(str(job.root))


@worker_app.command("run")
def worker_run(
    workflow: str = typer.Option(..., help="separation / muscriptor / game / basic_pitch"),
    request: Path = typer.Option(..., exists=True, readable=True, resolve_path=True),
) -> None:
    """按 request JSON 跑一个 workflow worker。"""
    if workflow not in WORKFLOWS:
        raise typer.BadParameter(f"未知 workflow: {workflow}")
    layout = resolve_layout()
    result = run_workflow_infer(layout, workflow, request)
    tee_stderr(result.stderr)
    if result.stdout:
        typer.echo(result.stdout, nl=False)
    raise typer.Exit(code=result.returncode)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
