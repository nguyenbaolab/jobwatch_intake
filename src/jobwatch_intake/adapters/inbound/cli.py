"""Layer: adapters.inbound.
Role: Read command-line arguments, print messages, and return an exit code.
Depends on: the standard library, application, domain, and the inbound adapters.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from jobwatch_intake.adapters.inbound.draft_reader import DraftError, read_draft
from jobwatch_intake.adapters.inbound.dto import JobDraftDTO
from jobwatch_intake.application.save_job import SaveJob
from jobwatch_intake.domain.job_posting import InvalidJobPosting

log = logging.getLogger("save_job")


def run(argv: list[str] | None, make_use_case: Callable[[Path], SaveJob]) -> int:
    parser = argparse.ArgumentParser(description="Save one job posting from a draft file.")
    parser.add_argument("draft", type=Path, help="path to the draft file")
    parser.add_argument("--out", type=Path, default=Path("data/jobs"), help="directory for the JSON files")
    parser.add_argument("--force", action="store_true", help="overwrite a posting that is already saved")
    parser.add_argument("--verbose", action="store_true", help="log each step for tracing")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="[%(name)s] %(message)s",
        stream=sys.stderr,
    )

    try:
        draft = read_draft(args.draft)
    except (OSError, UnicodeDecodeError, DraftError) as exc:
        print(f"Could not read the draft file: {exc}", file=sys.stderr)
        return 2

    try:
        dto = JobDraftDTO.model_validate(draft)
    except ValidationError as exc:
        _print_errors(_from_validation(exc))
        return 1

    try:
        result = make_use_case(args.out).execute(dto.to_command(force=args.force))
    except InvalidJobPosting as exc:
        _print_errors(exc.errors)
        return 1

    if result.status == "exists":
        print(f"Already saved, not written again: {result.path}  (use --force to overwrite)")
    else:
        print(f"Saved: {result.path}")
    return 0


def _from_validation(exc: ValidationError) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"]) or "(whole posting)"
        rows.append((field, str(err["msg"])))
    return rows


def _print_errors(errors: list[tuple[str, str]]) -> None:
    print(f"Invalid job posting ({len(errors)} errors):", file=sys.stderr)
    for field, message in errors:
        print(f"  - {field}: {message}", file=sys.stderr)
