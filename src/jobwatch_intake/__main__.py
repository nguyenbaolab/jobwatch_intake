"""Lớp: composition.
Vai trò: Điểm vào khi chạy python -m jobwatch_intake.
Phụ thuộc: adapter vào và composition.
"""

from __future__ import annotations

import sys

from jobwatch_intake.adapters.inbound.cli import run
from jobwatch_intake.composition import make_save_job


def main(argv: list[str] | None = None) -> int:
    return run(sys.argv[1:] if argv is None else argv, make_save_job)


if __name__ == "__main__":
    raise SystemExit(main())
