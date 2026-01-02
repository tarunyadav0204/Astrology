"""Yogi calculator extracted from main.py and YogiAnalyzer"""

import swisseph as swe
from .base_calculator import BaseCalculator
from utils.timezone_service import parse_timezone_offset, get_timezone_from_coordinates

class YogiCalculator(BaseCalculator):
    """Calculate Yogi, Avayogi, Dagdha Rashi and Tithi Shunya Rashi points"""
    
    def calculate_yogi_points(self, birth_data):
        """Calculate Yogi points - extracted from main.py calculate_yogi endpoint"""
        # Handle both dict and object input
        if isinstance(birth_data, dict):
            time_str = birth_data.get('time', '12:00')
            date_str = birth_data.get('date', '2000-01-01')
            latitude = birth_data.get('latitude', 0.0)
            longitude = birth_data.get('longitude', 0.0)
            timezone = birth_data.get('timezone', 'UTC+05:30')
        else:
            time_str = birth_data.time
            date_str = birth_data.date
            latitude = birth_data.latitude
            longitude = birth_data.longitude
            # Calculate timezone from coordinates if not provided
            if hasattr(birth_data, 'timezone'):
                timezone = birth_data.timezone
            else:
                timezone = get_timezone_from_coordinates(latitude, longitude)
        
        time_parts = time_str.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        # Get timezone offset using centralized service
        tz_offset = parse_timezone_offset(
            timezone,
            latitude,
            longitude
        )
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(date_str.split('-')[0]),
            int(date_str.split('-')[1]),
            int(date_str.split('-')[2]),
            utc_hour
        )
        
        # Set Lahiri Ayanamsa
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        
        sun_pos = swe.calc_ut(jd, 0, swe.FLG_SIDEREAL)[0][0]
        moon_pos = swe.calc_ut(jd, 1, swe.FLG_SIDEREAL)[0][0]
        
        # Calculate Yogi point - extracted from main.py
        yogi_point = (sun_pos + moon_pos) % 360
        yogi_sign = int(yogi_point / 30)
        yogi_degree = yogi_point % 30
        
        # Calculate Avayogi point - extracted from main.py
        avayogi_point = (yogi_point + 186.666667) % 360
        avayogi_sign = int(avayogi_point / 30)
        avayogi_degree = avayogi_point % 30
        
        # Calculate Dagdha Rashi - extracted from main.py
        dagdha_point = (avayogi_point + 12) % 360
        dagdha_sign = int(dagdha_point / 30)
        dagdha_degree = dagdha_point % 30
        
        # Calculate Tithi Shunya Rashi - extracted from main.py
        tithi_deg = (moon_pos - sun_pos) % 360
        tithi_num = int(tithi_deg / 12) + 1
        
        # Tithi Shunya Rashi calculation based on Tithi
        tithi_shunya_signs = {
            1: 11, 2: 5, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11,
            9: 0, 10: 1, 11: 2, 12: 3, 13: 4, 14: 5, 15: 6
        }
        
        tithi_shunya_sign = tithi_shunya_signs.get(tithi_num, 0)
        tithi_shunya_point = tithi_shunya_sign * 30 + 15  # Middle of the sign
        tithi_shunya_degree = 15.0
        
        return {
            "yogi": {
                "longitude": yogi_point,
                "sign": yogi_sign,
                "sign_name": self.SIGN_NAMES[yogi_sign],
                "degree": round(yogi_degree, 2),
                "lord": self.get_sign_lord(yogi_sign)
            },
            "avayogi": {
                "longitude": avayogi_point,
                "sign": avayogi_sign,
                "sign_name": self.SIGN_NAMES[avayogi_sign],
                "degree": round(avayogi_degree, 2),
                "lord": self.get_sign_lord(avayogi_sign)
            },
            "dagdha_rashi": {
                "longitude": dagdha_point,
                "sign": dagdha_sign,
                "sign_name": self.SIGN_NAMES[dagdha_sign],
                "degree": round(dagdha_degree, 2),
                "lord": self.get_sign_lord(dagdha_sign)
            },
            "tithi_shunya_rashi": {
                "longitude": tithi_shunya_point,
                "sign": tithi_shunya_sign,
                "sign_name": self.SIGN_NAMES[tithi_shunya_sign],
                "degree": round(tithi_shunya_degree, 2),
                "lord": self.get_sign_lord(tithi_shunya_sign)
            }
        }
    
    def analyze_yogi_impact_on_house(self, house_num, yogi_data):
        """Analyze Yogi impact on house - extracted from YogiAnalyzer"""
        impact_score = 50  # Neutral base
        
        yogi_lord = yogi_data['yogi']['lord']
        avayogi_lord = yogi_data['avayogi']['lord']
        dagdha_lord = yogi_data['dagdha_rashi']['lord']
        
        # Yogi lord impact (beneficial)
        yogi_impact = self._calculate_planet_impact_on_house(yogi_lord, house_num)
        impact_score += yogi_impact * 0.4  # 40% weight for Yogi
        
        # Avayogi lord impact (obstructive)
        avayogi_impact = self._calculate_planet_impact_on_house(avayogi_lord, house_num)
        impact_score -= avayogi_impact * 0.3  # 30% negative weight for Avayogi
        
        # Dagdha lord impact (destructive)
        dagdha_impact = self._calculate_planet_impact_on_house(dagdha_lord, house_num)
        impact_score -= dagdha_impact * 0.2  # 20% negative weight for Dagdha
        
        return {
            'total_impact': max(0, min(100, impact_score)),
            'yogi_lord': yogi_lord,
            'avayogi_lord': avayogi_lord,
            'dagdha_lord': dagdha_lord,
            'yogi_impact': yogi_impact,
            'avayogi_impact': avayogi_impact,
            'dagdha_impact': dagdha_impact
        }
    
    def _calculate_planet_impact_on_house(self, planet, house_num):
        """Calculate planet impact on house - extracted from YogiAnalyzer"""
        if planet not in self.chart_data['planets']:
            return 0
        
        planet_data = self.chart_data['planets'][planet]
        impact = 50  # Base impact
        
        # Planet's own strength
        if planet_data['sign'] == self.EXALTATION_SIGNS.get(planet):
            impact += 25
        elif planet_data['sign'] == self.DEBILITATION_SIGNS.get(planet):
            impact -= 25
        
        # Natural benefic/malefic
        if planet in self.NATURAL_BENEFICS:
            impact += 15
        elif planet in self.NATURAL_MALEFICS:
            impact -= 10
        
        # House position of the planet
        planet_house = planet_data.get('house', 1)
        if planet_house in [1, 4, 7, 10]:  # Kendra
            impact += 10
        elif planet_house in [1, 5, 9]:  # Trikona
            impact += 15
        elif planet_house in [6, 8, 12]:  # Dusthana
            impact -= 10
        
        # Aspect to target house
        if self._planet_aspects_house(planet, house_num):
            impact += 10
        
        return max(0, min(100, impact))
    
    def _planet_aspects_house(self, planet, house_num):
        """Check if planet aspects house - extracted from YogiAnalyzer"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # 7th aspect (all planets)
        if (planet_sign + 6) % 12 == target_house_sign:
            return True
        
        # Special aspects
        if planet == 'Mars':
            if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                return True
        elif planet == 'Jupiter':
            if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                return True
        elif planet == 'Saturn':
            if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                return True
        
        return False