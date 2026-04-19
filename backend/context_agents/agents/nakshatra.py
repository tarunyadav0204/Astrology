"""
Agent `nakshatra`: per-graha nakshatra, pada, D9 nakshatra, remedies, Navatara hints.

Sources: static `planetary_analysis`, `d9_planetary_analysis`, `nakshatra_remedies`,
`navatara_warnings`, `pushkara_navamsa` from `ChatContextBuilder._build_static_context`.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, Optional

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import PLANET_ORDER
from context_agents.scope import effective_time_scope

# Vimshottari sequence: 27 nakshatras cycle through 9 lords × 3.
_NAK_LORD_CYCLE = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")


def _nakshatra_index_from_name(name: Optional[str]) -> Optional[int]:
    if not name or not isinstance(name, str):
        return None
    # Match ChatContextBuilder / PlanetAnalyzer naming
    names = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
        "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
        "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati",
    ]
    for i, n in enumerate(names):
        if n.lower() == name.strip().lower():
            return i
    return None


def _nakshatra_lord(name: Optional[str]) -> Optional[str]:
    idx = _nakshatra_index_from_name(name)
    if idx is None:
        return None
    return _NAK_LORD_CYCLE[idx % 9]


def _pada(bi: Dict[str, Any]) -> Optional[int]:
    np = bi.get("nakshatra_pada")
    if isinstance(np, dict):
        p = np.get("pada")
        return int(p) if p is not None else None
    if isinstance(np, (int, float)):
        return int(np)
    return None


def _compact_row(pa: Dict[str, Any]) -> Dict[str, Any]:
    bi = (pa or {}).get("basic_info") or {}
    nk = bi.get("nakshatra")
    row: Dict[str, Any] = {
        "nk": nk,
        "ni": _nakshatra_index_from_name(nk),
        "pd": _pada(bi),
        "h": bi.get("house"),
        "sn": bi.get("sign_name"),
        "nl": _nakshatra_lord(nk),
    }
    return {k: v for k, v in row.items() if v is not None}


class NakshatraAgent(ContextAgent):
    agent_id = "nakshatra"
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

        pa = static.get("planetary_analysis") or {}
        d9 = static.get("d9_planetary_analysis") or {}
        p1: Dict[str, Any] = {}
        for name in PLANET_ORDER:
            if isinstance(pa.get(name), dict):
                p1[name] = _compact_row(pa[name])
        p9: Dict[str, Any] = {}
        for name in PLANET_ORDER:
            if isinstance(d9.get(name), dict):
                p9[name] = _compact_row(d9[name])

        remedies = static.get("nakshatra_remedies")
        nav = static.get("navatara_warnings")
        pk = static.get("pushkara_navamsa")

        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "P1": p1,
        }
        if p9:
            out["P9"] = p9
        if remedies:
            out["R"] = remedies
        if nav:
            out["NV"] = nav
        if pk:
            out["PK"] = pk
        return out
