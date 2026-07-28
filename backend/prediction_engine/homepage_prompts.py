from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from db import execute, get_conn


HOMEPAGE_PROMPT_KEYS = frozenset({
    "first_free_question",
    "monthly_events",
})


class HomepagePromptRepository:
    def state(self, userid: int) -> Dict[str, Optional[Dict[str, Any]]]:
        with get_conn() as conn:
            rows = execute(
                conn,
                """
                SELECT prompt_key, first_shown_at, last_shown_at,
                       shown_count, last_session_id
                FROM homepage_prompt_exposures
                WHERE userid = %s
                """,
                (userid,),
            ).fetchall()
        state: Dict[str, Optional[Dict[str, Any]]] = {
            key: None for key in HOMEPAGE_PROMPT_KEYS
        }
        for prompt_key, first_shown, last_shown, count, session_id in rows:
            state[str(prompt_key)] = {
                "first_shown_at": _iso(first_shown),
                "last_shown_at": _iso(last_shown),
                "shown_count": int(count or 0),
                "last_session_id": str(session_id or "") or None,
            }
        return state

    def record_shown(
        self,
        *,
        userid: int,
        prompt_key: str,
        session_id: Optional[str],
    ) -> Dict[str, Any]:
        if prompt_key not in HOMEPAGE_PROMPT_KEYS:
            raise ValueError(f"Unsupported homepage prompt: {prompt_key}")
        with get_conn() as conn:
            row = execute(
                conn,
                """
                INSERT INTO homepage_prompt_exposures (
                    userid, prompt_key, first_shown_at, last_shown_at,
                    shown_count, last_session_id, updated_at
                )
                VALUES (
                    %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                    1, %s, CURRENT_TIMESTAMP
                )
                ON CONFLICT (userid, prompt_key) DO UPDATE SET
                    last_shown_at = CURRENT_TIMESTAMP,
                    shown_count = homepage_prompt_exposures.shown_count + 1,
                    last_session_id = EXCLUDED.last_session_id,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING first_shown_at, last_shown_at,
                          shown_count, last_session_id
                """,
                (userid, prompt_key, session_id),
            ).fetchone()
            conn.commit()
        return {
            "first_shown_at": _iso(row[0]),
            "last_shown_at": _iso(row[1]),
            "shown_count": int(row[2] or 0),
            "last_session_id": str(row[3] or "") or None,
        }


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)
