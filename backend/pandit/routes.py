from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from credits.entitlements import (
    PANDIT_DESK_ENTITLEMENT,
    entitlement_summary,
    has_entitlement,
)
from pandit import service as pandit_service

router = APIRouter(prefix="/pandit", tags=["pandit"])


class PanditProfilePayload(BaseModel):
    display_name: str = Field(default="", max_length=80)
    city: str = Field(default="", max_length=80)
    pincode: str = Field(default="", max_length=10)
    languages: List[str] = Field(default_factory=lambda: ["hindi", "english"])
    puja_types: List[str] = Field(default_factory=list)
    tagline: str = Field(default="", max_length=120)
    phone: str = Field(default="", max_length=40)
    email: str = Field(default="", max_length=80)
    website: str = Field(default="", max_length=120)
    address: str = Field(default="", max_length=160)


def _me_payload(user: User) -> dict:
    profile = pandit_service.get_profile(user.userid)
    summary = entitlement_summary(user)
    licensed = bool(summary.get("is_pandit_licensed"))
    setup_complete = bool(profile and profile.get("setup_complete"))
    return {
        "success": True,
        "profile": profile,
        "is_pandit_licensed": licensed,
        "setup_complete": setup_complete,
        "desk_ready": licensed and setup_complete,
        "allowed_puja_types": pandit_service.ALLOWED_PUJA_TYPES,
        "entitlements": summary.get("entitlements") or [],
    }


@router.get("/me")
async def get_pandit_me(current_user: User = Depends(get_current_user)):
    return _me_payload(current_user)


@router.get("/meta")
async def get_pandit_meta():
    """Public catalog for practice setup UI (no auth)."""
    return {
        "success": True,
        "allowed_puja_types": pandit_service.ALLOWED_PUJA_TYPES,
        "default_languages": pandit_service.DEFAULT_LANGUAGES,
    }


@router.post("/join")
async def join_pandit_desk(
    payload: PanditProfilePayload,
    current_user: User = Depends(get_current_user),
):
    """Create/update practice profile and grant Free Pandit Desk entitlement."""
    try:
        body = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        profile = pandit_service.upsert_profile(current_user.userid, body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not profile.get("setup_complete"):
        raise HTTPException(
            status_code=400,
            detail="Complete display name, city, 6-digit pincode, and at least one puja type.",
        )

    granted = pandit_service.grant_free_desk(current_user.userid)
    if not granted and not has_entitlement(current_user, PANDIT_DESK_ENTITLEMENT):
        raise HTTPException(
            status_code=500,
            detail="Could not activate Free Pandit Desk. Ensure the pandit free plan is seeded.",
        )

    return {
        **_me_payload(current_user),
        "message": "Pandit Desk activated",
        "free_granted": True,
    }


@router.put("/profile")
async def update_pandit_profile(
    payload: PanditProfilePayload,
    current_user: User = Depends(get_current_user),
):
    existing = pandit_service.get_profile(current_user.userid)
    if not existing and not has_entitlement(current_user, PANDIT_DESK_ENTITLEMENT):
        raise HTTPException(
            status_code=400,
            detail="Join Pandit Desk first via POST /pandit/join.",
        )

    try:
        body = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
        profile = pandit_service.upsert_profile(current_user.userid, body)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Renew free entitlement if they finish setup later.
    if profile.get("setup_complete") and not has_entitlement(current_user, PANDIT_DESK_ENTITLEMENT):
        pandit_service.grant_free_desk(current_user.userid)

    return _me_payload(current_user)
