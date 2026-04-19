from __future__ import annotations

import os
from typing import Any, Dict, List

from context_agents.base import AgentContext, ContextAgent
from context_agents.agents.core_d1 import CoreD1Agent
from context_agents.agents.d1_graha_state import D1GrahaStateAgent
from context_agents.agents.vim_dasha import VimDashaAgent
from context_agents.agents.div_d9 import DivD9Agent
from context_agents.agents.div_intent import DivIntentAgent
from context_agents.agents.transit_win import TransitWinAgent
from context_agents.agents.dasha_win import DashaWinAgent
from context_agents.agents.panch_maitri import PanchMaitriAgent
from context_agents.agents.sniper_pts import SniperPtsAgent
from context_agents.agents.jaimini import JaiminiAgent
from context_agents.agents.nadi import NadiAgent
from context_agents.agents.chara_dasha import CharaDashaAgent
from context_agents.agents.ashtakavarga import AshtakavargaAgent
from context_agents.agents.nakshatra import NakshatraAgent
from context_agents.agents.kp import KpAgent

_AGENTS: Dict[str, ContextAgent] = {
    CoreD1Agent.agent_id: CoreD1Agent(),
    D1GrahaStateAgent.agent_id: D1GrahaStateAgent(),
    VimDashaAgent.agent_id: VimDashaAgent(),
    DivD9Agent.agent_id: DivD9Agent(),
    DivIntentAgent.agent_id: DivIntentAgent(),
    TransitWinAgent.agent_id: TransitWinAgent(),
    DashaWinAgent.agent_id: DashaWinAgent(),
    PanchMaitriAgent.agent_id: PanchMaitriAgent(),
    SniperPtsAgent.agent_id: SniperPtsAgent(),
    JaiminiAgent.agent_id: JaiminiAgent(),
    NadiAgent.agent_id: NadiAgent(),
    CharaDashaAgent.agent_id: CharaDashaAgent(),
    AshtakavargaAgent.agent_id: AshtakavargaAgent(),
    NakshatraAgent.agent_id: NakshatraAgent(),
    KpAgent.agent_id: KpAgent(),
}


def use_context_agents_env() -> bool:
    """When true, future orchestrator may assemble context from agents instead of legacy builder."""
    return os.environ.get("ASTRO_USE_CONTEXT_AGENTS", "").strip() in ("1", "true", "yes")


def list_agent_ids() -> List[str]:
    return sorted(_AGENTS.keys())


def build_agent(agent_id: str, ctx: AgentContext) -> Dict[str, Any]:
    """Run a single registered agent (for tests and incremental rollout)."""
    key = (agent_id or "").strip()
    agent = _AGENTS.get(key)
    if agent is None:
        raise KeyError(f"Unknown context agent: {agent_id!r}. Registered: {list_agent_ids()}")
    return agent.build(ctx)
