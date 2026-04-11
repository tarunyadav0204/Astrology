"""DB cache for Ashtakavarga life predictions (Dots of Destiny) — keyed by user + birth fingerprint."""
import hashlib
import json
from typing import Any, Dict, Optional

from db import execute


def birth_fingerprint(birth_data: Dict[str, Any]) -> str:
    """Stable hash for cache key (same chart = same fingerprint)."""
    try:
        lat = round(float(birth_data.get("latitude") or 0), 5)
        lon = round(float(birth_data.get("longitude") or 0), 5)
    except (TypeError, ValueError):
        lat, lon = 0.0, 0.0
    date_s = str(birth_data.get("date") or "").strip()
    time_s = str(birth_data.get("time") or "").strip()
    raw = f"{date_s}|{time_s}|{lat}|{lon}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_life_predictions_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_ashtakavarga_life_predictions (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            birth_hash TEXT NOT NULL,
            response_payload TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, birth_hash)
        )
        """,
    )


def fetch_cached_payload(conn, userid: int, birth_hash: str) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT response_payload
        FROM ai_ashtakavarga_life_predictions
        WHERE userid = ? AND birth_hash = ?
        """,
        (userid, birth_hash),
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None


def store_life_predictions_cache(conn, userid: int, birth_hash: str, payload: Dict[str, Any]) -> None:
    execute(
        conn,
        """
        INSERT INTO ai_ashtakavarga_life_predictions (userid, birth_hash, response_payload, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT (userid, birth_hash) DO UPDATE SET
            response_payload = EXCLUDED.response_payload,
            updated_at = CURRENT_TIMESTAMP
        """,
        (userid, birth_hash, json.dumps(payload, default=str)),
    )


def prediction_payload_is_successful(predictions: Any) -> bool:
    """True if Gemini returned usable content (no top-level error key)."""
    if not isinstance(predictions, dict):
        return False
    err = predictions.get("error")
    if err is None:
        return True
    if isinstance(err, str) and not err.strip():
        return True
    return False
