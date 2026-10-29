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
    }


def ensure_credit_grant_tables(conn) -> None:
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
          PRIMARY KEY (campaign_id, userid)
        )
    """)
    # Prevent a retry or two concurrent admin requests from adding the same grant twice.
    execute(conn, """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_grant_transaction_reference
        ON credit_transactions (userid, source, reference_id)
        WHERE source = 'credit_grant_campaign' AND reference_id IS NOT NULL
    """)
    conn.commit()


def _campaign_row(conn, campaign_id: int):
    return execute(conn, """
      SELECT c.id, c.name, c.credits, c.status, COUNT(r.userid),
             COUNT(r.userid) FILTER (WHERE r.grant_status = 'credited'), c.created_at
      FROM credit_grant_campaigns c
      LEFT JOIN credit_grant_campaign_recipients r ON r.campaign_id = c.id
      WHERE c.id = ? GROUP BY c.id, c.name, c.credits, c.status, c.created_at
    """, (campaign_id,)).fetchone()


def list_credit_grant_campaigns(limit: int = 50) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_credit_grant_tables(conn)
        rows = execute(conn, """
          SELECT c.id, c.name, c.credits, c.status, COUNT(r.userid),
                 COUNT(r.userid) FILTER (WHERE r.grant_status = 'credited'), c.created_at
          FROM credit_grant_campaigns c
          LEFT JOIN credit_grant_campaign_recipients r ON r.campaign_id = c.id
          GROUP BY c.id, c.name, c.credits, c.status, c.created_at
          ORDER BY c.id DESC LIMIT ?
        """, (limit,)).fetchall()
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
        """, (campaign_id,)).fetchall()
        recipients = []
        for row in rows:
            phone = str(row[1] or '').strip()
            if phone:
                recipients.append({"userid": int(row[0]), "phone": phone, "credits": int(row[2]), "balance": int(row[3] or 0)})
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
