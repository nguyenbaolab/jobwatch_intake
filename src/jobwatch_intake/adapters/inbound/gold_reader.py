"""Layer: adapters.inbound.
Role: Read a directory of gold-label files into GoldLabel objects.
Depends on: the standard library, pydantic, domain, and the inbound DTO.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO
from jobwatch_intake.domain.gold_label import GoldLabel, InvalidGoldLabel


class GoldReadError(Exception):
    """The label directory cannot be scored. The command stops."""


def read_gold_labels(directory: Path) -> list[GoldLabel]:
    if not directory.is_dir():
        raise GoldReadError(f"Label directory does not exist: {directory}")
    labels: list[GoldLabel] = []
    seen: dict[str, str] = {}
    for path in sorted(directory.glob("*.json")):
        labels.append(_read_one(path, seen))
    return labels


def _read_one(path: Path, seen: dict[str, str]) -> GoldLabel:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise GoldReadError(f"Could not read {path}: {exc}") from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GoldReadError(f"Invalid JSON in {path.name}: {exc}") from exc
    try:
        label = GoldLabelFileDTO.model_validate(payload).to_domain()
    except ValidationError as exc:
        raise GoldReadError(f"Invalid gold label {path.name}: {_shape(exc)}") from exc
    except InvalidGoldLabel as exc:
        raise GoldReadError(f"Invalid gold label {path.name}: {exc}") from exc
    if path.stem != label.job_id:
        raise GoldReadError(
            f"{path.name}: file name is '{path.stem}' but job_id is '{label.job_id}'"
        )
    previous = seen.get(label.job_id)
    if previous is not None:
        raise GoldReadError(
            f"Duplicate job_id {label.job_id} in {previous} and {path.name}"
        )
    seen[label.job_id] = path.name
    return label


def _shape(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"]) or "(whole file)"
        parts.append(f"{field}: {err['msg']}")
    return "; ".join(parts)
