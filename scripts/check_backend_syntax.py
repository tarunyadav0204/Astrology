#!/usr/bin/env python3
"""Parse backend application sources without importing them or writing bytecode."""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path


SKIP_DIRECTORIES = {".git", ".mypy_cache", ".pytest_cache", ".venv", "__pycache__", "venv"}
# Historical artifact retained for reference; it is not importable application code.
SKIP_FILES = {"wealth_routes_broken.py"}


def git_tracked_sources(root: Path):
    """Return release-owned Python sources when root belongs to a Git checkout."""
    try:
        repo_root = Path(
            subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        ).resolve()
        relative_root = root.relative_to(repo_root)
        output = subprocess.check_output(
            ["git", "-C", str(repo_root), "ls-files", "-z", "--", str(relative_root)],
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None

    return [
        (repo_root / raw.decode("utf-8", errors="surrogateescape")).resolve()
        for raw in output.split(b"\0")
        if raw and raw.endswith(b".py")
    ]


def iter_sources(root: Path):
    # A production checkout can contain runtime or stale untracked artifacts.
    # `git reset --hard` intentionally leaves those files alone, but they are not
    # part of the release and must not make validation differ from CI checkout.
    candidates = git_tracked_sources(root)
    if candidates is None:
        candidates = root.rglob("*.py")

    for path in candidates:
        if not path.is_file():
            continue
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
        except (OSError, SyntaxError, ValueError) as exc:
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
