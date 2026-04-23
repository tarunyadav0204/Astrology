"""
HTTP endpoints: daily nudge scan (cron), device token registration (app), admin send,
in-app inbox for stored nudges.
"""
import json
import logging
import os
import hmac
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Header, BackgroundTasks
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import get_conn, execute
from .service import run_nudge_scan
from . import db
from . import push as push_module
from .config_validate import ConfigValidationError, validate_and_normalize_config
from .template_render import TemplateRenderError, validate_templates
from .trigger_defaults import get_spec, list_registered_trigger_keys
from .trigger_def_loader import load_merged_definition
from utils.smtp_mail import send_plain_text_email

logger = logging.getLogger(__name__)
IST_TZ = ZoneInfo("Asia/Kolkata")

router = APIRouter(prefix="/nudge", tags=["nudge"])


def _verify_cron_secret(x_cron_secret: Optional[str]) -> None:
    expected = (os.getenv("NUDGE_CRON_SECRET") or "").strip()
    received = (x_cron_secret or "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="NUDGE_CRON_SECRET is not configured on server.",
        )
    if not received or not hmac.compare_digest(received, expected):
        raise HTTPException(status_code=401, detail="Invalid cron secret")


class DeviceTokenRequest(BaseModel):
    token: str
    platform: str  # "ios" or "android"


class AdminSendNotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str
    question: Optional[str] = None  # optional; when user taps notification, prefill chat input with this
    native_id: Optional[int] = None  # optional; birth_chart id — app will set this native as selected when user taps


class AdminGenerateNudgeFromChatRequest(BaseModel):
    user_id: int


class AdminSendBlogNotificationRequest(BaseModel):
    blog_id: int
    audience: str = "all"  # "all" or "eligible"
    user_ids: Optional[List[int]] = None  # optional explicit user selection


class AdminEmailNudgeReminderRequest(BaseModel):
    user_ids: Optional[List[int]] = None  # explicit targeting (must be non-empty unless send_all_eligible)
    send_all_eligible: bool = False  # send to every user with email and no device token (optional name filter)
    name: Optional[str] = None  # optional ILIKE filter on display name or email (admin search parity)
    subject: Optional[str] = None
    body: Optional[str] = None


_ELIGIBLE_OPTIN_FROM_SQL = """
FROM users u
LEFT JOIN (
    SELECT DISTINCT userid FROM device_tokens
) dt ON dt.userid = u.userid
"""


def _eligible_notification_optin_where(name: Optional[str]) -> tuple[str, List[Any]]:
    """WHERE clause fragment + params: has email, no device token, optional name/email search."""
    parts = [
        "COALESCE(NULLIF(TRIM(u.email), ''), '') <> ''",
        "dt.userid IS NULL",
    ]
    params: List[Any] = []
    if name and str(name).strip():
        pat = f"%{str(name).strip()}%"
        parts.append("(u.name ILIKE ? OR COALESCE(u.email, '') ILIKE ?)")
        params.extend([pat, pat])
    return " AND ".join(parts), params


class MarkNudgesReadRequest(BaseModel):
    """If ids is omitted or empty, mark all nudges read for the current user."""
    ids: Optional[List[int]] = None


class TriggerDefinitionUpdateRequest(BaseModel):
    """Admin-editable copy (templates) and JSON config for a registered nudge trigger."""

    enabled: bool = True
    priority: Optional[int] = Field(None, ge=0, le=200)
    title_template: str
    body_template: str
    question_template: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)


class BroadcastScheduleCreateRequest(BaseModel):
    template_id: int
    send_date: str  # YYYY-MM-DD
    send_time: str  # HH:MM
    is_active: bool = True


class BroadcastTemplateCreateRequest(BaseModel):
    title: str
    body: str
    category: str = "general"
    is_active: bool = True


def _admin_trigger_dto(merged, spec) -> Dict[str, Any]:
    return {
        "trigger_key": merged.trigger_key,
        "enabled": merged.enabled,
        "priority": merged.priority,
        "title_template": merged.title_template,
        "body_template": merged.body_template,
        "question_template": merged.question_template,
        "config": merged.config,
        "allowed_placeholders": sorted(spec.allowed_placeholders),
        "config_schema": spec.config_schema,
        "default_priority": spec.default_priority,
    }


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
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            db.save_device_token(conn, current_user.userid, body.token, platform)
            conn.commit()
        return {"ok": True, "message": "Token registered"}
    except Exception as e:
        logger.exception("Device token registration failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to register token") from e


@router.get("/admin/user-ids-with-tokens")
async def get_user_ids_with_tokens(
    current_user: User = Depends(get_current_user),
):
    """Return list of user_ids that have at least one device token (notifications accepted). Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        with db.get_conn() as conn:
            rows = db.get_all_device_tokens(conn)
            user_ids = list({r[0] for r in rows})
        return {"user_ids": user_ids}
    except Exception as e:
        logger.exception("Failed to get user ids with tokens: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load") from e


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
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            tokens = db.get_device_tokens_for_user(conn, body.user_id)
            push_data: Dict[str, Any] = {"trigger_id": "admin", "cta": "astroroshni://chat"}
            if body.question and (body.question or "").strip():
                push_data["question"] = (body.question or "").strip()[:500]
            if body.native_id is not None:
                push_data["native_id"] = str(body.native_id)
            sent = 0
            if tokens:
                for token, platform in tokens:
                    if push_module.send_expo_push(
                        token,
                        title,
                        body_text,
                        data=push_data,
                    ):
                        sent += 1
            channel = "push" if sent > 0 else "stored"
            db.insert_delivery(
                conn,
                userid=body.user_id,
                trigger_id="admin",
                title=title,
                body=body_text,
                sent_at=date.today(),
                event_params="{}",
                channel=channel,
                data_payload=push_data,
            )
            conn.commit()
        logger.info(
            "Admin send notification success: user_id=%s sent=%s tokens_found=%s",
            body.user_id,
            sent,
            len(tokens or []),
        )
        return {
            "ok": True,
            "sent": sent,
            "tokens_found": len(tokens or []),
            "message": (
                f"Notification sent to {sent} of {len(tokens or [])} device(s); "
                "also saved to in-app inbox."
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Admin send notification failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send notification") from e


@router.post("/admin/generate-nudge-from-chat")
async def admin_generate_nudge_from_chat(
    body: AdminGenerateNudgeFromChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Admin only. Load the user's last 1–2 completed chat Q&A turns and ask Gemini for
    push title, body, and a suggested chat question; used to pre-fill the custom notification form.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        from .chat_nudge_suggestion import load_last_completed_qa_turns, generate_push_nudge_via_gemini

        with db.get_conn() as conn:
            turns = load_last_completed_qa_turns(conn, body.user_id, max_turns=2)
        if not turns:
            raise HTTPException(
                status_code=400,
                detail="No completed chat question-and-answer pairs found for this user.",
            )
        out = generate_push_nudge_via_gemini(turns)
        return {
            "ok": True,
            "title": out["title"],
            "body": out["body"],
            "question": out["question"],
            "qa_pairs_used": len(turns),
            "model_used": out.get("model_used"),
            "usage_estimate": out.get("usage_estimate"),
        }
    except HTTPException:
        raise
    except RuntimeError as e:
        msg = str(e)
        if "GEMINI_API_KEY" in msg:
            raise HTTPException(status_code=503, detail=msg) from e
        raise HTTPException(status_code=502, detail=msg) from e
    except Exception as e:
        logger.exception("admin_generate_nudge_from_chat failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate nudge from chat") from e


@router.post("/admin/send-blog")
async def admin_send_blog_notification(
    body: AdminSendBlogNotificationRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a push notification for a specific blog post to many users.
    The notification uses the blog's title and featured image; the app can open the blog detail screen.
    """
    if current_user.role != "admin":
        logger.warning("Admin send blog notification rejected: user role=%s", current_user.role)
        raise HTTPException(status_code=403, detail="Admin only")
    if not body.blog_id:
        raise HTTPException(status_code=400, detail="blog_id required")

    try:
        with get_conn() as blog_conn:
            cur = execute(
                blog_conn,
                "SELECT id, title, slug, featured_image, status FROM blog_posts WHERE id = %s",
                (body.blog_id,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Blog post not found")
        blog_id, title, slug, featured_image, status = row
        if status != "published":
            raise HTTPException(status_code=400, detail="Blog post must be published")

        notif_title = (title or "").strip()[:100] or "New blog on AstroRoshni"
        notif_body = "Tap to read this new article on AstroRoshni."

        with db.get_conn() as conn:
            # Ensure nudge tables (including device_tokens) exist
            db.init_nudge_tables(conn)

            # Get all distinct user IDs that have at least one device token
            all_tokens: List[tuple] = db.get_all_device_tokens(conn)
            if not all_tokens:
                return {
                    "ok": False,
                    "sent": 0,
                    "tokens_found": 0,
                    "message": "No device tokens registered",
                }

            # Group tokens by user_id
            tokens_by_user = {}
            for userid, token, platform in all_tokens:
                tokens_by_user.setdefault(userid, []).append((token, platform))

            # If explicit user_ids provided, restrict to those
            target_user_ids: Optional[List[int]] = None
            if body.user_ids:
                target_user_ids = [int(u) for u in body.user_ids if isinstance(u, int) or str(u).isdigit()]

            sent = 0
            total_tokens = 0
            for userid, tokens in tokens_by_user.items():
                if target_user_ids is not None and userid not in target_user_ids:
                    continue

                # audience == "eligible" is same as "all" here since all have tokens for these users,
                # but we keep the parameter for future filtering.
                push_data = {
                    "trigger_id": "blog",
                    "cta": "astroroshni://blog",
                    "blog_id": str(blog_id),
                    "slug": slug or "",
                }
                user_sent = 0
                for token, platform in tokens:
                    total_tokens += 1
                    if push_module.send_expo_push(
                        token,
                        notif_title,
                        notif_body,
                        data=push_data,
                        image_url=featured_image if featured_image else None,
                    ):
                        sent += 1
                        user_sent += 1
                channel = "push" if user_sent else "stored"
                ep = json.dumps({"blog_id": blog_id, "slug": slug or ""}, ensure_ascii=False)
                db.insert_delivery(
                    conn,
                    userid=userid,
                    trigger_id="blog_admin",
                    title=notif_title,
                    body=notif_body,
                    sent_at=date.today(),
                    event_params=ep,
                    channel=channel,
                    data_payload=push_data,
                )
            conn.commit()

        logger.info(
            "Admin send blog notification success: blog_id=%s users=%s tokens_sent=%s",
            blog_id,
            len(tokens_by_user),
            sent,
        )
        return {
            "ok": True,
            "sent": sent,
            "tokens_found": total_tokens,
            "message": f"Notification sent to {sent} of {total_tokens} device(s)",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Admin send blog notification failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send blog notification") from e


@router.get("/admin/notification-optin-email-eligible-ids")
async def admin_notification_optin_email_eligible_ids(
    current_user: User = Depends(get_current_user),
    name: Optional[str] = Query(None, description="Filter by display name or email (partial, case-insensitive)"),
    limit: int = Query(20000, ge=1, le=50000, description="Max user IDs returned"),
):
    """
    List user IDs eligible for the notification opt-in email (has email, no device token).
    Used by admin UI to select all matching users across pages.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    where_extra, params = _eligible_notification_optin_where(name)
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            cur = execute(
                conn,
                f"SELECT COUNT(*) {_ELIGIBLE_OPTIN_FROM_SQL} WHERE {where_extra}",
                tuple(params),
            )
            total = int((cur.fetchone() or (0,))[0] or 0)

            cur = execute(
                conn,
                f"""
                SELECT u.userid
                {_ELIGIBLE_OPTIN_FROM_SQL}
                WHERE {where_extra}
                ORDER BY u.userid ASC
                LIMIT ?
                """,
                tuple(params + [limit]),
            )
            rows = cur.fetchall() or []
            ids = [int(r[0]) for r in rows]

        truncated = total > len(ids)
        return {
            "ok": True,
            "total": total,
            "user_ids": ids,
            "truncated": truncated,
            "limit": limit,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_notification_optin_email_eligible_ids failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to list eligible users") from e


@router.post("/admin/send-notification-optin-email")
async def admin_send_notification_optin_email(
    body: AdminEmailNudgeReminderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send an email reminder to users who do not have any registered device token.
    Uses the same SMTP provider used by OTP/support emails.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    default_subject = "Turn on AstroRoshni notifications for timely life signals"
    default_body = (
        "Hi,\n\n"
        "You are currently missing timely in-app signals from AstroRoshni.\n"
        "Please enable notifications in your device settings so you can receive important alerts "
        "about life events, timing windows, and planetary shifts right when they matter.\n\n"
        "Open AstroRoshni > Settings > Notifications and switch alerts ON.\n\n"
        "Warm regards,\n"
        "Team AstroRoshni"
    )
    subject = (body.subject or default_subject).strip()[:200]
    msg = (body.body or default_body).strip()[:4000]
    if not subject or not msg:
        raise HTTPException(status_code=400, detail="subject and body are required")

    clean_ids = [
        int(x)
        for x in (body.user_ids or [])
        if isinstance(x, int) or (isinstance(x, str) and str(x).isdigit())
    ]
    if body.send_all_eligible:
        if clean_ids:
            raise HTTPException(
                status_code=400,
                detail="Do not pass user_ids when send_all_eligible is true",
            )
    elif clean_ids:
        pass
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide non-empty user_ids or set send_all_eligible to true",
        )

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)

            where_extra, params = _eligible_notification_optin_where(
                body.name if body.send_all_eligible else None
            )
            params = list(params)
            where_sql = f"WHERE {where_extra}"
            if not body.send_all_eligible:
                placeholders = ",".join(["?"] * len(clean_ids))
                where_sql += f" AND u.userid IN ({placeholders})"
                params.extend(clean_ids)

            cur = execute(
                conn,
                f"""
                SELECT u.userid, COALESCE(TRIM(u.name), ''), TRIM(u.email)
                {_ELIGIBLE_OPTIN_FROM_SQL}
                {where_sql}
                ORDER BY u.userid ASC
                """,
                tuple(params),
            )
            rows = cur.fetchall() or []

        if not rows:
            return {
                "ok": True,
                "targeted_users": 0,
                "emails_sent": 0,
                "message": "No eligible users without notifications and with email found.",
            }

        emails_sent = 0
        failures = 0
        for uid, name, email in rows:
            greeting = f"Hi {name}," if name else "Hi,"
            if msg.startswith("Hi,\n\n"):
                personalized = f"{greeting}\n\n{msg[5:]}"
            else:
                personalized = msg
            ok = send_plain_text_email(email, subject, personalized)
            if ok:
                emails_sent += 1
            else:
                failures += 1
                logger.warning("Failed opt-in reminder email to user_id=%s email=%s", uid, email)

        return {
            "ok": True,
            "targeted_users": len(rows),
            "emails_sent": emails_sent,
            "failures": failures,
            "message": f"Sent {emails_sent} reminder email(s) out of {len(rows)} targeted users.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_send_notification_optin_email failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send reminder emails") from e


def _delivery_row_to_item(row: tuple) -> Dict[str, Any]:
    (
        rid,
        trigger_id,
        title,
        body,
        event_params,
        data_json_raw,
        sent_at,
        channel,
        created_at,
        read_at,
    ) = row
    data: Optional[Dict[str, Any]] = None
    if data_json_raw:
        try:
            data = json.loads(data_json_raw)
        except Exception:
            data = None
    def _iso(val):
        if val is None:
            return None
        if hasattr(val, "isoformat"):
            return val.isoformat()
        return str(val)

    return {
        "id": int(rid),
        "trigger_id": trigger_id,
        "title": title,
        "body": body,
        "event_params": event_params,
        "data": data,
        "sent_at": str(sent_at) if sent_at is not None else None,
        "channel": channel,
        "created_at": _iso(created_at),
        "read_at": _iso(read_at),
    }


@router.get("/inbox")
async def get_nudge_inbox(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """List nudges saved for this user (daily nudges, admin sends, blog announcements)."""
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        rows = db.list_deliveries_for_user(conn, current_user.userid, limit=limit, offset=offset)
        unread = db.count_unread_deliveries(conn, current_user.userid)
    return {"items": [_delivery_row_to_item(r) for r in rows], "unread_count": unread}


@router.get("/inbox/unread-count")
async def get_nudge_inbox_unread_count(current_user: User = Depends(get_current_user)):
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        n = db.count_unread_deliveries(conn, current_user.userid)
    return {"unread_count": n}


@router.post("/inbox/mark-read")
async def post_mark_nudges_read(
    body: MarkNudgesReadRequest,
    current_user: User = Depends(get_current_user),
):
    with db.get_conn() as conn:
        db.init_nudge_tables(conn)
        updated = db.mark_deliveries_read(conn, current_user.userid, body.ids)
        conn.commit()
    return {"ok": True, "updated": updated}


@router.get("/admin/trigger-definitions")
async def admin_list_trigger_definitions(current_user: User = Depends(get_current_user)):
    """List configurable nudge triggers with merged DB defaults (admin)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            items = []
            for key in list_registered_trigger_keys():
                merged = load_merged_definition(conn, key)
                spec = get_spec(key)
                if spec:
                    items.append(_admin_trigger_dto(merged, spec))
        return {"triggers": items}
    except Exception as e:
        logger.exception("admin_list_trigger_definitions: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load trigger definitions") from e


@router.get("/admin/trigger-definitions/{trigger_key}")
async def admin_get_trigger_definition(
    trigger_key: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    spec = get_spec(trigger_key)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown trigger_key")
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            merged = load_merged_definition(conn, trigger_key)
        return _admin_trigger_dto(merged, spec)
    except Exception as e:
        logger.exception("admin_get_trigger_definition: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load trigger definition") from e


@router.put("/admin/trigger-definitions/{trigger_key}")
async def admin_put_trigger_definition(
    trigger_key: str,
    body: TriggerDefinitionUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    spec = get_spec(trigger_key)
    if not spec:
        raise HTTPException(status_code=404, detail="Unknown trigger_key")
    title_t = (body.title_template or "").strip()
    body_t = (body.body_template or "").strip()
    question_t = (body.question_template or "").strip()
    if len(title_t) > 200 or len(body_t) > 600 or len(question_t) > 900:
        raise HTTPException(
            status_code=400,
            detail="Template length exceeds limits (title 200, body 600, question 900).",
        )
    try:
        validate_templates(title_t, body_t, question_t or None, spec.allowed_placeholders)
        norm_config = validate_and_normalize_config(trigger_key, body.config or {})
    except TemplateRenderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ConfigValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    cfg_json = json.dumps(norm_config, ensure_ascii=False, sort_keys=True)
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            db.upsert_trigger_definition(
                conn,
                trigger_key=trigger_key,
                enabled=body.enabled,
                priority=body.priority,
                title_template=title_t,
                body_template=body_t,
                question_template=question_t,
                config_json=cfg_json,
                updated_by=current_user.userid,
            )
            conn.commit()
            merged = load_merged_definition(conn, trigger_key)
        return _admin_trigger_dto(merged, spec)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_put_trigger_definition: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save trigger definition") from e


@router.get("/admin/broadcast/templates")
async def admin_list_broadcast_templates(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            rows = db.list_broadcast_templates(conn)
        items = [
            {
                "id": int(r[0]),
                "title": r[1],
                "body": r[2],
                "category": r[3],
                "is_active": bool(r[4]),
                "sort_order": int(r[5] or 0),
                "created_at": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
                "updated_at": r[7].isoformat() if hasattr(r[7], "isoformat") else str(r[7]),
            }
            for r in rows
        ]
        return {"templates": items}
    except Exception as e:
        logger.exception("admin_list_broadcast_templates failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load templates") from e


@router.post("/admin/broadcast/templates")
async def admin_create_broadcast_template(
    body: BroadcastTemplateCreateRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    title = (body.title or "").strip()
    text = (body.body or "").strip()
    category = (body.category or "general").strip().lower()[:80] or "general"
    if not title or not text:
        raise HTTPException(status_code=400, detail="title and body are required")
    if len(title) > 200:
        raise HTTPException(status_code=400, detail="title max length is 200")
    if len(text) > 600:
        raise HTTPException(status_code=400, detail="body max length is 600")

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            created_id = db.create_broadcast_template(
                conn,
                title=title,
                body=text,
                category=category,
                is_active=bool(body.is_active),
            )
            conn.commit()
        return {"ok": True, "id": created_id}
    except Exception as e:
        logger.exception("admin_create_broadcast_template failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create nudge template") from e


@router.get("/admin/broadcast/schedule")
async def admin_list_broadcast_schedule(
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        if start_date:
            date.fromisoformat(start_date)
        if end_date:
            date.fromisoformat(end_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date filter: {e}") from e

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            rows = db.list_broadcast_schedule(conn, start_date=start_date, end_date=end_date)
        items = []
        for r in rows:
            created_at = r[9]
            dispatched_at = r[10]
            items.append(
                {
                    "id": int(r[0]),
                    "template_id": int(r[1]),
                    "title": r[2],
                    "body": r[3],
                    "category": r[4],
                    "send_date": r[5],
                    "send_time": str(r[6])[:5] if r[6] is not None else None,
                    "is_active": bool(r[7]),
                    "created_by": r[8],
                    "created_at": created_at.isoformat()
                    if hasattr(created_at, "isoformat")
                    else str(created_at),
                    "dispatched_at": dispatched_at.isoformat()
                    if hasattr(dispatched_at, "isoformat")
                    else (str(dispatched_at) if dispatched_at else None),
                    "dispatched_count": int(r[11] or 0),
                }
            )
        return {"items": items}
    except Exception as e:
        logger.exception("admin_list_broadcast_schedule failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load schedule") from e


@router.post("/admin/broadcast/schedule")
async def admin_create_broadcast_schedule(
    body: BroadcastScheduleCreateRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        date.fromisoformat(body.send_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid send_date: {e}") from e
    try:
        h, m = str(body.send_time).split(":", 1)
        hh = int(h)
        mm = int(m)
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError("Hour/minute out of range")
        send_time_norm = f"{hh:02d}:{mm:02d}"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid send_time (HH:MM): {e}") from e

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            schedule_id = db.create_broadcast_schedule_item(
                conn,
                template_id=int(body.template_id),
                send_date=body.send_date,
                send_time=send_time_norm,
                created_by=current_user.userid,
                is_active=bool(body.is_active),
            )
            conn.commit()
        return {"ok": True, "id": schedule_id}
    except Exception as e:
        logger.exception("admin_create_broadcast_schedule failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to create schedule item") from e


@router.delete("/admin/broadcast/schedule/{schedule_id}")
async def admin_delete_broadcast_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            deleted = db.delete_broadcast_schedule_item(conn, int(schedule_id))
            conn.commit()
        if not deleted:
            raise HTTPException(status_code=404, detail="Schedule item not found")
        return {"ok": True, "deleted": deleted}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_delete_broadcast_schedule failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to delete schedule item") from e


def _dispatch_due_broadcast(limit: int) -> Dict[str, Any]:
    # Force IST for schedule evaluation even when server timezone differs.
    now = datetime.now(IST_TZ)
    today_iso = now.date().isoformat()
    now_hhmm = now.strftime("%H:%M")

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            due_rows = db.acquire_due_broadcast_schedule(conn, today_iso=today_iso, now_hhmm=now_hhmm, limit=limit)
            if not due_rows:
                conn.commit()
                return {
                    "ok": True,
                    "due_items": 0,
                    "schedule_items_marked": 0,
                    "delivery_rows_created": 0,
                    "push_sent": 0,
                    "message": "No due scheduled nudges at this time.",
                }

            token_rows = db.get_all_device_tokens(conn)
            tokens_by_user: Dict[int, List[tuple]] = {}
            for uid, token, platform in token_rows:
                tokens_by_user.setdefault(int(uid), []).append((token, platform))
            all_user_ids = db.get_all_user_ids(conn)
            n_users = len(all_user_ids)

            total_push_sent = 0
            total_delivery_rows = 0
            marked = 0

            for row in due_rows:
                schedule_id = int(row[0])
                title = (row[2] or "").strip()[:100]
                body_text = (row[3] or "").strip()[:200]
                category = (row[4] or "general").strip()

                if not title or not body_text:
                    db.mark_broadcast_schedule_dispatched(conn, schedule_id, 0)
                    marked += 1
                    continue

                # Include question so tap → chat pre-fills input (same contract as delivery.py / admin send).
                payload = {
                    "trigger_id": "broadcast_schedule",
                    "cta": "astroroshni://chat",
                    "schedule_id": str(schedule_id),
                    "category": category,
                    "question": body_text[:500],
                }
                event_params = json.dumps(
                    {"schedule_id": schedule_id, "category": category},
                    ensure_ascii=False,
                )
                data_json = ""
                try:
                    data_json = json.dumps(payload, ensure_ascii=False)[:8000]
                except Exception:
                    data_json = ""

                # One Expo HTTP request per 100 devices (avoids gateway timeouts on large user bases).
                expo_messages: List[Dict[str, Any]] = []
                message_uid: List[int] = []
                for uid in all_user_ids:
                    uid_int = int(uid)
                    for token, _platform in tokens_by_user.get(uid_int, []):
                        t = (token or "").strip()
                        if not t.startswith("ExponentPushToken["):
                            continue
                        expo_messages.append(
                            {
                                "to": t,
                                "title": title[:100],
                                "body": body_text[:200],
                                "sound": "default",
                                "data": payload,
                            }
                        )
                        message_uid.append(uid_int)

                push_ok_by_uid: Dict[int, bool] = defaultdict(bool)
                if expo_messages:
                    results = push_module.send_expo_push_messages(expo_messages)
                    for ok, uid_m in zip(results, message_uid):
                        if ok:
                            push_ok_by_uid[uid_m] = True
                            total_push_sent += 1

                sent_at_iso = now.date().isoformat()
                batch_rows: List[tuple] = []
                for uid in all_user_ids:
                    uid_int = int(uid)
                    ch = "push" if push_ok_by_uid.get(uid_int) else "stored"
                    batch_rows.append(
                        (
                            uid_int,
                            "broadcast_schedule",
                            title,
                            body_text,
                            event_params,
                            sent_at_iso,
                            ch,
                            data_json or "",
                        )
                    )
                db.insert_deliveries_batch(conn, batch_rows)
                total_delivery_rows += len(batch_rows)

                db.mark_broadcast_schedule_dispatched(conn, schedule_id, n_users)
                marked += 1

            conn.commit()

        logger.info(
            "broadcast dispatch-due: due_rows=%s users=%s deliveries=%s push_tickets_ok=%s",
            len(due_rows),
            n_users,
            total_delivery_rows,
            total_push_sent,
        )
        return {
            "ok": True,
            "due_items": len(due_rows),
            "schedule_items_marked": marked,
            "delivery_rows_created": total_delivery_rows,
            "push_sent": total_push_sent,
            "users_targeted": n_users,
        }
    except Exception as e:
        logger.exception("_dispatch_due_broadcast failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to dispatch due nudges") from e


def _recent_chat_user_candidates(
    conn,
    *,
    lookback_minutes: int,
    limit_users: int,
) -> List[Dict[str, int]]:
    """Users with at least one user question in lookback window; includes latest user message_id."""
    since_dt = datetime.utcnow() - timedelta(minutes=max(1, int(lookback_minutes)))
    cur = execute(
        conn,
        """
        SELECT cs.user_id,
               MAX(cm.message_id) AS last_user_message_id
        FROM chat_messages cm
        JOIN chat_sessions cs ON cs.session_id = cm.session_id
        WHERE cm.sender = 'user'
          AND cm.timestamp >= %s
        GROUP BY cs.user_id
        ORDER BY MAX(cm.timestamp) DESC
        LIMIT %s
        """,
        (since_dt, int(limit_users)),
    )
    out: List[Dict[str, int]] = []
    for row in cur.fetchall() or []:
        try:
            uid = int(row[0])
            mid = int(row[1]) if row[1] is not None else 0
            if uid > 0 and mid > 0:
                out.append({"user_id": uid, "message_id": mid})
        except Exception:
            continue
    return out


def _recent_chat_followup_dedupe_keys(conn, *, since_dt: datetime) -> set[tuple[int, int]]:
    """
    Already-sent (user_id, message_id) keys for trigger_id=chat_hourly_followup since since_dt.
    Prevents duplicate sends across frequent cron runs.
    """
    cur = execute(
        conn,
        """
        SELECT userid, event_params
        FROM nudge_deliveries
        WHERE trigger_id = %s
          AND created_at >= %s
        """,
        ("chat_hourly_followup", since_dt),
    )
    keys: set[tuple[int, int]] = set()
    for row in cur.fetchall() or []:
        try:
            uid = int(row[0])
            raw = row[1]
            if not raw:
                continue
            obj = json.loads(raw)
            mid = int(obj.get("message_id") or 0)
            if uid > 0 and mid > 0:
                keys.add((uid, mid))
        except Exception:
            continue
    return keys


def _dispatch_recent_chat_followups(
    *,
    limit_users: int = 200,
    lookback_minutes: int = 60,
    max_turns: int = 2,
) -> Dict[str, Any]:
    """
    Generate + send nudges for users active in chat in the last `lookback_minutes`.
    Intended for cron/background use.
    """
    from .chat_nudge_suggestion import (
        load_last_completed_qa_turns,
        generate_push_nudge_via_gemini,
    )

    lookback_minutes = max(1, min(int(lookback_minutes), 24 * 60))
    limit_users = max(1, min(int(limit_users), 500))
    max_turns = max(1, min(int(max_turns), 2))
    dedupe_since = datetime.utcnow() - timedelta(hours=6)

    targeted = 0
    generated = 0
    deliveries_created = 0
    push_sent = 0
    skipped_dedupe = 0
    skipped_no_turns = 0
    failed = 0

    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            candidates = _recent_chat_user_candidates(
                conn,
                lookback_minutes=lookback_minutes,
                limit_users=limit_users,
            )
            sent_keys = _recent_chat_followup_dedupe_keys(conn, since_dt=dedupe_since)
            today = date.today()

            for item in candidates:
                uid = int(item["user_id"])
                message_id = int(item["message_id"])
                targeted += 1

                if (uid, message_id) in sent_keys:
                    skipped_dedupe += 1
                    continue

                try:
                    turns = load_last_completed_qa_turns(conn, uid, max_turns=max_turns)
                    if not turns:
                        skipped_no_turns += 1
                        continue

                    out = generate_push_nudge_via_gemini(turns)
                    title = str(out.get("title") or "").strip()[:100]
                    body_text = str(out.get("body") or "").strip()[:200]
                    question = str(out.get("question") or "").strip()[:500]
                    if not title or not body_text:
                        failed += 1
                        continue
                    generated += 1

                    push_data: Dict[str, Any] = {
                        "trigger_id": "chat_hourly_followup",
                        "cta": "astroroshni://chat",
                        "question": question,
                        "source_message_id": str(message_id),
                    }

                    tokens = db.get_device_tokens_for_user(conn, uid)
                    sent = 0
                    for token, _platform in tokens or []:
                        if push_module.send_expo_push(token, title, body_text, data=push_data):
                            sent += 1
                    push_sent += sent

                    event_params = json.dumps(
                        {
                            "source": "recent_chat_hourly",
                            "message_id": message_id,
                            "lookback_minutes": lookback_minutes,
                        },
                        ensure_ascii=False,
                    )
                    channel = "push" if sent > 0 else "stored"
                    db.insert_delivery(
                        conn,
                        userid=uid,
                        trigger_id="chat_hourly_followup",
                        title=title,
                        body=body_text,
                        sent_at=today,
                        event_params=event_params,
                        channel=channel,
                        data_payload=push_data,
                    )
                    deliveries_created += 1
                except Exception as e:
                    failed += 1
                    logger.warning(
                        "chat_hourly_followup failed for user_id=%s message_id=%s: %s",
                        uid,
                        message_id,
                        e,
                    )
                    continue

            summary = {
                "ok": True,
                "targeted_users": targeted,
                "generated": generated,
                "deliveries_created": deliveries_created,
                "push_sent": push_sent,
                "skipped_dedupe": skipped_dedupe,
                "skipped_no_turns": skipped_no_turns,
                "failed": failed,
                "lookback_minutes": lookback_minutes,
                "limit_users": limit_users,
            }
            db.insert_cron_run(
                conn,
                job_key="chat_followup_dispatch_recent",
                status="success",
                summary_json=json.dumps(summary, ensure_ascii=False),
            )
            conn.commit()
    except Exception as e:
        summary = {
            "ok": False,
            "error": str(e),
            "targeted_users": targeted,
            "generated": generated,
            "deliveries_created": deliveries_created,
            "push_sent": push_sent,
            "skipped_dedupe": skipped_dedupe,
            "skipped_no_turns": skipped_no_turns,
            "failed": failed + 1,
            "lookback_minutes": lookback_minutes,
            "limit_users": limit_users,
        }
        try:
            with db.get_conn() as conn:
                db.init_nudge_tables(conn)
                db.insert_cron_run(
                    conn,
                    job_key="chat_followup_dispatch_recent",
                    status="failed",
                    summary_json=json.dumps(summary, ensure_ascii=False),
                )
                conn.commit()
        except Exception:
            pass
        logger.exception("chat_hourly_followup fatal error: %s", e)
        return summary

    logger.info("chat_hourly_followup summary: %s", summary)
    return summary


@router.post("/admin/broadcast/dispatch-due")
async def admin_dispatch_due_broadcast(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-triggered dispatch for due broadcast schedule items.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return _dispatch_due_broadcast(limit)


@router.post("/cron/broadcast/dispatch-due")
async def cron_dispatch_due_broadcast(
    limit: int = Query(100, ge=1, le=500),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    """
    Cron-safe endpoint secured by static secret header:
      X-Cron-Secret: <NUDGE_CRON_SECRET>
    """
    _verify_cron_secret(x_cron_secret)
    return _dispatch_due_broadcast(limit)


@router.post("/cron/chat-followup/dispatch-recent")
async def cron_dispatch_recent_chat_followups(
    background_tasks: BackgroundTasks,
    limit_users: int = Query(200, ge=1, le=500),
    lookback_minutes: int = Query(60, ge=1, le=1440),
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    """
    Cron-safe, non-blocking endpoint:
    - Finds users who asked >=1 question in the last lookback window.
    - Generates title/body/question from their recent completed chat exchanges.
    - Sends push (and stores delivery row) with dedupe by latest user message id.
    """
    _verify_cron_secret(x_cron_secret)
    background_tasks.add_task(
        _dispatch_recent_chat_followups,
        limit_users=int(limit_users),
        lookback_minutes=int(lookback_minutes),
        max_turns=2,
    )
    return {
        "ok": True,
        "queued": True,
        "message": "Recent chat follow-up dispatch queued in background",
        "limit_users": int(limit_users),
        "lookback_minutes": int(lookback_minutes),
    }


@router.get("/admin/cron/chat-followup/status")
async def admin_chat_followup_cron_status(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    """Admin status endpoint: recent run summaries for chat follow-up cron job."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            rows = db.list_cron_runs(
                conn,
                job_key="chat_followup_dispatch_recent",
                limit=int(limit),
            )
        items = []
        for r in rows:
            summary = {}
            try:
                summary = json.loads(r[3] or "{}")
                if not isinstance(summary, dict):
                    summary = {}
            except Exception:
                summary = {}
            items.append(
                {
                    "id": int(r[0]),
                    "job_key": r[1],
                    "status": r[2],
                    "summary": summary,
                    "created_at": r[4].isoformat() if hasattr(r[4], "isoformat") else str(r[4]),
                }
            )
        latest = items[0] if items else None
        return {"ok": True, "latest": latest, "items": items}
    except Exception as e:
        logger.exception("admin_chat_followup_cron_status failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch cron status") from e


@router.get("/admin/deliveries/today")
async def admin_list_today_deliveries(
    target_date: Optional[str] = Query(None, description="YYYY-MM-DD; defaults to today in IST"),
    limit: int = Query(500, ge=1, le=2000),
    current_user: User = Depends(get_current_user),
):
    """Admin list of notifications sent for a date (today by default), with delivery status."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    try:
        if target_date:
            day = date.fromisoformat(target_date)
        else:
            day = datetime.now(IST_TZ).date()
        with db.get_conn() as conn:
            db.init_nudge_tables(conn)
            rows = db.list_deliveries_for_date_admin(conn, day.isoformat(), limit=int(limit))
        items: List[Dict[str, Any]] = []
        for r in rows:
            channel = (r[8] or "stored").strip()
            status = "sent_push" if channel == "push" else "stored_only"
            items.append(
                {
                    "id": int(r[0]),
                    "user_id": int(r[1]),
                    "user_name": r[2] or "",
                    "user_phone": r[3] or "",
                    "trigger_id": r[4] or "",
                    "title": r[5] or "",
                    "body": r[6] or "",
                    "sent_at": r[7] or None,
                    "channel": channel,
                    "status": status,
                    "created_at": r[9].isoformat() if hasattr(r[9], "isoformat") else str(r[9]),
                    "read_at": r[10].isoformat() if hasattr(r[10], "isoformat") else (str(r[10]) if r[10] else None),
                }
            )
        return {"ok": True, "target_date": day.isoformat(), "count": len(items), "items": items}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid target_date: {e}") from e
    except Exception as e:
        logger.exception("admin_list_today_deliveries failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch deliveries") from e
