from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from credits.entitlements import ASTROLOGER_TOOLS_ENTITLEMENT, require_entitlement
from reports.context.base_context_builder import calculate_chart_for_birth

from .calculator import LongevityCalculator


router = APIRouter(prefix="/longevity", tags=["longevity"])


class LongevityRequest(BaseModel):
    birth_data: Dict[str, Any]
    chart_data: Optional[Dict[str, Any]] = None
    horizon_years: int = Field(default=12, ge=1, le=30)
    subject: Literal["self", "mother", "father"] = "self"


@router.post("/calculate")
async def calculate_longevity(
    request: LongevityRequest,
    current_user: User = Depends(get_current_user),
):
    """Return licensed deterministic longevity evidence without chat-credit use."""
    require_entitlement(current_user, ASTROLOGER_TOOLS_ENTITLEMENT)
    try:
        chart = request.chart_data or calculate_chart_for_birth(request.birth_data)
        result = LongevityCalculator(request.birth_data, chart, subject=request.subject).calculate(horizon_years=request.horizon_years)
        return {"success": True, "result": result}
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Unable to calculate longevity: {exc}") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Longevity calculation failed: {exc}") from exc
