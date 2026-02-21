"""Base class for nudge triggers. All triggers implement get_events(date)."""
from abc import ABC, abstractmethod
from datetime import date
from typing import List

from .models import NudgeEvent


class TriggerBase(ABC):
    """Pluggable trigger: for a given date, returns zero or more nudge events."""

    @abstractmethod
    def get_events(self, target_date: date) -> List[NudgeEvent]:
        """
        Compute all nudge events for the given date.
        Return empty list if nothing to send.
        """
        pass
