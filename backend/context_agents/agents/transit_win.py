"""
Agent `transit_win`: compact slow-graha transit activations for a year window.

Uses the same pipeline as chat: `ChatContextBuilder` static cache +
`_build_dynamic_context(..., intent_result=...)` when `needs_transits` and
`transit_request` are set (same shape the intent router will supply later).

Strips heavy fields (`all_aspects_cast`, `comprehensive_dashas`, long nested
blobs) from each activation; omits `ashtakavarga_filter` (deliver AV via a
separate agent). Does not modify the intent router — callers pass
`AgentContext.intent_result` (or rely on the built-in default window).
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any, Dict, List, Optional

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope, intent_for_transit_build

_MAX_ACTIVATIONS = int(os.environ.get("CONTEXT_AGENT_TRANSIT_MAX", "32"))


def _compact_activation(act: Dict[str, Any]) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "tp": act.get("transit_planet"),
        "np": act.get("natal_planet"),
        "an": act.get("aspect_number"),
        "sd": act.get("start_date"),
        "ed": act.get("end_date"),
        "th": act.get("transit_house"),
        "nh": act.get("natal_house"),
        "at": act.get("aspect_type"),
    }
    dr = act.get("dasha_reference")
    if isinstance(dr, dict) and dr.get("peak_date"):
        row["pk"] = dr["peak_date"]
    sig = act.get("dasha_significance")
    if isinstance(sig, str) and len(sig) <= 160:
        row["sg"] = sig
    return row


def _slim_period_dasha(pd: Any) -> Optional[List[Dict[str, Any]]]:
    if not isinstance(pd, dict):
        return None
    das = pd.get("dasha_activations")
    if not isinstance(das, list):
        return None
    keys = (
        "planet",
        "dasha_level",
        "probability",
        "transit_house",
        "natal_house",
        "primary_houses",
    )
    slim: List[Dict[str, Any]] = []
    for a in das[:12]:
        if not isinstance(a, dict):
            continue
        slim.append({k: a.get(k) for k in keys if k in a and a.get(k) is not None})
    return slim or None


def _vim_anchor(cd: Any) -> Optional[Dict[str, str]]:
    if not isinstance(cd, dict):
        return None
    md = cd.get("mahadasha") or {}
    ad = cd.get("antardasha") or {}
    mp = md.get("planet") if isinstance(md, dict) else None
    ap = ad.get("planet") if isinstance(ad, dict) else None
    if not mp and not ap:
        return None
    return {"m": str(mp or ""), "a": str(ap or "")}


class TransitWinAgent(ContextAgent):
    agent_id = "transit_win"
    schema_version = 3

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        intent_eff = intent_for_transit_build(ctx)

        if ctx.precomputed_static is not None and ctx.precomputed_dynamic is not None:
            dynamic = ctx.precomputed_dynamic
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]
                dynamic = builder._build_dynamic_context(
                    birth,
                    ctx.user_question or "",
                    None,
                    None,
                    intent_eff,
                )

        tr = intent_eff.get("transit_request") or {}
        sy = int(tr.get("startYear") or tr.get("start_year") or datetime.now().year)
        ey = int(tr.get("endYear") or tr.get("end_year") or sy + 2)

        raw_acts = dynamic.get("transit_activations") or []
        acts: List[Dict[str, Any]] = []
        if isinstance(raw_acts, list):
            for act in raw_acts[:_MAX_ACTIVATIONS]:
                if isinstance(act, dict):
                    acts.append(_compact_activation(act))

        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "Y": {"sy": sy, "ey": ey},
            "n": len(raw_acts) if isinstance(raw_acts, list) else 0,
            "A": acts,
        }

        anchor = _vim_anchor(dynamic.get("current_dashas"))
        if anchor:
            out["d"] = anchor

        pd_slim = _slim_period_dasha(dynamic.get("period_dasha_activations"))
        if pd_slim:
            out["p"] = pd_slim

        return out
