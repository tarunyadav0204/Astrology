"""
WhatsApp Cloud API — endpoints Meta calls on your server.

Configuration (Meta Developer → WhatsApp → Configuration):
  Callback URL:  https://<your-public-host>/api/webhooks/whatsapp
  Verify token:  same string as WHATSAPP_VERIFY_TOKEN in backend/.env

Meta sends:
  GET  — subscription verification (hub.mode, hub.verify_token, hub.challenge)
  POST — message + status events (JSON body; optional X-Hub-Signature-256)

Razorpay credit webhooks are unchanged: POST /api/credits/razorpay/webhook
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whatsapp"])


def _verify_token_expected() -> str:
    return (os.environ.get("WHATSAPP_VERIFY_TOKEN") or "").strip()


def _app_secret() -> str:
    return (os.environ.get("WHATSAPP_APP_SECRET") or "").strip()


def _signature_valid(body: bytes, signature_header: Optional[str]) -> bool:
    secret = _app_secret()
    if not secret:
        return True  # dev: allow unsigned if secret not configured
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected_hex = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    received = signature_header[7:].strip()
    if len(received) != len(expected_hex):
        return False
    return hmac.compare_digest(received, expected_hex)


def _log_payload_preview(payload: dict[str, Any]) -> None:
    try:
        preview = json.dumps(payload, default=str)[:2000]
    except Exception:
        preview = str(payload)[:2000]
    logger.info("whatsapp webhook POST preview: %s", preview)


@router.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request) -> PlainTextResponse:
    """
    Meta subscription verification. Must return hub.challenge as plain text (200).
    Query keys use dots: hub.mode, hub.verify_token, hub.challenge.
    """
    qp = request.query_params
    mode = qp.get("hub.mode")
    token = qp.get("hub.verify_token")
    challenge = qp.get("hub.challenge")

    expected = _verify_token_expected()
    if not expected:
        logger.warning("whatsapp verify: WHATSAPP_VERIFY_TOKEN is not set")
        raise HTTPException(status_code=503, detail="WhatsApp verify token not configured")

    if mode == "subscribe" and token == expected and challenge:
        return PlainTextResponse(content=str(challenge), status_code=200)

    logger.warning("whatsapp verify: rejected mode=%r token_match=%s", mode, token == expected)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook_events(request: Request) -> dict[str, str]:
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")
    if not _signature_valid(body, sig):
        logger.warning("whatsapp webhook: invalid or missing X-Hub-Signature-256")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        logger.warning("whatsapp webhook: non-JSON body")
        raise HTTPException(status_code=400, detail="Expected JSON body")

    # Acknowledge quickly; heavy work should go to a background queue later.
    object_type = payload.get("object")
    if object_type == "whatsapp_business_account":
        _log_payload_preview(payload)
        # TODO: parse entry[].changes[] → messages / statuses → birth chart / chat / payment deep links
    else:
        logger.info("whatsapp webhook POST object=%r", object_type)

    return {"status": "ok"}
