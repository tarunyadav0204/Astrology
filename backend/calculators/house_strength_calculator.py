"""Multi-factor weighted house strength calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator
from .strength_calculator import StrengthCalculator
from .aspect_calculator import AspectCalculator

class HouseStrengthCalculator(BaseCalculator):
    """Calculate comprehensive house strength using weighted factors"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        self.strength_calc = StrengthCalculator(chart_data)
        self.aspect_calc = AspectCalculator(chart_data)
    
    def calculate_house_strength(self, house_num):
        """Calculate comprehensive house strength - extracted from UniversalHouseAnalyzer"""
        strength_factors = {
            'lord_strength': self.strength_calc.calculate_lord_strength(house_num),
            'resident_planets_strength': self.strength_calc.calculate_resident_planets_strength(house_num),
            'aspects_strength': self._calculate_aspects_strength(house_num),
            'sign_strength': self._calculate_sign_strength(house_num),
            'positional_strength': self._calculate_positional_strength(house_num)
        }
        
        # Weighted calculation - exact weights from UniversalHouseAnalyzer
        total_strength = (
            strength_factors['lord_strength'] * 0.35 +
            strength_factors['resident_planets_strength'] * 0.25 +
            strength_factors['aspects_strength'] * 0.20 +
            strength_factors['sign_strength'] * 0.10 +
            strength_factors['positional_strength'] * 0.10
        )
        
        return {
            'total_strength': round(total_strength, 2),
            'factors': strength_factors,
            'interpretation': self._interpret_strength(total_strength),
            'grade': self._get_strength_grade(total_strength)
        }
    
    def _calculate_aspects_strength(self, house_num):
        """Calculate aspects strength - extracted from UniversalHouseAnalyzer"""
        aspecting_planets = self.aspect_calc.get_aspecting_planets(house_num)
        return self.aspect_calc.get_aspect_strength(aspecting_planets)
    
    def _calculate_sign_strength(self, house_num):
        """Calculate sign strength - extracted from UniversalHouseAnalyzer"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # Sign compatibility with house significations
        sign_strength = 50
        
        # House-sign compatibility from UniversalHouseAnalyzer
        house_sign_compatibility = {
            1: [0, 4, 8],      # Aries, Leo, Sagittarius good for 1st house
            2: [1, 5, 9],      # Taurus, Virgo, Capricorn good for 2nd house
            3: [2, 6, 10],     # Gemini, Libra, Aquarius good for 3rd house
            4: [3, 7, 11],     # Cancer, Scorpio, Pisces good for 4th house
            5: [0, 4, 8],      # Fire signs good for 5th house
            6: [5, 9],         # Earth signs good for 6th house
            7: [6, 1],         # Libra, Taurus good for 7th house
            8: [7, 3, 11],     # Water signs good for 8th house
            9: [8, 0, 4],      # Fire signs good for 9th house
            10: [9, 5, 1],     # Earth signs good for 10th house
            11: [10, 2, 6],    # Air signs good for 11th house
            12: [11, 3, 7]     # Water signs good for 12th house
        }
        
        if house_sign in house_sign_compatibility.get(house_num, []):
            sign_strength += 15
        
        return sign_strength
    
    def _calculate_positional_strength(self, house_num):
        """Calculate positional strength - extracted from UniversalHouseAnalyzer"""
        if house_num in [1, 4, 7, 10]:  # Kendra houses
            return 75
        elif house_num in [1, 5, 9]:    # Trikona houses
            return 80
        elif house_num in [3, 6, 11]:   # Upachaya houses
            return 65
        elif house_num in [6, 8, 12]:   # Dusthana houses
            return 35
        else:
            return 50
    
    def _interpret_strength(self, strength):
        """Interpret strength - extracted from UniversalHouseAnalyzer"""
        if strength >= 80:
            return "Excellent strength - Very favorable results expected"
        elif strength >= 65:
            return "Good strength - Favorable outcomes likely"
        elif strength >= 50:
            return "Average strength - Mixed results, effort needed"
        elif strength >= 35:
            return "Below average - Challenges present, remedies helpful"
        else:
            return "Weak - Significant challenges, strong remedies required"
    
    def _get_strength_grade(self, strength):
        """Get strength grade - extracted from UniversalHouseAnalyzer"""
        if strength >= 90:
            return 'A+'
        elif strength >= 80:
            return 'A'
        elif strength >= 70:
            return 'B+'
        elif strength >= 60:
            return 'B'
        elif strength >= 50:
            return 'C+'
        elif strength >= 40:
            return 'C'
        elif strength >= 30:
            return 'D'
        else:
            return 'F'