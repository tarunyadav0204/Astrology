"""Reel credit pricing and refunds using the common credit ledger."""
import json

from credits.credit_service import CreditService
from db import execute, get_conn

credit_service = CreditService()

REEL_SHORT_DURATION_SECONDS = 90
REEL_DEEP_DURATION_SECONDS = 180


def reel_pricing(user_id: int, duration_seconds: int = REEL_SHORT_DURATION_SECONDS, presenter_enabled: bool = False) -> dict:
    """Return the server-authoritative price for one supported Reel format."""
    key = (
        "reel_short_generation_cost"
        if int(duration_seconds) == REEL_SHORT_DURATION_SECONDS
        else "reel_deep_generation_cost"
    )
    base = credit_service.get_credit_setting(key)
    cost = credit_service.get_effective_cost(user_id, base, key)
    addon_key = 'reel_presenter_addon_cost'
    addon = credit_service.get_effective_cost(user_id, credit_service.get_credit_setting(addon_key), addon_key)
    return {"credit_cost": cost + (addon if presenter_enabled else 0), "base_credit_cost": cost,
            "presenter_addon_cost": addon, "presenter_enabled": presenter_enabled,
            "credits": credit_service.get_user_credits(user_id)}


def charge_reel(conn, user_id: int, cost: int, job_id: str, message_id: int) -> bool:
    """Caller commits this debit together with the new job under a draft lock."""
    if cost == 0:
        return True
    row = execute(conn, """UPDATE user_credits SET credits=credits-%s, updated_at=CURRENT_TIMESTAMP
        WHERE userid=%s AND credits >= %s RETURNING credits""", (cost, user_id, cost)).fetchone()
    if not row:
        return False
    execute(conn, """INSERT INTO credit_transactions
        (userid, transaction_type, amount, balance_after, source, reference_id, description, metadata)
        VALUES (%s, 'spent', %s, %s, 'feature_usage', 'reel', %s, %s)""",
        (user_id, -cost, row[0], f"Reel Studio generation ({job_id})", json.dumps({"job_id": job_id, "message_id": message_id})))
    return True


def refund_reel(job_id: str) -> None:
    """Refund at most once; balance, ledger and refund marker commit together."""
    with get_conn() as conn:
        row = execute(conn, "SELECT user_id, plan_json FROM reel_render_jobs WHERE id=%s FOR UPDATE", (job_id,)).fetchone()
        if not row:
            return
        user_id, raw = row
        plan = json.loads(raw)
        charge = plan.get("credit_charge") or {}
        cost = int(charge.get("cost") or 0)
        if not cost or charge.get("refunded"):
            return
        balance = execute(conn, """UPDATE user_credits SET credits=credits+%s, updated_at=CURRENT_TIMESTAMP
            WHERE userid=%s RETURNING credits""", (cost, user_id)).fetchone()
        if not balance:
            raise RuntimeError("Could not refund reel: credit account is missing")
        execute(conn, """INSERT INTO credit_transactions
            (userid, transaction_type, amount, balance_after, source, reference_id, description)
            VALUES (%s, 'refund', %s, %s, 'refund', 'reel', %s)""",
            (user_id, cost, balance[0], f"Reel Studio generation refund ({job_id})"))
        charge["refunded"] = True
        execute(conn, "UPDATE reel_render_jobs SET plan_json=%s WHERE id=%s", (json.dumps(plan), job_id))
        conn.commit()
