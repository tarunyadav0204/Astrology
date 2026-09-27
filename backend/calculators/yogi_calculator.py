"""Classical Yogi, Avayogi and related lunar-factor calculations.

Yogi and Avayogi are nakshatra lords, not sign lords.  The sign lord of
the Yoga Sphuta is the separate Duplicate Yogi.  Keep those identities
separate here so every consumer (including chat) receives the same facts.
"""

import math
import swisseph as swe
from .base_calculator import BaseCalculator
from .avayogi_policy import AVAYOGI_REVERSAL_HOUSES, avayogi_effect
from utils.timezone_service import parse_timezone_offset, get_timezone_from_coordinates

class YogiCalculator(BaseCalculator):
    """Calculate Yogi, Duplicate Yogi, Avayogi and Tithi Dagdha signs."""

    YOGI_OFFSET = 93.0 + (20.0 / 60.0)
    # Five nakshatras from Yoga Sphuta.  Some references use 186°40′
    # (fourteen nakshatras); that lands under the same Vimshottari lord but at
    # a different star.  66°40′ matches Iyer's sequence and Astro-Vision's
    # displayed Avayogi star as well as the planet.
    AVAYOGI_OFFSET = 66.0 + (40.0 / 60.0)
    NAKSHATRA_SPAN = 360.0 / 27.0
    NAKSHATRA_NAMES = (
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
        "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
        "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
        "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    )
    NAKSHATRA_LORDS = (
        "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter",
        "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars",
        "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
        "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    )

    # Seshadri Iyer's two-sign Tithi Dagdha table.  Values are zero-based
    # sidereal signs.  Purnima and Amavasya have no Dagdha signs.
    TITHI_DAGDHA_SIGNS = {
        1: (6, 9), 2: (8, 11), 3: (4, 9), 4: (1, 10), 5: (2, 5),
        6: (0, 4), 7: (3, 8), 8: (2, 5), 9: (4, 7), 10: (4, 7),
        11: (8, 11), 12: (6, 9), 13: (1, 4), 14: (11, 2, 5, 8),
        15: (),
    }

    @staticmethod
    def _normalize_birth_datetime(date_str, time_str):
        """Accept YYYY-MM-DD or ISO datetime from mobile/web clients."""
        date_raw = str(date_str or "2000-01-01").strip()
        time_raw = str(time_str or "12:00").strip()

        if "T" in date_raw:
            date_part, time_part = date_raw.split("T", 1)
            date_raw = date_part
            if time_part and (not time_raw or time_raw in ("12:00", "00:00")):
                time_raw = time_part

        date_only = date_raw.split("T")[0]
        year, month, day = (int(x) for x in date_only.split("-")[:3])

        time_clean = time_raw.replace("Z", "").split(".")[0]
        time_parts = time_clean.split(":")
        hour = float(time_parts[0])
        minute = float(time_parts[1]) if len(time_parts) > 1 else 0.0
        second = float(time_parts[2]) if len(time_parts) > 2 else 0.0
        hour += minute / 60.0 + second / 3600.0
        return year, month, day, hour
    
    @classmethod
    def _nakshatra_details(cls, longitude):
        normalized = float(longitude) % 360.0
        index = min(26, int(normalized / cls.NAKSHATRA_SPAN))
        return {
            "nakshatra_number": index + 1,
            "nakshatra_name": cls.NAKSHATRA_NAMES[index],
            "nakshatra_lord": cls.NAKSHATRA_LORDS[index],
        }

    @classmethod
    def _calculate_from_longitudes(cls, sun_pos, moon_pos):
        """Pure classical calculation, exposed separately for exact tests."""
        sun_pos = float(sun_pos) % 360.0
        moon_pos = float(moon_pos) % 360.0
        yogi_point = (sun_pos + moon_pos + cls.YOGI_OFFSET) % 360.0
        avayogi_point = (yogi_point + cls.AVAYOGI_OFFSET) % 360.0
        tithi_number = int(((moon_pos - sun_pos) % 360.0) // 12.0) + 1
        paksha_tithi_number = ((tithi_number - 1) % 15) + 1
        return {
            "sun_longitude": sun_pos,
            "moon_longitude": moon_pos,
            "yogi_point": yogi_point,
            "avayogi_point": avayogi_point,
            "tithi_number": tithi_number,
            "paksha_tithi_number": paksha_tithi_number,
            "tithi_dagdha_signs": list(cls.TITHI_DAGDHA_SIGNS[paksha_tithi_number]),
        }

    def _chart_longitude(self, planet):
        value = ((self.chart_data.get("planets") or {}).get(planet) or {}).get("longitude")
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value % 360.0 if math.isfinite(value) else None

    def calculate_yogi_points(self, birth_data):
        """Calculate the classical points using the chart's sidereal luminaries."""
        # Handle both dict and object input
        if isinstance(birth_data, dict):
            time_str = birth_data.get('time', '12:00')
            date_str = birth_data.get('date', '2000-01-01')
            latitude = birth_data.get('latitude', 0.0)
            longitude = birth_data.get('longitude', 0.0)
            timezone = birth_data.get('timezone', 'UTC+05:30')
        else:
            time_str = birth_data.time
            date_str = birth_data.date
            latitude = birth_data.latitude
            longitude = birth_data.longitude
            # Calculate timezone from coordinates if not provided
            if hasattr(birth_data, 'timezone'):
                timezone = birth_data.timezone
            else:
                timezone = get_timezone_from_coordinates(latitude, longitude)
        
        sun_pos = self._chart_longitude("Sun")
        moon_pos = self._chart_longitude("Moon")
        source = "chart_sidereal_longitudes"
        if sun_pos is None or moon_pos is None:
            year, month, day, local_hour = self._normalize_birth_datetime(date_str, time_str)
            tz_offset = parse_timezone_offset(
                timezone, latitude, longitude, for_date=date_str,
            )
            jd = swe.julday(year, month, day, local_hour - tz_offset)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
            source = "swiss_ephemeris_lahiri_fallback"

        calculated = self._calculate_from_longitudes(sun_pos, moon_pos)
        yogi_point = calculated["yogi_point"]
        yogi_sign = int(yogi_point / 30)
        yogi_degree = yogi_point % 30
        yogi_nakshatra = self._nakshatra_details(yogi_point)

        avayogi_point = calculated["avayogi_point"]
        avayogi_sign = int(avayogi_point / 30)
        avayogi_degree = avayogi_point % 30
        avayogi_nakshatra = self._nakshatra_details(avayogi_point)

        yogi_lord = yogi_nakshatra["nakshatra_lord"]
        duplicate_yogi_lord = self.get_sign_lord(yogi_sign)
        avayogi_lord = avayogi_nakshatra["nakshatra_lord"]

        dagdha_signs = calculated["tithi_dagdha_signs"]
        dagdha_rows = [
            {"sign": sign, "sign_name": self.SIGN_NAMES[sign], "lord": self.get_sign_lord(sign)}
            for sign in dagdha_signs
        ]
        dagdha_lords = {row["lord"] for row in dagdha_rows}
        avayogi_tithi_shunya_overlap = avayogi_lord in dagdha_lords
        avayogi_placement_house = (
            (self.chart_data.get('planets', {}).get(avayogi_lord) or {}).get('house')
        )
        avayogi_aspected_reversal_houses = [
            house for house in sorted(AVAYOGI_REVERSAL_HOUSES)
            if self._planet_aspects_house(avayogi_lord, house)
        ] if avayogi_lord in self.chart_data.get('planets', {}) else []
        avayogi_natal_effect = avayogi_effect(
            placement_house=avayogi_placement_house,
            tithi_shunya_overlap=avayogi_tithi_shunya_overlap,
        )

        return {
            "yogi": {
                "longitude": yogi_point,
                "sign": yogi_sign,
                "sign_name": self.SIGN_NAMES[yogi_sign],
                "degree": round(yogi_degree, 6),
                "lord": yogi_lord,
                "sign_lord": duplicate_yogi_lord,
                **yogi_nakshatra,
            },
            "duplicate_yogi": {
                "lord": duplicate_yogi_lord,
                "longitude": yogi_point,
                "sign": yogi_sign,
                "sign_name": self.SIGN_NAMES[yogi_sign],
                "degree": round(yogi_degree, 6),
                "derivation": "sign_lord_of_yogi_point",
            },
            "avayogi": {
                "longitude": avayogi_point,
                "sign": avayogi_sign,
                "sign_name": self.SIGN_NAMES[avayogi_sign],
                "degree": round(avayogi_degree, 6),
                "lord": avayogi_lord,
                "sign_lord": self.get_sign_lord(avayogi_sign),
                **avayogi_nakshatra,
            },
            "tithi_number": calculated["tithi_number"],
            "paksha_tithi_number": calculated["paksha_tithi_number"],
            "tithi_dagdha_rashis": dagdha_rows,
            # Compatibility aliases for older consumers.  There is no invented
            # longitude: a tithi may burn two (or, on Chaturdashi, four) signs.
            "dagdha_rashi": dagdha_rows[0] if dagdha_rows else None,
            "tithi_shunya_rashi": dagdha_rows[0] if dagdha_rows else None,
            "avayogi_tithi_shunya_overlap": {
                "is_active": avayogi_tithi_shunya_overlap,
                "planet": avayogi_lord if avayogi_tithi_shunya_overlap else None,
                "interpretation": (
                    "When the Avayogi planet is also the Tithi Shunya Adhipati, "
                    "its ordinary Avayogi obstruction is cancelled."
                    if avayogi_tithi_shunya_overlap
                    else None
                )
            },
            "avayogi_effect_policy": {
                "version": "1.0.0",
                "reversal_houses": sorted(AVAYOGI_REVERSAL_HOUSES),
                "placement_house": avayogi_placement_house,
                "aspected_reversal_houses": avayogi_aspected_reversal_houses,
                "natal_effect": avayogi_natal_effect,
                "rules": [
                    "Avayogi plus Tithi Shunya lord cancels the ordinary Avayogi penalty.",
                    "Avayogi placed in House 3, 6, 8 or 12 gives a supportive Avayogi contribution.",
                    "Avayogi aspecting House 3, 6, 8 or 12 gives a supportive Avayogi contribution to that house.",
                ],
            },
            "calculation_basis": {
                "version": "classical-yogi/2.0.0",
                "source": source,
                "ayanamsha": "lahiri_sidereal",
                "yogi_formula": "Sun + Moon + 93°20′",
                "avayogi_formula": "Yogi point + 66°40′ (five nakshatras)",
                "equivalent_avayogi_lord_offset": "186°40′ (same Vimshottari lord)",
                "tithi_dagdha_tradition": "seshadri_iyer_two_sign_table",
            },
        }
    
    def analyze_yogi_impact_on_house(self, house_num, yogi_data):
        """Analyze Yogi impact on house - extracted from YogiAnalyzer"""
        impact_score = 50  # Neutral base
        
        yogi_lord = yogi_data['yogi']['lord']
        avayogi_lord = yogi_data['avayogi']['lord']
        dagdha_lords = {
            row.get('lord') for row in yogi_data.get('tithi_dagdha_rashis', [])
            if row.get('lord')
        }
        if not dagdha_lords and yogi_data.get('dagdha_rashi'):
            dagdha_lords.add(yogi_data['dagdha_rashi'].get('lord'))
        dagdha_lords.discard(None)
        
        # Yogi lord impact (beneficial)
        yogi_impact = self._calculate_planet_impact_on_house(yogi_lord, house_num)
        impact_score += yogi_impact * 0.4  # 40% weight for Yogi
        
        # Avayogi contribution follows the shared cancellation/reversal policy.
        avayogi_impact = self._calculate_planet_impact_on_house(avayogi_lord, house_num)
        avayogi_planet = self.chart_data.get('planets', {}).get(avayogi_lord) or {}
        relation = (
            'occupant' if int(avayogi_planet.get('house') or 0) == int(house_num)
            else 'aspector' if self._planet_aspects_house(avayogi_lord, house_num)
            else 'house_lord'
        )
        avayogi_resolution = avayogi_effect(
            placement_house=avayogi_planet.get('house'),
            target_house=house_num,
            relation=relation,
            tithi_shunya_overlap=bool(
                (yogi_data.get('avayogi_tithi_shunya_overlap') or {}).get('is_active')
            ),
        )
        if avayogi_resolution['polarity'] == 'supportive':
            impact_score += avayogi_impact * 0.3
        elif avayogi_resolution['polarity'] == 'challenging':
            impact_score -= avayogi_impact * 0.3
        
        # Dagdha lord impact (destructive)
        dagdha_impacts = [
            self._calculate_planet_impact_on_house(lord, house_num)
            for lord in sorted(dagdha_lords)
        ]
        dagdha_impact = max(dagdha_impacts, default=0)
        impact_score -= dagdha_impact * 0.2  # 20% negative weight for Dagdha
        
        return {
            'total_impact': max(0, min(100, impact_score)),
            'yogi_lord': yogi_lord,
            'avayogi_lord': avayogi_lord,
            'dagdha_lords': sorted(dagdha_lords),
            'dagdha_lord': sorted(dagdha_lords)[0] if dagdha_lords else None,
            'yogi_impact': yogi_impact,
            'avayogi_impact': avayogi_impact,
            'avayogi_effect': avayogi_resolution,
            'dagdha_impact': dagdha_impact
        }
    
    def _calculate_planet_impact_on_house(self, planet, house_num):
        """Calculate planet impact on house - extracted from YogiAnalyzer"""
        if planet not in self.chart_data['planets']:
            return 0
        
        planet_data = self.chart_data['planets'][planet]
        impact = 50  # Base impact
        
        # Planet's own strength
        if planet_data['sign'] == self.EXALTATION_SIGNS.get(planet):
            impact += 25
        elif planet_data['sign'] == self.DEBILITATION_SIGNS.get(planet):
            impact -= 25
        
        # Natural benefic/malefic
        if planet in self.NATURAL_BENEFICS:
            impact += 15
        elif planet in self.NATURAL_MALEFICS:
            impact -= 10
        
        # House position of the planet
        planet_house = planet_data.get('house', 1)
        if planet_house in [1, 4, 7, 10]:  # Kendra
            impact += 10
        elif planet_house in [1, 5, 9]:  # Trikona
            impact += 15
        elif planet_house in [6, 8, 12]:  # Dusthana
            impact -= 10
        
        # Aspect to target house
        if self._planet_aspects_house(planet, house_num):
            impact += 10
        
        return max(0, min(100, impact))
    
    def _planet_aspects_house(self, planet, house_num):
        """Check if planet aspects house - extracted from YogiAnalyzer"""
        planet_sign = self.chart_data['planets'][planet]['sign']
        target_house_sign = self.chart_data['houses'][house_num - 1]['sign']
        
        # 7th aspect (all planets)
        if (planet_sign + 6) % 12 == target_house_sign:
            return True
        
        # Special aspects
        if planet == 'Mars':
            if (planet_sign + 3) % 12 == target_house_sign or (planet_sign + 7) % 12 == target_house_sign:
                return True
        elif planet == 'Jupiter':
            if (planet_sign + 4) % 12 == target_house_sign or (planet_sign + 8) % 12 == target_house_sign:
                return True
        elif planet == 'Saturn':
            if (planet_sign + 2) % 12 == target_house_sign or (planet_sign + 9) % 12 == target_house_sign:
                return True
        
        return False
