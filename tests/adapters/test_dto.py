"""Layer: test.
Role: Check that the DTOs reject an unknown field and a bad date.
Depends on: the inbound adapter and domain.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO, JobDraftDTO


def _draft(**overrides) -> dict:
    data = {
        "source": "example-board",
        "url": "https://example.invalid/jobs/1",
        "language": "en",
        "title": "Junior Data Engineer",
        "company": "Example Analytics Oy",
        "text": "x" * 40,
    }
    data.update(overrides)
    return data


def test_unknown_label_field_is_rejected():
    with pytest.raises(ValidationError):
        GoldLabelFileDTO.model_validate(
            {
                "job_id": "job-a1abfcca01d0",
                "labeler": "example",
                "labeled_at": "2026-11-22",
                "salary": 3000,
            }
        )


def test_typo_inside_language_block_is_rejected():
    with pytest.raises(ValidationError):
        GoldLabelFileDTO.model_validate(
            {
                "job_id": "job-a1abfcca01d0",
                "labeler": "example",
                "labeled_at": "2026-11-22",
                "finnish": {"requirement": "required", "levle": "fluent"},
            }
        )


def test_iso_date_is_parsed_and_a_bad_date_is_rejected():
    dto = JobDraftDTO.model_validate(_draft(published_at="2026-11-18"))
    assert dto.published_at == date(2026, 11, 18)
    with pytest.raises(ValidationError):
        JobDraftDTO.model_validate(_draft(published_at="18.11.2026"))


def test_unknown_draft_field_is_rejected():
    with pytest.raises(ValidationError) as caught:
        JobDraftDTO.model_validate(_draft(salary="3000"))
    assert any("salary" in err["loc"] for err in caught.value.errors())
