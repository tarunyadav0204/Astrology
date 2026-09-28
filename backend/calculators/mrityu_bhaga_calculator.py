"""Mrityu Bhaga (Fatal Degrees) Calculator"""

from .base_calculator import BaseCalculator
from .classical_mrityu_bhaga import JATAKA_PARIJATA_SARVARTHA, evaluate_mrityu_bhaga

class MrityuBhagaCalculator(BaseCalculator):
    """Calculate Mrityu Bhaga (fatal degrees) for planets"""
    
    def __init__(self, chart_data):
        super().__init__(chart_data)
        
        self.MRITYU_BHAGA = {
            planet: {sign: (degree - 1, degree) for sign, degree in enumerate(degrees)}
            for planet, degrees in JATAKA_PARIJATA_SARVARTHA.items()
        }
    
    def check_mrityu_bhaga(self, planet_name, longitude):
        """Check if planet is in Mrityu Bhaga"""
        canonical = evaluate_mrityu_bhaga(planet_name, longitude)
        if not canonical.get('applicable'):
            return {
                'is_mrityu_bhaga': False,
                'reason': f'Mrityu Bhaga not applicable for {planet_name}'
            }
        sign = canonical['sign']
        degree_in_sign = canonical['degree_in_sign']
        mrityu_range = (canonical['degree_span_start'], canonical['degree_span_end'])
        is_in_mrityu = canonical['is_mrityu_bhaga']
        return {
            **canonical,
            'is_mrityu_bhaga': is_in_mrityu,
            'sign': sign,
            'sign_name': self.get_sign_name(sign),
            'degree_in_sign': round(degree_in_sign, 2),
            'mrityu_range': mrityu_range,
            'distance_from_mrityu': canonical['distance_from_span'],
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
