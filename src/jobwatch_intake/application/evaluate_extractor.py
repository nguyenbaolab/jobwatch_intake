"""Layer: application.
Role: Join gold labels with predictions and return the score report.
Depends on: the standard library, domain, and the ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from jobwatch_intake.application.ports import PredictionSource
from jobwatch_intake.domain.gold_label import GoldLabel
from jobwatch_intake.domain.scoring import Extraction, ScoreReport, score_pairs


class DuplicatePrediction(Exception):
    """The source returned the same job_id twice."""

    def __init__(self, job_id: str):
        self.job_id = job_id
        super().__init__(f"prediction job_id appears twice: {job_id}")


@dataclass(frozen=True)
class Evaluation:
    scores: ScoreReport
    missing_predictions: tuple[str, ...]
    unlabeled_predictions: tuple[str, ...]


class EvaluateExtractor:
    def __init__(self, source: PredictionSource):
        self._source = source

    def execute(self, labels: Sequence[GoldLabel]) -> Evaluation:
        by_id: dict[str, Extraction] = {}
        for item in self._source.predict(labels):
            if item.job_id in by_id:
                raise DuplicatePrediction(item.job_id)
            by_id[item.job_id] = item
        gold_ids = {label.job_id for label in labels}
        missing = tuple(label.job_id for label in labels if label.job_id not in by_id)
        unlabeled = tuple(job_id for job_id in by_id if job_id not in gold_ids)
        pairs = [(label, by_id.get(label.job_id)) for label in labels]
        return Evaluation(
            scores=score_pairs(pairs),
            missing_predictions=missing,
            unlabeled_predictions=unlabeled,
        )
