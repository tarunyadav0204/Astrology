import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculators.chart_calculator import ChartCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.argala_calculator import ArgalaCalculator
from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from shared.dasha_calculator import DashaCalculator

class BaseAIContextGenerator:
    """Base context generator for all AI analysis types (health, education, career, marriage, etc.)"""
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
    
    def build_base_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build base astrological context needed for all analysis types"""
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        if birth_hash not in self.static_cache:
            self.static_cache[birth_hash] = self._build_static_base_context(birth_data)
        
        static_context = self.static_cache[birth_hash]
        
        # Add dynamic data (always fresh)
        dynamic_context = self._build_dynamic_base_context(birth_data)
        
        # Combine contexts
        return {
            **static_context,
            **dynamic_context
        }
    
    def _build_static_base_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build static base context (cached per birth data)"""
        
        # Calculate birth chart
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Initialize core analyzers
        planet_analyzer = PlanetAnalyzer(chart_data, birth_obj)
        divisional_calc = DivisionalChartCalculator(chart_data)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        argala_calc = ArgalaCalculator(chart_data)
        planetary_war_calc = PlanetaryWarCalculator(chart_data)
        vargottama_calc = VargottamaCalculator(chart_data, {})
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, {})
        
        # Extract ascendant information
        ascendant_degree = chart_data.get('ascendant', 0)
        ascendant_sign_num = int(ascendant_degree / 30)
        ascendant_sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        ascendant_sign_name = ascendant_sign_names[ascendant_sign_num]
        
        # Build base context
        context = {
            # Basic birth details
            "birth_details": {
                "name": birth_data.get('name'),
                "date": birth_data.get('date'),
                "time": birth_data.get('time'),
                "place": birth_data.get('place', birth_data.get('name', 'Unknown')),
                "latitude": birth_data.get('latitude'),
                "longitude": birth_data.get('longitude')
            },
            
            # Ascendant information
            "ascendant_info": {
                "degree": ascendant_degree,
                "sign_number": ascendant_sign_num + 1,
                "sign_name": ascendant_sign_name,
                "exact_degree_in_sign": ascendant_degree % 30,
                "formatted": f"{ascendant_sign_name} {ascendant_degree % 30:.2f}°"
            },
            
            # Main birth chart
            "d1_chart": chart_data,
            
            # Key divisional charts
            "divisional_charts": {
                "d9_navamsa": divisional_calc.calculate_divisional_chart(9),
                "d10_dasamsa": divisional_calc.calculate_divisional_chart(10),
                "d12_dwadasamsa": divisional_calc.calculate_divisional_chart(12)
            },
            
            # Yogas
            "yogas": yoga_calc.calculate_all_yogas(),
            
            # Chara Karakas
            "chara_karakas": chara_karaka_calc.calculate_chara_karakas(),
            
            # Planetary analysis for all planets
            "planetary_analysis": {},
            
            # Special points
            "special_points": {
                "badhaka_lord": badhaka_calc.get_badhaka_lord(int(chart_data['ascendant'] / 30))
            },
            
            # Relationships
            "relationships": {
                "argala_analysis": argala_calc.calculate_argala_analysis()
            },
            
            # Advanced Analysis
            "advanced_analysis": {
                "planetary_wars": planetary_war_calc.get_war_summary(),
                "vargottama_positions": vargottama_calc.get_vargottama_summary(),
                "neecha_bhanga": neecha_bhanga_calc.get_neecha_bhanga_summary()
            }
        }
        
        # Add planetary analysis for all planets
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        for planet in planets:
            try:
                context["planetary_analysis"][planet] = planet_analyzer.analyze_planet(planet)
            except Exception as e:
                continue
        
        return context
    
    def _build_dynamic_base_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build dynamic base context (always fresh)"""
        
        context = {}
        
        # Current dashas (always fresh)
        dasha_calc = DashaCalculator()
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # House lordship mapping
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        context['house_lordships'] = self._get_house_lordships(ascendant_sign)
        
        return context
    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def _get_house_lordships(self, ascendant_sign: int) -> Dict:
        """Get house lordships based on ascendant sign"""
        # Sign lordships (0=Aries, 1=Taurus, etc.)
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        house_lordships = {}
        for house in range(1, 13):
            # Calculate which sign rules this house
            house_sign = (ascendant_sign + house - 1) % 12
            lord = sign_lords[house_sign]
            
            if lord not in house_lordships:
                house_lordships[lord] = []
            house_lordships[lord].append(house)
        
        return house_lordships