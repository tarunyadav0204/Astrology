"""Funnel for free-answer detail blur → reveal CTA → credit purchase conversion."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from db import execute, get_conn

logger = logging.getLogger(__name__)

VALID_EVENTS = frozenset({"blur_shown", "reveal_clicked", "converted"})
CONVERSION_WINDOW = timedelta(days=7)


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
    plat = (str(platform or "").strip() or None)[:40]
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
    If the user clicked reveal recently, record a converted event (once per recent message).
    Returns number of new conversion rows.
    """
    uid = int(userid)
    since = datetime.now(timezone.utc) - CONVERSION_WINDOW
    inserted = 0
    with get_conn() as conn:
        ensure_free_answer_funnel_table(conn)
        cur = execute(
            conn,
            """
            SELECT DISTINCT message_id
            FROM free_answer_funnel_events
            WHERE userid = ?
              AND event_name = 'reveal_clicked'
              AND created_at >= ?
            """,
            (uid, since),
        )
        message_ids = [r[0] for r in (cur.fetchall() or [])]
        if not message_ids:
            # Still allow a user-level conversion with null message_id if they clicked reveal.
            cur = execute(
                conn,
                """
                SELECT 1 FROM free_answer_funnel_events
                WHERE userid = ? AND event_name = 'reveal_clicked' AND created_at >= ?
                LIMIT 1
                """,
                (uid, since),
            )
            if not cur.fetchone():
                return 0
            message_ids = [None]

        for mid in message_ids:
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
                continue
            execute(
                conn,
                """
                INSERT INTO free_answer_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, 'converted', 'purchase')
                """,
                (uid, mid),
            )
            inserted += 1
        conn.commit()
    return inserted


def _inclusive_date_clause(
    from_date: Optional[str],
    to_date: Optional[str],
    col: str,
) -> Tuple[List[str], List[Any]]:
    """Same inclusive date(col) pattern as working admin credit dashboards."""
    clauses: List[str] = []
    params: List[Any] = []
    if from_date:
        clauses.append(f"date({col}) >= ?")
        params.append(from_date)
    if to_date:
        clauses.append(f"date({col}) <= ?")
        params.append(to_date)
    return clauses, params


def get_funnel_analytics(
    *,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cohort funnel keyed by free answers persisted on chat messages.

    Impressions come from chat_messages.gate_metadata.free_question_completed
    (answers that show the free-detail blur UX), not sparse client blur_shown
    beacons. Date range filters answer completed_at. Reveal/purchase count only
    for those same message ids.
    """
    date_clauses, date_params = _inclusive_date_clause(
        from_date, to_date, "COALESCE(cm.completed_at, cm.started_at, cm.timestamp)"
    )
    date_sql = (" AND " + " AND ".join(date_clauses)) if date_clauses else ""

    # Free answers that can show a blurred detail block (quick-answer structure).
    impression_predicate = """
        cm.sender = 'assistant'
        AND cm.status = 'completed'
        AND cm.gate_metadata IS NOT NULL
        AND TRIM(cm.gate_metadata) <> ''
        AND LOWER(COALESCE(cm.gate_metadata::jsonb ->> 'free_question_completed', '')) IN ('true', '1')
        AND (
          LOWER(cm.content) LIKE '%quick-answer-card%'
          OR cm.content ~* '###\\s*(Quick Answer|Direct Answer|Short Answer|Bottom Line|Answer)\\b'
        )
    """

    impression_sql = f"""
        SELECT
          COUNT(DISTINCT cs.user_id) AS users,
          COUNT(*) AS events
        FROM chat_messages cm
        INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE {impression_predicate}
          {date_sql}
    """

    with get_conn() as conn:
        ensure_free_answer_funnel_table(conn)

        try:
            cur = execute(conn, impression_sql, tuple(date_params))
            shown_row = cur.fetchone() or (0, 0)
        except Exception:
            logger.exception("free-answer funnel impression query failed; retrying with json cast")
            conn.rollback()
            sql_json = impression_sql.replace("::jsonb", "::json")
            cur = execute(conn, sql_json, tuple(date_params))
            shown_row = cur.fetchone() or (0, 0)

        shown_users = int(shown_row[0] or 0)
        shown_events = int(shown_row[1] or 0)

        progress_sql = f"""
            SELECT
              COUNT(DISTINCT cs.user_id) AS users,
              COUNT(*) AS events
            FROM chat_messages cm
            INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
            INNER JOIN free_answer_funnel_events e
              ON e.userid = cs.user_id
             AND e.message_id = cm.message_id::text
             AND e.event_name = ?
            WHERE {impression_predicate}
              {date_sql}
        """

        def _progress(event_name: str) -> Tuple[int, int]:
            try:
                cur2 = execute(conn, progress_sql, (event_name, *date_params))
                row = cur2.fetchone() or (0, 0)
            except Exception:
                logger.exception("free-answer funnel progress query failed event=%s", event_name)
                conn.rollback()
                sql_json = progress_sql.replace("::jsonb", "::json")
                cur2 = execute(conn, sql_json, (event_name, *date_params))
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

        return {
            "from_date": from_date,
            "to_date": to_date,
            "impression_source": "chat_messages.gate_metadata.free_question_completed",
            "steps": steps,
            "reveal_to_purchase_pct": (
                round(100.0 * converted_users / reveal_users, 1) if reveal_users > 0 else None
            ),
        }
