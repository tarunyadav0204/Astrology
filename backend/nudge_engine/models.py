"""Data models for nudge events."""
from dataclasses import asdict, dataclass
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
    question: Optional[str] = None  # optional; when user taps notification, prefill chat input with this
    priority: int = 0  # higher = preferred when deduping per user

    def __post_init__(self) -> None:
        if not self.trigger_id or not self.title or not self.body:
            raise ValueError("trigger_id, title, and body are required")

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "NudgeEvent":
        return cls(
            trigger_id=str(payload.get("trigger_id") or "").strip(),
            user_ids=payload.get("user_ids"),
            params=payload.get("params") or {},
            title=str(payload.get("title") or "").strip(),
            body=str(payload.get("body") or "").strip(),
            cta_deep_link=str(payload.get("cta_deep_link") or "astroroshni://chat").strip(),
            question=payload.get("question"),
            priority=int(payload.get("priority") or 0),
        )
