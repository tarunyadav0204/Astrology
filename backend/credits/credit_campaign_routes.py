"""Admin APIs for targeted credit multiplier campaigns."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
import logging
import os
from typing import Dict, List, Literal, Optional
import uuid
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from credits.credit_campaigns import (
    create_credit_campaign,
    get_campaign_recipient_ids,
    get_credit_campaign,
    get_credit_campaign_recipient_report,
    list_credit_campaigns,
    set_credit_campaign_status,
)
from credits.web_continue import (
    ensure_continue_link_environment_is_safe,
    get_or_create_continue_tokens,
)
from db import execute, get_conn
from whatsapp.admin_routes import _find_template, _phone_number_id, _template_variables

router = APIRouter()
logger = logging.getLogger(__name__)


class CreditCampaignCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=120)
    multiplier: Decimal = Field(..., ge=Decimal("1.01"), le=Decimal("5"))
    starts_at: datetime
    ends_at: datetime
    recipient_ids: List[int] = Field(..., min_length=1, max_length=1000)
    product_ids: List[str] = Field(default_factory=list, max_length=20)
    status: Literal["draft", "active"] = "draft"


class CreditCampaignStatusBody(BaseModel):
    status: Literal["draft", "active", "paused", "completed"]


class CreditCampaignSendBody(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=512)
    language: str = Field(..., min_length=1, max_length=32)
    include_unlinked: bool = False


def _require_admin(user: User) -> None:
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def _validate_product_ids(product_ids: List[str]) -> List[str]:
    allowed = {"credits_50", "credits_100", "credits_250", "credits_999"}
    normalized = list(dict.fromkeys(str(value).strip() for value in product_ids if str(value).strip()))
    invalid = [value for value in normalized if value not in allowed]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unsupported credit packs: {', '.join(invalid)}")
    return normalized


@router.get("/admin/campaigns/credits")
async def admin_list_credit_campaigns(current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    campaigns = await run_in_threadpool(list_credit_campaigns)
    try:
        from nudge_engine.connections import assert_explicit_isolated_database_configuration
        from nudge_engine.credit_campaign_whatsapp import latest_credit_campaign_whatsapp_jobs

        await run_in_threadpool(assert_explicit_isolated_database_configuration)
        latest = await run_in_threadpool(
            latest_credit_campaign_whatsapp_jobs,
            [campaign["id"] for campaign in campaigns],
        )
        for campaign in campaigns:
            campaign["whatsapp_job"] = latest.get(campaign["id"])
    except Exception:
        # Campaign administration remains available if notification storage is
        # temporarily unavailable; send itself fails closed before enqueueing.
        pass
    return {"campaigns": campaigns}


@router.get("/admin/campaigns/credits/{campaign_id}/recipients")
async def admin_credit_campaign_recipient_report(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    campaign = await run_in_threadpool(get_credit_campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Credit campaign not found")
    recipients = await run_in_threadpool(get_credit_campaign_recipient_report, campaign_id)
    delivery_report = {"job": None, "metrics": {}, "recipients": {}}
    try:
        from nudge_engine.connections import assert_explicit_isolated_database_configuration
        from nudge_engine.credit_campaign_whatsapp import get_credit_campaign_whatsapp_delivery_report

        await run_in_threadpool(assert_explicit_isolated_database_configuration)
        delivery_report = await run_in_threadpool(
            get_credit_campaign_whatsapp_delivery_report,
            campaign_id,
        )
    except Exception:
        # Historical campaigns and local environments still return the legacy
        # accepted/failed, click, and purchase report if lifecycle storage is
        # unavailable or did not exist when the campaign was sent.
        logger.exception("Meta delivery report unavailable campaign=%s; using legacy fields", campaign_id)
    delivery_by_user = delivery_report.get("recipients") or {}
    for recipient in recipients:
        lifecycle = delivery_by_user.get(int(recipient["userid"]))
        if lifecycle:
            recipient.update(lifecycle)
        else:
            legacy_status = str(recipient.get("message_status") or "not_sent")
            recipient.update(
                {
                    "send_state": legacy_status,
                    "send_error": recipient.get("message_error"),
                    "meta_message_id": None,
                    "meta_status": legacy_status,
                    "meta_tracking_available": False,
                    "accepted_at": recipient.get("notified_at"),
                    "sent_at": None,
                    "delivered_at": None,
                    "read_at": None,
                    "failed_at": None,
                }
            )
    return {
        "campaign": {
            "id": campaign["id"],
            "name": campaign["name"],
            "summary": campaign.get("summary") or {},
        },
        "recipients": recipients,
        "delivery": {
            "job": delivery_report.get("job"),
            "metrics": delivery_report.get("metrics") or {},
        },
    }


@router.post("/admin/campaigns/credits")
async def admin_create_credit_campaign(
    body: CreditCampaignCreate,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    if body.ends_at <= body.starts_at:
        raise HTTPException(status_code=400, detail="Campaign end must be after its start")
    recipient_ids = list(dict.fromkeys(int(value) for value in body.recipient_ids if int(value) > 0))
    if not recipient_ids:
        raise HTTPException(status_code=400, detail="At least one valid user ID is required")
    campaign = await run_in_threadpool(
        lambda: create_credit_campaign(
            name=body.name,
            multiplier=body.multiplier,
            starts_at=body.starts_at,
            ends_at=body.ends_at,
            recipient_ids=recipient_ids,
            product_ids=_validate_product_ids(body.product_ids),
            status=body.status,
            created_by=int(current_user.userid),
        )
    )
    return {"campaign": campaign}


@router.patch("/admin/campaigns/credits/{campaign_id}/status")
async def admin_set_credit_campaign_status(
    campaign_id: int,
    body: CreditCampaignStatusBody,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    campaign = await run_in_threadpool(set_credit_campaign_status, campaign_id, body.status)
    if not campaign:
        raise HTTPException(status_code=404, detail="Credit campaign not found")
    return {"campaign": campaign}


def _format_multiplier(value) -> str:
    formatted = f"{Decimal(str(value)):.3f}".rstrip("0").rstrip(".")
    return formatted


def _template_values(template: Dict, campaign: Dict, recipient: Dict, token: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    expires = datetime.fromisoformat(str(campaign["ends_at"]).replace("Z", "+00:00"))
    expires_ist = expires.astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")
    multiplier = _format_multiplier(campaign["multiplier"])
    for variable in _template_variables(template):
        key = variable["key"]
        if variable.get("component") == "BUTTON" and variable.get("sub_type") == "url":
            values[key] = token
            continue
        name = str(variable.get("token") or "").strip().lower()
        if name in {"customer_name", "user_name", "name", "first_name"}:
            values[key] = str(recipient.get("name") or "there").strip() or "there"
        elif name in {"multiplier", "credit_multiplier", "offer_multiplier"}:
            values[key] = multiplier
        elif name in {"expires_at", "expiry", "offer_end", "end_time", "valid_until"}:
            values[key] = expires_ist
        elif name in {"campaign_name", "offer_name"}:
            values[key] = str(campaign["name"])
        elif variable.get("component") == "BODY" and name.isdigit():
            position = int(name)
            positional_values = {
                1: str(recipient.get("name") or "there").strip() or "there",
                2: multiplier,
                3: expires_ist,
                4: str(campaign["name"]),
            }
            if position not in positional_values:
                raise ValueError(f"Unsupported campaign body variable {{{{{name}}}}}")
            values[key] = positional_values[position]
        else:
            raise ValueError(f"Unsupported template variable {{{{{variable.get('token')}}}}}")
    return values


def _validate_campaign_template(template: Dict) -> None:
    variables = _template_variables(template)
    body_tokens = {
        str(variable.get("token") or "").strip().lower()
        for variable in variables
        if variable.get("component") == "BODY"
    }
    multiplier_tokens = {"multiplier", "credit_multiplier", "offer_multiplier"}
    expiry_tokens = {"expires_at", "expiry", "offer_end", "end_time", "valid_until"}
    has_multiplier = bool(body_tokens.intersection(multiplier_tokens)) or "2" in body_tokens
    has_expiry = bool(body_tokens.intersection(expiry_tokens)) or "3" in body_tokens
    has_secure_button = any(
        variable.get("component") == "BUTTON" and variable.get("sub_type") == "url"
        for variable in variables
    )
    missing = []
    if not has_multiplier:
        missing.append("a multiplier variable (body {{2}})")
    if not has_expiry:
        missing.append("an expiry variable (body {{3}})")
    if not has_secure_button:
        missing.append("a dynamic URL button")
    if missing:
        raise HTTPException(
            status_code=400,
            detail=(
                "This template is not safe for a flexible credit campaign; it needs "
                + ", ".join(missing)
                + "."
            ),
        )


def _save_campaign_template(campaign_id: int, template_name: str, language: str) -> None:
    with get_conn() as conn:
        execute(
            conn,
            """
            UPDATE credit_campaigns
            SET whatsapp_template_name = ?, whatsapp_template_language = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (template_name, language, int(campaign_id)),
        )
        conn.commit()


@router.get("/admin/campaigns/credits/{campaign_id}/whatsapp-jobs/{job_id}")
async def admin_get_credit_campaign_whatsapp_job(
    campaign_id: int,
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    from nudge_engine.connections import assert_explicit_isolated_database_configuration
    from nudge_engine.credit_campaign_whatsapp import get_credit_campaign_whatsapp_job

    try:
        await run_in_threadpool(assert_explicit_isolated_database_configuration)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    job = await run_in_threadpool(
        lambda: get_credit_campaign_whatsapp_job(job_id, include_issues=True)
    )
    if not job or int(job["campaign_id"]) != int(campaign_id):
        raise HTTPException(status_code=404, detail="WhatsApp campaign job not found")
    return {"job": job}


@router.post("/admin/campaigns/credits/{campaign_id}/send-whatsapp", status_code=202)
async def admin_send_credit_campaign_whatsapp(
    campaign_id: int,
    body: CreditCampaignSendBody,
    current_user: User = Depends(get_current_user),
):
    _require_admin(current_user)
    campaign = await run_in_threadpool(get_credit_campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Credit campaign not found")
    if campaign["status"] != "active":
        raise HTTPException(status_code=409, detail="Activate the campaign before sending WhatsApp messages")
    now = datetime.now(datetime.fromisoformat(campaign["starts_at"]).tzinfo)
    if datetime.fromisoformat(campaign["ends_at"]) <= now:
        raise HTTPException(status_code=409, detail="This campaign has already ended")
    try:
        ensure_continue_link_environment_is_safe()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    phone_number_id = _phone_number_id()
    if not phone_number_id:
        raise HTTPException(status_code=503, detail="WhatsApp phone number ID is not configured")
    template = await run_in_threadpool(_find_template, body.template_name.strip(), body.language.strip())
    _validate_campaign_template(template)
    from nudge_engine.credit_campaign_whatsapp import (
        active_credit_campaign_whatsapp_job,
        create_credit_campaign_whatsapp_job,
        set_job_enqueue_result,
    )
    from nudge_engine.connections import assert_explicit_isolated_database_configuration
    from nudge_engine.task_queue import (
        enqueue_nudge_task,
        nudge_tasks_are_isolated,
        nudge_tasks_enabled,
    )

    if not nudge_tasks_enabled() or not nudge_tasks_are_isolated():
        raise HTTPException(
            status_code=503,
            detail="WhatsApp campaigns require the isolated notification worker and cannot run on the main API",
        )
    try:
        await run_in_threadpool(assert_explicit_isolated_database_configuration)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    active_job = await run_in_threadpool(active_credit_campaign_whatsapp_job, campaign_id)
    if active_job:
        raise HTTPException(
            status_code=409,
            detail=f"A WhatsApp send is already {active_job['status']} for this campaign",
        )
    recipient_ids = await run_in_threadpool(get_campaign_recipient_ids, campaign_id)
    tokens = await run_in_threadpool(get_or_create_continue_tokens, recipient_ids)
    job_id = uuid.uuid4().hex
    await run_in_threadpool(
        lambda: create_credit_campaign_whatsapp_job(
            job_id=job_id,
            campaign=campaign,
            template=template,
            phone_number_id=phone_number_id,
            include_unlinked=body.include_unlinked,
            tokens_by_user=tokens,
            created_by=int(current_user.userid),
        )
    )
    batch_size = max(10, min(int(os.getenv("WHATSAPP_CAMPAIGN_BATCH_SIZE", "25") or "25"), 100))
    batches = [recipient_ids[index:index + batch_size] for index in range(0, len(recipient_ids), batch_size)]
    enqueued = 0
    failed_ids: List[int] = []
    for index, user_ids in enumerate(batches):
        queued = await run_in_threadpool(
            lambda index=index, user_ids=user_ids: enqueue_nudge_task(
                task_kind="credit-campaign-whatsapp-batch",
                task_id=f"{job_id}-{index}",
                payload={
                    "job_id": job_id,
                    "recipients": [
                        {"user_id": user_id, "secure_token": tokens[user_id]}
                        for user_id in user_ids
                    ],
                },
                dispatch_deadline_s=900,
            )
        )
        if queued:
            enqueued += 1
        else:
            failed_ids.extend(user_ids)
    enqueue_error = (
        f"Could not enqueue {len(failed_ids)} recipient(s) on the isolated worker"
        if failed_ids else None
    )
    job = await run_in_threadpool(
        lambda: set_job_enqueue_result(
            job_id,
            enqueued_batches=enqueued,
            failed_userids=failed_ids,
            error=enqueue_error,
        )
    )
    await run_in_threadpool(
        _save_campaign_template,
        campaign_id,
        body.template_name.strip(),
        body.language.strip(),
    )
    if enqueued == 0:
        raise HTTPException(status_code=503, detail=enqueue_error or "Could not enqueue WhatsApp campaign")
    return {
        "ok": True,
        "job": job,
        "message": "WhatsApp campaign queued on the isolated notification worker. You can leave this screen.",
    }
