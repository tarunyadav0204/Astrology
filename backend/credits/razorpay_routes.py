"""
Razorpay Checkout for web credit purchases (INR).
Packs match mobile Google Play: credits_50 … credits_999 (see ALLOWED_CREDITS).

Security:
- Amounts and credit counts are server-defined only.
- Client success path: HMAC verification (order_id|payment_id) + payment fetch from Razorpay API.
- Webhook: HMAC on raw body; same idempotent grant as client path (reference_id = payment_id).

Uses requests + REST API (no razorpay Python SDK) to avoid extra transitive deps.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from auth import User, get_current_user
from activity.publisher import publish_activity
from .credit_service import CreditService

logger = logging.getLogger(__name__)

router = APIRouter()
credit_service = CreditService()

RAZORPAY_SOURCE = "razorpay"
RAZORPAY_API_BASE = "https://api.razorpay.com/v1"

ALLOWED_CREDITS: Tuple[int, ...] = (50, 100, 250, 500, 999)

_DEFAULT_PRICE_PAISE: Dict[int, int] = {
    50: 4900,
    100: 9900,
    250: 22900,
    500: 44900,
    # Override with RAZORPAY_PRICE_PAISE_999 to match Play Console (paise).
    999: 84900,
}


def _get_razorpay_keys() -> Tuple[str, str]:
    key_id = (os.environ.get("RAZORPAY_KEY_ID") or "").strip()
    key_secret = (os.environ.get("RAZORPAY_KEY_SECRET") or "").strip()
    return key_id, key_secret


def _get_webhook_secret() -> str:
    return (os.environ.get("RAZORPAY_WEBHOOK_SECRET") or "").strip()


def _auth() -> HTTPBasicAuth:
    key_id, key_secret = _get_razorpay_keys()
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).",
        )
    return HTTPBasicAuth(key_id, key_secret)


def _expected_paise_for_pack(credits: int) -> int:
    """Authoritative price in paise (env override per pack)."""
    env_key = f"RAZORPAY_PRICE_PAISE_{credits}"
    raw = os.environ.get(env_key)
    if raw is not None and str(raw).strip().isdigit():
        return int(str(raw).strip())
    return _DEFAULT_PRICE_PAISE[credits]


def _price_paise(credits: int) -> int:
    if credits not in ALLOWED_CREDITS:
        raise HTTPException(status_code=400, detail="Invalid credits pack")
    return _expected_paise_for_pack(credits)


def _product_id(credits: int) -> str:
    return f"credits_{credits}"


def _format_inr(paise: int) -> str:
    rupees = paise / 100.0
    if rupees == int(rupees):
        return f"₹{int(rupees)}"
    return f"₹{rupees:.2f}"


class CreateOrderBody(BaseModel):
    credits: int = Field(..., description="One of 50, 100, 250, 500, 999")


class VerifyPaymentBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


def _verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    _, key_secret = _get_razorpay_keys()
    if not key_secret or not signature:
        return False
    msg = f"{order_id}|{payment_id}"
    expected = hmac.new(key_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _verify_webhook_signature(body: bytes, signature: Optional[str]) -> bool:
    secret = _get_webhook_secret()
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _process_captured_payment(payment: Dict[str, Any]) -> Dict[str, Any]:
    payment_id = (payment.get("id") or "").strip()
    if not payment_id:
        return {"success": False, "credits_added": 0, "message": "Missing payment id", "userid": None}

    status = (payment.get("status") or "").lower()
    if status != "captured":
        return {"success": False, "credits_added": 0, "message": f"Payment not captured (status={status})", "userid": None}

    notes = payment.get("notes") or {}
    uid_raw = str(notes.get("userid") or "").strip()
    credits_raw = str(notes.get("credits") or "").strip()
    product_id = str(notes.get("product_id") or "").strip()

    if not uid_raw.isdigit():
        return {"success": False, "credits_added": 0, "message": "Invalid order notes (userid)", "userid": None}
    userid = int(uid_raw)

    if not credits_raw.isdigit():
        return {"success": False, "credits_added": 0, "message": "Invalid order notes (credits)", "userid": None}
    credits = int(credits_raw)

    if credits not in ALLOWED_CREDITS:
        return {"success": False, "credits_added": 0, "message": "Invalid credits in notes", "userid": None}

    if product_id != _product_id(credits):
        return {"success": False, "credits_added": 0, "message": "product_id mismatch", "userid": None}

    amount_paise = payment.get("amount")
    if amount_paise is None:
        return {"success": False, "credits_added": 0, "message": "Missing amount", "userid": None}
    try:
        amount_paise = int(amount_paise)
    except (TypeError, ValueError):
        return {"success": False, "credits_added": 0, "message": "Invalid amount", "userid": None}

    expected = _expected_paise_for_pack(credits)

    if amount_paise != expected:
        logger.warning(
            "Razorpay amount mismatch payment=%s expected_paise=%s got_paise=%s",
            payment_id,
            expected,
            amount_paise,
        )
        return {"success": False, "credits_added": 0, "message": "Amount mismatch", "userid": userid}

    if credit_service.has_transaction_with_reference(userid, RAZORPAY_SOURCE, payment_id):
        return {
            "success": True,
            "credits_added": 0,
            "message": "Already credited",
            "userid": userid,
        }

    meta = json.dumps(
        {
            "payment_id": payment_id,
            "order_id": payment.get("order_id"),
            "amount_paise": amount_paise,
            "currency": payment.get("currency"),
            "product_id": product_id,
            "method": payment.get("method"),
        }
    )

    ok = credit_service.add_credits(
        userid,
        credits,
        RAZORPAY_SOURCE,
        reference_id=payment_id,
        description=f"Razorpay: {product_id}",
        metadata=meta,
    )
    if not ok:
        logger.error("Razorpay: add_credits failed user=%s payment=%s", userid, payment_id)
        return {
            "success": False,
            "credits_added": 0,
            "message": "Could not apply credits. Contact support with payment id.",
            "userid": userid,
        }

    return {"success": True, "credits_added": credits, "message": "Credits added", "userid": userid}


def _fetch_payment(payment_id: str) -> Dict[str, Any]:
    auth = _auth()
    r = requests.get(
        f"{RAZORPAY_API_BASE}/payments/{payment_id.strip()}",
        auth=auth,
        timeout=30,
    )
    if r.status_code != 200:
        logger.warning("Razorpay GET payment %s: %s %s", payment_id, r.status_code, r.text[:300])
        raise HTTPException(status_code=502, detail="Could not fetch payment from provider")
    return r.json()


@router.get("/razorpay/catalog")
async def razorpay_catalog(current_user: User = Depends(get_current_user)):
    key_id, _ = _get_razorpay_keys()
    if not key_id:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).",
        )
    packs: List[Dict[str, Any]] = []
    for c in ALLOWED_CREDITS:
        paise = _price_paise(c)
        packs.append(
            {
                "credits": c,
                "product_id": _product_id(c),
                "amount_paise": paise,
                "amount_display": _format_inr(paise),
                "currency": "INR",
            }
        )
    return {"key_id": key_id, "currency": "INR", "packs": packs}


@router.post("/razorpay/create-order")
async def razorpay_create_order(body: CreateOrderBody, current_user: User = Depends(get_current_user)):
    if body.credits not in ALLOWED_CREDITS:
        raise HTTPException(status_code=400, detail="credits must be one of: 50, 100, 250, 500, 999")

    amount = _price_paise(body.credits)
    auth = _auth()

    receipt = f"u{current_user.userid}c{body.credits}{secrets.token_hex(4)}"
    receipt = receipt[:40]

    payload = {
        "amount": amount,
        "currency": "INR",
        "receipt": receipt,
        "notes": {
            "userid": str(current_user.userid),
            "credits": str(body.credits),
            "product_id": _product_id(body.credits),
        },
    }

    try:
        r = requests.post(f"{RAZORPAY_API_BASE}/orders", auth=auth, json=payload, timeout=30)
    except requests.RequestException as e:
        logger.exception("Razorpay create order request failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach payment provider")

    if r.status_code not in (200, 201):
        logger.warning("Razorpay create order: %s %s", r.status_code, r.text[:500])
        raise HTTPException(status_code=502, detail="Could not create payment order. Try again later.")

    order = r.json()
    oid = order.get("id")
    if not oid:
        raise HTTPException(status_code=502, detail="Invalid response from payment provider")

    return {
        "order_id": oid,
        "amount": amount,
        "currency": "INR",
        "credits": body.credits,
        "product_id": _product_id(body.credits),
        "key_id": _get_razorpay_keys()[0],
    }


@router.post("/razorpay/verify")
async def razorpay_verify(body: VerifyPaymentBody, current_user: User = Depends(get_current_user)):
    if not _verify_payment_signature(
        body.razorpay_order_id.strip(),
        body.razorpay_payment_id.strip(),
        body.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment = _fetch_payment(body.razorpay_payment_id)
    notes = payment.get("notes") or {}
    if str(notes.get("userid") or "") != str(current_user.userid):
        raise HTTPException(status_code=403, detail="Payment does not belong to this account")

    result = _process_captured_payment(payment)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message") or "Could not apply credits")

    uid = result.get("userid")
    if result["credits_added"] and uid:
        publish_activity(
            "credits_purchased",
            user_id=uid,
            user_phone=current_user.phone,
            user_name=current_user.name,
            resource_type="payment",
            resource_id=body.razorpay_payment_id.strip(),
            metadata={
                "credits_added": result["credits_added"],
                "product_id": notes.get("product_id"),
                "order_id": body.razorpay_order_id.strip(),
                "channel": "razorpay_web",
            },
        )

    return {
        "success": True,
        "message": result["message"],
        "credits_added": result["credits_added"],
    }


@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Razorpay-Signature")

    if not _verify_webhook_signature(body, sig):
        logger.warning("Razorpay webhook: bad signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = (payload.get("event") or "").strip()
    if event != "payment.captured":
        return {"status": "ignored", "event": event or "unknown"}

    ent = payload.get("payload") or {}
    pay_container = ent.get("payment") or {}
    payment = pay_container.get("entity") if isinstance(pay_container, dict) else None
    if not isinstance(payment, dict):
        return {"status": "ignored", "reason": "no payment entity"}

    result = _process_captured_payment(payment)
    if not result["success"]:
        logger.warning("Razorpay webhook grant failed: %s", result)
        return {"status": "not_applied", "message": result.get("message")}

    uid = result.get("userid")
    if result.get("credits_added") and uid:
        try:
            from db import get_conn, execute

            with get_conn() as conn:
                cur = execute(conn, "SELECT phone, name FROM users WHERE userid = ?", (uid,))
                row = cur.fetchone()
            phone = row[0] if row else ""
            name = row[1] if row else ""
        except Exception:
            phone, name = "", ""

        publish_activity(
            "credits_purchased",
            user_id=uid,
            user_phone=phone,
            user_name=name,
            resource_type="payment",
            resource_id=(payment.get("id") or ""),
            metadata={
                "credits_added": result["credits_added"],
                "channel": "razorpay_webhook",
            },
        )

    return {"status": "ok", "credits_added": result.get("credits_added", 0)}


def fetch_razorpay_payment(payment_id: str) -> Dict[str, Any]:
    """GET /v1/payments/{id} — used by admin refund to resolve amounts when metadata is missing."""
    return _fetch_payment(payment_id)


def refund_razorpay_payment(payment_id: str, amount_paise: Optional[int] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    POST /v1/payments/{id}/refund. amount_paise None = full refund (omit amount in body).
    Returns (success, message, response_json_or_none).
    """
    key_id, key_secret = _get_razorpay_keys()
    if not key_id or not key_secret:
        return False, "Razorpay is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)", None
    pid = (payment_id or "").strip()
    if not pid:
        return False, "Missing payment id", None
    url = f"{RAZORPAY_API_BASE}/payments/{pid}/refund"
    payload: Dict[str, Any] = {}
    if amount_paise is not None:
        ap = int(amount_paise)
        if ap < 1:
            return False, "Invalid refund amount (paise)", None
        payload["amount"] = ap
    try:
        r = requests.post(url, auth=HTTPBasicAuth(key_id, key_secret), json=payload, timeout=45)
    except requests.RequestException as e:
        logger.exception("Razorpay refund POST failed: %s", e)
        return False, str(e), None
    try:
        data = r.json() if r.text else {}
    except json.JSONDecodeError:
        data = {}
    if r.status_code in (200, 201):
        st = (data.get("status") or "created") if isinstance(data, dict) else "ok"
        return True, str(st), data if isinstance(data, dict) else None
    err_obj = data.get("error") if isinstance(data, dict) else None
    desc = ""
    if isinstance(err_obj, dict):
        desc = (err_obj.get("description") or err_obj.get("code") or "") or ""
    if not desc and isinstance(data, dict):
        desc = str(data.get("message") or "")
    if not desc:
        desc = (r.text or "")[:500]
    err_l = desc.lower()
    if "already been fully refunded" in err_l or "already refunded" in err_l or "full refund" in err_l:
        return True, "Already refunded", data if isinstance(data, dict) else None
    return False, desc, data if isinstance(data, dict) else None
