"""
Assemble VARIABLE_DATA_JSON payloads from context agents (compact keys per SCHEMA.md).

Parashari branch uses a multi-agent bundle; specialist branches use one agent each.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional

# Parallel Parashari: div_intent must not repeat D1/D9 already sent as core_d1 + div_d9.
_PARASHARI_DIV_INTENT_OMIT = frozenset({"D1", "D9"})

from context_agents.base import AgentContext
from context_agents.registry import build_agent

logger = logging.getLogger(__name__)

# Ordered list for Parashari-style synthesis (no single parashari agent exists).
# Chara Dasha is Jaimini-only — not included here (see Jaimini branch).
# `div_intent`: intent-listed divisionals; D1/D9 are omitted when building this bundle (see `AgentContext.div_intent_omit_codes`)
# so they are not duplicated with `core_d1` + `div_d9`.
# `special_points` (Yogi / Avayogi / Dagdha / Gandanta) is merged in from full chart context when provided
# so agent-mode Parashari matches legacy `build_parashari_slice` for those keys.
PARASHARI_AGENT_IDS: tuple[str, ...] = (
    "core_d1",
    "d1_graha",
    "vim_dasha",
    "div_d9",
    "div_intent",
    "transit_win",
    "dasha_win",
    "panch_maitri",
    "sniper_pts",
)


def build_parashari_agent_payload(
    agent_ctx: AgentContext,
    user_question: str,
    *,
    merged_chart_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    agents: Dict[str, Any] = {}
    prev_omit = agent_ctx.div_intent_omit_codes
    agent_ctx.div_intent_omit_codes = _PARASHARI_DIV_INTENT_OMIT
    try:
        for aid in PARASHARI_AGENT_IDS:
            try:
                agents[aid] = build_agent(aid, agent_ctx)
            except Exception as e:
                logger.warning("parashari bundle agent %s failed: %s", aid, e)
                agents[aid] = {"a": aid, "error": str(e)[:300]}
    finally:
        agent_ctx.div_intent_omit_codes = prev_omit
    out: Dict[str, Any] = {"parashari_agents": agents, "user_question": user_question}
    if merged_chart_context:
        sp = merged_chart_context.get("special_points")
        if isinstance(sp, dict) and sp:
            out["special_points"] = copy.deepcopy(sp)
    return out


def build_single_agent_payload(agent_id: str, agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    blob = build_agent(agent_id, agent_ctx)
    return {agent_id: blob, "user_question": user_question}


def build_nakshatra_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    """Nakshatra + Vimshottari spine (MD/AD for NK pillar); compact agent JSON only."""
    return {
        "nakshatra": build_agent("nakshatra", agent_ctx),
        "vim_dasha": build_agent("vim_dasha", agent_ctx),
        "user_question": user_question,
    }


def build_kp_agent_payload(agent_ctx: AgentContext, user_question: str) -> Dict[str, Any]:
    """KP + Vimshottari spine for dasha trigger step."""
    return {
        "kp": build_agent("kp", agent_ctx),
        "vim_dasha": build_agent("vim_dasha", agent_ctx),
        "user_question": user_question,
    }


def build_all_parallel_agent_payloads(
    agent_ctx: AgentContext,
    user_question: str,
    merged_chart_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return branch_label -> VARIABLE_DATA_JSON dict for specialist branches (Sudarshan payload is built in orchestrator from merged context)."""
    return {
        "parashari": build_parashari_agent_payload(
            agent_ctx, user_question, merged_chart_context=merged_chart_context
        ),
        "jaimini": build_single_agent_payload("jaimini", agent_ctx, user_question),
        "nadi": build_single_agent_payload("nadi", agent_ctx, user_question),
        "nakshatra": build_nakshatra_agent_payload(agent_ctx, user_question),
        "kp": build_kp_agent_payload(agent_ctx, user_question),
        "ashtakavarga": build_single_agent_payload("ashtakavarga", agent_ctx, user_question),
    }
