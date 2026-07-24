"""
Cloud Run service for Google Play payment verification.

This service is designed for incremental rollout behind admin-controlled flags:
- main backend can proxy selected users here
- if this service is unavailable, backend falls back to legacy local handling
"""

import os
import sys
import logging
import secrets
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
import requests
from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENV_FILE = os.getenv("PLAY_PAYMENT_SERVICE_ENV_FILE", str(REPO_ROOT / ".env"))
if ENV_FILE and os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE, override=False)

from credits.routes import (  # noqa: E402
    GooglePlayVerifyRequest,
    GooglePlaySubscriptionVerifyRequest,
    _credit_verified_google_play_purchase,
    _process_pending_google_play_onetime_events_for_token,
    _sync_subscription_from_play,
    google_play_rtdn_push,
)
from credits.razorpay_routes import (  # noqa: E402
    CreateOrderBody,
    VerifyPaymentBody,
    _auth,
    _fetch_payment,
    _get_razorpay_keys,
    get_razorpay_credit_packs,
    _maybe_report_play_user_choice_credit_purchase,
    _price_paise,
    _process_captured_payment,
    _product_id,
    _verify_payment_signature,
    RAZORPAY_API_BASE,
    razorpay_webhook,
)
from activity.publisher import publish_activity  # noqa: E402
from auth import User, get_current_user  # noqa: E402
from utils.admin_settings import play_payment_service_enabled_for_user  # noqa: E402


app = FastAPI(title="play-payment-service")
logger = logging.getLogger(__name__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://astroroshni.com",
        "https://www.astroroshni.com",
        "https://test.astroroshni.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _shared_secret() -> str:
    return (os.getenv("PLAY_PAYMENT_SERVICE_SHARED_SECRET") or "").strip()


class InternalGooglePlayVerifyRequest(GooglePlayVerifyRequest):
    userid: int
    user_phone: Optional[str] = None
    user_name: Optional[str] = None


class InternalGooglePlaySubscriptionRequest(GooglePlaySubscriptionVerifyRequest):
    userid: int
    user_phone: Optional[str] = None
    user_name: Optional[str] = None


def _require_internal_secret(secret_header: Optional[str]) -> None:
    expected = _shared_secret()
    if not expected:
        raise HTTPException(status_code=503, detail="Payment service shared secret is not configured")
    if (secret_header or "").strip() != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


def _mark_payment_service_response(response: Dict[str, Any]) -> Dict[str, Any]:
    response["served_by"] = "play-payment-service"
    return response


def _log_payment_service_result(*, path: str, userid: Optional[int], order_id: Optional[str], detail: str = "") -> None:
    logger.info(
        "Play payment served_by=play-payment-service user=%s path=%s order_id=%s detail=%s",
        userid,
        path,
        (order_id or "").strip() or "n/a",
        detail or "ok",
    )


def _require_payment_service_flag_for_user(userid: Optional[int]) -> None:
    if not play_payment_service_enabled_for_user(userid):
        raise HTTPException(status_code=409, detail="Payment service is disabled for this user")


@app.get("/")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "play-payment-service"}


@app.post("/google-play/verify")
def verify_google_play_purchase_direct(
    request: GooglePlayVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    _require_payment_service_flag_for_user(current_user.userid)
    result = _credit_verified_google_play_purchase(
        userid=current_user.userid,
        user_phone=current_user.phone,
        user_name=current_user.name,
        purchase_token=request.purchase_token,
        product_id=(request.product_id or "").strip(),
        order_id_hint=(request.order_id or "").strip(),
        price_amount_micros=request.price_amount_micros,
        price_currency=request.price_currency,
        localized_price=request.localized_price,
    )
    try:
        pending_summary = _process_pending_google_play_onetime_events_for_token(
            userid=current_user.userid,
            purchase_token=request.purchase_token,
            product_id_hint=(request.product_id or "").strip() or None,
        )
        if pending_summary.get("found"):
            result["pending_rtdn_recovery"] = pending_summary
    except Exception:
        pass
    _log_payment_service_result(
        path="/google-play/verify",
        userid=current_user.userid,
        order_id=request.order_id,
        detail=str(result.get("message") or "ok"),
    )
    return _mark_payment_service_response(result)


@app.post("/internal/google-play/verify")
def internal_verify_google_play_purchase(
    request: InternalGooglePlayVerifyRequest,
    x_play_payment_service_secret: Optional[str] = Header(default=None),
):
    _require_internal_secret(x_play_payment_service_secret)
    result = _credit_verified_google_play_purchase(
        userid=request.userid,
        user_phone=request.user_phone,
        user_name=request.user_name,
        purchase_token=request.purchase_token,
        product_id=(request.product_id or "").strip(),
        order_id_hint=(request.order_id or "").strip(),
        price_amount_micros=request.price_amount_micros,
        price_currency=request.price_currency,
        localized_price=request.localized_price,
    )
    try:
        pending_summary = _process_pending_google_play_onetime_events_for_token(
            userid=request.userid,
            purchase_token=request.purchase_token,
            product_id_hint=(request.product_id or "").strip() or None,
        )
        if pending_summary.get("found"):
            result["pending_rtdn_recovery"] = pending_summary
    except Exception:
        # Keep main success path intact even if RTDN backlog recovery has an issue.
        pass
    _log_payment_service_result(
        path="/internal/google-play/verify",
        userid=request.userid,
        order_id=request.order_id,
        detail=str(result.get("message") or "ok"),
    )
    return _mark_payment_service_response(result)


@app.post("/internal/google-play/subscription/verify")
def internal_verify_google_play_subscription(
    request: InternalGooglePlaySubscriptionRequest,
    x_play_payment_service_secret: Optional[str] = Header(default=None),
):
    _require_internal_secret(x_play_payment_service_secret)
    if not (request.purchase_token or "").strip():
        raise HTTPException(status_code=400, detail="purchase_token is required")
    product_id = (request.product_id or "").strip()
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    try:
        result = _sync_subscription_from_play(
            request.userid,
            product_id,
            request.purchase_token.strip(),
            accept_any_payment_state=False,
            event_source="verify",
            order_id_hint=(request.order_id or "").strip() or None,
        )
        response = {
            "success": True,
            "message": "Subscription active",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
            "subscription_family": result.get("subscription_family", "vip"),
        }
        _log_payment_service_result(
            path="/internal/google-play/subscription/verify",
            userid=request.userid,
            order_id=request.order_id,
            detail="Subscription active",
        )
        return _mark_payment_service_response(response)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid or expired subscription: {str(exc)}")


@app.post("/internal/google-play/subscription/sync")
def internal_sync_google_play_subscription(
    request: InternalGooglePlaySubscriptionRequest,
    x_play_payment_service_secret: Optional[str] = Header(default=None),
):
    _require_internal_secret(x_play_payment_service_secret)
    if not (request.purchase_token or "").strip():
        raise HTTPException(status_code=400, detail="purchase_token is required")
    product_id = (request.product_id or "").strip()
    if not product_id:
        raise HTTPException(status_code=400, detail="product_id is required")
    try:
        result = _sync_subscription_from_play(
            request.userid,
            product_id,
            request.purchase_token.strip(),
            accept_any_payment_state=True,
            event_source="sync",
            order_id_hint=(request.order_id or "").strip() or None,
        )
        response = {
            "success": True,
            "message": "Subscription synced",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
            "subscription_family": result.get("subscription_family", "vip"),
        }
        _log_payment_service_result(
            path="/internal/google-play/subscription/sync",
            userid=request.userid,
            order_id=request.order_id,
            detail="Subscription synced",
        )
        return _mark_payment_service_response(response)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not sync subscription: {str(exc)}")


class InternalRazorpayVerifyRequest(VerifyPaymentBody):
    userid: int
    user_phone: Optional[str] = None
    user_name: Optional[str] = None


@app.post("/razorpay/create-order")
def create_razorpay_order_direct(
    body: CreateOrderBody,
    current_user: User = Depends(get_current_user),
):
    _require_payment_service_flag_for_user(current_user.userid)
    amount = _price_paise(body.credits)
    auth = _auth()
    receipt = f"u{current_user.userid}c{body.credits}{secrets.token_hex(4)}"[:40]
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
    except requests.RequestException as exc:
        logger.exception("Razorpay create order request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Could not reach payment provider") from exc
    if r.status_code not in (200, 201):
        logger.warning("Razorpay create order: %s %s", r.status_code, r.text[:500])
        raise HTTPException(status_code=502, detail="Could not create payment order. Try again later.")
    order = r.json()
    oid = order.get("id")
    if not oid:
        raise HTTPException(status_code=502, detail="Invalid response from payment provider")
    _log_payment_service_result(
        path="/razorpay/create-order",
        userid=current_user.userid,
        order_id=oid,
        detail=f"credits={body.credits}",
    )
    return {
        "order_id": oid,
        "amount": amount,
        "currency": "INR",
        "credits": body.credits,
        "product_id": _product_id(body.credits),
        "key_id": _get_razorpay_keys()[0],
    }


@app.get("/razorpay/catalog")
def razorpay_catalog_direct(current_user: User = Depends(get_current_user)):
    _require_payment_service_flag_for_user(current_user.userid)
    key_id, _ = _get_razorpay_keys()
    if not key_id:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured (set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).",
        )
    return {"key_id": key_id, "currency": "INR", "packs": get_razorpay_credit_packs()}


@app.post("/razorpay/verify")
def verify_razorpay_payment_direct(
    request: VerifyPaymentBody,
    current_user: User = Depends(get_current_user),
):
    _require_payment_service_flag_for_user(current_user.userid)
    internal = InternalRazorpayVerifyRequest(
        userid=current_user.userid,
        user_phone=current_user.phone,
        user_name=current_user.name,
        **request.model_dump(),
    )
    return internal_verify_razorpay_payment(internal, x_play_payment_service_secret=_shared_secret())


@app.post("/google-play/rtdn/push")
async def google_play_rtdn_push_direct(body: Dict[str, Any]):
    return await google_play_rtdn_push(body)


@app.post("/razorpay/webhook")
async def razorpay_webhook_direct(request: Request):
    return await razorpay_webhook(request)


@app.post("/internal/razorpay/verify")
def internal_verify_razorpay_payment(
    request: InternalRazorpayVerifyRequest,
    x_play_payment_service_secret: Optional[str] = Header(default=None),
):
    _require_internal_secret(x_play_payment_service_secret)
    if not _verify_payment_signature(
        request.razorpay_order_id.strip(),
        request.razorpay_payment_id.strip(),
        request.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment = _fetch_payment(request.razorpay_payment_id)
    notes = payment.get("notes") or {}
    if str(notes.get("userid") or "") != str(request.userid):
        raise HTTPException(status_code=403, detail="Payment does not belong to this account")

    result = _process_captured_payment(payment)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("message") or "Could not apply credits")

    gp_body_tok = (request.google_play_external_transaction_token or "").strip() or None
    _maybe_report_play_user_choice_credit_purchase(
        payment=payment,
        payment_notes=notes,
        body_token=gp_body_tok,
    )
    if result.get("credits_added"):
        publish_activity(
            "credits_purchased",
            user_id=request.userid,
            user_phone=request.user_phone,
            user_name=request.user_name,
            resource_type="payment",
            resource_id=request.razorpay_payment_id.strip(),
            metadata={
                "credits_added": result["credits_added"],
                "product_id": notes.get("product_id"),
                "order_id": request.razorpay_order_id.strip(),
                "channel": "razorpay_web",
            },
        )
    _log_payment_service_result(
        path="/internal/razorpay/verify",
        userid=request.userid,
        order_id=request.razorpay_order_id,
        detail=str(result.get("message") or "ok"),
    )
    return _mark_payment_service_response({
        "success": True,
        "message": result["message"],
        "credits_added": result["credits_added"],
    })
