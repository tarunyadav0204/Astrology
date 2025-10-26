from .base_calculator import BaseCalculator

class ShadbalaCalculator(BaseCalculator):
    """Extract Shadbala calculation from shadbala.py"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        self.NATURAL_STRENGTHS = {
            'Sun': 60.0, 'Moon': 51.43, 'Mars': 17.14, 'Mercury': 25.71,
            'Jupiter': 34.29, 'Venus': 42.86, 'Saturn': 8.57
        }
        
        self.DIRECTIONAL_HOUSES = {
            'Sun': 10, 'Moon': 4, 'Mars': 10, 'Mercury': 1,
            'Jupiter': 1, 'Venus': 4, 'Saturn': 7
        }
        
        self.EXALTATION_DATA = {
            'Sun': {'sign': 1, 'degree': 10}, 'Moon': {'sign': 2, 'degree': 3},
            'Mars': {'sign': 10, 'degree': 28}, 'Mercury': {'sign': 6, 'degree': 15},
            'Jupiter': {'sign': 4, 'degree': 5}, 'Venus': {'sign': 12, 'degree': 27},
            'Saturn': {'sign': 7, 'degree': 20}
        }
    
    def calculate_shadbala(self):
        """Calculate complete Shadbala for all planets"""
        planets = self.chart_data.get('planets', {})
        results = {}
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Rahu', 'Ketu']:
                continue
            results[planet_name] = self._calculate_planet_shadbala(planet_name, planet_data, planets)
        
        return results
    
    def _calculate_planet_shadbala(self, planet, planet_data, all_planets):
        """Calculate six-fold strength for a planet"""
        sthana_bala = self._calculate_sthana_bala(planet, planet_data)
        dig_bala = self._calculate_dig_bala(planet, planet_data)
        kala_bala = self._calculate_kala_bala(planet, planet_data)
        chesta_bala = self._calculate_chesta_bala(planet, planet_data, all_planets)
        naisargika_bala = self.NATURAL_STRENGTHS.get(planet, 0)
        drik_bala = self._calculate_drik_bala(planet, planet_data, all_planets)
        
        total_points = sthana_bala + dig_bala + kala_bala + chesta_bala + naisargika_bala + drik_bala
        total_rupas = total_points / 60.0
        
        grade = "Excellent" if total_rupas >= 6 else "Good" if total_rupas >= 4.5 else "Average" if total_rupas >= 3 else "Weak"
        
        return {
            'total_points': round(total_points, 2),
            'total_rupas': round(total_rupas, 2),
            'grade': grade,
            'components': {
                'sthana_bala': round(sthana_bala, 2),
                'dig_bala': round(dig_bala, 2),
                'kala_bala': round(kala_bala, 2),
                'chesta_bala': round(chesta_bala, 2),
                'naisargika_bala': round(naisargika_bala, 2),
                'drik_bala': round(drik_bala, 2)
            }
        }
    
    def _calculate_sthana_bala(self, planet, planet_data):
        """Calculate positional strength"""
        uccha_bala = self._calculate_uccha_bala(planet, planet_data)
        kendra_bala = self._calculate_kendra_bala(planet_data)
        
        own_sign_bonus = 0
        current_sign = planet_data.get('sign', 0)
        own_signs = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        if planet in own_signs and current_sign in own_signs[planet]:
            own_sign_bonus = 30
        
        return uccha_bala + kendra_bala + own_sign_bonus
    
    def _calculate_uccha_bala(self, planet, planet_data):
        """Calculate exaltation strength"""
        if planet not in self.EXALTATION_DATA:
            return 30
        
        current_longitude = planet_data.get('longitude', 0)
        exalt_data = self.EXALTATION_DATA[planet]
        exalt_longitude = (exalt_data['sign'] - 1) * 30 + exalt_data['degree']
        
        diff = abs(current_longitude - exalt_longitude)
        if diff > 180:
            diff = 360 - diff
        
        strength = 60 * (1 - diff / 180)
        return max(0, strength)
    
    def _calculate_kendra_bala(self, planet_data):
        """Calculate angular house strength"""
        house = planet_data.get('house', 1)
        if house in [1, 4, 7, 10]:
            return 60
        elif house in [2, 5, 8, 11]:
            return 30
        else:
            return 15
    
    def _calculate_dig_bala(self, planet, planet_data):
        """Calculate directional strength"""
        if planet not in self.DIRECTIONAL_HOUSES:
            return 30
        
        current_house = planet_data.get('house', 1)
        directional_house = self.DIRECTIONAL_HOUSES[planet]
        
        if current_house == directional_house:
            return 60
        elif current_house == ((directional_house + 6 - 1) % 12 + 1):
            return 0
        else:
            distance = min(abs(current_house - directional_house), 12 - abs(current_house - directional_house))
            return max(15, 60 * (1 - distance / 6))
    
    def _calculate_kala_bala(self, planet, planet_data):
        """Calculate temporal strength"""
        birth_time = '12:00'  # Default time for now
        hour = int(birth_time.split(':')[0])
        is_day = 6 <= hour <= 18
        
        total_kala_bala = 0
        
        day_planets = ['Sun', 'Jupiter', 'Venus']
        night_planets = ['Moon', 'Mars', 'Saturn']
        
        if (planet in day_planets and is_day) or (planet in night_planets and not is_day):
            total_kala_bala += 60
        
        if planet == 'Moon':
            total_kala_bala += 30
        
        return min(total_kala_bala, 60)
    
    def _calculate_chesta_bala(self, planet, planet_data, all_planets):
        """Calculate motional strength"""
        if planet == 'Sun':
            return 60
        elif planet == 'Moon':
            sun_data = all_planets.get('Sun', {})
            moon_longitude = planet_data.get('longitude', 0)
            sun_longitude = sun_data.get('longitude', 0)
            
            distance = abs(moon_longitude - sun_longitude)
            if distance > 180:
                distance = 360 - distance
            
            return 60 * (distance / 180)
        else:
            is_retrograde = planet_data.get('retrograde', False)
            return 60 if is_retrograde else 15
    
    def _calculate_drik_bala(self, planet, planet_data, all_planets):
        """Calculate aspectual strength"""
        house = planet_data.get('house', 1)
        strength = 0
        
        benefics = ['Jupiter', 'Venus', 'Mercury']
        malefics = ['Mars', 'Saturn', 'Sun']
        
        for other_planet, other_data in all_planets.items():
            if other_planet == planet:
                continue
            
            other_house = other_data.get('house', 1)
            
            if abs(house - other_house) == 6 or (house + other_house) == 13:
                if other_planet in benefics:
                    strength += 10
                elif other_planet in malefics:
                    strength -= 10
        
        return max(-30, min(30, strength))