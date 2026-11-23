"""Layer: test.
Role: Check the atomic JSON write and that non-ASCII letters are kept.
Depends on: the outbound adapter and domain.
"""

import json
from datetime import date, datetime, timezone
from pathlib import Path

from jobwatch_intake.adapters.outbound.json_job_repository import JsonJobRepository
from jobwatch_intake.domain.job_posting import JobPosting, Language


def test_save_keeps_finnish_letters_and_leaves_no_temp_file(tmp_path: Path):
    job = JobPosting(
        id="job-a1abfcca01d0",
        source="board",
        url="https://example.invalid/jobs/1",
        language=Language.fi,
        # Intentional non-ASCII test data: Finnish letters must survive ensure_ascii=False.
        title="Ohjelmistokehittäjä",
        company="Oy",
        location="Tampere",
        published_at=date(2026, 11, 16),
        deadline=date(2026, 12, 10),
        text="äö" * 80,
        captured_at=datetime(2026, 11, 22, 16, 58, 6, tzinfo=timezone.utc),
    )
    written = Path(JsonJobRepository(tmp_path).save(job))
    assert list(tmp_path.glob("*.tmp")) == []
    raw = written.read_bytes()
    assert b"\r" not in raw
    assert raw.endswith(b"\n")
    text = raw.decode("utf-8")
    assert "ä" in text and "ö" in text
    data = json.loads(text)
    assert list(data) == [
        "id",
        "source",
        "url",
        "language",
        "title",
        "company",
        "location",
        "published_at",
        "deadline",
        "text",
        "captured_at",
    ]
    assert data["title"] == "Ohjelmistokehittäjä"
    assert data["captured_at"] == "2026-11-22T16:58:06Z"
    assert "\\u00e4" not in text
