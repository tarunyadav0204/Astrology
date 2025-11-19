from fastapi import APIRouter, Request, Depends
from typing import Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel

try:
    from calculators.real_transit_calculator import RealTransitCalculator
    real_calculator = RealTransitCalculator()
except ImportError:
    real_calculator = None

router = APIRouter()

# Use the old class for compatibility but with real calculations
class VedicTransitAspectCalculator:
    def calculate_vedic_aspects(self, birth_data: Dict) -> List[Dict]:
        if real_calculator is None:
            return []  # Return empty if calculator not available
        
        real_aspects = real_calculator.find_real_aspects(birth_data)
        
        # Convert to expected format
        aspects = []
        for aspect in real_aspects:
            aspects.append({
                'planet1': aspect['transit_planet'],
                'planet2': aspect['natal_planet'],
                'aspect_type': f'{aspect["aspect_number"]}th_house',
                'natal_longitude': aspect['natal_longitude'],
                'natal_house': aspect['natal_house'],
                'aspect_house': aspect['aspect_number'],
                'description': f'Transit {aspect["transit_planet"]} {aspect["aspect_number"]}th house aspect to natal {aspect["natal_planet"]}',
                'enhancement_type': 'regular',
                'aspect_data': aspect  # Store full data for timeline calculation
            })
        
        return aspects
    
    def calculate_aspect_timeline(self, aspect_data: Dict, start_year: int, year_range: int) -> List[Dict]:
        if real_calculator is None:
            return []  # Return empty if calculator not available
        return real_calculator.calculate_aspect_timeline(aspect_data, start_year, year_range)

vedic_calculator = VedicTransitAspectCalculator()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str

@router.get("/test-vedic-aspects")
async def test_vedic_aspects():
    """Test endpoint to verify router is working"""
    return {"message": "Vedic transit aspects router is working!"}

@router.post("/vedic-transit-aspects")
async def get_vedic_transit_aspects(request: Request):
    """Get real Vedic transit aspects using astronomical calculations"""
    request_data = await request.json()
    birth_data = request_data['birth_data']
    
    # Use real calculator
    aspects = vedic_calculator.calculate_vedic_aspects(birth_data)
    
    return {
        'aspects': aspects
    }

@router.post("/vedic-transit-timeline")
async def get_vedic_transit_timeline(request: Request):
    """Get real timeline for specific Vedic transit aspect"""
    request_data = await request.json()
    
    birth_data = request_data['birth_data']
    aspect_type = request_data['aspect_type']
    planet1 = request_data['planet1']  # Transit planet
    planet2 = request_data['planet2']  # Natal planet
    start_year = request_data.get('start_year', datetime.now().year)
    year_range = request_data.get('year_range', 1)
    
    # Find the matching aspect data
    aspects = vedic_calculator.calculate_vedic_aspects(birth_data)
    
    matching_aspect = None
    for aspect in aspects:
        if (aspect['planet1'] == planet1 and 
            aspect['planet2'] == planet2 and 
            aspect['aspect_type'] == aspect_type):
            matching_aspect = aspect.get('aspect_data')
            break
    
    if not matching_aspect:
        return {'timeline': [], 'start_year': start_year, 'year_range': year_range}
    
    # Calculate real timeline
    timeline = vedic_calculator.calculate_aspect_timeline(
        matching_aspect, start_year, year_range
    )
    
    return {
        'timeline': timeline,
        'start_year': start_year,
        'year_range': year_range
    }

@router.post("/vedic-transit-timelines-bulk")
async def get_bulk_vedic_transit_timelines(request: Request):
    """Get timelines for ALL aspects in a single call"""
    request_data = await request.json()
    
    birth_data = request_data['birth_data']
    year = request_data.get('year', datetime.now().year)
    year_range = request_data.get('year_range', 1)
    
    # Get all aspects first
    aspects = vedic_calculator.calculate_vedic_aspects(birth_data)
    
    # Calculate timelines for ALL aspects in one call
    all_timelines = {}
    for aspect in aspects:
        if aspect.get('aspect_data'):
            timeline = vedic_calculator.calculate_aspect_timeline(
                aspect['aspect_data'], year, year_range
            )
            aspect_key = f"{aspect['planet1']}-{aspect['planet2']}-{aspect['aspect_type']}"
            all_timelines[aspect_key] = timeline
    
    return {
        'aspects': aspects,
        'timelines': all_timelines,
        'year': year,
        'year_range': year_range
    }

@router.post("/dasha-timeline")
async def get_dasha_timeline(request: Request):
    """Get pre-computed dasha timeline for efficient filtering"""
    request_data = await request.json()
    birth_data = request_data['birth_data']
    start_year = request_data.get('start_year', 2020)
    end_year = request_data.get('end_year', 2030)
    
    try:
        dasha_timeline = []
        
        # Calculate dashas every 3 days for better granularity
        current_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        while current_date <= end_date:
            date = current_date
            
            # Use existing dasha calculation
            from shared.dasha_calculator import DashaCalculator
            calculator = DashaCalculator()
            
            # Convert birth_data to expected format
            birth_dict = {
                'name': birth_data['name'],
                'date': birth_data['date'],
                'time': birth_data['time'],
                'latitude': birth_data['latitude'],
                'longitude': birth_data['longitude'],
                'timezone': birth_data['timezone']
            }
            
            dasha_data = calculator.calculate_dashas_for_date(date, birth_dict)
            
            dasha_timeline.append({
                'date': date.isoformat(),
                'mahadasha': dasha_data.get('mahadasha', {}).get('planet', ''),
                'antardasha': dasha_data.get('antardasha', {}).get('planet', ''),
                'pratyantardasha': dasha_data.get('pratyantardasha', {}).get('planet', ''),
                'sookshmadasha': dasha_data.get('sookshma', {}).get('planet', ''),
                'pranadasha': dasha_data.get('prana', {}).get('planet', '')
            })
            
            current_date += timedelta(days=3)
        
        return {
            'dasha_timeline': dasha_timeline,
            'start_year': start_year,
            'end_year': end_year
        }
    
    except Exception as e:
        return {'dasha_timeline': [], 'error': str(e)}