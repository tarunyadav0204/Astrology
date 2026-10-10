"""Nav Nayak: Ten Lords of the Year (Medini Jyotish).
The day and time of Aries Ingress determines King, Minister, Lord of Crops, etc.
"""

from typing import Dict, Any
from datetime import datetime


class NavNayakCalculator:
    """Calculates the 10 Lords of the Year from Aries Ingress datetime."""

    WEEKDAY_LORDS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    NAYAK_ORDER = ['Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury', 'Ketu', 'Venus']
    NAYAK_TITLES = [
        'raja', 'mantri', 'dhanapati', 'senapati', 'sandhivigrahika',
        'putra', 'ari', 'roga', 'dharma', 'karma'
    ]

    def calculate_nav_nayak(self, ingress_datetime: datetime, *, latitude=None, longitude=None) -> Dict[str, Any]:
        """Partial cabinet: Aries ingress determines Minister, NOT King.

        Other offices require independent calendrical anchors and a declared
        regional tradition. Preserve legacy keys, returning null for uncomputed
        roles instead of fabricating a nine-planet rotation.
        """
        from calculators.mundane.astronomy import utc_naive
        from utils.timezone_service import get_iana_timezone
        import pytz
        local = None
        if latitude is not None and longitude is not None:
            utc = pytz.UTC.localize(utc_naive(ingress_datetime))
            local = utc.astimezone(pytz.timezone(get_iana_timezone(latitude, longitude)))
        elif ingress_datetime.tzinfo is not None:
            local = ingress_datetime
        weekday = (local.weekday() + 1) % 7 if local else None
        minister = self.WEEKDAY_LORDS[weekday] if weekday is not None else None
        roles = {key: {'lord': None, 'title': self._get_title_label(key),
                       'available': False, 'interpretation': '',
                       'reason': 'Independent calendrical anchor and tradition not implemented'}
                 for key in self.NAYAK_TITLES}
        roles['mantri'].update(lord=minister, available=minister is not None,
            reason=None if minister else 'Location/timezone required',
            interpretation=self._get_interpretation(minister, 'mantri') if minister else '')
        return {'available': False, 'status': 'partial' if minister else 'unavailable',
                'raja': None, 'mantri': minister, 'nav_nayak': roles,
                'ingress_weekday': weekday,
                'interpretation_summary': 'Only the Aries-ingress Minister is computed. King and other offices are unresolved.',
                'method': 'aries_ingress_local_civil_weekday_minister_only',
                'source': 'https://www.drikpanchang.com/festivals/samvat-newyear/info/about-new-samvata-mantri-mandala.html'}

    def _get_title_label(self, key: str) -> str:
        labels = {
            'raja': 'King (Raja)', 'mantri': 'Minister (Mantri)',
            'dhanapati': 'Lord of Wealth (Dhanapati)', 'senapati': 'Commander (Senapati)',
            'sandhivigrahika': 'Enemy/Diplomat (Sandhivigrahika)', 'putra': 'Crops/Children (Putra)',
            'ari': 'Enemy (Ari)', 'roga': 'Disease (Roga)', 'dharma': 'Religion/Law (Dharma)', 'karma': 'Service (Karma)'
        }
        return labels.get(key, key)

    def _get_interpretation(self, lord: str, role: str) -> str:
        lord_traits = {
            'Sun': 'Government, authority, leadership, vitality',
            'Moon': 'Public mood, agriculture, water, masses',
            'Mars': 'Military, fires, aggression, conflict',
            'Mercury': 'Trade, communication, intellect',
            'Jupiter': 'Law, religion, expansion, prosperity',
            'Venus': 'Arts, luxury, diplomacy, comfort',
            'Saturn': 'Restriction, delays, labor, structures',
            'Rahu': 'Disruption, foreign influence, technology',
            'Ketu': 'Spiritual movements, epidemics, isolation'
        }
        return lord_traits.get(lord, 'General influence')

    def _year_flavor_summary(self, raja: str) -> str:
        flavors = {
            'Sun': 'Year marked by strong government, authority, and leadership focus',
            'Moon': 'Year focused on public mood, agriculture, and water-related events',
            'Mars': 'Year marked by fires, military activity, heat, and aggression',
            'Mercury': 'Year of trade, communication, and intellectual pursuits',
            'Jupiter': 'Year of expansion, law, religion, and prosperity',
            'Venus': 'Year of arts, luxury, diplomacy, and comfort',
            'Saturn': 'Year of restrictions, delays, hard work, and structural change',
            'Rahu': 'Year of disruption, foreign influence, and technology shocks',
            'Ketu': 'Year of spiritual movements, epidemics, or isolation'
        }
        return flavors.get(raja, 'Year influenced by the King planet')
