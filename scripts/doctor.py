"""薄封装：诊断本机依赖。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "polyscribe", "doctor", *sys.argv[1:]],
            cwd=ROOT,
        )
    )


if __name__ == "__main__":
    main()
