"""Funnel for remedy CTA card → tap → remedy-only response."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from db import execute, get_conn

logger = logging.getLogger(__name__)

VALID_EVENTS = frozenset({"card_shown", "card_clicked", "remedy_delivered"})
# Admin date filters use IST calendar days (product audience is primarily India).
_ADMIN_TZ = "Asia/Kolkata"


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


def _date_clause(from_date: Optional[str], to_date: Optional[str], col: str = "created_at"):
    clauses: List[str] = []
    params: List[Any] = []
    if from_date:
        clauses.append(f"({col} AT TIME ZONE '{_ADMIN_TZ}')::date >= ?::date")
        params.append(from_date)
    if to_date:
        clauses.append(f"({col} AT TIME ZONE '{_ADMIN_TZ}')::date <= ?::date")
        params.append(to_date)
    return clauses, params


def get_funnel_analytics(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cohort funnel keyed by remedy-card impressions.

    Date range filters when the card was *shown* (IST calendar day). Later steps
    count only matching (userid, message_id) that progressed — so tapped/delivered
    can never exceed saw. Clicks/deliveries after the range still count for
    impressions that entered in-range.
    """
    shown_clauses, shown_params = _date_clause(from_date, to_date, "s.created_at")
    shown_where = " AND ".join(["s.event_name = 'card_shown'", *shown_clauses])

    with get_conn() as conn:
        ensure_remedy_funnel_table(conn)

        # Impressions in range.
        cur = execute(
            conn,
            f"""
            SELECT COUNT(DISTINCT s.userid) AS users, COUNT(*) AS events
            FROM remedy_funnel_events s
            WHERE {shown_where}
            """,
            tuple(shown_params),
        )
        shown_row = cur.fetchone() or (0, 0)
        shown_users = int(shown_row[0] or 0)
        shown_events = int(shown_row[1] or 0)

        # Among those impressions, how many got a matching click (any time).
        cur = execute(
            conn,
            f"""
            SELECT
              COUNT(DISTINCT s.userid) AS users,
              COUNT(*) AS events
            FROM remedy_funnel_events s
            INNER JOIN remedy_funnel_events c
              ON c.userid = s.userid
             AND COALESCE(c.message_id, '') = COALESCE(s.message_id, '')
             AND c.event_name = 'card_clicked'
            WHERE {shown_where}
            """,
            tuple(shown_params),
        )
        clicked_row = cur.fetchone() or (0, 0)
        clicked_users = int(clicked_row[0] or 0)
        clicked_events = int(clicked_row[1] or 0)

        # Among those impressions, how many got a matching remedy-only answer (any time).
        cur = execute(
            conn,
            f"""
            SELECT
              COUNT(DISTINCT s.userid) AS users,
              COUNT(*) AS events
            FROM remedy_funnel_events s
            INNER JOIN remedy_funnel_events d
              ON d.userid = s.userid
             AND COALESCE(d.message_id, '') = COALESCE(s.message_id, '')
             AND d.event_name = 'remedy_delivered'
            WHERE {shown_where}
            """,
            tuple(shown_params),
        )
        delivered_row = cur.fetchone() or (0, 0)
        delivered_users = int(delivered_row[0] or 0)
        delivered_events = int(delivered_row[1] or 0)

        steps: List[Dict[str, Any]] = [
            {
                "event_name": "card_shown",
                "label": "Saw remedy card",
                "unique_users": shown_users,
                "events": shown_events,
            },
            {
                "event_name": "card_clicked",
                "label": "Tapped remedy CTA",
                "unique_users": clicked_users,
                "events": clicked_events,
            },
            {
                "event_name": "remedy_delivered",
                "label": "Got remedy-only answer",
                "unique_users": delivered_users,
                "events": delivered_events,
            },
        ]

        base = shown_users or 0
        for step in steps:
            users = step["unique_users"]
            step["conversion_from_card_shown_pct"] = (
                round(100.0 * users / base, 1) if base > 0 else None
            )

        return {
            "from_date": from_date,
            "to_date": to_date,
            "steps": steps,
            "click_to_delivered_pct": (
                round(100.0 * delivered_users / clicked_users, 1) if clicked_users > 0 else None
            ),
        }
