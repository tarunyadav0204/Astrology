"""
WhatsApp Cloud API — endpoints Meta calls on your server.

Configuration (Meta Developer → WhatsApp → Configuration):
  Callback URL:  https://<your-public-host>/api/webhooks/whatsapp
  Verify token:  same string as WHATSAPP_VERIFY_TOKEN in backend/.env

Meta sends:
  GET  — subscription verification (hub.mode, hub.verify_token, hub.challenge)
  POST — message + status events (JSON body; optional X-Hub-Signature-256)

Razorpay credit webhooks are unchanged: POST /api/credits/razorpay/webhook

Flow data channel (encrypted): POST /api/webhooks/whatsapp-flow
  Configure this URL in WhatsApp Manager → Flow → Endpoint. Requires WHATSAPP_FLOW_PRIVATE_KEY.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["whatsapp"])


def _verify_token_expected() -> str:
    return (os.environ.get("WHATSAPP_VERIFY_TOKEN") or "").strip()


def _app_secret() -> str:
    return (os.environ.get("WHATSAPP_APP_SECRET") or "").strip()


def _load_whatsapp_flow_private_key_pem() -> str:
    """
    PEM for RSA key that pairs with the public key uploaded to
    POST .../PHONE_NUMBER_ID/whatsapp_business_encryption.
    Prefer WHATSAPP_FLOW_PRIVATE_KEY_FILE on servers to avoid .env mangling.
    """
    path = (os.environ.get("WHATSAPP_FLOW_PRIVATE_KEY_FILE") or "").strip()
    if path:
        try:
            # utf-8-sig strips BOM so cryptography can parse the PEM.
            with open(path, "r", encoding="utf-8-sig") as f:
                raw = f.read().strip()
        except OSError as e:
            logger.error("whatsapp-flow: cannot read WHATSAPP_FLOW_PRIVATE_KEY_FILE=%r: %s", path, e)
            raise HTTPException(
                status_code=503,
                detail="WHATSAPP_FLOW_PRIVATE_KEY_FILE not readable",
            ) from e
        if not raw:
            raise HTTPException(status_code=503, detail="WHATSAPP_FLOW_PRIVATE_KEY_FILE is empty")
        return raw
    pem = (os.environ.get("WHATSAPP_FLOW_PRIVATE_KEY") or "").strip()
    if not pem:
        return ""
    # Some hosts wrap the whole value in quotes.
    if (pem.startswith('"') and pem.endswith('"')) or (pem.startswith("'") and pem.endswith("'")):
        pem = pem[1:-1].strip()
    return pem


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
async def whatsapp_webhook_events(request: Request, background_tasks: BackgroundTasks) -> dict[str, str]:
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

    object_type = payload.get("object")
    if object_type == "whatsapp_business_account":
        from .handlers import process_whatsapp_payload

        def _run() -> None:
            try:
                process_whatsapp_payload(payload)
            except Exception:
                logger.exception("whatsapp webhook processing failed")

        background_tasks.add_task(_run)
    else:
        logger.info("whatsapp webhook POST object=%r", object_type)

    return {"status": "ok"}


@router.post("/webhooks/whatsapp-flow")
async def whatsapp_flow_data_exchange(request: Request) -> PlainTextResponse:
    """
    WhatsApp Flows data endpoint (RSA + AES-GCM). Meta POSTs encrypted JSON;
    response is base64 ciphertext as text/plain.
    """
    body = await request.body()
    sig = request.headers.get("X-Hub-Signature-256") or request.headers.get("x-hub-signature-256")
    if not _signature_valid(body, sig):
        logger.warning("whatsapp-flow: invalid or missing X-Hub-Signature-256")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        outer = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Expected JSON body")

    for key in ("encrypted_flow_data", "encrypted_aes_key", "initial_vector"):
        if key not in outer or not isinstance(outer[key], str):
            raise HTTPException(status_code=400, detail=f"Missing or invalid field: {key}")

    try:
        private_pem = _load_whatsapp_flow_private_key_pem()
    except HTTPException:
        raise
    if not private_pem:
        logger.error("whatsapp-flow: set WHATSAPP_FLOW_PRIVATE_KEY or WHATSAPP_FLOW_PRIVATE_KEY_FILE")
        raise HTTPException(status_code=503, detail="Flow data endpoint not configured")

    from . import flow_crypto
    from . import flow_data_handler

    try:
        decrypted, aes_key, iv = flow_crypto.decrypt_flow_request(
            outer["encrypted_flow_data"],
            outer["encrypted_aes_key"],
            outer["initial_vector"],
            private_pem,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            "whatsapp-flow: decrypt failed (wrong PEM, key does not match uploaded public key, or corrupt payload): %s",
            e,
        )
        return PlainTextResponse(content="", status_code=421)

    try:
        response_obj = flow_data_handler.build_flow_data_response(decrypted)
        out_b64 = flow_crypto.encrypt_flow_response(response_obj, aes_key, iv)
    except Exception as e:
        logger.exception(
            "whatsapp-flow: handler/encrypt failed action=%r screen=%r err=%s",
            decrypted.get("action"),
            decrypted.get("screen"),
            e,
        )
        return PlainTextResponse(content="", status_code=421)

    return PlainTextResponse(content=out_b64, status_code=200, media_type="text/plain")
