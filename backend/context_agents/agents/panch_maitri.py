"""
Agent `panch_maitri`: Panchadha (5-fold) planetary friendship matrix.

Same source as chat static context: `FriendshipCalculator.calculate_friendship`
→ `friendship_matrix` (compound natural + temporal → great_friend, friend,
neutral, enemy, great_enemy, self). Optional `precomputed_static` may supply
`friendship_analysis` from `_build_static_context` to skip recalculation.

Does not emit `aspects_matrix` / `planet_positions` (separate agent if needed).
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict

from calculators.friendship_calculator import FriendshipCalculator
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import PLANET_ORDER

# Compact relation codes (decode in SCHEMA.md)
_REL_CODE: Dict[str, str] = {
    "self": ".",
    "great_friend": "++",
    "friend": "+",
    "neutral": "0",
    "enemy": "-",
    "great_enemy": "--",
}


def _encode_matrix(fm: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for p1 in PLANET_ORDER:
        row = fm.get(p1)
        if not isinstance(row, dict):
            continue
        out[p1] = {}
        for p2 in PLANET_ORDER:
            v = row.get(p2)
            if isinstance(v, str):
                out[p1][p2] = _REL_CODE.get(v, v)
            else:
                out[p1][p2] = "?"
    return out


class PanchMaitriAgent(ContextAgent):
    agent_id = "panch_maitri"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}

        if ctx.precomputed_static is not None:
            fa = ctx.precomputed_static.get("friendship_analysis") or {}
            if isinstance(fa, dict) and not fa.get("error") and fa.get("friendship_matrix"):
                fm = fa["friendship_matrix"]
            else:
                with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                    fm = FriendshipCalculator().calculate_friendship(birth)["friendship_matrix"]
        else:
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                fm = FriendshipCalculator().calculate_friendship(birth)["friendship_matrix"]

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "F": _encode_matrix(fm),
        }
