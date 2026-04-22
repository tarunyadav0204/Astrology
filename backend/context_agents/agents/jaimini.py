"""
Agent `jaimini`: Jaimini bundle — special lagnas, Chara Karakas, Argala.

Same sources as chat static `ChatContextBuilder._build_static_context`:
  - `jaimini_points` from `JaiminiPointCalculator.calculate_jaimini_points`
  - `chara_karakas` from `CharaKarakaCalculator.calculate_chara_karakas`
  - `relationships.argala_analysis` from `ArgalaCalculator.calculate_argala_analysis`

Omits long karaka prose (`title`, `description`, `life_areas`, `calculation_method`, `system`),
Jaimini `description` strings per point, and argala `argala_type` / `virodha_type` long strings
(replaced by small integer codes — see SCHEMA.md).
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple, Union

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope

_JP_BLOCKS: Tuple[Tuple[str, str], ...] = (
    ("arudha_lagna", "AL"),
    ("darapada", "A7"),
    ("upapada_lagna", "UL"),
    ("karkamsa_lagna", "KL"),
    ("swamsa_lagna", "S9"),
    ("hora_lagna", "HL"),
    ("ghatika_lagna", "GL"),
)

_KK_KEYS: Tuple[Tuple[str, str], ...] = (
    ("Atmakaraka", "AK"),
    ("Amatyakaraka", "AmK"),
    ("Bhratrukaraka", "BK"),
    ("Matrukaraka", "MK"),
    ("Putrakaraka", "PK"),
    ("Gnatikaraka", "GK"),
    ("Darakaraka", "DK"),
)

_ARGALA_KIND = {"2nd House Argala": 2, "4th House Argala": 4, "11th House Argala": 11}
_VIRODHA_KIND = {"12th House Virodha": 12, "10th House Virodha": 10, "3rd House Virodha": 3}

_GRADE_CODE = {
    "Very Strong Support": 1,
    "Strong Support": 2,
    "Good Support": 3,
    "Neutral": 4,
    "Mild Obstruction": 5,
    "Strong Obstruction": 6,
    "Very Strong Obstruction": 7,
}


def _house_row(raw: Dict[str, Any], h: int) -> Optional[Dict[str, Any]]:
    return raw.get(h) if h in raw else raw.get(str(h))


def _argala_kind(label: str) -> int:
    if not label:
        return 0
    return _ARGALA_KIND.get(label, 0) or (
        2 if "2nd" in label else (4 if "4th" in label else (11 if "11th" in label else 0))
    )


def _virodha_kind(label: str) -> int:
    if not label:
        return 0
    return _VIRODHA_KIND.get(label, 0) or (
        12 if "12th" in label else (10 if "10th" in label else (3 if "3rd" in label else 0))
    )


def _grade_code(g: str) -> int:
    return _GRADE_CODE.get(g or "", 4)


def _compact_jaimini_points(raw: Any, sign_map: Dict[int, List[str]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not isinstance(raw, dict):
        return out
    for long_k, short_k in _JP_BLOCKS:
        block = raw.get(long_k) or {}
        sid = block.get("sign_id") if isinstance(block, dict) else None
        if isinstance(sid, int):
            s0 = int(sid) % 12
            out[short_k] = {
                "s": s0 + 1,
                # Planets occupying the special lagna sign, needed for A7/UL/AL reading.
                "pp": list(sign_map.get(s0, [])),
            }
    return out


def _compact_chara_karakas(raw: Any) -> Dict[str, Dict[str, Union[str, int, float]]]:
    out: Dict[str, Dict[str, Union[str, int, float]]] = {}
    if not isinstance(raw, dict):
        return out
    inner = raw.get("chara_karakas") or {}
    if not isinstance(inner, dict):
        return out
    for long_k, short_k in _KK_KEYS:
        row = inner.get(long_k) or {}
        if not isinstance(row, dict):
            continue
        sign0 = row.get("sign", 0)
        try:
            s12 = int(sign0) + 1
        except (TypeError, ValueError):
            s12 = 1
        dg = row.get("degree_in_sign")
        if isinstance(dg, (int, float)):
            dg = round(float(dg), 2)
        out[short_k] = {
            "p": row.get("planet"),
            "dg": dg,
            "s": min(12, max(1, s12)),
            "h": row.get("house", 1),
        }
    return out


def _compact_planet_signs(d1: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    planets = d1.get("planets") or {}
    for planet, data in planets.items():
        try:
            out[str(planet)] = {"s": (int(data.get("sign")) % 12) + 1}
        except (TypeError, ValueError, AttributeError):
            continue
    try:
        out["Asc"] = {"s": (int(float(d1.get("ascendant", 0)) / 30) % 12) + 1}
    except (TypeError, ValueError, AttributeError):
        pass
    return out


def _compact_argala(raw: Any) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not isinstance(raw, dict):
        return out
    for h in range(1, 13):
        ha = _house_row(raw, h)
        if not isinstance(ha, dict):
            continue
        ap: List[Dict[str, Any]] = []
        for p in ha.get("argala_planets") or []:
            if not isinstance(p, dict):
                continue
            rs = p.get("real_strength")
            if isinstance(rs, (int, float)):
                rs = round(float(rs), 2)
            ap.append(
                {
                    "p": p.get("planet"),
                    "rs": rs,
                    "k": _argala_kind(str(p.get("argala_type") or "")),
                }
            )
        vp: List[Dict[str, Any]] = []
        for p in ha.get("virodha_argala_planets") or []:
            if not isinstance(p, dict):
                continue
            rs = p.get("real_strength")
            if isinstance(rs, (int, float)):
                rs = round(float(rs), 2)
            vp.append(
                {
                    "p": p.get("planet"),
                    "rs": rs,
                    "k": _virodha_kind(str(p.get("virodha_type") or "")),
                }
            )
        out[str(h)] = {
            "n": ha.get("net_argala_strength"),
            "g": _grade_code(str(ha.get("argala_grade") or "")),
            "ap": ap,
            "vp": vp,
        }
    return out


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


class JaiminiAgent(ContextAgent):
    agent_id = "jaimini"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        static = _resolve_static(ctx)
        jp = static.get("jaimini_points") or {}
        ck = static.get("chara_karakas") or {}
        rel = static.get("relationships") or {}
        ag = rel.get("argala_analysis") or {}

        if not isinstance(jp, dict):
            jp = {}
        if not isinstance(ck, dict):
            ck = {}
        if not isinstance(ag, dict) or not ag:
            d1 = static.get("d1_chart") or {}
            birth = ctx.birth_data or {}
            birth_obj = SimpleNamespace(**birth) if birth else SimpleNamespace()
            try:
                from calculators.argala_calculator import ArgalaCalculator

                with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                    ag = ArgalaCalculator(d1, birth_obj).calculate_argala_analysis()
            except Exception:
                ag = {}

        d1 = static.get("d1_chart") or {}
        planets = d1.get("planets") or {}
        sign_map: Dict[int, List[str]] = {i: [] for i in range(12)}
        for planet, data in planets.items():
            try:
                sign_map[int(data.get("sign")) % 12].append(planet)
            except (TypeError, ValueError, AttributeError):
                continue

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "JP": _compact_jaimini_points(jp, sign_map),
            "CK": _compact_chara_karakas(ck),
            "PS": _compact_planet_signs(d1),
            "AG": _compact_argala(ag),
        }
