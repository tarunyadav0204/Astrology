"""Funnel for remedy CTA card → tap → remedy-only response."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from db import execute, get_conn

logger = logging.getLogger(__name__)

VALID_EVENTS = frozenset({"card_shown", "card_clicked", "remedy_delivered"})
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


def ensure_remedy_funnel_schema() -> None:
    """Startup/deployment fallback; never call this from an analytics request."""
    with get_conn() as conn:
        ensure_remedy_funnel_table(conn)
        conn.commit()


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
    if name == "card_shown":
        # One exposure per user/day, regardless of how many historical answers
        # with remedy cards are mounted by this or an older client.
        local_day = datetime.now(ZoneInfo(_ADMIN_TZ)).date().isoformat()
        mid = f"chat_screen:{local_day}"
    plat = (str(platform or "").strip() or None)
    if plat:
        plat = plat[:40]
    with get_conn() as conn:
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


def _inclusive_date_clause(
    from_date: Optional[str],
    to_date: Optional[str],
    col: str,
) -> Tuple[List[str], List[Any]]:
    """Inclusive IST calendar-day filter for a TIMESTAMPTZ event column."""
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
    Cohort funnel keyed by recorded remedy-card impressions.

    Date range filters when the card impression was recorded (IST calendar day).
    A card impression is recorded once per chat session/day. Clicks and remedy
    delivery are therefore matched to the exposed user after that exposure,
    rather than to every remedy-bearing answer message.
    """
    date_clauses, date_params = _inclusive_date_clause(
        from_date, to_date, "s.created_at"
    )
    cohort_where = " AND ".join(["s.event_name = 'card_shown'", *date_clauses])

    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT
                COUNT(DISTINCT s.userid) AS users,
                COUNT(
                    DISTINCT (
                        s.userid,
                        (s.created_at AT TIME ZONE '{_ADMIN_TZ}')::date
                    )
                ) AS events
            FROM remedy_funnel_events s
            WHERE {cohort_where}
            """,
            tuple(date_params),
        )
        shown_row = cur.fetchone() or (0, 0)

        shown_users = int(shown_row[0] or 0)
        shown_events = int(shown_row[1] or 0)

        def _progress(event_name: str) -> Tuple[int, int]:
            cur2 = execute(
                conn,
                f"""
                WITH shown_cohort AS (
                    SELECT s.userid, MIN(s.created_at) AS first_shown_at
                    FROM remedy_funnel_events s
                    WHERE {cohort_where}
                    GROUP BY s.userid
                )
                SELECT
                    COUNT(DISTINCT c.userid) AS users,
                    COUNT(DISTINCT e.id) AS events
                FROM shown_cohort c
                INNER JOIN remedy_funnel_events e
                  ON e.userid = c.userid
                 AND e.event_name = ?
                 AND e.created_at >= c.first_shown_at
                """,
                (*date_params, event_name),
            )
            row = cur2.fetchone() or (0, 0)
            return int(row[0] or 0), int(row[1] or 0)

        clicked_users, clicked_events = _progress("card_clicked")
        delivered_users, delivered_events = _progress("remedy_delivered")

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

        cur = execute(
            conn,
            """
            SELECT MIN(created_at)
            FROM remedy_funnel_events
            WHERE event_name = 'card_shown'
            """,
        )
        tracking_row = cur.fetchone()
        tracking_started_at = tracking_row[0] if tracking_row else None

        return {
            "from_date": from_date,
            "to_date": to_date,
            "timezone": _ADMIN_TZ,
            "tracking_started_at": tracking_started_at,
            "impression_source": "remedy_funnel_events.card_shown",
            "steps": steps,
            "click_to_delivered_pct": (
                round(100.0 * delivered_users / clicked_users, 1) if clicked_users > 0 else None
            ),
        }
