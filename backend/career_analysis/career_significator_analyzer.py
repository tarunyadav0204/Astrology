import swisseph as swe
from typing import Dict, List

class CareerSignificatorAnalyzer:
    def __init__(self, birth_data):
        self.birth_data = birth_data
        self.chart_data = None
        
        # Career significator planets and their fields
        self.significators = {
            'Sun': {
                'fields': ['Government', 'Leadership', 'Authority', 'Politics', 'Administration'],
                'strength_factor': 1.2
            },
            'Mercury': {
                'fields': ['Communication', 'Business', 'Writing', 'IT', 'Media', 'Trading'],
                'strength_factor': 1.1
            },
            'Mars': {
                'fields': ['Engineering', 'Military', 'Sports', 'Real Estate', 'Surgery'],
                'strength_factor': 1.0
            },
            'Jupiter': {
                'fields': ['Teaching', 'Law', 'Finance', 'Spirituality', 'Consulting'],
                'strength_factor': 1.3
            },
            'Venus': {
                'fields': ['Arts', 'Entertainment', 'Beauty', 'Luxury Goods', 'Fashion'],
                'strength_factor': 1.0
            },
            'Saturn': {
                'fields': ['Manufacturing', 'Service', 'Oil & Gas', 'Mining', 'Agriculture'],
                'strength_factor': 1.1
            }
        }
    
    async def analyze(self):
        """Analyze career significator planets"""
        # Calculate chart data
        self.chart_data = await self._calculate_chart()
        
        # Analyze each significator planet
        significator_analysis = []
        for planet in self.significators.keys():
            analysis = await self._analyze_planet(planet)
            significator_analysis.append(analysis)
        
        # Find dominant significator
        dominant = self._find_dominant_significator(significator_analysis)
        
        return {
            "significators": significator_analysis,
            "dominant_significator": dominant,
            "overall_analysis": self._get_overall_analysis(significator_analysis)
        }
    
    async def _analyze_planet(self, planet_name):
        """Analyze individual planet as career significator"""
        # Get planet position (reuse existing calculation)
        planet_data = await self._get_planet_position(planet_name)
        
        # Calculate planet strength
        strength = self._calculate_planet_strength(planet_name, planet_data)
        
        # Get interpretation
        interpretation = self._get_planet_interpretation(planet_name, planet_data, strength)
        
        return {
            "name": planet_name,
            "sign": self._get_sign_name(planet_data['sign']),
            "house": planet_data['house'],
            "degree": round(planet_data['degree'], 2),
            "retrograde": planet_data.get('retrograde', False),
            "strength": strength,
            "interpretation": interpretation,
            "career_fields": self.significators[planet_name]['fields']
        }
    
    async def _calculate_chart(self):
        """Calculate birth chart"""
        time_parts = self.birth_data.time.split(':')
        hour = float(time_parts[0]) + float(time_parts[1])/60
        
        if 6.0 <= self.birth_data.latitude <= 37.0 and 68.0 <= self.birth_data.longitude <= 97.0:
            tz_offset = 5.5
        else:
            tz_offset = 0
            if self.birth_data.timezone.startswith('UTC'):
                tz_str = self.birth_data.timezone[3:]
                if tz_str and ':' in tz_str:
                    sign = 1 if tz_str[0] == '+' else -1
                    parts = tz_str[1:].split(':')
                    tz_offset = sign * (float(parts[0]) + float(parts[1])/60)
        
        utc_hour = hour - tz_offset
        jd = swe.julday(
            int(self.birth_data.date.split('-')[0]),
            int(self.birth_data.date.split('-')[1]),
            int(self.birth_data.date.split('-')[2]),
            utc_hour
        )
        
        # Calculate ascendant
        houses_data = swe.houses(jd, self.birth_data.latitude, self.birth_data.longitude, b'P')
        ayanamsa = swe.get_ayanamsa_ut(jd)
        ascendant_tropical = houses_data[1][0]
        ascendant_sidereal = (ascendant_tropical - ayanamsa) % 360
        
        return {
            'ascendant': ascendant_sidereal,
            'ascendant_sign': int(ascendant_sidereal / 30),
            'jd': jd,
            'ayanamsa': ayanamsa
        }
    
    async def _get_planet_position(self, planet_name):
        """Get planet position using Swiss Ephemeris"""
        planet_numbers = {
            'Sun': 0, 'Moon': 1, 'Mars': 4, 'Mercury': 2,
            'Jupiter': 5, 'Venus': 3, 'Saturn': 6
        }
        
        planet_num = planet_numbers.get(planet_name)
        if planet_num is None:
            return {'sign': 0, 'house': 1, 'degree': 0.0, 'retrograde': False}
        
        jd = self.chart_data['jd']
        pos = swe.calc_ut(jd, planet_num, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        longitude = pos[0][0]
        speed = pos[0][3] if len(pos[0]) > 3 else 0.0
        
        sign = int(longitude / 30)
        degree = longitude % 30
        house = self._calculate_house_position(longitude)
        retrograde = speed < 0
        
        return {
            'sign': sign,
            'house': house,
            'degree': degree,
            'longitude': longitude,
            'retrograde': retrograde
        }
    
    def _calculate_house_position(self, longitude):
        """Calculate house position from longitude"""
        ascendant_sign = self.chart_data['ascendant_sign']
        planet_sign = int(longitude / 30)
        house = ((planet_sign - ascendant_sign) % 12) + 1
        return house
    
    def _calculate_planet_strength(self, planet_name, planet_data):
        """Calculate planet strength for career"""
        base_strength = 50
        
        # Own sign strength
        own_signs = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        if planet_data['sign'] in own_signs.get(planet_name, []):
            base_strength += 20
        
        # Exaltation signs
        exaltation_signs = {
            'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
            'Jupiter': 3, 'Venus': 11, 'Saturn': 6
        }
        
        if planet_data['sign'] == exaltation_signs.get(planet_name):
            base_strength += 25
        
        # House position strength
        strong_houses = [1, 4, 7, 10]  # Kendra houses
        if planet_data['house'] in strong_houses:
            base_strength += 15
        
        # Career houses (2, 6, 10, 11)
        career_houses = [2, 6, 10, 11]
        if planet_data['house'] in career_houses:
            base_strength += 10
        
        # Retrograde consideration
        if planet_data.get('retrograde') and planet_name not in ['Sun', 'Moon']:
            base_strength -= 5
        
        # Apply significator factor
        base_strength *= self.significators[planet_name]['strength_factor']
        
        if base_strength >= 80:
            return "High"
        elif base_strength >= 60:
            return "Medium"
        else:
            return "Low"
    
    def _get_planet_interpretation(self, planet_name, planet_data, strength):
        """Get planet interpretation for career"""
        interpretations = {
            'Sun': {
                'High': "Excellent potential for leadership roles and government positions. Natural authority and administrative skills.",
                'Medium': "Good leadership qualities with potential for management roles. Steady career growth expected.",
                'Low': "Leadership skills need development. Focus on building confidence and authority."
            },
            'Mercury': {
                'High': "Outstanding communication skills perfect for business, writing, and IT careers. Quick learning ability.",
                'Medium': "Good analytical and communication skills. Suitable for business and technical fields.",
                'Low': "Communication skills need improvement. Focus on learning and skill development."
            },
            'Jupiter': {
                'High': "Excellent for teaching, law, finance, and advisory roles. Natural wisdom and guidance ability.",
                'Medium': "Good potential for educational and financial sectors. Steady growth in knowledge-based careers.",
                'Low': "Need to develop expertise and knowledge. Focus on continuous learning."
            }
        }
        
        return interpretations.get(planet_name, {}).get(strength, f"{planet_name} shows {strength.lower()} influence on career matters.")
    
    def _find_dominant_significator(self, significator_analysis):
        """Find the most dominant career significator"""
        # Sort by strength and house position
        sorted_planets = sorted(significator_analysis, 
                              key=lambda x: (x['strength'] == 'High', x['house'] in [1, 10, 11]), 
                              reverse=True)
        
        if sorted_planets:
            dominant = sorted_planets[0]
            return {
                "name": dominant['name'],
                "reason": f"Strongest career significator in {dominant['house']}th house with {dominant['strength']} strength",
                "recommended_fields": dominant['career_fields'][:3]  # Top 3 fields
            }
        
        return None
    
    def _get_overall_analysis(self, significator_analysis):
        """Get overall career significator analysis"""
        high_strength = [p for p in significator_analysis if p['strength'] == 'High']
        medium_strength = [p for p in significator_analysis if p['strength'] == 'Medium']
        
        if len(high_strength) >= 2:
            return "Multiple strong career significators indicate diverse career opportunities and success potential."
        elif len(high_strength) == 1:
            return f"Strong {high_strength[0]['name']} indicates focused career success in related fields."
        elif len(medium_strength) >= 2:
            return "Moderate career potential with opportunities for growth through skill development."
        else:
            return "Career success requires focused effort and skill development in chosen field."
    
    def _get_sign_name(self, sign_num):
        """Get sign name from number"""
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[sign_num % 12]