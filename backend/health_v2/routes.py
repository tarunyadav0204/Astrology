"""Licensed preview routes for Health V2."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import User, get_current_user
from credits.entitlements import ASTROLOGER_TOOLS_ENTITLEMENT, require_entitlement
from reports.context.base_context_builder import calculate_chart_for_birth, calculate_divisional_chart

from .natal_engine import NatalHealthBlueprintEngine
from .timing_engine import HealthTimingHeatmapEngine


router = APIRouter(prefix="/health-v2", tags=["health-v2"])


class NatalBlueprintRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Optional[Dict[str, Any]] = None


class TimingHeatmapRequest(NatalBlueprintRequest):
    start_date: date
    days: int = 120


@router.post("/natal-blueprint")
async def natal_blueprint(
    request: NatalBlueprintRequest,
    current_user: User = Depends(get_current_user),
):
    """Return an isolated natal-only professional health preview."""
    require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
    try:
        chart = request.chart_data or calculate_chart_for_birth(request.birth_data)
        has_longitudes = all(
            isinstance(data, dict) and data.get("longitude") is not None
            for planet, data in (chart.get("planets") or {}).items()
            if planet in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        )
        divisions = (
            {
                f"D{division}": calculate_divisional_chart(chart, division)["divisional_chart"]
                for division in (3, 9, 12)
            }
            if has_longitudes else {}
        )
        result = NatalHealthBlueprintEngine(
            chart,
            divisions,
            gender=request.birth_data.get("gender"),
        ).calculate()
        return {"success": True, "result": result}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Unable to calculate Health V2 blueprint: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Health V2 blueprint failed: {exc}") from exc


@router.post("/timing-heatmap")
async def timing_heatmap(
    request: TimingHeatmapRequest,
    current_user: User = Depends(get_current_user),
):
    """Return three-level Vimshottari health activation windows."""
    require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
    try:
        if request.days < 1 or request.days > 366:
            raise ValueError("days must be between 1 and 366")
        chart = request.chart_data or calculate_chart_for_birth(request.birth_data)
        has_longitudes = all(
            isinstance(data, dict) and data.get("longitude") is not None
            for planet, data in (chart.get("planets") or {}).items()
            if planet in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        )
        if not has_longitudes:
            raise ValueError("planetary longitudes are required for transit contacts")
        divisions = {
            f"D{division}": calculate_divisional_chart(chart, division)["divisional_chart"]
            for division in (3, 9, 12)
        }
        blueprint = NatalHealthBlueprintEngine(
            chart, divisions, gender=request.birth_data.get("gender")
        ).calculate()
        result = HealthTimingHeatmapEngine(
            chart, blueprint, request.birth_data
        ).calculate(request.start_date, request.days)
        return {"success": True, "result": result}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Unable to calculate health timing heatmap: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Health timing heatmap failed: {exc}") from exc
