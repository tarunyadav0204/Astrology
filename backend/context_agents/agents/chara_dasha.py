"""
Agent `chara_dasha`: full Jaimini Chara Dasha from `CharaDashaCalculator` (K.N. Rao style).

**Two levels:** Mahadasha = sign; Antardasha = sub-periods (12 per MD, sign-based).

**Lifetime scope:** The standalone calculator returns **one full Chara cycle** — **12 MD periods**
from birth until the cycle completes (often many decades total). It does **not** iterate second
and later rounds; extending multi-cycle lifetime would require calculator changes.

**Legacy chat (`ChatContextBuilder._build_dynamic_context`):** computes the same full sequence
internally, then **filters** `context['chara_dasha']['periods']` to either (a) periods overlapping
a transit window, or (b) **only the current MD** — so the LLM usually sees **one** MD block, not
the full lifetime list. This agent emits the **unfiltered** full calculator output in compact JSON.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any, Dict, List

from calculators.chara_dasha_calculator import CharaDashaCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import ContextTimeScope, effective_time_scope, filter_chara_periods, focus_datetime


def _sign_1_12(sign_idx: Any) -> int:
    try:
        return (int(sign_idx) % 12) + 1
    except (TypeError, ValueError):
        return 1


def _compact_antardashas(raw: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        return out
    for ad in raw:
        if not isinstance(ad, dict):
            continue
        out.append(
            {
                "s": _sign_1_12(ad.get("sign_id")),
                "nm": (ad.get("sign_name") or "")[:16],
                "ds": ad.get("start_date"),
                "de": ad.get("end_date"),
                "ic": bool(ad.get("is_current")),
            }
        )
    return out


def _compact_mahadashas(periods: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(periods, list):
        return out
    for p in periods:
        if not isinstance(p, dict):
            continue
        out.append(
            {
                "s": _sign_1_12(p.get("sign_id")),
                "nm": (p.get("sign_name") or "")[:16],
                "y": p.get("duration_years"),
                "ds": p.get("start_date"),
                "de": p.get("end_date"),
                "ic": bool(p.get("is_current")),
                "ad": _compact_antardashas(p.get("antardashas")),
            }
        )
    return out


class CharaDashaAgent(ContextAgent):
    agent_id = "chara_dasha"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        date_s = (birth.get("date") or "").strip()
        if not date_s:
            return {
                "a": self.agent_id,
                "v": self.schema_version,
                "err": "missing_birth_date",
            }

        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        chart = static.get("d1_chart") or {}
        if not chart:
            return {
                "a": self.agent_id,
                "v": self.schema_version,
                "err": "missing_d1_chart",
            }

        sc = effective_time_scope(ctx)
        focus = focus_datetime(ctx)
        dob_dt = datetime.strptime(date_s, "%Y-%m-%d")
        full = CharaDashaCalculator(chart).calculate_dasha(dob_dt, focus_date=focus)
        periods_raw: List[Dict[str, Any]] = list(full.get("periods") or [])
        ir = ctx.intent_result if isinstance(ctx.intent_result, dict) else None
        filtered, fn_tag = filter_chara_periods(periods_raw, sc, ir, focus)
        use_periods = filtered if filtered else periods_raw
        if not filtered:
            fn_tag = fn_tag or "fallback_all"

        note = (
            "sc=full: one Chara MD cycle (12 signs), all AD rows. "
            "sc=intent_window: MD periods overlapping intent transit years. "
            "sc=current: active MD only (legacy default)."
        )

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": sc.value,
            "fn": fn_tag,
            "sys": (full.get("system") or "Jaimini Chara Dasha (K.N. Rao)")[:80],
            "n": note,
            "P": _compact_mahadashas(use_periods),
        }
