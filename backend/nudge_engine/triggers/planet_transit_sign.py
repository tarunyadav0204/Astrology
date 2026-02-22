"""
Planet transiting into a new sign (global event).
Uses Swiss Ephemeris with Lahiri ayanamsa, same logic as transits/routes.get_monthly_transits.
"""
import logging
from datetime import date, timedelta
from typing import List

import swisseph as swe

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK

logger = logging.getLogger(__name__)

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Same planets as transits/routes.get_monthly_transits (Sun, Mars, Mercury, Jupiter, Venus, Saturn)
PLANETS = (
    (swe.SUN, "Sun"),
    (swe.MARS, "Mars"),
    (swe.MERCURY, "Mercury"),
    (swe.JUPITER, "Jupiter"),
    (swe.VENUS, "Venus"),
    (swe.SATURN, "Saturn"),
)


class PlanetTransitSignTrigger(TriggerBase):
    """Emit one global nudge per planet that enters a new sign on target_date."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except Exception as e:
            logger.exception("Swiss Ephemeris set_sid_mode failed: %s", e)
            return events

        try:
            jd_today = swe.julday(
                target_date.year, target_date.month, target_date.day, 12.0
            )
            prev_date = target_date - timedelta(days=1)
            jd_prev = swe.julday(
                prev_date.year, prev_date.month, prev_date.day, 12.0
            )
        except Exception as e:
            logger.exception("Julian day calculation failed for %s: %s", target_date, e)
            return events

        for planet_id, planet_name in PLANETS:
            try:
                pos_today = swe.calc_ut(jd_today, planet_id, swe.FLG_SIDEREAL)
                pos_prev = swe.calc_ut(jd_prev, planet_id, swe.FLG_SIDEREAL)
                if not pos_today or not pos_prev:
                    continue
                lon_today = pos_today[0][0]
                lon_prev = pos_prev[0][0]
                sign_today = int(lon_today / 30) % 12
                sign_prev = int(lon_prev / 30) % 12
                if sign_today != sign_prev:
                    sign_name = SIGNS[sign_today]
                    events.append(
                        NudgeEvent(
                            trigger_id="planet_transit_sign",
                            user_ids=None,
                            params={
                                "planet": planet_name,
                                "sign": sign_name,
                                "date": target_date.isoformat(),
                            },
                            title=f"{planet_name} enters {sign_name}",
                            body=f"{planet_name} has moved into {sign_name}. Ask in chat how this transit might affect you.",
                            cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                            question=f"How does {planet_name} in {sign_name} affect me?",
                            priority=0,
                        )
                    )
            except Exception as e:
                logger.warning(
                    "Planet %s transit check failed for %s: %s",
                    planet_name, target_date, e,
                    exc_info=True,
                )
                continue

        return events
