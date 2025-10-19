from fastapi import APIRouter
from typing import Dict, List
from ..calculators.aspect_calculator import NadiAspectCalculator
from ..calculators.timeline_calculator import NadiTimelineCalculator
from ..config.nadi_config import NADI_CONFIG

router = APIRouter()

# Include timeline router
from .timeline_service import router as timeline_router
router.include_router(timeline_router)

class NadiService:
    """Main service for Nadi astrology calculations"""
    
    def __init__(self):
        self.aspect_calculator = NadiAspectCalculator()
        self.timeline_calculator = NadiTimelineCalculator()
    
    def get_nadi_analysis(self, birth_data: Dict) -> Dict:
        """Get complete Nadi analysis"""
        try:
            # Extract planet positions from chart data
            natal_planets = self._extract_planet_positions(birth_data)
            
            # Calculate current aspects
            aspects = self.aspect_calculator.calculate_aspects(natal_planets)
            
            # Add planet longitudes first (fast operation)
            for aspect in aspects:
                if aspect['planet1'] in natal_planets:
                    aspect['planet1_longitude'] = natal_planets[aspect['planet1']]['longitude']
                if aspect['planet2'] in natal_planets:
                    aspect['planet2_longitude'] = natal_planets[aspect['planet2']]['longitude']
                
                # Initialize empty timeline - will be loaded on demand
                aspect['timeline'] = []
            
            return {
                'natal_aspects': aspects,
                'planet_positions': natal_planets,
                'config': NADI_CONFIG,
                'natal_planets': natal_planets  # Include for timeline calculations
            }
        except Exception as e:
            # Re-raise the error to show real issues
            raise e
    
    def _extract_planet_positions(self, birth_data: Dict) -> Dict:
        """Extract planet positions from existing chart data"""
        # Integrate with existing chart calculation system
        if 'chart_data' in birth_data and 'planets' in birth_data['chart_data']:
            # Chart data already calculated
            planets = {}
            print(f"Available chart planets: {list(birth_data['chart_data']['planets'].keys())}")
            for planet_name, planet_data in birth_data['chart_data']['planets'].items():
                print(f"Checking planet {planet_name}: in NADI_PLANETS = {planet_name in NADI_CONFIG['NADI_PLANETS']}")
                if planet_name in NADI_CONFIG['NADI_PLANETS']:
                    planets[planet_name] = {
                        'longitude': planet_data['longitude']
                    }
                    print(f"Added {planet_name} with longitude {planet_data['longitude']}")
            print(f"Final extracted planets: {list(planets.keys())}")
            return planets
        else:
            # No chart data provided - this should cause an error
            raise ValueError("Chart data is required for Nadi analysis")

# API endpoint
nadi_service = NadiService()

@router.post("/nadi-analysis")
async def get_nadi_analysis(request: Dict):
    """API endpoint for Nadi analysis"""
    return nadi_service.get_nadi_analysis(request)