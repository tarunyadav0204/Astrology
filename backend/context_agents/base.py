from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentContext:
    """Inputs shared by all context agents."""

    birth_data: Dict[str, Any]
    user_question: str = ""
    intent_result: Optional[Dict[str, Any]] = None
    # Same optional inputs as `ChatContextBuilder.build_complete_context` / `_build_dynamic_context`:
    requested_period: Optional[Dict[str, Any]] = None
    target_date: Optional[Any] = None  # datetime focus for Chara / dasha (optional)
    # Override time scope: "full" | "intent_window" | "current" — else derived from intent + period.
    time_scope: Optional[str] = None
    # Test / orchestrator fast path: skip rebuilding when already computed for this birth.
    precomputed_static: Optional[Dict[str, Any]] = None
    precomputed_dynamic: Optional[Dict[str, Any]] = None
    # When building `div_intent` alongside `core_d1` + `div_d9`, omit these router codes (e.g. D1, D9) to avoid duplication.
    div_intent_omit_codes: Optional[frozenset[str]] = None


class ContextAgent(ABC):
    """Single agent: returns one compact JSON-serializable dict."""

    agent_id: str
    schema_version: int = 1

    @abstractmethod
    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        """Produce the agent payload (compact keys, no overlap with other agents)."""
