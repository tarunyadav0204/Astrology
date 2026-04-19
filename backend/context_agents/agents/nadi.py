"""
Agent `nadi`: Bhrigu Nandi Nadi bundle — linkage web + progressive age activation.

Static (chat `_build_static_context`):
  - `nadi_links` from `NadiLinkageCalculator(chart_data_original).get_nadi_links()`

Dynamic (chat `_build_dynamic_context`):
  - `nadi_age_activation` — age milestones vs nakshatras + planets in those nakshatras
    (same `nadi_age_map` and `planetary_analysis` scan as `ChatContextBuilder`).

If `precomputed_dynamic` is omitted, age activation is recomputed with **server “now”**
and `planetary_analysis` from resolved static context (no full dynamic build).

Omits long `instruction` prose from the chat payload (models use structured `AA` only).
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any, Dict, List, Optional

from calculators.nadi_linkage_calculator import NadiLinkageCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import ContextTimeScope, effective_time_scope
from context_agents.compact_vedic import PLANET_ORDER

# Same ages / stars as `ChatContextBuilder._build_dynamic_context`
_NADI_AGE_MAP: Dict[int, Any] = {
    16: "Rohini",
    24: "Pushya",
    30: "Swati",
    36: ["Rohini", "Pushya"],
    45: "Magha",
    46: ["Magha", "Swati"],
    65: "Pushya",
    69: "Swati",
    83: "Rohini",
}


def _resolve_static(ctx: AgentContext) -> Dict[str, Any]:
    birth = ctx.birth_data or {}
    if ctx.precomputed_static is not None:
        return ctx.precomputed_static
    builder = ChatContextBuilder()
    birth_hash = builder._create_birth_hash(birth)
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        if birth_hash not in builder.static_cache:
            builder.static_cache[birth_hash] = builder._build_static_context(birth)
        return builder.static_cache[birth_hash]


def _compact_links(raw: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if not isinstance(raw, dict):
        return out
    for pname in PLANET_ORDER:
        row = raw.get(pname)
        if not isinstance(row, dict):
            continue
        si = row.get("sign_info") or {}
        sid = si.get("sign_id")
        try:
            s12 = int(sid) + 1 if isinstance(sid, int) else None
        except (TypeError, ValueError):
            s12 = None
        conn = row.get("connections") or {}
        out[pname] = {
            "s": s12,
            "rv": bool(si.get("is_retro")),
            "ex": bool(si.get("is_exchange")),
            "t": sorted(conn.get("trine") or []),
            "f": sorted(conn.get("next") or []),
            "b": sorted(conn.get("prev") or []),
            "o": sorted(conn.get("opposite") or []),
            "a": sorted(row.get("all_links") or []),
        }
    return out


def _compute_age_activation(
    birth_data: Dict[str, Any],
    planetary_analysis: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    try:
        dob = datetime.strptime(str(birth_data["date"]), "%Y-%m-%d")
    except Exception:
        return None
    current_age = datetime.now().year - dob.year
    activated = _NADI_AGE_MAP.get(current_age)
    if not activated:
        return None
    stars = activated if isinstance(activated, list) else [activated]
    planets_out: List[Dict[str, Any]] = []
    for planet, data in (planetary_analysis or {}).items():
        if not isinstance(data, dict):
            continue
        nak = (data.get("basic_info") or {}).get("nakshatra")
        if nak in stars:
            planets_out.append(
                {
                    "p": planet,
                    "n": nak,
                    "h": (data.get("basic_info") or {}).get("house"),
                }
            )
    return {
        "y": current_age,
        "k": stars,
        "pl": sorted(planets_out, key=lambda x: str(x.get("p") or "")),
    }


def _compact_age_activation(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    stars = raw.get("activated_nakshatras") or []
    if not isinstance(stars, list):
        stars = [stars] if stars else []
    pl: List[Dict[str, Any]] = []
    for row in raw.get("activated_planets") or []:
        if not isinstance(row, dict):
            continue
        pl.append(
            {
                "p": row.get("planet"),
                "n": row.get("nakshatra"),
                "h": row.get("house"),
            }
        )
    return {
        "y": raw.get("age"),
        "k": stars,
        "pl": sorted(pl, key=lambda x: str(x.get("p") or "")),
    }


class NadiAgent(ContextAgent):
    agent_id = "nadi"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        static = _resolve_static(ctx)

        raw_links = static.get("nadi_links")
        if not isinstance(raw_links, dict) or not raw_links:
            d1 = static.get("d1_chart") or {}
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                raw_links = NadiLinkageCalculator(d1).get_nadi_links()

        lk = _compact_links(raw_links)

        aa: Optional[Dict[str, Any]] = None
        if ctx.precomputed_dynamic is not None:
            na = ctx.precomputed_dynamic.get("nadi_age_activation")
            if isinstance(na, dict):
                aa = _compact_age_activation(na)
        if aa is None:
            aa = _compute_age_activation(birth, static.get("planetary_analysis") or {})

        sc = effective_time_scope(ctx)
        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": sc.value,
            "LK": lk,
            "AA": aa,
        }
        if sc == ContextTimeScope.FULL:
            out["MS"] = [
                {
                    "a": age,
                    "k": (stars if isinstance(stars, list) else [stars]),
                }
                for age, stars in sorted(_NADI_AGE_MAP.items())
            ]
        return out
