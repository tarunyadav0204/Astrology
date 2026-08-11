#!/usr/bin/env python3
"""Parse backend application sources without importing them or writing bytecode."""

from __future__ import annotations

import sys
from pathlib import Path


SKIP_DIRECTORIES = {".git", ".mypy_cache", ".pytest_cache", ".venv", "__pycache__", "venv"}
# Historical artifact retained for reference; it is not importable application code.
SKIP_FILES = {"wealth_routes_broken.py"}


def iter_sources(root: Path):
    for path in root.rglob("*.py"):
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRECTORIES for part in relative_parts):
            continue
        if path.name in SKIP_FILES:
            continue
        yield path


def main() -> int:
    backend_root = Path(sys.argv[1] if len(sys.argv) > 1 else "backend").resolve()
    failures: list[str] = []
    checked = 0

    for path in iter_sources(backend_root):
        checked += 1
        try:
            source = path.read_bytes()
            compile(source, str(path), "exec", dont_inherit=True)
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path}: {exc}")

    if failures:
        print("Backend syntax errors detected:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"Validated Python syntax in {checked} backend source files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
