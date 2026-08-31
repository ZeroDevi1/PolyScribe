"""薄封装：准备隔离环境。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    raise SystemExit(
        subprocess.call(
            [sys.executable, "-m", "polyscribe", "bootstrap", *sys.argv[1:]],
            cwd=ROOT,
        )
    )


if __name__ == "__main__":
    main()
