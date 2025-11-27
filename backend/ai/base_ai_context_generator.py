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
from calculators.sniper_points_calculator import SniperPointsCalculator
from shared.dasha_calculator import DashaCalculator

class BaseAIContextGenerator:
    """Base context generator for all AI analysis types (health, education, career, marriage, etc.)"""
    
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
        
        # Initialize Ashtakavarga calculator
        from calculators.ashtakavarga import AshtakavargaCalculator
        ashtakavarga_calc = AshtakavargaCalculator(birth_data, chart_data)
        
        # Initialize Panchang calculator
        from calculators.panchang_calculator import PanchangCalculator
        panchang_calc = PanchangCalculator()
        panchang_calc.birth_data = birth_data
        
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
            
            # Main birth chart (with sign names added to prevent indexing confusion)
            "d1_chart": self._add_sign_names_to_chart_copy(chart_data),
            
            # Bhav Chalit chart
            "bhav_chalit_chart": chart_data.get('bhav_chalit', {}),
            
            # Key divisional charts
            "divisional_charts": {
                "d3_drekkana": divisional_calc.calculate_divisional_chart(3),
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
                "neecha_bhanga": neecha_bhanga_calc.get_neecha_bhanga_summary(),
                "karaka_synthesis_note": self._generate_karaka_synthesis_note(chart_data, chara_karaka_calc.calculate_chara_karakas())
            },
            
            # Ashtakavarga Analysis
            "ashtakavarga": {
                "d1_rashi": {
                    "sarvashtakavarga": ashtakavarga_calc.calculate_sarvashtakavarga(),
                    "bhinnashtakavarga": {
                        planet: ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                        for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                    }
                }
            },
            
            # Birth Panchang
            "birth_panchang": panchang_calc.calculate_birth_panchang(birth_data),
            
            # Sniper Points (Critical for sudden events/health crises)
            "sniper_points": SniperPointsCalculator(
                chart_data,
                divisional_calc.calculate_divisional_chart(3),
                divisional_calc.calculate_divisional_chart(9)
            ).get_all_sniper_points()
        }
        
        # Add minimal planetary analysis (raw data only, no text bloat)
        planets = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        for planet in planets:
            try:
                full_analysis = planet_analyzer.analyze_planet(planet)
                context["planetary_analysis"][planet] = self._filter_planetary_analysis(full_analysis, chart_calc)
            except Exception as e:
                continue
        
        # Add D9 Ashtakavarga
        try:
            d9_ashtakavarga_calc = AshtakavargaCalculator(birth_data, context["divisional_charts"]["d9_navamsa"])
            context["ashtakavarga"]["d9_navamsa"] = {
                "sarvashtakavarga": d9_ashtakavarga_calc.calculate_sarvashtakavarga(),
                "bhinnashtakavarga": {
                    planet: d9_ashtakavarga_calc.calculate_individual_ashtakavarga(planet)
                    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
                }
            }
        except Exception:
            context["ashtakavarga"]["d9_navamsa"] = {"error": "D9 calculation failed"}
        
        return context
    
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
    
    def _filter_planetary_analysis(self, full_analysis: Dict, chart_calc: ChartCalculator) -> Dict:
        """Filter planetary analysis to keep only raw data, remove text bloat and friendship matrix redundancy"""
        return {
            'basic_info': {
                'planet': full_analysis['basic_info']['planet'],
                'sign': full_analysis['basic_info']['sign'],
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
        
        # Add Bhavat Bhavam analysis to current dashas
        if 'current_dashas' in context and context['current_dashas']:
            current_md = context['current_dashas'].get('mahadasha', {}).get('planet')
            current_ad = context['current_dashas'].get('antardasha', {}).get('planet')
            
            context['current_dashas']['analysis_matrix'] = {
                'mahadasha_lord': self._calculate_dasha_relationships(current_md, chart_data) if current_md else {},
                'antardasha_lord': self._calculate_dasha_relationships(current_ad, chart_data) if current_ad else {}
            }
            
            # Add to maha_dashas list if present
            if 'maha_dashas' in context['current_dashas']:
                for dasha in context['current_dashas']['maha_dashas']:
                    planet_name = dasha.get('planet')
                    if planet_name:
                        dasha['rel_pos'] = self._calculate_dasha_relationships(planet_name, chart_data)
        
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
    
    def _generate_karaka_synthesis_note(self, chart_data: Dict, chara_karakas: Dict) -> Dict:
        """Generate synthesis note for cross-referencing Chara Karaka vs House Lord strength"""
        planets_data = chart_data.get('planets', {})
        synthesis_notes = []
        
        # Key relationships to check
        key_relationships = {
            'Matrukaraka': {'house': 4, 'signification': 'Mother'},
            'Pitrukaraka': {'house': 9, 'signification': 'Father'},
            'Putrakaraka': {'house': 5, 'signification': 'Children'},
            'Gnatikaraka': {'house': 6, 'signification': 'Health/Enemies'},
            'Darakaraka': {'house': 7, 'signification': 'Spouse/Marriage'},
            'Amatyakaraka': {'house': 10, 'signification': 'Career'}
        }
        
        # Get house lords
        houses = chart_data.get('houses', [])
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        for karaka_type, info in key_relationships.items():
            if karaka_type in chara_karakas:
                karaka_planet = chara_karakas[karaka_type]
                house_num = info['house']
                signification = info['signification']
                
                # Get house lord
                if house_num <= len(houses):
                    house_sign = houses[house_num - 1].get('sign', 0)
                    house_lord = sign_lords.get(house_sign)
                    
                    if karaka_planet in planets_data and house_lord in planets_data:
                        # Analyze karaka strength
                        karaka_data = planets_data[karaka_planet]
                        karaka_issues = []
                        
                        if karaka_data.get('retrograde', False):
                            karaka_issues.append('retrograde')
                        
                        # Check combustion from planetary analysis if available
                        karaka_house = karaka_data.get('house', 1)
                        sun_house = planets_data.get('Sun', {}).get('house', 1)
                        if karaka_house == sun_house and karaka_planet != 'Sun':
                            karaka_issues.append('combust')
                        
                        # Analyze house lord strength
                        lord_data = planets_data[house_lord]
                        lord_issues = []
                        
                        if lord_data.get('retrograde', False):
                            lord_issues.append('retrograde')
                        
                        lord_house = lord_data.get('house', 1)
                        if lord_house == sun_house and house_lord != 'Sun':
                            lord_issues.append('combust')
                        
                        # Generate synthesis note if there's a significant difference
                        if len(karaka_issues) != len(lord_issues) or karaka_issues != lord_issues:
                            karaka_status = 'afflicted' if karaka_issues else 'strong'
                            lord_status = 'afflicted' if lord_issues else 'strong'
                            
                            if karaka_status != lord_status:
                                synthesis_notes.append({
                                    'signification': signification,
                                    'karaka_planet': karaka_planet,
                                    'karaka_status': karaka_status,
                                    'karaka_issues': karaka_issues,
                                    'house_lord': house_lord,
                                    'lord_status': lord_status,
                                    'lord_issues': lord_issues,
                                    'analysis_note': f'Cross-reference required: {karaka_planet} ({karaka_type}) is {karaka_status} while {house_lord} ({house_num}th lord) is {lord_status}. Consider both Parashara (house lord) and Jaimini (karaka) methods for complete analysis.'
                                })
        
        return {
            'synthesis_required': len(synthesis_notes) > 0,
            'conflicting_indications': synthesis_notes,
            'instruction': 'When analyzing life areas, cross-reference both Parashara (house lords) and Jaimini (chara karakas) methods. If they conflict, mention both perspectives and synthesize for balanced prediction.',
            'dusthana_analysis_rule': 'CRITICAL: If a planet rules a Dusthana (6th, 8th, 12th) and transits that same house, interpret it as an intensification of that house\'s themes (e.g., health issues, transformation, expenses) rather than just "benefic protection", even if the planet is natural benefic like Jupiter.'
        }
    
    def _calculate_dasha_relationships(self, planet_name: str, chart_data: Dict) -> Dict:
        """
        Calculates the Dasha Lord's position relative to key life pillars (Bhavat Bhavam).
        Universal logic for All Purposes (Career, Mother, Father, etc.)
        """
        if not planet_name or planet_name not in chart_data.get('planets', {}):
            return {}

        planet_sign = chart_data['planets'][planet_name]['sign']
        asc_sign = int(chart_data['ascendant'] / 30)

        # Define the Pillars (0-based sign index)
        pillars = {
            "Self": asc_sign,                               # 1st House
            "Mother": (asc_sign + 3) % 12,                  # 4th House
            "Children": (asc_sign + 4) % 12,                # 5th House
            "Spouse": (asc_sign + 6) % 12,                  # 7th House
            "Father": (asc_sign + 8) % 12,                  # 9th House
            "Career": (asc_sign + 9) % 12                   # 10th House
        }

        relationships = {}
        
        for pillar_name, pillar_sign in pillars.items():
            # Calculate position: (Planet - Pillar + 12) % 12 + 1
            relative_house = ((planet_sign - pillar_sign + 12) % 12) + 1
            
            # Interpret the relationship (Universal Rules)
            effect = "Neutral"
            if relative_house in [6, 8, 12]:
                effect = "Challenging/Loss"
            elif relative_house in [1, 5, 9]:
                effect = "Excellent/Supportive"
            elif relative_house in [3, 10, 11]:
                effect = "Growth/Effort"
            elif relative_house in [2, 4, 7]:
                effect = "Sustaining/Active"

            relationships[f"from_{pillar_name}"] = f"{relative_house} ({effect})"

        return relationships