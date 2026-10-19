"""Mrityu Bhaga (Fatal Degrees) Calculator"""

from .base_calculator import BaseCalculator
from .classical_mrityu_bhaga import JATAKA_PARIJATA_SARVARTHA, evaluate_mrityu_bhaga, analyze_chart_mrityu_bhaga

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
        """Expose the chart's complete calculation in the legacy chat schema."""
        canonical = analyze_chart_mrityu_bhaga(self.chart_data)
        results = {}
        affected = []
        for point, analysis in canonical['point_analysis'].items():
            results[point] = {
                **analysis,
                'sign_name': self.get_sign_name(analysis['sign']),
                'degree_in_sign': round(analysis['degree_in_sign'], 2),
                'mrityu_range': (analysis['degree_span_start'], analysis['degree_span_end']),
                'distance_from_mrityu': analysis['distance_from_span'],
                'health_implication': self._get_health_implication(point) if analysis['is_mrityu_bhaga'] else None,
            }
        for row in canonical['afflicted_points']:
            affected.append({
                **row,
                # Existing health, karma and remedy consumers expect this key,
                # including when the affected point is Lagna.
                'planet': row['point'],
                'sign': self.get_sign_name(row['sign']),
                'health_risk': self._get_health_implication(row['point']),
            })
        return {
            **canonical,
            'planet_analysis': results,
            'planets_in_mrityu': affected,
            'total_count': len(affected),
            'overall_risk': self._assess_overall_risk(affected),
        }

    def _get_health_implication(self, planet_name):
        """Keep the legacy field descriptive rather than inventing diagnoses."""
        return f'{planet_name} occupies its classical Mrityu Bhaga degree span.'

    def _assess_overall_risk(self, planets_in_mrityu):
        """A placement count is not a classical severity calculation."""
        count = len(planets_in_mrityu)
        return f'{count} natal point(s) in Mrityu Bhaga; assess with strength, lordship, aspects and timing.'
