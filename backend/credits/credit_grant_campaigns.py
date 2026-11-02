"""Permanent, auditable admin credit grants.

This deliberately does not reuse purchase-multiplier campaigns: a grant changes a
user's normal credit balance immediately and never has an expiry.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from db import execute, get_conn
from credits.credit_service import CreditService

SOURCE = "credit_grant_campaign"


def _row_dict(row: Any) -> Dict[str, Any]:
    return {
        "id": int(row[0]), "name": str(row[1]), "credits": int(row[2]),
        "status": str(row[3]), "recipient_count": int(row[4] or 0),
        "credited_count": int(row[5] or 0), "created_at": row[6].isoformat() if row[6] else None,
        "metrics": {
            "grant_failed": int(row[17] or 0),
            "credits_granted": int(row[18] or 0),
            "queued": int(row[7] or 0), "accepted": int(row[8] or 0),
            "sent": int(row[9] or 0), "delivered": int(row[10] or 0),
            "read": int(row[11] or 0), "failed": int(row[12] or 0),
            "chat_opened": int(row[13] or 0),
            "whatsapp_eligible": int(row[19] or 0),
            # These are deliberately paid purchases only.  They do not count the
            # campaign's free grant, promo credits, or a later credit spend.
            "paid_buyers": int(row[14] or 0),
            "paid_credit_purchased": int(row[15] or 0),
            "paid_purchase_count": int(row[16] or 0),
            "chat_converted": int(row[20] or 0),
            # Credits are fungible. We therefore attribute feature usage after
            # the grant to this grant until its amount is exhausted per user.
            "grant_credits_used": int(row[21] or 0),
            "grant_credits_remaining": int(row[22] or 0),
        },
    }


def ensure_credit_grant_tables(conn) -> None:
    # The nudge worker can run independently of the API startup path, so keep the
    # recipient eligibility column available here as well.
    execute(conn, """
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS whatsapp_marketing_opted_out_at TIMESTAMPTZ
    """)
    execute(conn, """
        CREATE TABLE IF NOT EXISTS credit_grant_campaigns (
          id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, credits INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'processing', created_by INTEGER,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    execute(conn, """
        CREATE TABLE IF NOT EXISTS credit_grant_campaign_recipients (
          campaign_id BIGINT NOT NULL, userid INTEGER NOT NULL,
          grant_reference TEXT NOT NULL UNIQUE, grant_status TEXT NOT NULL DEFAULT 'pending',
          balance_after INTEGER, credited_at TIMESTAMP, grant_error TEXT,
          whatsapp_status TEXT NOT NULL DEFAULT 'not_queued', whatsapp_queued_at TIMESTAMP,
          whatsapp_message_id TEXT, whatsapp_meta_status TEXT, whatsapp_accepted_at TIMESTAMP,
          whatsapp_sent_at TIMESTAMP, whatsapp_delivered_at TIMESTAMP, whatsapp_read_at TIMESTAMP,
          whatsapp_failed_at TIMESTAMP, whatsapp_error TEXT, chat_opened_at TIMESTAMP,
          PRIMARY KEY (campaign_id, userid)
        )
    """)
    for column in ("whatsapp_message_id TEXT", "whatsapp_meta_status TEXT", "whatsapp_accepted_at TIMESTAMP", "whatsapp_sent_at TIMESTAMP", "whatsapp_delivered_at TIMESTAMP", "whatsapp_read_at TIMESTAMP", "whatsapp_failed_at TIMESTAMP", "whatsapp_error TEXT", "chat_opened_at TIMESTAMP"):
        execute(conn, f"ALTER TABLE credit_grant_campaign_recipients ADD COLUMN IF NOT EXISTS {column}")
    # Prevent a retry or two concurrent admin requests from adding the same grant twice.
    execute(conn, """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_grant_transaction_reference
        ON credit_transactions (userid, source, reference_id)
        WHERE source = 'credit_grant_campaign' AND reference_id IS NOT NULL
    """)
    conn.commit()


def _campaign_row(conn, campaign_id: int):
    return execute(conn, _campaign_query("WHERE c.id = ?"), (campaign_id,)).fetchone()


def _campaign_query(where_clause: str = "") -> str:
    """Return campaign metrics with paid-purchase attribution after each grant.

    A recipient's paid purchase is attributed when its ledger entry was created
    at or after that recipient received this campaign's credits.  It is an
    outcome signal, not a claim that a particular purchased credit can be
    separated from a fungible account balance.
    """
    return f"""
      WITH paid_purchase_outcomes AS (
        SELECT r.campaign_id, r.userid,
               COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT AS paid_credit_purchased,
               COUNT(ct.id)::BIGINT AS paid_purchase_count
        FROM credit_grant_campaign_recipients r
        LEFT JOIN credit_transactions ct
          ON ct.userid = r.userid
         AND ct.created_at >= r.credited_at
         AND ct.transaction_type = 'earned'
         AND ct.source IN ('google_play', 'razorpay')
        WHERE r.grant_status = 'credited' AND r.credited_at IS NOT NULL
        GROUP BY r.campaign_id, r.userid
      ),
      credit_spend_outcomes AS (
        SELECT r.campaign_id, r.userid,
               COALESCE(SUM(ABS(ct.amount)), 0)::BIGINT AS feature_credits_used
        FROM credit_grant_campaign_recipients r
        LEFT JOIN credit_transactions ct
          ON ct.userid = r.userid
         AND ct.created_at >= r.credited_at
         AND ct.transaction_type = 'spent'
         AND ct.source = 'feature_usage'
        WHERE r.grant_status = 'credited' AND r.credited_at IS NOT NULL
        GROUP BY r.campaign_id, r.userid
      ),
      chat_conversion_outcomes AS (
        SELECT r.campaign_id, r.userid,
               EXISTS (
                 SELECT 1
                 FROM chat_sessions cs
                 JOIN chat_messages cm ON cm.session_id = cs.session_id
                 WHERE cs.user_id = r.userid
                   AND cm.sender = 'user'
                   AND cm.timestamp >= r.chat_opened_at
               ) AS chat_converted
        FROM credit_grant_campaign_recipients r
        WHERE r.grant_status = 'credited' AND r.chat_opened_at IS NOT NULL
      )
      SELECT c.id, c.name, c.credits, c.status, COUNT(r.userid),
             COUNT(r.userid) FILTER (WHERE r.grant_status = 'credited'), c.created_at,
             COUNT(r.userid) FILTER (WHERE r.whatsapp_status = 'queued'), COUNT(r.userid) FILTER (WHERE r.whatsapp_message_id IS NOT NULL),
             COUNT(r.userid) FILTER (WHERE r.whatsapp_meta_status = 'sent'), COUNT(r.userid) FILTER (WHERE r.whatsapp_meta_status IN ('delivered','read')),
             COUNT(r.userid) FILTER (WHERE r.whatsapp_meta_status = 'read'), COUNT(r.userid) FILTER (WHERE r.whatsapp_meta_status = 'failed'),
             COUNT(r.userid) FILTER (WHERE r.chat_opened_at IS NOT NULL),
             COUNT(r.userid) FILTER (WHERE COALESCE(p.paid_credit_purchased, 0) > 0),
             COALESCE(SUM(p.paid_credit_purchased), 0),
             COALESCE(SUM(p.paid_purchase_count), 0),
             COUNT(r.userid) FILTER (WHERE r.grant_status = 'failed'),
             COALESCE(SUM(c.credits) FILTER (WHERE r.grant_status = 'credited'), 0),
             COUNT(r.userid) FILTER (
               WHERE r.grant_status = 'credited'
                 AND NULLIF(BTRIM(COALESCE(u.phone, '')), '') IS NOT NULL
                 AND u.whatsapp_marketing_opted_out_at IS NULL
             ),
             COUNT(r.userid) FILTER (WHERE co.chat_converted),
             COALESCE(SUM(LEAST(c.credits::BIGINT, COALESCE(s.feature_credits_used, 0))), 0),
             COALESCE(SUM(c.credits) FILTER (WHERE r.grant_status = 'credited'), 0)
               - COALESCE(SUM(LEAST(c.credits::BIGINT, COALESCE(s.feature_credits_used, 0))), 0)
      FROM credit_grant_campaigns c
      LEFT JOIN credit_grant_campaign_recipients r ON r.campaign_id = c.id
      LEFT JOIN users u ON u.userid = r.userid
      LEFT JOIN paid_purchase_outcomes p ON p.campaign_id = r.campaign_id AND p.userid = r.userid
      LEFT JOIN credit_spend_outcomes s ON s.campaign_id = r.campaign_id AND s.userid = r.userid
      LEFT JOIN chat_conversion_outcomes co ON co.campaign_id = r.campaign_id AND co.userid = r.userid
      {where_clause}
      GROUP BY c.id, c.name, c.credits, c.status, c.created_at
    """


def list_credit_grant_campaigns(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        rows = execute(conn, f"{_campaign_query()} ORDER BY c.id DESC LIMIT ?", (limit,)).fetchall()
        return [_row_dict(row) for row in rows]


def create_credit_grant_campaign(*, name: str, credits: int, recipient_ids: Iterable[int], created_by: int) -> Dict[str, Any]:
    ids = list(dict.fromkeys(int(uid) for uid in recipient_ids if int(uid) > 0))
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        cur = execute(conn, """
          INSERT INTO credit_grant_campaigns (name, credits, created_by) VALUES (?, ?, ?)
          RETURNING id
        """, (name.strip(), int(credits), int(created_by)))
        campaign_id = int(cur.fetchone()[0])
        for uid in ids:
            reference = f"credit-grant:{campaign_id}:{uid}"
            execute(conn, """
              INSERT INTO credit_grant_campaign_recipients (campaign_id, userid, grant_reference)
              VALUES (?, ?, ?)
            """, (campaign_id, uid, reference))
        conn.commit()

    service = CreditService()
    credited = failed = 0
    for uid in ids:
        reference = f"credit-grant:{campaign_id}:{uid}"
        with get_conn() as conn:
            already = execute(conn, """
              SELECT balance_after FROM credit_transactions
              WHERE userid = ? AND source = ? AND reference_id = ? LIMIT 1
            """, (uid, SOURCE, reference)).fetchone()
        if already:
            ok, balance = True, int(already[0])
        else:
            ok = service.add_credits(
                uid, int(credits), SOURCE, reference,
                f"Admin credit grant: {name.strip()}",
                json.dumps({"campaign_id": campaign_id}),
            )
            balance = None
            if ok:
                with get_conn() as conn:
                    row = execute(conn, """
                      SELECT balance_after FROM credit_transactions
                      WHERE userid = ? AND source = ? AND reference_id = ? LIMIT 1
                    """, (uid, SOURCE, reference)).fetchone()
                    balance = int(row[0]) if row else None
        with get_conn() as conn:
            if ok:
                execute(conn, """UPDATE credit_grant_campaign_recipients
                  SET grant_status = 'credited', balance_after = ?, credited_at = CURRENT_TIMESTAMP, grant_error = NULL
                  WHERE campaign_id = ? AND userid = ?""", (balance, campaign_id, uid))
                credited += 1
            else:
                execute(conn, """UPDATE credit_grant_campaign_recipients
                  SET grant_status = 'failed', grant_error = 'Credit transaction failed'
                  WHERE campaign_id = ? AND userid = ?""", (campaign_id, uid))
                failed += 1
            conn.commit()
    with get_conn() as conn:
        execute(conn, "UPDATE credit_grant_campaigns SET status = ? WHERE id = ?",
                ("completed" if not failed else "partial", campaign_id))
        row = _campaign_row(conn, campaign_id)
        conn.commit()
    result = _row_dict(row)
    result.update({"failed_count": failed, "credited_count": credited})
    return result


def get_credit_grant_recipients_for_whatsapp(campaign_id: int) -> List[Dict[str, Any]]:
    """Build the minimal task payload from the application DB; worker never needs it."""
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        rows = execute(conn, """
          SELECT r.userid, COALESCE(u.phone, ''), c.credits, r.balance_after
          FROM credit_grant_campaign_recipients r
          JOIN credit_grant_campaigns c ON c.id = r.campaign_id
          JOIN users u ON u.userid = r.userid
          WHERE r.campaign_id = ? AND r.grant_status = 'credited'
            AND r.whatsapp_status <> 'queued'
            AND u.whatsapp_marketing_opted_out_at IS NULL
        """, (campaign_id,)).fetchall()
        recipients = []
        for row in rows:
            phone = str(row[1] or '').strip()
            if phone:
                recipients.append({"campaign_id": int(campaign_id), "userid": int(row[0]), "phone": phone, "credits": int(row[2]), "balance": int(row[3] or 0)})
        return recipients


def mark_credit_grant_whatsapp_queued(campaign_id: int, userids: Iterable[int]) -> None:
    ids = [int(value) for value in userids]
    if not ids:
        return
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        execute(conn, """UPDATE credit_grant_campaign_recipients
          SET whatsapp_status = 'queued', whatsapp_queued_at = CURRENT_TIMESTAMP
          WHERE campaign_id = ? AND userid = ANY(?)""", (campaign_id, ids))
        conn.commit()


def mark_credit_grant_whatsapp_result(campaign_id: int, userid: int, *, accepted: bool, message_id: str | None = None, error: str | None = None) -> None:
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        execute(conn, """UPDATE credit_grant_campaign_recipients SET whatsapp_message_id = COALESCE(?, whatsapp_message_id),
          whatsapp_meta_status = CASE WHEN ? THEN 'accepted' ELSE 'failed' END, whatsapp_accepted_at = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE whatsapp_accepted_at END,
          whatsapp_failed_at = CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE whatsapp_failed_at END, whatsapp_error = ?
          WHERE campaign_id = ? AND userid = ?""", (message_id, accepted, accepted, not accepted, error, campaign_id, userid))
        conn.commit()


def opted_out_credit_grant_whatsapp_userids(userids: Iterable[int]) -> set[int]:
    """Return users who opted out after a batch had already been queued."""
    ids = list({int(value) for value in userids})
    if not ids:
        return set()
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        rows = execute(conn, """SELECT userid FROM users
          WHERE userid = ANY(?) AND whatsapp_marketing_opted_out_at IS NOT NULL""", (ids,)).fetchall()
        return {int(row[0]) for row in rows}


def mark_credit_grant_whatsapp_suppressed(campaign_id: int, userid: int) -> None:
    """Record that a queued notice was intentionally not sent after STOP."""
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        execute(conn, """UPDATE credit_grant_campaign_recipients
          SET whatsapp_status = 'suppressed', whatsapp_meta_status = 'suppressed', whatsapp_error = NULL
          WHERE campaign_id = ? AND userid = ?""", (campaign_id, userid))
        conn.commit()


def mark_credit_grant_chat_opened(campaign_id: int, userid: int) -> bool:
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        cur = execute(conn, """UPDATE credit_grant_campaign_recipients SET chat_opened_at = COALESCE(chat_opened_at, CURRENT_TIMESTAMP)
          WHERE campaign_id = ? AND userid = ? AND grant_status = 'credited'""", (campaign_id, userid))
        conn.commit()
        return bool(cur.rowcount)


def record_credit_grant_whatsapp_status_updates(payload: Dict[str, Any]) -> int:
    """Apply Meta delivery receipts to grant messages by their wamid."""
    from nudge_engine.credit_campaign_whatsapp import extract_meta_whatsapp_status_updates
    timestamp_columns = {"sent": "whatsapp_sent_at", "delivered": "whatsapp_delivered_at", "read": "whatsapp_read_at", "failed": "whatsapp_failed_at"}
    matched = 0
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        for update in extract_meta_whatsapp_status_updates(payload):
            status = update["status"]
            column = timestamp_columns[status]
            cur = execute(conn, f"""UPDATE credit_grant_campaign_recipients SET {column} = COALESCE({column}, ?),
              whatsapp_meta_status = CASE WHEN ? = 'read' THEN 'read' WHEN ? = 'delivered' AND COALESCE(whatsapp_meta_status, '') <> 'read' THEN 'delivered'
              WHEN ? = 'sent' AND COALESCE(whatsapp_meta_status, '') NOT IN ('delivered','read','failed') THEN 'sent'
              WHEN ? = 'failed' AND COALESCE(whatsapp_meta_status, '') NOT IN ('delivered','read') THEN 'failed' ELSE COALESCE(whatsapp_meta_status, 'accepted') END,
              whatsapp_error = CASE WHEN ? = 'failed' THEN COALESCE(?, whatsapp_error) ELSE whatsapp_error END
              WHERE whatsapp_message_id = ?""", (update["occurred_at"], status, status, status, status, status, update.get("error"), update["message_id"]))
            matched += int(cur.rowcount or 0)
        conn.commit()
    return matched
