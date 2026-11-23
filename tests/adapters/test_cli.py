"""Layer: test.
Role: Check command-line exit codes through the real composition root.
Depends on: the standard library, the inbound adapter, and domain.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from jobwatch_intake.adapters.inbound.dto import GoldLabelFileDTO

ROOT = Path(__file__).resolve().parents[2]
BODY = (
    "Junior Data Engineer at Example Analytics Oy. You will build and maintain data pipelines "
    "with Python and SQL. Good English is required, Finnish is a plus. Apply by mid December."
)


def draft(tmp_path: Path, name: str = "d.txt", body: str = BODY, **overrides) -> Path:
    fields = {
        "source": "example-board",
        "url": "https://example.invalid/jobs/1",
        "language": "en",
        "title": "Junior Data Engineer",
        "company": "Example Analytics Oy",
        "location": "Helsinki",
        "published_at": "2026-11-18",
        "deadline": "2026-12-15",
    }
    fields.update(overrides)
    head = "\n".join(f"{key}: {value}" for key, value in fields.items() if value is not None)
    path = tmp_path / name
    path.write_text(f"{head}\n---\n{body}", encoding="utf-8")
    return path


def run(tmp_path: Path, draft_path: Path, *extra: str):
    out = tmp_path / "out"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "jobwatch_intake", str(draft_path), "--out", str(out), *extra],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result.returncode, out, result.stdout, result.stderr


def test_valid_english_posting_is_saved(tmp_path: Path):
    code, out, stdout, stderr = run(tmp_path, draft(tmp_path))
    assert code == 0, stderr
    files = list(out.glob("job-*.json"))
    assert len(files) == 1
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["company"] == "Example Analytics Oy"
    assert data["deadline"] == "2026-12-15"
    assert data["id"] == files[0].stem
    assert "Saved" in stdout


def test_finnish_letters_round_trip(tmp_path: Path):
    # Intentional non-ASCII test data: Finnish letters must survive ensure_ascii=False.
    body = "Ohjelmistokehittäjä backend-tiimiin Tampereelle. Työskentelet Kotlinilla ja Pythonilla, " * 2
    code, out, _, stderr = run(
        tmp_path,
        draft(
            tmp_path,
            body=body,
            language="fi",
            title="Ohjelmistokehittäjä",
            url="https://example.invalid/jobs/2",
        ),
    )
    assert code == 0, stderr
    raw = next(out.glob("*.json")).read_text(encoding="utf-8")
    assert "Ohjelmistokehittäjä" in raw
    assert json.loads(raw)["title"] == "Ohjelmistokehittäjä"


def test_missing_company_exit_1(tmp_path: Path):
    code, out, _, stderr = run(tmp_path, draft(tmp_path, company=None))
    assert code == 1
    assert "company" in stderr
    assert "Invalid job posting" in stderr
    assert not out.exists() or not list(out.glob("*.json"))


def test_deadline_before_published_exit_1(tmp_path: Path):
    code, _, _, stderr = run(
        tmp_path, draft(tmp_path, published_at="2026-12-20", deadline="2026-12-01")
    )
    assert code == 1
    assert "(whole posting)" in stderr


def test_unknown_header_key_exit_1(tmp_path: Path):
    code, _, _, stderr = run(tmp_path, draft(tmp_path, salary="3000"))
    assert code == 1
    assert "salary" in stderr


def test_text_too_short_exit_1(tmp_path: Path):
    code, _, _, stderr = run(tmp_path, draft(tmp_path, body="Too short."))
    assert code == 1
    assert "text" in stderr


def test_bad_language_exit_1(tmp_path: Path):
    code, _, _, _ = run(tmp_path, draft(tmp_path, language="de"))
    assert code == 1


def test_missing_separator_exit_2(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("source: x\ntitle: y\n" + BODY, encoding="utf-8")
    code, _, _, stderr = run(tmp_path, path)
    assert code == 2
    assert "Could not read the draft file" in stderr


def test_header_line_without_colon_exit_2(tmp_path: Path):
    path = tmp_path / "bad.txt"
    path.write_text("source x\n---\n" + BODY, encoding="utf-8")
    code, _, _, stderr = run(tmp_path, path)
    assert code == 2
    assert "Could not read the draft file" in stderr


def test_missing_file_exit_2(tmp_path: Path):
    code, _, _, stderr = run(tmp_path, tmp_path / "missing.txt")
    assert code == 2
    assert "Could not read the draft file" in stderr


def test_not_utf8_exit_2(tmp_path: Path):
    path = tmp_path / "latin1.txt"
    path.write_bytes("source: x\n---\nÄÖ".encode("latin-1"))
    code, _, _, stderr = run(tmp_path, path)
    assert code == 2
    assert "Could not read the draft file" in stderr


def test_second_run_is_idempotent(tmp_path: Path):
    path = draft(tmp_path)
    code1, out, _, stderr1 = run(tmp_path, path)
    assert code1 == 0, stderr1
    first = next(out.glob("*.json")).read_text(encoding="utf-8")
    code2, _, stdout, _ = run(tmp_path, path)
    assert code2 == 0
    assert len(list(out.glob("*.json"))) == 1
    assert next(out.glob("*.json")).read_text(encoding="utf-8") == first
    assert "Already saved" in stdout


def test_same_url_new_text_keeps_id_and_needs_force(tmp_path: Path):
    code, out, _, stderr = run(tmp_path, draft(tmp_path))
    assert code == 0, stderr
    changed = draft(tmp_path, name="d2.txt", body=BODY + " Update: deadline extended.")
    code, _, _, _ = run(tmp_path, changed)
    assert code == 0
    only = list(out.glob("*.json"))
    assert len(only) == 1
    assert "extended" not in only[0].read_text(encoding="utf-8")
    code, _, stdout, stderr = run(tmp_path, changed, "--force")
    assert code == 0, stderr
    assert "Saved" in stdout
    assert "extended" in only[0].read_text(encoding="utf-8")


def test_no_temp_file_left_behind(tmp_path: Path):
    code, out, _, stderr = run(tmp_path, draft(tmp_path))
    assert code == 0, stderr
    assert not list(out.glob("*.tmp"))


def test_verbose_logs_the_three_steps(tmp_path: Path):
    code, _, _, stderr = run(tmp_path, draft(tmp_path), "--verbose")
    assert code == 0
    assert "read " in stderr
    assert "valid:" in stderr
    assert "wrote " in stderr


def test_example_labels_validate_and_match_example_drafts(tmp_path: Path):
    expected = {
        "junior-data-engineer-helsinki.txt": "job-a1abfcca01d0",
        "ohjelmistokehittaja-tampere.txt": "job-f6c3dde722d5",
    }
    for draft_file in sorted((ROOT / "examples").glob("*.txt")):
        out = tmp_path / draft_file.stem
        code, _, _, stderr = _run_into(out, draft_file)
        assert code == 0, stderr
        job = json.loads(next(out.glob("*.json")).read_text(encoding="utf-8"))
        assert job["id"] == expected[draft_file.name]
        label_file = ROOT / "examples" / "labels" / f"{job['id']}.json"
        assert label_file.exists(), f"missing label for {draft_file.name} ({job['id']})"
        gold = GoldLabelFileDTO.model_validate_json(
            label_file.read_text(encoding="utf-8")
        ).to_domain()
        assert gold.job_id == job["id"]
        assert gold.deadline is not None
        assert gold.deadline.isoformat() == job["deadline"]


def _run_into(out: Path, draft_path: Path):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "jobwatch_intake", str(draft_path), "--out", str(out)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    return result.returncode, out, result.stdout, result.stderr
