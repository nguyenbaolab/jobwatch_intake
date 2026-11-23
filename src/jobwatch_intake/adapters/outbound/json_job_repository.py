"""Layer: adapters.outbound.
Role: Write each posting to one JSON file, atomically.
Depends on: the standard library, domain, and the stored-job DTO.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from jobwatch_intake.adapters.outbound.stored_job_dto import StoredJobDTO
from jobwatch_intake.domain.job_posting import JobPosting

log = logging.getLogger("save_job")


class JsonJobRepository:
    def __init__(self, out_dir: Path):
        self._out_dir = out_dir

    def _target(self, job_id: str) -> Path:
        return self._out_dir / f"{job_id}.json"

    def exists(self, job_id: str) -> bool:
        return self._target(job_id).exists()

    def locate(self, job_id: str) -> str:
        return str(self._target(job_id))

    def save(self, job: JobPosting) -> str:
        self._out_dir.mkdir(parents=True, exist_ok=True)
        target = self._target(job.id)
        payload = (
            json.dumps(
                StoredJobDTO.from_job(job).model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        log.debug("wrote %s (%d bytes)", target, len(payload.encode("utf-8")))
        return str(target)
