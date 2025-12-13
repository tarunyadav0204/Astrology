from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from calculators.yogini_dasha_calculator import YoginiDashaCalculator
from calculators.chart_calculator import ChartCalculator
router = APIRouter()

class YoginiDashaRequest(BaseModel):
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str
    years: Optional[int] = 5

@router.post("/yogini-dasha")
async def get_yogini_dasha(request: YoginiDashaRequest):
    """Get Yogini Dasha periods with current status and timeline"""
    try:
        # Calculate chart to get Moon longitude
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(
            date=request.date,
            time=request.time,
            latitude=request.latitude,
            longitude=request.longitude,
            timezone=request.timezone
        )
        
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        moon_lon = chart_data['planets']['Moon']['longitude']
        
        # Initialize Yogini calculator
        yogini_calc = YoginiDashaCalculator()
        
        # Get current Yogini Dasha
        birth_data = {
            'date': request.date,
            'time': request.time,
            'latitude': request.latitude,
            'longitude': request.longitude,
            'timezone': request.timezone
        }
        
        current_yogini = yogini_calc.calculate_current_yogini(birth_data, moon_lon)
        
        # Get full lifetime timeline (120 years default)
        timeline = yogini_calc.get_full_timeline(birth_data, moon_lon)
        
        # Inject sub_periods for current Mahadasha (match by name AND dates)
        current_maha = current_yogini['mahadasha']
        for period in timeline:
            if (period['name'] == current_maha['name'] and 
                period['start'] == current_maha['start'] and 
                period['end'] == current_maha['end']):
                # Convert string dates back to datetime objects for calculation
                p_start = datetime.strptime(period['start'], '%Y-%m-%d')
                p_end = datetime.strptime(period['end'], '%Y-%m-%d')
                
                # Use the new helper method to get the list
                period['sub_periods'] = yogini_calc.get_sub_periods_list(
                    period['name'],
                    p_start,
                    p_end
                )
                break
        
        # Calculate progress percentage for current Antardasha
        ad_start = datetime.strptime(current_yogini['antardasha']['start'], '%Y-%m-%d')
        ad_end = datetime.strptime(current_yogini['antardasha']['end'], '%Y-%m-%d')
        now = datetime.now()
        
        total_days = (ad_end - ad_start).days
        elapsed_days = (now - ad_start).days
        progress = (elapsed_days / total_days * 100) if total_days > 0 else 0
        progress = max(0, min(100, progress))  # Clamp between 0-100
        
        # Debug: Log sub_periods for current Mahadasha
        for period in timeline:
            if (period['name'] == current_maha['name'] and 
                period['start'] == current_maha['start'] and 
                period['end'] == current_maha['end']):
                print(f"DEBUG: Current Mahadasha '{current_maha['name']}' has {len(period.get('sub_periods', []))} sub-periods")
                if 'sub_periods' in period:
                    for sp in period['sub_periods']:
                        print(f"  - {sp['name']} ({sp['lord']}): {sp['start']} to {sp['end']}")
                break
        
        # Format response for frontend
        response = {
            'current': {
                'mahadasha': {
                    'name': current_yogini['mahadasha']['name'],
                    'lord': current_yogini['mahadasha']['lord'],
                    'start': current_yogini['mahadasha']['start'],
                    'end': current_yogini['mahadasha']['end'],
                    'vibe': current_yogini['mahadasha']['vibe']
                },
                'antardasha': {
                    'name': current_yogini['antardasha']['name'],
                    'lord': current_yogini['antardasha']['lord'],
                    'start': current_yogini['antardasha']['start'],
                    'end': current_yogini['antardasha']['end'],
                    'vibe': current_yogini['antardasha']['vibe']
                },
                'progress': round(progress, 1),
                'significance': current_yogini.get('significance', '')
            },
            'timeline': timeline
        }
        
        return response
        
    except Exception as e:
        import traceback
        print(f"ERROR in Yogini Dasha calculation: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error calculating Yogini Dasha: {str(e)}")
