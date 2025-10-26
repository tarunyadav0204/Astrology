"""Base calculator with common utilities extracted from existing code"""

class BaseCalculator:
    """Base class with common astrological constants and utilities"""
    
    SIGN_NAMES = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
                  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    
    SIGN_LORDS = {
        0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
        4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
        8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
    }
    
    NATURAL_BENEFICS = ['Jupiter', 'Venus', 'Moon', 'Mercury']
    NATURAL_MALEFICS = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu']
    
    EXALTATION_SIGNS = {
        'Sun': 0, 'Moon': 1, 'Mars': 9, 'Mercury': 5,
        'Jupiter': 3, 'Venus': 11, 'Saturn': 6
    }
    
    DEBILITATION_SIGNS = {
        'Sun': 6, 'Moon': 7, 'Mars': 3, 'Mercury': 11,
        'Jupiter': 9, 'Venus': 5, 'Saturn': 0
    }
    
    def __init__(self, chart_data):
        self.chart_data = chart_data
    
    def get_sign_name(self, sign_num):
        """Get sign name from number"""
        return self.SIGN_NAMES[sign_num] if 0 <= sign_num < 12 else 'Unknown'
    
    def get_sign_lord(self, sign_num):
        """Get lord of a sign"""
        return self.SIGN_LORDS.get(sign_num, 'Unknown')
    
    def is_benefic(self, planet):
        """Check if planet is natural benefic"""
        return planet in self.NATURAL_BENEFICS
    
    def is_malefic(self, planet):
        """Check if planet is natural malefic"""
        return planet in self.NATURAL_MALEFICS
    
    def get_planet_dignity(self, planet, sign):
        """Get planet's dignity in sign"""
        if sign == self.EXALTATION_SIGNS.get(planet):
            return 'Exalted'
        elif sign == self.DEBILITATION_SIGNS.get(planet):
            return 'Debilitated'
        elif sign in [s for s, l in self.SIGN_LORDS.items() if l == planet]:
            return 'Own Sign'
        else:
            return 'Neutral'