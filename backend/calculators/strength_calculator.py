"""Strength calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator

class StrengthCalculator(BaseCalculator):
    """Calculate various strength metrics using real Vedic formulas"""
    
    def calculate_lord_strength(self, house_num):
        """Calculate house lord strength - extracted from UniversalHouseAnalyzer"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        lord_planet = self.get_sign_lord(house_sign)
        
        if lord_planet not in self.chart_data['planets']:
            return 50
            
        lord_data = self.chart_data['planets'][lord_planet]
        strength = 50  # Base strength
        
        # Exaltation/Debilitation
        if lord_data['sign'] == self.EXALTATION_SIGNS.get(lord_planet):
            strength += 30
        elif lord_data['sign'] == self.DEBILITATION_SIGNS.get(lord_planet):
            strength -= 30
        
        # Own sign strength
        if lord_data['sign'] in [s for s, l in self.SIGN_LORDS.items() if l == lord_planet]:
            strength += 25
        
        # House position strength
        lord_house = lord_data.get('house', 1)
        if lord_house in [1, 4, 7, 10]:  # Kendra houses
            strength += 20
        elif lord_house in [1, 5, 9]:  # Trikona houses
            strength += 25
        elif lord_house in [6, 8, 12]:  # Dusthana houses
            strength -= 20
        
        # Retrograde consideration
        if lord_data.get('retrograde', False):
            strength += 5  # Retrograde can be beneficial in some cases
            
        return max(0, min(100, strength))
    
    def calculate_resident_planets_strength(self, house_num):
        """Calculate strength of planets in house - extracted from UniversalHouseAnalyzer"""
        resident_planets = self.get_planets_in_house(house_num)
        
        if not resident_planets:
            return 60  # Neutral if empty
        
        total_strength = 0
        for planet in resident_planets:
            planet_data = self.chart_data['planets'][planet]
            planet_strength = 50
            
            # Natural benefic/malefic
            if planet in self.NATURAL_BENEFICS:
                planet_strength += 15
            elif planet in self.NATURAL_MALEFICS:
                planet_strength -= 5
            
            # Exaltation/Debilitation
            if planet_data['sign'] == self.EXALTATION_SIGNS.get(planet):
                planet_strength += 25
            elif planet_data['sign'] == self.DEBILITATION_SIGNS.get(planet):
                planet_strength -= 25
            
            # Own sign
            if planet_data['sign'] in [s for s, l in self.SIGN_LORDS.items() if l == planet]:
                planet_strength += 20
            
            # House-specific planet effects
            planet_strength += self.get_planet_house_compatibility(planet, house_num)
            
            total_strength += planet_strength
        
        return max(0, min(100, total_strength / len(resident_planets)))
    
    def get_planets_in_house(self, house_num):
        """Get planets in house - extracted from UniversalHouseAnalyzer"""
        planets_in_house = []
        
        for planet, data in self.chart_data['planets'].items():
            if data.get('house') == house_num:
                planets_in_house.append(planet)
        
        return planets_in_house
    
    def get_planet_house_compatibility(self, planet, house_num):
        """Get compatibility score - extracted from UniversalHouseAnalyzer"""
        compatibility_matrix = {
            'Sun': {1: 20, 5: 15, 9: 15, 10: 20},
            'Moon': {1: 10, 4: 20, 11: 10},
            'Mars': {1: 15, 3: 15, 6: 20, 10: 15, 11: 10},
            'Mercury': {1: 10, 3: 15, 6: 10, 10: 15},
            'Jupiter': {1: 15, 2: 10, 5: 20, 9: 20, 11: 15},
            'Venus': {2: 15, 4: 10, 7: 20, 12: 10},
            'Saturn': {3: 10, 6: 15, 8: 10, 10: 15, 11: 20},
            'Rahu': {3: 10, 6: 15, 11: 15},
            'Ketu': {8: 10, 12: 15}
        }
        
        return compatibility_matrix.get(planet, {}).get(house_num, 0)