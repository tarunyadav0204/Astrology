"""
Hindu festivals falling on target_date (global events).
Uses FestivalCalculator; default location India (lat/lon) and amanta calendar.
"""
import logging
from datetime import date
from typing import List

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK

logger = logging.getLogger(__name__)

# Default location for festival dates (India)
DEFAULT_LAT = 28.6139
DEFAULT_LON = 77.2090
DEFAULT_TZ = "Asia/Kolkata"


class FestivalTrigger(TriggerBase):
    """Emit one global nudge per major festival on target_date."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            from festivals.festival_calculator import FestivalCalculator
        except ImportError as e:
            logger.warning("Festival trigger skipped: %s", e)
            return events

        try:
            calculator = FestivalCalculator()
            festivals = calculator.find_festival_dates(
                target_date.year,
                target_date.month,
                DEFAULT_LAT,
                DEFAULT_LON,
                "amanta",
                DEFAULT_TZ,
            )
        except Exception as e:
            logger.exception(
                "Festival lookup failed for %s: %s", target_date, e,
                exc_info=True,
            )
            return events

        target_str = target_date.isoformat()
        for f in festivals:
            if f.get("date") != target_str:
                continue
            name = f.get("name") or "Festival"
            ftype = f.get("type") or "festival"
            # Prefer one nudge per day; major festivals get higher priority so dedupe picks them
            priority = 2 if ftype == "major_festival" else 1
            events.append(
                NudgeEvent(
                    trigger_id="festival",
                    user_ids=None,
                    params={
                        "festival_id": f.get("id"),
                        "name": name,
                        "date": target_str,
                        "type": ftype,
                    },
                    title=f"Today: {name}",
                    body=f"Today is {name}. Ask in chat for significance and remedies.",
                    cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                    question=(
                        f"What is the astrological significance of {name} falling today on {target_str} "
                        f"for me personally, and are there any recommended remedies?"
                    ),
                    priority=priority,
                )
            )

        return events
