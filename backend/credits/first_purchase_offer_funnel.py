"""Attribution funnel for the post-free-question first-purchase offer."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from db import execute, get_conn

VALID_EVENTS = frozenset({"offer_shown", "offer_clicked", "offer_expired", "converted"})
CONVERSION_WINDOW = timedelta(days=7)
_ADMIN_TZ = "Asia/Kolkata"


def ensure_first_purchase_offer_funnel_table(conn) -> None:
    execute(conn, """
        CREATE TABLE IF NOT EXISTS first_purchase_offer_funnel_events (
            id BIGSERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            message_id TEXT,
            event_name TEXT NOT NULL,
            platform TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE INDEX IF NOT EXISTS idx_first_purchase_offer_funnel_user_event_created
        ON first_purchase_offer_funnel_events (userid, event_name, created_at DESC)
    """)
    execute(conn, """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_first_purchase_offer_funnel_user_msg_event
        ON first_purchase_offer_funnel_events (userid, (COALESCE(message_id, '')), event_name)
    """)


def record_funnel_event(*, userid: int, event_name: str, message_id: Optional[str] = None, platform: Optional[str] = None) -> bool:
    name = str(event_name or "").strip().lower()
    if name not in VALID_EVENTS:
        raise ValueError(f"invalid event_name={event_name!r}")
    uid = int(userid)
    mid = str(message_id or "").strip() or None
    plat = str(platform or "").strip()[:40] or None
    with get_conn() as conn:
        ensure_first_purchase_offer_funnel_table(conn)
        try:
            cur = execute(conn, """
                INSERT INTO first_purchase_offer_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING RETURNING id
            """, (uid, mid, name, plat))
            inserted = bool(cur.fetchone())
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            cur = execute(conn, """
                SELECT 1 FROM first_purchase_offer_funnel_events
                WHERE userid = ? AND COALESCE(message_id, '') = COALESCE(?, '') AND event_name = ? LIMIT 1
            """, (uid, mid, name))
            if cur.fetchone():
                return False
            execute(conn, """
                INSERT INTO first_purchase_offer_funnel_events (userid, message_id, event_name, platform)
                VALUES (?, ?, ?, ?)
            """, (uid, mid, name, plat))
            conn.commit()
            return True


def mark_converted_after_purchase(userid: int) -> int:
    uid = int(userid)
    since = datetime.now(timezone.utc) - CONVERSION_WINDOW
    with get_conn() as conn:
        ensure_first_purchase_offer_funnel_table(conn)
        cur = execute(conn, """
            SELECT message_id FROM first_purchase_offer_funnel_events
            WHERE userid = ? AND event_name = 'offer_clicked' AND created_at >= ?
            ORDER BY created_at DESC LIMIT 1
        """, (uid, since))
        row = cur.fetchone()
        if not row:
            return 0
        mid = row[0]
        cur = execute(conn, """
            SELECT 1 FROM first_purchase_offer_funnel_events
            WHERE userid = ? AND COALESCE(message_id, '') = COALESCE(?, '') AND event_name = 'converted'
            LIMIT 1
        """, (uid, mid))
        if cur.fetchone():
            return 0
        execute(conn, """
            INSERT INTO first_purchase_offer_funnel_events (userid, message_id, event_name, platform)
            VALUES (?, ?, 'converted', 'purchase')
        """, (uid, mid))
        conn.commit()
        return 1


def _date_clause(from_date: Optional[str], to_date: Optional[str]) -> Tuple[List[str], List[Any]]:
    clauses: List[str] = []
    params: List[Any] = []
    if from_date:
        clauses.append("(s.created_at AT TIME ZONE 'Asia/Kolkata')::date >= ?::date")
        params.append(from_date)
    if to_date:
        clauses.append("(s.created_at AT TIME ZONE 'Asia/Kolkata')::date <= ?::date")
        params.append(to_date)
    return clauses, params


def get_funnel_analytics(*, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
    clauses, params = _date_clause(from_date, to_date)
    cohort = " AND ".join(["s.event_name = 'offer_shown'", *clauses])
    with get_conn() as conn:
        ensure_first_purchase_offer_funnel_table(conn)
        cur = execute(conn, f"""
            SELECT COUNT(DISTINCT s.userid), COUNT(*) FROM first_purchase_offer_funnel_events s WHERE {cohort}
        """, tuple(params))
        row = cur.fetchone() or (0, 0)
        shown_users, shown_events = int(row[0] or 0), int(row[1] or 0)

        def progress(event_name: str) -> Tuple[int, int]:
            cur2 = execute(conn, f"""
                SELECT COUNT(DISTINCT s.userid), COUNT(*)
                FROM first_purchase_offer_funnel_events s
                INNER JOIN first_purchase_offer_funnel_events e
                  ON e.userid = s.userid
                 AND COALESCE(e.message_id, '') = COALESCE(s.message_id, '')
                 AND e.event_name = ?
                WHERE {cohort}
            """, (event_name, *params))
            r = cur2.fetchone() or (0, 0)
            return int(r[0] or 0), int(r[1] or 0)

        steps = []
        for event_name, label in (
            ("offer_shown", "Offer shown"),
            ("offer_clicked", "Tapped offer / opened credits"),
            ("converted", "Completed credit purchase"),
        ):
            users, events = (shown_users, shown_events) if event_name == "offer_shown" else progress(event_name)
            steps.append({"event_name": event_name, "label": label, "unique_users": users, "events": events,
                          "conversion_from_offer_pct": round(100 * users / shown_users, 1) if shown_users else None})
        cur = execute(conn, "SELECT MIN(created_at) FROM first_purchase_offer_funnel_events WHERE event_name = 'offer_shown'")
        start = cur.fetchone()
        return {
            "from_date": from_date, "to_date": to_date, "timezone": _ADMIN_TZ,
            "tracking_started_at": start[0] if start else None,
            "impression_source": "first_purchase_offer_funnel_events.offer_shown",
            "steps": steps,
            "click_to_purchase_pct": round(100 * steps[2]["unique_users"] / steps[1]["unique_users"], 1) if steps[1]["unique_users"] else None,
        }
