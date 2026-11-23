"""Layer: test.
Role: Check JobPosting rules without touching the filesystem.
Depends on: domain.
"""

from datetime import date, datetime, timezone

import pytest

from jobwatch_intake.domain.job_posting import (
    InvalidJobPosting,
    JobPosting,
    Language,
    make_job_id,
)


def _job(**overrides) -> JobPosting:
    data = dict(
        id="job-a1abfcca01d0",
        source="example-board",
        url="https://example.invalid/jobs/1",
        language=Language.en,
        title="Junior Data Engineer",
        company="Example Analytics Oy",
        location="Helsinki",
        published_at=date(2026, 11, 18),
        deadline=date(2026, 12, 15),
        text="x" * 150,
        captured_at=datetime(2026, 11, 22, 16, 58, 6, tzinfo=timezone.utc),
    )
    data.update(overrides)
    return JobPosting(**data)


def test_strips_fields_and_normalizes_newlines():
    job = _job(source="  ab ", title="  abc ", company="  oy ", text="\r\n" + ("ä" * 150) + "  ")
    assert job.source == "ab"
    assert job.title == "abc"
    assert job.company == "oy"
    assert job.text == "ä" * 150


def test_http_url_is_accepted():
    assert _job(url="http://example.invalid/a").url == "http://example.invalid/a"


def test_url_may_be_missing():
    assert _job(url=None).url is None


def test_reports_every_length_url_and_deadline_error():
    with pytest.raises(InvalidJobPosting) as caught:
        _job(
            source="a",
            title="ab",
            company="b",
            url="ftp://example.invalid/jobs/1",
            text="x" * 149,
            published_at=date(2026, 12, 20),
            deadline=date(2026, 12, 1),
        )
    assert [name for name, _ in caught.value.errors] == [
        "source",
        "url",
        "title",
        "company",
        "text",
        "(whole posting)",
    ]
    assert ("url", "url must start with http:// or https://") in caught.value.errors
    assert ("(whole posting)", "deadline must not be before published_at") in caught.value.errors


def test_bad_id_is_rejected():
    with pytest.raises(InvalidJobPosting) as caught:
        _job(id="job-XYZ")
    assert caught.value.errors[0][0] == "id"


def test_same_calendar_day_is_allowed():
    day = date(2026, 12, 1)
    assert _job(published_at=day, deadline=day).deadline == day


def test_job_id_is_stable_and_url_normalized():
    first = make_job_id("https://Example.invalid/jobs/1/", "A", "B", "x")
    second = make_job_id("https://example.invalid/jobs/1#top", "C", "D", "y")
    assert first == second
    assert make_job_id(None, "A", "B", "x" * 600) == make_job_id(None, "a", "b", "x" * 600 + "tail")
