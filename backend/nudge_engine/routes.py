"""
HTTP endpoints: daily nudge scan (cron), device token registration (app), admin send,
in-app inbox for stored nudges.
"""
import json
import logging
from datetime import date
from typing import Optional, List, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
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


class AdminSendBlogNotificationRequest(BaseModel):
    blog_id: int
    audience: str = "all"  # "all" or "eligible"
    user_ids: Optional[List[int]] = None  # optional explicit user selection


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
