"""
Agent `dasha_win`: Vimshottari levels for an arbitrary date window (from intent).

Always emits MD / AD / PD (with `st`/`en` where the calculator provides them, plus
`h`/`sn`/`ah` via `ChatContextBuilder.augment_current_dashas_with_chart_hints`).
Includes **Sookshma** and **Prana** only when the resolved calendar window is
**at most 31 days** (single `dasha_as_of` day counts as 1 day → includes SK/PR).

Window source (no intent-router changes): prefers `intent_result.transit_request`
(`startYear`, `endYear`, optional `yearMonthMap`) like `transit_win`; optional
`intent_result.dasha_as_of` (`YYYY-MM-DD`) overrides to a single day.

Uses `DashaCalculator.calculate_dashas_for_date` + static `d1_chart` for hints.
Adds **`T`**: compact **timeline** from `get_dasha_periods_for_range` over **`W`**
(capped by `CONTEXT_AGENT_DASHA_TIMELINE_MAX`, default 80). Each row includes
**`sk`/`pr`** only when that segment’s length is ≤31 days. Omits `maha_dashas`
bulk list.
"""

from __future__ import annotations

import copy
import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.compact_vedic import house_lordships_from_ascendant
from context_agents.scope import effective_time_scope, intent_for_dasha_window
from context_agents.agents.vim_dasha import _compact_dasha_level
from shared.dasha_calculator import DashaCalculator

_MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

_MAX_SUBLEVEL_DAYS = 31
_TIMELINE_MAX = int(os.environ.get("CONTEXT_AGENT_DASHA_TIMELINE_MAX", "80"))


def _last_day_of_month(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year, 12, 31, 12, 0, 0)
    nxt = datetime(year, month + 1, 1, 12, 0, 0)
    return nxt - timedelta(days=1)


def _parse_window(intent: Optional[Dict[str, Any]]) -> Tuple[datetime, datetime, int]:
    """Return (window_start, window_end, span_days inclusive)."""
    now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    if not isinstance(intent, dict):
        return now, now, 1

    as_of = intent.get("dasha_as_of")
    if isinstance(as_of, str) and len(as_of) >= 10:
        try:
            d0 = datetime.strptime(as_of[:10], "%Y-%m-%d").replace(hour=12)
            return d0, d0, 1
        except ValueError:
            pass

    tr = intent.get("transit_request")
    if not isinstance(tr, dict):
        return now, now, 1

    sy = int(tr.get("startYear") or tr.get("start_year") or now.year)
    ey = int(tr.get("endYear") or tr.get("end_year") or sy)
    ymm = tr.get("yearMonthMap") or {}

    if isinstance(ymm, dict) and ymm:
        starts: List[datetime] = []
        ends: List[datetime] = []
        for ys, months in ymm.items():
            try:
                y = int(str(ys))
            except ValueError:
                continue
            for mname in months or []:
                if not isinstance(mname, str):
                    continue
                m = _MONTH_MAP.get(mname.strip())
                if not m:
                    continue
                starts.append(datetime(y, m, 1, 12, 0, 0))
                ends.append(_last_day_of_month(y, m))
        if starts and ends:
            w_start = min(starts)
            w_end = max(ends)
        else:
            w_start = datetime(sy, 1, 1, 12, 0, 0)
            w_end = datetime(ey, 12, 31, 12, 0, 0)
    else:
        w_start = datetime(sy, 1, 1, 12, 0, 0)
        w_end = datetime(ey, 12, 31, 12, 0, 0)

    span = (w_end - w_start).days + 1
    return w_start, w_end, max(1, span)


def _anchor_date(w_start: datetime) -> datetime:
    """Date used for `calculate_dashas_for_date` (start of window)."""
    return w_start.replace(hour=12, minute=0, second=0, microsecond=0)


def _segment_days(sd: str, ed: str) -> int:
    try:
        d0 = datetime.strptime(sd[:10], "%Y-%m-%d")
        d1 = datetime.strptime(ed[:10], "%Y-%m-%d")
        return (d1 - d0).days + 1
    except (TypeError, ValueError):
        return 999


def _compact_timeline_row(p: Dict[str, Any]) -> Dict[str, Any]:
    sd = p.get("start_date")
    ed = p.get("end_date")
    row: Dict[str, Any] = {
        "sd": sd,
        "ed": ed,
        "M": p.get("mahadasha"),
        "A": p.get("antardasha"),
        "P": p.get("pratyantardasha"),
    }
    if isinstance(sd, str) and isinstance(ed, str) and _segment_days(sd, ed) <= _MAX_SUBLEVEL_DAYS:
        if p.get("sookshma") is not None:
            row["sk"] = p.get("sookshma")
        if p.get("prana") is not None:
            row["pr"] = p.get("prana")
    return row


class DashaWinAgent(ContextAgent):
    agent_id = "dasha_win"
    schema_version = 2

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        birth = ctx.birth_data or {}
        intent = intent_for_dasha_window(ctx)
        w_start, w_end, span = _parse_window(intent)
        anchor = _anchor_date(w_start)
        include_sk_pr = span <= _MAX_SUBLEVEL_DAYS

        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        d1 = static.get("d1_chart") or {}
        asc0 = int(float(d1.get("ascendant", 0.0)) / 30.0) % 12
        house_lordships = house_lordships_from_ascendant(asc0)

        calc = DashaCalculator()
        raw = calc.calculate_dashas_for_date(anchor, birth)

        cd = {
            "mahadasha": copy.deepcopy(raw.get("mahadasha") or {}),
            "antardasha": copy.deepcopy(raw.get("antardasha") or {}),
            "pratyantardasha": copy.deepcopy(raw.get("pratyantardasha") or {}),
        }
        ChatContextBuilder().augment_current_dashas_with_chart_hints(
            cd,
            d1,
            house_lordships,
        )

        out: Dict[str, Any] = {
            "a": self.agent_id,
            "v": self.schema_version,
            "sc": effective_time_scope(ctx).value,
            "W": {
                "sd": w_start.strftime("%Y-%m-%d"),
                "ed": w_end.strftime("%Y-%m-%d"),
                "sp": span,
            },
            "dt": anchor.strftime("%Y-%m-%d"),
            "md": _compact_dasha_level(cd.get("mahadasha")),
            "ad": _compact_dasha_level(cd.get("antardasha")),
            "pd": _compact_dasha_level(cd.get("pratyantardasha")),
            "mn": raw.get("moon_nakshatra"),
            "ml": raw.get("moon_lord"),
        }

        if include_sk_pr:
            out["sk"] = _compact_dasha_level(raw.get("sookshma"))
            out["pr"] = _compact_dasha_level(raw.get("prana"))

        periods = calc.get_dasha_periods_for_range(birth, w_start, w_end)
        t_rows: List[Dict[str, Any]] = []
        if isinstance(periods, list):
            for p in periods[:_TIMELINE_MAX]:
                if isinstance(p, dict):
                    t_rows.append(_compact_timeline_row(p))
        out["T"] = t_rows
        out["tn"] = len(periods) if isinstance(periods, list) else 0
        if isinstance(periods, list) and len(periods) > _TIMELINE_MAX:
            out["tx"] = True

        return out
