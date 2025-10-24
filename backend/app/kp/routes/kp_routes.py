from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from auth import get_current_user
from ..services.chart_service import KPChartService
from ..services.horary_service import KPHoraryService
from ..services.event_timing_service import KPEventTimingService
from ..utils.kp_calculations import KPCalculations

router = APIRouter(prefix="/kp", tags=["KP Astrology"])

class KPChartRequest(BaseModel):
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone_offset: Optional[float] = 0

class HoraryRequest(BaseModel):
    question_number: int
    question_text: str

class EventTimingRequest(BaseModel):
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    event_type: str

@router.post("/chart")
async def calculate_kp_chart(request: KPChartRequest, current_user: dict = Depends(get_current_user)):
    """Calculate KP chart with Placidus houses"""
    try:
        chart_data = KPChartService.calculate_kp_chart(
            request.birth_date,
            request.birth_time,
            request.latitude,
            request.longitude,
            request.timezone_offset
        )
        return {"success": True, "data": chart_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sub-lords")
async def get_sub_lords(request: KPChartRequest, current_user: dict = Depends(get_current_user)):
    """Get sub-lords for planets and cusps"""
    try:
        chart_data = KPChartService.calculate_kp_chart(
            request.birth_date,
            request.birth_time,
            request.latitude,
            request.longitude,
            request.timezone_offset
        )
        
        return {
            "success": True,
            "data": {
                "planet_sub_lords": chart_data["planet_sub_lords"],
                "cusp_sub_lords": chart_data["cusp_sub_lords"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ruling-planets")
async def get_ruling_planets(request: KPChartRequest, current_user: dict = Depends(get_current_user)):
    """Get KP ruling planets"""
    try:
        birth_datetime = datetime.strptime(f"{request.birth_date} {request.birth_time}", "%Y-%m-%d %H:%M")
        ruling_planets = KPCalculations.get_ruling_planets(
            birth_datetime,
            request.latitude,
            request.longitude
        )
        return {"success": True, "data": ruling_planets}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/horary")
async def analyze_horary(request: HoraryRequest, current_user: dict = Depends(get_current_user)):
    """Analyze horary question"""
    try:
        analysis = KPHoraryService.analyze_horary_question(
            request.question_number,
            request.question_text
        )
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/significators")
async def get_significators(request: KPChartRequest, current_user: dict = Depends(get_current_user)):
    """Get house significators"""
    try:
        chart_data = KPChartService.calculate_kp_chart(
            request.birth_date,
            request.birth_time,
            request.latitude,
            request.longitude,
            request.timezone_offset
        )
        
        return {
            "success": True,
            "data": {
                "significators": chart_data["significators"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/event-timing")
async def predict_event_timing(request: EventTimingRequest, current_user: dict = Depends(get_current_user)):
    """Predict event timing"""
    try:
        birth_data = {
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "latitude": request.latitude,
            "longitude": request.longitude
        }
        
        predictions = KPEventTimingService.predict_event_timing(
            birth_data,
            request.event_type
        )
        return {"success": True, "data": predictions}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))