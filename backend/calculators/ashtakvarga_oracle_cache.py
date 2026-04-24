"""Cache + history for Ashtakavarga oracle analyses."""
import hashlib
import json
from typing import Any, Dict, List, Optional

from db import execute


def normalize_question_text(question_text: Optional[str]) -> str:
    return " ".join(str(question_text or "").strip().lower().split())


def oracle_cache_key(
    birth_hash: str,
    date: str,
    chart_type: str,
    query_type: str,
    question_text: Optional[str],
) -> str:
    normalized_question = normalize_question_text(question_text)
    raw = f"{birth_hash}|{date}|{chart_type}|{query_type}|{normalized_question}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_oracle_history_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_ashtakavarga_oracle_history (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            birth_hash TEXT NOT NULL,
            oracle_key TEXT NOT NULL,
            date_key TEXT NOT NULL,
            chart_type TEXT NOT NULL,
            query_type TEXT NOT NULL,
            question_text TEXT,
            response_payload TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, oracle_key)
        )
        """,
    )


def fetch_cached_oracle_payload(conn, userid: int, oracle_key: str) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT response_payload
        FROM ai_ashtakavarga_oracle_history
        WHERE userid = ? AND oracle_key = ?
        """,
        (userid, oracle_key),
    )
    row = cur.fetchone()
    if not row or not row[0]:
        return None
    try:
        return json.loads(row[0])
    except (json.JSONDecodeError, TypeError):
        return None


def fetch_oracle_history_item(conn, userid: int, analysis_id: int) -> Optional[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT id, oracle_key, date_key, chart_type, query_type, question_text, response_payload, updated_at
        FROM ai_ashtakavarga_oracle_history
        WHERE userid = ? AND id = ?
        """,
        (userid, analysis_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    try:
        payload = json.loads(row[6]) if row[6] else None
    except (json.JSONDecodeError, TypeError):
        payload = None
    return {
        "id": row[0],
        "oracle_key": row[1],
        "date": row[2],
        "chart_type": row[3],
        "query_type": row[4],
        "question_text": row[5] or "",
        "response_payload": payload,
        "updated_at": str(row[7]) if row[7] is not None else None,
    }


def store_oracle_payload(
    conn,
    userid: int,
    birth_hash: str,
    oracle_key: str,
    date_key: str,
    chart_type: str,
    query_type: str,
    question_text: Optional[str],
    payload: Dict[str, Any],
) -> None:
    execute(
        conn,
        """
        INSERT INTO ai_ashtakavarga_oracle_history (
            userid, birth_hash, oracle_key, date_key, chart_type, query_type, question_text, response_payload, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT (userid, oracle_key) DO UPDATE SET
            response_payload = EXCLUDED.response_payload,
            question_text = EXCLUDED.question_text,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            userid,
            birth_hash,
            oracle_key,
            date_key,
            chart_type,
            query_type,
            question_text or "",
            json.dumps(payload, default=str),
        ),
    )


def list_oracle_history(conn, userid: int, birth_hash: str, limit: int = 25) -> List[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT id, oracle_key, date_key, chart_type, query_type, question_text, response_payload, updated_at
        FROM ai_ashtakavarga_oracle_history
        WHERE userid = ? AND birth_hash = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (userid, birth_hash, limit),
    )
    rows = cur.fetchall() or []
    results: List[Dict[str, Any]] = []
    for row in rows:
        payload = None
        try:
            payload = json.loads(row[5]) if row[5] else None
        except (json.JSONDecodeError, TypeError):
            payload = None
        results.append(
            {
                "id": row[0],
                "oracle_key": row[1],
                "date": row[2],
                "chart_type": row[3],
                "query_type": row[4],
                "question_text": row[5] or "",
                "response_payload": payload,
                "updated_at": str(row[7]) if row[7] is not None else None,
            }
        )
    return results


def list_user_oracle_history(conn, userid: int, limit: int = 50) -> List[Dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT id, oracle_key, date_key, chart_type, query_type, question_text, response_payload, updated_at
        FROM ai_ashtakavarga_oracle_history
        WHERE userid = ?
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (userid, limit),
    )
    rows = cur.fetchall() or []
    results: List[Dict[str, Any]] = []
    for row in rows:
        payload = None
        try:
            payload = json.loads(row[6]) if row[6] else None
        except (json.JSONDecodeError, TypeError):
            payload = None
        results.append(
            {
                "id": row[0],
                "oracle_key": row[1],
                "date": row[2],
                "chart_type": row[3],
                "query_type": row[4],
                "question_text": row[5] or "",
                "response_payload": payload,
                "updated_at": str(row[7]) if row[7] is not None else None,
            }
        )
    return results
