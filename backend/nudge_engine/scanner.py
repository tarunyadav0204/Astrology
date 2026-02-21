"""Run all registered triggers for a date and collect events."""
import logging
from datetime import date
from typing import List

from .models import NudgeEvent
from .trigger_registry import TRIGGERS

logger = logging.getLogger(__name__)


def scan(target_date: date) -> List[NudgeEvent]:
    """
    Run every registered trigger for target_date and return a flat list of events.
    Exceptions from individual triggers are caught and logged; others still run.
    """
    events: List[NudgeEvent] = []
    for trigger_id, trigger in TRIGGERS.items():
        try:
            trigger_events = trigger.get_events(target_date)
            events.extend(trigger_events)
        except Exception as e:
            logger.exception(
                "Trigger %s failed for date %s: %s", trigger_id, target_date, e
            )
    return events
