"""
Razorpay Checkout for web credit purchases (INR).
Packs match mobile Google Play credit pack product IDs (see ALLOWED_CREDITS).

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

# Live catalog: Shuruaat (50) / Aashirwad (100) / Sadhak (250) / Guru (999).
# Retired: 24 and old ₹49 entry; 500 stays inactive.
ALLOWED_CREDITS: Tuple[int, ...] = (50, 100, 250, 999)

# Display names + marketing copy for recharge UI (Play listing titles may lag).
CREDIT_PACK_META: Dict[int, Dict[str, Any]] = {
    50: {
        "name": "Shuruaat Pack",
        "badge": None,
        "questions": 2,
        "save_percent": 0,
        "value_prop": "New Users - 2 Questions",
        "bonus_credits": 0,
    },
    100: {
        "name": "Aashirwad Pack",
        "badge": "Most Popular",
        "questions": 4,
        "save_percent": 10,
        "value_prop": "Most Popular - 4 Questions",
        "bonus_credits": 0,
    },
    250: {
        "name": "Sadhak Pack",
        "badge": "Best Value",
        "questions": 11,
        "save_percent": 25,
        "value_prop": "Best Value - Save 25%",
        "bonus_credits": 0,
    },
    999: {
        "name": "Guru Pack",
        "badge": "For Serious Seekers",
        "questions": 45,
        "save_percent": 0,
        "value_prop": "45 Questions with Tara",
        # 5% extra → 999 + 50 = 1049 credits on purchase
        "bonus_credits": 50,
    },
}

_DEFAULT_PRICE_PAISE: Dict[int, int] = {
    50: 9900,      # ₹99 Shuruaat Pack
    100: 19900,    # ₹199 Aashirwad Pack
    250: 49900,    # ₹499 Sadhak Pack
    999: 199900,   # ₹1999 Guru Pack
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


def get_razorpay_credit_packs() -> List[Dict[str, Any]]:
    """Active packs only — respects admin credit_product_catalog.is_active."""
    packs: List[Dict[str, Any]] = []
    active_amounts = set(credit_service.list_active_credit_amounts())
    for c in ALLOWED_CREDITS:
        if c not in active_amounts:
            continue
        paise = _expected_paise_for_pack(c)
        meta = CREDIT_PACK_META.get(c) or {}
        packs.append(
            {
                "credits": c,
                "product_id": _product_id(c),
                "amount_paise": paise,
                "amount_display": _format_inr(paise),
                "currency": "INR",
                "name": meta.get("name") or f"{c} Credits",
                "badge": meta.get("badge"),
                "questions": meta.get("questions"),
                "save_percent": meta.get("save_percent") or 0,
                "value_prop": meta.get("value_prop"),
                "pack_bonus_credits": int(meta.get("bonus_credits") or 0),
            }
        )
    return packs


def create_razorpay_credit_payment_link(
    *,
    userid: int,
    credits: int,
    name: str = "",
    phone: str = "",
    email: str = "",
) -> Dict[str, Any]:
    """Create a Razorpay Payment Link for non-browser channels like WhatsApp."""
    if credits not in ALLOWED_CREDITS:
        raise ValueError("Invalid credits pack")
    if not credit_service.is_credit_pack_sellable(credits=credits):
        raise ValueError("This credits pack is currently unavailable")

    amount = _price_paise(credits)
    receipt = f"wa{int(userid)}c{credits}{secrets.token_hex(4)}"[:40]
    product_id = _product_id(credits)
    callback_base = (os.environ.get("PUBLIC_WEB_BASE_URL") or "https://astroroshni.com").rstrip("/")
    payload: Dict[str, Any] = {
        "amount": amount,
        "currency": "INR",
        "accept_partial": False,
        "reference_id": receipt,
        "description": f"AstroRoshni {credits} credits",
        "callback_url": f"{callback_base}/credits",
        "callback_method": "get",
        "notify": {"sms": False, "email": False},
        "notes": {
            "userid": str(userid),
            "credits": str(credits),
            "product_id": product_id,
            "channel": "whatsapp",
        },
    }
    customer: Dict[str, str] = {}
    if name:
        customer["name"] = str(name)[:100]
    if phone:
        customer["contact"] = str(phone)[:20]
    if email:
        customer["email"] = str(email)[:100]
    if customer:
        payload["customer"] = customer

    try:
        r = requests.post(f"{RAZORPAY_API_BASE}/payment_links", auth=_auth(), json=payload, timeout=30)
    except requests.RequestException as e:
        logger.exception("Razorpay create payment link request failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach payment provider") from e

    if r.status_code not in (200, 201):
        logger.warning("Razorpay create payment link: %s %s", r.status_code, r.text[:500])
        raise HTTPException(status_code=502, detail="Could not create payment link. Try again later.")

    link = r.json()
    short_url = (link.get("short_url") or "").strip()
    if not short_url:
        raise HTTPException(status_code=502, detail="Invalid payment link response")
    return {
        "payment_link_id": link.get("id"),
        "short_url": short_url,
        "amount": amount,
        "currency": "INR",
        "credits": credits,
        "product_id": product_id,
        "amount_display": _format_inr(amount),
    }


class CreateOrderBody(BaseModel):
    credits: int = Field(..., description="One of 24, 50, 100, 250, 500, 999")
    google_play_external_transaction_token: Optional[str] = Field(
        default=None,
        description="User Choice billing token from Play Billing; stored on the order for Play reporting after payment.",
    )


class VerifyPaymentBody(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    google_play_external_transaction_token: Optional[str] = Field(
        default=None,
        description="Optional override; otherwise read from Razorpay order/payment notes (gp_external_tx_token).",
    )


def _verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    _, key_secret = _get_razorpay_keys()
    if not key_secret or not signature:
        return False
    msg = f"{order_id}|{payment_id}"
    expected = hmac.new(key_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _maybe_report_play_user_choice_credit_purchase(
    *,
    payment: Dict[str, Any],
    payment_notes: Dict[str, Any],
    body_token: Optional[str] = None,
) -> None:
    """If this Razorpay payment was started from Play User Choice (alternative billing), report to Google Play."""
    token = (body_token or "").strip() or str((payment_notes or {}).get("gp_external_tx_token") or "").strip()
    if not token:
        return
    payment_id = (payment.get("id") or "").strip()
    if not payment_id:
        return
    try:
        amount_paise = int(payment.get("amount") or 0)
    except (TypeError, ValueError):
        amount_paise = 0
    if amount_paise <= 0:
        logger.warning("Play external report skipped: invalid amount for payment=%s", payment_id)
        return
    try:
        from credits.play_external_transactions import report_one_time_razorpay_purchase

        result = report_one_time_razorpay_purchase(
            razorpay_payment_id=payment_id,
            external_transaction_token=token,
            amount_paise=amount_paise,
        )
        if not result.get("ok") and not result.get("skipped"):
            logger.error("Play external report failed payment=%s result=%s", payment_id, result)
    except Exception:
        logger.exception("Play external report exception payment=%s", payment_id)


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
        extras = credit_service.apply_purchase_extras(
            userid=userid,
            purchased_credits=credits,
            purchase_source=RAZORPAY_SOURCE,
            purchase_reference_id=payment_id,
            product_id=product_id,
        )
        return {
            "success": True,
            "credits_added": 0,
            "bonus_credits_added": int(extras.get("bonus_credits_added") or 0),
            "first_purchase_bonus_credits_added": int(extras.get("first_purchase_bonus_credits_added") or 0),
            "discount_credits_added": int(extras.get("discount_credits_added") or 0),
            "first_purchase_bonus": extras.get("first_purchase_bonus"),
            "purchase_discount": extras.get("purchase_discount"),
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

    extras = credit_service.apply_purchase_extras(
        userid=userid,
        purchased_credits=credits,
        purchase_source=RAZORPAY_SOURCE,
        purchase_reference_id=payment_id,
        product_id=product_id,
    )
    bonus_added = int(extras.get("bonus_credits_added") or 0)
    return {
        "success": True,
        "credits_added": credits + bonus_added,
        "purchased_credits_added": credits,
        "bonus_credits_added": bonus_added,
        "first_purchase_bonus_credits_added": int(extras.get("first_purchase_bonus_credits_added") or 0),
        "discount_credits_added": int(extras.get("discount_credits_added") or 0),
        "first_purchase_bonus": extras.get("first_purchase_bonus"),
        "purchase_discount": extras.get("purchase_discount"),
        "message": "Credits added",
        "userid": userid,
    }


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


def _notify_whatsapp_credit_purchase(userid: int, credits_added: int) -> None:
    if not userid or not credits_added:
        return
    try:
        from db import get_conn, execute
        from whatsapp.messaging import send_whatsapp_interactive_list, send_whatsapp_text

        with get_conn() as conn:
            cur = execute(
                conn,
                """
                SELECT u.whatsapp_wa_id, ws.last_phone_number_id
                FROM users u
                LEFT JOIN whatsapp_sessions ws ON ws.wa_id = u.whatsapp_wa_id
                WHERE u.userid = %s
                """,
                (int(userid),),
            )
            row = cur.fetchone()
        if not row or not row[0] or not row[1]:
            logger.info("Razorpay WhatsApp notify skipped user=%s: missing wa_id or phone_number_id", userid)
            return
        balance = credit_service.get_user_credits(int(userid))
        send_whatsapp_text(
            to_wa_id=str(row[0]),
            phone_number_id=str(row[1]),
            body=(
                f"Payment successful. Added {int(credits_added)} AstroRoshni credits.\n"
                f"Your new balance: {balance} credits.\n\n"
                "You can now choose *Ask question* to continue, or use the menu below."
            ),
        )
        send_whatsapp_interactive_list(
            to_wa_id=str(row[0]),
            phone_number_id=str(row[1]),
            body="What would you like to do next?",
            button_text="Menu",
            section_title="AstroRoshni",
            rows=[
                ("wa_ask", "Ask question", "Use selected birth chart"),
                ("wa_charts", "Choose chart", "Pick an existing chart"),
                ("wa_buy_credits", "Buy credits", "Pay with Razorpay"),
                ("wa_support", "Support", "Open or reply to ticket"),
                ("wa_add_chart", "Add new chart", "Open birth details form"),
            ],
            header_text="AstroRoshni",
            footer_text="Type Menu anytime to see options.",
        )
    except Exception:
        logger.exception("Razorpay WhatsApp credit notification failed user=%s credits=%s", userid, credits_added)


@router.get("/razorpay/catalog")
async def razorpay_catalog(current_user: User = Depends(get_current_user)):
    key_id, _ = _get_razorpay_keys()
    if not key_id:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).",
        )
    return {"key_id": key_id, "currency": "INR", "packs": get_razorpay_credit_packs()}


@router.post("/razorpay/create-order")
async def razorpay_create_order(body: CreateOrderBody, current_user: User = Depends(get_current_user)):
    if body.credits not in ALLOWED_CREDITS:
        raise HTTPException(status_code=400, detail="credits must be one of: 24, 50, 100, 250, 500, 999")
    if not credit_service.is_credit_pack_sellable(credits=body.credits):
        raise HTTPException(status_code=400, detail="This credits pack is currently unavailable")

    amount = _price_paise(body.credits)
    auth = _auth()

    receipt = f"u{current_user.userid}c{body.credits}{secrets.token_hex(4)}"
    receipt = receipt[:40]

    notes: Dict[str, str] = {
        "userid": str(current_user.userid),
        "credits": str(body.credits),
        "product_id": _product_id(body.credits),
    }
    gp_tok = (body.google_play_external_transaction_token or "").strip()
    if gp_tok:
        notes["gp_external_tx_token"] = gp_tok[:2048]

    payload = {
        "amount": amount,
        "currency": "INR",
        "receipt": receipt,
        "notes": notes,
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
    from .routes import _proxy_to_play_payment_service

    proxied = _proxy_to_play_payment_service(
        path="/internal/razorpay/verify",
        payload=body.model_dump(),
        current_user=current_user,
    )
    if proxied is not None:
        return proxied

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

    gp_body_tok = (body.google_play_external_transaction_token or "").strip() or None
    _maybe_report_play_user_choice_credit_purchase(
        payment=payment,
        payment_notes=notes,
        body_token=gp_body_tok,
    )

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
    if event.startswith("subscription."):
        from credits.razorpay_subscription_routes import process_razorpay_subscription_webhook_event

        return process_razorpay_subscription_webhook_event(payload)

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

    pay_notes = payment.get("notes") or {}
    if isinstance(pay_notes, dict):
        _maybe_report_play_user_choice_credit_purchase(
            payment=payment,
            payment_notes=pay_notes,
            body_token=None,
        )

    uid = result.get("userid")
    if result.get("credits_added") and uid:
        notes = payment.get("notes") or {}
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
                "product_id": notes.get("product_id"),
                "channel": "razorpay_webhook",
            },
        )
        if str(notes.get("channel") or "").strip().lower() == "whatsapp":
            _notify_whatsapp_credit_purchase(int(uid), int(result["credits_added"]))

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
    # Razorpay wording varies, e.g. "The payment has been fully refunded already" (no "already refunded" substring).
    if (
        "already been fully refunded" in err_l
        or "already refunded" in err_l
        or "full refund" in err_l
        or "fully refunded" in err_l
        or "refunded already" in err_l
        or ("fully" in err_l and "refund" in err_l and "payment" in err_l)
    ):
        return True, "Already refunded", data if isinstance(data, dict) else None
    return False, desc, data if isinstance(data, dict) else None
