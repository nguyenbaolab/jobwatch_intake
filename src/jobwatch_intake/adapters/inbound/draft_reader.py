"""Layer: adapters.inbound.
Role: Read a draft file into a dict of fields plus the posting text.
Depends on: the standard library.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("save_job")

SEPARATOR = "---"


class DraftError(Exception):
    """The draft has the wrong shape (missing ---, or a line with no ':')."""


def read_draft(path: Path) -> dict:
    """Split a draft file into a dict of header fields plus the posting text."""
    raw = path.read_text(encoding="utf-8")
    lines = raw.replace("\r\n", "\n").split("\n")

    if SEPARATOR not in [line.strip() for line in lines]:
        raise DraftError(f"missing '{SEPARATOR}' line between the header and the posting text")
    sep_index = [line.strip() for line in lines].index(SEPARATOR)

    draft: dict = {}
    for number, line in enumerate(lines[:sep_index], start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise DraftError(f"line {number} has no ':' → {line!r}")
        key, value = line.split(":", 1)
        draft[key.strip()] = value.strip() or None

    draft["text"] = "\n".join(lines[sep_index + 1 :])
    log.debug(
        "read %s: %d header fields, %d characters of text",
        path,
        len(draft) - 1,
        len(draft["text"]),
    )
    return draft
