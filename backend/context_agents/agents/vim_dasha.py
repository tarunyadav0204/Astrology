"""
Agent `vim_dasha`: current Vimshottari dashas + maraka flags + chart hints for MD/AD/PD.

Uses the same pipeline as chat: `ChatContextBuilder._build_static_context` (fills cache),
then `_build_dynamic_context` (DashaCalculator + maraka on `current_dashas`), then
`augment_current_dashas_with_chart_hints` (parity with `build_complete_context`).
Omits `maha_dashas` (large); add a separate agent if the full sequence is needed.
"""

from __future__ import annotations

import copy
import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope


def _compact_dasha_level(d: Any) -> Dict[str, Any]:
    if not isinstance(d, dict):
        return {}
    out: Dict[str, Any] = {}
    p = d.get("planet")
    if p is not None:
        out["p"] = p
    for long_k, short_k in (
        ("start", "st"),
        ("end", "en"),
        ("house", "h"),
        ("sign", "sn"),
        ("analysis_hint", "ah"),
    ):
        v = d.get(long_k)
        if v is not None and v != "":
            out[short_k] = v
    return out


class VimDashaAgent(ContextAgent):
    agent_id = "vim_dasha"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        if ctx.precomputed_static is not None and ctx.precomputed_dynamic is not None:
            static = ctx.precomputed_static
            dynamic = ctx.precomputed_dynamic
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            # `_build_dynamic_context` expects `static_cache[birth_hash]` (same as `build_complete_context`).
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]
                dynamic = builder._build_dynamic_context(birth, "", None, None, None)

        cd = copy.deepcopy(dynamic.get("current_dashas") or {})
        ChatContextBuilder().augment_current_dashas_with_chart_hints(
            cd,
            static.get("d1_chart") or {},
            dynamic.get("house_lordships") or {},
        )

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "D": {
                "md": _compact_dasha_level(cd.get("mahadasha")),
                "ad": _compact_dasha_level(cd.get("antardasha")),
                "pd": _compact_dasha_level(cd.get("pratyantardasha")),
                "sk": _compact_dasha_level(cd.get("sookshma")),
                "pr": _compact_dasha_level(cd.get("prana")),
                "mn": cd.get("moon_nakshatra"),
                "ml": cd.get("moon_lord"),
                "mk": cd.get("maraka_analysis") or {},
            },
        }
