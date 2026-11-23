# jobwatch_intake

Intake step of Jobwatch. It reads a job-posting draft, validates it, and stores one JSON file per posting.
It also defines a gold-label format so an extractor can be scored later. There is no extractor in this repository.

## Quickstart

Python 3.10 or newer.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m jobwatch_intake .\examples\junior-data-engineer-helsinki.txt --out .\data\jobs
python -m pytest -q
```

macOS and Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m jobwatch_intake examples/junior-data-engineer-helsinki.txt --out data/jobs
python -m pytest -q
```

## Usage

A draft is a few `key: value` lines, then one line that is only `---`, then the posting text. A line that starts with `#` is ignored. The first `---` separates the header from the text; a later `---` stays in the text. An empty value means the field is absent.

Keys: `source`, `url`, `language` (`fi`, `en`, or `sv`), `title`, `company`, `location`, `published_at`, `deadline`. Dates use `YYYY-MM-DD`. See `examples/`.

| Flag | Meaning |
|---|---|
| `--out DIR` | Directory for the JSON files. Default: `data/jobs`. |
| `--force` | Overwrite a posting that is already saved. |
| `--verbose` | Log the read, validate, and write steps at DEBUG. |

| Exit code | Meaning |
|---|---|
| 0 | Saved, or already saved and left unchanged. |
| 1 | The posting content is invalid. stderr shows `Invalid job posting (N errors):` and one `  - field: reason` line per error. Shape errors (missing field, wrong type, bad date, bad language, unknown field) are printed first. If the shape is valid and a business rule fails, every error from that pass is printed. |
| 2 | The draft could not be read or has the wrong shape (missing file, bad UTF-8, no `---` line, or a header line with no `:`). |

## Architecture

Dependencies point inward. Domain holds the business rules and uses only the standard library. Application holds the `SaveJob` use case and talks to the outside through `Protocol` ports. Adapters read the draft, print the CLI, and write JSON. `composition.py` is the only module that builds the concrete adapters. `__main__.py` is the only module that imports it.

Details, diagrams, and the per-file table: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Label rules: [docs/LABELING.md](docs/LABELING.md).

## Project layout

```
pyproject.toml          project metadata
src/jobwatch_intake/    library: domain, application, adapters, composition
tools/                  generate JSON Schema from the DTOs
schemas/                generated schema for a saved posting and a label
examples/               two draft postings and their labels
data/jobs/              saved postings (JSON is gitignored)
data/labels/            real labels, kept apart from the postings
docs/                   architecture and labeling rules
tests/                  domain, application, adapter, and architecture tests
```

## Testing

```powershell
python -m pytest -q
```

`tests/test_architecture.py` parses imports with `ast`. Domain may import only the standard library and other domain modules. Application may not import adapters or pydantic. Inbound and outbound adapters may not import each other. Nothing except `__main__.py` may import `composition`.

After a DTO description changes, regenerate the schema:

```powershell
python .\tools\make_schemas.py
```

## How this was built

I designed the architecture, validation rules and label format. Implementation was done with Cursor and Claude as coding assistants. I reviewed and can explain every file; see docs/ARCHITECTURE.md.
