"""Layer: application.
Role: Ports the use cases use to reach the outside world.
Depends on: the standard library and domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, Sequence

from jobwatch_intake.domain.gold_label import GoldLabel
from jobwatch_intake.domain.job_posting import JobPosting
from jobwatch_intake.domain.scoring import Extraction


class JobRepository(Protocol):
    def exists(self, job_id: str) -> bool:
        """Whether this posting is already in the store."""

    def locate(self, job_id: str) -> str:
        """Path printed when the posting is saved or already present."""

    def save(self, job: JobPosting) -> str:
        """Write the posting and return the path that was written."""


class Clock(Protocol):
    def now(self) -> datetime:
        """The current time. The system clock returns UTC, rounded to the second."""


class PredictionSource(Protocol):
    def predict(self, labels: Sequence[GoldLabel]) -> Sequence[Extraction]:
        """Extractions the source can produce. A missing job_id is a missing prediction."""
