"""Targeted, time-bound credit multiplier campaigns."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Optional

from db import execute, get_conn

logger = logging.getLogger(__name__)


def ensure_credit_campaign_tables(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaigns (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            multiplier NUMERIC(6, 3) NOT NULL,
            starts_at TIMESTAMPTZ NOT NULL,
            ends_at TIMESTAMPTZ NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            product_ids_json TEXT NOT NULL DEFAULT '[]',
            payment_channel TEXT NOT NULL DEFAULT 'razorpay_web',
            whatsapp_template_name TEXT,
            whatsapp_template_language TEXT,
            created_by INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaign_recipients (
            campaign_id BIGINT NOT NULL REFERENCES credit_campaigns(id) ON DELETE CASCADE,
            userid INTEGER NOT NULL,
            notified_at TIMESTAMPTZ,
            opened_at TIMESTAMPTZ,
            message_status TEXT,
            message_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (campaign_id, userid)
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_campaign_awards (
            id BIGSERIAL PRIMARY KEY,
            campaign_id BIGINT NOT NULL REFERENCES credit_campaigns(id),
            userid INTEGER NOT NULL,
            purchase_source TEXT NOT NULL,
            purchase_reference_id TEXT NOT NULL,
            product_id TEXT,
            purchased_credits INTEGER NOT NULL,
            credits_before_campaign INTEGER NOT NULL DEFAULT 0,
            campaign_bonus_credits INTEGER NOT NULL,
            target_total_credits INTEGER NOT NULL,
            awarded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (campaign_id, purchase_source, purchase_reference_id)
        )
        """,
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_credit_campaign_recipients_user ON credit_campaign_recipients (userid, campaign_id)",
    )
    execute(
        conn,
        "CREATE INDEX IF NOT EXISTS idx_credit_campaign_awards_campaign ON credit_campaign_awards (campaign_id, awarded_at DESC)",
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _product_ids(raw: Any) -> List[str]:
    try:
        values = json.loads(raw or "[]") if isinstance(raw, str) else list(raw or [])
    except Exception:
        values = []
    return [str(value).strip() for value in values if str(value).strip()]


def _campaign_dict(row: Any) -> Dict[str, Any]:
    return {
        "id": int(row[0]),
        "name": str(row[1]),
        "multiplier": float(row[2]),
        "starts_at": row[3].isoformat() if row[3] else None,
        "ends_at": row[4].isoformat() if row[4] else None,
        "status": str(row[5]),
        "product_ids": _product_ids(row[6]),
        "payment_channel": str(row[7]),
        "whatsapp_template_name": row[8],
        "whatsapp_template_language": row[9],
        "created_by": row[10],
        "created_at": row[11].isoformat() if row[11] else None,
    }


_CAMPAIGN_SELECT = """
    SELECT c.id, c.name, c.multiplier, c.starts_at, c.ends_at, c.status,
           c.product_ids_json, c.payment_channel, c.whatsapp_template_name,
           c.whatsapp_template_language, c.created_by, c.created_at
    FROM credit_campaigns c
"""


def create_credit_campaign(
    *,
    name: str,
    multiplier: Decimal,
    starts_at: datetime,
    ends_at: datetime,
    recipient_ids: Iterable[int],
    product_ids: Iterable[str],
    status: str,
    created_by: int,
    payment_channel: str = "razorpay_web",
) -> Dict[str, Any]:
    recipients = list(dict.fromkeys(int(value) for value in recipient_ids))
    products = list(dict.fromkeys(str(value).strip() for value in product_ids if str(value).strip()))
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        cur = execute(
            conn,
            """
            INSERT INTO credit_campaigns
              (name, multiplier, starts_at, ends_at, status, product_ids_json,
               payment_channel, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (
                name.strip(),
                str(multiplier),
                _utc(starts_at),
                _utc(ends_at),
                status,
                json.dumps(products),
                payment_channel,
                int(created_by),
            ),
        )
        campaign_id = int(cur.fetchone()[0])
        for userid in recipients:
            execute(
                conn,
                "INSERT INTO credit_campaign_recipients (campaign_id, userid) VALUES (?, ?) ON CONFLICT DO NOTHING",
                (campaign_id, userid),
            )
        conn.commit()
    return get_credit_campaign(campaign_id) or {}


def get_credit_campaign(campaign_id: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        cur = execute(conn, f"{_CAMPAIGN_SELECT} WHERE c.id = ?", (int(campaign_id),))
        row = cur.fetchone()
        if not row:
            return None
        campaign = _campaign_dict(row)
        campaign.update(get_credit_campaign_summary(int(campaign_id), conn=conn))
        return campaign


def list_credit_campaigns() -> List[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        rows = execute(conn, f"{_CAMPAIGN_SELECT} ORDER BY c.created_at DESC, c.id DESC").fetchall()
        result = []
        for row in rows:
            campaign = _campaign_dict(row)
            campaign.update(get_credit_campaign_summary(campaign["id"], conn=conn))
            result.append(campaign)
        return result


def get_credit_campaign_summary(campaign_id: int, *, conn=None) -> Dict[str, Any]:
    owns_connection = conn is None
    context = get_conn() if owns_connection else None
    active_conn = context.__enter__() if context else conn
    try:
        ensure_credit_campaign_tables(active_conn)
        recipient_row = execute(
            active_conn,
            """
            SELECT COUNT(*),
                   COUNT(*) FILTER (WHERE notified_at IS NOT NULL),
                   COUNT(*) FILTER (WHERE opened_at IS NOT NULL),
                   COUNT(*) FILTER (WHERE message_status = 'failed')
            FROM credit_campaign_recipients WHERE campaign_id = ?
            """,
            (int(campaign_id),),
        ).fetchone()
        award_row = execute(
            active_conn,
            """
            SELECT COUNT(*), COUNT(DISTINCT userid),
                   COALESCE(SUM(purchased_credits), 0),
                   COALESCE(SUM(campaign_bonus_credits), 0)
            FROM credit_campaign_awards WHERE campaign_id = ?
            """,
            (int(campaign_id),),
        ).fetchone()
        return {
            "summary": {
                "recipients": int(recipient_row[0] or 0),
                "notified": int(recipient_row[1] or 0),
                "opened": int(recipient_row[2] or 0),
                "message_failed": int(recipient_row[3] or 0),
                "purchases": int(award_row[0] or 0),
                "buyers": int(award_row[1] or 0),
                "purchased_credits": int(award_row[2] or 0),
                "campaign_bonus_credits": int(award_row[3] or 0),
            }
        }
    finally:
        if context:
            context.__exit__(None, None, None)


def get_credit_campaign_recipient_report(campaign_id: int) -> List[Dict[str, Any]]:
    """Return one row per recipient from the app read replica."""
    from nudge_engine.connections import get_audience_conn

    with get_audience_conn() as conn:
        rows = execute(
            conn,
            """
            WITH purchase_totals AS (
                SELECT campaign_id, userid,
                       COUNT(*) AS purchase_count,
                       MIN(awarded_at) AS first_purchase_at,
                       MAX(awarded_at) AS latest_purchase_at,
                       COALESCE(SUM(purchased_credits), 0) AS purchased_credits,
                       COALESCE(SUM(campaign_bonus_credits), 0) AS campaign_bonus_credits
                FROM credit_campaign_awards
                WHERE campaign_id = ?
                GROUP BY campaign_id, userid
            )
            SELECT r.userid, u.name, u.phone,
                   r.message_status, r.message_error, r.notified_at, r.opened_at,
                   COALESCE(p.purchase_count, 0),
                   p.first_purchase_at, p.latest_purchase_at,
                   COALESCE(p.purchased_credits, 0),
                   COALESCE(p.campaign_bonus_credits, 0)
            FROM credit_campaign_recipients r
            LEFT JOIN users u ON u.userid = r.userid
            LEFT JOIN purchase_totals p
              ON p.campaign_id = r.campaign_id AND p.userid = r.userid
            WHERE r.campaign_id = ?
            ORDER BY (p.userid IS NOT NULL) DESC,
                     r.opened_at DESC NULLS LAST,
                     r.userid
            """,
            (int(campaign_id), int(campaign_id)),
        ).fetchall()
        return [
            {
                "userid": int(row[0]),
                "name": row[1],
                "phone": row[2],
                "message_status": row[3],
                "message_error": row[4],
                "notified_at": row[5],
                "opened_at": row[6],
                "clicked": row[6] is not None,
                "purchase_count": int(row[7] or 0),
                "first_purchase_at": row[8],
                "latest_purchase_at": row[9],
                "purchased": int(row[7] or 0) > 0,
                "purchased_credits": int(row[10] or 0),
                "campaign_bonus_credits": int(row[11] or 0),
            }
            for row in rows
        ]


def set_credit_campaign_status(campaign_id: int, status: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        cur = execute(
            conn,
            "UPDATE credit_campaigns SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, int(campaign_id)),
        )
        conn.commit()
        if not cur.rowcount:
            return None
    return get_credit_campaign(campaign_id)


def get_campaign_recipient_ids(campaign_id: int) -> List[int]:
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        rows = execute(
            conn,
            "SELECT userid FROM credit_campaign_recipients WHERE campaign_id = ? ORDER BY userid",
            (int(campaign_id),),
        ).fetchall()
        return [int(row[0]) for row in rows]


def active_credit_campaigns_for_user(
    userid: int,
    *,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    moment = _utc(now or datetime.now(timezone.utc))
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        rows = execute(
            conn,
            f"""
            {_CAMPAIGN_SELECT}
            JOIN credit_campaign_recipients r ON r.campaign_id = c.id
            WHERE r.userid = ? AND c.status = 'active'
              AND c.starts_at <= ? AND c.ends_at > ?
              AND c.payment_channel = 'razorpay_web'
            ORDER BY c.multiplier DESC, c.ends_at ASC, c.id DESC
            """,
            (int(userid), moment, moment),
        ).fetchall()
        return [_campaign_dict(row) for row in rows]


def active_credit_campaign_for_user(
    userid: int,
    *,
    product_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    for campaign in active_credit_campaigns_for_user(userid, now=now):
        products = campaign["product_ids"]
        if not products or not product_id or str(product_id) in products:
            return campaign
    return None


def calculate_campaign_bonus(
    purchased_credits: int,
    multiplier: Any,
    *,
    existing_bonus_credits: int = 0,
) -> Dict[str, int]:
    base = max(0, int(purchased_credits or 0))
    existing = max(0, int(existing_bonus_credits or 0))
    factor = max(Decimal("1"), Decimal(str(multiplier)))
    target = int((Decimal(base) * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    campaign_bonus = max(0, target - base - existing)
    return {
        "target_total_credits": target,
        "campaign_bonus_credits": campaign_bonus,
        "existing_bonus_credits": existing,
    }


def calculate_campaign_question_count(base_questions: Any, multiplier: Any) -> int:
    """Scale pack question copy with the same half-up rule as campaign credits."""
    questions = max(0, int(base_questions or 0))
    factor = max(Decimal("1"), Decimal(str(multiplier)))
    return int((Decimal(questions) * factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def preview_credit_campaign(
    userid: int,
    *,
    purchased_credits: int,
    product_id: str,
    existing_bonus_credits: int = 0,
) -> Optional[Dict[str, Any]]:
    campaign = active_credit_campaign_for_user(userid, product_id=product_id)
    if not campaign:
        return None
    calculation = calculate_campaign_bonus(
        purchased_credits,
        campaign["multiplier"],
        existing_bonus_credits=existing_bonus_credits,
    )
    return {
        "id": campaign["id"],
        "name": campaign["name"],
        "multiplier": campaign["multiplier"],
        "starts_at": campaign["starts_at"],
        "ends_at": campaign["ends_at"],
        **calculation,
    }


def maybe_apply_credit_campaign(
    credit_service,
    *,
    userid: int,
    purchased_credits: int,
    purchase_source: str,
    purchase_reference_id: str,
    product_id: Optional[str],
    existing_bonus_credits: int,
    purchase_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    if str(purchase_source or "").lower() != "razorpay":
        return {"applied": False, "eligible": False, "bonus_credits": 0, "reason": "unsupported_channel"}
    campaign = active_credit_campaign_for_user(userid, product_id=product_id, now=purchase_at)
    if not campaign:
        return {"applied": False, "eligible": False, "bonus_credits": 0, "reason": "no_active_campaign"}
    calculation = calculate_campaign_bonus(
        purchased_credits,
        campaign["multiplier"],
        existing_bonus_credits=existing_bonus_credits,
    )
    bonus = calculation["campaign_bonus_credits"]
    reference_id = f"{purchase_source}:{purchase_reference_id}:credit_campaign:{campaign['id']}"
    if credit_service.has_transaction_with_reference(userid, "credit_campaign_bonus", reference_id):
        return {"applied": False, "eligible": True, "bonus_credits": bonus, "reason": "already_applied", "campaign": campaign, **calculation}
    if bonus <= 0:
        return {"applied": False, "eligible": True, "bonus_credits": 0, "reason": "target_already_met", "campaign": campaign, **calculation}
    metadata = json.dumps(
        {
            "campaign_id": campaign["id"],
            "campaign_name": campaign["name"],
            "multiplier": campaign["multiplier"],
            "purchase_source": purchase_source,
            "purchase_reference_id": purchase_reference_id,
            "product_id": product_id,
            "purchased_credits": int(purchased_credits),
            **calculation,
        }
    )
    ok = credit_service.add_credits(
        userid,
        bonus,
        "credit_campaign_bonus",
        reference_id=reference_id,
        description=f"{campaign['name']}: +{bonus} credits ({campaign['multiplier']}x target)",
        metadata=metadata,
    )
    if not ok:
        return {"applied": False, "eligible": True, "bonus_credits": bonus, "reason": "bonus_write_failed", "campaign": campaign, **calculation}
    try:
        with get_conn() as conn:
            ensure_credit_campaign_tables(conn)
            execute(
                conn,
                """
                INSERT INTO credit_campaign_awards
                  (campaign_id, userid, purchase_source, purchase_reference_id, product_id,
                   purchased_credits, credits_before_campaign, campaign_bonus_credits,
                   target_total_credits)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (campaign_id, purchase_source, purchase_reference_id) DO NOTHING
                """,
                (
                    campaign["id"], userid, purchase_source, purchase_reference_id,
                    product_id, int(purchased_credits), int(existing_bonus_credits),
                    bonus, calculation["target_total_credits"],
                ),
            )
            conn.commit()
    except Exception:
        logger.exception("credit campaign award audit insert failed campaign=%s payment=%s", campaign["id"], purchase_reference_id)
    return {"applied": True, "eligible": True, "bonus_credits": bonus, "reason": "applied", "campaign": campaign, **calculation}


def mark_campaign_opened(userid: int, campaign_id: int) -> None:
    try:
        with get_conn() as conn:
            ensure_credit_campaign_tables(conn)
            execute(
                conn,
                """
                UPDATE credit_campaign_recipients r
                SET opened_at = COALESCE(opened_at, CURRENT_TIMESTAMP)
                FROM credit_campaigns c
                WHERE r.campaign_id = c.id AND r.userid = ? AND r.campaign_id = ? AND c.status = 'active'
                  AND c.starts_at <= CURRENT_TIMESTAMP AND c.ends_at > CURRENT_TIMESTAMP
                """,
                (int(userid), int(campaign_id)),
            )
            conn.commit()
    except Exception:
        logger.debug("credit campaign open tracking skipped userid=%s campaign=%s", userid, campaign_id, exc_info=True)


def record_campaign_message_result(campaign_id: int, userid: int, status: str, error: Optional[str]) -> None:
    with get_conn() as conn:
        ensure_credit_campaign_tables(conn)
        execute(
            conn,
            """
            UPDATE credit_campaign_recipients
            SET message_status = ?, message_error = ?,
                notified_at = CASE WHEN ? = 'accepted' THEN CURRENT_TIMESTAMP ELSE notified_at END
            WHERE campaign_id = ? AND userid = ?
            """,
            (status, (error or "")[:1000] or None, status, int(campaign_id), int(userid)),
        )
        conn.commit()
