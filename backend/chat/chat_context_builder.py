import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from calculators.chart_calculator import ChartCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.yogi_calculator import YogiCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.friendship_calculator import FriendshipCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.argala_calculator import ArgalaCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.pancha_mahapurusha_calculator import PanchaMahapurushaCalculator
from shared.dasha_calculator import DashaCalculator

class ChatContextBuilder:
    """Builds comprehensive astrological context for chat conversations"""
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
    
    def build_complete_context(self, birth_data: Dict, user_question: str = "", target_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Build complete astrological context for chat"""
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        if birth_hash not in self.static_cache:
            self.static_cache[birth_hash] = self._build_static_context(birth_data)
        
        static_context = self.static_cache[birth_hash]
        
        # Add dynamic data
        dynamic_context = self._build_dynamic_context(birth_data, user_question, target_date)
        
        # Combine contexts
        return {
            **static_context,
            **dynamic_context
        }
    
    def _build_static_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build static chart context (cached per birth data)"""
        
        # Calculate birth chart using existing API endpoint logic
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        
        # Initialize analyzers
        planet_analyzer = PlanetAnalyzer(chart_data, birth_obj)
        divisional_calc = DivisionalChartCalculator(chart_data)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yogi_calc = YogiCalculator(chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        friendship_calc = FriendshipCalculator()
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        argala_calc = ArgalaCalculator(chart_data)
        
        # Advanced calculators
        planetary_war_calc = PlanetaryWarCalculator(chart_data)
        vargottama_calc = VargottamaCalculator(chart_data, {})
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, {})
        pancha_mahapurusha_calc = PanchaMahapurushaCalculator(chart_data)
        
        # Extract and validate ascendant information
        ascendant_degree = chart_data.get('ascendant', 0)
        ascendant_sign_num = int(ascendant_degree / 30)
        ascendant_sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        ascendant_sign_name = ascendant_sign_names[ascendant_sign_num]
        
        # Validate ascendant calculation
        try:
            from chart_validator import validate_ascendant_calculation
            validation = validate_ascendant_calculation(birth_data, ascendant_degree)
            ascendant_validation_note = f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'} - Difference: {validation['difference_degrees']:.4f}°"
        except Exception as e:
            ascendant_validation_note = f"Validation unavailable: {str(e)}"
        
        # Build comprehensive context
        context = {
            # Basic chart
            "birth_details": {
                "date": birth_data.get('date'),
                "time": birth_data.get('time'),
                "place": birth_data.get('place', birth_data.get('name', 'Unknown')),
                "latitude": birth_data.get('latitude'),
                "longitude": birth_data.get('longitude')
            },
            
            # Validated ascendant information
            "ascendant_info": {
                "degree": ascendant_degree,
                "sign_number": ascendant_sign_num + 1,
                "sign_name": ascendant_sign_name,
                "exact_degree_in_sign": ascendant_degree % 30,
                "note": "This is the calculated Sidereal/Vedic ascendant using Swiss Ephemeris with Lahiri Ayanamsa",
                "validation": ascendant_validation_note,
                "formatted": f"{ascendant_sign_name} {ascendant_degree % 30:.2f}°"
            },
            
            "d1_chart": chart_data,
        }
        
        # Calculate divisional charts
        d9_chart = divisional_calc.calculate_divisional_chart(9)
        d10_chart = divisional_calc.calculate_divisional_chart(10)
        d12_chart = divisional_calc.calculate_divisional_chart(12)
        
        divisional_charts = {
            "d9_navamsa": d9_chart,
            "d10_dasamsa": d10_chart,
            "d12_dwadasamsa": d12_chart
        }
        
        # Update advanced calculators with divisional charts
        vargottama_calc = VargottamaCalculator(chart_data, divisional_charts)
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, divisional_charts)
        
        context.update({
            # Key divisional charts
            "divisional_charts": divisional_charts,
            
            # Planetary analysis
            "planetary_analysis": {},
            
            # Special points
            "special_points": {
                "badhaka_lord": badhaka_calc.get_badhaka_lord(int(chart_data['ascendant'] / 30))
            },
            
            # Relationships
            "relationships": {
                "argala_analysis": argala_calc.calculate_argala_analysis()
            },
            
            # Yogas
            "yogas": yoga_calc.calculate_all_yogas(),
            
            # Chara Karakas
            "chara_karakas": chara_karaka_calc.calculate_chara_karakas(),
            
            # Advanced Analysis
            "advanced_analysis": {
                "planetary_wars": planetary_war_calc.get_war_summary(),
                "vargottama_positions": vargottama_calc.get_vargottama_summary(),
                "neecha_bhanga": neecha_bhanga_calc.get_neecha_bhanga_summary(),
                "pancha_mahapurusha": pancha_mahapurusha_calc.get_pancha_mahapurusha_summary()
            }
        })
        
        # Add planetary analysis for all planets
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        for planet in planets:
            try:
                context["planetary_analysis"][planet] = planet_analyzer.analyze_planet(planet)
            except Exception as e:
                print(f"Error analyzing {planet}: {e}")
                continue
        
        return context
    
    def _build_dynamic_context(self, birth_data: Dict, user_question: str, target_date: Optional[datetime]) -> Dict[str, Any]:
        """Build dynamic context based on question and date"""
        
        context = {}
        
        # Always include current dashas
        dasha_calc = DashaCalculator()
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # Add specific date dashas if requested
        if target_date:
            context['target_date_dashas'] = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Add transit activations for timing questions
        if self._contains_timing_keywords(user_question):
            try:
                real_calc = RealTransitCalculator()
                aspects = real_calc.find_real_aspects(birth_data)
                
                # Calculate timeline for next 2 years
                current_year = datetime.now().year
                transit_activations = []
                
                for aspect in aspects[:10]:  # Limit to top 10 aspects for performance
                    timeline = real_calc.calculate_aspect_timeline(aspect, current_year, 2)
                    for period in timeline:
                        transit_activations.append({
                            **period,
                            'transit_planet': aspect['transit_planet'],
                            'natal_planet': aspect['natal_planet'],
                            'aspect_number': aspect['aspect_number']
                        })
                
                context['transit_activations'] = transit_activations
            except Exception as e:
                print(f"Error calculating transit activations: {e}")
                context['transit_activations'] = []
        
        return context
    
    def _contains_timing_keywords(self, question: str) -> bool:
        """Check if question contains timing-related keywords"""
        timing_keywords = [
            'when', 'timing', 'time', 'date', 'period', 'year', 'month',
            'future', 'upcoming', 'next', 'soon', 'later', 'eventually',
            'marriage', 'job', 'career', 'travel', 'move', 'change',
            'good time', 'bad time', 'auspicious', 'favorable'
        ]
        
        question_lower = question.lower()
        return any(keyword in question_lower for keyword in timing_keywords)
    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()