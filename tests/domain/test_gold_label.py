"""Layer: test.
Role: Check GoldLabel rules without touching the filesystem.
Depends on: domain.
"""

from datetime import date

import pytest

from jobwatch_intake.domain.gold_label import (
    GoldLabel,
    InvalidGoldLabel,
    LanguageNeed,
    Level,
    Requirement,
)


def _label(**overrides) -> GoldLabel:
    data = dict(
        job_id="job-a1abfcca01d0",
        labeler="example",
        labeled_at=date(2026, 11, 22),
    )
    data.update(overrides)
    return GoldLabel(**data)


def test_gold_label_minimal_is_valid_and_skills_are_lowercased():
    label = _label(skills_required=["Python", " SQL "])
    assert label.skills_required == ("python", "sql")


def test_required_language_may_carry_a_level():
    label = _label(finnish=LanguageNeed(Requirement.required, Level.fluent))
    assert label.finnish.level == Level.fluent


def test_not_mentioned_with_level_is_rejected():
    with pytest.raises(InvalidGoldLabel) as caught:
        _label(finnish=LanguageNeed(Requirement.not_mentioned, Level.fluent))
    assert caught.value.errors == [
        ("finnish", "level must be unspecified when the language is not mentioned")
    ]


def test_skill_in_both_lists_is_rejected():
    with pytest.raises(InvalidGoldLabel) as caught:
        _label(skills_required=["python"], skills_preferred=["Python"])
    assert caught.value.errors == [
        ("(whole posting)", "skill is in both required and preferred: ['python']")
    ]


def test_duplicate_skill_is_rejected():
    with pytest.raises(InvalidGoldLabel) as caught:
        _label(skills_required=["python", "Python"])
    assert ("skills_required", "skill is duplicated in the same list") in caught.value.errors


def test_empty_skill_is_rejected():
    with pytest.raises(InvalidGoldLabel) as caught:
        _label(skills_required=["  "])
    assert ("skills_required", "skill is empty") in caught.value.errors


def test_experience_years_stay_in_range_or_empty():
    assert _label(experience_years_min=0).experience_years_min == 0
    assert _label(experience_years_min=30).experience_years_min == 30
    assert _label(experience_years_min=None).experience_years_min is None
    with pytest.raises(InvalidGoldLabel):
        _label(experience_years_min=-1)
    with pytest.raises(InvalidGoldLabel):
        _label(experience_years_min=31)


def test_short_labeler_and_bad_job_id_are_both_reported():
    with pytest.raises(InvalidGoldLabel) as caught:
        _label(job_id="nope", labeler="v")
    assert [name for name, _ in caught.value.errors] == ["job_id", "labeler"]
