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
from jobwatch_intake.adapters.inbound.gold_reader import GoldReadError, read_gold_labels
from jobwatch_intake.application.evaluate_extractor import (
    DuplicatePrediction,
    EvaluateExtractor,
    Evaluation,
)
from jobwatch_intake.application.ports import PredictionSource
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


def run_eval(argv: list[str] | None, make_source: Callable[[], PredictionSource]) -> int:
    parser = argparse.ArgumentParser(description="Score an extractor against gold labels.")
    parser.add_argument("--labels", type=Path, required=True, help="directory of gold-label JSON files")
    parser.add_argument("--fake", choices=["gold"], required=True, help="in-memory extractor; gold copies the label")
    args = parser.parse_args(argv)
    try:
        labels = read_gold_labels(args.labels)
    except GoldReadError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    try:
        result = EvaluateExtractor(make_source()).execute(labels)
    except DuplicatePrediction as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(_format_evaluation(result))
    return 0


def _format_evaluation(result: Evaluation) -> str:
    lines = [
        f"{'field':<24} {'n':>3} {'correct':>7} {'acc_all':>12} {'n_nonempty':>10} {'acc_gold_nonempty':>18}"
    ]
    for row in result.scores.fields:
        lines.append(
            f"{row.field:<24} {row.n:>3} {row.correct:>7} "
            f"{_ratio(row.correct, row.n):>12} {row.n_nonempty:>10} "
            f"{_ratio(row.correct_nonempty, row.n_nonempty):>18}"
        )
    lines.append("")
    lines.append("skills")
    for row in result.scores.skills:
        lines.append(
            f"{row.field:<24} precision {_ratio(row.tp, row.predicted)}"
            f"  recall {_ratio(row.tp, row.gold)}"
            f"  F1 {_ratio(2 * row.tp, row.predicted + row.gold)}"
        )
    lines.append("")
    lines.append("wrong cells")
    lines.append("job_id | field | gold | prediction")
    if result.scores.mismatches:
        for cell in result.scores.mismatches:
            lines.append(
                f"{cell.job_id} | {cell.field} | {_show(cell.gold)} | {_show(cell.prediction)}"
            )
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("missing_predictions")
    lines.append(_ids(result.missing_predictions))
    lines.append("")
    lines.append("unlabeled_predictions")
    lines.append(_ids(result.unlabeled_predictions))
    return "\n".join(lines)


def _ratio(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator} ({numerator / denominator:.2f})"


def _show(value: object) -> str:
    if value is None:
        return "null"
    raw = getattr(value, "value", value)
    return str(raw)


def _ids(job_ids: tuple[str, ...]) -> str:
    if not job_ids:
        return "(none)"
    return "\n".join(job_ids)
