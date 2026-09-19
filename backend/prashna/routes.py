"""Guided-question Prashna API."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from auth import User, get_current_user
from credits.credit_service import CreditService
from prashna.question_interpreter import public_topics, resolve_guided_question
from prashna.service import analyze_prashna


router = APIRouter(prefix="/prashna", tags=["prashna"])
credit_service = CreditService()
PRASHNA_COST_SETTING = "prashna_analysis_cost"


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: Optional[str] = None
    # Legacy fields are accepted only to return one readable migration error.
    question: Optional[str] = None
    confirmed_topic: Optional[str] = None
    confirmed_paraphrase: Optional[str] = None
    confirmed_intent: Optional[str] = None
    category: Optional[str] = None
    date: str
    time: str
    latitude: float = Field(..., ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(..., ge=-180, le=180, allow_inf_nan=False)
    timezone: str = ""
    place: str = ""
    name: str = "Prashna"

@router.get("/topics")
def topics_route():
    return {"topics": public_topics()}


@router.post("/analyze")
def analyze_route(request: AnalyzeRequest, current_user: User = Depends(get_current_user)):
    if request.category is not None or any((request.confirmed_topic, request.confirmed_paraphrase, request.confirmed_intent)):
        if (request.category or "").strip().lower() in {"relationship", "love", "partner"}:
            detail = ("This request came from an older Prashna screen. Reload or update the app, then choose the exact "
                      "guided love or relationship question: contact, unblock, reconciliation, return, or marriage.")
        else:
            detail = ("This request came from an older Prashna screen. Reload or update the app, select one of the "
                      "guided questions, and cast it directly.")
        raise HTTPException(status_code=409, detail=detail)
    if not request.question_id:
        raise HTTPException(status_code=400, detail="Select one of the supported Prashna questions before casting the chart.")
    try:
        # Validate the immutable catalogue ID before checking or charging credits.
        resolve_guided_question(request.question_id)
        base_cost = int(credit_service.get_credit_setting(PRASHNA_COST_SETTING) or 3)
        cost = int(credit_service.get_effective_cost(current_user.userid, base_cost, PRASHNA_COST_SETTING))
        balance = int(credit_service.get_user_credits(current_user.userid))
        if balance < cost:
            raise HTTPException(status_code=402,
                detail=f"Insufficient credits. You need {cost} credits but have {balance}.")
        result = analyze_prashna(question_id=request.question_id, date=request.date, time=request.time,
            latitude=request.latitude, longitude=request.longitude,
            timezone=request.timezone, place=request.place, name=request.name)
        if not credit_service.spend_credits(current_user.userid, cost, "prashna_analysis",
                                             f"Classical Prashna: {request.question_id}"):
            raise HTTPException(status_code=402,
                detail="The Prashna chart was not charged because your available credits changed. Refresh your balance and try again.")
        result["billing"] = {"feature": "prashna", "credits_spent": cost,
                             "credits_remaining": max(0, balance - cost)}
        return result
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logging.getLogger(__name__).exception("Prashna calculation failed")
        raise HTTPException(status_code=500, detail="Unable to calculate the question chart") from exc
