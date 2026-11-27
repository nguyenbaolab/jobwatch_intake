"""Layer: test.
Role: Check the hand-scored example in EVAL_RULES.md section 7.
Depends on: domain.
"""

from datetime import date
from fractions import Fraction

from jobwatch_intake.domain.gold_label import (
    GoldLabel,
    LanguageNeed,
    Level,
    Requirement,
    WorkMode,
)
from jobwatch_intake.domain.scoring import Extraction, score_pairs

J1 = "job-000000000001"
J2 = "job-000000000002"
J3 = "job-000000000003"


def _gold(job_id: str, **overrides) -> GoldLabel:
    data = dict(
        job_id=job_id,
        labeler="example",
        labeled_at=date(2026, 11, 26),
    )
    data.update(overrides)
    return GoldLabel(**data)


def _section_7_pairs():
    return [
        (
            _gold(
                J1,
                experience_years_min=3,
                work_mode=WorkMode.hybrid,
                city="helsinki",
                skills_required=("python", "sql"),
            ),
            Extraction(
                J1,
                experience_years_min=3,
                work_mode=WorkMode.hybrid,
                city="Helsinki",
                skills_required=("sql", "python"),
            ),
        ),
        (
            _gold(J2, work_mode=WorkMode.remote, skills_required=("react",)),
            Extraction(
                J2,
                experience_years_min=2,
                work_mode=WorkMode.remote,
                skills_required=("react", "typescript"),
            ),
        ),
        (
            _gold(
                J3,
                experience_years_min=5,
                work_mode=WorkMode.onsite,
                city="espoo",
                skills_required=("java", "spring", "sql"),
            ),
            Extraction(
                J3,
                work_mode=WorkMode.onsite,
                city="espoo",
                skills_required=("java",),
            ),
        ),
    ]


def test_section_7_field_accuracy_matches_the_hand_score():
    report = score_pairs(_section_7_pairs())
    by_field = {row.field: row for row in report.fields}

    years = by_field["experience_years_min"]
    assert (years.correct, years.n) == (1, 3)
    assert (years.correct_nonempty, years.n_nonempty) == (1, 2)
    assert years.acc_all() == Fraction(1, 3)
    assert years.acc_gold_nonempty() == Fraction(1, 2)

    mode = by_field["work_mode"]
    assert (mode.correct, mode.n) == (3, 3)
    assert (mode.correct_nonempty, mode.n_nonempty) == (3, 3)
    assert mode.acc_all() == Fraction(3, 3)
    assert mode.acc_gold_nonempty() == Fraction(3, 3)

    city = by_field["city"]
    assert (city.correct, city.n) == (3, 3)
    assert (city.correct_nonempty, city.n_nonempty) == (2, 2)
    assert city.acc_all() == Fraction(3, 3)
    assert city.acc_gold_nonempty() == Fraction(2, 2)

    skills = by_field["skills_required"]
    assert (skills.correct, skills.n) == (1, 3)
    assert (skills.correct_nonempty, skills.n_nonempty) == (1, 3)
    assert skills.acc_all() == Fraction(1, 3)
    assert skills.acc_gold_nonempty() == Fraction(1, 3)


def test_section_7_skill_micro_scores_match_the_hand_score():
    report = score_pairs(_section_7_pairs())
    required = {row.field: row for row in report.skills}["skills_required"]
    assert (required.tp, required.predicted, required.gold) == (4, 5, 6)
    assert required.precision() == Fraction(4, 5)
    assert required.recall() == Fraction(4, 6)
    assert required.f1() == Fraction(8, 11)


def test_section_7_only_the_four_wrong_cells_are_listed():
    report = score_pairs(_section_7_pairs())
    assert [(row.job_id, row.field) for row in report.mismatches] == [
        (J2, "experience_years_min"),
        (J2, "skills_required"),
        (J3, "experience_years_min"),
        (J3, "skills_required"),
    ]


def test_a_bad_prediction_is_scored_instead_of_rejected():
    gold = _gold(
        J1,
        skills_required=("python",),
        skills_preferred=("sql",),
    )
    prediction = Extraction(
        J1,
        skills_required=("python", "python"),
        skills_preferred=("python",),
    )
    report = score_pairs([(gold, prediction)])
    required = {row.field: row for row in report.fields}["skills_required"]
    assert required.correct == 1
    preferred = {row.field: row for row in report.skills}["skills_preferred"]
    assert preferred.tp == 0
    assert preferred.predicted == 1
    assert preferred.gold == 1


def test_unspecified_and_not_mentioned_count_as_correct_and_nonempty_is_na():
    gold = _gold(
        J1,
        work_mode=WorkMode.unspecified,
        finnish=LanguageNeed(Requirement.not_mentioned, Level.unspecified),
    )
    prediction = Extraction(
        J1,
        work_mode=WorkMode.unspecified,
        finnish=LanguageNeed(Requirement.not_mentioned, Level.unspecified),
    )
    report = score_pairs([(gold, prediction)])
    by_field = {row.field: row for row in report.fields}
    for name in ("work_mode", "finnish.requirement"):
        row = by_field[name]
        assert (row.correct, row.n) == (1, 1)
        assert row.acc_all() == Fraction(1, 1)
        assert row.n_nonempty == 0
        assert row.acc_gold_nonempty() is None


def test_repeated_skill_in_prediction_is_scored():
    gold = _gold(J1, skills_required=("python",))
    prediction = Extraction(J1, skills_required=["python", "python"])
    report = score_pairs([(gold, prediction)])
    row = {item.field: item for item in report.fields}["skills_required"]
    assert row.correct == 1
    micro = {item.field: item for item in report.skills}["skills_required"]
    assert (micro.tp, micro.predicted, micro.gold) == (1, 1, 1)
