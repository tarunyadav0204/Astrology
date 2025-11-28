import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.yoga_calculator import YogaCalculator
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.mrityu_bhaga_calculator import MrityuBhagaCalculator
from vedic_predictions.config.functional_nature import FUNCTIONAL_BENEFICS, FUNCTIONAL_MALEFICS

class HealthAIContextGenerator(BaseAIContextGenerator):
    """Health-specific AI context generator inheriting from base"""
    
    def build_health_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build complete health analysis context"""
        
        # Get base context first
        base_context = self.build_base_context(birth_data)
        
        # Add health-specific context
        health_context = self._build_health_specific_context(birth_data)
        
        # Combine contexts
        return {
            **base_context,
            **health_context
        }
    
    def _build_health_specific_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build health-specific context components"""
        
        # Get chart data from base context
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        
        # Initialize health-specific calculators
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        divisional_calc = DivisionalChartCalculator(chart_data)
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        badhaka_calc = BadhakaCalculator(chart_data)
        planet_analyzer = PlanetAnalyzer(chart_data, birth_data)
        mrityu_calc = MrityuBhagaCalculator(chart_data)
        
        # Get ascendant sign
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        
        # Calculate D-30
        d30_chart = divisional_calc.calculate_divisional_chart(30)
        
        context = {
            # Health charts with analysis
            "health_charts": {
                "d30_trimsamsa": d30_chart,
                "d30_analysis": self._analyze_d30_chart(d30_chart, chart_data, ascendant_sign)
            },
            
            # Health house analysis
            "health_houses": self._analyze_health_houses(chart_data),
            
            # Vitality indicators
            "vitality_analysis": self._analyze_vitality(chart_data),
            
            # Disease susceptibility
            "disease_indicators": self._analyze_disease_indicators(chart_data),
            
            # Mental health
            "mental_health": self._analyze_mental_health(chart_data),
            
            # Health timing
            "health_timing": self._analyze_health_timing(birth_data, chart_data),
            
            # Body parts analysis (enhanced)
            "body_parts": self._analyze_body_parts_enhanced(chart_data),
            
            # Badhaka analysis
            "badhaka_analysis": badhaka_calc.get_chart_badhaka_summary(ascendant_sign),
            
            # Mrityu Bhaga analysis
            "mrityu_bhaga_analysis": mrityu_calc.analyze_chart_mrityu_bhaga(),
            
            # Functional nature analysis
            "functional_nature": self._analyze_functional_nature(chart_data, ascendant_sign),
            
            # Health analysis instructions
            "health_analysis_instructions": {
                "critical_note": "Focus on prevention and wellness, not diagnosis. Provide age-appropriate health guidance.",
                "disclaimer": "This is astrological guidance only, not medical advice. Always consult qualified healthcare professionals.",
                "system_instruction": self.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION
            }
        }
        
        return context
    
    def _analyze_health_houses(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze health-related houses"""
        
        health_houses = {
            "1st_house": self._analyze_house(1, chart_data),  # Physical body, vitality
            "6th_house": self._analyze_house(6, chart_data),  # Diseases, acute illness
            "8th_house": self._analyze_house(8, chart_data),  # Chronic diseases, surgery
            "12th_house": self._analyze_house(12, chart_data),  # Hospitalization, bed rest
            "4th_house": self._analyze_house(4, chart_data),  # Mental peace, chest
            "5th_house": self._analyze_house(5, chart_data),  # Digestive system
        }
        
        return health_houses
    
    def _analyze_house(self, house_num: int, chart_data: Dict) -> Dict[str, Any]:
        """Analyze a specific house for health"""
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', [])
        
        if house_num > len(houses):
            return {}
        
        house_sign = houses[house_num - 1].get('sign', 0)
        house_lord = self.SIGN_LORDS.get(house_sign, 'Unknown')
        
        # Find planets in this house
        planets_in_house = []
        for planet, data in planets.items():
            if data.get('house', 1) == house_num:
                planets_in_house.append(planet)
        
        # Get lord's position
        lord_position = {}
        if house_lord in planets:
            lord_data = planets[house_lord]
            lord_position = {
                'house': lord_data.get('house', 1),
                'sign': lord_data.get('sign', 0),
                'longitude': lord_data.get('longitude', 0)
            }
        
        return {
            'sign': house_sign,
            'lord': house_lord,
            'lord_position': lord_position,
            'planets_in_house': planets_in_house,
            'planet_count': len(planets_in_house)
        }
    
    def _analyze_vitality(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze overall vitality and immunity"""
        planets = chart_data.get('planets', {})
        
        # Ascendant lord (vitality)
        asc_lord_analysis = {}
        houses = chart_data.get('houses', [])
        if houses:
            asc_sign = houses[0].get('sign', 0)
            asc_lord = self.SIGN_LORDS.get(asc_sign, 'Unknown')
            if asc_lord in planets:
                asc_lord_data = planets[asc_lord]
                asc_lord_analysis = {
                    'planet': asc_lord,
                    'house': asc_lord_data.get('house', 1),
                    'sign': asc_lord_data.get('sign', 0),
                    'strength': self._get_planet_strength(asc_lord_data)
                }
        
        # Sun (immunity, vitality)
        sun_analysis = {}
        if 'Sun' in planets:
            sun_data = planets['Sun']
            sun_analysis = {
                'house': sun_data.get('house', 1),
                'sign': sun_data.get('sign', 0),
                'strength': self._get_planet_strength(sun_data)
            }
        
        # Mars (energy, blood)
        mars_analysis = {}
        if 'Mars' in planets:
            mars_data = planets['Mars']
            mars_analysis = {
                'house': mars_data.get('house', 1),
                'sign': mars_data.get('sign', 0),
                'strength': self._get_planet_strength(mars_data)
            }
        
        return {
            'ascendant_lord': asc_lord_analysis,
            'sun_analysis': sun_analysis,
            'mars_analysis': mars_analysis,
            'overall_vitality': self._calculate_overall_vitality(asc_lord_analysis, sun_analysis)
        }
    
    def _analyze_disease_indicators(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze disease susceptibility"""
        planets = chart_data.get('planets', {})
        
        # 6th house (acute diseases)
        sixth_house = self._analyze_house(6, chart_data)
        
        # 8th house (chronic diseases)
        eighth_house = self._analyze_house(8, chart_data)
        
        # Saturn (chronic issues)
        saturn_analysis = {}
        if 'Saturn' in planets:
            saturn_data = planets['Saturn']
            saturn_analysis = {
                'house': saturn_data.get('house', 1),
                'sign': saturn_data.get('sign', 0),
                'strength': self._get_planet_strength(saturn_data),
                'indicates': 'Chronic conditions, bones, teeth, joints'
            }
        
        # Rahu/Ketu (sudden issues)
        rahu_ketu_analysis = {}
        if 'Rahu' in planets and 'Ketu' in planets:
            rahu_ketu_analysis = {
                'rahu_house': planets['Rahu'].get('house', 1),
                'ketu_house': planets['Ketu'].get('house', 1),
                'indicates': 'Sudden health issues, mysterious ailments'
            }
        
        return {
            'sixth_house_analysis': sixth_house,
            'eighth_house_analysis': eighth_house,
            'saturn_influence': saturn_analysis,
            'rahu_ketu_influence': rahu_ketu_analysis,
            'disease_risk_level': self._calculate_disease_risk(sixth_house, eighth_house)
        }
    
    def _analyze_mental_health(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze mental health indicators"""
        planets = chart_data.get('planets', {})
        
        # Moon (mind, emotions)
        moon_analysis = {}
        if 'Moon' in planets:
            moon_data = planets['Moon']
            moon_analysis = {
                'house': moon_data.get('house', 1),
                'sign': moon_data.get('sign', 0),
                'strength': self._get_planet_strength(moon_data),
                'indicates': 'Emotional stability, mental peace'
            }
        
        # Mercury (nervous system)
        mercury_analysis = {}
        if 'Mercury' in planets:
            mercury_data = planets['Mercury']
            mercury_analysis = {
                'house': mercury_data.get('house', 1),
                'sign': mercury_data.get('sign', 0),
                'strength': self._get_planet_strength(mercury_data),
                'indicates': 'Nervous system, communication, anxiety'
            }
        
        # 4th house (mental peace)
        fourth_house = self._analyze_house(4, chart_data)
        
        return {
            'moon_analysis': moon_analysis,
            'mercury_analysis': mercury_analysis,
            'fourth_house_analysis': fourth_house,
            'mental_health_status': self._calculate_mental_health_status(moon_analysis, mercury_analysis)
        }
    
    def _analyze_health_timing(self, birth_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze health crisis timing"""
        
        # Get current dashas
        from shared.dasha_calculator import DashaCalculator
        dasha_calc = DashaCalculator()
        current_dashas = dasha_calc.calculate_current_dashas(birth_data)
        
        # Health timing factors
        timing_factors = {
            'current_dashas': current_dashas,
            'vulnerable_periods': self._get_vulnerable_periods(current_dashas, chart_data),
            'saturn_transit_info': self._get_saturn_transit_info(),
            'current_period_analysis': self._analyze_current_period_for_health(current_dashas, chart_data)
        }
        
        return timing_factors
    
    def _analyze_body_parts(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze body parts ruled by different signs and planets"""
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', [])
        
        body_part_mapping = {
            0: 'Head, brain, face',  # Aries
            1: 'Neck, throat, thyroid',  # Taurus
            2: 'Shoulders, arms, lungs',  # Gemini
            3: 'Chest, breasts, stomach',  # Cancer
            4: 'Heart, spine, upper back',  # Leo
            5: 'Digestive system, intestines',  # Virgo
            6: 'Kidneys, lower back, skin',  # Libra
            7: 'Reproductive organs, excretory system',  # Scorpio
            8: 'Hips, thighs, liver',  # Sagittarius
            9: 'Knees, bones, teeth',  # Capricorn
            10: 'Calves, ankles, circulation',  # Aquarius
            11: 'Feet, lymphatic system'  # Pisces
        }
        
        # Analyze afflicted signs
        afflicted_body_parts = []
        for house_num, house_data in enumerate(houses, 1):
            sign = house_data.get('sign', 0)
            planets_in_house = [p for p, data in planets.items() if data.get('house', 1) == house_num]
            
            # Check for malefic influence
            malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']
            if any(p in malefics for p in planets_in_house):
                body_part = body_part_mapping.get(sign, 'Unknown')
                afflicted_body_parts.append({
                    'body_part': body_part,
                    'sign': sign,
                    'house': house_num,
                    'afflicting_planets': [p for p in planets_in_house if p in malefics]
                })
        
        return {
            'body_part_mapping': body_part_mapping,
            'afflicted_areas': afflicted_body_parts,
            'areas_needing_attention': [item['body_part'] for item in afflicted_body_parts[:3]]
        }
    
    def _get_planet_strength(self, planet_data: Dict) -> str:
        """Get basic planet strength"""
        house = planet_data.get('house', 1)
        
        if house in [1, 4, 7, 10]:  # Kendra
            return 'Strong'
        elif house in [1, 5, 9]:  # Trikona
            return 'Strong'
        elif house in [6, 8, 12]:  # Dusthana
            return 'Weak'
        else:
            return 'Medium'
    
    def _calculate_overall_vitality(self, asc_lord: Dict, sun: Dict) -> str:
        """Calculate overall vitality level"""
        if not asc_lord or not sun:
            return 'Medium'
        
        asc_strength = asc_lord.get('strength', 'Medium')
        sun_strength = sun.get('strength', 'Medium')
        
        if asc_strength == 'Strong' and sun_strength == 'Strong':
            return 'Excellent'
        elif asc_strength == 'Weak' or sun_strength == 'Weak':
            return 'Needs Attention'
        else:
            return 'Good'
    
    def _calculate_disease_risk(self, sixth_house: Dict, eighth_house: Dict) -> str:
        """Calculate disease risk level"""
        sixth_planets = sixth_house.get('planet_count', 0)
        eighth_planets = eighth_house.get('planet_count', 0)
        
        total_affliction = sixth_planets + eighth_planets
        
        if total_affliction >= 3:
            return 'High - Requires preventive care'
        elif total_affliction >= 1:
            return 'Moderate - Regular checkups recommended'
        else:
            return 'Low - Maintain healthy lifestyle'
    
    def _calculate_mental_health_status(self, moon: Dict, mercury: Dict) -> str:
        """Calculate mental health status"""
        if not moon or not mercury:
            return 'Stable'
        
        moon_strength = moon.get('strength', 'Medium')
        mercury_strength = mercury.get('strength', 'Medium')
        
        if moon_strength == 'Weak' or mercury_strength == 'Weak':
            return 'Needs emotional support and stress management'
        elif moon_strength == 'Strong' and mercury_strength == 'Strong':
            return 'Excellent mental resilience'
        else:
            return 'Stable with occasional stress'
    
    def _get_vulnerable_periods(self, current_dashas: Dict, chart_data: Dict) -> list:
        """Get vulnerable health periods"""
        if not current_dashas:
            return []
        
        mahadasha = current_dashas.get('mahadasha', 'Unknown')
        
        # Health-challenging planets
        challenging_planets = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        
        vulnerable = []
        if mahadasha in challenging_planets:
            vulnerable.append(f"Current {mahadasha} Mahadasha may bring health challenges")
        
        return vulnerable
    
    def _get_saturn_transit_info(self) -> Dict[str, Any]:
        """Get current Saturn position for health timing"""
        from calculators.real_transit_calculator import RealTransitCalculator
        from datetime import datetime
        
        try:
            transit_calc = RealTransitCalculator()
            current_date = datetime.now()
            
            saturn_longitude = transit_calc.get_planet_position(current_date, 'Saturn')
            current_saturn_sign = int(saturn_longitude / 30) if saturn_longitude else 0
            
            sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
            
            return {
                'current_saturn_sign': sign_names[current_saturn_sign],
                'saturn_longitude': saturn_longitude,
                'health_note': 'Saturn transits can indicate periods requiring extra health care'
            }
        except Exception as e:
            return {
                'error': f'Transit position error: {e}',
                'health_note': 'Saturn transits can indicate periods requiring extra health care'
            }
    
    def _analyze_current_period_for_health(self, current_dashas: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze current dasha period for health"""
        if not current_dashas:
            return {'analysis': 'No current dasha data available'}
        
        mahadasha = current_dashas.get('mahadasha', 'Unknown')
        antardasha = current_dashas.get('antardasha', 'Unknown')
        
        # Health-challenging planets
        challenging_planets = ['Saturn', 'Mars', 'Rahu', 'Ketu']
        
        health_status = 'Good'
        if mahadasha in challenging_planets or antardasha in challenging_planets:
            health_status = 'Requires attention'
        
        analysis = {
            'current_mahadasha': mahadasha,
            'current_antardasha': antardasha,
            'health_status': health_status,
            'recommendation': f'Current {mahadasha}-{antardasha} period health guidance'
        }
        
        return analysis
    
    def _analyze_d30_chart(self, d30_chart: Dict, d1_chart: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze D-30 (Trimsamsa) for disease severity"""
        if not d30_chart or 'planets' not in d30_chart:
            return {'analysis': 'D-30 chart not available'}
        
        d30_planets = d30_chart['planets']
        d1_planets = d1_chart['planets']
        
        # Get 6th lord from D-1
        sixth_sign = (ascendant_sign + 5) % 12
        sixth_lord = self.SIGN_LORDS.get(sixth_sign, 'Unknown')
        
        # Get Lagna lord from D-1
        lagna_lord = self.SIGN_LORDS.get(ascendant_sign, 'Unknown')
        
        # Analyze 6th lord in D-30
        sixth_lord_d30_analysis = {}
        if sixth_lord in d30_planets:
            d30_sign = d30_planets[sixth_lord].get('sign', 0)
            malefic_signs = [0, 3, 6, 7, 9]  # Aries, Cancer, Libra, Scorpio, Capricorn
            benefic_signs = [1, 2, 4, 5, 8, 10, 11]  # Others
            
            is_malefic_sign = d30_sign in malefic_signs
            sixth_lord_d30_analysis = {
                'planet': sixth_lord,
                'd30_sign': d30_sign,
                'sign_nature': 'malefic' if is_malefic_sign else 'benefic',
                'disease_severity': 'Serious/Fatal' if is_malefic_sign else 'Curable',
                'interpretation': f"6th lord {sixth_lord} in {'malefic' if is_malefic_sign else 'benefic'} sign in D-30 indicates {'serious' if is_malefic_sign else 'manageable'} health issues"
            }
        
        # Analyze Lagna lord in D-30
        lagna_lord_d30_analysis = {}
        if lagna_lord in d30_planets:
            d30_sign = d30_planets[lagna_lord].get('sign', 0)
            d30_house = d30_planets[lagna_lord].get('house', 1)
            
            is_afflicted = d30_house in [6, 8, 12]
            lagna_lord_d30_analysis = {
                'planet': lagna_lord,
                'd30_sign': d30_sign,
                'd30_house': d30_house,
                'is_afflicted': is_afflicted,
                'vitality_status': 'Compromised' if is_afflicted else 'Strong',
                'interpretation': f"Lagna lord {lagna_lord} in {d30_house}th house of D-30 shows {'compromised' if is_afflicted else 'good'} vitality"
            }
        
        return {
            'sixth_lord_analysis': sixth_lord_d30_analysis,
            'lagna_lord_analysis': lagna_lord_d30_analysis,
            'overall_d30_assessment': self._assess_d30_overall(sixth_lord_d30_analysis, lagna_lord_d30_analysis)
        }
    
    def _assess_d30_overall(self, sixth_analysis: Dict, lagna_analysis: Dict) -> str:
        """Assess overall D-30 health indication"""
        if not sixth_analysis or not lagna_analysis:
            return 'Insufficient D-30 data'
        
        sixth_severity = sixth_analysis.get('disease_severity', 'Unknown')
        lagna_vitality = lagna_analysis.get('vitality_status', 'Unknown')
        
        if sixth_severity == 'Serious/Fatal' and lagna_vitality == 'Compromised':
            return 'High health risk - requires immediate preventive measures and regular medical monitoring'
        elif sixth_severity == 'Serious/Fatal' or lagna_vitality == 'Compromised':
            return 'Moderate health risk - preventive care and healthy lifestyle essential'
        else:
            return 'Good health potential - maintain wellness practices'
    
    def _analyze_body_parts_enhanced(self, chart_data: Dict) -> Dict[str, Any]:
        """Enhanced body parts analysis with house-sign overlay"""
        planets = chart_data.get('planets', {})
        houses = chart_data.get('houses', [])
        
        # House-to-body-part mapping (Kalpurusha)
        house_body_mapping = {
            1: 'Head, brain, face',
            2: 'Face, eyes, throat, neck',
            3: 'Shoulders, arms, hands',
            4: 'Chest, breasts, heart, lungs',
            5: 'Stomach, upper abdomen, digestive',
            6: 'Intestines, lower abdomen, kidneys',
            7: 'Reproductive organs, lower back',
            8: 'Excretory system, chronic organs',
            9: 'Hips, thighs, liver',
            10: 'Knees, joints',
            11: 'Calves, ankles, circulation',
            12: 'Feet, lymphatic, hidden organs'
        }
        
        # Sign-to-body-part mapping (Natural zodiac)
        sign_body_mapping = {
            0: 'Head, brain, face',  # Aries
            1: 'Neck, throat, thyroid',  # Taurus
            2: 'Shoulders, arms, lungs',  # Gemini
            3: 'Chest, breasts, stomach',  # Cancer
            4: 'Heart, spine, upper back',  # Leo
            5: 'Digestive system, intestines',  # Virgo
            6: 'Kidneys, lower back, skin',  # Libra
            7: 'Reproductive organs, excretory system',  # Scorpio
            8: 'Hips, thighs, liver',  # Sagittarius
            9: 'Knees, bones, teeth',  # Capricorn
            10: 'Calves, ankles, circulation',  # Aquarius
            11: 'Feet, lymphatic system'  # Pisces
        }
        
        # Analyze afflictions by house
        afflicted_areas = []
        for house_num, house_data in enumerate(houses, 1):
            sign = house_data.get('sign', 0)
            planets_in_house = [p for p, data in planets.items() if data.get('house', 1) == house_num]
            
            malefics = ['Mars', 'Saturn', 'Rahu', 'Ketu']
            malefic_planets = [p for p in planets_in_house if p in malefics]
            
            if malefic_planets:
                house_body_part = house_body_mapping.get(house_num, 'Unknown')
                sign_body_part = sign_body_mapping.get(sign, 'Unknown')
                
                # Determine affliction type based on sign
                affliction_type = self._determine_affliction_type(sign, malefic_planets)
                
                afflicted_areas.append({
                    'house': house_num,
                    'house_body_part': house_body_part,
                    'sign': sign,
                    'sign_body_part': sign_body_part,
                    'afflicting_planets': malefic_planets,
                    'affliction_type': affliction_type,
                    'interpretation': f"{house_body_part} affected by {', '.join(malefic_planets)} causing {affliction_type}"
                })
        
        return {
            'house_body_mapping': house_body_mapping,
            'sign_body_mapping': sign_body_mapping,
            'afflicted_areas': afflicted_areas,
            'priority_areas': [item['house_body_part'] for item in afflicted_areas[:3]]
        }
    
    def _determine_affliction_type(self, sign: int, malefic_planets: list) -> str:
        """Determine type of affliction based on sign element"""
        fire_signs = [0, 4, 8]  # Aries, Leo, Sagittarius
        water_signs = [3, 7, 11]  # Cancer, Scorpio, Pisces
        air_signs = [2, 6, 10]  # Gemini, Libra, Aquarius
        earth_signs = [1, 5, 9]  # Taurus, Virgo, Capricorn
        
        if sign in fire_signs:
            return 'Inflammation, fever, acidity, heat-related issues'
        elif sign in water_signs:
            return 'Fluid retention, swelling, emotional disorders'
        elif sign in air_signs:
            return 'Nervous disorders, anxiety, circulation issues'
        elif sign in earth_signs:
            return 'Chronic conditions, structural problems, stiffness'
        else:
            return 'General health challenges'
    
    def _analyze_functional_nature(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze functional benefic/malefic nature for health"""
        planets = chart_data.get('planets', {})
        
        functional_benefics = FUNCTIONAL_BENEFICS.get(ascendant_sign, [])
        functional_malefics = FUNCTIONAL_MALEFICS.get(ascendant_sign, [])
        
        health_benefics = []
        health_malefics = []
        
        for planet_name in planets.keys():
            if planet_name in ['Rahu', 'Ketu']:
                continue
            
            planet_data = planets[planet_name]
            house = planet_data.get('house', 1)
            
            if planet_name in functional_benefics:
                health_benefics.append({
                    'planet': planet_name,
                    'house': house,
                    'health_impact': 'Positive - supports health and vitality'
                })
            elif planet_name in functional_malefics:
                # Functional malefic in health houses is particularly bad
                if house in [1, 6, 8, 12]:
                    health_malefics.append({
                        'planet': planet_name,
                        'house': house,
                        'health_impact': f'Negative - functional malefic in {house}th house creates health challenges'
                    })
        
        return {
            'ascendant_sign': ascendant_sign,
            'functional_benefics': health_benefics,
            'functional_malefics': health_malefics,
            'health_assessment': self._assess_functional_health(health_benefics, health_malefics)
        }
    
    def _assess_functional_health(self, benefics: list, malefics: list) -> str:
        """Assess overall functional health status"""
        if len(malefics) > len(benefics):
            return 'Functional malefics dominate - requires extra health vigilance'
        elif len(benefics) > len(malefics):
            return 'Functional benefics support health - good natural immunity'
        else:
            return 'Balanced functional nature - moderate health management needed'
    
    @property
    def SIGN_LORDS(self):
        """Sign lordships"""
        return {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
