"""Lớp: công cụ.
Vai trò: Sinh JSON Schema từ DTO của file tin đã lưu và file nhãn.
Phụ thuộc: thư viện chuẩn và các DTO.
"""

from __future__ import annotations

import json
from pathlib import Path

from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO
from jobwatch_intake.adapters.outbound.stored_job_dto import StoredJobDTO


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "schemas"
    out.mkdir(exist_ok=True)
    for name, model in (("job_posting", StoredJobDTO), ("gold_label", GoldLabelFileDTO)):
        schema = model.model_json_schema()
        destination = out / f"{name}.schema.json"
        destination.write_text(
            json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print("đã ghi", destination)


if __name__ == "__main__":
    main()
