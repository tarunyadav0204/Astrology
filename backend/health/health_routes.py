from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Add the parent directory to the path to import calculators
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chart_calculator import ChartCalculator
from calculators.health_calculator import HealthCalculator

router = APIRouter(prefix="/health", tags=["health"])

class BirthDetailsRequest(BaseModel):
    birth_date: str  # YYYY-MM-DD
    birth_time: str  # HH:MM
    birth_place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None

@router.post("/overall-assessment")
async def get_overall_health_assessment(request: BirthDetailsRequest):
    """Get overall health assessment"""
    try:
        # Create birth data object
        from types import SimpleNamespace
        birth_data = SimpleNamespace(
            date=request.birth_date,
            time=request.birth_time,
            place=request.birth_place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+5:30'
        )
        
        # Calculate birth chart
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_data)
        
        # Calculate health analysis
        health_calc = HealthCalculator(chart_data, birth_data)
        health_analysis = health_calc.calculate_overall_health()
        
        return {
            "status": "success",
            "data": health_analysis
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Health calculation error: {error_details}")
        raise HTTPException(status_code=500, detail=f"Health calculation error: {str(e)}\n{error_details}")