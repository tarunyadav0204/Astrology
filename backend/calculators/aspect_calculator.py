"""Aspect calculator extracted from UniversalHouseAnalyzer"""

from .base_calculator import BaseCalculator
from .vedic_graha_drishti import planets_aspecting_house_sign


class AspectCalculator(BaseCalculator):
    """Calculate planetary aspects using real Vedic astrology rules (vedic_graha_drishti)."""

    def get_aspecting_planets(self, house_num):
        """Get planets aspecting the specified house (whole sign, Parāśara drishti)."""
        target_house_sign = self.chart_data["houses"][house_num - 1]["sign"]
        return planets_aspecting_house_sign(self.chart_data["planets"], target_house_sign)

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
            if planet == "Jupiter":
                aspect_strength += 20  # Jupiter's aspect is always beneficial
            elif planet == "Saturn":
                aspect_strength -= 5  # Saturn's aspect can be restrictive

            total_strength += aspect_strength

        return max(0, min(100, total_strength / len(aspecting_planets)))
