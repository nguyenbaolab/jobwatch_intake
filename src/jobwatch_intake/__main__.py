"""Layer: composition.
Role: Entry point for python -m jobwatch_intake.
Depends on: the inbound adapter and composition.
"""

from __future__ import annotations

import sys

from jobwatch_intake.adapters.inbound.cli import run, run_eval
from jobwatch_intake.composition import make_echo_gold, make_save_job


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == ["eval"]:
        return run_eval(args[1:], make_echo_gold)
    return run(args, make_save_job)


if __name__ == "__main__":
    raise SystemExit(main())
