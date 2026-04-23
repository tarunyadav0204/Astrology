"""
Agent `health`: compact health summary from the existing HealthCalculator plus
health-focused transit pressure windows from dynamic transit activations.

This is only intended to be included for router categories `health` / `disease`.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, List, Optional

from calculators.health_calculator import HealthCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope

_HEALTH_HOUSES = {1, 4, 5, 6, 8, 12}
_RISKY_PLANETS = {"Mars", "Saturn", "Rahu", "Ketu", "Sun"}
_PLANET_DOSHA = {
    "Sun": "pitta",
    "Moon": "kapha",
    "Mars": "pitta",
    "Mercury": "vata",
    "Jupiter": "kapha",
    "Venus": "kapha",
    "Saturn": "vata",
    "Rahu": "vata",
    "Ketu": "vata-pitta",
}
_PLANET_DHATU = {
    "Sun": "ojas-vitality / heart-fire axis",
    "Moon": "rasa / fluids / nourishment",
    "Mars": "rakta-mamsa / blood-muscle axis",
    "Mercury": "majja-nerves / skin signaling",
    "Jupiter": "meda-growth / liver-nourishment axis",
    "Venus": "shukra-reproductive / hormonal balance",
    "Saturn": "asthi-majja / bones-degeneration axis",
    "Rahu": "ama-toxin / irregular nervous burden",
    "Ketu": "depletion / hidden sensitivity axis",
}


def _resolve_static_dynamic(ctx: AgentContext) -> tuple[Dict[str, Any], Dict[str, Any]]:
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

    if ctx.precomputed_dynamic is not None:
        dynamic = ctx.precomputed_dynamic
    else:
        dynamic = {}
    return static, dynamic


def _compact_planet_impacts(planet_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for planet, analysis in (planet_analysis or {}).items():
        if not isinstance(analysis, dict):
            continue
        impact = analysis.get("health_impact") or {}
        it = str(impact.get("impact_type") or "")
        if it not in {"Very Positive", "Challenging", "Gandanta Afflicted"}:
            continue
        rows.append(
            {
                "p": str(planet),
                "it": it,
                "se": str(impact.get("severity") or ""),
                "sys": list(analysis.get("body_systems") or [])[:3],
                "rs": str(impact.get("reasoning") or "")[:160],
                "dosha": _PLANET_DOSHA.get(str(planet), "mixed"),
                "dhatu": _PLANET_DHATU.get(str(planet), "general tissue axis"),
            }
        )
    rows.sort(key=lambda row: (0 if row["it"] == "Gandanta Afflicted" else 1 if row["it"] == "Challenging" else 2, row["p"]))
    return rows[:6]


def _compact_house_impacts(house_analysis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for house, analysis in (house_analysis or {}).items():
        if not isinstance(analysis, dict):
            continue
        key = str(house)
        ha = analysis.get("house_analysis") or {}
        oa = ha.get("overall_house_assessment") or {}
        out[key] = {
            "sc": oa.get("overall_strength_score"),
            "cg": oa.get("classical_grade"),
            "txt": str(analysis.get("health_interpretation") or "")[:180],
        }
    return out


def _dominant_charak(planet_rows: List[Dict[str, Any]], constitution_type: str) -> Dict[str, Any]:
    dosha_scores: Dict[str, int] = {"vata": 0, "pitta": 0, "kapha": 0}
    for row in planet_rows:
        dosha = str(row.get("dosha") or "")
        if "-" in dosha:
            for d in dosha.split("-"):
                if d in dosha_scores:
                    dosha_scores[d] += 1
        elif dosha in dosha_scores:
            dosha_scores[dosha] += 1
    ranked = sorted(dosha_scores.items(), key=lambda item: (-item[1], item[0]))
    lead = ranked[0][0] if ranked and ranked[0][1] > 0 else "mixed"
    return {
        "type": str(constitution_type or "Unknown"),
        "lead": lead,
        "mix": ranked,
    }


def _risk_windows(dynamic: Dict[str, Any]) -> List[Dict[str, Any]]:
    acts = dynamic.get("transit_activations") or []
    if not isinstance(acts, list):
        return []
    rows: List[Dict[str, Any]] = []
    for act in acts:
        if not isinstance(act, dict):
            continue
        try:
            nh = int(act.get("natal_house"))
        except (TypeError, ValueError):
            continue
        if nh not in _HEALTH_HOUSES:
            continue
        tp = str(act.get("transit_planet") or "")
        np = str(act.get("natal_planet") or "")
        score = 2
        if nh in {6, 8, 12}:
            score += 3
        if tp in _RISKY_PLANETS:
            score += 2
        if np in _RISKY_PLANETS:
            score += 1
        if str(act.get("aspect_type") or "").lower() == "conjunction":
            score += 1
        if int(act.get("aspect_number") or 0) in {4, 8, 10}:
            score += 1
        if score >= 8:
            band = "high"
        elif score >= 6:
            band = "medium"
        else:
            band = "low"
        rows.append(
            {
                "sd": act.get("start_date"),
                "ed": act.get("end_date"),
                "tp": tp,
                "np": np,
                "nh": nh,
                "at": act.get("aspect_type"),
                "rk": score,
                "band": band,
            }
        )
    rows.sort(key=lambda row: (-int(row.get("rk") or 0), str(row.get("sd") or ""), str(row.get("tp") or "")))
    return rows[:8]


def _safe_call(default: Any, fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except Exception:
        return default


class HealthAgent(ContextAgent):
    agent_id = "health"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        static, dynamic = _resolve_static_dynamic(ctx)
        birth = ctx.birth_data or {}
        d1 = static.get("d1_chart") or {}
        calc = HealthCalculator(d1, birth)
        try:
            raw = calc.calculate_overall_health()
        except Exception:
            planet_analysis = _safe_call({}, calc._analyze_health_planets)
            house_analysis = _safe_call({}, calc._analyze_health_houses)
            yoga_analysis = {
                "beneficial_yogas": [],
                "affliction_yogas": [],
                "total_beneficial": 0,
                "total_afflictions": 0,
            }
            score = _safe_call({"score": 0}, calc._calculate_health_score, planet_analysis, house_analysis, yoga_analysis)
            raw = {
                "planet_analysis": planet_analysis,
                "house_analysis": house_analysis,
                "yoga_analysis": yoga_analysis,
                "health_score": score.get("score", 0),
                "constitution_type": _safe_call("Unknown", calc._determine_constitution),
                "element_balance": _safe_call({}, calc._calculate_element_balance),
            }
        ph = _compact_planet_impacts(raw.get("planet_analysis") or {})
        hh = _compact_house_impacts(raw.get("house_analysis") or {})
        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "hs": int(raw.get("health_score") or 0),
            "ct": _dominant_charak(ph, str(raw.get("constitution_type") or "Unknown")),
            "eb": dict(raw.get("element_balance") or {}),
            "ph": ph,
            "hh": hh,
            "yg": {
                "b": int(((raw.get("yoga_analysis") or {}).get("total_beneficial")) or 0),
                "a": int(((raw.get("yoga_analysis") or {}).get("total_afflictions")) or 0),
            },
            "rw": _risk_windows(dynamic),
            "d30": bool(((static.get("divisional_charts") or {}).get("d30_trimsamsa"))),
        }
        return out
