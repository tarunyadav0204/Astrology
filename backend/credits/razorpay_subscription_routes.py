"""
Razorpay Subscriptions for VIP plans on web (Google Play alternative billing).

Separate from one-time credit orders in razorpay_routes.py.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from credits.razorpay_routes import RAZORPAY_API_BASE, _auth, _get_razorpay_keys, _verify_webhook_signature, _fetch_payment
from credits.credit_service import CreditService
from credits.subscription_pricing_util import (
    build_feature_pricing_for_tier,
    format_inr_from_paise,
)

logger = logging.getLogger(__name__)

router = APIRouter()
credit_service = CreditService()


class CreateSubscriptionBody(BaseModel):
    plan_id: int = Field(..., description="Internal subscription_plans.plan_id")
    google_play_external_transaction_token: Optional[str] = Field(
        default=None,
        description="User Choice billing token from Play Billing; stored on the Razorpay subscription for reporting.",
    )


class VerifySubscriptionBody(BaseModel):
    razorpay_subscription_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    google_play_external_transaction_token: Optional[str] = Field(
        default=None,
        description="Optional override; otherwise read from subscription notes (gp_external_tx_token).",
    )


class UpgradeSubscriptionBody(BaseModel):
    plan_id: int = Field(..., description="Target subscription_plans.plan_id (must be a higher tier)")


def _verify_subscription_signature(payment_id: str, subscription_id: str, signature: str) -> bool:
    _, key_secret = _get_razorpay_keys()
    if not key_secret or not signature:
        return False
    msg = f"{payment_id}|{subscription_id}"
    expected = hmac.new(key_secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _patch_razorpay_subscription(subscription_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    sub_id = (subscription_id or "").strip()
    try:
        r = requests.patch(
            f"{RAZORPAY_API_BASE}/subscriptions/{sub_id}",
            auth=_auth(),
            json=payload,
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("Razorpay patch subscription failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach payment provider")
    if r.status_code not in (200, 202):
        body = r.text[:500]
        logger.warning("Razorpay patch subscription %s: %s %s", sub_id, r.status_code, body)
        lowered = body.lower()
        if r.status_code == 400 and "upi" in lowered:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Plan changes are not supported for UPI subscriptions. "
                    "Cancel at period end and subscribe to the higher plan, or use a card subscription."
                ),
            )
        raise HTTPException(status_code=502, detail="Could not update subscription. Try again later.")
    data = r.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Invalid subscription response")
    return data


def _fetch_razorpay_subscription(subscription_id: str) -> Dict[str, Any]:
    sub_id = (subscription_id or "").strip()
    r = requests.get(f"{RAZORPAY_API_BASE}/subscriptions/{sub_id}", auth=_auth(), timeout=30)
    if r.status_code != 200:
        logger.warning("Razorpay fetch subscription %s: %s %s", sub_id, r.status_code, r.text[:300])
        raise HTTPException(status_code=502, detail="Could not verify subscription with payment provider")
    data = r.json()
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="Invalid subscription response")
    return data


def _dates_from_razorpay_subscription(sub: Dict[str, Any]) -> tuple:
    start = sub.get("current_start") or sub.get("start_at")
    end = sub.get("current_end") or sub.get("end_at")
    if not start or not end:
        raise HTTPException(status_code=400, detail="Subscription period not available yet")
    start_date = datetime.utcfromtimestamp(int(start)).strftime("%Y-%m-%d")
    end_date = datetime.utcfromtimestamp(int(end)).strftime("%Y-%m-%d")
    return start_date, end_date


def _apply_razorpay_subscription_entitlement(
    userid: int,
    internal_plan_id: int,
    product_id: str,
    razorpay_subscription_id: str,
    sub_payload: Dict[str, Any],
    *,
    cancel_at_period_end: bool = False,
) -> dict:
    start_date, end_date = _dates_from_razorpay_subscription(sub_payload)
    ok = credit_service.set_user_subscription(
        userid,
        internal_plan_id,
        start_date,
        end_date,
        billing_provider="razorpay",
        razorpay_subscription_id=razorpay_subscription_id,
        cancel_at_period_end=cancel_at_period_end,
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to update subscription")
    credit_service.upsert_razorpay_subscription_map(
        razorpay_subscription_id, userid, internal_plan_id, product_id
    )
    return {
        "start_date": start_date,
        "end_date": end_date,
        "tier_name": credit_service.get_subscription_tier_name(userid),
    }


def _notes_from_subscription(sub: Dict[str, Any]) -> Dict[str, str]:
    notes = sub.get("notes") or {}
    return {str(k): str(v) for k, v in notes.items()} if isinstance(notes, dict) else {}


def process_razorpay_subscription_webhook_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle subscription.* webhook events (called from credits webhook router)."""
    event = (payload.get("event") or "").strip()
    ent = payload.get("payload") or {}
    sub_container = ent.get("subscription") or {}
    subscription = sub_container.get("entity") if isinstance(sub_container, dict) else None
    if not isinstance(subscription, dict):
        return {"status": "ignored", "reason": "no subscription entity"}

    sub_id = (subscription.get("id") or "").strip()
    notes = _notes_from_subscription(subscription)
    userid = credit_service.get_userid_by_razorpay_subscription(sub_id)
    if userid is None and notes.get("userid", "").isdigit():
        userid = int(notes["userid"])

    internal_plan_id = None
    if notes.get("internal_plan_id", "").isdigit():
        internal_plan_id = int(notes["internal_plan_id"])
    product_id = notes.get("product_id") or ""

    if event == "subscription.updated":
        if userid is None:
            userid = credit_service.get_userid_by_razorpay_subscription(sub_id)
        rz_plan_id = (subscription.get("plan_id") or "").strip()
        plan = credit_service.get_plan_by_razorpay_plan_id(rz_plan_id) if rz_plan_id else None
        if plan:
            internal_plan_id = plan["plan_id"]
            product_id = plan.get("product_id") or product_id
        mapping = credit_service.get_razorpay_subscription_map(sub_id)
        if mapping:
            userid = userid or mapping.get("userid")
            if internal_plan_id is None:
                internal_plan_id = mapping.get("internal_plan_id")
            product_id = product_id or (mapping.get("product_id") or "")

    if event in (
        "subscription.authenticated",
        "subscription.activated",
        "subscription.charged",
        "subscription.updated",
    ):
        if userid is None or internal_plan_id is None:
            return {"status": "ignored", "reason": "unknown subscription mapping"}
        try:
            _apply_razorpay_subscription_entitlement(
                userid,
                internal_plan_id,
                product_id,
                sub_id,
                subscription,
                cancel_at_period_end=(subscription.get("status") == "cancelled"),
            )
        except HTTPException as e:
            return {"status": "error", "detail": e.detail}
        return {"status": "ok", "event": event}

    if event == "subscription.cancelled" and userid and sub_id:
        credit_service.mark_razorpay_subscription_cancel_pending(userid, sub_id)
        return {"status": "ok", "event": event}

    return {"status": "ignored", "event": event}


def _fetch_razorpay_plan_amount_display(razorpay_plan_id: str) -> Optional[str]:
    """Live monthly price from Razorpay plan (paise → ₹ display)."""
    rz_id = (razorpay_plan_id or "").strip()
    if not rz_id:
        return None
    try:
        r = requests.get(f"{RAZORPAY_API_BASE}/plans/{rz_id}", auth=_auth(), timeout=15)
    except requests.RequestException:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    if not isinstance(data, dict):
        return None
    item = data.get("item") if isinstance(data.get("item"), dict) else {}
    amount = item.get("amount") or data.get("amount")
    try:
        paise = int(amount)
    except (TypeError, ValueError):
        return None
    return format_inr_from_paise(paise)


@router.get("/razorpay/subscription/plans")
async def razorpay_subscription_plans():
    """VIP plans for web checkout (requires razorpay_plan_id on plan or env)."""
    plans = credit_service.list_razorpay_subscription_plans()
    key_id = _get_razorpay_keys()[0]
    if not key_id:
        raise HTTPException(status_code=503, detail="Razorpay is not configured")
    enriched = []
    for plan in plans:
        rz_price = _fetch_razorpay_plan_amount_display(plan.get("razorpay_plan_id") or "")
        discount = int(plan.get("discount_percent") or 0)
        enriched.append(
            {
                **plan,
                "formatted_price": rz_price,
                "amount_display": rz_price or plan.get("amount_display"),
                "feature_pricing": build_feature_pricing_for_tier(credit_service, discount),
            }
        )
    return {
        "key_id": key_id,
        "plans": enriched,
        "currency": "INR",
        "billing_period": "monthly",
        "credits_label": "credits per use",
    }


@router.post("/razorpay/subscription/create")
async def razorpay_subscription_create(body: CreateSubscriptionBody, current_user: User = Depends(get_current_user)):
    if credit_service.user_has_active_google_play_subscription(current_user.userid):
        raise HTTPException(
            status_code=409,
            detail="You already have an active subscription via Google Play. Manage it in the Play Store.",
        )
    existing = credit_service.get_user_subscription_details(current_user.userid)
    if existing and existing.get("billing_provider") == "razorpay" and not existing.get("cancel_at_period_end"):
        raise HTTPException(status_code=409, detail="You already have an active Razorpay subscription.")

    plan = credit_service.get_plan_by_internal_id(body.plan_id)
    if not plan or not plan.get("razorpay_plan_id"):
        raise HTTPException(status_code=400, detail="Plan not available for web subscription")

    payload = {
        "plan_id": plan["razorpay_plan_id"],
        "total_count": 120,
        "customer_notify": 1,
        "notes": {
            "userid": str(current_user.userid),
            "internal_plan_id": str(plan["plan_id"]),
            "product_id": plan["product_id"] or "",
        },
    }
    gp_tok = (body.google_play_external_transaction_token or "").strip()
    if gp_tok:
        payload["notes"]["gp_external_tx_token"] = gp_tok[:2048]
    try:
        r = requests.post(f"{RAZORPAY_API_BASE}/subscriptions", auth=_auth(), json=payload, timeout=30)
    except requests.RequestException as e:
        logger.exception("Razorpay create subscription failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach payment provider")

    if r.status_code not in (200, 201):
        logger.warning("Razorpay create subscription: %s %s", r.status_code, r.text[:500])
        raise HTTPException(status_code=502, detail="Could not create subscription. Try again later.")

    sub = r.json()
    sub_id = sub.get("id")
    if not sub_id:
        raise HTTPException(status_code=502, detail="Invalid response from payment provider")

    credit_service.upsert_razorpay_subscription_map(
        sub_id, current_user.userid, plan["plan_id"], plan.get("product_id") or ""
    )

    return {
        "subscription_id": sub_id,
        "key_id": _get_razorpay_keys()[0],
        "tier_name": plan["tier_name"],
        "product_id": plan["product_id"],
    }


@router.post("/razorpay/subscription/verify")
async def razorpay_subscription_verify(body: VerifySubscriptionBody, current_user: User = Depends(get_current_user)):
    if not _verify_subscription_signature(
        body.razorpay_payment_id.strip(),
        body.razorpay_subscription_id.strip(),
        body.razorpay_signature,
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    sub = _fetch_razorpay_subscription(body.razorpay_subscription_id.strip())
    notes = _notes_from_subscription(sub)
    note_uid = notes.get("userid", "")
    if note_uid.isdigit() and int(note_uid) != current_user.userid:
        raise HTTPException(status_code=403, detail="Subscription does not belong to this account")

    internal_plan_id = int(notes["internal_plan_id"]) if notes.get("internal_plan_id", "").isdigit() else None
    product_id = notes.get("product_id") or ""
    mapping = credit_service.get_razorpay_subscription_map(body.razorpay_subscription_id.strip())
    if mapping:
        if mapping["userid"] != current_user.userid:
            raise HTTPException(status_code=403, detail="Subscription does not belong to this account")
        internal_plan_id = internal_plan_id or mapping.get("internal_plan_id")
        product_id = product_id or (mapping.get("product_id") or "")
    elif note_uid.isdigit() and int(note_uid) != current_user.userid:
        raise HTTPException(status_code=403, detail="Subscription does not belong to this account")

    if internal_plan_id is None:
        raise HTTPException(status_code=400, detail="Missing plan on subscription")

    result = _apply_razorpay_subscription_entitlement(
        current_user.userid,
        internal_plan_id,
        product_id,
        body.razorpay_subscription_id.strip(),
        sub,
    )

    gp_tok = (body.google_play_external_transaction_token or "").strip() or str(
        notes.get("gp_external_tx_token") or ""
    ).strip()
    if gp_tok:
        try:
            pay = _fetch_payment(body.razorpay_payment_id.strip())
            amt = int(pay.get("amount") or 0)
            if amt > 0:
                from credits.play_external_transactions import report_recurring_initial_razorpay_subscription

                rep = report_recurring_initial_razorpay_subscription(
                    razorpay_subscription_id=body.razorpay_subscription_id.strip(),
                    external_transaction_token=gp_tok,
                    amount_paise=amt,
                )
                if not rep.get("ok") and not rep.get("skipped"):
                    logger.error(
                        "Google Play external recurring report failed sub=%s result=%s",
                        body.razorpay_subscription_id.strip(),
                        rep,
                    )
        except Exception:
            logger.exception(
                "Google Play external recurring report exception sub=%s",
                body.razorpay_subscription_id.strip(),
            )

    return {"success": True, "subscription": result}


@router.post("/razorpay/subscription/upgrade")
async def razorpay_subscription_upgrade(
    body: UpgradeSubscriptionBody, current_user: User = Depends(get_current_user)
):
    """Upgrade an active Razorpay VIP subscription to a higher tier (immediate proration)."""
    details = credit_service.get_user_subscription_details(current_user.userid)
    if not details or details.get("billing_provider") != "razorpay":
        raise HTTPException(status_code=400, detail="No active Razorpay subscription to upgrade")
    if details.get("cancel_at_period_end"):
        raise HTTPException(
            status_code=409,
            detail="Subscription is set to cancel. Subscribe again after it ends, or contact support.",
        )

    sub_id = (details.get("razorpay_subscription_id") or "").strip()
    if not sub_id:
        raise HTTPException(status_code=400, detail="Subscription id not found")

    current_plan_id = details.get("plan_id")
    current_discount = int(details.get("discount_percent") or 0)

    target = credit_service.get_plan_by_internal_id(body.plan_id)
    if not target or not target.get("razorpay_plan_id"):
        raise HTTPException(status_code=400, detail="Plan not available for web subscription")
    if target["plan_id"] == current_plan_id:
        raise HTTPException(status_code=400, detail="You are already on this plan")
    if int(target.get("discount_percent") or 0) <= current_discount:
        raise HTTPException(status_code=400, detail="Choose a higher tier to upgrade")

    sub = _fetch_razorpay_subscription(sub_id)
    status = (sub.get("status") or "").strip().lower()
    if status not in ("active", "authenticated"):
        raise HTTPException(
            status_code=409,
            detail=f"Subscription is not active (status: {status or 'unknown'}). Try again after payment completes.",
        )

    _patch_razorpay_subscription(
        sub_id,
        {
            "plan_id": target["razorpay_plan_id"],
            "schedule_change_at": "now",
            "customer_notify": True,
        },
    )

    updated = _fetch_razorpay_subscription(sub_id)
    result = _apply_razorpay_subscription_entitlement(
        current_user.userid,
        target["plan_id"],
        target.get("product_id") or "",
        sub_id,
        updated,
    )
    return {
        "success": True,
        "message": f"Upgraded to {target['tier_name']}. VIP discount applies immediately.",
        "subscription": result,
        "tier_name": target["tier_name"],
    }


@router.post("/razorpay/subscription/cancel")
async def razorpay_subscription_cancel(current_user: User = Depends(get_current_user)):
    details = credit_service.get_user_subscription_details(current_user.userid)
    if not details or details.get("billing_provider") != "razorpay":
        raise HTTPException(status_code=400, detail="No active Razorpay subscription to cancel")
    sub_id = (details.get("razorpay_subscription_id") or "").strip()
    if not sub_id:
        raise HTTPException(status_code=400, detail="Subscription id not found")

    try:
        r = requests.post(
            f"{RAZORPAY_API_BASE}/subscriptions/{sub_id}/cancel",
            auth=_auth(),
            json={"cancel_at_cycle_end": 1},
            timeout=30,
        )
    except requests.RequestException as e:
        logger.exception("Razorpay cancel subscription failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach payment provider")

    if r.status_code not in (200, 202):
        logger.warning("Razorpay cancel subscription: %s %s", r.status_code, r.text[:500])
        raise HTTPException(status_code=502, detail="Could not cancel subscription. Try again or contact support.")

    credit_service.mark_razorpay_subscription_cancel_pending(current_user.userid, sub_id)
    return {
        "success": True,
        "message": "Subscription will cancel at the end of the current billing period.",
        "end_date": details.get("end_date"),
    }
