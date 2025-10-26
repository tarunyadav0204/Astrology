"""Aspect calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator

class AspectCalculator(BaseCalculator):
    """Calculate planetary aspects using real Vedic astrology rules"""
    
    def get_aspecting_planets(self, house_num):
        """Get planets aspecting the specified house - extracted from UniversalHouseAnalyzer"""
        aspecting = []
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        for planet, data in self.chart_data['planets'].items():
            planet_sign = data['sign']
            
            # 7th aspect (all planets)
            if (planet_sign + 6) % 12 == target_house_sign:
                aspecting.append(planet)
            
            # Special aspects
            if planet == 'Mars':
                # Mars aspects 4th and 8th houses from its position
                if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                    aspecting.append(planet)
            elif planet == 'Jupiter':
                # Jupiter aspects 5th and 9th houses from its position
                if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                    aspecting.append(planet)
            elif planet == 'Saturn':
                # Saturn aspects 3rd and 10th houses from its position
                if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                    aspecting.append(planet)
        
        return list(set(aspecting))  # Remove duplicates
    
    def get_aspect_strength(self, aspecting_planets):
        """Calculate aspect strength - extracted from UniversalHouseAnalyzer"""
        if not aspecting_planets:
            return 50
        
        total_strength = 0
        for planet in aspecting_planets:
            aspect_strength = 50
            
            if planet in self.NATURAL_BENEFICS:
                aspect_strength += 15
            elif planet in self.NATURAL_MALEFICS:
                aspect_strength -= 10
            
            # Special aspects
            if planet == 'Jupiter':
                aspect_strength += 20  # Jupiter's aspect is always beneficial
            elif planet == 'Saturn':
                aspect_strength -= 5   # Saturn's aspect can be restrictive
            
            total_strength += aspect_strength
        
        return max(0, min(100, total_strength / len(aspecting_planets)))