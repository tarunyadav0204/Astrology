"""
Full Moon and New Moon (global events).
Uses Swiss Ephemeris: Sun–Moon elongation at noon UT; new moon ≈ 0°, full moon ≈ 180°.
"""
import logging
from datetime import date, timedelta
from typing import List

import swisseph as swe

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK

logger = logging.getLogger(__name__)

# Elongation bands: new moon 0° (0–15 or 345–360), full moon 180° (165–195)
NEW_MOON_MIN, NEW_MOON_MAX = 0.0, 15.0
NEW_MOON_ALT_MIN, NEW_MOON_ALT_MAX = 345.0, 360.0
FULL_MOON_MIN, FULL_MOON_MAX = 165.0, 195.0


def _in_new_moon_band(elongation: float) -> bool:
    return (NEW_MOON_MIN <= elongation <= NEW_MOON_MAX) or (
        NEW_MOON_ALT_MIN <= elongation <= NEW_MOON_ALT_MAX
    )


def _in_full_moon_band(elongation: float) -> bool:
    return FULL_MOON_MIN <= elongation <= FULL_MOON_MAX


class LunarPhaseTrigger(TriggerBase):
    """Emit one global nudge on the day of Full Moon or New Moon."""

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

        try:
            sun_today = swe.calc_ut(jd_today, swe.SUN, swe.FLG_SIDEREAL)
            moon_today = swe.calc_ut(jd_today, swe.MOON, swe.FLG_SIDEREAL)
            sun_prev = swe.calc_ut(jd_prev, swe.SUN, swe.FLG_SIDEREAL)
            moon_prev = swe.calc_ut(jd_prev, swe.MOON, swe.FLG_SIDEREAL)
            if not all([sun_today, moon_today, sun_prev, moon_prev]):
                return events

            elongation_today = (moon_today[0][0] - sun_today[0][0] + 360) % 360
            elongation_prev = (moon_prev[0][0] - sun_prev[0][0] + 360) % 360

            in_new_today = _in_new_moon_band(elongation_today)
            in_new_prev = _in_new_moon_band(elongation_prev)
            in_full_today = _in_full_moon_band(elongation_today)
            in_full_prev = _in_full_moon_band(elongation_prev)

            if in_new_today and not in_new_prev:
                events.append(
                    NudgeEvent(
                        trigger_id="lunar_phase",
                        user_ids=None,
                        params={
                            "phase": "new_moon",
                            "date": target_date.isoformat(),
                        },
                        title="New Moon today",
                        body="Today is New Moon (Amavasya). A good time for new beginnings. Ask in chat for a lunar insight.",
                        cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                        question=(
                            f"How will today's New Moon on {target_date.isoformat()} affect me personally, "
                            f"and how long will its effects last?"
                        ),
                        priority=1,
                    )
                )
            if in_full_today and not in_full_prev:
                events.append(
                    NudgeEvent(
                        trigger_id="lunar_phase",
                        user_ids=None,
                        params={
                            "phase": "full_moon",
                            "date": target_date.isoformat(),
                        },
                        title="Full Moon today",
                        body="Today is Full Moon (Purnima). A time of culmination and clarity. Ask in chat how it might affect you.",
                        cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                        question=(
                            f"How will today's Full Moon on {target_date.isoformat()} affect me personally, "
                            f"and how long will its effects last?"
                        ),
                        priority=1,
                    )
                )
        except Exception as e:
            logger.exception(
                "Lunar phase check failed for %s: %s", target_date, e,
                exc_info=True,
            )

        return events
