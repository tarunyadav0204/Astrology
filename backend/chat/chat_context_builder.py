import sys
import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

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
from calculators.indu_lagna_calculator import InduLagnaCalculator
from shared.dasha_calculator import DashaCalculator
from calculators.kalachakra_dasha_calculator import KalachakraDashaCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from calculators.shoola_dasha_calculator import ShoolaDashaCalculator
from calculators.yogini_dasha_calculator import YoginiDashaCalculator
from calculators.kota_chakra_calculator import KotaChakraCalculator
from calculators.prashna_calculator import PrashnaCalculator
from calculators.varshphal_calculator import VarshphalCalculator
from calculators.chara_dasha_calculator import CharaDashaCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.jaimini_full_analyzer import JaiminiFullAnalyzer
from calculators.nadi_linkage_calculator import NadiLinkageCalculator
from calculators.pushkara_calculator import PushkaraCalculator
from calculators.sudarshana_chakra_calculator import SudarshanaChakraCalculator
from calculators.sudarshana_dasha_calculator import SudarshanaDashaCalculator
from calculators.nakshatra_remedy_calculator import NakshatraRemedyCalculator
from app.kp.services.chart_service import KPChartService

# Import modular system instruction config
from .system_instruction_config import (
    ORIGINAL_VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION,
    build_system_instruction
)

class ChatContextBuilder:
    """Builds comprehensive astrological context for chat conversations"""
    
    # Class-level constants
    NAKSHATRA_NAMES = [
        'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
        'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
        'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
        'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
        'Uttara Bhadrapada', 'Revati'
    ]
    
    def __init__(self):
        self.static_cache = {}  # Cache static chart data
        self.dynamic_cache = {}  # Cache dynamic context data
    
    def build_synastry_context(self, native_birth_data: Dict, partner_birth_data: Dict, user_question: str = "", intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dual-chart context for partnership/compatibility analysis"""
        return {
            'analysis_type': 'synastry',
            'native': self.build_complete_context(native_birth_data, user_question, None, None, intent_result),
            'partner': self.build_complete_context(partner_birth_data, user_question, None, None, intent_result)
        }
    
    def build_annual_context(self, birth_data: Dict, target_year: int, user_question: str = "", intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Builds context with BOTH Birth Chart (Base) and Varshphal (Overlay)."""
        # print(f"📅 Building Annual Context for Year: {target_year}")
        
        base_context = self.build_complete_context(birth_data, user_question, None, None, intent_result)
        
        chart_calc = ChartCalculator({})
        vp_calc = VarshphalCalculator(chart_calc)
        
        try:
            varshphal_data = vp_calc.calculate_varshphal(birth_data, target_year)
            
            base_context['analysis_type'] = 'annual_forecast'
            base_context['focus_year'] = target_year
            base_context['varshphal'] = {
                'muntha': varshphal_data['muntha'],
                'year_lord': varshphal_data['year_lord'],
                'mudda_dasha': varshphal_data['mudda_dasha']
            }
        except Exception as e:
            # print(f"❌ Varshphal calculation failed: {e}")
            base_context['analysis_error'] = f"Annual calculation failed: {str(e)}"
            
        return base_context
    
    def build_complete_context(self, birth_data: Dict, user_question: str = "", target_date: Optional[datetime] = None, requested_period: Optional[Dict] = None, intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build complete astrological context for chat"""
        import time
        import json
        
        context_start_time = time.time()
        # print(f"\n⏱️ CONTEXT PREPARATION STARTED")
        
        # Create birth hash for caching
        birth_hash = self._create_birth_hash(birth_data)
        
        # Get static data (cached)
        static_start_time = time.time()
        if birth_hash not in self.static_cache:
            # print(f"   📊 Building static context (not cached)...")
            self.static_cache[birth_hash] = self._build_static_context(birth_data)
        else:
            print(f"   ✅ Using cached static context")
        static_context = self.static_cache[birth_hash]
        static_time = time.time() - static_start_time
        # print(f"   Static context time: {static_time:.2f}s")
        
        # Dynamic Cache Key (birth_hash + current_date + requested_period + intent_result)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        period_str = json.dumps(requested_period, sort_keys=True) if requested_period else "none"
        intent_str = json.dumps(intent_result, sort_keys=True) if intent_result else "none"
        dynamic_cache_key = f"{birth_hash}_{current_date_str}_{period_str}_{intent_str}"
        
        # Check Dynamic Cache
        dynamic_start_time = time.time()
        if dynamic_cache_key not in self.dynamic_cache:
            # print(f"   🔄 Calculating fresh dynamic context...")
            self.dynamic_cache[dynamic_cache_key] = self._build_dynamic_context(birth_data, user_question, target_date, requested_period, intent_result)
        else:
            print(f"   ✅ Using cached dynamic context")
        
        dynamic_context = self.dynamic_cache[dynamic_cache_key]
        dynamic_time = time.time() - dynamic_start_time
        # print(f"   Dynamic context time: {dynamic_time:.2f}s")
        
        total_context_time = time.time() - context_start_time
        # print(f"⏱️ TOTAL CONTEXT PREPARATION TIME: {total_context_time:.2f}s")
        
        # Combine contexts and apply minification
        full_context = {
            **static_context,
            **dynamic_context,
            'intent': intent_result
        }
        
        # Enrich current_dashas with house and sign info for easy access
        current_dashas = full_context.get('current_dashas', {})
        d1_chart = full_context.get('d1_chart', {})
        d1_planets = d1_chart.get('planets', {})
        house_lordships = full_context.get('house_lordships', {})
        
        for level in ['mahadasha', 'antardasha', 'pratyantardasha']:
            dasha_info = current_dashas.get(level, {})
            lord = dasha_info.get('planet')
            if lord and lord in d1_planets:
                planet_data = d1_planets[lord]
                # Use house from d1_chart for consistency
                house = planet_data.get('house')
                sign_name = planet_data.get('sign_name', '')
                
                # Inject house and sign directly into dasha info
                dasha_info['house'] = house
                dasha_info['sign'] = sign_name
                
                # Add analysis hint with lordships
                ruled_houses = house_lordships.get(lord, [])
                dasha_info['analysis_hint'] = (
                    f"{lord} is in house {house} ({sign_name}). "
                    f"It rules houses {', '.join(map(str, ruled_houses))}."
                )
        
        full_context['current_dashas'] = current_dashas
        
        # Filter divisional charts based on intent router recommendations
        if intent_result and intent_result.get('divisional_charts'):
            requested_chart_codes = intent_result['divisional_charts']
            # print(f"🎯 Filtering divisional charts for Gemini: {requested_chart_codes}")
            
            # Map codes to chart names
            chart_name_mapping = {
                'D3': 'd3_drekkana', 'D4': 'd4_chaturthamsa', 'D7': 'd7_saptamsa',
                'D9': 'd9_navamsa', 'D10': 'd10_dasamsa', 'D12': 'd12_dwadasamsa',
                'D16': 'd16_shodasamsa', 'D20': 'd20_vimsamsa', 'D24': 'd24_chaturvimsamsa',
                'D27': 'd27_nakshatramsa', 'D30': 'd30_trimsamsa', 'D40': 'd40_khavedamsa',
                'D45': 'd45_akshavedamsa', 'D60': 'd60_shashtiamsa'
            }
            
            # Filter to only requested charts
            filtered_divisional_charts = {}
            all_charts = full_context.get('divisional_charts', {})
            
            for code in requested_chart_codes:
                chart_name = chart_name_mapping.get(code)
                if chart_name and chart_name in all_charts:
                    filtered_divisional_charts[chart_name] = all_charts[chart_name]
                    # print(f"   ✅ Including {code} ({chart_name})")
            
            # Always ensure D9 is included (required for analysis)
            if 'd9_navamsa' not in filtered_divisional_charts and 'd9_navamsa' in all_charts:
                filtered_divisional_charts['d9_navamsa'] = all_charts['d9_navamsa']
                # print(f"   ✅ Added mandatory D9 Navamsa")
            
            # Add Karkamsa/Swamsa if requested
            if 'Karkamsa' in requested_chart_codes or 'Swamsa' in requested_chart_codes:
                from calculators.jaimini_chart_calculator import JaiminiChartCalculator
                
                # Get Atmakaraka from context
                karaka_data = full_context.get('chara_karakas', {}).get('chara_karakas', {})
                atmakaraka_data = karaka_data.get('Atmakaraka', {})
                atmakaraka_planet = atmakaraka_data.get('planet')
                
                if atmakaraka_planet:
                    birth_hash = self._create_birth_hash(birth_data)
                    d1_chart = self.static_cache[birth_hash]['d1_chart']
                    
                    jaimini_calc = JaiminiChartCalculator(d1_chart, atmakaraka_planet)
                    
                    if 'Karkamsa' in requested_chart_codes:
                        karkamsa_result = jaimini_calc.calculate_karkamsa_chart()
                        filtered_divisional_charts['karkamsa'] = karkamsa_result
                        # print(f"   ✅ Added Karkamsa chart (D1 planets from D9 AK lagna)")
                    
                    if 'Swamsa' in requested_chart_codes:
                        swamsa_result = jaimini_calc.calculate_swamsa_chart()
                        filtered_divisional_charts['swamsa'] = swamsa_result
                        # print(f"   ✅ Added Swamsa chart (D9 planets from D9 AK lagna)")
            
            full_context['divisional_charts'] = filtered_divisional_charts
            # print(f"📊 Sending {len(filtered_divisional_charts)} divisional charts to Gemini")
        else:
            print(f"📊 No filtering - sending all {len(full_context.get('divisional_charts', {}))} divisional charts")
        
        # Apply minification before returning
        return self._minify_data(full_context)
    
    def _build_static_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build static chart context (cached per birth data)"""
        
        # Calculate birth chart using existing API endpoint logic
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        # DEBUG: Log what we're sending to calculate chart
        print(f"\n📤 [CHART CALCULATION INPUT]")
        print(f"Date: {birth_data.get('date')}")
        print(f"Time: {birth_data.get('time')}")
        print(f"Latitude: {birth_data.get('latitude')}")
        print(f"Longitude: {birth_data.get('longitude')}")
        print(f"Timezone: {birth_data.get('timezone', 'NOT PROVIDED')}")
        print(f"Place: {birth_data.get('place', 'NOT PROVIDED')}")
        
        chart_calc = ChartCalculator({})
        chart_data = chart_calc.calculate_chart(birth_obj)
        chart_data_original = chart_data  # Store original before enrichment
        
        # Initialize divisional calculator first so divisions are available for Shadbala
        divisional_calc = DivisionalChartCalculator(chart_data)
        chart_data['divisions'] = divisional_calc.calculate_all_divisional_charts()
        
        # Initialize analyzers
        planet_analyzer = PlanetAnalyzer(chart_data, birth_obj)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yogi_calc = YogiCalculator(chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        friendship_calc = FriendshipCalculator()
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        argala_calc = ArgalaCalculator(chart_data, birth_obj)
        
        # Initialize Ashtakavarga calculator
        from calculators.ashtakavarga import AshtakavargaCalculator
        ashtakavarga_calc = AshtakavargaCalculator(birth_data, chart_data)
        
        # Initialize Panchang calculator
        from calculators.panchang_calculator import PanchangCalculator
        panchang_calc = PanchangCalculator()
        panchang_calc.birth_data = birth_data
        
        # Advanced calculators
        planetary_war_calc = PlanetaryWarCalculator(chart_data)
        vargottama_calc = VargottamaCalculator(chart_data, {})
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, {})
        pancha_mahapurusha_calc = PanchaMahapurushaCalculator(chart_data)
        indu_lagna_calc = InduLagnaCalculator(chart_data)
        
        # Extract and validate ascendant information
        ascendant_degree = chart_data.get('ascendant', 0)
        
        # DEBUG: Log ascendant value
        print(f"\n🔍 [ASCENDANT DEBUG]")
        print(f"Raw ascendant from chart_data: {ascendant_degree}°")
        print(f"Birth data: {birth_data.get('date')} {birth_data.get('time')} at {birth_data.get('latitude')}, {birth_data.get('longitude')}")
        
        ascendant_sign_num = int(ascendant_degree / 30)
        ascendant_sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                               'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        ascendant_sign_name = ascendant_sign_names[ascendant_sign_num]
        
        print(f"Calculated sign: {ascendant_sign_name} (sign #{ascendant_sign_num})")
        print(f"Degree in sign: {ascendant_degree % 30:.2f}°")
        
        # Validate ascendant calculation
        try:
            from utils.chart_validator import validate_ascendant_calculation
            validation = validate_ascendant_calculation(birth_data, ascendant_degree)
            ascendant_validation_note = f"Validation: {'PASSED' if validation['is_valid'] else 'FAILED'} - Difference: {validation['difference_degrees']:.4f}°"
        except Exception as e:
            ascendant_validation_note = f"Validation unavailable: {str(e)}"
        
        # Build comprehensive context
        context = {
            # Basic chart
            "birth_details": {
                "name": birth_data.get('name'),
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
            
            "d1_chart": self._add_sign_names_to_chart_copy(chart_data)
        }
        
        # Calculate divisional charts with dignity analysis
        # Cache ALL standard charts to prevent stale cache issues when topics change
        requested_charts = [
            'D1', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 
            'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'
        ]
        # print(f"📊 Calculating ALL Divisional Charts for Cache (prevents topic-switch bugs)...")
        
        divisional_charts = {}
        
        # Calculate all divisional charts for robust caching
        for chart_code in requested_charts:
            if chart_code == 'D1':
                continue  # Already included as d1_chart
            
            try:
                chart_number = int(chart_code[1:])  # Extract number from D9, D10, etc.
                chart_data = divisional_calc.calculate_divisional_chart(chart_number)
                chart_data = self._add_sign_names_to_divisional_chart(chart_data)
                
                # Map to standard names
                chart_name_mapping = {
                    3: 'd3_drekkana',
                    4: 'd4_chaturthamsa', 
                    7: 'd7_saptamsa',
                    9: 'd9_navamsa',
                    10: 'd10_dasamsa',
                    12: 'd12_dwadasamsa',
                    16: 'd16_shodasamsa',
                    20: 'd20_vimsamsa',
                    24: 'd24_chaturvimsamsa',
                    27: 'd27_nakshatramsa',
                    30: 'd30_trimsamsa',
                    40: 'd40_khavedamsa',
                    45: 'd45_akshavedamsa',
                    60: 'd60_shashtiamsa'
                }
                
                chart_name = chart_name_mapping.get(chart_number, f'd{chart_number}')
                divisional_charts[chart_name] = chart_data
                # print(f"   ✅ Calculated {chart_code} ({chart_name})")
                
            except Exception as e:
                # print(f"   ❌ Failed to calculate {chart_code}: {e}")
                continue
        
        # CRITICAL FIX: Add divisions key to chart_data for Shadbala calculator
        # Include D1 from chart_data itself, then add other divisional charts
        divisions_data = {'D1': {p: {'sign': d.get('sign', 0), 'house': d.get('house', 1)} 
                                 for p, d in chart_data.get('planets', {}).items()}}
        divisions_data.update(self._convert_divisional_charts_to_divisions_format(divisional_charts))
        chart_data['divisions'] = divisions_data
        
        # Update advanced calculators with divisional charts
        vargottama_calc = VargottamaCalculator(chart_data, divisional_charts)
        neecha_bhanga_calc = NeechaBhangaCalculator(chart_data, divisional_charts)
        
        # Initialize D9 analyzer for separate analysis (use D9 from divisional_charts)
        d9_chart_for_analysis = divisional_charts.get('d9_navamsa')
        if d9_chart_for_analysis:
            d9_data_structure = d9_chart_for_analysis.get('divisional_chart', d9_chart_for_analysis)
            d9_planet_analyzer = PlanetAnalyzer(d9_data_structure, birth_obj)
        else:
            d9_planet_analyzer = None
        
        # Calculate Chara Karakas
        karaka_data = chara_karaka_calc.calculate_chara_karakas()
        
        # NOTE: Chara Dasha will be calculated in dynamic context with proper focus_date
        # We'll pass it to Jaimini analyzer from there
        chara_dasha_data = None
        
        # Calculate Jaimini Points
        # FIX: Extract the planet name string explicitly to prevent "unhashable type: dict" error
        atmakaraka_data = karaka_data['chara_karakas'].get('Atmakaraka', {})
        atmakaraka_planet = atmakaraka_data.get('planet')  # e.g., "Sun"
        
        # 1. Calculate Jaimini Points (static - doesn't depend on date)
        # Extract D9 chart data correctly to prevent structure mismatch
        d9_for_jaimini = divisional_charts['d9_navamsa'].get('divisional_chart', divisional_charts['d9_navamsa'])
        jaimini_calc = JaiminiPointCalculator(
            chart_data, 
            d9_for_jaimini, 
            atmakaraka_planet
        )
        jaimini_points = jaimini_calc.calculate_jaimini_points()
        
        # NOTE: Jaimini Full Analysis moved to dynamic context for focus_date sync
        
        # Calculate Nadi Links (use original chart_data before enrichment)
        try:
            nadi_calc = NadiLinkageCalculator(chart_data_original)
            nadi_links = nadi_calc.get_nadi_links()
            # print(f"   Nadi links calculated: {len(nadi_links)} planets")
            if not nadi_links:
                print(f"   ⚠️ Nadi links returned empty - check calculator")
        except Exception as e:
            # print(f"   ❌ Nadi calculation error: {e}")
            nadi_links = {}
        
        # Calculate Sudarshana Chakra (use original chart_data)
        try:
            sudarshana_calc = SudarshanaChakraCalculator(chart_data_original)
            sudarshana_data = sudarshana_calc.get_sudarshana_view()
            # print(f"   Sudarshana calculated: {len(sudarshana_data)} perspectives")
            if not sudarshana_data:
                print(f"   ⚠️ Sudarshana returned empty - check calculator")
        except Exception as e:
            # print(f"   ❌ Sudarshana calculation error: {e}")
            sudarshana_data = {}
        
        # Calculate Pushkara Navamsa (blessed degrees)
        try:
            pushkara_calc = PushkaraCalculator()
            pushkara_data = pushkara_calc.analyze_chart(chart_data_original, ascendant_sign_num)
        except Exception as e:
            pushkara_data = {'has_pushkara': False, 'pushkara_planets': []}
        
        # Calculate Planetary Friendship and Aspects
        try:
            friendship_data = friendship_calc.calculate_friendship(birth_data)
        except Exception as e:
            print(f"❌ Friendship calculation failed for chat context: {e}")
            friendship_data = {"error": "Friendship calculation unavailable"}
        
        # Calculate KP Chart Data
        try:
            kp_data = KPChartService.calculate_kp_chart(
                birth_data.get('date'),
                birth_data.get('time'),
                birth_data.get('latitude'),
                birth_data.get('longitude'),
                birth_data.get('timezone')
            )
            # Include all KP levels (Sign, Star, Sub, Sub-Sub) as calculations are now verified
            kp_analysis = {
                "planet_lords": kp_data.get('planet_lords', {}),
                "cusp_lords": kp_data.get('cusp_lords', {}),
                "significators": kp_data.get('significators', {})
            }
        except Exception as e:
            print(f"❌ KP calculation failed for chat context: {e}")
            kp_analysis = {"error": "KP calculation unavailable"}

        context.update({
            # KP Analysis (Full 4-level analysis)
            "kp_analysis": kp_analysis,
            
            # Planetary Friendship and Aspects
            "friendship_analysis": friendship_data,
            
            # Key divisional charts
            "divisional_charts": divisional_charts,
            
            # Jaimini Points (static)
            "jaimini_points": jaimini_points,
            
            # Chara Karakas (static)
            "chara_karakas": karaka_data,
            
            # NOTE: jaimini_full_analysis will be added in dynamic context
            
            # Nadi Links
            "nadi_links": nadi_links,
            
            # Sudarshana Chakra
            "sudarshana_chakra": sudarshana_data,
            
            # Pushkara Navamsa (blessed degrees)
            "pushkara_navamsa": pushkara_data,
            
            # Planetary analysis
            "planetary_analysis": {},  # D1 (Rashi)
            "d9_planetary_analysis": {},  # D9 (Navamsa)
            
            # Special points
            "special_points": {
                "badhaka_lord": badhaka_calc.get_badhaka_lord(int(chart_data.get('ascendant', 0) / 30))
            },
            
            # Relationships
            "relationships": {
                "argala_analysis": argala_calc.calculate_argala_analysis()
            },
            
            # Yogas
            "yogas": yoga_calc.calculate_all_yogas(),
            
            # Chara Karakas
            "chara_karakas": karaka_data,
            
            # Advanced Analysis (pruned for relevance)
            "advanced_analysis": self._prune_advanced_analysis({
                "planetary_wars": self._prune_planetary_wars(planetary_war_calc.get_war_summary()),
                "vargottama_positions": vargottama_calc.get_vargottama_summary(),
                "neecha_bhanga": self._prune_neecha_bhanga(neecha_bhanga_calc.get_neecha_bhanga_summary()),
                "pancha_mahapurusha": pancha_mahapurusha_calc.get_pancha_mahapurusha_summary()
            }),
            
            # Ashtakavarga Analysis
            "ashtakavarga": {
                "d1_rashi": {
                    "sarvashtakavarga": ashtakavarga_calc.calculate_sarvashtakavarga(),
                    "bhinnashtakavarga": {
                        planet: ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                    }
                },
                "d9_navamsa": self._calculate_d9_ashtakavarga(divisional_charts.get('d9_navamsa'), birth_data) if 'd9_navamsa' in divisional_charts else {}
            },
            
            # Birth Panchang
            "birth_panchang": panchang_calc.calculate_birth_panchang(birth_data),
            
            # Add InduLagna analysis to context
            **indu_lagna_calc.get_indu_lagna_analysis(),
            
            # Sniper Points (Critical for sudden events/health crises)
            "sniper_points": SniperPointsCalculator(
                context['d1_chart'],  # Use the enriched d1_chart from context
                divisional_charts.get('d3_drekkana', {}),
                divisional_charts.get('d9_navamsa', {})
            ).get_all_sniper_points(),
            
            # Nakshatra Remedies (Classical Upaya)
            "nakshatra_remedies": NakshatraRemedyCalculator().get_chart_remedies({})
        })
        
        # Add planetary analysis for both D1 and D9
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        
        for planet in planets:
            # D1 Analysis (existing)
            try:
                full_analysis = planet_analyzer.analyze_planet(planet)
                context["planetary_analysis"][planet] = self._filter_planetary_analysis(full_analysis, chart_calc)
            except Exception as e:
                continue
            
            # D9 Analysis (new)
            if d9_planet_analyzer:
                try:
                    d9_full = d9_planet_analyzer.analyze_planet(planet)
                    context["d9_planetary_analysis"][planet] = self._filter_planetary_analysis(d9_full, chart_calc)
                except Exception as e:
                    continue
        
        # Generate nakshatra remedies after planetary analysis is complete - OPTIMIZED
        context["nakshatra_remedies"] = self._prune_remedies_by_relevance(
            NakshatraRemedyCalculator().get_chart_remedies(context["planetary_analysis"]),
            context["planetary_analysis"],
            {}  # Pass empty dict instead of current_dashas since it's not available in static context
        )
        
        return context
    
    def _filter_planetary_analysis(self, full_analysis: Dict, chart_calc: ChartCalculator) -> Dict:
        """Filter planetary analysis to keep only raw data, remove text bloat and friendship matrix redundancy"""
        return {
            'basic_info': {
                'planet': full_analysis['basic_info']['planet'],
                'sign': full_analysis['basic_info']['sign'],
                'sign_name': full_analysis['basic_info'].get('sign_name'),
                'house': full_analysis['basic_info']['house'],
                'degree': full_analysis['basic_info']['degree'],
                'longitude': full_analysis['basic_info']['longitude'],
                'nakshatra': full_analysis['basic_info']['nakshatra'],
                'nakshatra_pada': self._get_nakshatra_pada(full_analysis['basic_info']['longitude']),
                'avastha': chart_calc.get_baladi_avastha(
                    full_analysis['basic_info']['planet'],
                    full_analysis['basic_info']['degree'],
                    full_analysis['basic_info']['sign']
                )
            },
            'dignity_analysis': {
                'dignity': full_analysis['dignity_analysis']['dignity'],
                'functional_nature': full_analysis['dignity_analysis']['functional_nature'],
                'strength_multiplier': full_analysis['dignity_analysis']['strength_multiplier']
            },
            'strength_analysis': {
                'shadbala_rupas': full_analysis['strength_analysis']['shadbala_rupas'],
                'shadbala_points': full_analysis['strength_analysis']['shadbala_points'],
                'shadbala_grade': full_analysis['strength_analysis']['shadbala_grade']
            },
            'house_position_analysis': {
                'house_number': full_analysis['house_position_analysis']['house_number'],
                'house_types': full_analysis['house_position_analysis']['house_types']
            },
            'conjunctions': {
                'has_conjunctions': full_analysis['conjunctions']['has_conjunctions'],
                'conjunction_count': full_analysis['conjunctions']['conjunction_count'],
                'conjunctions': [{
                    'planet': c['planet'],
                    'type': c['type'],
                    'orb': c['orb']
                } for c in full_analysis['conjunctions']['conjunctions']]
            },
            'combustion_status': {
                'is_combust': full_analysis['combustion_status']['is_combust'],
                'is_cazimi': full_analysis['combustion_status']['is_cazimi'],
                'status': full_analysis['combustion_status']['status']
            },
            'retrograde_analysis': {
                'is_retrograde': full_analysis['retrograde_analysis']['is_retrograde']
            },
            'aspects_received': {
                'has_aspects': full_analysis['aspects_received']['has_aspects'],
                'aspect_count': full_analysis['aspects_received']['aspect_count'],
                'aspects': [{
                    'aspecting_planet': a['aspecting_planet'],
                    'aspect_type': a['aspect_type'],
                    'effect_score': a.get('effect_score', 0)
                } for a in full_analysis['aspects_received']['aspects']]
            },
            'overall_assessment': {
                'overall_strength_score': full_analysis['overall_assessment']['overall_strength_score'],
                'classical_grade': full_analysis['overall_assessment']['classical_grade']
            }
            # Removed friendship_analysis - massive redundancy eliminated
        }
    
    def _build_dynamic_context(self, birth_data: Dict, user_question: str, target_date: Optional[datetime], requested_period: Optional[Dict] = None, intent_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Build dynamic context based on question and date"""
        
        context = {}
        
        # Always include current dashas
        dasha_calc = DashaCalculator()
        
        # DEBUG: Log what we're sending to dasha calculator from chat context
        print(f"\n💬 CHAT CONTEXT BUILDER DEBUG:")
        print(f"   Calling dasha_calc.calculate_current_dashas with:")
        print(f"   birth_data keys: {list(birth_data.keys())}")
        print(f"   Name: {birth_data.get('name', 'N/A')}")
        print(f"   Date: {birth_data.get('date', 'N/A')}")
        print(f"   Time: {birth_data.get('time', 'N/A')}")
        print(f"   Timezone: {birth_data.get('timezone', 'N/A')} (type: {type(birth_data.get('timezone'))})")
        print(f"   Lat/Lon: {birth_data.get('latitude', 'N/A')}, {birth_data.get('longitude', 'N/A')}")
        
        context['current_dashas'] = dasha_calc.calculate_current_dashas(birth_data)
        
        # Add Maraka analysis for relatives (both Mahadasha and Antardasha)
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        asc_sign = int(chart_data['ascendant'] / 30)
        
        relatives = {
            "Mother": (asc_sign + 3) % 12,        # 4th
            "Father": (asc_sign + 8) % 12,        # 9th
            "Spouse": (asc_sign + 6) % 12,        # 7th
            "First_Child": self._get_child_lagna(asc_sign, 1, method='bhavat_bhavam'),
            "Second_Child": self._get_child_lagna(asc_sign, 2, method='bhavat_bhavam'),
            "Third_Child": self._get_child_lagna(asc_sign, 3, method='bhavat_bhavam')
        }
        
        # Get BOTH Dasha Lords
        md_planet = context['current_dashas'].get('mahadasha', {}).get('planet')
        ad_planet = context['current_dashas'].get('antardasha', {}).get('planet')
        
        # Analyze Maraka Status for BOTH
        context['current_dashas']['maraka_analysis'] = {}
        
        if md_planet:
            context['current_dashas']['maraka_analysis']['mahadasha_lord'] = {}
            for rel_name, rel_lagna in relatives.items():
                status = self._check_relative_maraka(md_planet, rel_lagna, chart_data)
                context['current_dashas']['maraka_analysis']['mahadasha_lord'][rel_name] = status

        if ad_planet:
            context['current_dashas']['maraka_analysis']['antardasha_lord'] = {}
            for rel_name, rel_lagna in relatives.items():
                status = self._check_relative_maraka(ad_planet, rel_lagna, chart_data)
                context['current_dashas']['maraka_analysis']['antardasha_lord'][rel_name] = status
        
        # Add Kalchakra dasha
        kalchakra_calc = KalachakraDashaCalculator()
        context['kalchakra_dasha'] = kalchakra_calc.calculate_kalchakra_dasha(birth_data)
        
        # Add Shoola Dasha (Jaimini longevity system)
        shoola_calc = ShoolaDashaCalculator(chart_data)
        context['shoola_dasha'] = shoola_calc.calculate_shoola_dasha(birth_data)
        
        # Add Yogini Dasha
        yogini_calc = YoginiDashaCalculator()
        moon_lon = chart_data['planets']['Moon']['longitude']
        context['yogini_dasha'] = yogini_calc.calculate_current_yogini(birth_data, moon_lon, target_date)
        
        # Add Kota Chakra (Uttara Kalamrita fortress grid)
        try:
            kota_calc = KotaChakraCalculator(chart_data)
            kota_data = kota_calc.calculate()
            if kota_data and 'error' not in kota_data:
                context['kota_chakra'] = kota_data
                # print(f"✅ Kota Chakra calculated: {kota_data['protection_score']['status']}")
        except Exception as e:
            print(f"❌ Kota Chakra calculation failed: {e}")
        
        # Add Dasha Conflict Analysis
        context['dasha_conflicts'] = self._analyze_dasha_conflicts(
            context['current_dashas'], 
            context['yogini_dasha']
        )
        
        # Add Special Points Analysis (Gandanta, Yogi, Avayogi, Dagdha Rashi)
        from calculators.gandanta_calculator import GandantaCalculator
        from calculators.yogi_calculator import YogiCalculator
        
        yogi_calc = YogiCalculator(chart_data)
        gandanta_calc = GandantaCalculator(chart_data)
        
        context['special_points'] = {
            'yogi_points': yogi_calc.calculate_yogi_points(birth_data),
            'gandanta_analysis': gandanta_calc.calculate_gandanta_analysis()
        }
        
        # Add Sudarshana Dasha (Annual Clock with precision triggers)
        if intent_result and intent_result.get('needs_transits'):
            try:
                from datetime import datetime
                birth_hash = self._create_birth_hash(birth_data)
                chart_data = self.static_cache[birth_hash]['d1_chart']
                
                # Determine target year from intent
                target_year = datetime.now().year
                if intent_result.get('transit_request'):
                    target_year = intent_result['transit_request'].get('startYear', target_year)
                
                sudarshana_dasha_calc = SudarshanaDashaCalculator(chart_data, birth_data)
                context['sudarshana_dasha'] = sudarshana_dasha_calc.calculate_precision_triggers(target_year)
            except Exception as e:
                print(f"❌ Sudarshana Dasha calculation failed: {e}")
        
        # Add Varshphal if question is about a specific year
        if intent_result and intent_result.get('transit_request'):
            req = intent_result['transit_request']
            year = req.get('startYear') or req.get('start_year')
            if year:
                try:
                    chart_calc = ChartCalculator({})
                    vp_calc = VarshphalCalculator(chart_calc)
                    varshphal_data = vp_calc.calculate_varshphal(birth_data, int(year))
                    
                    # Extract muntha lord from sign
                    muntha_sign = varshphal_data['muntha']['sign']
                    sign_lords = {
                        1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon', 5: 'Sun', 6: 'Mercury',
                        7: 'Venus', 8: 'Mars', 9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter'
                    }
                    muntha_lord = sign_lords.get(muntha_sign, 'Unknown')
                    
                    context['varshphal'] = {
                        'muntha_house': varshphal_data['muntha']['house'],
                        'muntha_sign': muntha_sign,
                        'muntha_lord': muntha_lord,
                        'mudda_dasha': varshphal_data['mudda_dasha'],
                        'year_lord': varshphal_data['year_lord'],
                        'year': year
                    }
                    # print(f"✅ Varshphal calculated for year {year}")
                except Exception as e:
                    print(f"❌ Varshphal calculation failed: {e}")
        
        # Add Chara Dasha (Jaimini) with DYNAMIC TARGETING
        try:
            from datetime import datetime
            birth_hash = self._create_birth_hash(birth_data)
            chart_data = self.static_cache[birth_hash]['d1_chart']
            chara_calc = CharaDashaCalculator(chart_data)
            dob_dt = datetime.strptime(birth_data['date'], '%Y-%m-%d')
            
            # Calculate full sequence
            full_chara_data = chara_calc.calculate_dasha(dob_dt)
            
            # Determine focus date (PRIORITY ORDER)
            focus_date = datetime.now()
            
            # PRIORITY 1: Intent Router (User's explicit question: "How is 2028?")
            if intent_result and intent_result.get('transit_request'):
                req = intent_result['transit_request']
                year = req.get('startYear') or req.get('start_year')
                if year:
                    focus_date = datetime(int(year), 1, 1)
            
            # PRIORITY 2: Explicit Target Date (Backend override/Annual mode)
            elif target_date:
                focus_date = target_date
            
            # PRIORITY 3: Gemini Requested Period (Tool call/Drill-down)
            elif requested_period:
                year = requested_period.get('startYear') or requested_period.get('start_year')
                if year:
                    focus_date = datetime(int(year), 1, 1)
            
            # Filter periods to only relevant ones for the transit period
            filtered_periods = []
            if intent_result and intent_result.get('transit_request'):
                req = intent_result['transit_request']
                start_year = req.get('startYear') or req.get('start_year')
                end_year = req.get('endYear') or req.get('end_year')
                
                if start_year and end_year:
                    period_start = datetime(int(start_year), 1, 1)
                    period_end = datetime(int(end_year), 12, 31)
                    
                    for period in full_chara_data['periods']:
                        p_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
                        p_end = datetime.strptime(period['end_date'], "%Y-%m-%d")
                        
                        # Include period if it overlaps with transit period
                        if p_start <= period_end and p_end >= period_start:
                            # Update is_current flag based on focus date
                            period['is_current'] = p_start <= focus_date < p_end
                            if period['is_current']:
                                period['note'] = "ACTIVE PERIOD for User Question"
                            filtered_periods.append(period)
                else:
                    # Fallback to current period only
                    for period in full_chara_data['periods']:
                        p_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
                        p_end = datetime.strptime(period['end_date'], "%Y-%m-%d")
                        period['is_current'] = p_start <= focus_date < p_end
                        if period['is_current']:
                            period['note'] = "ACTIVE PERIOD for User Question"
                            filtered_periods.append(period)
                            break
            else:
                # No specific transit request - include current period only
                for period in full_chara_data['periods']:
                    p_start = datetime.strptime(period['start_date'], "%Y-%m-%d")
                    p_end = datetime.strptime(period['end_date'], "%Y-%m-%d")
                    period['is_current'] = p_start <= focus_date < p_end
                    if period['is_current']:
                        period['note'] = "ACTIVE PERIOD for User Question"
                        filtered_periods.append(period)
                        break
            
            # Create filtered chara dasha data
            context['chara_dasha'] = {
                'calculation_method': full_chara_data.get('calculation_method', 'Standard'),
                'periods': filtered_periods,
                'note': f'Filtered to {len(filtered_periods)} relevant periods for transit analysis'
            }
            
            # Update Jaimini Full Analysis with the correct chara_dasha
            try:
                birth_hash = self._create_birth_hash(birth_data)
                static_data = self.static_cache[birth_hash]
                karaka_data = static_data.get('chara_karakas', {})
                jaimini_points = static_data.get('jaimini_points', {})
                
                # Recalculate Jaimini analyzer with the focus_date chara_dasha
                jaimini_analyzer = JaiminiFullAnalyzer(chart_data, karaka_data, jaimini_points, full_chara_data)
                context['jaimini_full_analysis'] = jaimini_analyzer.get_jaimini_report()
                # print(f"✅ Jaimini Full Analysis updated with focus_date Chara Dasha")
            except Exception as e:
                print(f"❌ Jaimini analyzer update failed: {e}")
        except Exception as e:
            print(f"Chara Dasha calculation error: {e}")
        
        # Add specific date dashas if requested
        if target_date:
            context['target_date_dashas'] = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Add house lordship mapping
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        context['house_lordships'] = self._get_house_lordships(ascendant_sign)
        

        
        # Add 5-year macro transit timeline for slow-moving planets
        try:
            real_calc = RealTransitCalculator()
            macro_transits = real_calc.get_slow_planet_transits(birth_data, years=5)
            context['macro_transits_timeline'] = macro_transits
            
            total_periods = sum(len(periods) for periods in macro_transits.values())
            # print(f"✅ Macro transits timeline: {total_periods} periods for 5 years")
            
            # Print detailed breakdown
            # print(f"\n📊 MACRO TRANSITS TIMELINE (5 YEARS):")
            for planet, periods in macro_transits.items():
                # print(f"\n{planet.upper()} ({len(periods)} periods):")
                for i, period in enumerate(periods[:3], 1):  # Show first 3 periods
                    retro_flag = " [RETROGRADE RETURN]" if period.get('retrograde_return') else ""
                    # print(f"  {i}. {period['start_date']} to {period['end_date']}")
                    # print(f"     Sign: {period['sign']} | House: {period['house']} | Segment: {period['segment']}{retro_flag}")
                if len(periods) > 3:
                    print(f"  ... and {len(periods) - 3} more periods")
            # print()
            
        except Exception as e:
            # print(f"❌ Macro transits calculation failed: {e}")
            context['macro_transits_timeline'] = {}
        
        # Add Navatara (Tara Bala) filtering for transit analysis
        try:
            from calculators.navatara_calculator import NavataraCalculator
            
            # Get Moon's birth nakshatra from planetary analysis
            birth_hash = self._create_birth_hash(birth_data)
            planetary_analysis = self.static_cache[birth_hash].get('planetary_analysis', {})
            moon_data = planetary_analysis.get('Moon', {})
            moon_nakshatra = moon_data.get('basic_info', {}).get('nakshatra')
            
            print(f"\n🌙 NAVATARA DEBUG:")
            print(f"   Moon nakshatra from planetary_analysis: {moon_nakshatra}")
            
            # Get nakshatra number (0-26)
            moon_nakshatra_number = None
            if moon_nakshatra:
                try:
                    moon_nakshatra_number = self.NAKSHATRA_NAMES.index(moon_nakshatra)
                    print(f"   Moon nakshatra number: {moon_nakshatra_number}")
                except ValueError:
                    print(f"   ❌ Moon nakshatra '{moon_nakshatra}' not found in NAKSHATRA_NAMES")
            else:
                print(f"   ❌ Moon nakshatra is None or empty")
            
            if moon_nakshatra_number is not None and 'macro_transits_timeline' in context:
                navatara_calc = NavataraCalculator(moon_nakshatra_number)
                print(f"   ✅ NavataraCalculator initialized with Moon nakshatra {moon_nakshatra_number}")
                
                # Analyze each transit planet's nakshatra position
                navatara_warnings = {}
                for planet, periods in context['macro_transits_timeline'].items():
                    if periods and len(periods) > 0:
                        # Get current/first period's nakshatra
                        current_period = periods[0]
                        transit_nakshatra_number = current_period.get('nakshatra_number')
                        transit_nakshatra_name = current_period.get('nakshatra', 'Unknown')
                        
                        print(f"   {planet}: transit_nakshatra_number={transit_nakshatra_number}, name={transit_nakshatra_name}")
                        
                        if transit_nakshatra_number is not None:
                            tara_info = navatara_calc.calculate_tara(transit_nakshatra_number)
                            print(f"      Tara: {tara_info['name']} (effect: {tara_info['effect']})")
                            
                            if tara_info['effect'] == 'bad':
                                navatara_warnings[planet] = {
                                    'tara': tara_info['name'],
                                    'tara_number': tara_info['number'],
                                    'effect': tara_info['description'],
                                    'transit_nakshatra': transit_nakshatra_name,
                                    'birth_moon_nakshatra': moon_nakshatra,
                                    'warning': f"Karmic Obstacle: {planet} in {tara_info['name']} Tara",
                                    'mandatory_statement': f"{planet} is transiting in {transit_nakshatra_name}, which is your {tara_info['name']} Tara from your birth Moon in {moon_nakshatra}. This creates {tara_info['description'].lower()}."
                                }
                                print(f"      ⚠️ MALEFIC TARA DETECTED: {planet} in {tara_info['name']}")
                        else:
                            print(f"      ⚠️ transit_nakshatra_number is None")
                
                context['navatara_warnings'] = navatara_warnings
                print(f"   ✅ Navatara analysis complete: {len(navatara_warnings)} malefic positions detected")
                print(f"   navatara_warnings: {navatara_warnings}")
            else:
                print(f"   ❌ Skipping Navatara: moon_nakshatra_number={moon_nakshatra_number}, has_macro_transits={'macro_transits_timeline' in context}")
                context['navatara_warnings'] = {}
        except Exception as e:
            print(f"❌ Navatara calculation failed: {e}")
            import traceback
            traceback.print_exc()
            context['navatara_warnings'] = {}
        
        # Add Progressive Nadi Age Activation
        try:
            dob = datetime.strptime(birth_data['date'], '%Y-%m-%d')
            current_age = datetime.now().year - dob.year
            
            # Comprehensive Nadi Age Activation Map
            nadi_age_map = {
                16: 'Rohini', 24: 'Pushya', 30: 'Swati', 36: ['Rohini', 'Pushya'],
                45: 'Magha', 46: ['Magha', 'Swati'], 65: 'Pushya', 69: 'Swati', 83: 'Rohini'
            }
            
            activated_stars = nadi_age_map.get(current_age)
            if activated_stars:
                if not isinstance(activated_stars, list):
                    activated_stars = [activated_stars]
                
                # Get planetary analysis to find planets in activated nakshatras
                birth_hash = self._create_birth_hash(birth_data)
                planetary_analysis = self.static_cache[birth_hash].get('planetary_analysis', {})
                
                activated_planets = []
                for planet, data in planetary_analysis.items():
                    planet_nakshatra = data.get('basic_info', {}).get('nakshatra')
                    if planet_nakshatra in activated_stars:
                        house = data.get('basic_info', {}).get('house')
                        activated_planets.append({
                            'planet': planet,
                            'nakshatra': planet_nakshatra,
                            'house': house
                        })
                
                context['nadi_age_activation'] = {
                    'age': current_age,
                    'activated_nakshatras': activated_stars,
                    'activated_planets': activated_planets,
                    'instruction': f"NADI AGE TRIGGER: Age {current_age} activates {', '.join(activated_stars)} nakshatra(s). Planets in these nakshatras MUST manifest their karma this year."
                }
        except Exception as e:
            # print(f"❌ Nadi age activation failed: {e}")
            context['nadi_age_activation'] = None
        
        # Add transit data availability info with enhanced methodology
        current_year = datetime.now().year
        context['transit_data_availability'] = {
            "current_period": f"{current_year}-{current_year + 2} (2 years)",
            "available_range": "1900-2100",
            "can_request": True,
            "request_format": "Include JSON in your response: {\"requestType\": \"transitRequest\", \"startYear\": 2027, \"endYear\": 2028, \"specificMonths\": [\"January\", \"February\", \"March\"], \"detailed_dashas\": true}",
            "note": "You can request specific periods for detailed timing analysis using JSON format. Set detailed_dashas: true for Sookshma/Prana levels in short-term analysis",
            "comprehensive_analysis_methodology": {
                "principle": "Events manifest when dasha planets recreate natal relationships through transits, activating ALL connected house significations",
                "dasha_priority_system": {
                    "short_term_analysis": "For daily/weekly/monthly questions, PRIORITIZE period_dasha_activations over general transit_activations. Use dasha planet transit positions as primary timing indicators.",
                    "probability_weighting": "Use the probability field from period_dasha_activations to weight predictions: very_high (90%+) = definite events, high (60-80%) = likely events, medium (40-60%) = possible events, low (<40%) = background influences.",
                    "connection_significance": "Maximum strength connections (conjunctions) = major life events, High strength (same nakshatra) = significant developments, Medium strength (aspects) = moderate influences, None = subtle background effects."
                },
                "mandatory_analysis_steps": [
                    "1. CHECK: If period_dasha_activations exists, analyze it FIRST before transit_activations",
                    "2. MANDATORY: Use ALL 5 dasha levels (Mahadasha through Prana) from period_dasha_activations for daily, or any short period predictions",
                    "3. For each dasha planet activation, identify ALL activated_houses from the data",
                    "4. MANDATORY: Reference specific transit planet positions and aspects from transit_activations data",
                    "5. Apply probability weighting: prioritize very_high and high probability activations",
                    "6. Check connection types: conjunctions and same_nakshatra create strongest events",
                    "7. Predict SPECIFIC events by combining activated house meanings",
                    "8. Use exact dates from the period_dasha_activations for precise timing",
                    "9. CRITICAL: Mention Sookshma and Prana dasha lords by name in Parashari View section"
                ],
                "critical_transit_rules": {
                    "exit_rule": "CRITICAL TRANSIT RULE: If a Dasha Lord flagged as a 'Maraka' transits the 12th House (House of Exit) relative to the person, interpret this as 'Departure', 'Final Release', or 'End of Life Cycle', not just financial loss. This is often the trigger for death.",
                    "dasha_chhidra_rule": "TIMING RULE: If a malefic Antardasha (e.g., Mars-Rahu) is ending within 1-2 months, prioritize this 'Dasha Transition Period' as the most likely time for a critical event, even if later transits look stronger. The end of a malefic period is a classic trigger.",
                    "trigger_planet_rule": "TRIGGER RULE: In a Maraka period, the event often manifests when the Sun or Mars transits the 12th, 8th, or 1st house. Check the monthly transit data for these specific triggers."
                },
                "example_analysis": "DASHA ACTIVATION EXAMPLE: Sookshma Mercury (very_high probability) activates houses [1,4,7,10] through conjunction connection on Feb 2nd. House synthesis: 1st+10th = personal career breakthrough, 4th+7th = home-related partnership decision, 1st+4th = personal property matter. Specific events: Job interview success, property purchase discussion with spouse, home office setup for new role.",
                "quick_answer_requirements": {
                    "must_include": "4-6 SPECIFIC life events with exact dates from transit periods - predict MORE events by combining house meanings",
                    "event_examples": "Property purchase opportunity, job promotion, relationship milestone, health checkup needed, father's travel for medical treatment, children's achievement ceremony, financial gain through work, legal matter resolution, vehicle purchase, educational course enrollment, long distance travel for work, family medical expenses, etc.",
                    "avoid_generic_terms": "Do NOT use vague terms like 'good period', 'challenges', 'growth'. Use specific event predictions.",
                    "house_synthesis_mandatory": "MUST combine multiple house meanings: 2nd+10th = career income, 4th+7th = home with spouse, 6th+9th = father's health + long travel = father's medical travel, 5th+12th = children's expenses, 3rd+9th = communication with father/mentor, 1st+6th = personal health from work, 6th+9th = service-related long travel, health issues requiring travel, father's work problems, etc.",
                    "comprehensive_event_prediction": "For each transit, predict events from ALL house combinations, not just obvious ones. Example: 6th+9th houses = father's health issues, father's work problems, long travel for medical treatment, legal issues with father, father's service to others, health expenses, work-related travel, educational travel, spiritual journey for healing, etc.",
                    "laymen_summary_mandatory": {
                        "purpose": "Quick Answer section MUST provide a clear, simple summary for non-astrologers",
                        "format": "Write as if explaining to someone who knows nothing about astrology",
                        "requirements": [
                            "Start with: 'Based on your birth chart and upcoming planetary movements:'",
                            "List 2-3 specific life events with exact date ranges",
                            "Place Key Insights section IMMEDIATELY after Quick Answer section",
                            "Use proper markdown: ## Key Insights (with double newline before content)",
                            "Format Key Insights as: ## Key Insights\n\n• Point 1\n• Point 2\n• Point 3"
                            "Explain WHY these events are likely (in simple terms)",
                            "End with: 'These predictions are based on the detailed astrological analysis below.'"
                        ],
                        "example_format": "Based on your birth chart and upcoming planetary movements: Between Jan 15-Mar 20, 2025, you're likely to have a property purchase opportunity through career advancement, as your career planet activates your wealth sector. From Feb 5-25, 2025, expect father's health to need attention with possible travel for treatment, creating family expenses. These predictions are based on the detailed astrological analysis below.",
                        "forbidden_in_summary": [
                            "Astrological jargon (houses, aspects, dashas, transits)",
                            "Planet names without context",
                            "Technical terms like 'benefic', 'malefic', 'conjunction'",
                            "Philosophical or spiritual language"
                        ],
                        "required_language": "Use everyday language: 'career opportunities', 'family matters', 'health concerns', 'financial gains', 'relationship changes', 'property matters', 'travel plans', etc."
                    },

                },
                "instruction": "MANDATORY: For short-term questions (daily/weekly/monthly), PRIORITIZE period_dasha_activations data over transit_activations. Use dasha planet positions, connections, and probability weights as primary prediction sources. For longer periods, use both systems together. RESPONSE MUST HAVE EXACTLY 6 MAIN SECTIONS IN THIS ORDER: 1) Quick Answer paragraph 2) ## Key Insights 3) ## Astrological Analysis (with sub-sections) 4) ## Nakshatra Insights 5) ## Timing & Guidance 6) ## Final Thoughts. Use standard markdown formatting only.",

            }
        }
        
        # Add period-specific dasha activations for short-term questions
        if intent_result and intent_result.get('transit_request'):
            req = intent_result['transit_request']
            start_year = req.get('startYear', current_year)
            end_year = req.get('endYear', current_year)

            # FIX: Ensure years are integers, as they can come from JSON as strings
            start_year = int(start_year)
            end_year = int(end_year)
            
            # Check if this is a short-term request (daily/weekly/monthly)
            if start_year == end_year:
                year_months = req.get('yearMonthMap', {}).get(str(start_year), [])
                if len(year_months) <= 3:  # 3 months or less
                    # Calculate specific date range
                    if len(year_months) == 1:
                        # Single month - use entire month
                        month_num = {
                            'January': 1, 'February': 2, 'March': 3, 'April': 4,
                            'May': 5, 'June': 6, 'July': 7, 'August': 8,
                            'September': 9, 'October': 10, 'November': 11, 'December': 12
                        }.get(year_months[0], 1)
                        
                        start_date = datetime(start_year, month_num, 1)
                        if month_num == 12:
                            end_date = datetime(start_year + 1, 1, 1) - timedelta(days=1)
                        else:
                            end_date = datetime(start_year, month_num + 1, 1) - timedelta(days=1)
                    else:
                        # Multiple months - use range
                        first_month = None
                        if len(year_months) > 0:
                            first_month = year_months[0]
                            last_month = year_months[-1]
                        
                        if not first_month:
                            # Fallback if no months specified
                            start_date = datetime(start_year, 1, 1)
                            end_date = datetime(start_year, 12, 31)
                        else:
                            first_month_num = {
                                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                'September': 9, 'October': 10, 'November': 11, 'December': 12
                            }.get(first_month, 1)
                            
                            last_month_num = {
                                'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                'September': 9, 'October': 10, 'November': 11, 'December': 12
                            }.get(last_month, 12)
                            
                            start_date = datetime(start_year, first_month_num, 1)
                            if last_month_num == 12:
                                end_date = datetime(start_year + 1, 1, 1) - timedelta(days=1)
                            else:
                                end_date = datetime(start_year, last_month_num + 1, 1) - timedelta(days=1)                    
                    # Calculate period-specific dasha activations
                    try:
                        period_activations = self._calculate_period_dasha_activations(start_date, end_date, birth_data)
                        context['period_dasha_activations'] = period_activations
                        print(f"✅ Period dasha activations calculated for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
                        print(f"🔍 DEBUG: period_dasha_activations keys: {list(period_activations.keys()) if period_activations else 'None'}")
                        if period_activations and 'dasha_activations' in period_activations:
                            print(f"🔍 DEBUG: Found {len(period_activations['dasha_activations'])} dasha activations")
                            for i, activation in enumerate(period_activations['dasha_activations'][:2]):
                                print(f"🔍 DEBUG: Activation {i+1}: {activation.get('planet')} {activation.get('dasha_level')} - probability: {activation.get('probability')}")
                    except Exception as e:
                        print(f"❌ Period dasha activation failed: {e}")
        
        # Calculate transit data if requested by Intent Router or Gemini
        transit_request = None
        # print(f"\n🔍 TRANSIT REQUEST DEBUG:")
        # print(f"   intent_result type: {type(intent_result)}")
        # print(f"   intent_result exists: {intent_result is not None}")
        # print(f"   intent_result value: {intent_result}")
        if intent_result:
            # print(f"   needs_transits: {intent_result.get('needs_transits')}")
            # print(f"   transit_request exists: {'transit_request' in intent_result}")
            if 'transit_request' in intent_result:
                print(f"   transit_request: {intent_result['transit_request']}")
        # print(f"   requested_period: {requested_period}")
        
        if intent_result and intent_result.get('needs_transits') and intent_result.get('transit_request'):
            transit_request = intent_result['transit_request']
            # print(f"\n🎯 INTENT ROUTER REQUESTED TRANSITS: {transit_request['startYear']}-{transit_request['endYear']}")
        elif requested_period:
            transit_request = requested_period
            # print(f"\n🎯 GEMINI REQUESTED TRANSITS: {requested_period}")
        else:
            print(f"\n❌ NO TRANSIT REQUEST DETECTED - intent_result: {intent_result}, requested_period: {requested_period}")
        
        
        # print(f"\n🎯 FINAL TRANSIT REQUEST: {transit_request}")
        if transit_request:
            import time
            transit_start_time = time.time()
            
            # Handle both formats: Intent Router uses 'startYear', old format uses 'start_year'
            start_year = int(transit_request.get('startYear') or transit_request.get('start_year', current_year))
            end_year = int(transit_request.get('endYear') or transit_request.get('end_year', current_year + 2))
            year_range = end_year - start_year
            # print(f"\n🎯 TRANSIT PERIOD: {start_year}-{end_year} ({year_range} years)")
            # print(f"⏱️ TRANSIT CALCULATION STARTED")
            
            # Get static context for ashtakavarga data
            birth_hash = self._create_birth_hash(birth_data)
            static_context = self.static_cache.get(birth_hash, {})
            
            try:
                init_start = time.time()
                # print(f"📊 Initializing RealTransitCalculator...")
                real_calc = RealTransitCalculator()
                init_time = time.time() - init_start
                # print(f"   Initialization time: {init_time:.2f}s")
                
                aspects_start = time.time()
                # print(f"🔍 Finding real aspects for birth data...")
                all_aspects = real_calc.find_real_aspects(birth_data)
                
                # Extract month filtering from intent router request
                requested_months = None
                if transit_request.get('yearMonthMap'):
                    year_month_map = transit_request['yearMonthMap']
                    # For long periods, combine all requested months into a unique set
                    # This allows filtering if Gemini requested specific months across different years
                    all_requested_months = set()
                    for year_str, months in year_month_map.items():
                        if months:
                            all_requested_months.update(months)
                    
                    if all_requested_months:
                        requested_months = list(all_requested_months)
                        # print(f"   📅 MONTH FILTERING: Including months {requested_months} across all years")
                
                # Include Mars for short-term analysis (daily/weekly/monthly)
                if requested_months and len(requested_months) <= 3:
                    # For short-term analysis, include Mars
                    major_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
                else:
                    # For longer periods, exclude Mars to reduce compute load
                    major_planets = ['Jupiter', 'Saturn', 'Rahu', 'Ketu', 'Mars']
                aspects = [a for a in all_aspects if a['transit_planet'] in major_planets]
                
                aspects_time = time.time() - aspects_start
                # print(f"   Found {len(all_aspects)} total aspects, filtered to {len(aspects)} major aspects in {aspects_time:.2f}s")
                # print(f"   Optimization: Skipped fast movers (Sun, Moon, Mercury, Venus) to reduce compute load")
                
                transit_activations = []
                
                for i, aspect in enumerate(aspects):
                    # print(f"   Processing aspect {i+1}/{len(aspects)}: {aspect['transit_planet']} -> {aspect['natal_planet']}")
                    # print(f"     Aspect details: {aspect}")
                    try:
                        timeline = real_calc.calculate_aspect_timeline(aspect, start_year, year_range, birth_data)
                        # print(f"     Timeline periods found: {len(timeline)} for {aspect['transit_planet']}->{aspect['natal_planet']} aspect {aspect['aspect_number']}")
                        
                        # Apply month filtering if requested
                        if requested_months:
                            filtered_timeline = []
                            for period in timeline:
                                start_date = datetime.strptime(period['start_date'], '%Y-%m-%d')
                                end_date = datetime.strptime(period['end_date'], '%Y-%m-%d')
                                
                                # Check if period overlaps with requested months
                                period_overlaps = False
                                for month_name in requested_months:
                                    month_num = {
                                        'January': 1, 'February': 2, 'March': 3, 'April': 4,
                                        'May': 5, 'June': 6, 'July': 7, 'August': 8,
                                        'September': 9, 'October': 10, 'November': 11, 'December': 12
                                    }.get(month_name)
                                    
                                    if month_num:
                                        # Check if period overlaps with this month in ANY year of the range
                                        # We check if the month_num is present in any year between start_date and end_date
                                        current_p_year = start_date.year
                                        while current_p_year <= end_date.year:
                                            month_start = datetime(current_p_year, month_num, 1)
                                            if month_num == 12:
                                                month_end = datetime(current_p_year + 1, 1, 1) - timedelta(days=1)
                                            else:
                                                month_end = datetime(current_p_year, month_num + 1, 1) - timedelta(days=1)
                                            
                                            if start_date <= month_end and end_date >= month_start:
                                                period_overlaps = True
                                                break
                                            current_p_year += 1
                                        
                                        if period_overlaps:
                                            break
                                
                                if period_overlaps:
                                    filtered_timeline.append(period)
                            
                            timeline = filtered_timeline
                            # print(f"     Filtered to {len(timeline)} periods overlapping with {requested_months}")
                        
                        for j, period in enumerate(timeline):
                            # print(f"     Period {j+1}: {period['start_date']} to {period['end_date']}")
                            # print(f"       Transit house: {period.get('transit_house')}, Natal house: {period.get('natal_house')}")
                            # print(f"       Conjunct planets: {period.get('conjunct_natal_planets', [])}")
                            # print(f"       All aspects cast: {len(period.get('all_aspects_cast', []))} aspects")
                            
                            # Log each aspect cast
                            for aspect_cast in period.get('all_aspects_cast', []):
                                # print(f"         {aspect_cast['aspect_type']} -> House {aspect_cast['target_house']} (planets: {aspect_cast['target_planets']})")
                                pass
                            
                            # Add dasha correlation for this transit period
                            start_date_obj = datetime.strptime(period['start_date'], '%Y-%m-%d')
                            end_date_obj = datetime.strptime(period['end_date'], '%Y-%m-%d')
                            
                            # Get all 5 Vimshottari dasha levels for this period
                            dasha_periods = dasha_calc.get_dasha_periods_for_range(
                                birth_data, start_date_obj, end_date_obj
                            )
                            
                            # Get Chara Dasha periods for this range - use existing context data
                            chara_periods_for_range = []
                            try:
                                # Use the Chara Dasha data already calculated in the context
                                existing_chara = context.get('chara_dasha', {}).get('periods', [])
                                for chara_period in existing_chara:
                                    p_start = datetime.strptime(chara_period['start_date'], "%Y-%m-%d")
                                    p_end = datetime.strptime(chara_period['end_date'], "%Y-%m-%d")
                                    
                                    # Check if chara period overlaps with transit period
                                    if (p_start <= end_date_obj and p_end >= start_date_obj):
                                        # Find the AD that covers the start of transit period
                                        ad_sign_name = chara_period.get('sign_name', 'Unknown')  # Default to MD
                                        antardashas = chara_period.get('antardashas', [])
                                        
                                        if antardashas:
                                            for ad in antardashas:
                                                ad_start = datetime.strptime(ad['start_date'], "%Y-%m-%d")
                                                ad_end = datetime.strptime(ad['end_date'], "%Y-%m-%d")
                                                if ad_start <= start_date_obj < ad_end:
                                                    ad_sign_name = ad.get('sign_name', 'Unknown')
                                                    break
                                        chara_periods_for_range.append({
                                            'mahadasha_sign': chara_period.get('sign_name', 'Unknown'),
                                            'antardasha_sign': ad_sign_name,
                                            'start_date': chara_period['start_date'],
                                            'end_date': chara_period['end_date'],
                                            'is_active': chara_period.get('is_current', False)
                                        })
                            except Exception as e:
                                print(f"DEBUG: Chara transit loop error: {e}")
                            
                            # Get Yogini Dasha periods for this range - calculate for specific transit period
                            yogini_periods_for_range = []
                            try:
                                yogini_calc = YoginiDashaCalculator()
                                moon_lon = chart_data['planets']['Moon']['longitude']
                                
                                # Calculate Yogini dasha for the specific transit start date
                                transit_yogini = yogini_calc.calculate_current_yogini(birth_data, moon_lon, start_date_obj)
                                if transit_yogini and 'antardasha' in transit_yogini:
                                    y_info = {
                                        'mahadasha': transit_yogini['mahadasha'].get('name', 'Unknown'),
                                        'antardasha': transit_yogini['antardasha'].get('name', 'Unknown'),
                                        'vibe': transit_yogini['antardasha'].get('vibe', 'Neutral'),
                                        'start_date': transit_yogini['antardasha'].get('start', ''),
                                        'end_date': transit_yogini['antardasha'].get('end', '')
                                    }
                                    yogini_periods_for_range.append(y_info)
                            except Exception as e:
                                print(f"DEBUG: Yogini transit loop error: {e}")
                            
                            # Analyze dasha significance
                            significance = self._analyze_dasha_transit_significance(
                                aspect['transit_planet'], aspect['natal_planet'], dasha_periods
                            )
                            
                            # Determine dasha levels based on intent or period length
                            dasha_levels = self._get_required_dasha_levels(intent_result, year_range)
                            
                            # Create optimized dasha reference for this transit period
                            dasha_reference = {
                                'peak_date': period['start_date'],
                                'significance': significance,
                                'note': 'Reference unified_dasha_timeline for complete dasha sequences'
                            }
                            
                            # Create clean period without transit/natal planet fields to avoid duplication
                            clean_period = {k: v for k, v in period.items() if k not in ['transit_planet', 'natal_planet']}
                            
                            transit_activations.append({
                                'transit_planet': aspect['transit_planet'],
                                'natal_planet': aspect['natal_planet'],
                                **clean_period,
                                'aspect_number': aspect['aspect_number'],
                                'dasha_reference': dasha_reference,
                                'dasha_significance': significance,
                                'ashtakavarga_filter': self._apply_ashtakavarga_filter(
                                    period.get('transit_house'), 
                                    aspect['transit_planet'], 
                                    static_context.get('ashtakavarga', {})
                                ),
                                'karmic_triggers': self._detect_karmic_triggers(
                                    aspect['transit_planet'],
                                    period,
                                    chart_data
                                )
                            })
                    except Exception as aspect_error:
                        # print(f"     ❌ Error calculating timeline: {aspect_error}")
                        # import traceback
                        # traceback.print_exc()
                        pass
                        continue
                
                context['transit_activations'] = transit_activations
                
                # Add standalone dasha summary for entire period (covers quiet periods)
                context['requested_dasha_summary'] = self._build_standalone_dasha_summary(
                    birth_data, start_year, end_year, chart_data, context, intent_result, year_range
                )
                
                # Add logging to measure data size impact
                import json
                context_json = json.dumps(transit_activations)
                # print(f"🔍 TRANSIT DATA SIZE: {len(context_json)} characters")
                # print(f"🔍 TRANSIT COUNT: {len(transit_activations)}")
                
                # Sample first transit for inspection
                if transit_activations:
                    sample = transit_activations[0]
                    sample_json = json.dumps(sample)
                    # print(f"🔍 SAMPLE TRANSIT SIZE: {len(sample_json)} characters")
                    
                    # Log comprehensive dasha structure
                    comp_dashas = sample.get('comprehensive_dashas', {})
                    vims_count = len(comp_dashas.get('vimshottari_periods', []))
                    chara_count = len(comp_dashas.get('chara_periods', []))
                    yogini_count = len(comp_dashas.get('yogini_periods', []))
                    
                    # print(f"🔍 COMPREHENSIVE DASHA DATA:")
                    # print(f"   Vimshottari periods: {vims_count}")
                    # print(f"   Chara periods: {chara_count}")
                    # print(f"   Yogini periods: {yogini_count}")
                    
                    if vims_count > 0:
                        sample_vims = comp_dashas['vimshottari_periods'][0]
                        # print(f"   Sample Vimshottari: {sample_vims['mahadasha']}-{sample_vims['antardasha']}-{sample_vims['pratyantardasha']}")
                
                # Validate transit data integrity
                self._validate_transit_data(transit_activations)
                
                total_transit_time = time.time() - transit_start_time
                # print(f"⏱️ TOTAL TRANSIT CALCULATION TIME: {total_transit_time:.2f}s")
                # print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                # print(f"   Period: {start_year}-{end_year}")
                # print(f"   Total activations: {len(transit_activations)}")
                # print(f"   Enhanced with: All 5 Vimshottari levels + Chara Dasha + Yogini Dasha")
                for i, activation in enumerate(transit_activations[:3]):
                    comp_dashas = activation.get('comprehensive_dashas', {})
                    vims_count = len(comp_dashas.get('vimshottari_periods', []))
                    # print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']}) - {vims_count} dasha periods")
                if len(transit_activations) > 3:
                    print(f"     ... and {len(transit_activations) - 3} more")
                
                # Build unified dasha timeline (sent once at top level)
                context['unified_dasha_timeline'] = {
                    'vimshottari_periods': [
                        self._filter_dasha_levels(d, dasha_levels) for d in dasha_periods
                    ],
                    'chara_periods': chara_periods_for_range,
                    'yogini_periods': yogini_periods_for_range,
                    'dasha_levels_included': dasha_levels,
                    'note': 'Reference this timeline for all transit activations'
                }
                # Add comprehensive transit analysis instructions
                context['comprehensive_transit_analysis'] = {
                    "mandatory_approach": "For each transit activation, analyze ALL connected houses and predict MULTIPLE specific life events by combining house meanings",
                    "analysis_steps": [
                        "1. Identify transit planet's natal house + lordship houses",
                        "2. Identify natal planet's house + lordship houses", 
                        "3. Note the transit house where activation occurs",
                        "4. List ALL significations from each house (use complete house meanings provided)",
                        "5. Create event combinations by mixing house significations (e.g., 6th+9th = father's health + long travel = father's medical travel)",
                        "6. Apply planetary natures (benefic/malefic) for outcome polarity",
                        "7. Predict MINIMUM 3-5 specific events per transit activation, not just 1-2"
                    ],
                    "forbidden_approaches": [
                        "Generic philosophical statements about planetary influences",
                        "Vague terms like 'challenges', 'growth', 'good period'",
                        "Single house analysis ignoring lordships and connections",
                        "Theoretical discussions without specific event predictions"
                    ]
                }
                
                # Log transit data being sent
                # print(f"📊 TRANSIT DATA SENT TO GEMINI:")
                # print(f"   Period: {start_year}-{end_year}")
                # print(f"   Total activations: {len(transit_activations)}")
                # for i, activation in enumerate(transit_activations[:5]):
                #     print(f"     {i+1}. {activation['transit_planet']} -> {activation['natal_planet']} ({activation['start_date']} to {activation['end_date']})")
                # if len(transit_activations) > 5:
                #     print(f"     ... and {len(transit_activations) - 5} more")
                    
            except Exception as e:
                total_transit_time = time.time() - transit_start_time
                # print(f"❌ Error calculating transit activations after {total_transit_time:.2f}s: {e}")
                import traceback
                traceback.print_exc()
                context['transit_activations'] = []
                
        # Add transit optimization flag
        if intent_result and intent_result.get('needs_transits'):
            context['transit_optimization'] = {
                "source": "intent_router",
                "pre_calculated": True,
                "eliminates_second_call": True
            }
        elif requested_period:
            context['transit_optimization'] = {
                "source": "gemini_request", 
                "pre_calculated": False,
                "second_call_required": True
            }
        
        # Add period focus instructions if this is for a specific period
        if hasattr(self, '_selected_period_data'):
            context['selected_period_focus'] = {
                "period_data": self._selected_period_data,
                "response_format": "event_prediction_focused",
                "instruction": "Focus ONLY on specific event predictions for the selected period. Use the response_format_for_period_predictions template. Skip general chart analysis sections."
            }
        
        # Add Bhavat Bhavam analysis if question involves relatives
        bhavat_bhavam_analysis = self._detect_and_analyze_bhavat_bhavam(user_question, context)
        if bhavat_bhavam_analysis:
            context['bhavat_bhavam'] = bhavat_bhavam_analysis
        
        # Add Prediction Matrix for high-impact overlaps
        context['prediction_matrix'] = self._build_prediction_matrix(context)
        
        # ESSENTIAL STRUCTURE ONLY - Removed duplicate formatting (handled by output_schema.py)
        # context['RESPONSE_STRUCTURE_REQUIRED'] removed to prevent duplication
        
        return context
    
    def set_selected_period(self, period_data: Dict):
        """Set selected period for focused predictions"""
        self._selected_period_data = period_data
    
    def _create_birth_hash(self, birth_data: Dict) -> str:
        """Create unique hash for birth data"""
        import hashlib
        birth_string = f"{birth_data.get('date')}_{birth_data.get('time')}_{birth_data.get('latitude')}_{birth_data.get('longitude')}"
        return hashlib.sha256(birth_string.encode()).hexdigest()
    
    def _convert_divisional_charts_to_divisions_format(self, divisional_charts: Dict) -> Dict:
        """Convert divisional_charts dict to divisions format expected by Shadbala calculator.
        
        Input format: {'d9_navamsa': {'divisional_chart': {'planets': {...}}}, ...}
        Output format: {'D9': {'Sun': {'sign': 4, 'house': 10}, 'Moon': {...}}, ...}
        """
        divisions = {}
        
        # Mapping from chart names to division codes (D1 handled separately)
        chart_to_division = {
            'd2_hora': 'D2',
            'd3_drekkana': 'D3',
            'd7_saptamsa': 'D7',
            'd9_navamsa': 'D9',
            'd10_dasamsa': 'D10',
            'd12_dwadasamsa': 'D12',
            'd30_trimsamsa': 'D30'
        }
        
        for chart_name, division_code in chart_to_division.items():
            if chart_name in divisional_charts:
                chart_data = divisional_charts[chart_name]
                
                # Extract planets from nested structure
                if 'divisional_chart' in chart_data:
                    planets_data = chart_data['divisional_chart'].get('planets', {})
                else:
                    planets_data = chart_data.get('planets', {})
                
                # Convert to simple format
                division_planets = {}
                for planet_name, planet_data in planets_data.items():
                    division_planets[planet_name] = {
                        'sign': planet_data.get('sign', 0),
                        'house': planet_data.get('house', 1)
                    }
                
                if division_planets:
                    divisions[division_code] = division_planets
        
        return divisions
    
    def _analyze_dasha_transit_significance(self, transit_planet: str, natal_planet: str, dasha_periods: List[Dict]) -> str:
        """Analyze the significance of transit based on current dasha periods"""
        # print(f"         Analyzing significance for {transit_planet} -> {natal_planet}")
        
        if not dasha_periods:
            # print(f"         No dasha periods provided, returning moderate")
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
            
            # print(f"         Period {i+1} active planets: {active_planets}")
            
            transit_in_dasha = transit_planet in active_planets
            natal_in_dasha = natal_planet in active_planets
            
            # print(f"         {transit_planet} in dasha: {transit_in_dasha}, {natal_planet} in dasha: {natal_in_dasha}")
            
            if transit_in_dasha and natal_in_dasha:
                # print(f"         Both planets in dasha - MAXIMUM significance")
                max_significance = "maximum"
            elif transit_in_dasha or natal_in_dasha:
                if max_significance != "maximum":
                    # print(f"         One planet in dasha - HIGH significance")
                    max_significance = "high"
        
        # print(f"         Final significance: {max_significance}")
        return max_significance
    
    def get_high_significance_periods(self, birth_data: Dict, years_ahead: int = 2, selected_year: int = None) -> List[Dict]:
        """Get high-significance event periods for the next specified years"""
        current_year = datetime.now().year
        
        if selected_year:
            start_year = selected_year
            end_year = selected_year + 1
        else:
            start_year = current_year
            end_year = current_year + years_ahead
        
        # Build context with transit data
        context = self.build_complete_context(
            birth_data, "", None, 
            requested_period={'start_year': start_year, 'end_year': end_year}
        )
        
        # Extract high-significance periods with enhanced data
        periods = []
        dasha_calc = DashaCalculator()
        
        for activation in context.get('transit_activations', []):
            if activation['dasha_significance'] in ['high', 'maximum']:
                # Get overlapping dasha periods for this specific transit period
                start_date_obj = datetime.strptime(activation['start_date'], '%Y-%m-%d')
                end_date_obj = datetime.strptime(activation['end_date'], '%Y-%m-%d')
                
                overlapping_dashas = dasha_calc.get_dasha_periods_for_range(
                    birth_data, start_date_obj, end_date_obj
                )
                
                # Get the actual aspect number from the activation data (already calculated correctly)
                aspect_number = activation.get('aspect_number')
                transit_house = activation.get('transit_house')
                natal_house = activation.get('natal_house')
                
                # Validate aspect against planet's capabilities
                transit_planet = activation['transit_planet']
                valid_aspects = {
                    'Sun': [1, 7],
                    'Moon': [1, 7], 
                    'Mars': [1, 4, 7, 8],
                    'Mercury': [1, 7],
                    'Jupiter': [1, 5, 7, 9],
                    'Venus': [1, 7],
                    'Saturn': [1, 3, 7, 10],
                    'Rahu': [1, 5, 7, 9],
                    'Ketu': [1, 5, 7, 9]
                }
                
                # Only include if aspect is valid for this planet
                if aspect_number not in valid_aspects.get(transit_planet, []):
                    continue
                
                # Find which dasha the transit planet will be in during this period
                transit_planet_dashas = []
                for dasha in overlapping_dashas:
                    if dasha['mahadasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Mahadasha',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['antardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Antardasha', 
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['pratyantardasha'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Pratyantardasha',
                            'planet': transit_planet, 
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                    elif dasha['sookshma'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Sookshma',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'], 
                            'end_date': dasha['end_date']
                        })
                    elif dasha['prana'] == transit_planet:
                        transit_planet_dashas.append({
                            'type': 'Prana',
                            'planet': transit_planet,
                            'start_date': dasha['start_date'],
                            'end_date': dasha['end_date']
                        })
                

                
                # Calculate life areas affected by this transit
                life_areas = self._calculate_life_areas(
                    activation['transit_planet'],
                    activation['natal_planet'], 
                    transit_house,
                    natal_house,
                    context.get('house_lordships', {})
                )
                
                # Convert heavy dasha objects to lightweight strings for period data
                lightweight_transit_planet_dashas = [
                    f"{p.get('type', '')}: {p.get('planet', '')}"
                    for p in transit_planet_dashas
                ]
                
                periods.append({
                    'id': f"{activation['transit_planet']}-{activation['natal_planet']}-{activation['start_date']}",
                    'label': f"{activation['start_date']} to {activation['end_date']}: {activation['transit_planet']}→{activation['natal_planet']}",
                    'start_date': activation['start_date'],
                    'end_date': activation['end_date'],
                    'transit_planet': activation['transit_planet'],
                    'natal_planet': activation['natal_planet'],
                    'significance': activation['dasha_significance'],
                    'life_areas': life_areas,
                    'period_data': {
                        **activation,
                        'aspect_number': aspect_number,
                        # Remove 'overlapping_dashas' entirely (redundant)
                        'transit_planet_dashas': lightweight_transit_planet_dashas,
                        'life_areas': life_areas
                    }
                })
                

        
        # Sort by date
        periods.sort(key=lambda x: x['start_date'])
        

        return periods[:20]  # Return top 20 periods
    
    def _get_nakshatra_pada(self, longitude):
        """Calculate Nakshatra Pada from longitude with high precision"""
        # Normalize longitude (handle 360.0 or >360 cases)
        longitude = longitude % 360
        
        # Exact division: 360 degrees / 27 nakshatras
        nakshatra_span = 360 / 27
        
        # Calculate position (0-based index)
        absolute_position = longitude / nakshatra_span
        
        # Get nakshatra index (0 to 26)
        nakshatra_index = int(absolute_position)
        
        # Calculate pada (1 to 4)
        fractional_part = absolute_position - nakshatra_index
        pada = int(fractional_part * 4) + 1
        
        # Safety check for index bounds
        if nakshatra_index >= 27:
            nakshatra_index = 26
            
        return {
            'nakshatra': self.NAKSHATRA_NAMES[nakshatra_index],
            'nakshatra_id': nakshatra_index + 1,
            'pada': pada,
            'formatted': f"{self.NAKSHATRA_NAMES[nakshatra_index]} ({pada})"
        }
    
    def _calculate_d9_ashtakavarga(self, d9_chart, birth_data):
        """Calculate Ashtakavarga for D9 Navamsa chart"""
        try:
            from calculators.ashtakavarga import AshtakavargaCalculator
            # Access the correct nested structure
            d9_chart_data = d9_chart.get('divisional_chart', d9_chart)
            d9_ashtakavarga_calc = AshtakavargaCalculator(birth_data, d9_chart_data)
            
            return {
                "sarvashtakavarga": d9_ashtakavarga_calc.calculate_sarvashtakavarga(),
                "bhinnashtakavarga": {
                    planet: d9_ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                },
                "navamsa_analysis": d9_ashtakavarga_calc.get_ashtakavarga_analysis('navamsa')
            }
        except Exception as e:
            return {"error": f"D9 Ashtakavarga calculation failed: {e}"}
    
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
    
    def _calculate_life_areas(self, transit_planet: str, natal_planet: str, transit_house: int, natal_house: int, house_lordships: Dict) -> List[str]:
        """Calculate life areas affected by transit activation"""
        
        # Comprehensive house signification mapping for all life areas
        house_areas = {
            1: ["Self", "Health", "Personality", "Appearance", "Vitality", "Leadership", "Independence", "Identity"],
            2: ["Wealth", "Family", "Speech", "Values", "Food", "Savings", "Possessions", "Financial Security", "Material Assets"],
            3: ["Siblings", "Courage", "Communication", "Short Travel", "Efforts", "Neighbors", "Writing", "Media", "Skills", "Hobbies"],
            4: ["Home", "Mother", "Education", "Property", "Vehicles", "Happiness", "Domestic Life", "Real Estate", "Comfort", "Inner Peace"],
            5: ["Children", "Creativity", "Intelligence", "Romance", "Speculation", "Entertainment", "Sports", "Gambling", "Love Affairs", "Pregnancy"],
            6: ["Health Issues", "Enemies", "Service", "Daily Work", "Debts", "Diseases", "Employment", "Medical Treatment", "Competition", "Pets"],
            7: ["Marriage", "Partnerships", "Business", "Spouse", "Public Relations", "Contracts", "Legal Matters", "Cooperation", "Negotiations"],
            8: ["Transformation", "Occult", "Longevity", "Inheritance", "Accidents", "Research", "Surgery", "Insurance", "Taxes", "Joint Resources"],
            9: ["Fortune", "Dharma", "Higher Learning", "Father", "Spirituality", "Long Travel", "Philosophy", "Religion", "Foreign Countries", "Teaching"],
            10: ["Career", "Reputation", "Authority", "Public Image", "Government", "Profession", "Status", "Recognition", "Boss", "Fame"],
            11: ["Gains", "Friends", "Aspirations", "Elder Siblings", "Income", "Fulfillment", "Social Networks", "Hopes", "Profits", "Community"],
            12: ["Losses", "Spirituality", "Foreign Lands", "Expenses", "Isolation", "Moksha", "Hospitals", "Meditation", "Charity", "Liberation"]
        }
        
        affected_houses = set()
        
        # Add primary houses
        if transit_house:
            affected_houses.add(transit_house)
        if natal_house:
            affected_houses.add(natal_house)
        
        # Add lordship houses
        if transit_planet in house_lordships:
            affected_houses.update(house_lordships[transit_planet])
        if natal_planet in house_lordships:
            affected_houses.update(house_lordships[natal_planet])
        
        # Convert to life areas and prioritize
        life_areas = []
        priority_houses = [transit_house, natal_house] if transit_house and natal_house else []
        
        # Add primary areas first (top 2 from each priority house)
        for house in priority_houses:
            if house in house_areas:
                house_significations = house_areas[house][:2]  # Take top 2 significations
                for area in house_significations:
                    if area not in life_areas:
                        life_areas.append(area)
        
        # Add secondary areas from lordships (1 from each house)
        for house in sorted(affected_houses):
            if house in house_areas and house not in priority_houses:
                area = house_areas[house][0]  # Take primary signification
                if area not in life_areas and len(life_areas) < 4:
                    life_areas.append(area)
        
        return life_areas[:4]  # Return top 4 most relevant areas
    
    def _add_sign_names_to_chart_copy(self, chart_data: Dict) -> Dict:
        """Create copy of chart data with sign names to prevent Gemini 0-based vs 1-based indexing confusion"""
        import copy
        chart_copy = copy.deepcopy(chart_data)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Add sign names to all planets in d1_chart
        if 'planets' in chart_copy:
            for planet_name, planet_data in chart_copy['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        # Add sign names to bhav_chalit chart
        if 'bhav_chalit' in chart_copy and 'planets' in chart_copy['bhav_chalit']:
            for planet_name, planet_data in chart_copy['bhav_chalit']['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        return chart_copy
    
    def _get_child_lagna(self, ascendant_sign: int, child_number: int, method: str = 'bhavat_bhavam') -> int:
        """
        Calculates the Derived Lagna (Sign Index 0-11) for the Nth child.
        
        Args:
            ascendant_sign (int): Native's Lagna (0=Aries, 1=Taurus...)
            child_number (int): 1 for 1st child, 2 for 2nd, etc.
            method (str): 
                'sibling' = 5th, 7th, 9th (Standard Parashara - 3rd from previous)
                'bhavat_bhavam' = 5th, 9th, 1st (Deep Reflection - 5th from previous)
        
        Returns:
            int: The sign index (0-11) for that child's Lagna.
        """
        if child_number < 1: return ascendant_sign
        
        # 1. Start at the 5th House (Index + 4)
        # This is the universal house for the 1st Child
        child_lagna = (ascendant_sign + 4) % 12
        
        # 2. If looking for 2nd, 3rd, etc., apply the jump
        if child_number > 1:
            if method == 'sibling':
                # Jump 3 houses (Index + 2) for each subsequent child
                # 1st=5th, 2nd=7th, 3rd=9th...
                jump = 2
            else:
                # 'bhavat_bhavam' (The one that worked for the death prediction)
                # Jump 5 houses (Index + 4) for each subsequent child
                # 1st=5th, 2nd=9th, 3rd=1st...
                jump = 4
                
            # Apply jumps
            total_jump = jump * (child_number - 1)
            child_lagna = (child_lagna + total_jump) % 12
            
        return child_lagna
    
    def _check_relative_maraka(self, planet_name: str, relative_lagna_sign: int, chart_data: Dict) -> str:
        """
        Checks if a planet is a Maraka (Killer) for a relative's Lagna.
        """
        if planet_name not in chart_data['planets']: return "Neutral"
        
        # 1. Calculate Maraka Houses (2nd and 7th from Relative)
        maraka_house_2 = (relative_lagna_sign + 1) % 12  # 2nd Sign
        maraka_house_7 = (relative_lagna_sign + 6) % 12  # 7th Sign
        
        # 2. Get Lordships of the Planet
        sign_lords = {0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 
                      5: 'Mercury', 6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 
                      10: 'Saturn', 11: 'Jupiter'}
        
        is_maraka_lord = False
        if sign_lords[maraka_house_2] == planet_name: is_maraka_lord = True
        if sign_lords[maraka_house_7] == planet_name: is_maraka_lord = True
        
        # 3. Check Placement (Is it sitting in 2nd or 7th?)
        p_sign = chart_data['planets'][planet_name]['sign']
        is_in_maraka_house = (p_sign == maraka_house_2) or (p_sign == maraka_house_7)
        
        if is_maraka_lord and is_in_maraka_house:
            return "Strong Maraka Influence (Requires Remedies)"
        elif is_maraka_lord:
            return "Maraka Activation (Sensitivity)"
        elif is_in_maraka_house:
            return "Maraka Placement (Stress)"
            
        return "Safe"
    
    def _minify_data(self, data: Any) -> Any:
        """Recursively rounds floats to 2 decimal places to save tokens"""
        if isinstance(data, dict):
            return {k: self._minify_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._minify_data(i) for i in data]
        elif isinstance(data, float):
            return round(data, 2)
        return data
    
    def _apply_ashtakavarga_filter(self, transit_house: int, transit_planet: str, ashtakavarga_data: Dict) -> Dict:
        """Apply Ashtakavarga filter to transit predictions with BAV override"""
        if not transit_house or not ashtakavarga_data:
            return {'status': 'no_data', 'strength': 'unknown'}
        
        # Get Sarvashtakavarga (total points)
        d1_ashtakavarga = ashtakavarga_data.get('d1_rashi', {})
        sarvashtakavarga = d1_ashtakavarga.get('sarvashtakavarga', {})
        sav_points = sarvashtakavarga.get('house_points', [])
        
        # Get Bhinnashtakavarga for the transiting planet
        bhinnashtakavarga = d1_ashtakavarga.get('bhinnashtakavarga', {})
        planet_ashtakavarga = bhinnashtakavarga.get(transit_planet, {})
        
        if not sav_points or not planet_ashtakavarga:
            return {'status': 'no_data', 'strength': 'unknown'}
        
        # Get points for the transit house (convert 1-12 to 0-11 indexing)
        house_index = (transit_house - 1) % 12
        
        if len(sav_points) <= house_index:
            return {'status': 'no_house_data', 'strength': 'unknown'}
        
        sav_house_points = sav_points[house_index]
        
        # Get BAV points for this planet in this house
        bav_house_points_list = planet_ashtakavarga.get('house_points', [])
        if len(bav_house_points_list) <= house_index:
            bav_house_points = None
        else:
            bav_house_points = bav_house_points_list[house_index]
        
        # SAV strength classification
        if sav_house_points >= 28:
            sav_strength = 'excellent'
        elif sav_house_points >= 25:
            sav_strength = 'good'
        elif sav_house_points >= 22:
            sav_strength = 'moderate'
        elif sav_house_points >= 19:
            sav_strength = 'weak'
        else:
            sav_strength = 'very_weak'
        
        # BAV Override Logic
        if bav_house_points is not None:
            if bav_house_points < 3:
                # Planet struggles despite house strength
                if sav_strength in ['excellent', 'good']:
                    final_strength = 'mixed_bav_override'
                    prediction_modifier = 'paradox_strong_house_weak_planet'
                else:
                    final_strength = 'weak_bav_override'
                    prediction_modifier = 'disappointing_results'
            elif bav_house_points >= 4:
                # Planet strong, use SAV classification
                final_strength = sav_strength
                if sav_strength == 'excellent':
                    prediction_modifier = 'exceptional_results'
                elif sav_strength == 'good':
                    prediction_modifier = 'good_results'
                elif sav_strength == 'moderate':
                    prediction_modifier = 'moderate_results'
                else:
                    prediction_modifier = 'weak_results'
            else:  # BAV 3
                final_strength = f'{sav_strength}_adequate_bav'
                prediction_modifier = 'adequate_results'
        else:
            # No BAV data, use SAV only
            final_strength = sav_strength
            if sav_strength == 'excellent':
                prediction_modifier = 'exceptional_results'
            elif sav_strength == 'good':
                prediction_modifier = 'good_results'
            elif sav_strength == 'moderate':
                prediction_modifier = 'mixed_results'
            elif sav_strength == 'weak':
                prediction_modifier = 'limited_results'
            else:
                prediction_modifier = 'disappointing_results'
        
        return {
            'status': 'calculated',
            'sav_points': sav_house_points,
            'bav_points': bav_house_points,
            'sav_strength': sav_strength,
            'final_strength': final_strength,
            'prediction_modifier': prediction_modifier,
            'house': transit_house,
            'planet': transit_planet,
            'interpretation': self._get_combined_ashtakavarga_interpretation(
                sav_house_points, bav_house_points, transit_planet, transit_house
            ),
            'bav_override_active': bav_house_points is not None and bav_house_points < 3 and sav_house_points >= 25
        }
    
    def _get_combined_ashtakavarga_interpretation(self, sav_points: int, bav_points: int, planet: str, house: int) -> str:
        """Get interpretation based on both SAV and BAV points"""
        if bav_points is None:
            # Fallback to SAV only
            return self._get_ashtakavarga_interpretation(sav_points, planet, house)
        
        # BAV Override scenarios
        if bav_points < 3 and sav_points >= 25:
            return f"{planet} transit through {house}th house creates a paradox: The house has strong Sarvashtakavarga support ({sav_points} points), but {planet}'s individual Bhinnashtakavarga shows only {bav_points} points. The house is strong, but the planet struggles here - expect obstacles and delays despite favorable house strength."
        elif bav_points >= 4 and sav_points >= 28:
            return f"{planet} transit through {house}th house has exceptional support: Sarvashtakavarga {sav_points} points + {planet}'s Bhinnashtakavarga {bav_points} points = Outstanding results with smooth manifestation."
        elif bav_points >= 4 and sav_points >= 25:
            return f"{planet} transit through {house}th house has good support: Sarvashtakavarga {sav_points} points + {planet}'s Bhinnashtakavarga {bav_points} points = Positive outcomes with steady progress."
        elif bav_points == 3:
            return f"{planet} transit through {house}th house has adequate support: Sarvashtakavarga {sav_points} points + {planet}'s Bhinnashtakavarga {bav_points} points = Moderate results requiring effort."
        else:
            return f"{planet} transit through {house}th house has weak support: Sarvashtakavarga {sav_points} points + {planet}'s Bhinnashtakavarga {bav_points} points = Limited results with significant challenges."
    
    def _get_ashtakavarga_interpretation(self, points: int, planet: str, house: int) -> str:
        """Get interpretation based on Ashtakavarga points"""
        if points >= 28:
            return f"{planet} transit through {house}th house has exceptional Ashtakavarga support ({points} points) - expect outstanding results"
        elif points >= 25:
            return f"{planet} transit through {house}th house has good Ashtakavarga support ({points} points) - expect positive outcomes"
        elif points >= 22:
            return f"{planet} transit through {house}th house has moderate Ashtakavarga support ({points} points) - expect mixed results"
        elif points >= 19:
            return f"{planet} transit through {house}th house has weak Ashtakavarga support ({points} points) - results may be limited"
        else:
            return f"{planet} transit through {house}th house has very weak Ashtakavarga support ({points} points) - expect disappointing results despite good planetary position"
    
    def _detect_karmic_triggers(self, transit_planet: str, period: Dict, natal_chart: Dict) -> Dict:
        """Detect karmic triggers when slow planets conjunct natal planets within 3 degrees"""
        if transit_planet not in ['Saturn', 'Rahu', 'Jupiter']:
            return {'status': 'not_applicable', 'triggers': []}
        
        if not natal_chart.get('planets'):
            return {'status': 'no_natal_data', 'triggers': []}
        
        triggers = []
        conjunct_planets = period.get('conjunct_natal_planets', [])
        
        # For each conjunct planet, check if it's a precise karmic trigger
        for natal_planet in conjunct_planets:
            if natal_planet not in natal_chart['planets']:
                continue
            
            # Get natal planet longitude
            natal_longitude = natal_chart['planets'][natal_planet].get('longitude', 0)
            
            # Calculate trigger details
            trigger_type = self._get_karmic_trigger_type(transit_planet, natal_planet)
            duration = self._get_karmic_duration(transit_planet)
            
            triggers.append({
                'transit_planet': transit_planet,
                'natal_planet': natal_planet,
                'natal_longitude': natal_longitude,
                'trigger_type': trigger_type,
                'duration': duration,
                'karmic_theme': self._get_karmic_theme(transit_planet, natal_planet),
                'life_area': self._get_karmic_life_area(natal_planet),
                'intensity': 'maximum',  # Exact conjunctions are always maximum intensity
                'prediction_template': f"{transit_planet} triggers natal {natal_planet} - {trigger_type}"
            })
        
        return {
            'status': 'calculated' if triggers else 'no_triggers',
            'total_triggers': len(triggers),
            'triggers': triggers,
            'interpretation': self._get_karmic_trigger_interpretation(triggers, period)
        }
    
    def _get_karmic_trigger_type(self, transit_planet: str, natal_planet: str) -> str:
        """Get karmic trigger type based on planet combination"""
        combinations = {
            ('Saturn', 'Sun'): 'Authority Transformation',
            ('Saturn', 'Moon'): 'Emotional Maturation', 
            ('Saturn', 'Mars'): 'Disciplined Action',
            ('Saturn', 'Mercury'): 'Communication Mastery',
            ('Saturn', 'Jupiter'): 'Wisdom Through Hardship',
            ('Saturn', 'Venus'): 'Relationship Restructuring',
            ('Rahu', 'Sun'): 'Sudden Fame/Recognition',
            ('Rahu', 'Moon'): 'Mental Breakthrough',
            ('Rahu', 'Mars'): 'Explosive Action',
            ('Rahu', 'Mercury'): 'Innovative Communication',
            ('Rahu', 'Jupiter'): 'Unconventional Wisdom',
            ('Rahu', 'Venus'): 'Unusual Relationships',
            ('Jupiter', 'Sun'): 'Leadership Expansion',
            ('Jupiter', 'Moon'): 'Emotional Wisdom',
            ('Jupiter', 'Mars'): 'Righteous Action',
            ('Jupiter', 'Mercury'): 'Teaching/Learning',
            ('Jupiter', 'Venus'): 'Dharmic Relationships',
            ('Jupiter', 'Saturn'): 'Structured Growth'
        }
        return combinations.get((transit_planet, natal_planet), f'{transit_planet}-{natal_planet} Activation')
    
    def _get_karmic_duration(self, transit_planet: str) -> str:
        """Get karmic effect duration"""
        durations = {
            'Saturn': '2.5 years',
            'Rahu': '1.5 years', 
            'Jupiter': '1 year'
        }
        return durations.get(transit_planet, '1 year')
    
    def _get_karmic_theme(self, transit_planet: str, natal_planet: str) -> str:
        """Get karmic theme for the trigger"""
        themes = {
            'Saturn': 'Discipline, Responsibility, Permanent Change',
            'Rahu': 'Innovation, Foreign Elements, Sudden Elevation',
            'Jupiter': 'Expansion, Wisdom, Dharmic Growth'
        }
        return themes.get(transit_planet, 'Transformation')
    
    def _get_karmic_life_area(self, natal_planet: str) -> str:
        """Get life area affected by natal planet"""
        areas = {
            'Sun': 'Authority, Career, Father, Government',
            'Moon': 'Mind, Emotions, Mother, Public',
            'Mars': 'Energy, Property, Siblings, Competition',
            'Mercury': 'Communication, Business, Learning, Travel',
            'Jupiter': 'Wisdom, Children, Spirituality, Teaching',
            'Venus': 'Relationships, Wealth, Arts, Luxury',
            'Saturn': 'Service, Discipline, Longevity, Karma'
        }
        return areas.get(natal_planet, 'General Life')
    
    def _get_karmic_trigger_interpretation(self, triggers: List[Dict], period: Dict) -> str:
        """Get interpretation for karmic triggers"""
        if not triggers:
            return 'No karmic triggers detected in this period'
        
        if len(triggers) == 1:
            trigger = triggers[0]
            return f"KARMIC TRIGGER: {trigger['transit_planet']} activates your natal {trigger['natal_planet']}, creating {trigger['trigger_type']} lasting {trigger['duration']}"
        else:
            return f"MULTIPLE KARMIC TRIGGERS: {len(triggers)} planetary activations create a major life transformation period lasting up to 2.5 years"
    
    def _detect_and_analyze_bhavat_bhavam(self, user_question: str, base_context: Dict) -> Optional[Dict]:
        """Detect if question involves relatives and apply Bhavat Bhavam analysis"""
        if not user_question:
            return None
        
        question_lower = user_question.lower()
        
        # Relative detection patterns
        relative_patterns = {
            'spouse': {'keywords': ['husband', 'wife', 'spouse', 'partner'], 'house': 7},
            'father': {'keywords': ['father', 'dad', 'papa'], 'house': 9},
            'mother': {'keywords': ['mother', 'mom', 'mama'], 'house': 4},
            'children': {'keywords': ['child', 'son', 'daughter', 'kids'], 'house': 5},
            'siblings': {'keywords': ['brother', 'sister', 'sibling'], 'house': 3},
            'elder_sibling': {'keywords': ['elder brother', 'elder sister'], 'house': 11}
        }
        
        # Topic detection patterns
        topic_patterns = {
            'career': {'keywords': ['job', 'career', 'business', 'work', 'profession'], 'house_offset': 9},  # 10th from relative
            'health': {'keywords': ['health', 'illness', 'disease', 'medical'], 'house_offset': 5},  # 6th from relative
            'wealth': {'keywords': ['money', 'wealth', 'income', 'finance'], 'house_offset': 1},  # 2nd from relative
            'marriage': {'keywords': ['marriage', 'wedding', 'relationship'], 'house_offset': 6},  # 7th from relative
            'children': {'keywords': ['children', 'pregnancy', 'kids'], 'house_offset': 4}  # 5th from relative
        }
        
        detected_relative = None
        detected_topic = None
        
        # Detect relative
        for relative, data in relative_patterns.items():
            if any(keyword in question_lower for keyword in data['keywords']):
                detected_relative = {'name': relative, 'house': data['house']}
                break
        
        # Detect topic
        for topic, data in topic_patterns.items():
            if any(keyword in question_lower for keyword in data['keywords']):
                detected_topic = {'name': topic, 'house_offset': data['house_offset']}
                break
        
        if not detected_relative or not detected_topic:
            return None
        
        # Calculate Bhavat Bhavam house
        relative_house = detected_relative['house']
        topic_offset = detected_topic['house_offset']
        bhavat_bhavam_house = ((relative_house + topic_offset - 2) % 12) + 1
        
        return {
            'detected': True,
            'relative': detected_relative['name'],
            'relative_house': relative_house,
            'topic': detected_topic['name'],
            'topic_offset': topic_offset,
            'bhavat_bhavam_house': bhavat_bhavam_house,
            'analysis_instruction': f"Analyze {detected_topic['name']} of {detected_relative['name']} by examining the {bhavat_bhavam_house}th house (which is the {topic_offset}th house from the {relative_house}th house)",
            'example': f"Question about {detected_relative['name']}'s {detected_topic['name']} → Look at {bhavat_bhavam_house}th house"
        }
    
    def _analyze_dasha_conflicts(self, vimshottari_dasha: Dict, yogini_dasha: Dict) -> Dict:
        """Analyze conflicts between Vimshottari and Yogini dasha systems"""
        if not vimshottari_dasha or not yogini_dasha:
            return {'status': 'insufficient_data', 'conflicts': []}
        
        # Get current periods
        vims_maha = vimshottari_dasha.get('mahadasha', {}).get('planet')
        vims_antar = vimshottari_dasha.get('antardasha', {}).get('planet')
        yogini_period = yogini_dasha.get('current_yogini', {}).get('yogini')
        
        if not vims_maha or not yogini_period:
            return {'status': 'missing_periods', 'conflicts': []}
        
        conflicts = []
        
        # Analyze Mahadasha vs Yogini conflict
        maha_conflict = self._detect_planet_yogini_conflict(vims_maha, yogini_period)
        if maha_conflict:
            conflicts.append({
                'type': 'mahadasha_yogini',
                'vimshottari_planet': vims_maha,
                'yogini_period': yogini_period,
                'conflict_nature': maha_conflict,
                'prediction_impact': self._get_conflict_prediction_impact(vims_maha, yogini_period, maha_conflict)
            })
        
        # Analyze Antardasha vs Yogini conflict
        if vims_antar:
            antar_conflict = self._detect_planet_yogini_conflict(vims_antar, yogini_period)
            if antar_conflict:
                conflicts.append({
                    'type': 'antardasha_yogini',
                    'vimshottari_planet': vims_antar,
                    'yogini_period': yogini_period,
                    'conflict_nature': antar_conflict,
                    'prediction_impact': self._get_conflict_prediction_impact(vims_antar, yogini_period, antar_conflict)
                })
        
        return {
            'status': 'analyzed',
            'total_conflicts': len(conflicts),
            'conflicts': conflicts,
            'interpretation': self._get_dasha_conflict_interpretation(conflicts)
        }
    
    def _detect_planet_yogini_conflict(self, planet: str, yogini: str) -> Optional[str]:
        """Detect conflict between planet nature and yogini nature"""
        # Planet natures
        benefic_planets = ['Jupiter', 'Venus', 'Moon', 'Mercury']
        malefic_planets = ['Saturn', 'Mars', 'Rahu', 'Ketu', 'Sun']
        
        # Yogini natures
        auspicious_yoginis = ['Siddha', 'Mangala', 'Pingala']
        inauspicious_yoginis = ['Sankata', 'Ulka', 'Dhanya']
        
        planet_nature = 'benefic' if planet in benefic_planets else 'malefic'
        yogini_nature = 'auspicious' if yogini in auspicious_yoginis else 'inauspicious'
        
        # Detect conflicts
        if planet_nature == 'benefic' and yogini_nature == 'inauspicious':
            return 'benefic_planet_difficult_yogini'
        elif planet_nature == 'malefic' and yogini_nature == 'auspicious':
            return 'malefic_planet_auspicious_yogini'
        
        return None
    
    def _get_conflict_prediction_impact(self, planet: str, yogini: str, conflict_type: str) -> str:
        """Get prediction impact based on dasha conflict"""
        impacts = {
            'benefic_planet_difficult_yogini': f"{planet} promises positive results, but {yogini} Yogini indicates stress, delays, or unconventional circumstances",
            'malefic_planet_auspicious_yogini': f"{planet} indicates challenges, but {yogini} Yogini suggests unexpected support or positive outcomes through difficulties"
        }
        return impacts.get(conflict_type, f"Complex interaction between {planet} and {yogini}")
    
    def _get_dasha_conflict_interpretation(self, conflicts: List[Dict]) -> str:
        """Get overall interpretation of dasha conflicts"""
        if not conflicts:
            return "Vimshottari and Yogini dashas are aligned - expect straightforward manifestation of planetary results"
        
        if len(conflicts) == 1:
            conflict = conflicts[0]
            return f"DASHA CONFLICT DETECTED: {conflict['prediction_impact']} - expect nuanced results with mixed outcomes"
        else:
            return f"MULTIPLE DASHA CONFLICTS: {len(conflicts)} conflicting influences create a complex period requiring careful navigation"
    
    def _build_prediction_matrix(self, context: Dict) -> Dict:
        """Flags moments where multiple rules intersect for 'Stunning' accuracy"""
        triggers = []
        
        # Logic: If Karmic Trigger AND High Ashtakavarga AND Dasha Alignment
        for activation in context.get('transit_activations', []):
            karmic_status = activation.get('karmic_triggers', {}).get('status')
            ashtaka_points = activation.get('ashtakavarga_filter', {}).get('points', 0)
            dasha_significance = activation.get('dasha_significance')
            
            if (karmic_status == 'calculated' and 
                ashtaka_points > 28 and
                dasha_significance == 'maximum'):
                
                triggers.append({
                    "type": "LIFE_PIVOT_POINT",
                    "period": f"{activation['start_date']} to {activation['end_date']}",
                    "reason": "Karmic trigger aligned with powerful dasha and house strength",
                    "planets": f"{activation['transit_planet']} -> {activation['natal_planet']}",
                    "confidence": "95%_certainty"
                })
        
        # Check for Neecha Bhanga + Dasha alignment
        neecha_data = context.get('advanced_analysis', {}).get('neecha_bhanga', {})
        current_dasha = context.get('current_dashas', {})
        
        if neecha_data.get('neecha_bhanga_planets'):
            maha_planet = current_dasha.get('mahadasha', {}).get('planet')
            for nb_planet in neecha_data['neecha_bhanga_planets']:
                if nb_planet['planet'] == maha_planet and nb_planet['strength'] in ['Complete Cancellation', 'Strong Cancellation']:
                    triggers.append({
                        "type": "RAGS_TO_RICHES_ACTIVATION",
                        "period": "Current Mahadasha Period",
                        "reason": f"Neecha Bhanga {nb_planet['planet']} dasha creates legendary transformation",
                        "confidence": "90%_certainty"
                    })
        
        return {
            'total_triggers': len(triggers),
            'high_impact_periods': triggers,
            'interpretation': self._get_matrix_interpretation(triggers)
        }
    
    def _get_matrix_interpretation(self, triggers: List[Dict]) -> str:
        """Get interpretation for prediction matrix"""
        if not triggers:
            return "Standard astrological influences - no exceptional convergences detected"
        
        if len(triggers) == 1:
            trigger = triggers[0]
            return f"EXCEPTIONAL PERIOD DETECTED: {trigger['type']} with {trigger['confidence']} - {trigger['reason']}"
        else:
            return f"MULTIPLE LIFE-CHANGING CONVERGENCES: {len(triggers)} exceptional periods create a transformational phase"
    
    def _get_required_dasha_levels(self, intent_result: Optional[Dict], year_range: int) -> List[str]:
        """Determine required dasha levels based on intent and time period"""
        # Check if intent router specifically requests detailed dashas
        if intent_result and intent_result.get('detailed_dashas'):
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']
        
        # Smart selection based on time period
        if year_range <= 1:  # 1 year or less - include all levels
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']
        elif year_range <= 3:  # 2-3 years - first 4 levels
            return ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma']
        else:  # 4+ years - first 3 levels only
            return ['mahadasha', 'antardasha', 'pratyantardasha']
    
    def _filter_dasha_levels(self, dasha_period: Dict, required_levels: List[str]) -> Dict:
        """Filter dasha period to include only required levels"""
        filtered = {
            'start_date': dasha_period.get('start_date', ''),
            'end_date': dasha_period.get('end_date', '')
        }
        
        for level in required_levels:
            filtered[level] = dasha_period.get(level, '')
        
        return filtered
    
    def _build_standalone_dasha_summary(self, birth_data: Dict, start_year: int, end_year: int, chart_data: Dict, context: Dict, intent_result: Optional[Dict] = None, year_range: int = 1) -> Dict:
        """Build complete dasha summary for entire period to cover quiet periods"""
        from datetime import datetime, timedelta
        
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        dasha_calc = DashaCalculator()
        
        # Get all Vimshottari periods for the range
        vimshottari_periods = dasha_calc.get_dasha_periods_for_range(birth_data, start_date, end_date)
        
        # Determine required dasha levels
        dasha_levels = self._get_required_dasha_levels(intent_result, year_range)
        
        # Get house lordships for enriched data
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        house_lordships = self._get_house_lordships(ascendant_sign)
        
        # DIRECT EXTRACTION - Chara Dasha (use filtered data from context)
        chara_periods = context.get('chara_dasha', {}).get('periods', [])
        
        # DIRECT CALCULATION - Yogini Dasha for requested period start
        yogini_periods = []
        try:
            yogini_calc = YoginiDashaCalculator()
            moon_lon = chart_data.get('planets', {}).get('Moon', {}).get('longitude', 0)
            y_data = yogini_calc.calculate_current_yogini(birth_data, moon_lon, start_date)
            if y_data and 'antardasha' in y_data:
                yogini_periods.append({
                    'mahadasha': y_data['mahadasha'].get('name', 'Unknown'),
                    'antardasha': y_data['antardasha'].get('name', 'Unknown'),
                    'vibe': y_data['antardasha'].get('vibe', 'Neutral'),
                    'start_date': y_data['antardasha'].get('start', ''),
                    'end_date': y_data['antardasha'].get('end', '')
                })
        except Exception as e:
            print(f"DEBUG: Yogini summary calculation error: {e}")
        
        return {
            'period_coverage': f"{start_year}-{end_year}",
            'vimshottari_sequence': [
                self._filter_dasha_levels(d, dasha_levels) for d in vimshottari_periods
            ],
            'all_five_levels_sequence': [
                # ALWAYS provide all 5 levels with complete house data for Parashari analysis
                {
                    'target_date': d.get('start_date', ''),
                    'mahadasha': {
                        'lord': d.get('mahadasha', ''),
                        'natal_house': self._get_planet_natal_house(d.get('mahadasha', ''), chart_data),
                        'lordships': house_lordships.get(d.get('mahadasha', ''), []),
                        'transit_house': self._get_planet_transit_house(d.get('mahadasha', ''), start_date, birth_data)
                    },
                    'antardasha': {
                        'lord': d.get('antardasha', ''),
                        'natal_house': self._get_planet_natal_house(d.get('antardasha', ''), chart_data),
                        'lordships': house_lordships.get(d.get('antardasha', ''), []),
                        'transit_house': self._get_planet_transit_house(d.get('antardasha', ''), start_date, birth_data)
                    },
                    'pratyantardasha': {
                        'lord': d.get('pratyantardasha', ''),
                        'natal_house': self._get_planet_natal_house(d.get('pratyantardasha', ''), chart_data),
                        'lordships': house_lordships.get(d.get('pratyantardasha', ''), []),
                        'transit_house': self._get_planet_transit_house(d.get('pratyantardasha', ''), start_date, birth_data)
                    },
                    'sookshma': {
                        'lord': d.get('sookshma', ''),
                        'natal_house': self._get_planet_natal_house(d.get('sookshma', ''), chart_data),
                        'lordships': house_lordships.get(d.get('sookshma', ''), []),
                        'transit_house': self._get_planet_transit_house(d.get('sookshma', ''), start_date, birth_data)
                    },
                    'prana': {
                        'lord': d.get('prana', ''),
                        'natal_house': self._get_planet_natal_house(d.get('prana', ''), chart_data),
                        'lordships': house_lordships.get(d.get('prana', ''), []),
                        'transit_house': self._get_planet_transit_house(d.get('prana', ''), start_date, birth_data)
                    }
                } for d in vimshottari_periods
            ],
            'chara_sequence': chara_periods,
            'yogini_sequence': yogini_periods,
            'dasha_levels_included': dasha_levels,
            'note': f'Dasha coverage with {len(dasha_levels)} levels for {year_range}-year period. Use all_five_levels_sequence for complete Parashari analysis.'
        }
    
    def _validate_transit_data(self, transit_activations: List[Dict]) -> None:
        """Ensure essential data is preserved after optimization"""
        for activation in transit_activations:
            # Check required fields exist
            assert 'transit_planet' in activation, "Missing transit_planet"
            assert 'natal_planet' in activation, "Missing natal_planet"
            assert 'start_date' in activation, "Missing start_date"
            assert 'end_date' in activation, "Missing end_date"
            assert 'dasha_reference' in activation, "Missing dasha_reference"
        
        return None
    
    def _add_sign_names_to_divisional_chart(self, divisional_chart: Dict) -> Dict:
        """Add sign names to divisional chart to prevent Gemini indexing confusion"""
        import copy
        chart_copy = copy.deepcopy(divisional_chart)
        
        sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                     'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        
        # Add sign names to divisional chart planets
        if 'divisional_chart' in chart_copy and 'planets' in chart_copy['divisional_chart']:
            for planet_name, planet_data in chart_copy['divisional_chart']['planets'].items():
                if 'sign' in planet_data:
                    sign_index = planet_data['sign']
                    planet_data['sign_name'] = sign_names[sign_index]
        
        # Add sign names to houses
        if 'divisional_chart' in chart_copy and 'houses' in chart_copy['divisional_chart']:
            for house_data in chart_copy['divisional_chart']['houses']:
                if 'sign' in house_data:
                    sign_index = house_data['sign']
                    house_data['sign_name'] = sign_names[sign_index]
        
        return chart_copy

    
    def _prune_planetary_wars(self, war_summary: Dict) -> Dict:
        """Remove inactive planetary wars to reduce context noise"""
        if not war_summary or not war_summary.get('wars'):
            return war_summary
        
        # Keep only active wars
        active_wars = [w for w in war_summary.get('wars', []) if w.get('is_active', False)]
        
        return {
            'total_wars': len(active_wars),
            'wars': active_wars,
            'note': 'Only active wars included'
        }
    
    def _prune_neecha_bhanga(self, neecha_summary: Dict) -> Dict:
        """Remove empty neecha bhanga data to reduce context noise"""
        if not neecha_summary or not neecha_summary.get('planets_with_neecha_bhanga'):
            return {'total_neecha_bhanga_planets': 0, 'planets_with_neecha_bhanga': [], 'note': 'No neecha bhanga yogas'}
        
        # Keep only planets with actual cancellations
        return neecha_summary
    
    def _prune_remedies_by_relevance(self, all_remedies: Dict, planetary_analysis: Dict, current_dashas: Dict) -> Dict:
        """Prune remedies to only include relevant nakshatras based on current dashas and active planets"""
        if not all_remedies or not planetary_analysis or not current_dashas:
            return all_remedies
        
        # Get active planets from current dashas
        active_planets = set()
        md_planet = current_dashas.get('mahadasha', {}).get('planet')
        ad_planet = current_dashas.get('antardasha', {}).get('planet')
        pd_planet = current_dashas.get('pratyantardasha', {}).get('planet')
        
        if md_planet: active_planets.add(md_planet)
        if ad_planet: active_planets.add(ad_planet)
        if pd_planet: active_planets.add(pd_planet)
        
        # Get nakshatras of active planets
        relevant_nakshatras = set()
        for planet in active_planets:
            planet_data = planetary_analysis.get(planet, {})
            nakshatra = planet_data.get('basic_info', {}).get('nakshatra')
            if nakshatra:
                relevant_nakshatras.add(nakshatra)
        
        # Filter remedies to only relevant nakshatras
        if not relevant_nakshatras:
            return all_remedies
        
        pruned_remedies = {}
        for nakshatra in relevant_nakshatras:
            if nakshatra in all_remedies:
                pruned_remedies[nakshatra] = all_remedies[nakshatra]
        
        return pruned_remedies
    
    def _get_planet_natal_house(self, planet: str, chart_data: Dict) -> int:
        """Get natal house of planet from chart data"""
        if not planet or not chart_data.get('planets'):
            return 0
        planet_data = chart_data['planets'].get(planet, {})
        return planet_data.get('house', 0)
    
    def _get_planet_transit_house(self, planet: str, date: datetime, birth_data: Dict) -> int:
        """Get transit house of planet for given date"""
        if not planet:
            return 0
        try:
            from calculators.real_transit_calculator import RealTransitCalculator
            real_calc = RealTransitCalculator()
            transit_longitude = real_calc.get_planet_position(date, planet)
            if transit_longitude is None:
                return 0
            
            # Calculate house from longitude and ascendant
            birth_hash = self._create_birth_hash(birth_data)
            chart_data = self.static_cache[birth_hash]['d1_chart']
            ascendant_longitude = chart_data.get('ascendant', 0)
            transit_house = int((transit_longitude - ascendant_longitude) / 30) % 12 + 1
            return transit_house
        except Exception:
            return 0
    
    def _prune_advanced_analysis(self, advanced_data: Dict) -> Dict:
        """Remove empty advanced analysis sections to reduce token usage"""
        pruned = {}
        
        # Only include vargottama if there are actual vargottama planets
        vargottama = advanced_data.get('vargottama_positions', {})
        if vargottama.get('total_vargottama_planets', 0) > 0:
            pruned['vargottama_positions'] = vargottama
        
        # Only include neecha bhanga if there are actual cancellations
        neecha = advanced_data.get('neecha_bhanga', {})
        if neecha.get('total_neecha_bhanga_planets', 0) > 0:
            pruned['neecha_bhanga'] = neecha
        
        # Only include pancha mahapurusha if there are actual yogas
        pancha = advanced_data.get('pancha_mahapurusha', {})
        if pancha.get('total_yogas', 0) > 0:
            pruned['pancha_mahapurusha'] = pancha
        
        # Only include planetary wars if there are active wars
        wars = advanced_data.get('planetary_wars', {})
        if wars.get('total_wars', 0) > 0:
            pruned['planetary_wars'] = wars
        
        return pruned
    
    def _calculate_period_dasha_activations(self, start_date: datetime, end_date: datetime, birth_data: Dict) -> Dict:
        """Calculate dasha activations for any time period (day/week/month/year)"""
        period_days = (end_date - start_date).days
        
        if period_days <= 1:
            return self._calculate_daily_activations(start_date, birth_data)
        elif period_days <= 7:
            return self._calculate_weekly_activations(start_date, end_date, birth_data)
        elif period_days <= 31:
            return self._calculate_monthly_activations(start_date, end_date, birth_data)
        else:
            return self._calculate_extended_activations(start_date, end_date, birth_data)
    
    def _calculate_daily_activations(self, target_date: datetime, birth_data: Dict) -> Dict:
        """Calculate precise dasha activations for a single day"""
        dasha_calc = DashaCalculator()
        real_calc = RealTransitCalculator()
        
        # Get exact 5-level dashas for target date
        exact_dashas = dasha_calc.calculate_dashas_for_date(target_date, birth_data)
        
        # Get natal chart data
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        house_lordships = self._get_house_lordships(int(chart_data['ascendant'] / 30))
        
        activations = []
        dasha_levels = ['mahadasha', 'antardasha', 'pratyantardasha', 'sookshma', 'prana']
        
        for level in dasha_levels:
            planet = exact_dashas.get(level, {}).get('planet')
            if not planet:
                continue
                
            # Get transit position of dasha planet
            transit_longitude = real_calc.get_planet_position(target_date, planet)
            if transit_longitude is None:
                continue
                
            # Calculate activations
            activation = self._analyze_dasha_planet_activation(
                planet, level, transit_longitude, chart_data, house_lordships, target_date
            )
            activations.append(activation)
        
        return {
            'period_type': 'daily',
            'target_date': target_date.strftime('%Y-%m-%d'),
            'exact_dashas': exact_dashas,
            'dasha_activations': activations,
            'analysis_depth': 'maximum'
        }
    
    def _calculate_weekly_activations(self, start_date: datetime, end_date: datetime, birth_data: Dict) -> Dict:
        """Calculate dasha activations for a week (sample 3 key dates)"""
        mid_date = start_date + (end_date - start_date) / 2
        sample_dates = [start_date, mid_date, end_date]
        
        activations = []
        for date in sample_dates:
            daily_activation = self._calculate_daily_activations(date, birth_data)
            activations.append({
                'date': date.strftime('%Y-%m-%d'),
                'activations': daily_activation['dasha_activations'][:3]
            })
        
        return {
            'period_type': 'weekly',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'sampled_activations': activations,
            'analysis_depth': 'high'
        }
    
    def _calculate_monthly_activations(self, start_date: datetime, end_date: datetime, birth_data: Dict) -> Dict:
        """Calculate dasha activations for a month (sample weekly intervals)"""
        sample_dates = []
        current = start_date
        while current <= end_date:
            sample_dates.append(current)
            current += timedelta(days=7)
        
        activations = []
        for date in sample_dates:
            daily_activation = self._calculate_daily_activations(date, birth_data)
            activations.append({
                'date': date.strftime('%Y-%m-%d'),
                'activations': daily_activation['dasha_activations'][:2]
            })
        
        return {
            'period_type': 'monthly',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'sampled_activations': activations,
            'analysis_depth': 'medium'
        }
    
    def _calculate_extended_activations(self, start_date: datetime, end_date: datetime, birth_data: Dict) -> Dict:
        """Use existing transit system for longer periods"""
        return {
            'period_type': 'extended',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'note': 'Using existing transit activation system',
            'analysis_depth': 'standard'
        }
    
    def _analyze_dasha_planet_activation(self, planet: str, dasha_level: str, transit_longitude: float, 
                                       chart_data: Dict, house_lordships: Dict, target_date: datetime) -> Dict:
        """Analyze how a dasha planet is activated by its transit position"""
        # Get natal planet data
        natal_data = chart_data['planets'].get(planet, {})
        natal_longitude = natal_data.get('longitude', 0)
        natal_house = natal_data.get('house', 0)
        
        # Calculate transit house
        ascendant_longitude = chart_data.get('ascendant', 0)
        transit_house = int((transit_longitude - ascendant_longitude) / 30) % 12 + 1
        
        # Check transit connections
        connections = self._check_transit_connections(transit_longitude, natal_longitude, planet)
        
        # Get all activated houses
        activated_houses = set()
        activated_houses.add(natal_house)
        activated_houses.add(transit_house)
        activated_houses.update(house_lordships.get(planet, []))
        
        # Calculate probability based on connections and dasha level
        probability = self._calculate_activation_probability(connections, dasha_level)
        
        return {
            'planet': planet,
            'dasha_level': dasha_level,
            'natal_house': natal_house,
            'transit_house': transit_house,
            'activated_houses': list(activated_houses),
            'connections': connections,
            'probability': probability,
            'date': target_date.strftime('%Y-%m-%d')
        }
    
    def _check_transit_connections(self, transit_longitude: float, natal_longitude: float, planet: str) -> Dict:
        """Check various types of transit-natal connections"""
        connections = {'types': [], 'strength': 'none'}
        
        # Conjunction (within 3 degrees)
        orb = abs(transit_longitude - natal_longitude)
        if orb > 180:
            orb = 360 - orb
        
        if orb <= 3:
            connections['types'].append('conjunction')
            connections['strength'] = 'maximum'
        
        # Same nakshatra
        transit_nakshatra = int(transit_longitude / 13.333333)
        natal_nakshatra = int(natal_longitude / 13.333333)
        
        if transit_nakshatra == natal_nakshatra:
            connections['types'].append('same_nakshatra')
            if connections['strength'] == 'none':
                connections['strength'] = 'high'
        
        # Aspect (simplified - 7th house aspect)
        aspect_longitude = (natal_longitude + 180) % 360
        aspect_orb = abs(transit_longitude - aspect_longitude)
        if aspect_orb > 180:
            aspect_orb = 360 - aspect_orb
        
        if aspect_orb <= 5:
            connections['types'].append('opposition_aspect')
            if connections['strength'] == 'none':
                connections['strength'] = 'medium'
        
        return connections
    
    def _calculate_activation_probability(self, connections: Dict, dasha_level: str) -> str:
        """Calculate probability of manifestation based on connections and dasha level"""
        base_probabilities = {
            'mahadasha': 0.5,
            'antardasha': 0.4,
            'pratyantardasha': 0.3,
            'sookshma': 0.2,
            'prana': 0.1
        }
        
        connection_multipliers = {
            'maximum': 2.0,
            'high': 1.5,
            'medium': 1.2,
            'none': 1.0
        }
        
        base_prob = base_probabilities.get(dasha_level, 0.3)
        multiplier = connection_multipliers.get(connections['strength'], 1.0)
        final_prob = min(base_prob * multiplier, 0.95)
        
        if final_prob >= 0.8:
            return 'very_high'
        elif final_prob >= 0.6:
            return 'high'
        elif final_prob >= 0.4:
            return 'medium'
        else:
            return 'low'