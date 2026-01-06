from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from calculators.chara_dasha_calculator import CharaDashaCalculator
from calculators.chart_calculator import ChartCalculator
from utils.timezone_service import parse_timezone_offset

router = APIRouter(prefix="/chara-dasha", tags=["Chara Dasha"])

class BirthData(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    latitude: float
    longitude: float
    place: Optional[str] = None
    
    @property
    def timezone(self):
        """Auto-detect timezone from coordinates"""
        try:
            return parse_timezone_offset('', self.latitude, self.longitude)
        except Exception:
            return 5.5  # IST fallback

@router.post("/calculate")
async def calculate_chara_dasha(birth_data: BirthData):
    """Calculate Jaimini Chara Dasha periods"""
    try:
        # Calculate birth chart
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data.dict())
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Calculate Chara Dasha
        chara_calc = CharaDashaCalculator(chart_data)
        dob_dt = datetime.strptime(birth_data.date, '%Y-%m-%d')
        dasha_data = chara_calc.calculate_dasha(dob_dt)
        
        return {
            "status": "success",
            "system": dasha_data["system"],
            "periods": dasha_data["periods"],
            "ascendant_sign": int(chart_data.get('ascendant', 0) / 30),
            "ascendant_name": _get_sign_name(int(chart_data.get('ascendant', 0) / 30))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AntardashaRequest(BaseModel):
    name: Optional[str] = None
    date: str
    time: str
    latitude: float
    longitude: float
    place: Optional[str] = None
    maha_sign_id: int
    
    @property
    def timezone(self):
        """Auto-detect timezone from coordinates"""
        try:
            return parse_timezone_offset('', self.latitude, self.longitude)
        except Exception:
            return 5.5  # IST fallback

@router.post("/antardasha")
async def calculate_chara_antardasha(request: AntardashaRequest):
    """Calculate Chara Dasha antardashas for a specific mahadasha sign"""
    try:
        print(f"\n=== CHARA ANTARDASHA REQUEST ===")
        print(f"Request data: {request.dict()}")
        print(f"Maha sign ID: {request.maha_sign_id}")
        
        from types import SimpleNamespace
        birth_dict = request.dict(exclude={'maha_sign_id'})
        print(f"Birth dict: {birth_dict}")
        
        birth_obj = SimpleNamespace(**birth_dict)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Calculate full Chara Dasha
        chara_calc = CharaDashaCalculator(chart_data)
        dob_dt = datetime.strptime(request.date, '%Y-%m-%d')
        dasha_data = chara_calc.calculate_dasha(dob_dt)
        
        print(f"Available periods: {[p['sign_id'] for p in dasha_data['periods']]}")
        
        # Find the requested mahadasha period
        maha_period = next((p for p in dasha_data["periods"] if p["sign_id"] == request.maha_sign_id), None)
        if not maha_period:
            print(f"ERROR: Mahadasha period not found for sign_id {request.maha_sign_id}")
            raise HTTPException(status_code=404, detail="Mahadasha period not found")
        
        print(f"Found maha period: {maha_period}")
        
        # Calculate antardashas (12 sub-periods)
        antardashas = _calculate_antardashas(maha_period, chara_calc)
        
        return {
            "status": "success",
            "maha_sign": maha_period["sign_name"],
            "maha_sign_id": request.maha_sign_id,
            "antar_periods": antardashas
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n=== CHARA ANTARDASHA ERROR ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_antardashas(maha_period: dict, chara_calc: CharaDashaCalculator) -> list:
    """Calculate 12 antardasha sub-periods for a mahadasha using calculator's method"""
    from datetime import datetime
    
    maha_sign_id = maha_period["sign_id"]
    total_years = maha_period["duration_years"]
    start_date = datetime.strptime(maha_period["start_date"], "%Y-%m-%d")
    current_time = datetime.now()
    
    # Use the calculator's method to ensure consistency
    antardashas = chara_calc._calculate_antardashas(maha_sign_id, total_years, start_date, current_time)
    
    # Add 'sign' key for frontend compatibility
    for ad in antardashas:
        ad['sign'] = ad['sign_name']  # Frontend expects 'sign' key
    
    return antardashas

def _get_sign_name(sign_id: int) -> str:
    """Get sign name from sign ID"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs[sign_id]
