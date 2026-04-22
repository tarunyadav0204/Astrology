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

    def _synthesize_perspectives(self) -> Dict[str, Any]:
        """Identify tri-perspective house patterns in a reusable compact form."""
        insights: List[str] = []

        lagna = self._rotate_chart(self.ascendant)
        moon = self._rotate_chart(self.moon_long)
        sun = self._rotate_chart(self.sun_long)

        perspective_maps = {
            "lagna": lagna,
            "moon": moon,
            "sun": sun,
        }
        benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
        malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
        supportive_houses = {1, 2, 4, 5, 7, 9, 10, 11}
        obstructive_houses = {6, 8, 12}

        house_rows = []
        for house in range(1, 13):
            present_in = []
            benefic_hits = 0
            malefic_hits = 0
            occupants: Dict[str, List[str]] = {}
            for label, pmap in perspective_maps.items():
                occ = sorted([planet for planet, h in pmap.items() if h == house])
                if occ:
                    present_in.append(label)
                    occupants[label] = occ
                benefic_hits += len([planet for planet in occ if planet in benefics])
                malefic_hits += len([planet for planet in occ if planet in malefics])

            agreement = len(present_in)
            if house in supportive_houses and agreement >= 2 and benefic_hits >= malefic_hits:
                band = "supportive"
            elif house in obstructive_houses and agreement >= 2 and malefic_hits >= benefic_hits:
                band = "challenging"
            elif agreement >= 2:
                band = "mixed"
            else:
                band = "weak"

            house_rows.append(
                {
                    "h": house,
                    "agree": agreement,
                    "in": present_in,
                    "ben": benefic_hits,
                    "mal": malefic_hits,
                    "band": band,
                    "occ": occupants,
                }
            )

        house_rows.sort(key=lambda row: (-int(row["agree"]), -int(row["ben"]), int(row["mal"]), int(row["h"])))

        bad_houses = [6, 8, 12]
        sat_l = lagna.get('Saturn')
        sat_m = moon.get('Saturn')
        sat_s = sun.get('Saturn')

        if sat_l in bad_houses and sat_m in bad_houses and sat_s in bad_houses:
            insights.append("Saturn is consistently difficult (in 6/8/12) from Body, Mind, and Soul.")

        strong_333 = [row["h"] for row in house_rows if row["agree"] == 3 and row["band"] == "supportive"][:4]
        hard_333 = [row["h"] for row in house_rows if row["agree"] == 3 and row["band"] == "challenging"][:4]
        if strong_333:
            insights.append(f"Strong 3/3 alignment on houses {strong_333}.")
        if hard_333:
            insights.append(f"Challenging 3/3 alignment on houses {hard_333}.")

        return {
            "patterns": insights,
            "house_agreement": house_rows,
            "dominant_houses": [row["h"] for row in house_rows[:5]],
        }
