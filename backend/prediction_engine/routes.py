from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from birth_charts.routes import _row_to_chart
from db import execute, get_conn
from utils.timezone_service import get_iana_timezone

from .contracts import BirthChartInput, PredictionRequest
from .errors import PredictionEngineError
from .service import PredictionService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prediction-engine", tags=["prediction-engine"])


class ActivationExplorerRequest(BaseModel):
    birth_chart_id: Optional[int] = None
    birth_data: Optional[Dict[str, Any]] = None
    as_of: date = Field(default_factory=date.today)
    horizon_days: int = Field(default=90, ge=1, le=366)
    maximum_candidates: int = Field(default=100, ge=1, le=100)
    trace: bool = True

    @model_validator(mode="after")
    def require_chart_source(self):
        if self.birth_chart_id is None and not self.birth_data:
            raise ValueError("birth_chart_id or birth_data is required")
        return self


def _load_owned_birth_chart(chart_id: int, user_id: int) -> Dict[str, Any]:
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT id, userid, name, date, time, latitude, longitude, timezone,
                   created_at, place, gender, relation, relation_order,
                   relation_side, relation_label, is_family_member
            FROM birth_charts
            WHERE id = %s AND userid = %s
            """,
            (chart_id, user_id),
        )
        row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Birth chart not found")
    return _row_to_chart(row)


def _normalise_birth_data(payload: Dict[str, Any]) -> Dict[str, Any]:
    value = dict(payload)
    if value.get("chart_id") is not None and value.get("birth_chart_id") is None:
        value["birth_chart_id"] = value["chart_id"]
    if value.get("id") is not None and value.get("birth_chart_id") is None:
        value["birth_chart_id"] = value["id"]
    if not value.get("timezone") and value.get("latitude") is not None and value.get("longitude") is not None:
        value["timezone"] = get_iana_timezone(
            float(value["latitude"]),
            float(value["longitude"]),
        )
    value["date"] = str(value.get("date") or "").split("T", 1)[0]
    raw_time = str(value.get("time") or "")
    value["time"] = raw_time.split("T", 1)[-1][:8] if "T" in raw_time else raw_time[:8]
    return value


def _generate_activation_dossier(payload: ActivationExplorerRequest, chart: Dict[str, Any]) -> Dict[str, Any]:
    birth = BirthChartInput.from_mapping(_normalise_birth_data(chart))
    result = PredictionService().generate(
        PredictionRequest(
            birth=birth,
            as_of=payload.as_of,
            horizon_days=payload.horizon_days,
            maximum_candidates=payload.maximum_candidates,
            trace=payload.trace,
            exploration_mode=True,
        )
    )
    response = result.to_dict(include_evidence=payload.trace)
    response["chart"] = {
        "id": birth.birth_chart_id,
        "name": birth.name,
        "date": birth.date,
        "time": birth.time,
        "place": birth.place,
    }
    return response


@router.post("/activation-explorer")
async def get_activation_explorer(
    payload: ActivationExplorerRequest,
    current_user: User = Depends(get_current_user),
):
    """Return a deterministic, traceable activation dossier for one chart."""
    try:
        chart = (
            _load_owned_birth_chart(payload.birth_chart_id, current_user.userid)
            if payload.birth_chart_id is not None
            else dict(payload.birth_data or {})
        )
        return await run_in_threadpool(_generate_activation_dossier, payload, chart)
    except HTTPException:
        raise
    except PredictionEngineError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception(
            "Activation Explorer calculation failed for user=%s chart=%s",
            current_user.userid,
            payload.birth_chart_id,
        )
        raise HTTPException(
            status_code=500,
            detail="Activation calculation failed. No fallback result was generated.",
        ) from exc
