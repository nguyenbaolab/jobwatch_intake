"""Lớp: test.
Vai trò: Kiểm tra đọc file nháp sai cấu trúc hoặc sai bảng mã.
Phụ thuộc: adapter vào.
"""

from pathlib import Path

import pytest

from jobwatch_intake.adapters.inbound.draft_reader import DraftError, read_draft

BODY = "nội dung " * 20


def test_missing_separator(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("source: x\ntitle: y\n" + BODY, encoding="utf-8")
    with pytest.raises(DraftError, match="---"):
        read_draft(path)


def test_header_line_without_colon(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("source x\n---\n" + BODY, encoding="utf-8")
    with pytest.raises(DraftError, match=":"):
        read_draft(path)


def test_not_utf8(tmp_path: Path):
    path = tmp_path / "latin1.txt"
    path.write_bytes("source: x\n---\nÄÖ".encode("latin-1"))
    with pytest.raises(UnicodeDecodeError):
        read_draft(path)


def test_comment_is_skipped_and_later_separator_stays_in_text(tmp_path: Path):
    path = tmp_path / "d.txt"
    path.write_text("source: board\n# ghi chú\n\n---\ndòng\n---\nthêm\n", encoding="utf-8")
    draft = read_draft(path)
    assert draft["source"] == "board"
    assert draft["text"].startswith("dòng\n---\nthêm")
