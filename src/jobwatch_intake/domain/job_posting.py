"""Layer: domain.
Role: A job posting and the rules it must satisfy.
Depends on: the standard library.
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
    """The posting breaks a business rule. errors is a list of (field, reason)."""

    def __init__(self, errors: list[tuple[str, str]]):
        self.errors = errors
        super().__init__("; ".join(f"{field}: {message}" for field, message in errors))


def make_job_id(url: Optional[str], company: str, title: str, text: str) -> str:
    """Stable id: the same url (or the same company, title, and start of the text) gives the same id.

    Running the command twice on one posting therefore does not create two copies.
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
    # datetime is a subclass of date; the deadline rule compares calendar dates only.
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
            errors.append(("id", "id must match ^job-[0-9a-f]{12}$"))
        if not isinstance(source, str) or len(source) < 2:
            errors.append(("source", "source must be at least 2 characters"))
        if self.url is not None and not (
            isinstance(self.url, str) and self.url.startswith(("http://", "https://"))
        ):
            errors.append(("url", "url must start with http:// or https://"))
        if not isinstance(self.language, Language):
            errors.append(("language", "language must be fi, en, or sv"))
        if not isinstance(title, str) or len(title) < 3:
            errors.append(("title", "title must be at least 3 characters"))
        if not isinstance(company, str) or len(company) < 2:
            errors.append(("company", "company must be at least 2 characters"))
        if not isinstance(text, str) or len(text) < MIN_TEXT_CHARS:
            errors.append(("text", "text must be at least 150 characters"))
        if (
            _is_calendar_date(self.published_at)
            and _is_calendar_date(self.deadline)
            and self.deadline < self.published_at
        ):
            errors.append(("(whole posting)", "deadline must not be before published_at"))
        if errors:
            raise InvalidJobPosting(errors)
