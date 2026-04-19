"""
Agent `div_d9`: Navamsa (D9) lagna, planet rows, and whole-sign house lordships.

Same source as chat: `ChatContextBuilder._build_static_context` →
`divisional_charts['d9_navamsa']` (with `_add_sign_names_to_divisional_chart`).
Geometry keys mirror `core_d1` (`L`, `P`, `H`) but for the D9 frame; no birth `b`
(identity stays on `core_d1`). Implementation shares `compact_wheel_chart` with
`div_intent`.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_chart_geometry import compact_wheel_chart


def _d9_inner(static: Dict[str, Any]) -> Dict[str, Any]:
    wrap = (static.get("divisional_charts") or {}).get("d9_navamsa") or {}
    inner = wrap.get("divisional_chart", wrap)
    return inner if isinstance(inner, dict) else {}


class DivD9Agent(ContextAgent):
    agent_id = "div_d9"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        inner = _d9_inner(static)
        geom = compact_wheel_chart(inner)

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            **geom,
        }
