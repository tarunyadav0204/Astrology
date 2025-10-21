from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from classical_engine.advanced_classical import AdvancedClassicalTechniques

router = APIRouter()

class BirthData(BaseModel):
    name: str
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: str

@router.post("/chara-karakas")
async def calculate_chara_karakas(request: Dict[str, Any]):
    """Calculate Chara Karakas (variable significators) from chart data"""
    try:
        chart_data = request.get('chart_data', {})
        birth_data = request.get('birth_data', {})
        
        if not chart_data or not chart_data.get('planets'):
            raise HTTPException(status_code=400, detail="Chart data with planets required")
        
        # Initialize advanced classical techniques
        advanced_techniques = AdvancedClassicalTechniques(birth_data, chart_data.get('planets', {}))
        
        # Calculate Chara Karakas
        chara_karakas_result = advanced_techniques.analyze_chara_karakas()
        
        # Format the result for frontend
        formatted_karakas = {}
        karaka_descriptions = {
            "Atmakaraka": {
                "title": "Soul Significator",
                "description": "Represents the soul, self, and overall life purpose. Most important planet in the chart.",
                "areas": ["Self-realization", "Life purpose", "Spiritual growth", "Personal identity"]
            },
            "Amatyakaraka": {
                "title": "Career Significator", 
                "description": "Represents career, profession, and material achievements.",
                "areas": ["Career", "Profession", "Work environment", "Material success"]
            },
            "Bhratrukaraka": {
                "title": "Siblings Significator",
                "description": "Represents siblings, courage, and personal efforts.",
                "areas": ["Siblings", "Courage", "Personal efforts", "Initiative"]
            },
            "Matrukaraka": {
                "title": "Mother Significator",
                "description": "Represents mother, home, emotions, and nurturing.",
                "areas": ["Mother", "Home", "Emotions", "Nurturing", "Comfort"]
            },
            "Putrakaraka": {
                "title": "Children Significator", 
                "description": "Represents children, creativity, and intelligence.",
                "areas": ["Children", "Creativity", "Intelligence", "Learning", "Innovation"]
            },
            "Gnatikaraka": {
                "title": "Obstacles Significator",
                "description": "Represents obstacles, diseases, enemies, and challenges.",
                "areas": ["Obstacles", "Health issues", "Enemies", "Challenges", "Competition"]
            },
            "Darakaraka": {
                "title": "Spouse Significator",
                "description": "Represents spouse, partnerships, and relationships.",
                "areas": ["Spouse", "Marriage", "Partnerships", "Relationships", "Cooperation"]
            }
        }
        
        for karaka_name, karaka_data in chara_karakas_result.get('chara_karakas', {}).items():
            planet = karaka_data['planet']
            degree = karaka_data['degree']
            
            # Get planet data from chart
            planet_info = chart_data['planets'].get(planet, {})
            
            formatted_karakas[karaka_name] = {
                'planet': planet,
                'degree_in_sign': round(degree, 2),
                'sign': planet_info.get('sign', 0),
                'house': planet_info.get('house', 1),
                'longitude': planet_info.get('longitude', 0),
                'title': karaka_descriptions.get(karaka_name, {}).get('title', karaka_name),
                'description': karaka_descriptions.get(karaka_name, {}).get('description', ''),
                'life_areas': karaka_descriptions.get(karaka_name, {}).get('areas', [])
            }
        
        return {
            "chara_karakas": formatted_karakas,
            "calculation_method": "Highest to lowest degrees in signs (excluding Rahu/Ketu)",
            "system": "Jaimini Chara Karaka System"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate Chara Karakas: {str(e)}")