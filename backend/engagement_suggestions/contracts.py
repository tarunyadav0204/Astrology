from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class OpportunityInput:
    userid: int
    birth_chart_id: Optional[int]
    chart_name: str
    source_type: str
    source_reference_id: str
    question: str
    locale: str = "en"
    source_version: str = "1"
    manifestation_id: Optional[str] = None
    domain: str = "other"
    subject: str = "self"
    evidence: Dict[str, Any] = field(default_factory=dict)
    support_strength: float = 0.0
    relevance_score: float = 0.0
    event_window_start: Optional[datetime] = None
    event_window_end: Optional[datetime] = None
    eligible_from: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    semantic_cluster: str = ""
    title: str = ""
    body: str = ""
    generation_method: str = "deterministic"
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None

