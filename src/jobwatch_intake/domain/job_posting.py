"""Lớp: domain.
Vai trò: Tin tuyển dụng và các luật bất biến của nó.
Phụ thuộc: thư viện chuẩn.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

JOB_ID_PATTERN = re.compile(r"^job-[0-9a-f]{12}$")
MIN_TEXT_CHARS = 150


class Language(str, Enum):
    fi = "fi"
    en = "en"
    sv = "sv"


class InvalidJobPosting(Exception):
    """Tin vi phạm luật nghiệp vụ. errors là danh sách (trường, lý do)."""

    def __init__(self, errors: list[tuple[str, str]]):
        self.errors = errors
        super().__init__("; ".join(f"{field}: {message}" for field, message in errors))


def make_job_id(url: Optional[str], company: str, title: str, text: str) -> str:
    """Id ổn định: cùng url (hoặc cùng công ty + tên việc + đầu nội dung) thì cùng id.

    Nhờ vậy chạy script hai lần trên cùng một tin không tạo ra hai bản.
    """
    if url:
        key = url.strip().split("#")[0].rstrip("/").lower()
    else:
        key = "|".join(
            [company.strip().lower(), title.strip().lower(), text.strip()[:500].lower()]
        )
    return "job-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]


def _as_stripped(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _is_calendar_date(value: object) -> bool:
    # datetime là lớp con của date; luật hạn nộp chỉ so ngày lịch.
    return isinstance(value, date) and not isinstance(value, datetime)


@dataclass(frozen=True)
class JobPosting:
    id: str
    source: str
    url: Optional[str]
    language: Language
    title: str
    company: str
    location: Optional[str]
    published_at: Optional[date]
    deadline: Optional[date]
    text: str
    captured_at: datetime

    def __post_init__(self) -> None:
        source = _as_stripped(self.source)
        title = _as_stripped(self.title)
        company = _as_stripped(self.company)
        location = _as_stripped(self.location) if self.location is not None else None
        text = self.text.replace("\r\n", "\n").strip() if isinstance(self.text, str) else self.text
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "company", company)
        object.__setattr__(self, "location", location)
        object.__setattr__(self, "text", text)

        errors: list[tuple[str, str]] = []
        if not isinstance(self.id, str) or JOB_ID_PATTERN.fullmatch(self.id) is None:
            errors.append(("id", "id phải khớp ^job-[0-9a-f]{12}$"))
        if not isinstance(source, str) or len(source) < 2:
            errors.append(("source", "source phải có ít nhất 2 ký tự"))
        if self.url is not None and not (
            isinstance(self.url, str) and self.url.startswith(("http://", "https://"))
        ):
            errors.append(("url", "url phải bắt đầu bằng http:// hoặc https://"))
        if not isinstance(self.language, Language):
            errors.append(("language", "language phải là fi, en hoặc sv"))
        if not isinstance(title, str) or len(title) < 3:
            errors.append(("title", "title phải có ít nhất 3 ký tự"))
        if not isinstance(company, str) or len(company) < 2:
            errors.append(("company", "company phải có ít nhất 2 ký tự"))
        if not isinstance(text, str) or len(text) < MIN_TEXT_CHARS:
            errors.append(("text", "text phải có ít nhất 150 ký tự"))
        if (
            _is_calendar_date(self.published_at)
            and _is_calendar_date(self.deadline)
            and self.deadline < self.published_at
        ):
            errors.append(("(cả tin)", "deadline không được trước published_at"))
        if errors:
            raise InvalidJobPosting(errors)
