"""
HTTP endpoints: daily nudge scan (cron), device token registration (app), admin send.
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import User, get_current_user
from .service import run_nudge_scan
from . import db
from . import push as push_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nudge", tags=["nudge"])


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str  # "ios" or "android"


class AdminSendNotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
    question: Optional[str] = None  # optional; when user taps notification, prefill chat input with this
    native_id: Optional[int] = None  # optional; birth_chart id — app will set this native as selected when user taps


@router.post("/scan")
async def trigger_nudge_scan(
    scan_date: Optional[str] = Query(
        None,
        description="Date YYYY-MM-DD; default is today",
    ),
):
    """
    Run the nudge engine for the given date (or today).
    Intended to be called by a cron job or scheduler.
    """
    try:
        target = date.today()
        if scan_date:
            target = date.fromisoformat(scan_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date: {e}") from e

    try:
        summary = run_nudge_scan(target)
        return summary
    except Exception as e:
        logger.exception("Nudge scan endpoint failed: %s", e)
        raise HTTPException(status_code=500, detail="Nudge scan failed") from e


@router.post("/device-token")
async def register_device_token(
    body: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Register the device push token for the current user. Call after login when
    you have an Expo push token (ExponentPushToken[...]). Nudges will be sent
    to this device when the daily scan runs.
    """
    if not body.token or not body.platform:
        raise HTTPException(status_code=400, detail="token and platform required")
    platform = body.platform.strip().lower()
    if platform not in ("ios", "android"):
        raise HTTPException(status_code=400, detail="platform must be ios or android")
    try:
        conn = db.get_conn()
        try:
            db.init_nudge_tables(conn)
            db.save_device_token(conn, current_user.userid, body.token, platform)
        finally:
            conn.close()
        return {"ok": True, "message": "Token registered"}
    except Exception as e:
        logger.exception("Device token registration failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to register token") from e


@router.post("/admin/send")
async def admin_send_notification(
    body: AdminSendNotificationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send an arbitrary push notification to a specific user. Admin only.
    Use from admin UI: select user (by user_id), enter title and body.
    """
    logger.info(
        "Admin send notification: admin_userid=%s target_userid=%s title=%s",
        current_user.userid,
        body.user_id,
        (body.title or "")[:50],
    )
    if current_user.role != "admin":
        logger.warning("Admin send notification rejected: user role=%s", current_user.role)
        raise HTTPException(status_code=403, detail="Admin only")
    if not body.title or not body.body:
        logger.warning("Admin send notification rejected: missing title or body")
        raise HTTPException(status_code=400, detail="title and body required")
    title = (body.title or "").strip()[:100]
    body_text = (body.body or "").strip()[:200]
    if not title or not body_text:
        raise HTTPException(status_code=400, detail="title and body required")
    try:
        conn = db.get_conn()
        try:
            tokens = db.get_device_tokens_for_user(conn, body.user_id)
            if not tokens:
                logger.info(
                    "Admin send notification: user_id=%s has no device tokens",
                    body.user_id,
                )
                return {
                    "ok": False,
                    "sent": 0,
                    "tokens_found": 0,
                    "message": "User has no registered device tokens",
                }
            push_data = {"trigger_id": "admin", "cta": "astroroshni://chat"}
            if body.question and (body.question or "").strip():
                push_data["question"] = (body.question or "").strip()[:500]
            if body.native_id is not None:
                push_data["native_id"] = str(body.native_id)
            sent = 0
            for token, platform in tokens:
                if push_module.send_expo_push(
                    token,
                    title,
                    body_text,
                    data=push_data,
                ):
                    sent += 1
            channel = "push" if sent else "stored"
            db.insert_delivery(
                conn,
                userid=body.user_id,
                trigger_id="admin",
                title=title,
                body=body_text,
                sent_at=date.today(),
                event_params="{}",
                channel=channel,
            )
        finally:
            conn.close()
        logger.info(
            "Admin send notification success: user_id=%s sent=%s tokens_found=%s",
            body.user_id,
            sent,
            len(tokens),
        )
        return {
            "ok": True,
            "sent": sent,
            "tokens_found": len(tokens),
            "message": f"Notification sent to {sent} of {len(tokens)} device(s)",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Admin send notification failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send notification") from e
