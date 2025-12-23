from typing import Dict, Any, List

class SudarshanaChakraCalculator:
    """
    Calculates the Sudarshana Chakra (Triple Perspective).
    Analyzes the chart from three reference points:
    1. Lagna (Ascendant) - Physical Body / Reality
    2. Chandra (Moon) - Mind / Emotions
    3. Surya (Sun) - Soul / Authority
    """

    def __init__(self, chart_data: Dict[str, Any]):
        self.planets = chart_data.get('planets', {})
        self.ascendant = chart_data.get('ascendant', 0)
        self.moon_long = self.planets.get('Moon', {}).get('longitude', 0)
        self.sun_long = self.planets.get('Sun', {}).get('longitude', 0)

    def get_sudarshana_view(self) -> Dict[str, Any]:
        return {
            "lagna_chart": self._rotate_chart(self.ascendant),
            "chandra_lagna": self._rotate_chart(self.moon_long),
            "surya_lagna": self._rotate_chart(self.sun_long),
            "synthesis": self._synthesize_perspectives()
        }

    def _rotate_chart(self, new_ascendant_deg: float) -> Dict[str, int]:
        """
        Re-calculates house positions for all planets based on a new Ascendant.
        Uses Whole Sign Houses.
        """
        asc_sign = int(new_ascendant_deg / 30)
        rotated_houses = {}

        for planet, data in self.planets.items():
            p_long = data.get('longitude', 0)
            p_sign = int(p_long / 30)
            house = (p_sign - asc_sign) + 1
            if house <= 0:
                house += 12
            rotated_houses[planet] = house
            
        return rotated_houses

    def _synthesize_perspectives(self) -> Dict[str, str]:
        """Identifies patterns visible in all 3 charts."""
        insights = []
        
        lagna = self._rotate_chart(self.ascendant)
        moon = self._rotate_chart(self.moon_long)
        sun = self._rotate_chart(self.sun_long)
        
        bad_houses = [6, 8, 12]
        sat_l = lagna.get('Saturn')
        sat_m = moon.get('Saturn')
        sat_s = sun.get('Saturn')
        
        if sat_l in bad_houses and sat_m in bad_houses and sat_s in bad_houses:
            insights.append("Saturn is consistently difficult (in 6/8/12) from Body, Mind, and Soul.")
        
        return {"patterns": insights}
