"""
Agent `div_intent`: compact L/P/H for every divisional (and D1) chart listed in
`intent_result['divisional_charts']`, matching chat router codes (`D3`…`D60`,
`D1`, `Karkamsa`, `Swamsa`).

Sources:
- D1: `static['d1_chart']`
- D3–D60: `static['divisional_charts'][<mapped key>]` (same keys as
  `ChatContextBuilder` merge / filter mapping)
- Karkamsa / Swamsa: `JaiminiChartCalculator` with Atmakaraka from static
  `chara_karakas` (same as chat when those codes are requested)

If `divisional_charts` is missing or empty, defaults to `["D9"]` so standalone
CLI/tests still return one chart. At most 14 charts per request (order preserved).

When ``AgentContext.div_intent_omit_codes`` contains normalized router codes (e.g. ``D1``, ``D9``),
those charts are skipped — used by parallel Parashari so ``div_intent`` does not duplicate
``core_d1`` / ``div_d9`` in the same bundle.
"""

from __future__ import annotations

import os
import re
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Dict, List, Optional

from calculators.jaimini_chart_calculator import JaiminiChartCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_chart_geometry import compact_wheel_chart

# Intent router / chat filter codes -> keys on `static['divisional_charts']`
INTENT_CODE_TO_STATIC_KEY: Dict[str, str] = {
    "D3": "d3_drekkana",
    "D4": "d4_chaturthamsa",
    "D7": "d7_saptamsa",
    "D9": "d9_navamsa",
    "D10": "d10_dasamsa",
    "D12": "d12_dwadasamsa",
    "D16": "d16_shodasamsa",
    "D20": "d20_vimsamsa",
    "D24": "d24_chaturvimsamsa",
    "D27": "d27_nakshatramsa",
    "D30": "d30_trimsamsa",
    "D40": "d40_khavedamsa",
    "D45": "d45_akshavedamsa",
    "D60": "d60_shashtiamsa",
}

_DEFAULT_CODES = ("D9",)
_MAX_CHARTS = 14


def _normalize_intent_chart_code(raw: Any) -> Optional[str]:
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    if s in ("Karkamsa", "Swamsa"):
        return s
    m = re.match(r"^D(\d+)$", s, re.IGNORECASE)
    if not m:
        return None
    return "D" + str(int(m.group(1), 10))


def _omit_codes_from_ctx(ctx: AgentContext) -> frozenset[str]:
    raw = ctx.div_intent_omit_codes
    if not raw:
        return frozenset()
    out: set[str] = set()
    for x in raw:
        if not isinstance(x, str):
            continue
        n = _normalize_intent_chart_code(x.strip())
        if n:
            out.add(n)
    return frozenset(out)


def _dedupe_preserve_order(codes: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _atmakaraka_planet(static: Dict[str, Any]) -> Optional[str]:
    ck = static.get("chara_karakas") or {}
    cc = ck.get("chara_karakas") or {}
    ak = cc.get("Atmakaraka") or {}
    p = ak.get("planet")
    return str(p).strip() if p else None


def _inner_from_divisional_wrap(wrap: Any) -> Dict[str, Any]:
    if not isinstance(wrap, dict):
        return {}
    inner = wrap.get("divisional_chart", wrap)
    return inner if isinstance(inner, dict) else {}


class DivIntentAgent(ContextAgent):
    agent_id = "div_intent"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        intent = ctx.intent_result or {}
        raw_list = intent.get("divisional_charts")
        if not isinstance(raw_list, list) or not raw_list:
            codes: List[str] = list(_DEFAULT_CODES)
        else:
            codes = []
            for item in raw_list:
                n = _normalize_intent_chart_code(item)
                if n:
                    codes.append(n)
            if not codes:
                codes = list(_DEFAULT_CODES)
        codes = _dedupe_preserve_order(codes)[:_MAX_CHARTS]

        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        divisional_charts = static.get("divisional_charts") or {}
        d1_chart = static.get("d1_chart") or {}

        C: Dict[str, Any] = {}
        skipped: List[str] = []

        ak = _atmakaraka_planet(static)
        omit = _omit_codes_from_ctx(ctx)

        for code in codes:
            if code in omit:
                skipped.append(f"{code}:omit_overlap")
                continue
            if code == "D1":
                if d1_chart.get("ascendant") is not None and d1_chart.get("planets"):
                    C["D1"] = compact_wheel_chart(d1_chart)
                else:
                    skipped.append("D1")
                continue

            if code in ("Karkamsa", "Swamsa"):
                if not ak:
                    skipped.append(f"{code}:no_ak")
                    continue
                try:
                    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                        jm = JaiminiChartCalculator(d1_chart, ak)
                        if code == "Karkamsa":
                            res = jm.calculate_karkamsa_chart()
                            inner = res.get("karkamsa_chart") or {}
                        else:
                            res = jm.calculate_swamsa_chart()
                            inner = res.get("swamsa_chart") or {}
                    if inner.get("ascendant") is not None and inner.get("planets"):
                        C[code] = compact_wheel_chart(inner)
                    else:
                        skipped.append(code)
                except Exception:
                    skipped.append(f"{code}:err")
                continue

            static_key = INTENT_CODE_TO_STATIC_KEY.get(code)
            if not static_key:
                skipped.append(f"{code}:unsupported")
                continue
            wrap = divisional_charts.get(static_key)
            inner = _inner_from_divisional_wrap(wrap)
            if inner.get("ascendant") is None or not inner.get("planets"):
                skipped.append(f"{code}:missing")
                continue
            C[code] = compact_wheel_chart(inner)

        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "Q": list(C.keys()),
            "C": C,
        }
        if skipped:
            out["S"] = skipped
        return out
