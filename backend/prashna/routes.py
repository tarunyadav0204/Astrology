"""Guided-question Prashna API."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from auth import User, get_current_user
from credits.credit_service import CreditService
from credits.transaction_receipt import prashna_usage_metadata
from db import execute, get_conn
from prashna.question_interpreter import public_topics, resolve_guided_question
from prashna.service import analyze_prashna


router = APIRouter(prefix="/prashna", tags=["prashna"])
credit_service = CreditService()
PRASHNA_COST_SETTING = "prashna_analysis_cost"
_prashna_readings_ready = False


def _ensure_prashna_readings() -> None:
    global _prashna_readings_ready
    if _prashna_readings_ready:
        return
    with get_conn() as conn:
        execute(
            conn,
            """
            CREATE TABLE IF NOT EXISTS prashna_readings (
                id SERIAL PRIMARY KEY,
                userid INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        )
        conn.commit()
    _prashna_readings_ready = True


def _save_prashna_reading(userid: int, question_id: str, result: dict) -> int:
    _ensure_prashna_readings()
    import json

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            INSERT INTO prashna_readings (userid, question_id, result_json)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (userid, question_id, json.dumps(result)),
        )
        row = cur.fetchone()
        conn.commit()
    if not row or row[0] is None:
        raise RuntimeError("Prashna reading was not saved")
    return int(row[0])


def _load_prashna_reading(userid: int, reading_id: int):
    _ensure_prashna_readings()
    import json

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT result_json
            FROM prashna_readings
            WHERE id = ? AND userid = ?
            """,
            (reading_id, userid),
        )
        row = cur.fetchone()
    if not row or not row[0]:
        return None
    stored = row[0]
    return json.loads(stored) if isinstance(stored, str) else stored


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


@router.get("/readings/{reading_id}")
def reading_route(reading_id: int, current_user: User = Depends(get_current_user)):
    """Return one saved Prashna casting for this user. Does not charge credits."""
    if reading_id < 1:
        raise HTTPException(status_code=404, detail="Prashna reading not found")
    stored = _load_prashna_reading(current_user.userid, reading_id)
    if not stored:
        raise HTTPException(status_code=404, detail="Prashna reading not found")
    return stored


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
        reading_id = _save_prashna_reading(current_user.userid, request.question_id, result)
        if not credit_service.spend_credits(
            current_user.userid,
            cost,
            "prashna_analysis",
            f"Classical Prashna: {request.question_id}",
            metadata=prashna_usage_metadata(reading_id),
        ):
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
