"""Layer: domain.
Role: Compare one gold label with one extraction and total the scores.
Depends on: the standard library and domain.gold_label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from fractions import Fraction
from typing import Optional, Sequence

from jobwatch_intake.domain.gold_label import (
    GoldLabel,
    LanguageNeed,
    Level,
    Requirement,
    WorkMode,
)

SCORED_FIELDS: tuple[str, ...] = (
    "experience_years_min",
    "city",
    "work_mode",
    "deadline",
    "finnish.requirement",
    "finnish.level",
    "swedish.requirement",
    "swedish.level",
    "english.requirement",
    "english.level",
    "skills_required",
    "skills_preferred",
)

SKILL_FIELDS: tuple[str, ...] = ("skills_required", "skills_preferred")


@dataclass(frozen=True)
class Extraction:
    """One extractor output. A bad prediction is kept and scored, not rejected."""

    job_id: str
    skills_required: tuple[str, ...] = ()
    skills_preferred: tuple[str, ...] = ()
    finnish: LanguageNeed = field(default_factory=LanguageNeed)
    swedish: LanguageNeed = field(default_factory=LanguageNeed)
    english: LanguageNeed = field(default_factory=LanguageNeed)
    experience_years_min: Optional[int] = None
    city: Optional[str] = None
    work_mode: WorkMode = WorkMode.unspecified
    deadline: Optional[date] = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "skills_required", tuple(self.skills_required))
        object.__setattr__(self, "skills_preferred", tuple(self.skills_preferred))


@dataclass(frozen=True)
class FieldScore:
    field: str
    n: int
    correct: int
    n_nonempty: int
    correct_nonempty: int

    def acc_all(self) -> Optional[Fraction]:
        if self.n == 0:
            return None
        return Fraction(self.correct, self.n)

    def acc_gold_nonempty(self) -> Optional[Fraction]:
        if self.n_nonempty == 0:
            return None
        return Fraction(self.correct_nonempty, self.n_nonempty)


@dataclass(frozen=True)
class SkillsScore:
    field: str
    tp: int
    predicted: int
    gold: int

    def precision(self) -> Optional[Fraction]:
        if self.predicted == 0:
            return None
        return Fraction(self.tp, self.predicted)

    def recall(self) -> Optional[Fraction]:
        if self.gold == 0:
            return None
        return Fraction(self.tp, self.gold)

    def f1(self) -> Optional[Fraction]:
        total = self.predicted + self.gold
        if total == 0:
            return None
        return Fraction(2 * self.tp, total)


@dataclass(frozen=True)
class CellMismatch:
    job_id: str
    field: str
    gold: object
    prediction: object


@dataclass(frozen=True)
class ScoreReport:
    fields: tuple[FieldScore, ...]
    skills: tuple[SkillsScore, ...]
    mismatches: tuple[CellMismatch, ...]


def score_pairs(
    pairs: Sequence[tuple[GoldLabel, Extraction | None]],
) -> ScoreReport:
    """Score joined pairs. None means the prediction is missing: every field is wrong."""

    tallies = {
        name: {"correct": 0, "n_nonempty": 0, "correct_nonempty": 0}
        for name in SCORED_FIELDS
    }
    mismatches: list[CellMismatch] = []
    for gold, prediction in pairs:
        for name in SCORED_FIELDS:
            gold_value = _value(gold, name)
            tally = tallies[name]
            if prediction is None:
                mismatches.append(CellMismatch(gold.job_id, name, gold_value, None))
                if not _is_empty(name, gold_value):
                    tally["n_nonempty"] += 1
                continue
            prediction_value = _value(prediction, name)
            matched = _cells_match(name, gold_value, prediction_value)
            if matched:
                tally["correct"] += 1
            else:
                mismatches.append(
                    CellMismatch(gold.job_id, name, gold_value, prediction_value)
                )
            if not _is_empty(name, gold_value):
                tally["n_nonempty"] += 1
                if matched:
                    tally["correct_nonempty"] += 1
    rows = [
        FieldScore(field=name, n=len(pairs), **tallies[name]) for name in SCORED_FIELDS
    ]
    return ScoreReport(
        fields=tuple(rows),
        skills=tuple(_skills_score(name, pairs) for name in SKILL_FIELDS),
        mismatches=tuple(mismatches),
    )


def _skills_score(
    name: str, pairs: Sequence[tuple[GoldLabel, Extraction | None]]
) -> SkillsScore:
    tp = 0
    predicted = 0
    gold_count = 0
    for gold, prediction in pairs:
        gold_skills = _skill_set(_value(gold, name))
        predicted_skills = (
            set() if prediction is None else _skill_set(_value(prediction, name))
        )
        tp += len(gold_skills & predicted_skills)
        predicted += len(predicted_skills)
        gold_count += len(gold_skills)
    return SkillsScore(field=name, tp=tp, predicted=predicted, gold=gold_count)


def _value(record: GoldLabel | Extraction, name: str) -> object:
    if "." not in name:
        return getattr(record, name)
    language, part = name.split(".", 1)
    return getattr(getattr(record, language), part)


def _is_empty(name: str, value: object) -> bool:
    if name in SKILL_FIELDS:
        return _skill_set(value) == set()
    if name == "work_mode":
        return value == WorkMode.unspecified
    if name.endswith(".requirement"):
        return value == Requirement.not_mentioned
    if name.endswith(".level"):
        return value == Level.unspecified
    return value is None


def _cells_match(name: str, gold: object, prediction: object) -> bool:
    gold_empty = _is_empty(name, gold)
    prediction_empty = _is_empty(name, prediction)
    if gold_empty or prediction_empty:
        return gold_empty and prediction_empty and _same_value(name, gold, prediction)
    return _same_value(name, gold, prediction)


def _same_value(name: str, gold: object, prediction: object) -> bool:
    if name == "city":
        return _city(gold) == _city(prediction)
    if name in SKILL_FIELDS:
        return _skill_set(gold) == _skill_set(prediction)
    return gold == prediction


def _city(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    return value.strip().lower()


def _skill_set(value: object) -> set[str]:
    if not isinstance(value, (tuple, list)):
        return set()
    return {item.strip().lower() for item in value}
