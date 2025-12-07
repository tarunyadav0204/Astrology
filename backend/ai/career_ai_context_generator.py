import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.aspect_calculator import AspectCalculator
from calculators.nakshatra_calculator import NakshatraCalculator
from calculators.d10_analyzer import D10Analyzer
from calculators.tenth_house_analyzer import TenthHouseAnalyzer
from calculators.nakshatra_career_analyzer import NakshatraCareerAnalyzer

class CareerAIContextGenerator(BaseAIContextGenerator):
    """Career-specific AI context generator inheriting from base"""
    
    def build_career_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build complete career analysis context"""
        
        # Get base context first
        base_context = self.build_base_context(birth_data)
        
        # Add career-specific context
        career_context = self._build_career_specific_context(birth_data)
        
        # Combine contexts
        return {
            **base_context,
            **career_context
        }
    
    def _build_career_specific_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build career-specific context components"""
        
        # Get chart data from base context
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        base_context = self.static_cache[birth_hash]
        
        # Get Amatyakaraka from base context
        amatyakaraka = base_context.get('chara_karakas', {}).get('Amatyakaraka')
        
        # Calculate dignities once
        dignities_calc = PlanetaryDignitiesCalculator(chart_data)
        dignities_report = dignities_calc.calculate_planetary_dignities()
        
        # Initialize calculators with AmK
        aspect_calc = AspectCalculator(chart_data)
        nakshatra_calc = NakshatraCalculator(birth_data, chart_data)
        d10_analyzer = D10Analyzer(chart_data, amatyakaraka=amatyakaraka)
        tenth_house_analyzer = TenthHouseAnalyzer(chart_data, birth_data)
        nakshatra_career = NakshatraCareerAnalyzer(chart_data)
        
        # Get ascendant sign
        ascendant_sign = int(chart_data.get('ascendant', 0) / 30)
        
        context = {
            # Career houses analysis (10th, 6th, 7th, 2nd, 11th)
            "career_houses": self._analyze_career_houses(chart_data, ascendant_sign),
            
            # 10th house detailed analysis
            "tenth_house_analysis": self._analyze_tenth_house(chart_data, ascendant_sign),
            
            # 6th house (service, daily work, employment)
            "sixth_house_analysis": self._analyze_sixth_house(chart_data, ascendant_sign),
            
            # 7th house (business, partnerships, public dealings)
            "seventh_house_analysis": self._analyze_seventh_house(chart_data, ascendant_sign),
            
            # 2nd house (earned wealth, speech value)
            "second_house_analysis": self._analyze_second_house(chart_data, ascendant_sign),
            
            # 11th house (gains, income, large organizations)
            "eleventh_house_analysis": self._analyze_eleventh_house(chart_data, ascendant_sign),
            
            # Saturn analysis (Karma Karaka) - pass pre-calculated dignity
            "saturn_analysis": self._analyze_saturn_for_career(chart_data, dignities_report.get('Saturn', {})),
            
            # Sun analysis (authority, government)
            "sun_analysis": self._analyze_sun_for_career(chart_data),
            
            # Mercury analysis (business, communication)
            "mercury_analysis": self._analyze_mercury_for_career(chart_data),
            
            # Amatyakaraka analysis (already in base, add interpretation)
            "amatyakaraka_career": self._analyze_amatyakaraka(chart_data, base_context=self.static_cache[birth_hash]),
            
            # D10 detailed analysis with AmK
            "d10_detailed": d10_analyzer.analyze_d10_chart(),
            
            # Arudha Lagna (Status vs Work)
            "arudha_analysis": self._calculate_arudha_padas(chart_data),
            
            # Planetary dignities (already calculated)
            "planetary_dignities": dignities_report,
            
            # Nakshatra positions
            "nakshatra_positions": nakshatra_calc.calculate_nakshatra_positions(),
            
            # Nakshatra career analysis
            "nakshatra_career_analysis": nakshatra_career.analyze_career_nakshatras(),
            
            # 10th house comprehensive analysis
            "tenth_house_comprehensive": tenth_house_analyzer.analyze_tenth_house(),
            
            # Career yogas
            "career_yogas": self._analyze_career_yogas(chart_data, ascendant_sign),
            
            # Career timing
            "career_timing": self._analyze_career_timing(birth_data, chart_data),
            
            # Job vs Business indicators
            "job_vs_business": self._analyze_job_vs_business(chart_data, ascendant_sign),
            
            # Career analysis instructions
            "career_analysis_instructions": {
                "critical_note": "Analyze ALL career houses: 10th (career), 6th (service), 7th (business), 2nd (income), 11th (gains)",
                "system_instruction": self.VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION
            }
        }
        
        return context
    
    def _get_nakshatra_career_hint(self, nakshatra_name: str) -> str:
        """Get career hint from nakshatra"""
        hints = {
            'Ashwini': 'Healing/Medical/Speed-based careers',
            'Bharani': 'Creative/Artistic Authority',
            'Krittika': 'Administrative/Military Authority',
            'Rohini': 'Creative/Growth-oriented fields',
            'Mrigashira': 'Research/Exploration careers',
            'Ardra': 'Technology/Innovation fields',
            'Punarvasu': 'Teaching/Restoration work',
            'Pushya': 'Service/Nurturing professions',
            'Ashlesha': 'Strategic/Psychological work',
            'Magha': 'Administration/Lineage-based roles',
            'Purva Phalguni': 'Creative/Entertainment fields',
            'Uttara Phalguni': 'Organization/Management',
            'Hasta': 'Skillful/Hands-on work',
            'Chitra': 'Architecture/Design careers',
            'Swati': 'Business/Independent work',
            'Vishakha': 'Goal-oriented/Competitive fields',
            'Anuradha': 'Organization/Group work',
            'Jyeshtha': 'Senior/Protective roles',
            'Mula': 'Research/Investigation work',
            'Purva Ashadha': 'Invincible/Artistic fields',
            'Uttara Ashadha': 'Leadership/Permanent positions',
            'Shravana': 'Communication/Learning fields',
            'Dhanishta': 'Music/Finance careers',
            'Shatabhisha': 'Healing/Mystical work',
            'Purva Bhadrapada': 'Transformation/Spiritual work',
            'Uttara Bhadrapada': 'Deep research/Mysticism',
            'Revati': 'Guidance/Protection services'
        }
        return hints.get(nakshatra_name, 'Diverse career options')
    
    def _calculate_arudha_padas(self, chart_data: Dict) -> Dict[str, Any]:
        """Calculate Arudha Lagna (AL) and Rajya Pada (A10) for status analysis"""
        houses = chart_data.get('houses', [])
        planets = chart_data.get('planets', {})
        
        def calculate_pada(house_num: int) -> Dict[str, Any]:
            if house_num > len(houses):
                return {'sign': 'Unknown', 'interpretation': 'Unable to calculate'}
            
            # Get house sign and lord
            house_sign = houses[house_num - 1].get('sign', 0)
            lord = self.SIGN_LORDS.get(house_sign)
            
            if not lord or lord not in planets:
                return {'sign': self._get_sign_name(house_sign), 'interpretation': 'Lord not found'}
            
            # Get lord's sign
            lord_sign = planets[lord].get('sign', 0)
            
            # Calculate distance from house to lord
            dist = (lord_sign - house_sign) % 12
            if dist == 0:
                dist = 12  # Same sign convention
            
            # Count same distance from lord
            arudha_sign = (lord_sign + dist - 1) % 12
            
            # Jaimini exception: If pada falls in 1st or 7th from original house, move 10 signs
            pada_from_house = (arudha_sign - house_sign) % 12
            if pada_from_house == 0 or pada_from_house == 6:
                arudha_sign = (arudha_sign + 9) % 12
            
            return {
                'sign': arudha_sign,
                'sign_name': self._get_sign_name(arudha_sign),
                'lord': lord,
                'calculation': f'House {house_num} lord {lord} in sign {lord_sign}, distance {dist}'
            }
        
        al_data = calculate_pada(1)
        a10_data = calculate_pada(10)
        
        # Analyze planets in AL and A10
        al_planets = [p for p, data in planets.items() if data.get('sign') == al_data.get('sign')]
        a10_planets = [p for p, data in planets.items() if data.get('sign') == a10_data.get('sign')]
        
        return {
            'arudha_lagna_AL': {
                **al_data,
                'planets': al_planets,
                'significance': 'Public image, status, how world sees you'
            },
            'rajya_pada_A10': {
                **a10_data,
                'planets': a10_planets,
                'significance': 'Actual workplace, office environment, career reality'
            },
            'status_vs_work_analysis': self._analyze_al_vs_10th(al_data, a10_data, chart_data),
            'interpretation': 'AL shows status/fame, A10 shows actual work. Strong AL with weak 10th = fame without substance. Strong 10th with weak AL = hard work without recognition.'
        }
    
    def _analyze_al_vs_10th(self, al_data: Dict, a10_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze difference between status (AL) and work (10th house)"""
        planets = chart_data.get('planets', {})
        
        # Check benefics in AL
        al_benefics = [p for p in ['Jupiter', 'Venus', 'Mercury', 'Moon'] 
                       if p in planets and planets[p].get('sign') == al_data.get('sign')]
        
        # Check malefics in AL
        al_malefics = [p for p in ['Saturn', 'Mars', 'Sun', 'Rahu', 'Ketu'] 
                       if p in planets and planets[p].get('sign') == al_data.get('sign')]
        
        # Check 10th house strength
        tenth_house_sign = chart_data.get('houses', [])[9].get('sign', 0) if len(chart_data.get('houses', [])) > 9 else 0
        tenth_planets = [p for p, data in planets.items() if data.get('house') == 10]
        
        analysis = {
            'al_strength': 'Strong' if len(al_benefics) > len(al_malefics) else 'Weak',
            'al_benefics': al_benefics,
            'al_malefics': al_malefics,
            'tenth_house_planets': tenth_planets,
            'prediction': ''
        }
        
        # Generate prediction
        if len(al_benefics) > 0 and len(tenth_planets) > 0:
            analysis['prediction'] = 'Fame and recognition with substantial work - ideal combination'
        elif len(al_benefics) > 0 and len(tenth_planets) == 0:
            analysis['prediction'] = 'High status/fame but work may not match the image'
        elif len(al_benefics) == 0 and len(tenth_planets) > 0:
            analysis['prediction'] = 'Hard work without proportional recognition - delayed fame'
        else:
            analysis['prediction'] = 'Moderate status and work - steady career path'
        
        return analysis
    
    def _analyze_career_houses(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze all career-related houses"""
        
        career_houses = {
            "10th_house": self._analyze_house(10, chart_data, ascendant_sign),
            "6th_house": self._analyze_house(6, chart_data, ascendant_sign),
            "7th_house": self._analyze_house(7, chart_data, ascendant_sign),
            "2nd_house": self._analyze_house(2, chart_data, ascendant_sign),
            "11th_house": self._analyze_house(11, chart_data, ascendant_sign)
        }
        
        return career_houses
    
    def _analyze_house(self, house_num: int, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze a specific house for career"""
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
                'longitude': lord_data.get('longitude', 0),
                'strength': self._get_planet_strength(lord_data)
            }
        
        return {
            'sign': house_sign,
            'sign_name': self._get_sign_name(house_sign),
            'lord': house_lord,
            'lord_position': lord_position,
            'planets_in_house': planets_in_house,
            'planet_count': len(planets_in_house)
        }
    
    def _analyze_tenth_house(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Detailed 10th house analysis with nakshatra"""
        tenth_house = self._analyze_house(10, chart_data, ascendant_sign)
        
        # Add 10th lord nakshatra analysis
        lord = tenth_house.get('lord')
        if lord and lord in chart_data.get('planets', {}):
            lord_data = chart_data['planets'][lord]
            nakshatra_calc = NakshatraCalculator(None, chart_data)
            lord_nakshatra = nakshatra_calc._get_nakshatra_info(lord_data.get('longitude', 0))
            tenth_house['lord_nakshatra'] = lord_nakshatra
            tenth_house['career_nuance'] = f"10th Lord in {lord_nakshatra['name']} Nakshatra (ruled by {lord_nakshatra['lord']}) - {self._get_nakshatra_career_hint(lord_nakshatra['name'])}"
        
        tenth_house['career_significance'] = 'Primary career house - profession, reputation, authority'
        return tenth_house
    
    def _analyze_sixth_house(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """6th house analysis for service and employment"""
        
        sixth_house = self._analyze_house(6, chart_data, ascendant_sign)
        
        sixth_house['career_significance'] = 'Service, daily work, employment, subordinates, competition'
        sixth_house['interpretation'] = self._interpret_sixth_house(sixth_house, chart_data)
        
        return sixth_house
    
    def _analyze_seventh_house(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """7th house analysis for business and partnerships"""
        
        seventh_house = self._analyze_house(7, chart_data, ascendant_sign)
        
        seventh_house['career_significance'] = 'Business, partnerships, public dealings, contracts, trade'
        seventh_house['interpretation'] = self._interpret_seventh_house(seventh_house, chart_data)
        
        return seventh_house
    
    def _analyze_second_house(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """2nd house analysis for earned wealth"""
        
        second_house = self._analyze_house(2, chart_data, ascendant_sign)
        
        second_house['career_significance'] = 'Earned wealth, speech value, family business, financial security'
        second_house['interpretation'] = self._interpret_second_house(second_house, chart_data)
        
        return second_house
    
    def _analyze_eleventh_house(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """11th house analysis for gains and income"""
        
        eleventh_house = self._analyze_house(11, chart_data, ascendant_sign)
        
        eleventh_house['career_significance'] = 'Gains, income, large organizations, fulfillment of desires'
        eleventh_house['interpretation'] = self._interpret_eleventh_house(eleventh_house, chart_data)
        
        return eleventh_house
    
    def _analyze_saturn_for_career(self, chart_data: Dict, saturn_dignity: Dict = None) -> Dict[str, Any]:
        """Saturn as Karma Karaka analysis with dignity"""
        planets = chart_data.get('planets', {})
        if 'Saturn' not in planets:
            return {}
        
        saturn_data = planets['Saturn']
        
        # Use passed dignity or calculate if not provided
        if saturn_dignity is None:
            dignities_calc = PlanetaryDignitiesCalculator(chart_data)
            saturn_dignity = dignities_calc.calculate_planetary_dignities().get('Saturn', {})
        
        nakshatra_calc = NakshatraCalculator(None, chart_data)
        saturn_nakshatra = nakshatra_calc._get_nakshatra_info(saturn_data.get('longitude', 0))
        
        return {
            'house': saturn_data.get('house', 1),
            'sign': saturn_data.get('sign', 0),
            'sign_name': self._get_sign_name(saturn_data.get('sign', 0)),
            'dignity': saturn_dignity.get('dignity', 'neutral'),
            'retrograde': saturn_data.get('retrograde', False),
            'nakshatra': saturn_nakshatra,
            'career_significance': 'Natural career significator - discipline, hard work, longevity',
            'strength_multiplier': saturn_dignity.get('strength_multiplier', 1.0)
        }
    
    def _analyze_sun_for_career(self, chart_data: Dict) -> Dict[str, Any]:
        """Sun analysis for authority and government"""
        
        planets = chart_data.get('planets', {})
        if 'Sun' not in planets:
            return {}
        
        sun_data = planets['Sun']
        
        return {
            'house': sun_data.get('house', 1),
            'sign': sun_data.get('sign', 0),
            'sign_name': self._get_sign_name(sun_data.get('sign', 0)),
            'strength': self._get_planet_strength(sun_data),
            'career_significance': 'Authority, government positions, leadership, father\'s influence',
            'interpretation': self._interpret_sun_career(sun_data)
        }
    
    def _analyze_mercury_for_career(self, chart_data: Dict) -> Dict[str, Any]:
        """Mercury analysis for business and communication"""
        
        planets = chart_data.get('planets', {})
        if 'Mercury' not in planets:
            return {}
        
        mercury_data = planets['Mercury']
        
        return {
            'house': mercury_data.get('house', 1),
            'sign': mercury_data.get('sign', 0),
            'sign_name': self._get_sign_name(mercury_data.get('sign', 0)),
            'strength': self._get_planet_strength(mercury_data),
            'career_significance': 'Business, trade, communication, intellect, versatility',
            'interpretation': self._interpret_mercury_career(mercury_data)
        }
    
    def _analyze_amatyakaraka(self, chart_data: Dict, base_context: Dict) -> Dict[str, Any]:
        """Amatyakaraka career interpretation"""
        
        chara_karakas = base_context.get('chara_karakas', {})
        amatyakaraka = chara_karakas.get('Amatyakaraka', 'Unknown')
        
        if amatyakaraka == 'Unknown' or amatyakaraka not in chart_data.get('planets', {}):
            return {}
        
        amk_data = chart_data['planets'][amatyakaraka]
        
        return {
            'planet': amatyakaraka,
            'house': amk_data.get('house', 1),
            'sign': amk_data.get('sign', 0),
            'sign_name': self._get_sign_name(amk_data.get('sign', 0)),
            'career_significance': 'Jaimini professional significator - natural career path',
            'interpretation': self._interpret_amatyakaraka(amatyakaraka, amk_data)
        }
    
    def _analyze_d10_chart(self, chart_data: Dict) -> Dict[str, Any]:
        """Detailed D10 Dasamsa analysis"""
        
        divisional_calc = DivisionalChartCalculator(chart_data)
        d10_chart = divisional_calc.calculate_divisional_chart(10)
        
        if not d10_chart or 'planets' not in d10_chart:
            return {'analysis': 'D10 chart not available'}
        
        d10_planets = d10_chart['planets']
        
        # Analyze D10 10th house
        d10_ascendant = d10_chart.get('ascendant', 0)
        d10_asc_sign = int(d10_ascendant / 30)
        d10_tenth_sign = (d10_asc_sign + 9) % 12
        d10_tenth_lord = self.SIGN_LORDS.get(d10_tenth_sign, 'Unknown')
        
        return {
            'd10_ascendant_sign': self._get_sign_name(d10_asc_sign),
            'd10_tenth_lord': d10_tenth_lord,
            'd10_tenth_lord_position': self._get_planet_position_in_d10(d10_tenth_lord, d10_planets),
            'career_specialization': self._interpret_d10_specialization(d10_asc_sign, d10_tenth_lord, d10_planets)
        }
    
    def _analyze_career_yogas(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze career-specific yogas"""
        
        planets = chart_data.get('planets', {})
        
        # Dharma Karmadhipati Yoga (9th + 10th lords connection)
        ninth_sign = (ascendant_sign + 8) % 12
        tenth_sign = (ascendant_sign + 9) % 12
        ninth_lord = self.SIGN_LORDS.get(ninth_sign)
        tenth_lord = self.SIGN_LORDS.get(tenth_sign)
        
        dharma_karma_yoga = self._check_dharma_karma_yoga(ninth_lord, tenth_lord, planets)
        
        return {
            'dharma_karmadhipati_yoga': dharma_karma_yoga,
            'raj_yogas': 'Check base yogas for Raj Yogas',
            'career_yoga_strength': self._assess_career_yoga_strength(dharma_karma_yoga)
        }
    
    def _analyze_career_timing(self, birth_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze career timing from dashas"""
        
        from shared.dasha_calculator import DashaCalculator
        dasha_calc = DashaCalculator()
        current_dashas = dasha_calc.calculate_current_dashas(birth_data)
        
        return {
            'current_dashas': current_dashas,
            'career_timing_analysis': self._interpret_career_timing(current_dashas, chart_data)
        }
    
    def _analyze_job_vs_business(self, chart_data: Dict, ascendant_sign: int) -> Dict[str, Any]:
        """Analyze job vs business indicators"""
        
        planets = chart_data.get('planets', {})
        
        # Get 10th lord
        tenth_sign = (ascendant_sign + 9) % 12
        tenth_lord = self.SIGN_LORDS.get(tenth_sign)
        tenth_lord_house = planets.get(tenth_lord, {}).get('house', 1) if tenth_lord in planets else 1
        
        # Get 7th lord (business)
        seventh_sign = (ascendant_sign + 6) % 12
        seventh_lord = self.SIGN_LORDS.get(seventh_sign)
        
        # Job indicators
        job_score = 0
        if tenth_lord_house in [1, 4, 7, 10]:  # Kendra
            job_score += 2
        if planets.get('Sun', {}).get('house', 1) in [1, 10]:
            job_score += 1
        
        # Business indicators
        business_score = 0
        if tenth_lord_house in [7]:  # 7th house
            business_score += 2
        if planets.get('Mercury', {}).get('house', 1) in [1, 7, 10]:
            business_score += 1
        
        recommendation = 'Job' if job_score > business_score else 'Business' if business_score > job_score else 'Both'
        
        return {
            'job_score': job_score,
            'business_score': business_score,
            'recommendation': recommendation,
            'interpretation': self._interpret_job_vs_business(job_score, business_score, tenth_lord_house)
        }
    
    # Helper methods
    
    def _get_planet_strength(self, planet_data: Dict) -> str:
        """Get basic planet strength"""
        house = planet_data.get('house', 1)
        
        if house in [1, 4, 7, 10]:
            return 'Strong (Kendra)'
        elif house in [1, 5, 9]:
            return 'Strong (Trikona)'
        elif house in [6, 8, 12]:
            return 'Weak (Dusthana)'
        else:
            return 'Medium'
    
    def _get_sign_name(self, sign_num: int) -> str:
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num % 12]
    
    def _interpret_tenth_house(self, tenth_house: Dict, chart_data: Dict) -> str:
        """Interpret 10th house for career"""
        lord = tenth_house.get('lord', 'Unknown')
        lord_house = tenth_house.get('lord_position', {}).get('house', 1)
        planets = tenth_house.get('planets_in_house', [])
        
        interpretation = f"10th lord {lord} in {lord_house}th house"
        if planets:
            interpretation += f" with {', '.join(planets)} in 10th house"
        
        return interpretation
    
    def _interpret_sixth_house(self, sixth_house: Dict, chart_data: Dict) -> str:
        """Interpret 6th house for service"""
        lord = sixth_house.get('lord', 'Unknown')
        planets = sixth_house.get('planets_in_house', [])
        
        if planets:
            return f"Strong service orientation with {', '.join(planets)} in 6th house"
        return f"6th lord {lord} indicates service nature"
    
    def _interpret_seventh_house(self, seventh_house: Dict, chart_data: Dict) -> str:
        """Interpret 7th house for business"""
        lord = seventh_house.get('lord', 'Unknown')
        planets = seventh_house.get('planets_in_house', [])
        
        if planets:
            return f"Strong business potential with {', '.join(planets)} in 7th house"
        return f"7th lord {lord} indicates partnership/business nature"
    
    def _interpret_second_house(self, second_house: Dict, chart_data: Dict) -> str:
        """Interpret 2nd house for wealth"""
        return "Earned wealth and speech value analysis"
    
    def _interpret_eleventh_house(self, eleventh_house: Dict, chart_data: Dict) -> str:
        """Interpret 11th house for gains"""
        return "Income and gains from career"
    
    def _interpret_saturn_career(self, saturn_data: Dict) -> str:
        """Interpret Saturn for career"""
        house = saturn_data.get('house', 1)
        return f"Saturn in {house}th house indicates disciplined career approach"
    
    def _interpret_sun_career(self, sun_data: Dict) -> str:
        """Interpret Sun for career"""
        house = sun_data.get('house', 1)
        return f"Sun in {house}th house indicates authority and leadership"
    
    def _interpret_mercury_career(self, mercury_data: Dict) -> str:
        """Interpret Mercury for career"""
        house = mercury_data.get('house', 1)
        return f"Mercury in {house}th house indicates business and communication skills"
    
    def _interpret_amatyakaraka(self, planet: str, amk_data: Dict) -> str:
        """Interpret Amatyakaraka"""
        return f"{planet} as Amatyakaraka indicates natural career path"
    
    def _get_planet_position_in_d10(self, planet: str, d10_planets: Dict) -> Dict:
        """Get planet position in D10"""
        if planet in d10_planets:
            return {
                'house': d10_planets[planet].get('house', 1),
                'sign': d10_planets[planet].get('sign', 0)
            }
        return {}
    
    def _interpret_d10_specialization(self, d10_asc_sign: int, d10_tenth_lord: str, d10_planets: Dict) -> str:
        """Interpret D10 for career specialization"""
        return f"D10 ascendant in {self._get_sign_name(d10_asc_sign)} with 10th lord {d10_tenth_lord}"
    
    def _check_dharma_karma_yoga(self, ninth_lord: str, tenth_lord: str, planets: Dict) -> Dict:
        """Check Dharma Karmadhipati Yoga"""
        if ninth_lord not in planets or tenth_lord not in planets:
            return {'present': False}
        
        ninth_house = planets[ninth_lord].get('house', 1)
        tenth_house = planets[tenth_lord].get('house', 1)
        
        # Check if they are in same house (conjunction)
        if ninth_house == tenth_house:
            return {
                'present': True,
                'type': 'Conjunction',
                'strength': 'Strong'
            }
        
        return {'present': False}
    
    def _assess_career_yoga_strength(self, dharma_karma_yoga: Dict) -> str:
        """Assess career yoga strength"""
        if dharma_karma_yoga.get('present'):
            return 'Strong career yogas present'
        return 'Moderate career potential'
    
    def _interpret_career_timing(self, current_dashas: Dict, chart_data: Dict) -> str:
        """Interpret career timing"""
        if not current_dashas:
            return 'No dasha data available'
        
        mahadasha = current_dashas.get('mahadasha', {}).get('planet', 'Unknown')
        return f"Current {mahadasha} Mahadasha career implications"
    
    def _interpret_job_vs_business(self, job_score: int, business_score: int, tenth_lord_house: int) -> str:
        """Interpret job vs business"""
        if job_score > business_score:
            return f"Job/Service recommended (10th lord in {tenth_lord_house}th house)"
        elif business_score > job_score:
            return "Business/Entrepreneurship recommended"
        return "Both job and business are viable options"
    
    @property
    def SIGN_LORDS(self):
        """Sign lordships"""
        return {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
