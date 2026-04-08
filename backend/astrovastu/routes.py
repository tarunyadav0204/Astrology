"""
AstroVastu API — V1 deterministic map + narrative (see docs/ASTROVASTU_PRODUCT_SPEC.md).
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user, User
from ai.gemini_astrovastu_analyzer import GeminiAstroVastuAnalyzer
from calculators.chart_calculator import ChartCalculator
from shared.dasha_calculator import DashaCalculator

from .mapping_engine import MAPPING_VERSION, build_energy_map
from .storage import get_latest_run, save_latest_run

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/astrovastu", tags=["astrovastu"])
_ai_analyzer: Optional[GeminiAstroVastuAnalyzer] = None


def _get_ai_analyzer() -> GeminiAstroVastuAnalyzer:
    global _ai_analyzer
    if _ai_analyzer is None:
        _ai_analyzer = GeminiAstroVastuAnalyzer()
    return _ai_analyzer


class AstroVastuAnalyzeRequest(BaseModel):
    birth_data: Dict[str, Any] = Field(..., description="name, date, time, latitude, longitude, timezone, place, gender")
    goal: str = Field("complete_all", description="complete_all (default) | wealth | career | relationship | health | focus")
    door_facing: str = Field("E", description="N | NE | E | SE | S | SW | W | NW")
    zone_tags: Optional[Dict[str, List[str]]] = Field(
        None,
        description="Map direction keys to tags: toilet, bed, kitchen, desk, storage, main_door, empty, clutter, other",
    )


class _BirthDataSimple:
    """Minimal birth object for ChartCalculator (same pattern as /calculate-chart-only)."""

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "Unknown")
        self.date = data.get("date")
        self.time = data.get("time")
        self.latitude = float(data.get("latitude") or 0)
        self.longitude = float(data.get("longitude") or 0)
        self.timezone = data.get("timezone") or ""
        self.place = data.get("place", "")
        self.gender = data.get("gender", "")
        self.relation = data.get("relation", "other")

    @property
    def timezone_offset(self):
        try:
            from utils.timezone_service import get_timezone_from_coordinates

            return get_timezone_from_coordinates(self.latitude, self.longitude)
        except Exception:
            return "UTC+0"


@router.post("/analyze")
async def analyze_astrovastu(
    request: AstroVastuAnalyzeRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Compute whole-sign chart and return personalized 8-direction energy map.
    V1: no credits gate (add credit_settings + spend in a later iteration).
    """
    try:
        birth_obj = _BirthDataSimple(request.birth_data)
        if not birth_obj.date or not birth_obj.time:
            raise HTTPException(status_code=400, detail="date and time are required")

        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_obj)
        dasha_calc = DashaCalculator()
        dasha_context = dasha_calc.calculate_current_dashas(request.birth_data)
        houses = chart_data.get("houses") or []
        asc_name = houses[0].get("sign_name") if houses else None

        payload = build_energy_map(
            chart_data,
            door_facing=request.door_facing,
            zone_tags=request.zone_tags,
            goal=request.goal,
            dasha_context=dasha_context,
        )

        payload["meta"] = {
            "mapping_version": MAPPING_VERSION,
            "userid": current_user.userid,
            "ascendant_sign": asc_name,
            "ai_enrichment_used": False,
            "dasha_mahadasha": (dasha_context or {}).get("mahadasha", {}).get("planet"),
            "dasha_antardasha": (dasha_context or {}).get("antardasha", {}).get("planet"),
        }
        try:
            ai = _get_ai_analyzer()
            ai_data = ai.enrich(
                payload=payload,
                birth_data=request.birth_data,
                goal=request.goal,
                door_facing=request.door_facing,
                zone_tags=request.zone_tags,
            )
            payload["ai"] = ai_data
            payload["meta"]["ai_enrichment_used"] = True
            payload["meta"]["ai_model"] = ai_data.get("ai_model")
        except Exception as ai_exc:
            logger.warning("AstroVastu Gemini enrichment skipped: %s", ai_exc)
            payload["meta"]["ai_fallback_reason"] = str(ai_exc)

        try:
            save_latest_run(
                current_user.userid,
                request.birth_data,
                request.goal,
                request.door_facing,
                request.zone_tags,
                MAPPING_VERSION,
                payload,
            )
        except Exception as db_exc:
            logger.warning("AstroVastu save_latest_run failed (response still returned): %s", db_exc)
        return payload
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("AstroVastu analyze failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AstroVastu analysis failed: {e}")


@router.get("/mapping-version")
async def get_mapping_version(current_user: User = Depends(get_current_user)):
    return {"mapping_version": MAPPING_VERSION}


@router.get("/latest")
async def get_latest_astrovastu(current_user: User = Depends(get_current_user)):
    """
    Return the user's most recently saved AstroVastu result (after POST /analyze).
    Includes stored request inputs so the client can restore or compare before re-running.
    """
    try:
        row = get_latest_run(current_user.userid)
    except Exception as e:
        logger.exception("get_latest_astrovastu failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not load saved map")
    if not row:
        return {"has_saved": False}
    return {
        "has_saved": True,
        "updated_at": row["updated_at"],
        "input_hash": row["input_hash"],
        "mapping_version": row["mapping_version"],
        "request": row["request"],
        "result": row["result"],
    }
