from fastapi import APIRouter, Request
from typing import Dict, List
from datetime import datetime, timedelta
from ..calculators.timeline_calculator import NadiTimelineCalculator
from ..config.nadi_config import NADI_CONFIG

router = APIRouter()

class TimelineService:
    """Separate service for timeline calculations"""
    
    def __init__(self):
        self.timeline_calculator = NadiTimelineCalculator()
    
    def get_aspect_timeline(self, request: Dict) -> Dict:
        """Get timeline for specific aspect and year range"""
        natal_planets = request['natal_planets']
        aspect_type = request['aspect_type']
        planet1 = request['planet1']
        planet2 = request['planet2']
        start_year = request.get('start_year', datetime.now().year)
        year_range = request.get('year_range', 1)  # Default 1 year
        
        # Calculate timeline for specific year range only
        timeline = self.timeline_calculator.calculate_aspect_timeline_range(
            natal_planets, aspect_type, planet1, planet2, start_year, year_range
        )
        
        return {
            'timeline': timeline,
            'start_year': start_year,
            'year_range': year_range
        }

timeline_service = TimelineService()

@router.post("/nadi-timeline")
async def get_aspect_timeline(request: Request):
    """API endpoint for aspect timeline"""
    request_data = await request.json()
    return timeline_service.get_aspect_timeline(request_data)