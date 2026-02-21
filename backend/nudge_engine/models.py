"""Data models for nudge events."""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class NudgeEvent:
    """A single nudge event: who gets it, what message, and metadata."""

    trigger_id: str
    user_ids: Optional[List[int]]  # None = "all users" (expand later)
    params: Dict[str, Any]  # e.g. {"planet": "Mars", "sign": "Gemini"}
    title: str
    body: str
    cta_deep_link: str = "astroroshni://chat"
    priority: int = 0  # higher = preferred when deduping per user

    def __post_init__(self) -> None:
        if not self.trigger_id or not self.title or not self.body:
            raise ValueError("trigger_id, title, and body are required")
