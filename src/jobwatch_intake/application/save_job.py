"""Lớp: application.
Vai trò: Use case lưu một tin tuyển dụng đúng một lần.
Phụ thuộc: thư viện chuẩn, domain và các cổng.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Literal, Optional

from jobwatch_intake.application.ports import Clock, JobRepository
from jobwatch_intake.domain.job_posting import JobPosting, Language, make_job_id

log = logging.getLogger("save_job")


@dataclass
class SaveJobCommand:
    source: str
    url: Optional[str]
    language: str
    title: str
    company: str
    location: Optional[str]
    published_at: Optional[date]
    deadline: Optional[date]
    text: str
    force: bool = False


@dataclass
class SaveJobResult:
    job_id: str
    status: Literal["saved", "exists"]
    path: str


class SaveJob:
    def __init__(self, repository: JobRepository, clock: Clock):
        self._repository = repository
        self._clock = clock

    def execute(self, command: SaveJobCommand) -> SaveJobResult:
        job = JobPosting(
            id=make_job_id(command.url, command.company, command.title, command.text),
            source=command.source,
            url=command.url,
            language=Language(command.language),
            title=command.title,
            company=command.company,
            location=command.location,
            published_at=command.published_at,
            deadline=command.deadline,
            text=command.text,
            captured_at=self._clock.now(),
        )
        log.debug("hợp lệ: id=%s language=%s", job.id, job.language.value)
        if not command.force and self._repository.exists(job.id):
            path = self._repository.locate(job.id)
            log.debug("đã có %s, bỏ qua", path)
            return SaveJobResult(job_id=job.id, status="exists", path=path)
        path = self._repository.save(job)
        return SaveJobResult(job_id=job.id, status="saved", path=path)
