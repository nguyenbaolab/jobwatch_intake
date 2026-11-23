"""Layer: adapters.inbound.
Role: Check the shape of a draft and a label file, then turn them into plain objects.
Depends on: pydantic, domain, and application.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from jobwatch_intake.application.save_job import SaveJobCommand
from jobwatch_intake.domain.gold_label import (
    GoldLabel,
    LanguageNeed,
    Level,
    Requirement,
    WorkMode,
)
class JobDraftDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    url: Optional[str] = None
    language: Literal["fi", "en", "sv"]
    title: str
    company: str
    location: Optional[str] = None
    published_at: Optional[date] = None
    deadline: Optional[date] = None
    text: str

    def to_command(self, *, force: bool) -> SaveJobCommand:
        return SaveJobCommand(
            source=self.source,
            url=self.url,
            language=self.language,
            title=self.title,
            company=self.company,
            location=self.location,
            published_at=self.published_at,
            deadline=self.deadline,
            text=self.text,
            force=force,
        )


class LanguageNeedDTO(BaseModel):
    """Requirement for one language. This is the most important field in a label."""

    model_config = ConfigDict(extra="forbid")

    requirement: Requirement = Requirement.not_mentioned
    level: Level = Level.unspecified

    def to_domain(self) -> LanguageNeed:
        return LanguageNeed(requirement=self.requirement, level=self.level)


class GoldLabelFileDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", title="GoldLabel")

    job_id: str
    labeler: str
    labeled_at: date
    skills_required: list[str] = Field(default_factory=list)
    skills_preferred: list[str] = Field(default_factory=list)
    finnish: LanguageNeedDTO = Field(default_factory=LanguageNeedDTO)
    swedish: LanguageNeedDTO = Field(default_factory=LanguageNeedDTO)
    english: LanguageNeedDTO = Field(default_factory=LanguageNeedDTO)
    experience_years_min: Optional[int] = None
    city: Optional[str] = None
    work_mode: WorkMode = WorkMode.unspecified
    deadline: Optional[date] = None
    notes: str = ""

    def to_domain(self) -> GoldLabel:
        return GoldLabel(
            job_id=self.job_id,
            labeler=self.labeler,
            labeled_at=self.labeled_at,
            skills_required=tuple(self.skills_required),
            skills_preferred=tuple(self.skills_preferred),
            finnish=self.finnish.to_domain(),
            swedish=self.swedish.to_domain(),
            english=self.english.to_domain(),
            experience_years_min=self.experience_years_min,
            city=self.city,
            work_mode=self.work_mode,
            deadline=self.deadline,
            notes=self.notes,
        )
