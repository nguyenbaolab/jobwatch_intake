"""Lớp: application.
Vai trò: Cổng để use case nói chuyện với kho tin và đồng hồ.
Phụ thuộc: thư viện chuẩn và domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from jobwatch_intake.domain.job_posting import JobPosting


class JobRepository(Protocol):
    def exists(self, job_id: str) -> bool:
        """Tin này đã có trong kho hay chưa."""

    def locate(self, job_id: str) -> str:
        """Đường dẫn sẽ in ra khi lưu hoặc khi tin đã có sẵn."""

    def save(self, job: JobPosting) -> str:
        """Ghi tin và trả về đường dẫn đã ghi."""


class Clock(Protocol):
    def now(self) -> datetime:
        """Thời điểm hiện tại. Bản hệ thống trả về UTC, làm tròn tới giây."""
