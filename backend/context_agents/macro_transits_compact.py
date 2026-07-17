"""
Compact slow-planet sign timelines for LLM payloads.

`macro_transits_timeline` is the ephemeris authority for Jupiter/Saturn/Rahu/Ketu
sign ingress years. Agent Parashari historically dropped it; these helpers keep a
small, prompt-safe copy in `transit_win.M`, `px.TR.MT`, and free-question finals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

_SLOW_PLANETS = ("Jupiter", "Saturn", "Rahu", "Ketu")
_DEFAULT_MAX_PER_PLANET = 16


def _year_window_bounds(
    start_year: Optional[int],
    end_year: Optional[int],
) -> Optional[Tuple[str, str]]:
    if start_year is None and end_year is None:
        return None
    sy = int(start_year if start_year is not None else end_year)
    ey = int(end_year if end_year is not None else start_year)
    if ey < sy:
        sy, ey = ey, sy
    return (f"{sy:04d}-01-01", f"{ey:04d}-12-31")


def _overlaps(sd: Any, ed: Any, win_start: str, win_end: str) -> bool:
    s = str(sd or "")[:10]
    e = str(ed or "")[:10]
    if not s:
        return False
    if not e:
        e = s
    return s <= win_end and e >= win_start


def compact_macro_transits_timeline(
    macro: Any,
    *,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    max_per_planet: int = _DEFAULT_MAX_PER_PLANET,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Shrink `macro_transits_timeline` to prompt-safe rows.

    Each period becomes:
      { "sg": sign, "h": house, "sd": start_date, "ed": end_date, "rr": retrograde_return }
    """
    if not isinstance(macro, dict) or not macro:
        return {}

    bounds = _year_window_bounds(start_year, end_year)
    out: Dict[str, List[Dict[str, Any]]] = {}
    cap = max(1, int(max_per_planet or _DEFAULT_MAX_PER_PLANET))

    for planet in _SLOW_PLANETS:
        periods = macro.get(planet)
        if not isinstance(periods, list):
            continue
        rows: List[Dict[str, Any]] = []
        for period in periods:
            if not isinstance(period, dict):
                continue
            sd = period.get("start_date")
            ed = period.get("end_date")
            if bounds and not _overlaps(sd, ed, bounds[0], bounds[1]):
                continue
            sign = period.get("sign")
            if not sign and not sd:
                continue
            row: Dict[str, Any] = {
                "sg": sign,
                "sd": sd,
                "ed": ed,
            }
            if period.get("house") is not None:
                row["h"] = period.get("house")
            if period.get("retrograde_return"):
                row["rr"] = True
            rows.append(row)
            if len(rows) >= cap:
                break
        if rows:
            out[planet] = rows
    return out


def authoritative_slow_transits_packet(
    ctx: Dict[str, Any],
    *,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Packet for free-question / merge finals — cite only these ingress dates."""
    macro = ctx.get("macro_transits_timeline") if isinstance(ctx, dict) else None
    compact = compact_macro_transits_timeline(
        macro,
        start_year=start_year,
        end_year=end_year,
    )
    meta = {}
    if isinstance(ctx, dict) and isinstance(ctx.get("macro_transits_meta"), dict):
        meta = {
            k: ctx["macro_transits_meta"].get(k)
            for k in ("start", "end", "note")
            if ctx["macro_transits_meta"].get(k) is not None
        }
    return {
        "authority": "macro_transits_timeline",
        "planets": compact,
        "meta": meta or None,
        "rule": (
            "Cite ONLY these start_date/end_date values for Jupiter/Saturn/Rahu/Ketu "
            "sign or house changes. Never invent ingress years from memory. "
            "If a planet/sign is absent, say unavailable — do not estimate."
        ),
    }
