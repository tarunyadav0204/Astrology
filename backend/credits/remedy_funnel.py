"""Funnel for remedy CTA card → tap → remedy-only response."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

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
    Cohort funnel keyed by remedy cards persisted on chat answers.

    Impressions come from chat_messages.next_action (type=remedy), not sparse
    client card_shown beacons. Date range filters answer completed_at.
    Clicks/deliveries count only for those same message ids (any later time).
    """
    date_clauses, date_params = _inclusive_date_clause(
        from_date, to_date, "COALESCE(cm.completed_at, cm.started_at, cm.timestamp)"
    )
    date_sql = (" AND " + " AND ".join(date_clauses)) if date_clauses else ""

    # next_action is TEXT JSON. Prefer jsonb; fall back handled via try/except below.
    impression_sql = f"""
        SELECT
          COUNT(DISTINCT cs.user_id) AS users,
          COUNT(*) AS events
        FROM chat_messages cm
        INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.sender = 'assistant'
          AND cm.status = 'completed'
          AND cm.next_action IS NOT NULL
          AND TRIM(cm.next_action) <> ''
          AND LOWER(COALESCE(cm.next_action::jsonb ->> 'type', '')) = 'remedy'
          {date_sql}
    """

    with get_conn() as conn:
        ensure_remedy_funnel_table(conn)

        try:
            cur = execute(conn, impression_sql, tuple(date_params))
            shown_row = cur.fetchone() or (0, 0)
        except Exception:
            logger.exception("remedy funnel impression query failed; retrying with json cast")
            conn.rollback()
            impression_sql_json = impression_sql.replace("::jsonb", "::json")
            cur = execute(conn, impression_sql_json, tuple(date_params))
            shown_row = cur.fetchone() or (0, 0)

        shown_users = int(shown_row[0] or 0)
        shown_events = int(shown_row[1] or 0)

        # Among those impression message ids, how many have a matching click / delivery.
        progress_sql = f"""
            SELECT
              COUNT(DISTINCT cs.user_id) AS users,
              COUNT(*) AS events
            FROM chat_messages cm
            INNER JOIN chat_sessions cs ON cs.session_id = cm.session_id
            INNER JOIN remedy_funnel_events e
              ON e.userid = cs.user_id
             AND e.message_id = cm.message_id::text
             AND e.event_name = ?
            WHERE cm.sender = 'assistant'
              AND cm.status = 'completed'
              AND cm.next_action IS NOT NULL
              AND TRIM(cm.next_action) <> ''
              AND LOWER(COALESCE(cm.next_action::jsonb ->> 'type', '')) = 'remedy'
              {date_sql}
        """

        def _progress(event_name: str) -> Tuple[int, int]:
            try:
                cur2 = execute(conn, progress_sql, (event_name, *date_params))
                row = cur2.fetchone() or (0, 0)
            except Exception:
                logger.exception("remedy funnel progress query failed event=%s", event_name)
                conn.rollback()
                sql_json = progress_sql.replace("::jsonb", "::json")
                cur2 = execute(conn, sql_json, (event_name, *date_params))
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

        return {
            "from_date": from_date,
            "to_date": to_date,
            "impression_source": "chat_messages.next_action",
            "steps": steps,
            "click_to_delivered_pct": (
                round(100.0 * delivered_users / clicked_users, 1) if clicked_users > 0 else None
            ),
        }
