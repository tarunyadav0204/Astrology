from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from credits.credit_service import CreditService
from db import execute, get_conn
from support_routes import create_support_ticket_for_user

router = APIRouter(tags=["order_management"])
credit_service = CreditService()

_CREDIT_PRODUCT_RE = re.compile(r"^credits_(\d+)$")


class OrderSupportBody(BaseModel):
    order_key: str = Field(..., min_length=1, max_length=160)
    issue_type: str = Field(default="support", max_length=40)
    message: Optional[str] = Field(default=None, max_length=4000)


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parse_metadata(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _credits_from_product(product_id: str, fallback: Any = None) -> Optional[int]:
    m = _CREDIT_PRODUCT_RE.match((product_id or "").strip())
    if m:
        return int(m.group(1))
    try:
        return int(fallback) if fallback is not None else None
    except (TypeError, ValueError):
        return None


def _format_amount(meta: Dict[str, Any]) -> Optional[str]:
    localized = meta.get("localized_price")
    if localized:
        return str(localized)

    currency = (meta.get("currency") or meta.get("price_currency") or "").strip().upper()
    paise = meta.get("amount_paise")
    if paise is not None:
        try:
            amount = int(paise) / 100
            if currency == "INR":
                return f"Rs {amount:,.0f}" if amount == int(amount) else f"Rs {amount:,.2f}"
            return f"{amount:,.2f} {currency}".strip()
        except (TypeError, ValueError):
            pass

    micros = meta.get("price_amount_micros")
    if micros is not None:
        try:
            amount = int(micros) / 1_000_000
            if currency == "INR":
                return f"Rs {amount:,.0f}" if amount == int(amount) else f"Rs {amount:,.2f}"
            return f"{amount:,.2f} {currency}".strip()
        except (TypeError, ValueError):
            pass
    return None


def _status(source: str, reversed_amount: int, amount: int) -> str:
    if reversed_amount <= 0:
        return "credited"
    if reversed_amount >= abs(int(amount or 0)):
        return "refunded"
    return "partially_refunded"


def _list_credit_orders(userid: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT ct.id, ct.source, ct.reference_id, ct.amount, ct.balance_after,
                   ct.description, ct.metadata, ct.created_at,
                   COALESCE(rev.reversed_amount, 0) AS reversed_amount
            FROM credit_transactions ct
            LEFT JOIN (
                SELECT userid, source, TRIM(BOTH FROM COALESCE(reference_id, '')) AS ref_key,
                       SUM(ABS(amount))::bigint AS reversed_amount
                FROM credit_transactions
                WHERE userid = ?
                  AND source IN ('razorpay_refund', 'google_play_refund')
                  AND reference_id IS NOT NULL
                GROUP BY userid, source, TRIM(BOTH FROM COALESCE(reference_id, ''))
            ) rev ON rev.userid = ct.userid
               AND rev.source = CASE
                    WHEN ct.source = 'razorpay' THEN 'razorpay_refund'
                    WHEN ct.source = 'google_play' THEN 'google_play_refund'
                    ELSE ''
               END
               AND rev.ref_key = TRIM(BOTH FROM COALESCE(ct.reference_id, ''))
            WHERE ct.userid = ?
              AND ct.transaction_type = 'earned'
              AND ct.source IN ('razorpay', 'google_play')
            ORDER BY ct.created_at DESC
            LIMIT 100
            """,
            (userid, userid),
        )
        rows = cur.fetchall() or []

    orders: List[Dict[str, Any]] = []
    for row in rows:
        tx_id, source, reference_id, amount, balance_after, description, metadata, created_at, reversed_raw = row
        meta = _parse_metadata(metadata)
        provider = "Razorpay" if source == "razorpay" else "Google Play"
        product_id = str(meta.get("product_id") or "").strip()
        credits = _credits_from_product(product_id, amount)
        payment_id = reference_id if source == "razorpay" else str(meta.get("payment_id") or "").strip()
        order_id = (
            str(meta.get("order_id") or "").strip()
            if source == "razorpay"
            else str(reference_id or meta.get("order_id") or "").strip()
        )
        reversed_amount = int(reversed_raw or 0)
        status = _status(str(source), reversed_amount, int(amount or 0))

        order_key = f"{source}:{reference_id or tx_id}"
        orders.append(
            {
                "order_key": order_key,
                "transaction_id": tx_id,
                "kind": "credit_purchase",
                "provider": provider,
                "provider_key": source,
                "product_id": product_id or (f"credits_{credits}" if credits else ""),
                "title": f"{credits} credits" if credits else (description or "Credit purchase"),
                "credits_added": int(amount or 0),
                "credits_reversed": reversed_amount or None,
                "balance_after": int(balance_after or 0),
                "status": status,
                "amount_display": _format_amount(meta),
                "currency": meta.get("currency") or meta.get("price_currency"),
                "payment_id": payment_id,
                "order_id": order_id,
                "created_at": _iso(created_at),
                "support_reference": order_id or payment_id or str(reference_id or tx_id),
                "can_request_support": True,
                "can_request_refund": status == "credited",
            }
        )
    return orders


@router.get("")
async def get_order_management(current_user: User = Depends(get_current_user)):
    orders = _list_credit_orders(current_user.userid)
    subscription = credit_service.get_user_subscription_details(current_user.userid)
    balance = credit_service.get_user_credits(current_user.userid)
    return {
        "balance": balance,
        "orders": orders,
        "subscription": subscription,
        "support_note": "Refunds and unauthorized transaction reports are handled by support after order review.",
    }


@router.post("/support")
async def create_order_support_ticket(body: OrderSupportBody, current_user: User = Depends(get_current_user)):
    orders = _list_credit_orders(current_user.userid)
    order = next((o for o in orders if o["order_key"] == body.order_key), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    issue = (body.issue_type or "support").strip().lower()
    if issue not in {"support", "refund", "unauthorized"}:
        issue = "support"

    issue_label = {
        "support": "Billing help",
        "refund": "Refund request",
        "unauthorized": "Unauthorized transaction report",
    }[issue]

    reference = order.get("support_reference") or order.get("order_key")
    details = [
        f"{issue_label} for {order.get('title') or 'order'}",
        f"Provider: {order.get('provider')}",
        f"Reference: {reference}",
        f"Status: {order.get('status')}",
    ]
    if order.get("amount_display"):
        details.append(f"Amount: {order.get('amount_display')}")
    if order.get("created_at"):
        details.append(f"Date: {order.get('created_at')}")
    if body.message and body.message.strip():
        details.extend(["", "User message:", body.message.strip()])

    ticket_id = create_support_ticket_for_user(
        current_user.userid,
        f"{issue_label}: {reference}",
        "\n".join(details),
        source="web",
    )
    return {"ticket_id": ticket_id, "message": "Support ticket created"}
