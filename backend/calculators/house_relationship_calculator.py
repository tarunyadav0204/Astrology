"""House relationship calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator

class HouseRelationshipCalculator(BaseCalculator):
    """Calculate house lord relationships and positions"""
    
    def analyze_house_lord(self, house_num):
        """Detailed house lord analysis - extracted from UniversalHouseAnalyzer"""
        house_sign = self.chart_data['houses'][house_num - 1]['sign']
        lord_planet = self.get_sign_lord(house_sign)
        
        if lord_planet not in self.chart_data['planets']:
            return {'status': 'Lord not found in chart'}
        
        lord_data = self.chart_data['planets'][lord_planet]
        lord_house = lord_data.get('house', 1)
        
        analysis = {
            'planet': lord_planet,
            'position_sign': lord_data['sign'],
            'position_house': lord_house,
            'degree': lord_data.get('degree', 0),
            'retrograde': lord_data.get('retrograde', False),
            'dignity': self.get_planet_dignity(lord_planet, lord_data['sign']),
            'house_relationship': self._get_house_relationship(house_num, lord_house)
        }
        
        return analysis
    
    def _get_house_relationship(self, house_num, lord_house):
        """Analyze house-lord relationship - extracted from UniversalHouseAnalyzer"""
        if lord_house == house_num:
            return 'Lord in own house - Very strong'
        elif lord_house in [1, 4, 7, 10]:
            return 'Lord in Kendra - Strong'
        elif lord_house in [1, 5, 9]:
            return 'Lord in Trikona - Excellent'
        elif lord_house in [6, 8, 12]:
            return 'Lord in Dusthana - Challenging'
        else:
            return 'Neutral position'