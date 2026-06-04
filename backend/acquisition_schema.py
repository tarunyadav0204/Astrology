"""
Idempotent Postgres DDL for the mobile install / acquisition funnel.
Statements are loaded from migrations/add_app_installations.sql so ops can still run the file manually.
"""

from __future__ import annotations

import logging
import os
import re

from db import execute, get_conn

logger = logging.getLogger(__name__)

_SQL_REL_PATH = os.path.join("migrations", "add_app_installations.sql")


def _sql_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _SQL_REL_PATH)


def _split_sql_statements(raw: str) -> list[str]:
    """Strip full-line -- comments, then split on semicolons (no ?/params in this migration)."""
    lines: list[str] = []
    for line in raw.splitlines():
        if re.match(r"^\s*--", line):
            continue
        lines.append(line)
    text = "\n".join(lines)
    parts: list[str] = []
    for chunk in text.split(";"):
        s = chunk.strip()
        if s:
            parts.append(s)
    return parts


def ensure_app_installations_schema() -> None:
    """
    Create app_installations and indexes if missing. Safe on every backend start.
    Uses CREATE IF NOT EXISTS only; does not alter existing table definitions.
    """
    path = _sql_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        logger.warning("Could not read app_installations migration file %s: %s", path, e)
        return

    statements = _split_sql_statements(raw)
    if not statements:
        logger.warning("No SQL statements parsed from %s", path)
        return

    try:
        with get_conn() as conn:
            for stmt in statements:
                execute(conn, stmt)
            conn.commit()
    except Exception as e:
        logger.warning("Could not ensure app_installations schema: %s", e)
