"""
Cloud Run service for Google Play payment verification.

This service is designed for incremental rollout behind admin-controlled flags:
- main backend can proxy selected users here
- if this service is unavailable, backend falls back to legacy local handling
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
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
)


app = FastAPI(title="play-payment-service")


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


@app.get("/")
def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "play-payment-service"}


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
        return _mark_payment_service_response({
            "success": True,
            "message": "Subscription active",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        })
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
        return _mark_payment_service_response({
            "success": True,
            "message": "Subscription synced",
            "subscription_tier_name": result["tier_name"],
            "end_date": result["end_date"],
        })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not sync subscription: {str(exc)}")
