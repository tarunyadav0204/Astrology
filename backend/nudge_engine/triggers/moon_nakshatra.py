"""
Moon changing nakshatra (daily lunar transit) — global events.
Uses Swiss Ephemeris with Lahiri ayanamsa and standard 27-nakshatra division.
"""
import logging
from datetime import date, timedelta
from typing import List

import swisseph as swe

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK
from event_prediction.config import NAKSHATRA_NAMES

logger = logging.getLogger(__name__)


class MoonNakshatraTrigger(TriggerBase):
    """Emit one global nudge when Moon enters a new nakshatra on target_date."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        except Exception as e:
            logger.exception("Swiss Ephemeris set_sid_mode failed: %s", e)
            return events

        try:
            # Use noon UT for both days for consistency
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
            # Swiss Ephemeris: sidereal Moon longitude
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            moon_today = swe.calc_ut(jd_today, swe.MOON, swe.FLG_SIDEREAL)
            moon_prev = swe.calc_ut(jd_prev, swe.MOON, swe.FLG_SIDEREAL)
            if not moon_today or not moon_prev:
                return events

            lon_today = moon_today[0][0] % 360.0
            lon_prev = moon_prev[0][0] % 360.0

            nak_span = 360.0 / 27.0  # 13°20'
            idx_today = int(lon_today / nak_span)
            idx_prev = int(lon_prev / nak_span)

            # Clamp just in case of rounding
            idx_today = max(0, min(26, idx_today))
            idx_prev = max(0, min(26, idx_prev))

            if idx_today != idx_prev:
                nak_name = NAKSHATRA_NAMES[idx_today]
                events.append(
                    NudgeEvent(
                        trigger_id="moon_nakshatra",
                        user_ids=None,
                        params={
                            "nakshatra_index": idx_today + 1,
                            "nakshatra_name": nak_name,
                            "date": target_date.isoformat(),
                        },
                        title=f"Moon enters {nak_name} nakshatra",
                        body=(
                            f"Today the Moon has moved into {nak_name} nakshatra. "
                            f"Ask in chat how this lunar transit colors your day."
                        ),
                        cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                        question=(
                            f"How will the Moon transiting through {nak_name} nakshatra today on "
                            f"{target_date.isoformat()} affect me personally, and how long will its effects last?"
                        ),
                        priority=1,
                    )
                )
        except Exception as e:
            logger.warning(
                "Moon nakshatra check failed for %s: %s",
                target_date,
                e,
                exc_info=True,
            )

        return events

