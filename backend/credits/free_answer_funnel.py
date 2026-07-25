"""Funnel for free-answer detail blur → reveal CTA → credit purchase conversion."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from db import execute, get_conn

logger = logging.getLogger(__name__)

VALID_EVENTS = frozenset({"blur_shown", "reveal_clicked", "converted"})
CONVERSION_WINDOW = timedelta(days=7)
_ADMIN_TZ = "Asia/Kolkata"


def ensure_free_answer_funnel_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS free_answer_funnel_events (
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
        CREATE INDEX IF NOT EXISTS idx_free_answer_funnel_user_event_created
        ON free_answer_funnel_events (userid, event_name, created_at DESC)
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_free_answer_funnel_user_msg_event
        ON free_answer_funnel_events (userid, (COALESCE(message_id, '')), event_name)
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
    plat = str(platform or "").strip() or None
    if plat:
        plat = plat[:40]
    with get_conn() as conn:
        ensure_free_answer_funnel_table(conn)
        try:
            cur = execute(
                conn,
                """
                INSERT INTO free_answer_funnel_events (userid, message_id, event_name, platform)
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
            # Unique index on COALESCE may not work with ON CONFLICT DO NOTHING without a constraint name.
            conn.rollback()
            cur = execute(
                conn,
                """
                SELECT 1 FROM free_answer_funnel_events
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
                INSERT INTO free_answer_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, ?, ?)
                """,
                (uid, mid, name, plat),
            )
            conn.commit()
            return True


def mark_converted_after_purchase(userid: int) -> int:
    """
    Attribute a purchase to the user's most recent reveal click within seven days.

    One purchase is one conversion; it must not convert every blurred answer the
    user happened to open during the attribution window.
    """
    uid = int(userid)
    since = datetime.now(timezone.utc) - CONVERSION_WINDOW
    inserted = 0
    with get_conn() as conn:
        ensure_free_answer_funnel_table(conn)
        cur = execute(
            conn,
            """
            SELECT message_id
            FROM free_answer_funnel_events
            WHERE userid = ?
              AND event_name = 'reveal_clicked'
              AND created_at >= ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (uid, since),
        )
        row = cur.fetchone()
        if not row:
            return 0
        mid = row[0]

        cur = execute(
            conn,
            """
            SELECT 1 FROM free_answer_funnel_events
            WHERE userid = ?
              AND COALESCE(message_id, '') = COALESCE(?, '')
              AND event_name = 'converted'
            LIMIT 1
            """,
            (uid, mid),
        )
        if cur.fetchone():
            return 0
        execute(
            conn,
            """
            INSERT INTO free_answer_funnel_events (userid, message_id, event_name, platform)
            VALUES (?, ?, 'converted', 'purchase')
            """,
            (uid, mid),
        )
        inserted = 1
        conn.commit()
    return inserted


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
    Cohort funnel keyed by recorded blurred-detail impressions.

    Date range filters when the blur impression was recorded (IST calendar day).
    Reveal and purchase count only when they match the same user and source
    message; they may occur after the selected range.
    """
    date_clauses, date_params = _inclusive_date_clause(
        from_date, to_date, "s.created_at"
    )
    cohort_where = " AND ".join(["s.event_name = 'blur_shown'", *date_clauses])

    with get_conn() as conn:
        ensure_free_answer_funnel_table(conn)

        cur = execute(
            conn,
            f"""
            SELECT COUNT(DISTINCT s.userid) AS users, COUNT(*) AS events
            FROM free_answer_funnel_events s
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
                SELECT COUNT(DISTINCT s.userid) AS users, COUNT(*) AS events
                FROM free_answer_funnel_events s
                INNER JOIN free_answer_funnel_events e
                  ON e.userid = s.userid
                 AND COALESCE(e.message_id, '') = COALESCE(s.message_id, '')
                 AND e.event_name = ?
                WHERE {cohort_where}
                """,
                (event_name, *date_params),
            )
            row = cur2.fetchone() or (0, 0)
            return int(row[0] or 0), int(row[1] or 0)

        reveal_users, reveal_events = _progress("reveal_clicked")
        converted_users, converted_events = _progress("converted")

        steps: List[Dict[str, Any]] = [
            {
                "event_name": "blur_shown",
                "label": "Saw blurred detail",
                "unique_users": shown_users,
                "events": shown_events,
            },
            {
                "event_name": "reveal_clicked",
                "label": "Tapped reveal",
                "unique_users": reveal_users,
                "events": reveal_events,
            },
            {
                "event_name": "converted",
                "label": "Purchased credits",
                "unique_users": converted_users,
                "events": converted_events,
            },
        ]

        base = shown_users or 0
        for step in steps:
            users = step["unique_users"]
            step["conversion_from_blur_pct"] = (
                round(100.0 * users / base, 1) if base > 0 else None
            )

        cur = execute(
            conn,
            """
            SELECT MIN(created_at)
            FROM free_answer_funnel_events
            WHERE event_name = 'blur_shown'
            """,
        )
        tracking_row = cur.fetchone()
        tracking_started_at = tracking_row[0] if tracking_row else None

        return {
            "from_date": from_date,
            "to_date": to_date,
            "timezone": _ADMIN_TZ,
            "tracking_started_at": tracking_started_at,
            "impression_source": "free_answer_funnel_events.blur_shown",
            "steps": steps,
            "reveal_to_purchase_pct": (
                round(100.0 * converted_users / reveal_users, 1) if reveal_users > 0 else None
            ),
        }
