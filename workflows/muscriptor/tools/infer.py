"""MuScriptor 完整混音转录 worker。stdout 仅 JSONL。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "common"))

from protocol import emit, fail, load_request, require_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    args = parser.parse_args()
    request = load_request(args.request)
    emit(request, "started", {"workflow": "muscriptor"})

    audio = Path(request["inputs"]["audio"])
    midi_out = Path(request["outputs"]["midi"])
    midi_out.parent.mkdir(parents=True, exist_ok=True)
    require_file(audio, request, what="输入音频")

    params = request.get("params") or {}
    model = params.get("model", "medium")
    instruments = params.get("instruments")
    cli = shutil.which("muscriptor")
    if cli:
        command = [cli, "transcribe", str(audio), "-o", str(midi_out), "--model", str(model)]
    else:
        command = [
            sys.executable,
            "-m",
            "muscriptor",
            "transcribe",
            str(audio),
            "-o",
            str(midi_out),
            "--model",
            str(model),
        ]
    if instruments:
        command.extend(["--instruments", str(instruments)])
    emit(request, "progress", {"message": "running muscriptor transcribe", "model": model})
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    if completed.returncode != 0:
        fail(
            request,
            f"muscriptor 退出码 {completed.returncode}: {(completed.stderr or completed.stdout)[-2000:]}",
        )
    require_file(midi_out, request, what="MuScriptor MIDI")
    version = None
    try:
        version = metadata.version("muscriptor")
    except metadata.PackageNotFoundError:
        version = None
    emit(
        request,
        "succeeded",
        {
            "midi": str(midi_out),
            "model": model,
            "instruments": instruments,
            "package_version": version,
        },
    )


if __name__ == "__main__":
    main()
