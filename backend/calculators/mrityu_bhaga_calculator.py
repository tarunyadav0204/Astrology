"""Mrityu Bhaga (Fatal Degrees) Calculator"""

from .base_calculator import BaseCalculator

class MrityuBhagaCalculator(BaseCalculator):
    """Calculate Mrityu Bhaga (fatal degrees) for planets"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        
        # Mrityu Bhaga degrees for each planet in each sign
        # Format: {planet: {sign: degree_range}}
        self.MRITYU_BHAGA = {
            'Sun': {
                0: (19, 20), 1: (9, 10), 2: (13, 14), 3: (26, 27),
                4: (20, 21), 5: (12, 13), 6: (7, 8), 7: (14, 15),
                8: (13, 14), 9: (25, 26), 10: (4, 5), 11: (12, 13)
            },
            'Moon': {
                0: (26, 27), 1: (12, 13), 2: (13, 14), 3: (25, 26),
                4: (24, 25), 5: (11, 12), 6: (26, 27), 7: (14, 15),
                8: (13, 14), 9: (24, 25), 10: (5, 6), 11: (12, 13)
            },
            'Mars': {
                0: (27, 28), 1: (26, 27), 2: (23, 24), 3: (27, 28),
                4: (20, 21), 5: (23, 24), 6: (27, 28), 7: (14, 15),
                8: (13, 14), 9: (26, 27), 10: (20, 21), 11: (18, 19)
            },
            'Mercury': {
                0: (15, 16), 1: (14, 15), 2: (13, 14), 3: (12, 13),
                4: (25, 26), 5: (15, 16), 6: (15, 16), 7: (14, 15),
                8: (13, 14), 9: (13, 14), 10: (12, 13), 11: (9, 10)
            },
            'Jupiter': {
                0: (13, 14), 1: (14, 15), 2: (7, 8), 3: (13, 14),
                4: (20, 21), 5: (16, 17), 6: (8, 9), 7: (14, 15),
                8: (13, 14), 9: (10, 11), 10: (20, 21), 11: (9, 10)
            },
            'Venus': {
                0: (28, 29), 1: (15, 16), 2: (8, 9), 3: (17, 18),
                4: (11, 12), 5: (21, 22), 6: (28, 29), 7: (14, 15),
                8: (13, 14), 9: (19, 20), 10: (27, 28), 11: (12, 13)
            },
            'Saturn': {
                0: (10, 11), 1: (26, 27), 2: (4, 5), 3: (4, 5),
                4: (20, 21), 5: (6, 7), 6: (21, 22), 7: (14, 15),
                8: (13, 14), 9: (20, 21), 10: (9, 10), 11: (25, 26)
            }
        }
    
    def check_mrityu_bhaga(self, planet_name, longitude):
        """Check if planet is in Mrityu Bhaga"""
        if planet_name not in self.MRITYU_BHAGA:
            return {
                'is_mrityu_bhaga': False,
                'reason': f'Mrityu Bhaga not applicable for {planet_name}'
            }
        
        sign = int(longitude / 30)
        degree_in_sign = longitude % 30
        
        if sign not in self.MRITYU_BHAGA[planet_name]:
            return {
                'is_mrityu_bhaga': False,
                'sign': sign,
                'degree_in_sign': degree_in_sign
            }
        
        mrityu_range = self.MRITYU_BHAGA[planet_name][sign]
        is_in_mrityu = mrityu_range[0] <= degree_in_sign <= mrityu_range[1]
        
        return {
            'is_mrityu_bhaga': is_in_mrityu,
            'sign': sign,
            'sign_name': self.get_sign_name(sign),
            'degree_in_sign': round(degree_in_sign, 2),
            'mrityu_range': mrityu_range,
            'distance_from_mrityu': self._calculate_distance(degree_in_sign, mrityu_range) if not is_in_mrityu else 0,
            'health_implication': self._get_health_implication(planet_name) if is_in_mrityu else None
        }
    
    def analyze_chart_mrityu_bhaga(self):
        """Analyze all planets for Mrityu Bhaga"""
        results = {}
        planets_in_mrityu = []
        
        for planet_name, planet_data in self.chart_data['planets'].items():
            if planet_name in ['Rahu', 'Ketu']:
                continue
            
            longitude = planet_data.get('longitude', 0)
            analysis = self.check_mrityu_bhaga(planet_name, longitude)
            results[planet_name] = analysis
            
            if analysis['is_mrityu_bhaga']:
                planets_in_mrityu.append({
                    'planet': planet_name,
                    'sign': analysis['sign_name'],
                    'degree': analysis['degree_in_sign'],
                    'health_risk': analysis['health_implication']
                })
        
        return {
            'planet_analysis': results,
            'planets_in_mrityu': planets_in_mrityu,
            'total_count': len(planets_in_mrityu),
            'overall_risk': self._assess_overall_risk(planets_in_mrityu)
        }
    
    def _calculate_distance(self, degree, mrityu_range):
        """Calculate distance from Mrityu Bhaga range"""
        if degree < mrityu_range[0]:
            return mrityu_range[0] - degree
        else:
            return degree - mrityu_range[1]
    
    def _get_health_implication(self, planet_name):
        """Get health implication for planet in Mrityu Bhaga"""
        implications = {
            'Sun': 'Heart problems, vitality issues, life force depletion',
            'Moon': 'Mental health crises, emotional instability, fluid imbalances',
            'Mars': 'Blood disorders, accidents, inflammatory diseases',
            'Mercury': 'Nervous breakdown, respiratory failure, communication disorders',
            'Jupiter': 'Liver failure, immune collapse, metabolic disorders',
            'Venus': 'Reproductive system failure, kidney problems, hormonal crises',
            'Saturn': 'Chronic disease culmination, bone/joint failure, terminal conditions'
        }
        return implications.get(planet_name, 'Serious health risk')
    
    def _assess_overall_risk(self, planets_in_mrityu):
        """Assess overall health risk from Mrityu Bhaga"""
        count = len(planets_in_mrityu)
        
        if count == 0:
            return 'No Mrityu Bhaga - Normal health risk'
        elif count == 1:
            return 'One planet in Mrityu Bhaga - Moderate health risk, requires preventive care'
        elif count == 2:
            return 'Two planets in Mrityu Bhaga - High health risk, immediate attention needed'
        else:
            return 'Multiple planets in Mrityu Bhaga - Critical health risk, urgent medical consultation required'
