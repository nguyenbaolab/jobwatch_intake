"""Lớp: adapters.outbound.
Vai trò: Định dạng JSON của một tin đã lưu.
Phụ thuộc: pydantic và domain.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from jobwatch_intake.domain.job_posting import JobPosting


class StoredJobDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", title="JobPosting")

    id: str
    source: str = Field(description="Tên nguồn, vd duunitori, company-site")
    url: Optional[str] = None
    language: Literal["fi", "en", "sv"]
    title: str
    company: str
    location: Optional[str] = None
    published_at: Optional[date] = None
    deadline: Optional[date] = None
    text: str
    captured_at: datetime

    @classmethod
    def from_job(cls, job: JobPosting) -> StoredJobDTO:
        return cls(
            id=job.id,
            source=job.source,
            url=job.url,
            language=job.language.value,
            title=job.title,
            company=job.company,
            location=job.location,
            published_at=job.published_at,
            deadline=job.deadline,
            text=job.text,
            captured_at=job.captured_at,
        )
