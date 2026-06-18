import json
from typing import Any, Dict, Iterable, Optional

from db import execute


def ensure_chart_response_cache_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS chart_response_cache (
            cache_key TEXT PRIMARY KEY,
            birth_hash TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_chart_response_cache_birth_hash ON chart_response_cache (birth_hash)",
    )


def build_chart_cache_key(kind: str, birth_hash: str, **parts: Any) -> str:
    if not parts:
        return f"{kind}:{birth_hash}"
    normalized = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return f"{kind}:{birth_hash}:{normalized}"


def fetch_cached_chart_payload(conn, cache_key: str) -> Optional[Dict[str, Any]]:
    ensure_chart_response_cache_table(conn)
    cur = execute(
        conn,
        """
        SELECT payload_json
        FROM chart_response_cache
        WHERE cache_key = %s
        LIMIT 1
        """,
        (cache_key,),
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def store_chart_payload(conn, cache_key: str, birth_hash: str, payload: Dict[str, Any]) -> None:
    ensure_chart_response_cache_table(conn)
    execute(
        conn,
        """
        INSERT INTO chart_response_cache (cache_key, birth_hash, payload_json, updated_at)
        VALUES (%s, %s, %s, NOW())
        ON CONFLICT (cache_key) DO UPDATE SET
            birth_hash = EXCLUDED.birth_hash,
            payload_json = EXCLUDED.payload_json,
            updated_at = NOW()
        """,
        (cache_key, birth_hash, json.dumps(payload, default=str)),
    )


def delete_chart_cache_for_birth_hashes(conn, birth_hashes: Iterable[Optional[str]]) -> None:
    hashes = [h for h in birth_hashes if h]
    if not hashes:
        return
    ensure_chart_response_cache_table(conn)
    execute(
        conn,
        "DELETE FROM chart_response_cache WHERE birth_hash = ANY(%s)",
        (hashes,),
    )
