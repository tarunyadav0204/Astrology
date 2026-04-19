"""Load birth_data dict from Postgres (latest birth_charts row per userid). Shared by tests and CLI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict


def load_backend_dotenv() -> None:
    """Load backend/.env then repo-root .env (override=False so shell exports win)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    backend_dir = Path(__file__).resolve().parent.parent
    for p in (backend_dir / ".env", backend_dir.parent / ".env"):
        if p.is_file():
            load_dotenv(p, override=False)


def fetch_latest_birth_for_user(user_id: int) -> Dict[str, Any]:
    """
    Latest birth_charts row for userid. Decrypts like main app.
    Raises RuntimeError if DB, key, or row is missing.
    """
    if not (os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")):
        raise RuntimeError("POSTGRES_DSN or DATABASE_URL not set")

    try:
        from encryption_utils import EncryptionManager

        encryptor = EncryptionManager()
    except ValueError as e:
        raise RuntimeError("ENCRYPTION_KEY not set — cannot decrypt birth_charts") from e

    from db import execute, get_conn

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT id, name, date, time, latitude, longitude, timezone, place, gender
            FROM birth_charts
            WHERE userid = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()

    if not row:
        raise RuntimeError(f"No birth_charts row for userid={user_id}")

    name = encryptor.decrypt(row[1])
    date = encryptor.decrypt(row[2])
    time = encryptor.decrypt(row[3])
    lat = float(encryptor.decrypt(str(row[4])))
    lon = float(encryptor.decrypt(str(row[5])))
    place = encryptor.decrypt(row[7])
    tz = row[6] or "UTC"

    return {
        "name": name,
        "date": date,
        "time": time,
        "latitude": lat,
        "longitude": lon,
        "timezone": tz,
        "place": place,
    }
