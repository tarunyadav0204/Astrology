"""
Agent `sniper_pts`: Bhrigu Bindu, 22nd Drekkana (Kharesh), 64th Navamsa, Mrityu Bhaga.

Same source as chat static: `ChatContextBuilder._build_static_context` →
`SniperPointsCalculator(d1_chart, d3_drekkana, d9_navamsa).get_all_sniper_points()`
stored as `sniper_points` (`kharesh`, `navamsa_64th`, `bhrigu_bindu`, `mrityu_bhaga`).

Omits long prose (`significance`, `transit_watch`, `lord_location_d1`, `formatted`) and
`bhrigu_bindu.upcoming_transits` (large / time-dependent); use chat or a transit agent
for timing detail.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, List, Optional

from calculators.sniper_points_calculator import SniperPointsCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import SIGN_NAMES


def _sign_1_12_from_name(name: Optional[str]) -> Optional[int]:
    if not name or not isinstance(name, str):
        return None
    try:
        return SIGN_NAMES.index(name) + 1
    except ValueError:
        return None


def _err(d: Any) -> Optional[str]:
    if isinstance(d, dict) and d.get("error"):
        return str(d["error"])[:160]
    return None


def _compress_kharesh(d: Dict[str, Any]) -> Dict[str, Any]:
    e = _err(d)
    if e:
        return {"e": e}
    s = _sign_1_12_from_name(d.get("danger_sign"))
    out: Dict[str, Any] = {"kl": d.get("kharesh_lord")}
    if s is not None:
        out["s"] = s
    elif d.get("danger_sign"):
        out["nm"] = d.get("danger_sign")
    return out


def _compress_navamsa_64(d: Dict[str, Any]) -> Dict[str, Any]:
    e = _err(d)
    if e:
        return {"e": e}
    s = _sign_1_12_from_name(d.get("danger_sign"))
    out: Dict[str, Any] = {"l": d.get("danger_lord")}
    if s is not None:
        out["s"] = s
    elif d.get("danger_sign"):
        out["nm"] = d.get("danger_sign")
    return out


def _compress_bhrigu_bindu(d: Dict[str, Any]) -> Dict[str, Any]:
    e = _err(d)
    if e:
        return {"e": e}
    s = _sign_1_12_from_name(d.get("sign"))
    lon = d.get("longitude")
    deg = d.get("degree")
    out: Dict[str, Any] = {
        "lon": round(float(lon), 2) if isinstance(lon, (int, float)) else lon,
        "d": round(float(deg), 2) if isinstance(deg, (int, float)) else deg,
        "h": d.get("house"),
        "ld": d.get("lord"),
    }
    if s is not None:
        out["s"] = s
    elif d.get("sign"):
        out["nm"] = d.get("sign")
    return out


def _intensity_code(label: Optional[str]) -> int:
    if label == "Critical":
        return 1
    return 2


def _compress_mrityu_bhaga(d: Dict[str, Any]) -> Dict[str, Any]:
    e = _err(d)
    if e:
        return {"e": e}
    rows: List[Dict[str, Any]] = []
    for ap in d.get("afflicted_points") or []:
        if not isinstance(ap, dict):
            continue
        if ap.get("point") == "Ascendant":
            rows.append(
                {
                    "p": "Asc",
                    "dg": ap.get("degree"),
                    "o": ap.get("orb"),
                    "i": _intensity_code(ap.get("intensity")),
                }
            )
        elif ap.get("planet"):
            rows.append(
                {
                    "p": ap.get("planet"),
                    "h": ap.get("house"),
                    "dg": ap.get("degree"),
                    "o": ap.get("orb"),
                    "i": _intensity_code(ap.get("intensity")),
                }
            )
    return {"x": bool(d.get("has_affliction")), "r": rows}


def _compress_bundle(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "K": _compress_kharesh(raw.get("kharesh") or {}),
        "N": _compress_navamsa_64(raw.get("navamsa_64th") or {}),
        "B": _compress_bhrigu_bindu(raw.get("bhrigu_bindu") or {}),
        "M": _compress_mrityu_bhaga(raw.get("mrityu_bhaga") or {}),
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


class SniperPtsAgent(ContextAgent):
    agent_id = "sniper_pts"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        static = _resolve_static(ctx)
        sp = static.get("sniper_points")
        if not isinstance(sp, dict) or not sp:
            d1 = static.get("d1_chart") or {}
            div = static.get("divisional_charts") or {}
            d3 = div.get("d3_drekkana") or {}
            d9 = div.get("d9_navamsa") or {}
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                sp = SniperPointsCalculator(d1, d3, d9).get_all_sniper_points()

        body = _compress_bundle(sp if isinstance(sp, dict) else {})
        return {
            "a": self.agent_id,
            "v": self.schema_version,
            **body,
        }
