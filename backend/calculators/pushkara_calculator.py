"""
Pushkara Navamsa Calculator - Identifies blessed degrees
Planets in Pushkara Navamsas receive divine grace and miraculous outcomes
"""

from typing import Dict, Any, List

class PushkaraCalculator:
    
    PUSHKARA_MAP = {
        'fire': [7, 9],   # Libra, Sagittarius
        'earth': [3, 5],  # Pisces, Taurus
        'air': [6, 8],    # Pisces, Taurus
        'water': [1, 3]   # Virgo, Scorpio
    }
    
    ELEMENTS = {
        0: 'fire', 1: 'earth', 2: 'air', 3: 'water',
        4: 'fire', 5: 'earth', 6: 'air', 7: 'water',
        8: 'fire', 9: 'earth', 10: 'air', 11: 'water'
    }
    
    PUSHKARA_BHAGAS = {
        0: 21, 4: 14, 8: 24,  # Fire
        1: 14, 5: 24, 9: 21,  # Earth
        2: 21, 6: 14, 10: 24, # Air
        3: 7,  7: 11, 11: 23  # Water
    }
    
    def analyze_chart(self, chart_data: Dict[str, Any], ascendant_sign: int) -> Dict[str, Any]:
        """Analyze all planets for Pushkara Navamsa status"""
        planets = chart_data.get('planets', {})
        pushkara_planets = []
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Rahu', 'Ketu']:
                continue
            
            d1_sign = planet_data.get('sign', 0)
            d1_longitude = planet_data.get('longitude', 0)
            
            result = self._analyze_planet(planet_name, d1_sign, d1_longitude, ascendant_sign)
            
            if result['is_pushkara_navamsa'] or result['is_pushkara_bhaga']:
                pushkara_planets.append(result)
        
        return {
            'total_pushkara_planets': len(pushkara_planets),
            'pushkara_planets': pushkara_planets,
            'has_pushkara': len(pushkara_planets) > 0
        }
    
    def _analyze_planet(self, planet_name: str, d1_sign: int, d1_longitude: float, ascendant_sign: int) -> Dict[str, Any]:
        """Calculate Pushkara status for a single planet"""
        degree_in_sign = d1_longitude % 30
        navamsa_no = int(degree_in_sign / (30/9)) + 1
        element = self.ELEMENTS.get(d1_sign)
        
        is_pushkara_navamsa = navamsa_no in self.PUSHKARA_MAP[element]
        
        target_bhaga = self.PUSHKARA_BHAGAS.get(d1_sign)
        is_pushkara_bhaga = abs(degree_in_sign - target_bhaga) <= 1.0
        
        # Calculate house lordships
        ruled_houses = self._get_house_lordships(planet_name, ascendant_sign)
        
        return {
            "planet": planet_name,
            "navamsa_no": navamsa_no,
            "degree_in_sign": round(degree_in_sign, 2),
            "is_pushkara_navamsa": is_pushkara_navamsa,
            "is_pushkara_bhaga": is_pushkara_bhaga,
            "intensity": "Extreme" if is_pushkara_bhaga else ("High" if is_pushkara_navamsa else "Normal"),
            "description": "Degree of Miracles" if is_pushkara_bhaga else ("Nourishing degree" if is_pushkara_navamsa else "Standard degree"),
            "ruled_houses": ruled_houses
        }
    
    def _get_house_lordships(self, planet_name: str, ascendant_sign: int) -> List[int]:
        """Get houses ruled by planet"""
        sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        
        ruled_houses = []
        for house in range(1, 13):
            house_sign = (ascendant_sign + house - 1) % 12
            if sign_lords[house_sign] == planet_name:
                ruled_houses.append(house)
        
        return ruled_houses
