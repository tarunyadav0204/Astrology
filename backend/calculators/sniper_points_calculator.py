from typing import Dict, Any
from calculators.base_calculator import BaseCalculator

class SniperPointsCalculator(BaseCalculator):
    """Calculator for Sniper Points - critical degrees that trigger sudden events"""
    
    def __init__(self, d1_chart: Dict, d3_chart: Dict, d9_chart: Dict):
        self.d1_chart = d1_chart
        self.d3_chart = d3_chart
        self.d9_chart = d9_chart
        
        self.sign_names = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]
        
        self.sign_lords = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon', 4: 'Sun', 5: 'Mercury',
            6: 'Venus', 7: 'Mars', 8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
    
    def calculate_kharesh_point(self) -> Dict[str, Any]:
        """Calculate 22nd Drekkana (Kharesh) - 8th sign from D3 ascendant"""
        try:
            d3_asc_long = self.d3_chart.get('ascendant', 0)
            d3_asc_sign = int(d3_asc_long / 30)
            
            drekkana_22_sign_idx = (d3_asc_sign + 7) % 12
            kharesh_lord = self.sign_lords[drekkana_22_sign_idx]
            
            lord_in_d1 = self.d1_chart['planets'].get(kharesh_lord, {})
            
            return {
                'point_name': '22nd Drekkana (Kharesh)',
                'danger_sign': self.sign_names[drekkana_22_sign_idx],
                'kharesh_lord': kharesh_lord,
                'lord_location_d1': f"{self.sign_names[lord_in_d1.get('sign', 0)]} ({lord_in_d1.get('house', 0)}th House)",
                'significance': 'Sensitive point for health and sudden events.',
                'transit_watch': f"Watch when Saturn/Rahu transits {self.sign_names[drekkana_22_sign_idx]} or crosses {kharesh_lord}."
            }
        except Exception as e:
            return {'error': f'Kharesh calculation failed: {e}'}
    
    def calculate_64th_navamsa(self) -> Dict[str, Any]:
        """Calculate 64th Navamsa - 4th sign from Moon in D9 chart"""
        try:
            moon_d9 = self.d9_chart['planets'].get('Moon', {})
            moon_d9_sign = moon_d9.get('sign')
            
            if moon_d9_sign is None:
                moon_d9_sign = int(moon_d9.get('longitude', 0) / 30)
            
            navamsa_64_sign_idx = (moon_d9_sign + 3) % 12
            navamsa_lord = self.sign_lords[navamsa_64_sign_idx]
            
            return {
                'point_name': '64th Navamsa',
                'danger_sign': self.sign_names[navamsa_64_sign_idx],
                'danger_lord': navamsa_lord,
                'significance': 'Critical point for mental stress and transformation.',
                'transit_watch': f"Watch when Saturn/Rahu transits {self.sign_names[navamsa_64_sign_idx]}."
            }
        except Exception as e:
            return {'error': f'64th Navamsa calculation failed: {e}'}
    
    def get_all_sniper_points(self) -> Dict[str, Any]:
        """Get all sniper points"""
        return {
            'kharesh': self.calculate_kharesh_point(),
            'navamsa_64th': self.calculate_64th_navamsa()
        }