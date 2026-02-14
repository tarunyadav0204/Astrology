from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from auth import get_current_user
from calculators.yoga_calculator import YogaCalculator
from calculators.chart_calculator import ChartCalculator

class YogaRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    gender: Optional[str] = None

router = APIRouter(prefix="/yogas", tags=["yogas"])

@router.post("/")
async def get_yogas(request: YogaRequest, current_user = Depends(get_current_user)):
    """
    Calculates and returns all yogas for a given birth chart.
    """
    try:
        from types import SimpleNamespace
        
        birth_data = SimpleNamespace(
            name=request.name,
            date=request.date,
            time=request.time,
            place=request.place,
            latitude=request.latitude or 28.6139,
            longitude=request.longitude or 77.2090,
            timezone=request.timezone or 'UTC+0',
            gender=request.gender
        )

        chart_calculator = ChartCalculator({})
        chart_data = chart_calculator.calculate_chart(birth_data)

        yoga_calculator = YogaCalculator(birth_data, chart_data)
        yogas = yoga_calculator.calculate_all_yogas()

        return {"status": "success", "yogas": yogas}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
