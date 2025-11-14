import sys
import os
import re
from typing import Dict, Any, Optional, List
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
from shared.dasha_calculator import DashaCalculator
from calculators.planetary_war_calculator import PlanetaryWarCalculator
from calculators.vargottama_calculator import VargottamaCalculator
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.pancha_mahapurusha_calculator import PanchaMahapurushaCalculator
from shared.dasha_calculator import DashaCalculator

class ChatContextBuilder:
    """Builds comprehensive astrological context for chat conversations"""
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
    
    def build_complete_context(self, birth_data: Dict, user_question: str = "", target_date: Optional[datetime] = None, requested_period: Optional[Dict] = None) -> Dict[str, Any]:
        """Build complete astrological context for chat"""
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        if birth_hash not in self.static_cache:
            self.static_cache[birth_hash] = self._build_static_context(birth_data)
        
        static_context = self.static_cache[birth_hash]
        
        # Add dynamic data
        dynamic_context = self._build_dynamic_context(birth_data, user_question, target_date, requested_period)
        
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
    
    def _build_dynamic_context(self, birth_data: Dict, user_question: str, target_date: Optional[datetime], requested_period: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dynamic context based on question and date"""
        
        context = {}
        
        # Always include current dashas
        dasha_calc = DashaCalculator()
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # Add specific date dashas if requested
        if target_date:
            context['target_date_dashas'] = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Add transit data availability info with precision methodology
        current_year = datetime.now().year
        context['transit_data_availability'] = {
            "current_period": f"{current_year}-{current_year + 2} (2 years)",
            "available_range": "1900-2100",
            "can_request": True,
            "request_format": "Include JSON in your response: {\"requestType\": \"transitRequest\", \"startYear\": 2027, \"endYear\": 2028, \"specificMonths\": [\"January\", \"February\", \"March\"]}",
            "note": "You can request specific periods for detailed timing analysis using JSON format",
            "precision_methodology": {
                "principle": "Events manifest with highest probability when dasha planets create the SAME relationships in transit as they had in natal chart",
                "technique": "Identify periods where: 1) Dasha planet transits and aspects/conjoins natal positions of planets it had natal relationships with, 2) Combine house significations of all involved planets (natal houses + lordships + transit houses), 3) Synthesize significations with native's current life context for specific event predictions",
                "example": "If Saturn (lord of 8th,9th, natal 2nd house) transits 2nd house aspecting natal Mercury (8th house, lord of 3rd,6th), combine significations: 2nd,3rd,6th,8th,9th houses = wealth,communication,health,transformation,dharma = possible events: financial transformation through communication/writing, health issues requiring medical expenses, inheritance matters, spiritual studies, etc.",
                "instruction": "MANDATORY: For ALL timing questions (when/best time/periods/dates), you MUST ONLY request transit data using JSON format. Do NOT provide a complete astrological analysis. Simply explain that transit data is needed and include the JSON request. The complete analysis will be provided after the transit data is calculated.",
                "critical_usage_rules": {
                    "transit_data_format": "Each transit_activation shows: transit_planet -> natal_planet (dates). This means the TRANSITING planet is aspecting/activating the NATAL planet.",
                    "do_not_assume": "NEVER assume transit house positions, aspects, or conjunctions. ONLY use the exact transit_activations provided.",
                    "correct_interpretation": "'Jupiter -> Mars (2027-01-01 to 2027-01-25)' means transiting Jupiter is activating natal Mars during this period. Do NOT assume Jupiter's house position or aspect type.",
                    "forbidden_calculations": "Do NOT calculate: 1) Transit house positions, 2) Aspect types (7th, 5th, 9th), 3) Conjunctions, 4) Transit degrees. Only use provided activation periods.",
                    "proper_usage": "Focus on: 1) Which natal planet is being activated, 2) The activation period dates, 3) Combine natal planet's significations with current dasha context for event prediction."
                }
            }
        }
        
        # Only calculate transit data if specifically requested by Gemini
        if requested_period:
            start_year = requested_period.get('start_year', current_year)
            end_year = requested_period.get('end_year', current_year + 2)
            year_range = end_year - start_year
            print(f"🎯 GEMINI REQUESTED TRANSIT PERIOD: {start_year}-{end_year} ({year_range} years)")
            
            try:
                real_calc = RealTransitCalculator()
                aspects = real_calc.find_real_aspects(birth_data)
                print(f"   Found {len(aspects)} potential aspects")
                
                transit_activations = []
                
                for i, aspect in enumerate(aspects):
                    print(f"   Processing aspect {i+1}/{len(aspects)}: {aspect['transit_planet']} -> {aspect['natal_planet']}")
                    print(f"     Aspect details: {aspect}")
                    try:
                        timeline = real_calc.calculate_aspect_timeline(aspect, start_year, year_range, birth_data)
                        print(f"     Timeline periods found: {len(timeline)}")
                        
                        for j, period in enumerate(timeline):
                            print(f"     Period {j+1}: {period['start_date']} to {period['end_date']}")
                            print(f"       Transit house: {period.get('transit_house')}, Natal house: {period.get('natal_house')}")
                            print(f"       Conjunct planets: {period.get('conjunct_natal_planets', [])}")
                            print(f"       All aspects cast: {len(period.get('all_aspects_cast', []))} aspects")
                            
                            # Log each aspect cast
                            for aspect_cast in period.get('all_aspects_cast', []):
                                print(f"         {aspect_cast['aspect_type']} -> House {aspect_cast['target_house']} (planets: {aspect_cast['target_planets']})")
                            
                            # Add dasha correlation for this transit period
                            start_date_obj = datetime.strptime(period['start_date'], '%Y-%m-%d')
                            end_date_obj = datetime.strptime(period['end_date'], '%Y-%m-%d')
                            
                            print(f"       Calculating dashas for {start_date_obj.strftime('%Y-%m-%d')} to {end_date_obj.strftime('%Y-%m-%d')}")
                            dasha_periods = dasha_calc.get_dasha_periods_for_range(
                                birth_data, start_date_obj, end_date_obj
                            )
                            print(f"       Dasha periods found: {len(dasha_periods)}")
                            
                            for k, dasha_period in enumerate(dasha_periods):
                                print(f"         Dasha {k+1}: {dasha_period['start_date']} to {dasha_period['end_date']}")
                                print(f"           Maha: {dasha_period['mahadasha']}, Antar: {dasha_period['antardasha']}, Pratyantar: {dasha_period['pratyantardasha']}")
                                print(f"           Sookshma: {dasha_period['sookshma']}, Prana: {dasha_period['prana']}")
                            
                            # Analyze dasha significance
                            significance = self._analyze_dasha_transit_significance(
                                aspect['transit_planet'], aspect['natal_planet'], dasha_periods
                            )
                            print(f"       Dasha significance: {significance}")
                            
                            transit_activations.append({
                                **period,
                                'transit_planet': aspect['transit_planet'],
                                'natal_planet': aspect['natal_planet'],
                                'aspect_number': aspect['aspect_number'],
                                'dasha_periods': dasha_periods,
                                'dasha_significance': significance
                            })
                    except Exception as aspect_error:
                        print(f"     ❌ Error calculating timeline: {aspect_error}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                context['transit_activations'] = transit_activations
                
                # Add critical usage instructions for transit data
                context['transit_usage_instructions'] = {
                    "critical_warning": "DO NOT assume transit house positions, aspects, or conjunctions. Use ONLY the provided transit_activations data.",
                    "data_format": "Each entry shows 'transit_planet -> natal_planet (dates)' meaning the transiting planet is activating the natal planet during those dates.",
                    "correct_approach": "1) Identify which natal planet is activated, 2) Use activation period dates, 3) Combine natal planet significations with dasha context for predictions.",
                    "forbidden": "Never calculate or assume: transit house positions, aspect types (7th/5th/9th), conjunctions, or transit degrees.",
                    "example": "'Jupiter -> Mars (2027-01-01 to 2027-01-25)' = Transiting Jupiter activates natal Mars from Jan 1-25, 2027. Focus on Mars significations (energy, action, siblings, property) being enhanced by Jupiter's benefic influence during this period."
                }
                
                # Log transit data being sent
                print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                print(f"   Period: {start_year}-{end_year}")
                print(f"   Total activations: {len(transit_activations)}")
                for i, activation in enumerate(transit_activations[:5]):
                    print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']})")
                if len(transit_activations) > 5:
                    print(f"     ... and {len(transit_activations) - 5} more")
                    
            except Exception as e:
                print(f"❌ Error calculating transit activations: {e}")
                context['transit_activations'] = []
        
        return context
    

    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def _analyze_dasha_transit_significance(self, transit_planet: str, natal_planet: str, dasha_periods: List[Dict]) -> str:
        """Analyze the significance of transit based on current dasha periods"""
        print(f"         Analyzing significance for {transit_planet} -> {natal_planet}")
        
        if not dasha_periods:
            print(f"         No dasha periods provided, returning moderate")
            return "moderate"
        
        max_significance = "moderate"
        
        # Check if transit planet or natal planet is in any dasha level
        for i, period in enumerate(dasha_periods):
            active_planets = [
                period.get('mahadasha'),
                period.get('antardasha'), 
                period.get('pratyantardasha'),
                period.get('sookshma'),
                period.get('prana')
            ]
            
            print(f"         Period {i+1} active planets: {active_planets}")
            
            transit_in_dasha = transit_planet in active_planets
            natal_in_dasha = natal_planet in active_planets
            
            print(f"         {transit_planet} in dasha: {transit_in_dasha}, {natal_planet} in dasha: {natal_in_dasha}")
            
            if transit_in_dasha and natal_in_dasha:
                print(f"         Both planets in dasha - MAXIMUM significance")
                max_significance = "maximum"
            elif transit_in_dasha or natal_in_dasha:
                if max_significance != "maximum":
                    print(f"         One planet in dasha - HIGH significance")
                    max_significance = "high"
        
        print(f"         Final significance: {max_significance}")
        return max_significance