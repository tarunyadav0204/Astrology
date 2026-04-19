"""
Time scope for context agents — mirrors how legacy `ChatContextBuilder` tightens or widens
dynamic data (Chara filter, transit years, dasha windows) from `intent_result` + `requested_period`.

Scopes:
  - **full** — lifespan / open “when” analysis: wide coverage (full Chara cycle, wide transit/dasha window).
  - **intent_window** — explicit or router-derived year/month window only.
  - **current** — present-focused (daily, “now”, default when no strong window).
"""

from __future__ import annotations

import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


class ContextTimeScope(str, Enum):
    FULL = "full"
    INTENT_WINDOW = "intent_window"
    CURRENT = "current"


def _env_scope_override() -> Optional[ContextTimeScope]:
    raw = (os.environ.get("CONTEXT_AGENT_TIME_SCOPE") or "").strip().lower()
    if not raw:
        return None
    for m in ContextTimeScope:
        if raw == m.value:
            return m
    return None


def resolve_context_scope(
    intent_result: Optional[Dict[str, Any]],
    requested_period: Optional[Dict[str, Any]] = None,
    explicit_time_scope: Optional[str] = None,
) -> ContextTimeScope:
    """
    Derive scope from env override, explicit string, intent mode, and period hints
    (same signals legacy chat uses in `_build_dynamic_context`).
    """
    o = _env_scope_override()
    if o is not None:
        return o

    if explicit_time_scope:
        es = explicit_time_scope.strip().lower()
        for m in ContextTimeScope:
            if es == m.value:
                return m

    ir: Dict[str, Any] = intent_result if isinstance(intent_result, dict) else {}
    mode_u = str(ir.get("mode") or "").strip().upper()

    # Lifespan / open-ended major life timing → wide context (legacy still filters Chara in places;
    # agents can send full Chara cycle + wide Vim windows).
    if mode_u == "LIFESPAN_EVENT_TIMING":
        return ContextTimeScope.FULL

    # Daily / today
    if mode_u == "PREDICT_DAILY" or mode_u.startswith("PREDICT_DAILY"):
        return ContextTimeScope.CURRENT

    # Explicit backend / annual period
    if isinstance(requested_period, dict) and (
        requested_period.get("startYear")
        or requested_period.get("start_year")
        or requested_period.get("endYear")
        or requested_period.get("end_year")
    ):
        return ContextTimeScope.INTENT_WINDOW

    tr = ir.get("transit_request")
    if isinstance(tr, dict) and (tr.get("startYear") or tr.get("start_year")):
        return ContextTimeScope.INTENT_WINDOW

    # Period outlook / event lists → usually a bounded window from the router
    if mode_u in ("PREDICT_PERIOD_OUTLOOK", "PREDICT_EVENTS_FOR_PERIOD"):
        return ContextTimeScope.INTENT_WINDOW if ir.get("transit_request") else ContextTimeScope.CURRENT

    # Default: same spirit as legacy Chara default (current period) and compact transits
    return ContextTimeScope.CURRENT


def focus_datetime(ctx: Any) -> datetime:
    """Anchor date for Chara filtering (intent focus or explicit target_date)."""
    td = getattr(ctx, "target_date", None)
    if td is not None:
        try:
            if isinstance(td, datetime):
                return td.replace(tzinfo=None) if td.tzinfo else td
        except Exception:
            pass
    ir: Dict[str, Any] = getattr(ctx, "intent_result", None) or {}
    tr = ir.get("transit_request")
    if isinstance(tr, dict):
        y = tr.get("startYear") or tr.get("start_year")
        if y is not None:
            try:
                return datetime(int(y), 6, 15)
            except (TypeError, ValueError):
                pass
    return datetime.now()


def effective_time_scope(ctx: Any) -> ContextTimeScope:
    """Resolve scope from `AgentContext` (explicit override + intent + requested_period)."""
    explicit = getattr(ctx, "time_scope", None)
    ir = getattr(ctx, "intent_result", None)
    rp = getattr(ctx, "requested_period", None)
    return resolve_context_scope(ir, rp, explicit)


def _birth_year(birth_data: Optional[Dict[str, Any]]) -> int:
    if not isinstance(birth_data, dict):
        return datetime.now().year
    ds = str(birth_data.get("date") or "")[:10]
    try:
        return int(ds[:4])
    except (TypeError, ValueError):
        return datetime.now().year


def _default_transit_intent(cy: int) -> Dict[str, Any]:
    return {
        "needs_transits": True,
        "transit_request": {
            "startYear": cy,
            "endYear": cy + 2,
            "yearMonthMap": {str(y): list(_MONTHS) for y in range(cy, cy + 3)},
        },
    }


def intent_for_transit_build(
    ctx: Any,
    scope: Optional[ContextTimeScope] = None,
) -> Dict[str, Any]:
    """
    Effective `intent_result` for `ChatContextBuilder._build_dynamic_context` + `transit_win`:
    merges caller intent with defaults, then widens or narrows by scope (legacy-style).
    """
    sc = scope if scope is not None else effective_time_scope(ctx)
    birth = getattr(ctx, "birth_data", None) or {}
    cy = datetime.now().year
    by = _birth_year(birth if isinstance(birth, dict) else None)

    base = _default_transit_intent(cy)
    raw = getattr(ctx, "intent_result", None)
    if not isinstance(raw, dict):
        raw = {}

    out: Dict[str, Any] = {**base, **raw}
    if not out.get("needs_transits"):
        out["needs_transits"] = True

    rp = getattr(ctx, "requested_period", None)
    if isinstance(rp, dict):
        sy = rp.get("startYear") or rp.get("start_year")
        ey = rp.get("endYear") or rp.get("end_year")
        if sy is not None:
            try:
                sy_i = int(sy)
                ey_i = int(ey) if ey is not None else sy_i
                tr = dict(out.get("transit_request") or {})
                tr["startYear"] = sy_i
                tr["endYear"] = ey_i
                out["transit_request"] = tr
            except (TypeError, ValueError):
                pass

    tr_merged = dict(base["transit_request"])
    user_tr = out.get("transit_request")
    if isinstance(user_tr, dict):
        tr_merged.update(user_tr)
    out["transit_request"] = tr_merged

    if sc == ContextTimeScope.FULL:
        ey_wide = min(by + 100, cy + 80)
        out["transit_request"] = {
            **tr_merged,
            "startYear": by,
            "endYear": max(ey_wide, tr_merged.get("endYear") or ey_wide),
        }
        # Avoid multi-MB yearMonthMap for century spans
        if (out["transit_request"].get("endYear", ey_wide) - out["transit_request"].get("startYear", by)) > 15:
            out["transit_request"]["yearMonthMap"] = {}

    elif sc == ContextTimeScope.CURRENT:
        out["transit_request"] = {
            **tr_merged,
            "startYear": cy,
            "endYear": cy + 2,
        }

    return out


def intent_for_dasha_window(
    ctx: Any,
    scope: Optional[ContextTimeScope] = None,
) -> Optional[Dict[str, Any]]:
    """
    Effective intent for `dasha_win._parse_window`: FULL → life-wide range; CURRENT → anchor “today”;
    INTENT_WINDOW → merged transit_request / requested_period (legacy-style).
    """
    sc = scope if scope is not None else effective_time_scope(ctx)
    birth = getattr(ctx, "birth_data", None) or {}
    if not isinstance(birth, dict):
        birth = {}
    by = _birth_year(birth)
    cy = datetime.now().year
    raw = getattr(ctx, "intent_result", None)
    base: Dict[str, Any] = dict(raw) if isinstance(raw, dict) else {}

    if sc == ContextTimeScope.FULL:
        return {
            **base,
            "transit_request": {
                "startYear": by,
                "endYear": min(by + 100, cy + 85),
            },
        }

    if sc == ContextTimeScope.CURRENT:
        today = datetime.now().strftime("%Y-%m-%d")
        return {**base, "dasha_as_of": base.get("dasha_as_of") or today}

    return intent_for_transit_build(ctx, scope=ContextTimeScope.INTENT_WINDOW)


def filter_chara_periods(
    periods: List[Dict[str, Any]],
    scope: ContextTimeScope,
    intent_result: Optional[Dict[str, Any]],
    focus_date: datetime,
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Same filtering idea as `chat_context_builder` Chara block: overlap window, or current MD only.
    FULL returns all periods unchanged.
    """
    if scope == ContextTimeScope.FULL or not periods:
        return list(periods), "full_cycle"

    ir: Dict[str, Any] = intent_result if isinstance(intent_result, dict) else {}

    if scope == ContextTimeScope.INTENT_WINDOW:
        tr = ir.get("transit_request")
        if isinstance(tr, dict):
            sy = tr.get("startYear") or tr.get("start_year")
            ey = tr.get("endYear") or tr.get("end_year")
            if sy is not None:
                try:
                    period_start = datetime(int(sy), 1, 1)
                    period_end = datetime(int(ey), 12, 31) if ey is not None else datetime(int(sy), 12, 31)
                    filtered: List[Dict[str, Any]] = []
                    for period in periods:
                        p_start = datetime.strptime(period["start_date"], "%Y-%m-%d")
                        p_end = datetime.strptime(period["end_date"], "%Y-%m-%d")
                        if p_start <= period_end and p_end >= period_start:
                            period = dict(period)
                            period["is_current"] = p_start <= focus_date < p_end
                            filtered.append(period)
                    return filtered, "intent_overlap"
                except (TypeError, ValueError, KeyError):
                    pass

    # CURRENT (default): single active MD
    for period in periods:
        try:
            p_start = datetime.strptime(period["start_date"], "%Y-%m-%d")
            p_end = datetime.strptime(period["end_date"], "%Y-%m-%d")
            if p_start <= focus_date < p_end:
                q = dict(period)
                q["is_current"] = True
                q["note"] = "ACTIVE_PERIOD"
                return [q], "current_md"
        except (KeyError, ValueError, TypeError):
            continue
    return [], "no_match"
