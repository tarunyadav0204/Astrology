"""
Build `AgentContext` from merged `ChatContextBuilder` output so context agents skip redundant work.

When `precomputed_static` / `precomputed_dynamic` are populated from the same keys the builder
would have produced, agents read from cache instead of re-running `_build_static_context`.
"""

from __future__ import annotations

import copy
import os
from datetime import datetime
from typing import Any, Dict, Optional, Set, Tuple

from context_agents.base import AgentContext

# Keys typically produced / augmented in `_build_dynamic_context` (merged chart chat).
_DYNAMIC_TOP_LEVEL_KEYS: Set[str] = {
    "transit_activations",
    "macro_transits_timeline",
    "period_dasha_activations",
    "unified_dasha_timeline",
    "requested_dasha_summary",
    "nadi_age_activation",
    "current_dashas",
    "extracted_context",
    "jaimini_full_analysis",
}

# Meta keys not needed inside static/dynamic caches (intent is on AgentContext.intent_result).
_META_KEYS: Set[str] = {
    "intent",
    "response_format",
    "analysis_type",
    "current_date_info",
}


def parallel_agent_context_enabled() -> bool:
    """When true, parallel chat branch payloads use compact context agent JSON (see SCHEMA.md)."""
    return os.environ.get("ASTRO_PARALLEL_AGENT_CONTEXT", "").strip().lower() in ("1", "true", "yes")


def merged_context_to_birth_data(merged: Dict[str, Any]) -> Dict[str, Any]:
    """Map `birth_details` from merged chat context to calculator `birth_data` shape."""
    bd = merged.get("birth_details") or {}
    return {
        "name": bd.get("name"),
        "date": bd.get("date"),
        "time": bd.get("time"),
        "place": bd.get("place"),
        "latitude": bd.get("latitude"),
        "longitude": bd.get("longitude"),
        "timezone": bd.get("timezone"),
        "gender": bd.get("gender"),
    }


def _split_static_dynamic(merged: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    static_part: Dict[str, Any] = {}
    dynamic_part: Dict[str, Any] = {}
    for k, v in merged.items():
        if k in _META_KEYS:
            continue
        if k in _DYNAMIC_TOP_LEVEL_KEYS:
            dynamic_part[k] = copy.deepcopy(v)
        else:
            static_part[k] = copy.deepcopy(v)
    return static_part, dynamic_part


def merged_context_to_agent_context(merged: Dict[str, Any], *, user_question: str) -> AgentContext:
    """
    Build AgentContext for `build_agent` calls.

    Fills precomputed_static / precomputed_dynamic from merged dict when possible so agents
    do not each invoke ChatContextBuilder cold.
    """
    birth_data = merged_context_to_birth_data(merged)
    intent_block = merged.get("intent")
    intent_result: Optional[Dict[str, Any]] = (
        copy.deepcopy(intent_block) if isinstance(intent_block, dict) else None
    )

    requested_period: Optional[Dict[str, Any]] = None
    target_date = None
    if isinstance(intent_result, dict):
        tr = intent_result.get("transit_request")
        if isinstance(tr, dict):
            requested_period = {
                "start_year": tr.get("startYear"),
                "end_year": tr.get("endYear"),
                "yearMonthMap": tr.get("yearMonthMap", {}),
            }
        as_of = intent_result.get("dasha_as_of")
        if isinstance(as_of, str) and len(as_of) >= 10:
            try:
                target_date = datetime.strptime(as_of[:10], "%Y-%m-%d")
            except ValueError:
                target_date = None

    static_part, dynamic_part = _split_static_dynamic(merged)

    return AgentContext(
        birth_data=birth_data,
        user_question=user_question or "",
        intent_result=intent_result,
        requested_period=requested_period,
        target_date=target_date,
        time_scope=None,
        precomputed_static=static_part if static_part else None,
        precomputed_dynamic=dynamic_part if dynamic_part else None,
    )
