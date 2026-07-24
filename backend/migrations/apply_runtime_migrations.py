"""Apply idempotent PostgreSQL migrations required before the API restarts."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = Path(__file__).resolve().parent
RUNTIME_MIGRATIONS = (
    "add_astrologer_subscription.sql",
)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def apply_runtime_migrations() -> None:
    load_dotenv(BACKEND_DIR / ".env", override=False)

    from db import get_conn

    with get_conn() as conn:
        cursor = conn.cursor()
        for filename in RUNTIME_MIGRATIONS:
            sql_path = MIGRATIONS_DIR / filename
            sql = sql_path.read_text(encoding="utf-8")
            cursor.execute(sql)
            print(f"Applied runtime migration: {filename}")
        conn.commit()


if __name__ == "__main__":
    apply_runtime_migrations()
