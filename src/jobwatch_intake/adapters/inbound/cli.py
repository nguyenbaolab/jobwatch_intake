"""Lớp: adapters.inbound.
Vai trò: Đọc đối số dòng lệnh, in thông báo và trả mã thoát.
Phụ thuộc: thư viện chuẩn, application, domain và adapter vào.
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
    parser = argparse.ArgumentParser(description="Lưu một tin tuyển dụng từ file nháp.")
    parser.add_argument("draft", type=Path, help="đường dẫn file nháp")
    parser.add_argument("--out", type=Path, default=Path("data/jobs"), help="thư mục ghi JSON")
    parser.add_argument("--force", action="store_true", help="ghi đè nếu tin đã được lưu")
    parser.add_argument("--verbose", action="store_true", help="in từng bước để trace")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="[%(name)s] %(message)s",
        stream=sys.stderr,
    )

    try:
        draft = read_draft(args.draft)
    except (OSError, UnicodeDecodeError, DraftError) as exc:
        print(f"Không đọc được file nháp: {exc}", file=sys.stderr)
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
        print(f"Đã có sẵn, không ghi lại: {result.path}  (dùng --force để ghi đè)")
    else:
        print(f"Đã lưu: {result.path}")
    return 0


def _from_validation(exc: ValidationError) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"]) or "(cả tin)"
        rows.append((field, str(err["msg"])))
    return rows


def _print_errors(errors: list[tuple[str, str]]) -> None:
    print(f"Tin không hợp lệ ({len(errors)} lỗi):", file=sys.stderr)
    for field, message in errors:
        print(f"  - {field}: {message}", file=sys.stderr)
