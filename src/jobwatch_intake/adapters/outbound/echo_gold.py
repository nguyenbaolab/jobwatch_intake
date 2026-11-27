"""Layer: adapters.outbound.
Role: Fake extractor that returns the gold fields as an Extraction.
Depends on: the standard library and domain.
"""

from __future__ import annotations

from typing import Sequence

from jobwatch_intake.domain.gold_label import GoldLabel
from jobwatch_intake.domain.scoring import Extraction


class EchoGoldExtractor:
    def predict(self, labels: Sequence[GoldLabel]) -> tuple[Extraction, ...]:
        return tuple(_copy(label) for label in labels)


def _copy(label: GoldLabel) -> Extraction:
    return Extraction(
        job_id=label.job_id,
        skills_required=label.skills_required,
        skills_preferred=label.skills_preferred,
        finnish=label.finnish,
        swedish=label.swedish,
        english=label.english,
        experience_years_min=label.experience_years_min,
        city=label.city,
        work_mode=label.work_mode,
        deadline=label.deadline,
    )
