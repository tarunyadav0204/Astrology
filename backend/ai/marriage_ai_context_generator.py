import sys
import os
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.base_ai_context_generator import BaseAIContextGenerator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.yoga_calculator import YogaCalculator

class MarriageAIContextGenerator(BaseAIContextGenerator):
    """Marriage-specific AI context generator inheriting from base"""
    
    def build_marriage_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build complete marriage analysis context"""
        
        # Get base context first
        base_context = self.build_base_context(birth_data)
        
        # Add marriage-specific context
        marriage_context = self._build_marriage_specific_context(birth_data)
        
        # Combine contexts
        return {
            **base_context,
            **marriage_context
        }
    
    def _build_marriage_specific_context(self, birth_data: Dict) -> Dict[str, Any]:
        """Build marriage-specific context components"""
        
        # Get chart data from base context
        birth_hash = self._create_birth_hash(birth_data)
        chart_data = self.static_cache[birth_hash]['d1_chart']
        
        # Initialize marriage-specific calculators
        from types import SimpleNamespace
        birth_obj = SimpleNamespace(**birth_data)
        
        divisional_calc = DivisionalChartCalculator(chart_data)
        chara_karaka_calc = CharaKarakaCalculator(chart_data)
        yoga_calc = YogaCalculator(birth_obj, chart_data)
        
        context = {
            # Marriage charts (D9 for spouse, avoid D60 due to timing sensitivity)
            "marriage_charts": {
                "d9_navamsa": divisional_calc.calculate_divisional_chart(9)
            },
            
            # Marriage karakas
            "marriage_karakas": {
                "darakaraka": chara_karaka_calc.get_darakaraka(),
                "all_karakas": chara_karaka_calc.calculate_chara_karakas()
            },
            
            # Marriage yogas
            "marriage_yogas": yoga_calc.get_marriage_yogas_only(),
            
            # Marriage house analysis
            "marriage_houses": self._analyze_marriage_houses(chart_data),
            
            # Spouse characteristics
            "spouse_analysis": self._analyze_spouse_characteristics(chart_data),
            
            # Marriage timing
            "marriage_timing": self._analyze_marriage_timing(birth_data, chart_data),
            
            # Marriage analysis instructions
            "marriage_analysis_instructions": {
                "critical_note": "Use the 'future_marriage_transits' data provided. It contains pre-calculated activation years where Double Transit Theory supports marriage. Match these years with Dasha periods for precise timing.",
                "double_transit_theory": "Marriage requires BOTH Jupiter and Saturn to influence 7th house/lord simultaneously. Years marked as 'Double Transit Active' are most favorable."
            }
        }
        
        return context
    
    def _analyze_marriage_houses(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze marriage-related houses"""
        planets = chart_data.get('planets', {})
        
        marriage_houses = {
            "7th_house": self._analyze_house(7, chart_data),
            "2nd_house": self._analyze_house(2, chart_data),
            "4th_house": self._analyze_house(4, chart_data),
            "5th_house": self._analyze_house(5, chart_data),
            "8th_house": self._analyze_house(8, chart_data),
            "11th_house": self._analyze_house(11, chart_data),
            "12th_house": self._analyze_house(12, chart_data)
        }
        
        return marriage_houses
    
    def _analyze_house(self, house_num: int, chart_data: Dict) -> Dict[str, Any]:
        """Analyze a specific house for marriage"""
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
    
    def _analyze_spouse_characteristics(self, chart_data: Dict) -> Dict[str, Any]:
        """Analyze spouse characteristics from 7th house and Navamsa"""
        planets = chart_data.get('planets', {})
        
        # 7th house analysis
        seventh_house = self._analyze_house(7, chart_data)
        
        # Venus analysis (natural karaka for marriage)
        venus_analysis = {}
        if 'Venus' in planets:
            venus_data = planets['Venus']
            venus_analysis = {
                'house': venus_data.get('house', 1),
                'sign': venus_data.get('sign', 0),
                'strength': self._get_planet_strength(venus_data),
                'aspects': self._get_planet_aspects('Venus', chart_data)
            }
        
        # Jupiter analysis (karaka for husband)
        jupiter_analysis = {}
        if 'Jupiter' in planets:
            jupiter_data = planets['Jupiter']
            jupiter_analysis = {
                'house': jupiter_data.get('house', 1),
                'sign': jupiter_data.get('sign', 0),
                'strength': self._get_planet_strength(jupiter_data),
                'aspects': self._get_planet_aspects('Jupiter', chart_data)
            }
        
        return {
            'seventh_house_analysis': seventh_house,
            'venus_analysis': venus_analysis,
            'jupiter_analysis': jupiter_analysis,
            'spouse_indicators': self._get_spouse_indicators(chart_data)
        }
    
    def _analyze_marriage_timing(self, birth_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze marriage timing indicators"""
        planets = chart_data.get('planets', {})
        
        # Get current dashas
        from shared.dasha_calculator import DashaCalculator
        dasha_calc = DashaCalculator()
        current_dashas = dasha_calc.calculate_current_dashas(birth_data)
        
        # Get 15-year marriage transit summary (single calculation)
        future_marriage_transits = self._get_marriage_transit_activations(birth_data, chart_data)
        
        # Marriage timing factors
        timing_factors = {
            'current_dashas': current_dashas,
            'future_marriage_transits': future_marriage_transits,
            'jupiter_saturn_transits': self._get_jupiter_transit_info(),
            'current_period_analysis': self._analyze_current_period_for_marriage(current_dashas, chart_data)
        }
        
        return timing_factors
    
    def _get_planet_strength(self, planet_data: Dict) -> str:
        """Get basic planet strength"""
        # Simplified strength calculation
        sign = planet_data.get('sign', 0)
        house = planet_data.get('house', 1)
        
        if house in [1, 4, 7, 10]:  # Kendra
            return 'Strong'
        elif house in [1, 5, 9]:  # Trikona
            return 'Strong'
        elif house in [6, 8, 12]:  # Dusthana
            return 'Weak'
        else:
            return 'Medium'
    
    def _get_planet_aspects(self, planet_name: str, chart_data: Dict) -> list:
        """Get houses aspected by planet"""
        from calculators.aspect_calculator import AspectCalculator
        aspect_calc = AspectCalculator(chart_data)
        
        aspected_houses = []
        for house_num in range(1, 13):
            aspecting_planets = aspect_calc.get_aspecting_planets(house_num)
            if planet_name in aspecting_planets:
                aspected_houses.append(house_num)
        
        return aspected_houses
    
    def _get_spouse_indicators(self, chart_data: Dict) -> Dict[str, Any]:
        """Get spouse characteristic indicators"""
        planets = chart_data.get('planets', {})
        
        # 7th house planets indicate spouse nature
        seventh_house_planets = []
        for planet, data in planets.items():
            if data.get('house', 1) == 7:
                seventh_house_planets.append(planet)
        
        # Count benefic vs malefic influence
        benefics = ['Venus', 'Jupiter', 'Mercury']
        malefics = ['Mars', 'Saturn', 'Sun', 'Rahu', 'Ketu']
        
        benefic_count = sum(1 for p in seventh_house_planets if p in benefics)
        malefic_count = sum(1 for p in seventh_house_planets if p in malefics)
        
        return {
            'planets_in_seventh': seventh_house_planets,
            'seventh_house_influence': len(seventh_house_planets),
            'benefic_influence': benefic_count,
            'malefic_influence': malefic_count,
            'overall_influence': 'Positive' if benefic_count > malefic_count else 'Challenging' if malefic_count > benefic_count else 'Neutral'
        }
    
    def _analyze_marriage_significance(self, transit_planet: str, natal_planet: str, natal_house: int, dasha_periods: list) -> str:
        """Analyze marriage significance of transit activation"""
        # Marriage-relevant factors
        marriage_planets = ['Venus', 'Jupiter']
        marriage_houses = [1, 2, 4, 5, 7, 8, 11, 12]
        
        significance_score = 0
        
        # Transit planet relevance
        if transit_planet in marriage_planets:
            significance_score += 2
        elif transit_planet in ['Saturn']:  # Saturn for timing
            significance_score += 1
        
        # Natal house relevance
        if natal_house == 7:  # Primary marriage house
            significance_score += 3
        elif natal_house in [1, 2, 4, 5, 8, 11, 12]:  # Secondary marriage houses
            significance_score += 1
        
        # Dasha correlation
        for period in dasha_periods:
            active_planets = [
                period.get('mahadasha'),
                period.get('antardasha'),
                period.get('pratyantardasha')
            ]
            
            if transit_planet in active_planets or natal_planet in active_planets:
                significance_score += 2
                break
        
        # Convert score to significance level
        if significance_score >= 5:
            return 'maximum'
        elif significance_score >= 3:
            return 'high'
        else:
            return 'moderate'
    
    def _get_jupiter_transit_info(self) -> Dict[str, Any]:
        """Get current Jupiter and Saturn positions for marriage timing"""
        from calculators.real_transit_calculator import RealTransitCalculator
        from datetime import datetime
        
        try:
            transit_calc = RealTransitCalculator()
            current_date = datetime.now()
            
            # Get current positions
            jupiter_longitude = transit_calc.get_planet_position(current_date, 'Jupiter')
            saturn_longitude = transit_calc.get_planet_position(current_date, 'Saturn')
            
            current_jupiter_sign = int(jupiter_longitude / 30) if jupiter_longitude else 0
            current_saturn_sign = int(saturn_longitude / 30) if saturn_longitude else 0
            
            sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
            
            return {
                'current_jupiter_sign': sign_names[current_jupiter_sign],
                'current_saturn_sign': sign_names[current_saturn_sign],
                'jupiter_longitude': jupiter_longitude,
                'saturn_longitude': saturn_longitude,
                'double_transit_theory': 'Marriage occurs when both Jupiter and Saturn influence 7th house/lord simultaneously'
            }
        except Exception as e:
            return {
                'error': f'Transit position error: {e}',
                'double_transit_theory': 'Marriage occurs when both Jupiter and Saturn influence 7th house/lord simultaneously'
            }
    
    def _get_marriage_transit_activations(self, birth_data: Dict, chart_data: Dict) -> str:
        """Get 15-year marriage transit summary WITH AGE FILTER"""
        from calculators.real_transit_calculator import RealTransitCalculator
        from datetime import date
        
        try:
            current_year = date.today().year
            end_year = current_year + 15
            
            # Calculate birth year for age logic
            dob_str = birth_data.get('date', '')  # Expects YYYY-MM-DD
            birth_year = int(dob_str.split('-')[0])
            
            # Get 7th house lord for Double Transit Theory
            houses = chart_data.get('houses', [])
            seventh_lord = 'Unknown'
            if len(houses) >= 7:
                seventh_sign = houses[6].get('sign', 0)
                seventh_lord = self.SIGN_LORDS.get(seventh_sign, 'Unknown')
            
            activation_summary = []
            transit_calc = RealTransitCalculator()
            
            for year in range(current_year, end_year + 1):
                # SOCIAL FILTER: Calculate age
                age_at_time = year - birth_year
                
                # Skip years where user is too young for marriage
                if age_at_time < 22:
                    continue
                
                activation_result = self._check_year_activation(year, chart_data, seventh_lord, transit_calc)
                
                if activation_result['score'] >= 0.5:  # Moderate to Strong only
                    summary = f"Year {year} (Age {age_at_time}): {activation_result['description']} (Strength: {activation_result['strength']})"
                    activation_summary.append(summary)
            
            if not activation_summary:
                return "No socially viable marriage windows detected in the next 15 years. (Early activations were filtered). Focus on Dasha."
            
            return "\n".join(activation_summary)
            
        except Exception as e:
            return f"Transit calculation error: {e}. Use Dasha analysis for timing."
    
    def _analyze_current_period_for_marriage(self, current_dashas: Dict, chart_data: Dict) -> Dict[str, Any]:
        """Analyze current dasha period for marriage prospects"""
        if not current_dashas:
            return {'analysis': 'No current dasha data available'}
        
        mahadasha = current_dashas.get('mahadasha', 'Unknown')
        antardasha = current_dashas.get('antardasha', 'Unknown')
        
        # Marriage-favorable planets
        marriage_planets = ['Venus', 'Jupiter']
        
        analysis = {
            'current_mahadasha': mahadasha,
            'current_antardasha': antardasha,
            'marriage_favorability': 'High' if mahadasha in marriage_planets or antardasha in marriage_planets else 'Medium',
            'recommendation': f'Current {mahadasha}-{antardasha} period analysis for marriage timing'
        }
        
        return analysis
    
    @property
    def SIGN_LORDS(self):
        """Sign lordships"""
        return {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    def _check_year_activation(self, year: int, chart_data: Dict, seventh_lord: str, transit_calc) -> Dict[str, Any]:
        """Check marriage activation strength for a specific year"""
        from datetime import datetime
        
        try:
            test_date = datetime(year, 6, 15)
            
            jup_pos = transit_calc.get_planet_position(test_date, 'Jupiter')
            sat_pos = transit_calc.get_planet_position(test_date, 'Saturn')
            
            if not jup_pos or not sat_pos:
                return {'score': 0, 'description': 'Transit data unavailable', 'strength': 'None'}
            
            jup_house = self._get_transit_house(jup_pos, chart_data)
            sat_house = self._get_transit_house(sat_pos, chart_data)
            
            details = []
            score = 0
            
            # Jupiter checks
            jup_active = False
            if jup_house == 7:
                jup_active = True
                details.append("Jupiter in 7th")
            elif self._planet_aspects_house(jup_house, 7, 'Jupiter'):
                jup_active = True
                details.append("Jupiter aspects 7th")
            elif self._influences_seventh_lord(jup_house, jup_pos, seventh_lord, chart_data, 'Jupiter'):
                jup_active = True
                details.append(f"Jupiter aspects 7th Lord ({seventh_lord})")
            
            # Saturn checks
            sat_active = False
            if sat_house == 7:
                sat_active = True
                details.append("Saturn in 7th")
            elif self._planet_aspects_house(sat_house, 7, 'Saturn'):
                sat_active = True
                details.append("Saturn aspects 7th")
            elif self._influences_seventh_lord(sat_house, sat_pos, seventh_lord, chart_data, 'Saturn'):
                sat_active = True
                details.append("Saturn aspects 7th Lord")
            
            # Scoring
            if jup_active and sat_active:
                score = 1.0
                strength = "Double Transit (High)"
            elif jup_active:
                score = 0.5
                strength = "Jupiter Only"
            elif sat_active:
                score = 0.3
                strength = "Saturn Only"
            else:
                strength = "None"
            
            return {'score': score, 'description': ', '.join(details), 'strength': strength}
            
        except Exception:
            return {'score': 0, 'description': 'Error', 'strength': 'None'}
    
    def _get_transit_house(self, planet_longitude: float, chart_data: Dict) -> int:
        """Get house number (1-12) for transiting planet relative to Ascendant"""
        ascendant = chart_data.get('ascendant', 0)
        relative = (planet_longitude - ascendant + 360) % 360
        return int(relative / 30) + 1
    
    def _planet_aspects_house(self, planet_house: int, target_house: int, planet_name: str) -> bool:
        """Check if planet at planet_house aspects target_house (Vedic inclusive counting)"""
        if planet_house == target_house:
            return True  # Conjunction
        
        # Calculate distance with Vedic inclusive counting
        distance = (target_house - planet_house + 12) % 12 + 1
        
        if planet_name == 'Jupiter':
            return distance in [5, 7, 9]
        elif planet_name == 'Saturn':
            return distance in [3, 7, 10]
        elif planet_name == 'Mars':
            return distance in [4, 7, 8]
        
        return distance == 7  # Default 7th aspect
    
    def _influences_seventh_lord(self, transit_house: int, transit_pos: float, seventh_lord: str, chart_data: Dict, planet_name: str) -> bool:
        """Check if transit planet influences 7th Lord (conjunction OR aspect)"""
        planets = chart_data.get('planets', {})
        if seventh_lord not in planets:
            return False
        
        lord_house = planets[seventh_lord].get('house', 1)
        
        # Check conjunction
        if transit_house == lord_house:
            return True
        
        # Check aspect
        return self._planet_aspects_house(transit_house, lord_house, planet_name)