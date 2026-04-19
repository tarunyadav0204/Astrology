"""
Compact context agents (parallel to legacy ChatContextBuilder).

See README.md. Import agents via context_agents.registry when orchestrating.
"""

from context_agents.base import AgentContext, ContextAgent
from context_agents.registry import build_agent, list_agent_ids, use_context_agents_env
from context_agents.scope import (
    ContextTimeScope,
    effective_time_scope,
    intent_for_dasha_window,
    intent_for_transit_build,
    resolve_context_scope,
)

__all__ = [
    "AgentContext",
    "ContextAgent",
    "ContextTimeScope",
    "build_agent",
    "effective_time_scope",
    "intent_for_dasha_window",
    "intent_for_transit_build",
    "list_agent_ids",
    "resolve_context_scope",
    "use_context_agents_env",
]
