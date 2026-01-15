from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from auth import get_current_user, User

router = APIRouter()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    place: str = ""
    gender: str = ""
    timezone: Optional[str] = None

class TransitRequest(BaseModel):
    birth_data: BirthData
    transit_date: str

@router.post("/ashtakavarga/yearly-house-strength")
async def get_yearly_house_strength(request: dict, current_user: User = Depends(get_current_user)):
    """Calculate daily ashtakvarga strength for a specific house throughout the year"""
    try:
        from calculators.ashtakavarga import AshtakavargaCalculator
        from calculators.chart_calculator import ChartCalculator
        from utils.timezone_service import get_timezone_from_coordinates
        
        birth_data = BirthData(**request['birth_data'])
        
        # Get timezone if not provided
        if not birth_data.timezone:
            birth_data.timezone = get_timezone_from_coordinates(
                birth_data.latitude,
                birth_data.longitude
            )
        house_number = request['house_number']
        year = request.get('year', datetime.now().year)
        
        # Calculate birth chart ashtakvarga first
        calculator = ChartCalculator({})
        chart_data = calculator.calculate_chart(birth_data, 'mean')
        
        birth_calculator = AshtakavargaCalculator(birth_data, chart_data)
        birth_sarva = birth_calculator.calculate_sarvashtakavarga()
        
        # Get birth bindus for this house
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        sign_num = (house_number - 1 + ascendant_sign) % 12
        birth_bindus = birth_sarva['sarvashtakavarga'].get(str(sign_num), 0)
        
        # Calculate daily transit ashtakvarga for the year
        daily_data = []
        start_date = datetime(year, 1, 1)
        
        # Import calculate_transits from main
        from main import calculate_transits
        
        for day in range(365):
            current_date = start_date + timedelta(days=day)
            
            # Calculate transit for this date
            transit_request = TransitRequest(
                birth_data=birth_data,
                transit_date=current_date.strftime('%Y-%m-%d')
            )
            transit_chart = await calculate_transits(transit_request)
            
            # Calculate ashtakvarga for transit
            transit_calculator = AshtakavargaCalculator(birth_data, transit_chart)
            transit_sarva = transit_calculator.calculate_sarvashtakavarga()
            transit_bindus = transit_sarva['sarvashtakavarga'].get(str(sign_num), 0)
            
            # Categorize strength
            if transit_bindus >= 30:
                category = "strong"
            elif transit_bindus <= 25:
                category = "weak"
            else:
                category = "moderate"
            
            daily_data.append({
                "date": current_date.strftime('%Y-%m-%d'),
                "bindus": transit_bindus,
                "difference": transit_bindus - birth_bindus,
                "category": category
            })
        
        return {
            "house": house_number,
            "year": year,
            "birth_bindus": birth_bindus,
            "daily_data": daily_data
        }
        
    except Exception as e:
        print(f"Yearly house strength error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")
