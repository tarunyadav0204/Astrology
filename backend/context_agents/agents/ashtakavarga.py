"""
Agent `ashtakavarga`: Sarvashtakavarga + Bhinnashtakavarga (D1), optional D9 block.

Same source as chat static `ChatContextBuilder._build_static_context` → `ashtakavarga`.
Emits compact numeric tables for token efficiency. `D1.S` / `D1.B` are indexed by **zodiac sign**
(Aries=0 … Pisces=11). **`D1.Ho`** (when ascendant is known) reindexes SAV/BAV by **house from lagna**
(1–12) so models do not misread rows as houses.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, List, Optional

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope

_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_SIGN_NAMES = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)


def _sav_row_from_block(sav_inner: Any) -> Optional[List[int]]:
    """Extract 12 sign bindus from `calculate_sarvashtakavarga()` return dict."""
    if not isinstance(sav_inner, dict):
        return None
    raw = sav_inner.get("sarvashtakavarga")
    if not isinstance(raw, dict):
        return None
    out: List[int] = []
    for i in range(12):
        k = str(i)
        v = raw.get(k, raw.get(i))
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            out.append(0)
    return out


def _bav_rows(bh: Any) -> Dict[str, List[int]]:
    out: Dict[str, List[int]] = {}
    if not isinstance(bh, dict):
        return out
    for p in _PLANETS:
        row = bh.get(p)
        if not isinstance(row, dict):
            continue
        bmap = row.get("bindus")
        if not isinstance(bmap, dict):
            continue
        vals: List[int] = []
        for i in range(12):
            k = str(i)
            v = bmap.get(k, bmap.get(i))
            try:
                vals.append(int(v))
            except (TypeError, ValueError):
                vals.append(0)
        out[p] = vals
    return out


def _asc_sign_0_from_static(static: Dict[str, Any]) -> Optional[int]:
    """Lagna sign as 0=Aries … 11=Pisces from precomputed static context."""
    ai = static.get("ascendant_info") or {}
    sn = ai.get("sign_number")
    if isinstance(sn, (int, float)) and 1 <= int(sn) <= 12:
        return int(sn) - 1
    d1c = static.get("d1_chart") or {}
    deg = d1c.get("ascendant")
    if deg is not None:
        try:
            return int(float(deg) // 30) % 12
        except (TypeError, ValueError):
            pass
    return None


def _houses_from_lagna(
    sav12: List[int],
    bav_by_planet: Dict[str, List[int]],
    asc_sign_0: int,
) -> Dict[str, Dict[str, Any]]:
    """
    Whole-sign houses 1–12 from lagna: house H occupies zodiac index
    (asc_sign_0 + H - 1) % 12. Bindus in S/B at that index apply to that house.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for h in range(1, 13):
        si = (asc_sign_0 + h - 1) % 12
        z = si + 1
        b_row: Dict[str, int] = {}
        for p in _PLANETS:
            row = bav_by_planet.get(p)
            if isinstance(row, list) and len(row) > si:
                b_row[p] = int(row[si])
        out[str(h)] = {
            "z": z,
            "zn": _SIGN_NAMES[si],
            "s": int(sav12[si]) if len(sav12) > si else 0,
            "B": b_row,
        }
    return out


def _compact_d1_block(d1: Any, *, asc_sign_0: Optional[int] = None) -> Dict[str, Any]:
    if not isinstance(d1, dict):
        return {}
    sav_big = d1.get("sarvashtakavarga")
    sav = _sav_row_from_block(sav_big) if isinstance(sav_big, dict) else None
    tb = None
    if isinstance(sav_big, dict):
        try:
            tb = int(sav_big.get("total_bindus") or 0)
        except (TypeError, ValueError):
            tb = None
    bh = _bav_rows(d1.get("bhinnashtakavarga"))
    sav_list = sav or [0] * 12
    out: Dict[str, Any] = {"S": sav_list, "tb": tb, "B": bh}
    if asc_sign_0 is not None:
        out["La"] = asc_sign_0 + 1
        out["Ho"] = _houses_from_lagna(sav_list, bh, asc_sign_0)
    return out


def _compact_d9(d9: Any) -> Dict[str, Any]:
    if not isinstance(d9, dict) or not d9:
        return {}
    out: Dict[str, Any] = {}
    sav_big = d9.get("sarvashtakavarga")
    if isinstance(sav_big, dict):
        r = _sav_row_from_block(sav_big)
        if r:
            out["S9"] = r
    bh = d9.get("bhinnashtakavarga")
    if isinstance(bh, dict) and bh:
        out["B9"] = _bav_rows(bh)
    return out


class AshtakavargaAgent(ContextAgent):
    agent_id = "ashtakavarga"
    schema_version = 2

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

        raw = static.get("ashtakavarga") or {}
        d1 = raw.get("d1_rashi") or {}
        d9 = raw.get("d9_navamsa") or {}
        asc0 = _asc_sign_0_from_static(static)

        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "D1": _compact_d1_block(d1, asc_sign_0=asc0),
        }
        d9c = _compact_d9(d9)
        if d9c:
            out["D9"] = d9c
        return out
