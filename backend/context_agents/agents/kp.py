"""
Agent `kp`: Krishnamurti Paddhati — cusp lords, planet lords, significators from static chat context.

Source: `ChatContextBuilder._build_static_context` → `kp_analysis` (same as `KPChartService.calculate_kp_chart` summary).
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope


class KpAgent(ContextAgent):
    agent_id = "kp"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            birth = ctx.birth_data or {}
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        raw = static.get("kp_analysis")
        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
        }
        if raw is not None:
            out["KP"] = raw
        return out
