"""薄封装：处理一首音频。默认指向仓库内《天生冷血》flac。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "audios" / "天生冷血 - 陈默之.flac"


def main() -> None:
    args = sys.argv[1:]
    if not args:
        args = [str(DEFAULT), "--targets", "piano,vocal,harmony,chords"]
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "polyscribe", "process", *args],
            cwd=ROOT,
        )
    )


if __name__ == "__main__":
    main()
