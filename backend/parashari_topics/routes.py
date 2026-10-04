"""Authenticated Parashari Topic Lens APIs."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from credits.entitlements import ASTROLOGER_TOOLS_ENTITLEMENT, require_entitlement
from prediction_engine.routes import _load_owned_birth_chart

from .registry import get_topic, public_topics
from .service import TopicJudgmentService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parashari", tags=["parashari-topics"])
service = TopicJudgmentService()


class TopicJudgmentRequest(BaseModel):
    topic_id: str
    birth_chart_id: Optional[int] = None
    birth_data: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None
    as_of: date = Field(default_factory=date.today)
    calculation_profile: Optional[Dict[str, str]] = None

    @model_validator(mode="after")
    def validate_request(self):
        get_topic(self.topic_id)
        if self.birth_chart_id is None and not self.birth_data:
            raise ValueError("birth_chart_id or birth_data is required")
        return self


class TopicTimingRequest(TopicJudgmentRequest):
    start_date: date
    days: int = Field(default=120, ge=1, le=366)


def _birth_data(request: TopicJudgmentRequest, user: User) -> Dict[str, Any]:
    if request.birth_chart_id is not None:
        return _load_owned_birth_chart(request.birth_chart_id, user.userid)
    return dict(request.birth_data or {})


@router.get("/topics")
async def topics(current_user: User = Depends(get_current_user)):
    return public_topics()


@router.post("/topic-judgment")
async def topic_judgment(
    request: TopicJudgmentRequest,
    current_user: User = Depends(get_current_user),
):
    require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
    try:
        return await run_in_threadpool(
            service.generate,
            topic_key=request.topic_id,
            birth_data=_birth_data(request, current_user),
            chart_data=request.chart_data,
            as_of=request.as_of,
            calculation_profile=request.calculation_profile,
        )
    except HTTPException:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Unable to calculate Topic Lens: {exc}") from exc
    except Exception as exc:
        logger.exception("Topic Lens failed for user=%s topic=%s", current_user.userid, request.topic_id)
        raise HTTPException(status_code=500, detail="Topic Lens calculation failed. No fallback was generated.") from exc


@router.post("/topic-timing")
async def topic_timing(
    request: TopicTimingRequest,
    current_user: User = Depends(get_current_user),
):
    require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
    try:
        return await run_in_threadpool(
            service.timing,
            topic_key=request.topic_id,
            birth_data=_birth_data(request, current_user),
            chart_data=request.chart_data,
            start_date=request.start_date,
            days=request.days,
            calculation_profile=request.calculation_profile,
        )
    except HTTPException:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Unable to calculate Topic Lens timing: {exc}") from exc
    except Exception as exc:
        logger.exception("Topic timing failed for user=%s topic=%s", current_user.userid, request.topic_id)
        raise HTTPException(status_code=500, detail="Topic timing calculation failed. No fallback was generated.") from exc
