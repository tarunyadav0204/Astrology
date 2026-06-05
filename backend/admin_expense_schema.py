"""Idempotent DDL for admin internal expense log (see migrations/add_admin_company_expenses.sql)."""

from __future__ import annotations

import logging
import os
import re

from db import execute, get_conn

logger = logging.getLogger(__name__)

_SQL_REL_PATH = os.path.join("migrations", "add_admin_company_expenses.sql")


def _sql_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), _SQL_REL_PATH)


def _split_sql_statements(raw: str) -> list[str]:
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


def ensure_admin_company_expenses_schema() -> None:
    """Create admin_company_expenses + indexes if missing. Safe on every backend start."""
    path = _sql_path()
    try:
        with open(path, encoding="utf-8") as f:
            raw = f.read()
    except OSError as e:
        logger.warning("Could not read admin expenses migration file %s: %s", path, e)
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
        logger.warning("Could not ensure admin_company_expenses schema: %s", e)
