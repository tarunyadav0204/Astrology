"""Public exchange + admin helpers for WhatsApp → PWA credit continue links."""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, create_access_token_for_user, get_current_user
from credits.web_continue import (
    build_continue_url,
    get_or_create_continue_token,
    lookup_user_for_web_topup,
    resolve_continue_token,
    rotate_continue_token,
)

logger = logging.getLogger(__name__)

auth_router = APIRouter()
admin_router = APIRouter()

CREDITS_WEB_TOPUP_TEMPLATE = (
    os.getenv("WHATSAPP_CREDITS_WEB_TOPUP_TEMPLATE") or "credits_web_topup_bonus"
).strip()
CREDITS_WEB_TOPUP_TEMPLATE_LANG = (
    os.getenv("WHATSAPP_CREDITS_WEB_TOPUP_TEMPLATE_LANGUAGE") or "en"
).strip()


class WebContinueBody(BaseModel):
    token: str = Field(..., min_length=8, max_length=200)


class AdminWebTopupBody(BaseModel):
    userid: Optional[int] = None
    phone: Optional[str] = None
    rotate: bool = False
    send_whatsapp: bool = False


def _digits_only(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def _template_phone_number_id() -> str:
    return (
        os.getenv("WHATSAPP_NUDGE_PHONE_NUMBER_ID")
        or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        or ""
    ).strip()


def _require_admin(user: User) -> None:
    if getattr(user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


@auth_router.post("/web-continue")
async def exchange_web_continue_token(body: WebContinueBody):
    """Exchange a reusable continue token for a normal browser JWT + user payload."""
    user = resolve_continue_token(body.token)
    if not user or not user.get("phone"):
        raise HTTPException(status_code=404, detail="Invalid or revoked continue link")
    access_token = create_access_token_for_user(
        phone=user["phone"],
        userid=int(user["userid"]),
        name=str(user.get("name") or ""),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "userid": int(user["userid"]),
            "name": user.get("name"),
            "phone": user.get("phone"),
            "role": user.get("role") or "user",
            "email": user.get("email"),
            "signup_client": user.get("signup_client"),
        },
        "next": "Credits",
    }


def _build_link_payload(userid: int, *, rotate: bool = False) -> dict:
    token = rotate_continue_token(userid) if rotate else get_or_create_continue_token(userid)
    url = build_continue_url(token)
    return {"userid": int(userid), "token": token, "url": url}


def send_credits_web_topup_whatsapp(
    *, userid: int, name: str, phone: str, token: str
) -> tuple[bool, Optional[str]]:
    """Returns (ok, error_detail)."""
    phone_number_id = _template_phone_number_id()
    if not phone_number_id:
        msg = "missing WHATSAPP_PHONE_NUMBER_ID / WHATSAPP_NUDGE_PHONE_NUMBER_ID on server"
        logger.warning("credits web topup WA skipped: %s", msg)
        return False, msg
    recipient = _digits_only(phone)
    if not recipient:
        msg = f"no phone digits for userid={userid}"
        logger.warning("credits web topup WA skipped: %s", msg)
        return False, msg
    display_name = (name or "there").strip() or "there"
    # Meta template body often rejects newlines / odd chars in variables.
    display_name = re.sub(r"\s+", " ", display_name)[:60]
    try:
        from whatsapp.messaging import send_whatsapp_template

        # Meta often stores English as en_US; try configured lang then en_US/en.
        lang_candidates = []
        for code in (
            CREDITS_WEB_TOPUP_TEMPLATE_LANG,
            "en_US",
            "en",
        ):
            c = (code or "").strip()
            if c and c not in lang_candidates:
                lang_candidates.append(c)

        last_err = None
        for lang in lang_candidates:
            # Template uses named body var {{customer_name}}, not positional {{1}}.
            ok, err = send_whatsapp_template(
                to=recipient,
                phone_number_id=phone_number_id,
                template_name=CREDITS_WEB_TOPUP_TEMPLATE,
                language_code=lang,
                body_named_params={"customer_name": display_name},
                url_button_suffix=token,
                return_error=True,
            )
            if ok:
                if lang != CREDITS_WEB_TOPUP_TEMPLATE_LANG:
                    logger.info(
                        "credits web topup WA sent with language fallback userid=%s lang=%s",
                        userid,
                        lang,
                    )
                return True, None
            last_err = err
        return False, last_err or "template send failed"
    except Exception as e:
        logger.exception("credits web topup WA send failed userid=%s", userid)
        return False, str(e)


@admin_router.post("/admin/web-topup-link")
async def admin_web_topup_link(body: AdminWebTopupBody, current_user: User = Depends(get_current_user)):
    """Create or return reusable PWA Credits continue link; optionally send WhatsApp template."""
    _require_admin(current_user)
    found = lookup_user_for_web_topup(userid=body.userid, phone=body.phone)
    if not found:
        raise HTTPException(status_code=404, detail="User not found")
    userid, phone, name = found
    if not phone:
        raise HTTPException(status_code=400, detail="User has no phone on file")
    payload = _build_link_payload(userid, rotate=bool(body.rotate))
    wa_sent = False
    wa_error = None
    if body.send_whatsapp:
        wa_sent, wa_error = send_credits_web_topup_whatsapp(
            userid=userid,
            name=name,
            phone=phone,
            token=payload["token"],
        )
        if not wa_sent:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Link created but WhatsApp template send failed. "
                    f"template={CREDITS_WEB_TOPUP_TEMPLATE} lang={CREDITS_WEB_TOPUP_TEMPLATE_LANG}. "
                    f"Meta error: {wa_error or 'unknown'}"
                ),
            )
    return {
        **payload,
        "name": name,
        "phone": phone,
        "whatsapp_sent": wa_sent,
        "template_name": CREDITS_WEB_TOPUP_TEMPLATE,
        "template_language": CREDITS_WEB_TOPUP_TEMPLATE_LANG,
        "whatsapp_error": wa_error,
    }
