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

    def calculate_nav_nayak(self, ingress_datetime: datetime) -> Dict[str, Any]:
        """Compute Nav Nayak from Aries Ingress moment."""
        py_weekday = ingress_datetime.weekday()
        classical_weekday = (py_weekday + 1) % 7
        raja_lord = self.WEEKDAY_LORDS[classical_weekday]
        start_idx = self.NAYAK_ORDER.index(raja_lord) if raja_lord in self.NAYAK_ORDER else 0

        nav_nayak = {}
        for i in range(10):
            lord = self.NAYAK_ORDER[(start_idx + i) % 9]
            nav_nayak[self.NAYAK_TITLES[i]] = {
                'lord': lord,
                'title': self._get_title_label(self.NAYAK_TITLES[i]),
                'interpretation': self._get_interpretation(lord, self.NAYAK_TITLES[i])
            }

        return {
            'raja': nav_nayak['raja']['lord'],
            'nav_nayak': nav_nayak,
            'ingress_weekday': classical_weekday,
            'interpretation_summary': self._year_flavor_summary(nav_nayak['raja']['lord'])
        }

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
