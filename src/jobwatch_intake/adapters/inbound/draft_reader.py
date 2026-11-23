"""Lớp: adapters.inbound.
Vai trò: Đọc file nháp thành dict các trường và nội dung tin.
Phụ thuộc: thư viện chuẩn.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("save_job")

SEPARATOR = "---"


class DraftError(Exception):
    """File nháp sai cấu trúc (thiếu dòng ---, dòng không có dấu :)."""


def read_draft(path: Path) -> dict:
    """Tách file nháp thành dict các trường + nội dung tin."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.replace("\r\n", "\n").split("\n")

    if SEPARATOR not in [line.strip() for line in lines]:
        raise DraftError(f"thiếu dòng '{SEPARATOR}' ngăn phần đầu và nội dung tin")
    sep_index = [line.strip() for line in lines].index(SEPARATOR)

    draft: dict = {}
    for number, line in enumerate(lines[:sep_index], start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise DraftError(f"dòng {number} không có dấu ':' → {line!r}")
        key, value = line.split(":", 1)
        draft[key.strip()] = value.strip() or None

    draft["text"] = "\n".join(lines[sep_index + 1 :])
    log.debug(
        "đọc xong %s: %d trường đầu, %d ký tự nội dung",
        path,
        len(draft) - 1,
        len(draft["text"]),
    )
    return draft
