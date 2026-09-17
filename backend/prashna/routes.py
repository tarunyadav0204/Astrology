"""Standalone Prashna API. Chat is not wired here."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_optional_user
from prashna.service import analyze_prashna

router = APIRouter(prefix="/prashna", tags=["prashna"])


class PrashnaAnalyzeRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    category: Optional[str] = None
    date: str = Field(..., description="Question date YYYY-MM-DD")
    time: str = Field(..., description="Question local time HH:MM or HH:MM:SS")
    latitude: float
    longitude: float
    timezone: Optional[str] = ""
    place: Optional[str] = ""
    horary_number: Optional[int] = Field(default=None, ge=1, le=249)
    name: Optional[str] = "Prashna"


@router.post("/analyze")
def analyze_prashna_route(
    request: PrashnaAnalyzeRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    del current_user  # Auth is optional; the same payload is reusable from chat later.
    try:
        return analyze_prashna(
            question=request.question.strip(),
            category=request.category,
            date=request.date,
            time=request.time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone or "",
            place=request.place or "",
            horary_number=request.horary_number,
            name=request.name or "Prashna",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prashna calculation failed: {exc}") from exc
