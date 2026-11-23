"""Layer: test.
Role: Check the SaveJob use case with an in-memory store and a fixed clock.
Depends on: application and domain.
"""

from datetime import date, datetime, timezone

import pytest

from jobwatch_intake.application.save_job import SaveJob, SaveJobCommand
from jobwatch_intake.domain.job_posting import InvalidJobPosting, JobPosting

WHEN = datetime(2026, 11, 22, 16, 58, 6, tzinfo=timezone.utc)
BODY = "x" * 150


class FakeJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[str, JobPosting] = {}

    def exists(self, job_id: str) -> bool:
        return job_id in self.jobs

    def locate(self, job_id: str) -> str:
        return f"memory:{job_id}"

    def save(self, job: JobPosting) -> str:
        self.jobs[job.id] = job
        return self.locate(job.id)


class FixedClock:
    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        return self._moment


def _command(**overrides) -> SaveJobCommand:
    data = dict(
        source="example-board",
        url="https://example.invalid/jobs/1",
        language="en",
        title="Junior Data Engineer",
        company="Example Analytics Oy",
        location="Helsinki",
        published_at=date(2026, 11, 18),
        deadline=date(2026, 12, 15),
        text=BODY,
        force=False,
    )
    data.update(overrides)
    return SaveJobCommand(**data)


def test_saves_a_new_job_with_the_fixed_clock():
    repository = FakeJobRepository()
    result = SaveJob(repository, FixedClock(WHEN)).execute(_command())
    assert result.status == "saved"
    stored = repository.jobs[result.job_id]
    assert stored.captured_at == WHEN
    assert stored.company == "Example Analytics Oy"


def test_second_save_reports_exists_and_keeps_the_first_copy():
    repository = FakeJobRepository()
    first = SaveJob(repository, FixedClock(WHEN)).execute(_command())
    later = datetime(2026, 12, 1, tzinfo=timezone.utc)
    second = SaveJob(repository, FixedClock(later)).execute(
        _command(title="Other title", text=BODY + " more")
    )
    assert (first.status, second.status) == ("saved", "exists")
    assert second.job_id == first.job_id
    assert repository.jobs[first.job_id].captured_at == WHEN
    assert "more" not in repository.jobs[first.job_id].text


def test_force_overwrites_the_stored_job():
    repository = FakeJobRepository()
    SaveJob(repository, FixedClock(WHEN)).execute(_command())
    result = SaveJob(repository, FixedClock(WHEN)).execute(
        _command(text=BODY + " extended", force=True)
    )
    assert result.status == "saved"
    assert "extended" in repository.jobs[result.job_id].text


def test_invalid_job_raises_and_does_not_save():
    repository = FakeJobRepository()
    with pytest.raises(InvalidJobPosting):
        SaveJob(repository, FixedClock(WHEN)).execute(_command(text="Too short."))
    assert repository.jobs == {}
