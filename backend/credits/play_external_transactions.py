"""
Report completed alternative-billing (User Choice) purchases to Google Play
using the Android Publisher API externalTransactions resource.

See: https://developer.android.com/google/play/billing/outside-gpb-backend
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from urllib.parse import quote

import requests
from google.auth.transport.requests import AuthorizedSession

logger = logging.getLogger(__name__)

PACKAGE_NAME = "com.astroroshni.mobile"

_EXTERNAL_TX_URL = (
    f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE_NAME}/externalTransactions"
)


def _sanitize_external_transaction_id(raw: str) -> str:
    """
    Google requires 1-63 chars, [a-zA-Z0-9_-] only.
    """
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", (raw or "").strip())[:63]
    s = s.strip("_") or "ext"
    return s[:63]


def _paise_to_price_micros_in_inr(paise: int) -> Tuple[str, str]:
    """
    Convert GST-inclusive amount in paise to pre-tax and tax priceMicros strings (INR).
    priceMicros = amount in 1/1_000_000 of a rupee (see Android Publisher Money type).
    """
    rate_str = (os.environ.get("RAZORPAY_GST_RATE") or "0.18").strip()
    try:
        gst_rate = float(rate_str)
    except ValueError:
        gst_rate = 0.18
    if gst_rate < 0 or gst_rate >= 1:
        gst_rate = 0.18

    total_rupees = float(paise) / 100.0
    pretax_rupees = total_rupees / (1.0 + gst_rate)
    tax_rupees = max(0.0, total_rupees - pretax_rupees)
    pre_micros = int(round(pretax_rupees * 1_000_000))
    tax_micros = int(round(tax_rupees * 1_000_000))
    return str(pre_micros), str(tax_micros)


def _user_tax_address_in() -> Dict[str, str]:
    region = (os.environ.get("PLAY_EXTERNAL_TX_REGION_CODE") or "IN").strip().upper()[:2]
    out: Dict[str, str] = {"regionCode": region or "IN"}
    if region == "IN":
        area = (os.environ.get("PLAY_EXTERNAL_TX_IN_ADMIN_AREA") or "").strip().upper()
        if area:
            out["administrativeArea"] = area
    return out


def _authorized_play_session() -> AuthorizedSession:
    from credits.routes import _get_play_credentials  # deferred: avoid import cycles at startup

    credentials = _get_play_credentials()
    if not credentials:
        raise RuntimeError("Google Play credentials not configured")
    return AuthorizedSession(credentials)


def report_one_time_razorpay_purchase(
    *,
    razorpay_payment_id: str,
    external_transaction_token: str,
    amount_paise: int,
    transaction_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Report a one-time in-app purchase completed via Razorpay after User Choice billing.

    external_transaction_token: from Play Billing UserChoiceBillingDetails.
    """
    token = (external_transaction_token or "").strip()
    if not token:
        return {"ok": False, "skipped": True, "reason": "missing_token"}

    ext_id = _sanitize_external_transaction_id(f"rzp_{razorpay_payment_id}")
    pre_micros, tax_micros = _paise_to_price_micros_in_inr(int(amount_paise))
    t = transaction_time or datetime.now(timezone.utc)
    transaction_time_iso = t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body: Dict[str, Any] = {
        "transactionTime": transaction_time_iso,
        "originalPreTaxAmount": {"currency": "INR", "priceMicros": pre_micros},
        "originalTaxAmount": {"currency": "INR", "priceMicros": tax_micros},
        "oneTimeTransaction": {"externalTransactionToken": token},
        "userTaxAddress": _user_tax_address_in(),
    }

    session = _authorized_play_session()
    url = f"{_EXTERNAL_TX_URL}?externalTransactionId={quote(ext_id, safe='')}"
    try:
        resp = session.post(url, json=body, timeout=60)
    except requests.RequestException as e:
        logger.exception("Google Play externalTransactions POST failed: %s", e)
        return {"ok": False, "error": str(e)}

    if resp.status_code in (200, 201):
        logger.info("Google Play external transaction reported id=%s payment=%s", ext_id, razorpay_payment_id)
        return {"ok": True, "external_transaction_id": ext_id, "status": resp.status_code}

    if resp.status_code == 409:
        logger.info(
            "Google Play external transaction idempotent conflict id=%s (treating as ok): %s",
            ext_id,
            resp.text[:300],
        )
        return {"ok": True, "external_transaction_id": ext_id, "status": resp.status_code, "duplicate": True}

    logger.error(
        "Google Play externalTransactions one-time failed status=%s id=%s body=%s",
        resp.status_code,
        ext_id,
        resp.text[:800],
    )
    return {"ok": False, "status": resp.status_code, "body": resp.text[:800]}


def report_recurring_initial_razorpay_subscription(
    *,
    razorpay_subscription_id: str,
    external_transaction_token: str,
    amount_paise: int,
    transaction_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Report the first charge of an external (Razorpay) subscription after User Choice billing.
    """
    token = (external_transaction_token or "").strip()
    if not token:
        return {"ok": False, "skipped": True, "reason": "missing_token"}

    ext_id = _sanitize_external_transaction_id(f"rzs_{razorpay_subscription_id}")
    pre_micros, tax_micros = _paise_to_price_micros_in_inr(int(amount_paise))
    t = transaction_time or datetime.now(timezone.utc)
    transaction_time_iso = t.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    body: Dict[str, Any] = {
        "transactionTime": transaction_time_iso,
        "originalPreTaxAmount": {"currency": "INR", "priceMicros": pre_micros},
        "originalTaxAmount": {"currency": "INR", "priceMicros": tax_micros},
        "recurringTransaction": {
            "externalTransactionToken": token,
            "externalSubscription": {"subscriptionType": "RECURRING"},
        },
        "userTaxAddress": _user_tax_address_in(),
    }

    session = _authorized_play_session()
    url = f"{_EXTERNAL_TX_URL}?externalTransactionId={quote(ext_id, safe='')}"
    try:
        resp = session.post(url, json=body, timeout=60)
    except requests.RequestException as e:
        logger.exception("Google Play externalTransactions recurring POST failed: %s", e)
        return {"ok": False, "error": str(e)}

    if resp.status_code in (200, 201):
        logger.info(
            "Google Play external recurring (initial) reported id=%s sub=%s",
            ext_id,
            razorpay_subscription_id,
        )
        return {"ok": True, "external_transaction_id": ext_id, "status": resp.status_code}

    if resp.status_code == 409:
        logger.info(
            "Google Play external recurring idempotent conflict id=%s (treating as ok): %s",
            ext_id,
            resp.text[:300],
        )
        return {"ok": True, "external_transaction_id": ext_id, "status": resp.status_code, "duplicate": True}

    logger.error(
        "Google Play externalTransactions recurring failed status=%s id=%s body=%s",
        resp.status_code,
        ext_id,
        resp.text[:800],
    )
    return {"ok": False, "status": resp.status_code, "body": resp.text[:800]}
