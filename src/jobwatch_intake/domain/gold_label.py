"""Lớp: domain.
Vai trò: Nhãn vàng và các luật bất biến của nó.
Phụ thuộc: thư viện chuẩn và domain.job_posting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional, Sequence

from jobwatch_intake.domain.job_posting import JOB_ID_PATTERN


class Requirement(str, Enum):
    required = "required"
    preferred = "preferred"
    not_mentioned = "not_mentioned"


class Level(str, Enum):
    unspecified = "unspecified"
    basic = "basic"
    good = "good"
    fluent = "fluent"
    native = "native"


class WorkMode(str, Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"
    unspecified = "unspecified"


class InvalidGoldLabel(Exception):
    """Nhãn vi phạm luật nghiệp vụ. errors là danh sách (trường, lý do)."""

    def __init__(self, errors: list[tuple[str, str]]):
        self.errors = errors
        super().__init__("; ".join(f"{name}: {message}" for name, message in errors))


@dataclass(frozen=True)
class LanguageNeed:
    requirement: Requirement = Requirement.not_mentioned
    level: Level = Level.unspecified


def _clean_skills(
    field_name: str, skills: Sequence[str], errors: list[tuple[str, str]]
) -> tuple[str, ...]:
    cleaned = tuple(item.strip().lower() for item in skills)
    if any(not item for item in cleaned):
        errors.append((field_name, "có kỹ năng rỗng"))
    if len(set(cleaned)) != len(cleaned):
        errors.append((field_name, "kỹ năng bị lặp trong cùng một danh sách"))
    return cleaned


@dataclass(frozen=True)
class GoldLabel:
    job_id: str
    labeler: str
    labeled_at: date
    skills_required: tuple[str, ...] = ()
    skills_preferred: tuple[str, ...] = ()
    finnish: LanguageNeed = field(default_factory=LanguageNeed)
    swedish: LanguageNeed = field(default_factory=LanguageNeed)
    english: LanguageNeed = field(default_factory=LanguageNeed)
    experience_years_min: Optional[int] = None
    city: Optional[str] = None
    work_mode: WorkMode = WorkMode.unspecified
    deadline: Optional[date] = None
    notes: str = ""

    def __post_init__(self) -> None:
        errors: list[tuple[str, str]] = []
        required = _clean_skills("skills_required", self.skills_required, errors)
        preferred = _clean_skills("skills_preferred", self.skills_preferred, errors)
        object.__setattr__(self, "skills_required", required)
        object.__setattr__(self, "skills_preferred", preferred)

        if not isinstance(self.job_id, str) or JOB_ID_PATTERN.fullmatch(self.job_id) is None:
            errors.append(("job_id", "job_id phải khớp ^job-[0-9a-f]{12}$"))
        if not isinstance(self.labeler, str) or len(self.labeler) < 2:
            errors.append(("labeler", "labeler phải có ít nhất 2 ký tự"))

        for name in ("finnish", "swedish", "english"):
            need: LanguageNeed = getattr(self, name)
            if (
                need.requirement == Requirement.not_mentioned
                and need.level != Level.unspecified
            ):
                errors.append((name, "không nhắc ngôn ngữ này thì level phải là unspecified"))

        years = self.experience_years_min
        if years is not None and (
            isinstance(years, bool) or not isinstance(years, int) or years < 0 or years > 30
        ):
            errors.append(("experience_years_min", "experience_years_min phải từ 0 đến 30"))

        overlap = set(required) & set(preferred)
        if overlap:
            errors.append(
                ("(cả tin)", f"kỹ năng nằm ở cả required và preferred: {sorted(overlap)}")
            )
        if errors:
            raise InvalidGoldLabel(errors)
