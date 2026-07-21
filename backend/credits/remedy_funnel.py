"""Funnel for remedy CTA card → tap → remedy-only response."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from db import execute, get_conn

logger = logging.getLogger(__name__)

VALID_EVENTS = frozenset({"card_shown", "card_clicked", "remedy_delivered"})


def ensure_remedy_funnel_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS remedy_funnel_events (
            id BIGSERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            message_id TEXT,
            event_name TEXT NOT NULL,
            platform TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE INDEX IF NOT EXISTS idx_remedy_funnel_user_event_created
        ON remedy_funnel_events (userid, event_name, created_at DESC)
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_remedy_funnel_user_msg_event
        ON remedy_funnel_events (userid, (COALESCE(message_id, '')), event_name)
        """,
    )


def record_funnel_event(
    *,
    userid: int,
    event_name: str,
    message_id: Optional[str] = None,
    platform: Optional[str] = None,
) -> bool:
    """Idempotent per (userid, message_id, event). Returns True if a new row was inserted."""
    name = str(event_name or "").strip().lower()
    if name not in VALID_EVENTS:
        raise ValueError(f"invalid event_name={event_name!r}")
    uid = int(userid)
    mid = (str(message_id or "").strip() or None)
    plat = (str(platform or "").strip() or None)
    if plat:
        plat = plat[:40]
    with get_conn() as conn:
        ensure_remedy_funnel_table(conn)
        try:
            cur = execute(
                conn,
                """
                INSERT INTO remedy_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, ?, ?)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (uid, mid, name, plat),
            )
            row = cur.fetchone()
            conn.commit()
            return bool(row)
        except Exception:
            conn.rollback()
            cur = execute(
                conn,
                """
                SELECT 1 FROM remedy_funnel_events
                WHERE userid = ?
                  AND COALESCE(message_id, '') = COALESCE(?, '')
                  AND event_name = ?
                LIMIT 1
                """,
                (uid, mid, name),
            )
            if cur.fetchone():
                return False
            execute(
                conn,
                """
                INSERT INTO remedy_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, ?, ?)
                """,
                (uid, mid, name, plat),
            )
            conn.commit()
            return True


def get_funnel_analytics(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    clauses = ["1=1"]
    params: List[Any] = []
    if from_date:
        clauses.append("created_at >= ?::timestamptz")
        params.append(f"{from_date}T00:00:00+00:00")
    if to_date:
        clauses.append("created_at < (?::date + INTERVAL '1 day')")
        params.append(to_date)
    where = " AND ".join(clauses)

    with get_conn() as conn:
        ensure_remedy_funnel_table(conn)
        steps: List[Dict[str, Any]] = []
        for event_name, label in (
            ("card_shown", "Saw remedy card"),
            ("card_clicked", "Tapped remedy CTA"),
            ("remedy_delivered", "Got remedy-only answer"),
        ):
            cur = execute(
                conn,
                f"""
                SELECT COUNT(DISTINCT userid) AS users, COUNT(*) AS events
                FROM remedy_funnel_events
                WHERE {where} AND event_name = ?
                """,
                (*params, event_name),
            )
            row = cur.fetchone() or (0, 0)
            steps.append(
                {
                    "event_name": event_name,
                    "label": label,
                    "unique_users": int(row[0] or 0),
                    "events": int(row[1] or 0),
                }
            )

        base = steps[0]["unique_users"] or 0
        for step in steps:
            users = step["unique_users"]
            step["conversion_from_card_shown_pct"] = (
                round(100.0 * users / base, 1) if base > 0 else None
            )

        clicked_users = steps[1]["unique_users"] or 0
        delivered_users = steps[2]["unique_users"] or 0
        return {
            "from_date": from_date,
            "to_date": to_date,
            "steps": steps,
            "click_to_delivered_pct": (
                round(100.0 * delivered_users / clicked_users, 1) if clicked_users > 0 else None
            ),
        }
