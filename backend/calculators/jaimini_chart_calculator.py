"""Reference charts based on the Atmakaraka's Navamsha sign.

The terminology is not uniform across Jaimini commentaries.  This calculator
therefore declares the convention it uses and returns structural charts only:

* Karakamsha reference: D1 grahas counted from the AK's D9 sign.
* Swamsha reference: D9 grahas counted from the AK's D9 sign.

It does not turn the sign alone into a prediction.
"""

from .base_calculator import BaseCalculator
from .divisional_chart_calculator import DivisionalChartCalculator
from .classical_jaimini import ClassicalJaiminiCalculator, JAIMINI_GRAHAS, SIGN_NAMES


class JaiminiChartCalculator(BaseCalculator):
    """Calculate auditable D1 and D9 reference frames from the AK's D9 sign."""

    SOURCE = "Jaimini Upadesa Sutras, Chapter 1, Pada 2 (Swamsha/Karakamsha section)"
    TERMINOLOGY_NOTE = (
        "This screen calls the D9 frame from the Atmakaraka's Navamsha sign Swamsha, "
        "and the D1 frame from the same sign Karakamsha. Commentarial terminology varies."
    )
    
    def __init__(self, chart_data, atmakaraka_planet=None, karaka_scheme="seven"):
        """
        Initialize with chart data and Atmakaraka planet
        
        Args:
            chart_data: D1 chart data with planetary positions
            atmakaraka_planet: Name of Atmakaraka planet (e.g., 'Saturn')
        """
        super().__init__(chart_data)
        self.atmakaraka_planet = atmakaraka_planet
        if karaka_scheme not in {"seven", "eight"}:
            raise ValueError("karaka_scheme must be 'seven' or 'eight'")
        self.karaka_scheme = karaka_scheme
        self.divisional_calc = DivisionalChartCalculator(chart_data)

    def _foundation(self):
        d9_chart = self.divisional_calc.calculate_divisional_chart(9)['divisional_chart']
        worksheet = ClassicalJaiminiCalculator(self.chart_data, d9_chart).calculate()
        scheme = worksheet['karaka_schemes'][self.karaka_scheme]
        calculated_atmakaraka = scheme['atmakaraka']
        if self.atmakaraka_planet and self.atmakaraka_planet != calculated_atmakaraka:
            raise ValueError(
                f"Atmakaraka mismatch: received {self.atmakaraka_planet}, "
                f"but the {self.karaka_scheme}-karaka calculation gives {calculated_atmakaraka}"
            )
        self.atmakaraka_planet = calculated_atmakaraka
        reference = worksheet['svamsha_karakamsha'][self.karaka_scheme]
        return d9_chart, scheme, reference
    
    def calculate_karkamsa_chart(self):
        """
        Calculate the Karakamsha reference chart used by this application.
        
        Lagna: Atmakaraka's sign in D9
        Planets: D1 (Rashi) positions mapped to houses from Karkamsa lagna
        
        Returns:
            dict: Karkamsa chart with D1 planets relative to D9 AK sign
        """
        d9_chart, scheme, reference = self._foundation()
        karkamsa_sign = reference['sign_id']

        # Step 2: Map D1 planets to houses relative to Karkamsa lagna
        karkamsa_chart = self._recast_with_d1_planets(karkamsa_sign)
        
        return {
            'karkamsa_chart': karkamsa_chart,
            'karkamsa_sign': karkamsa_sign,
            'atmakaraka': self.atmakaraka_planet,
            'atmakaraka_degree_in_d9': d9_chart['planets'][self.atmakaraka_planet]['degree'],
            'karaka_scheme': self.karaka_scheme,
            'karaka_assignment_unambiguous': scheme['is_unambiguous'],
            'significance': "D1 grahas counted from the Atmakaraka's Navamsha sign",
            'calculation_basis': {
                'source': self.SOURCE,
                'reference_sign': SIGN_NAMES[karkamsa_sign],
                'reference_sign_id': karkamsa_sign,
                'planetary_frame': 'D1',
                'terminology_note': self.TERMINOLOGY_NOTE,
            },
        }
    
    def calculate_swamsa_chart(self):
        """
        Calculate the Swamsha reference chart used by this application.
        
        Lagna: Atmakaraka's sign in D9
        Planets: D9 (Navamsa) positions mapped to houses from Swamsa lagna
        
        Returns:
            dict: Swamsa chart with D9 planets relative to D9 AK sign
        """
        d9_chart, scheme, reference = self._foundation()
        swamsa_sign = reference['sign_id']

        # Step 2: Map D9 planets to houses relative to Swamsa lagna
        swamsa_chart = self._recast_with_d9_planets(d9_chart, swamsa_sign)
        
        return {
            'swamsa_chart': swamsa_chart,
            'swamsa_sign': swamsa_sign,
            'atmakaraka': self.atmakaraka_planet,
            'atmakaraka_degree_in_d9': d9_chart['planets'][self.atmakaraka_planet]['degree'],
            'karaka_scheme': self.karaka_scheme,
            'karaka_assignment_unambiguous': scheme['is_unambiguous'],
            'significance': "D9 grahas counted from the Atmakaraka's Navamsha sign",
            'calculation_basis': {
                'source': self.SOURCE,
                'reference_sign': SIGN_NAMES[swamsa_sign],
                'reference_sign_id': swamsa_sign,
                'planetary_frame': 'D9',
                'terminology_note': self.TERMINOLOGY_NOTE,
            },
        }
    
    def _recast_with_d1_planets(self, karkamsa_sign):
        """Map D1 planets to houses from Karkamsa lagna"""
        chart = {
            'ascendant_sign': karkamsa_sign,
            'ascendant': karkamsa_sign * 30,
            'chart_type': 'Karkamsa',
            'planets': {},
            'houses': [{'house_number': i+1, 'sign': (karkamsa_sign+i)%12} for i in range(12)],
            'ayanamsa': self.chart_data.get('ayanamsa', 0)
        }
        
        for planet, data in self.chart_data['planets'].items():
            if planet not in JAIMINI_GRAHAS:
                continue
            planet_sign = data['sign']
            house = ((planet_sign - karkamsa_sign) % 12) + 1
            chart['planets'][planet] = {
                'sign': planet_sign,
                'sign_name': SIGN_NAMES[planet_sign],
                'degree': data.get('degree', float(data['longitude']) % 30.0),
                'longitude': data['longitude'],
                'house': house,
                'retrograde': data.get('retrograde', False)
            }
        
        return chart
    
    def _recast_with_d9_planets(self, d9_chart, swamsa_sign):
        """Map D9 planets to houses from Swamsa lagna"""
        chart = {
            'ascendant_sign': swamsa_sign,
            'ascendant': swamsa_sign * 30,
            'chart_type': 'Swamsa',
            'planets': {},
            'houses': [{'house_number': i+1, 'sign': (swamsa_sign+i)%12} for i in range(12)],
            'ayanamsa': d9_chart.get('ayanamsa', 0)
        }
        
        for planet, data in d9_chart['planets'].items():
            if planet not in JAIMINI_GRAHAS:
                continue
            planet_sign = data['sign']
            house = ((planet_sign - swamsa_sign) % 12) + 1
            chart['planets'][planet] = {
                'sign': planet_sign,
                'sign_name': SIGN_NAMES[planet_sign],
                'degree': data.get('degree', float(data['longitude']) % 30.0),
                'longitude': data['longitude'],
                'house': house,
                'retrograde': data.get('retrograde', False)
            }
        
        return chart
    
    def get_karkamsa_interpretation(self, karkamsa_sign):
        """
        Get classical interpretation of Karkamsa sign
        
        Args:
            karkamsa_sign: Sign number (0-11)
            
        Returns:
            str: Classical interpretation
        """
        sign_name = SIGN_NAMES[int(karkamsa_sign) % 12]
        return f"Karakamsha reference: D1 grahas counted from {sign_name}, the Atmakaraka's D9 sign."
    
    def get_swamsa_interpretation(self, swamsa_sign):
        """
        Get classical interpretation of Swamsa sign
        
        Args:
            swamsa_sign: Sign number (0-11)
            
        Returns:
            str: Classical interpretation
        """
        sign_name = SIGN_NAMES[int(swamsa_sign) % 12]
        return f"Swamsha reference: D9 grahas counted from {sign_name}, the Atmakaraka's D9 sign."
