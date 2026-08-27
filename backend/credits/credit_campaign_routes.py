"""Admin APIs for targeted credit multiplier campaigns."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Literal, Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from credits.credit_campaigns import (
    create_credit_campaign,
    get_campaign_recipient_ids,
    get_credit_campaign,
    list_credit_campaigns,
    record_campaign_message_result,
    set_credit_campaign_status,
)
from credits.web_continue import (
    ensure_continue_link_environment_is_safe,
    get_or_create_continue_token,
)
from db import execute, get_conn
from whatsapp.admin_routes import (
    _build_send_components,
    _find_template,
    _phone_number_id,
    _resolve_recipients,
    _template_variables,
)
from whatsapp.messaging import send_whatsapp_template

router = APIRouter()


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
    return {"campaigns": await run_in_threadpool(list_credit_campaigns)}


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


@router.post("/admin/campaigns/credits/{campaign_id}/send-whatsapp")
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
    recipient_ids = await run_in_threadpool(get_campaign_recipient_ids, campaign_id)
    recipients = await run_in_threadpool(_resolve_recipients, recipient_ids)
    eligible = [
        row for row in recipients
        if row["status"] == "linked" or (body.include_unlinked and row["status"] == "phone_only")
    ]
    skipped = [row for row in recipients if row not in eligible]

    def send_one(row: Dict) -> Dict:
        try:
            token = f"{get_or_create_continue_token(int(row['user_id']))}.cc{campaign_id}"
            values = _template_values(template, campaign, row, token)
            components = _build_send_components(template, values)
            ok, error = send_whatsapp_template(
                to=row["recipient"],
                phone_number_id=phone_number_id,
                template_name=body.template_name.strip(),
                language_code=body.language.strip(),
                components_override=components,
                return_error=True,
            )
            status = "accepted" if ok else "failed"
            record_campaign_message_result(campaign_id, row["user_id"], status, error)
            return {"user_id": row["user_id"], "status": status, "error": error}
        except Exception as exc:
            record_campaign_message_result(campaign_id, row["user_id"], "failed", str(exc))
            return {"user_id": row["user_id"], "status": "failed", "error": str(exc)}

    def send_all() -> List[Dict]:
        if not eligible:
            return []
        results: List[Dict] = []
        with ThreadPoolExecutor(max_workers=min(5, len(eligible))) as executor:
            futures = [executor.submit(send_one, row) for row in eligible]
            for future in as_completed(futures):
                results.append(future.result())
        return results

    results = await run_in_threadpool(send_all)
    results.extend(
        {"user_id": row["user_id"], "status": "skipped", "error": row["status"]}
        for row in skipped
    )
    await run_in_threadpool(_save_campaign_template, campaign_id, body.template_name.strip(), body.language.strip())
    results.sort(key=lambda row: row["user_id"])
    return {
        "accepted": sum(1 for row in results if row["status"] == "accepted"),
        "failed": sum(1 for row in results if row["status"] == "failed"),
        "skipped": sum(1 for row in results if row["status"] == "skipped"),
        "results": results,
    }
