"""
Agent `d1_graha`: D1 graha state (dignity, retrograde, combustion, baladi avastha, grades).

Uses the same pipeline as chat static context: `ChatContextBuilder._build_static_context`
then maps `planetary_analysis` (already `PlanetAnalyzer` + `_filter_planetary_analysis`).
No new calculator logic.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import PLANET_ORDER


def _compact_graha_from_filtered(p: Dict[str, Any]) -> Dict[str, Any]:
    dig = p.get("dignity_analysis") or {}
    comb = p.get("combustion_status") or {}
    retro = p.get("retrograde_analysis") or {}
    basic = p.get("basic_info") or {}
    overall = p.get("overall_assessment") or {}
    return {
        "r": bool(retro.get("is_retrograde")),
        "d": dig.get("dignity"),
        "fn": dig.get("functional_nature"),
        "sm": dig.get("strength_multiplier"),
        "cb": bool(comb.get("is_combust")),
        "cz": bool(comb.get("is_cazimi")),
        "cs": comb.get("status"),
        "av": basic.get("avastha"),
        "cg": overall.get("classical_grade"),
        "sc": overall.get("overall_strength_score"),
    }


class D1GrahaStateAgent(ContextAgent):
    agent_id = "d1_graha"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                static = builder._build_static_context(birth)

        pa = static.get("planetary_analysis") or {}
        g: Dict[str, Any] = {}
        for name in PLANET_ORDER:
            pdata = pa.get(name)
            if isinstance(pdata, dict):
                g[name] = _compact_graha_from_filtered(pdata)

        return {"a": self.agent_id, "v": self.schema_version, "G": g}
