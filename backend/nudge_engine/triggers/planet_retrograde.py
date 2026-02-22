"""
Planet turning retrograde or direct (station) — global events.
Uses Swiss Ephemeris: compare daily motion (speed in longitude) on target_date vs previous day.
"""
import logging
from datetime import date, timedelta
from typing import List

import swisseph as swe

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK

logger = logging.getLogger(__name__)

# Planets that go retrograde (inner + outer; exclude Sun/Moon)
PLANETS = (
    (swe.MERCURY, "Mercury"),
    (swe.VENUS, "Venus"),
    (swe.MARS, "Mars"),
    (swe.JUPITER, "Jupiter"),
    (swe.SATURN, "Saturn"),
)


class PlanetRetrogradeTrigger(TriggerBase):
    """Emit one global nudge when a planet turns retrograde or direct on target_date."""

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
                # pos[0][3] = speed in longitude (degrees per day)
                speed_today = pos_today[0][3]
                speed_prev = pos_prev[0][3]

                if speed_prev >= 0 and speed_today < 0:
                    events.append(
                        NudgeEvent(
                            trigger_id="planet_retrograde",
                            user_ids=None,
                            params={
                                "planet": planet_name,
                                "event": "retrograde",
                                "date": target_date.isoformat(),
                            },
                            title=f"{planet_name} turns retrograde",
                            body=f"{planet_name} is stationing retrograde today. Ask in chat how this might affect you.",
                            cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                            priority=1,
                        )
                    )
                elif speed_prev < 0 and speed_today >= 0:
                    events.append(
                        NudgeEvent(
                            trigger_id="planet_retrograde",
                            user_ids=None,
                            params={
                                "planet": planet_name,
                                "event": "direct",
                                "date": target_date.isoformat(),
                            },
                            title=f"{planet_name} turns direct",
                            body=f"{planet_name} is stationing direct today. Ask in chat what this shift may mean for you.",
                            cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                            priority=1,
                        )
                    )
            except Exception as e:
                logger.warning(
                    "Planet %s retrograde check failed for %s: %s",
                    planet_name, target_date, e,
                    exc_info=True,
                )
                continue

        return events
