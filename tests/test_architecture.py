"""Layer: test.
Role: Scan imports with ast so the dependency rule between layers holds.
Depends on: the standard library.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE = SRC / "jobwatch_intake"
STDLIB = set(sys.stdlib_module_names) | {"__future__"}


def _python_files(folder: Path) -> list[Path]:
    return [path for path in folder.rglob("*.py") if "__pycache__" not in path.parts]


def _package_parts(path: Path) -> list[str] | None:
    try:
        relative = path.relative_to(SRC)
    except ValueError:
        return None
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        return parts[:-1]
    return parts[:-1]


def _imported(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = _package_parts(path)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.append(node.module)
        elif isinstance(node, ast.ImportFrom) and node.level:
            if package is None:
                raise AssertionError(f"{path} uses a relative import outside src")
            keep = package[: len(package) - (node.level - 1)]
            if node.module:
                found.append(".".join((*keep, node.module)))
            else:
                found.append(".".join(keep))
    return found


def test_domain_imports_only_stdlib_and_domain():
    for path in _python_files(PACKAGE / "domain"):
        for module in _imported(path):
            top = module.split(".", 1)[0]
            assert top in STDLIB or module.startswith("jobwatch_intake.domain"), (path, module)


def test_application_does_not_import_adapters_or_pydantic():
    for path in _python_files(PACKAGE / "application"):
        for module in _imported(path):
            assert "pydantic" not in module.split("."), (path, module)
            assert not module.startswith("jobwatch_intake.adapters"), (path, module)


def test_inbound_and_outbound_do_not_import_each_other():
    for path in _python_files(PACKAGE / "adapters" / "inbound"):
        for module in _imported(path):
            assert not module.startswith("jobwatch_intake.adapters.outbound"), (path, module)
    for path in _python_files(PACKAGE / "adapters" / "outbound"):
        for module in _imported(path):
            assert not module.startswith("jobwatch_intake.adapters.inbound"), (path, module)


def test_only_main_imports_composition():
    offenders: list[tuple[Path, str]] = []
    for folder in (PACKAGE, ROOT / "tests", ROOT / "tools"):
        for path in _python_files(folder):
            if path.name == "__main__.py":
                continue
            for module in _imported(path):
                if module == "jobwatch_intake.composition" or module.startswith(
                    "jobwatch_intake.composition."
                ):
                    offenders.append((path, module))
    assert offenders == []
