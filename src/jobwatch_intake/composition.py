"""Layer: composition.
Role: The only place that wires adapters into the use case.
Depends on: application and adapters.outbound.
"""

from __future__ import annotations

from pathlib import Path

from jobwatch_intake.adapters.outbound.json_job_repository import JsonJobRepository
from jobwatch_intake.adapters.outbound.system_clock import SystemClock
from jobwatch_intake.application.save_job import SaveJob


def make_save_job(out_dir: Path) -> SaveJob:
    return SaveJob(JsonJobRepository(out_dir), SystemClock())
