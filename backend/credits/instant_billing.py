"""Server-owned, prepaid minute metering for Instant Chat.

Each started minute is paid before it is used.  A heartbeat never trusts client
elapsed time; it advances the session using PostgreSQL's clock.  Missing
heartbeats receive a short reconnect grace and then end the consultation.
"""

from __future__ import annotations

import math
import os
import json
import uuid
from typing import Any, Dict, Optional

from db import execute, get_conn


HEARTBEAT_INTERVAL_SECONDS = max(5, int(os.getenv("INSTANT_BILLING_HEARTBEAT_SECONDS", "10") or 10))
RECONNECT_GRACE_SECONDS = max(
    HEARTBEAT_INTERVAL_SECONDS * 2,
    int(os.getenv("INSTANT_BILLING_RECONNECT_GRACE_SECONDS", "75") or 75),
)
LOW_BALANCE_MINUTES = max(1, int(os.getenv("INSTANT_BILLING_LOW_BALANCE_MINUTES", "5") or 5))


class InstantBillingError(Exception):
    def __init__(self, message: str, *, status_code: int = 400, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = int(status_code)
        self.detail = detail or {"message": message}


def ensure_table(conn) -> None:
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS instant_billing_sessions (
            session_id TEXT PRIMARY KEY,
            userid INTEGER NOT NULL,
            chat_session_id TEXT NOT NULL,
            client_instance_id TEXT,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            per_minute_cost INTEGER NOT NULL,
            original_per_minute_cost INTEGER NOT NULL,
            first_minute_cost INTEGER,
            original_first_minute_cost INTEGER,
            discount_percent INTEGER NOT NULL DEFAULT 0,
            starting_balance INTEGER NOT NULL,
            charged_credits INTEGER NOT NULL DEFAULT 0,
            billed_minutes INTEGER NOT NULL DEFAULT 0,
            billable_seconds INTEGER NOT NULL DEFAULT 0,
            last_heartbeat_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )
    execute(conn, "ALTER TABLE instant_billing_sessions ADD COLUMN IF NOT EXISTS first_minute_cost INTEGER")
    execute(conn, "ALTER TABLE instant_billing_sessions ADD COLUMN IF NOT EXISTS original_first_minute_cost INTEGER")
    execute(
        conn,
        """
        UPDATE instant_billing_sessions
        SET first_minute_cost = COALESCE(first_minute_cost, per_minute_cost),
            original_first_minute_cost = COALESCE(original_first_minute_cost, original_per_minute_cost)
        WHERE first_minute_cost IS NULL OR original_first_minute_cost IS NULL
        """,
    )
    execute(
        conn,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_instant_billing_one_active_user
        ON instant_billing_sessions(userid) WHERE status = 'active'
        """,
    )


def _balance_for_update(conn, userid: int) -> int:
    cur = execute(conn, "SELECT credits FROM user_credits WHERE userid = ? FOR UPDATE", (userid,))
    row = cur.fetchone()
    return int(row[0] or 0) if row else 0


def _charge(
    conn,
    *,
    userid: int,
    session_id: str,
    chat_session_id: str,
    minutes: int,
    rate: int,
    balance: int,
    phase: str,
) -> tuple[int, int]:
    minutes = max(0, int(minutes or 0))
    rate = max(1, int(rate or 1))
    charge = minutes * rate
    if charge <= 0:
        return 0, balance
    if balance < charge:
        raise InstantBillingError(
            "There are not enough credits for the next Instant Chat minute.",
            status_code=402,
            detail={
                "message": "Add credits to continue Instant Chat.",
                "required_credits": charge,
                "balance": balance,
                "per_minute_cost": rate,
            },
        )
    new_balance = balance - charge
    execute(
        conn,
        "UPDATE user_credits SET credits = ?, updated_at = CURRENT_TIMESTAMP WHERE userid = ?",
        (new_balance, userid),
    )
    execute(
        conn,
        """
        INSERT INTO credit_transactions
        (userid, transaction_type, amount, balance_after, source, reference_id, description, metadata)
        VALUES (?, 'spent', ?, ?, 'feature_usage', 'instant_chat_minutes', ?, ?)
        """,
        (
            userid,
            -charge,
            new_balance,
            "Instant Chat · first minute" if phase == "first" else f"Instant Chat · {minutes} continuing minute(s)",
            json.dumps({
                "billing_session_id": session_id,
                "chat_session_id": chat_session_id,
                "billing_phase": phase,
                "billed_minutes": minutes,
                "rate_per_minute": rate,
            }),
        ),
    )
    return charge, new_balance


def _row_locked(conn, session_id: str, userid: int):
    cur = execute(
        conn,
        """
        SELECT session_id, userid, chat_session_id, client_instance_id, status,
               per_minute_cost, original_per_minute_cost, discount_percent,
               COALESCE(first_minute_cost, per_minute_cost),
               COALESCE(original_first_minute_cost, original_per_minute_cost),
               starting_balance, charged_credits, billed_minutes, billable_seconds,
               started_at, ended_at, ended_reason,
               GREATEST(0, EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat_at)))::INTEGER AS heartbeat_gap,
               GREATEST(0, EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)))::INTEGER AS total_elapsed
        FROM instant_billing_sessions
        WHERE session_id = ? AND userid = ?
        FOR UPDATE
        """,
        (session_id, userid),
    )
    return cur.fetchone()


def _payload(row, *, balance: int) -> Dict[str, Any]:
    rate = max(1, int(row[5] or 1))
    first_rate = max(1, int(row[8] or rate))
    original_first_rate = max(1, int(row[9] or first_rate))
    billed_minutes = max(0, int(row[12] or 0))
    billable_seconds = max(0, int(row[13] or 0))
    paid_seconds_remaining = max(0, billed_minutes * 60 - billable_seconds)
    purchasable_seconds = max(0, int(balance // rate) * 60)
    remaining_seconds = paid_seconds_remaining + purchasable_seconds
    low_threshold = LOW_BALANCE_MINUTES * 60
    return {
        "session_id": row[0],
        "chat_session_id": row[2],
        "status": str(row[4] or "ended"),
        "per_minute_cost": rate,
        "original_per_minute_cost": int(row[6] or rate),
        "following_minute_cost": rate,
        "original_following_minute_cost": int(row[6] or rate),
        "first_minute_cost": first_rate,
        "original_first_minute_cost": original_first_rate,
        "subscription_discount_percent": int(row[7] or 0),
        "starting_balance": int(row[10] or 0),
        "charged_credits": int(row[11] or 0),
        "billed_minutes": billed_minutes,
        "elapsed_seconds": billable_seconds,
        "balance": int(balance),
        "remaining_seconds": remaining_seconds,
        "remaining_minutes": round(remaining_seconds / 60.0, 1),
        "low_balance": remaining_seconds < low_threshold,
        "low_balance_threshold_minutes": LOW_BALANCE_MINUTES,
        "heartbeat_interval_seconds": HEARTBEAT_INTERVAL_SECONDS,
        "reconnect_grace_seconds": RECONNECT_GRACE_SECONDS,
        "started_at": str(row[14]) if row[14] is not None else None,
        "ended_at": str(row[15]) if row[15] is not None else None,
        "ended_reason": row[16],
    }


def _settle_locked(conn, row, *, explicit_end_reason: Optional[str] = None) -> Dict[str, Any]:
    userid = int(row[1])
    status = str(row[4] or "")
    balance = _balance_for_update(conn, userid)
    if status != "active":
        return _payload(row, balance=balance)

    gap = max(0, int(row[17] or 0))
    disconnected = gap > RECONNECT_GRACE_SECONDS
    prior_billable_seconds = max(0, int(row[13] or 0))
    total_elapsed_seconds = max(prior_billable_seconds, int(row[18] or 0))
    # While heartbeats are healthy, elapsed time comes directly from the server
    # start timestamp so sub-second truncation cannot accumulate.  A genuinely
    # disconnected client is charged only through the reconnect grace window.
    billable_seconds = (
        prior_billable_seconds + RECONNECT_GRACE_SECONDS
        if disconnected
        else total_elapsed_seconds
    )
    rate = max(1, int(row[5] or 1))
    billed_minutes = max(1, int(row[12] or 1))
    wanted_minutes = max(1, int(math.ceil(max(1, billable_seconds) / 60.0)))
    additional_minutes = max(0, wanted_minutes - billed_minutes)
    affordable_minutes = balance // rate
    minutes_to_charge = min(additional_minutes, affordable_minutes)
    charge, balance = _charge(
        conn,
        userid=userid,
        session_id=str(row[0]),
        chat_session_id=str(row[2]),
        minutes=minutes_to_charge,
        rate=rate,
        balance=balance,
        phase="following",
    )
    billed_minutes += minutes_to_charge
    exhausted = minutes_to_charge < additional_minutes
    if exhausted:
        billable_seconds = min(billable_seconds, billed_minutes * 60)

    end_reason = explicit_end_reason or ("connection_lost" if disconnected else "credits_exhausted" if exhausted else None)
    next_status = "ended" if end_reason else "active"
    execute(
        conn,
        """
        UPDATE instant_billing_sessions
        SET status = ?, ended_at = CASE WHEN ? = 'ended' THEN CURRENT_TIMESTAMP ELSE ended_at END,
            charged_credits = charged_credits + ?, billed_minutes = ?, billable_seconds = ?,
            last_heartbeat_at = CURRENT_TIMESTAMP, ended_reason = COALESCE(?, ended_reason),
            updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ? AND userid = ?
        """,
        (next_status, next_status, charge, billed_minutes, billable_seconds, end_reason, row[0], userid),
    )
    updated = _row_locked(conn, str(row[0]), userid)
    return _payload(updated, balance=balance)


def _pricing(userid: int) -> tuple[int, int, int, int, int]:
    from credits.credit_service import CreditService

    credits = CreditService()
    following_base = int(credits.get_credit_setting("instant_chat_per_minute_cost") or 1)
    following_effective = int(credits.get_effective_cost(userid, following_base, "instant_chat_per_minute_cost") or following_base)
    following_original = int(credits.get_credit_setting_and_original("instant_chat_per_minute_cost")[1] or following_base)
    first_base = int(credits.get_credit_setting("instant_chat_first_minute_cost") or following_base)
    first_effective = int(credits.get_effective_cost(userid, first_base, "instant_chat_first_minute_cost") or first_base)
    first_original = int(credits.get_credit_setting_and_original("instant_chat_first_minute_cost")[1] or first_base)
    discount = int(credits.get_subscription_discount_percent(userid) or 0)
    return (
        max(1, first_effective), max(1, first_original),
        max(1, following_effective), max(1, following_original), discount,
    )


def start_session(userid: int, chat_session_id: str, client_instance_id: Optional[str] = None) -> Dict[str, Any]:
    chat_session_id = str(chat_session_id or "").strip()
    if not chat_session_id:
        raise InstantBillingError("chat_session_id is required")
    first_rate, first_original, rate, original, discount = _pricing(userid)
    with get_conn() as conn:
        ensure_table(conn)
        # A billing meter may only be attached to a conversation owned by the
        # authenticated user.  Do this before taking any credits so a forged
        # chat_session_id can never create a paid session.
        cur = execute(
            conn,
            "SELECT 1 FROM chat_sessions WHERE session_id = ? AND user_id = ?",
            (chat_session_id, userid),
        )
        if not cur.fetchone():
            raise InstantBillingError("Chat session not found", status_code=404)
        cur = execute(
            conn,
            """
            SELECT session_id FROM instant_billing_sessions
            WHERE userid = ? AND status = 'active'
            ORDER BY started_at DESC LIMIT 1 FOR UPDATE
            """,
            (userid,),
        )
        active = cur.fetchone()
        if active:
            row = _row_locked(conn, str(active[0]), userid)
            state = _settle_locked(conn, row)
            if state["status"] == "active" and state["chat_session_id"] == chat_session_id:
                conn.commit()
                state["resumed"] = True
                return state
            if state["status"] == "active":
                row = _row_locked(conn, str(active[0]), userid)
                _settle_locked(conn, row, explicit_end_reason="replaced_by_new_session")

        balance = _balance_for_update(conn, userid)
        if balance < first_rate:
            raise InstantBillingError(
                "Add credits to start Instant Chat.",
                status_code=402,
                detail={
                    "message": "You need enough credits for at least one minute.",
                    "required_credits": first_rate,
                    "balance": balance,
                    "per_minute_cost": rate,
                    "first_minute_cost": first_rate,
                    "minimum_minutes": 1,
                },
            )
        session_id = f"instant_{uuid.uuid4().hex}"
        charged, balance = _charge(
            conn,
            userid=userid,
            session_id=session_id,
            chat_session_id=chat_session_id,
            minutes=1,
            rate=first_rate,
            balance=balance,
            phase="first",
        )
        execute(
            conn,
            """
            INSERT INTO instant_billing_sessions (
                session_id, userid, chat_session_id, client_instance_id,
                per_minute_cost, original_per_minute_cost,
                first_minute_cost, original_first_minute_cost, discount_percent,
                starting_balance, charged_credits, billed_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                session_id, userid, chat_session_id, str(client_instance_id or "")[:120] or None,
                rate, original, first_rate, first_original, discount, balance + charged, charged,
            ),
        )
        row = _row_locked(conn, session_id, userid)
        result = _payload(row, balance=balance)
        conn.commit()
    result["resumed"] = False
    return result


def heartbeat_session(userid: int, session_id: str) -> Dict[str, Any]:
    with get_conn() as conn:
        ensure_table(conn)
        row = _row_locked(conn, str(session_id), userid)
        if not row:
            raise InstantBillingError("Instant Chat session not found", status_code=404)
        result = _settle_locked(conn, row)
        conn.commit()
        return result


def end_session(userid: int, session_id: str, reason: str = "user_ended") -> Dict[str, Any]:
    with get_conn() as conn:
        ensure_table(conn)
        row = _row_locked(conn, str(session_id), userid)
        if not row:
            raise InstantBillingError("Instant Chat session not found", status_code=404)
        if str(row[4] or "") != "active":
            balance = _balance_for_update(conn, userid)
            result = _payload(row, balance=balance)
            result["already_ended"] = True
        else:
            result = _settle_locked(conn, row, explicit_end_reason=str(reason or "user_ended")[:80])
        conn.commit()
        return result


def require_active_session(userid: int, session_id: str, chat_session_id: str) -> Dict[str, Any]:
    state = heartbeat_session(userid, session_id)
    if state.get("status") != "active":
        raise InstantBillingError(
            "Instant Chat session has ended.",
            status_code=402,
            detail={"message": "Start a new Instant Chat session to continue.", **state},
        )
    if str(state.get("chat_session_id")) != str(chat_session_id):
        raise InstantBillingError("Instant Chat session does not belong to this conversation", status_code=409)
    return state
