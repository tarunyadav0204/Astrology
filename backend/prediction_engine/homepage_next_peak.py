from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

from calculators.chart_calculator import ChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from shared.dasha_calculator import DashaCalculator

from chat.instant_chat_pipeline import (
    _as_naive_local_datetime,
    _build_forward_event_dasha_scan,
    _get_house_lordships,
    _parse_ymd,
)

HOMEPAGE_NEXT_PEAK_HORIZON_DAYS = 120
PD_HANDOFF_DAYS = 21
MAX_DISPLAY_HOUSES = 3
MIN_DIRECT_HOUSE_SCORE = 60
MIN_RELATIVE_HOUSE_SCORE = 0.45


def _ascendant_sign_index(chart: Dict[str, Any]) -> int:
    return int(float(chart["ascendant"]) / 30.0)


def _house_scores_from_period(period: Dict[str, Any]) -> Dict[int, int]:
    """Score only houses directly delivered by a transit trigger.

    ``activated_focus_houses`` can fall back to every natal house connected to
    a dasha carrier.  That is useful calculation context, but it is too broad
    to tell a user that all of those life areas are actively manifesting.
    """
    scores: Dict[int, int] = {}
    peaks = list(period.get("peak_activation_windows") or [])
    if not peaks:
        peaks = [
            row
            for row in (period.get("transit_trigger_windows") or [])
            if str(row.get("strength") or "") in {"high", "medium"}
        ]
    for peak in peaks:
        state_weight = 100 if str(peak.get("strength") or "") == "high" else 60
        trigger_score = int(peak.get("trigger_score") or 0)
        for detail in peak.get("delivered_event_houses") or []:
            house = detail.get("native_house") or detail.get("house")
            if house is None:
                continue
            native_house = int(house)
            scores[native_house] = scores.get(native_house, 0) + state_weight + trigger_score
    return scores


def _background_house_scores(period: Dict[str, Any]) -> Dict[int, int]:
    """Rank the current/forthcoming PD's natal themes for a quiet fallback."""
    scores: Dict[int, int] = {}
    pd = str(period.get("pratyantardasha") or "").strip()
    for carrier in period.get("carrier_planets") or []:
        levels = {str(level).lower() for level in (carrier.get("dasha_levels") or [])}
        if "pd" not in levels and str(carrier.get("planet") or "").strip() != pd:
            continue
        event_links = list(carrier.get("event_links") or [])
        for link in event_links:
            house = link.get("house") or link.get("native_house")
            if house is None:
                continue
            mechanisms = {str(item) for item in (link.get("mechanisms") or [])}
            score = 0
            if "natal_occupation" in mechanisms:
                score += 45
            if "lordship" in mechanisms:
                score += 35
            if "natal_aspect" in mechanisms:
                score += 20
            native_house = int(house)
            scores[native_house] = scores.get(native_house, 0) + max(score, 10)
        if not event_links:
            for house in carrier.get("natal_event_houses") or []:
                if house is None:
                    continue
                native_house = int(house)
                scores[native_house] = scores.get(native_house, 0) + 30
    # Older/cached scan rows may not contain carrier detail. Keep the fallback
    # useful, while still applying the strict three-area cap below.
    if not scores:
        for house in period.get("activated_focus_houses") or []:
            if house is None:
                continue
            native_house = int(house)
            scores[native_house] = scores.get(native_house, 0) + 10
    return scores


def _rank_display_houses(
    scores: Dict[int, int],
    *,
    state: str,
    direct: bool,
) -> List[Dict[str, Any]]:
    valid = [(house, score) for house, score in scores.items() if 1 <= house <= 12]
    if not valid:
        return []
    valid.sort(key=lambda item: (-item[1], item[0]))
    top_score = valid[0][1]
    rows = []
    for house, score in valid:
        if direct and (
            score < MIN_DIRECT_HOUSE_SCORE
            or score < (top_score * MIN_RELATIVE_HOUSE_SCORE)
        ):
            continue
        rows.append({"house": house, "score": score, "state": state})
        if len(rows) >= MAX_DISPLAY_HOUSES:
            break
    return rows


def _display_house_reasons(
    period: Dict[str, Any],
    houses: List[Dict[str, Any]],
    *,
    display_mode: str,
) -> List[Dict[str, Any]]:
    """Attach structured explanation data without baking UI copy into the API."""
    reasons_by_house: Dict[int, Dict[str, Any]] = {}
    if display_mode == "highly_active":
        natal_links_by_house: Dict[int, List[Dict[str, Any]]] = {}
        for carrier in period.get("carrier_planets") or []:
            for link in carrier.get("event_links") or []:
                house = link.get("native_house") or link.get("house")
                if house is None:
                    continue
                natal_links_by_house.setdefault(int(house), []).append({
                    "planet": carrier.get("planet"),
                    "dasha_levels": list(carrier.get("dasha_levels") or []),
                    "natal_house": carrier.get("natal_placement_house"),
                    "mechanisms": list(link.get("mechanisms") or []),
                })
        for links in natal_links_by_house.values():
            links.sort(key=lambda row: (
                -len(row.get("dasha_levels") or []),
                0 if "natal_occupation" in (row.get("mechanisms") or []) else 1,
                str(row.get("planet") or ""),
            ))
        for peak in period.get("peak_activation_windows") or []:
            if str(peak.get("strength") or "") != "high":
                continue
            for detail in peak.get("delivered_event_houses") or []:
                house = detail.get("native_house") or detail.get("house")
                if house is None:
                    continue
                native_house = int(house)
                reasons_by_house.setdefault(native_house, {
                    "kind": "direct_transit",
                    "transit": {
                        "planet": peak.get("planet"),
                        "house": peak.get("transit_native_house"),
                        "mechanism": detail.get("mechanism") or "transit_aspect",
                        "dasha_levels": list(peak.get("dasha_levels") or []),
                    },
                    "natal_support": natal_links_by_house.get(native_house, [])[:2],
                })
    else:
        pd = str(period.get("pratyantardasha") or "").strip()
        for carrier in period.get("carrier_planets") or []:
            levels = {str(level).lower() for level in (carrier.get("dasha_levels") or [])}
            if "pd" not in levels and str(carrier.get("planet") or "").strip() != pd:
                continue
            for link in carrier.get("event_links") or []:
                house = link.get("house") or link.get("native_house")
                if house is None:
                    continue
                mechanisms = list(link.get("mechanisms") or [])
                # Choose the clearest, strongest human explanation.
                mechanism = next(
                    (item for item in ("natal_occupation", "lordship", "natal_aspect") if item in mechanisms),
                    "dasha_connection",
                )
                reasons_by_house[int(house)] = {
                    "kind": "pd_background",
                    "planet": carrier.get("planet") or pd,
                    "mechanism": mechanism,
                    "dasha_levels": list(carrier.get("dasha_levels") or []),
                }
    return [
        {**row, "reason": reasons_by_house.get(int(row["house"]), {
            "kind": "pd_background" if display_mode == "background" else "direct_transit",
            "planet": period.get("pratyantardasha"),
            "mechanism": "dasha_connection",
            "dasha_levels": ["PD"],
        })}
        for row in houses
    ]


def _period_peak_band(period: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    peaks = list(period.get("peak_activation_windows") or [])
    if peaks:
        return (
            min(str(row.get("start") or "") for row in peaks if row.get("start")),
            max(str(row.get("end") or "") for row in peaks if row.get("end")),
        )
    triggers = [
        row
        for row in (period.get("transit_trigger_windows") or [])
        if str(row.get("strength") or "") in {"high", "medium"}
    ]
    if triggers:
        return (
            min(str(row.get("start") or "") for row in triggers if row.get("start")),
            max(str(row.get("end") or "") for row in triggers if row.get("end")),
        )
    start = str(period.get("start") or "").strip()
    end = str(period.get("end") or "").strip()
    if start and end:
        return start, end
    return None


def _period_sort_key(period: Dict[str, Any], *, as_of: date) -> Optional[Tuple[date, int, int]]:
    band = _period_peak_band(period)
    if not band:
        return None
    start = _parse_ymd(band[0])
    end = _parse_ymd(band[1])
    if start is None or end is None or end.date() < as_of:
        return None
    strength_rank = {
        "highly_active": 0,
        "active": 1,
        "background": 2,
    }.get(str(period.get("activation_strength") or ""), 3)
    # A peak already underway is as relevant as one beginning today.
    effective_start = max(start.date(), as_of)
    return (effective_start, strength_rank, -int(period.get("relevance_score") or 0))


def _select_period(
    periods: List[Dict[str, Any]],
    *,
    as_of: date,
    pd_handoff_soon: bool,
) -> Optional[Dict[str, Any]]:
    # A user-facing "Coming up" claim must have a real high-strength transit
    # peak. Choose the nearest such period, not merely the nearest dasha band.
    eligible: List[Tuple[Tuple, Dict[str, Any]]] = []
    for period in periods:
        if str(period.get("activation_strength") or "") != "highly_active":
            continue
        # Strength alone is insufficient for the card. A strong claim must
        # identify at least one house directly delivered by the transit.
        if not _rank_display_houses(
            _house_scores_from_period(period),
            state="fully_reinforced",
            direct=True,
        ):
            continue
        if pd_handoff_soon and str(period.get("time_status") or "") == "current":
            continue
        key = _period_sort_key(period, as_of=as_of)
        if key is not None:
            eligible.append((key, period))
    eligible.sort(key=lambda item: item[0])
    if eligible:
        return eligible[0][1]
    # No high transit peak: show the PD's quieter natal themes instead. When a
    # handoff is imminent, prefer the next PD; otherwise use the current PD.
    preferred_status = "future" if pd_handoff_soon else "current"
    background = [
        period for period in periods
        if str(period.get("time_status") or "") == preferred_status
    ]
    if not background:
        background = list(periods)
    background.sort(key=lambda period: (
        _parse_ymd(period.get("start")) or datetime.max,
        -int(period.get("relevance_score") or 0),
    ))
    if background:
        return background[0]
    return None


def _house_state_from_period(period: Dict[str, Any]) -> str:
    strength = str(period.get("activation_strength") or "")
    if strength == "highly_active":
        return "fully_reinforced"
    if strength == "active":
        return "dasha_transit_activated"
    return "dasha_connected"


def _mechanism_summary(period: Dict[str, Any]) -> str:
    peaks = period.get("peak_activation_windows") or []
    if peaks and peaks[0].get("why"):
        return str(peaks[0]["why"])[:240]
    why = str(period.get("why") or "").strip()
    if why:
        return why[:240]
    pd = str(period.get("pratyantardasha") or "").strip()
    ad = str(period.get("antardasha") or "").strip()
    if pd and ad:
        return f"{pd} PD within {ad} AD re-engages natal themes in this window."
    return "Dasha carriers and transits reinforce several life houses in this window."


def _pd_handoff_payload(
    current_dashas: Dict[str, Any],
    *,
    as_of: date,
) -> Dict[str, Any]:
    pd = current_dashas.get("pratyantardasha") or {}
    end_raw = pd.get("end")
    end_dt = _parse_ymd(end_raw)
    if end_dt is None:
        return {"show": False}
    days_until = (end_dt.date() - as_of).days
    if days_until < 0 or days_until > PD_HANDOFF_DAYS:
        return {"show": False}
    return {
        "show": True,
        "days_until_pd_change": days_until,
        "current_pd_planet": str(pd.get("planet") or "").strip() or None,
        "pd_end": end_dt.date().isoformat(),
    }


def _next_pd_planet(periods: List[Dict[str, Any]], current_pd: Optional[str]) -> Optional[str]:
    current = str(current_pd or "").strip()
    for period in periods:
        if str(period.get("time_status") or "") != "future":
            continue
        candidate = str(period.get("pratyantardasha") or "").strip()
        if candidate and candidate != current:
            return candidate
    return None


def generate_homepage_next_peak(
    chart: Dict[str, Any],
    *,
    as_of: Optional[date] = None,
    horizon_days: int = HOMEPAGE_NEXT_PEAK_HORIZON_DAYS,
) -> Dict[str, Any]:
    as_of = as_of or date.today()
    now_local = _as_naive_local_datetime(datetime.combine(as_of, datetime.min.time()))
    end_local = now_local + timedelta(days=max(horizon_days, 7))

    birth_data = dict(chart)
    birth_data["date"] = str(birth_data.get("date") or "").split("T", 1)[0]
    raw_time = str(birth_data.get("time") or "")
    birth_data["time"] = raw_time.split("T", 1)[-1][:8] if "T" in raw_time else raw_time[:8]

    try:
        natal_chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth_data))
        ascendant_longitude = float(natal_chart["ascendant"])
        house_lordships = _get_house_lordships(_ascendant_sign_index(natal_chart))
    except Exception:
        return {"status": "error", "peak": None}

    dasha_calc = DashaCalculator()
    try:
        current_dashas = dasha_calc.calculate_current_dashas(birth_data, now_local)
        raw_periods = dasha_calc.get_dasha_periods_for_range(birth_data, now_local, end_local)
    except Exception:
        return {"status": "error", "peak": None}

    transit_calc = RealTransitCalculator()

    scan = _build_forward_event_dasha_scan(
        birth_data=birth_data,
        now_local=now_local,
        house_lordships=house_lordships,
        focus_houses=list(range(1, 13)),
        category="general",
        chart_data=natal_chart,
        transit_calc=transit_calc,
        ascendant_longitude=ascendant_longitude,
        current_dashas=current_dashas,
        limit=24,
        raw_periods=raw_periods,
    )
    periods = list(scan.get("periods") or [])
    pd_handoff = _pd_handoff_payload(current_dashas, as_of=as_of)
    if pd_handoff.get("show"):
        pd_handoff["next_pd_planet"] = _next_pd_planet(
            periods,
            (current_dashas.get("pratyantardasha") or {}).get("planet"),
        )

    selected = _select_period(
        periods,
        as_of=as_of,
        pd_handoff_soon=bool(pd_handoff.get("show")),
    )
    if not selected:
        return {"status": "empty", "peak": None, "pd_handoff": pd_handoff}

    direct_scores = _house_scores_from_period(selected)
    direct_houses = _rank_display_houses(
        direct_scores,
        state=_house_state_from_period(selected),
        direct=True,
    )
    display_mode = (
        "highly_active"
        if str(selected.get("activation_strength") or "") == "highly_active" and direct_houses
        else "background"
    )
    band = _period_peak_band(selected)
    if not band:
        return {"status": "empty", "peak": None, "pd_handoff": pd_handoff}

    if display_mode == "background":
        # A current PD may have begun in the past. The card describes what is
        # quietly active from today onward, not a retroactive date range.
        band_start = _parse_ymd(band[0])
        if band_start is None or band_start.date() < as_of:
            band = (as_of.isoformat(), band[1])

    activated_houses = direct_houses if display_mode == "highly_active" else _rank_display_houses(
        _background_house_scores(selected),
        state="pd_background",
        direct=False,
    )
    activated_houses = _display_house_reasons(
        selected,
        activated_houses,
        display_mode=display_mode,
    )
    if not activated_houses:
        return {
            "status": "theme_only",
            "peak": {
                "peak_start": band[0],
                "peak_end": band[1],
                "days_until_start": max((_parse_ymd(band[0]).date() - as_of).days, 0) if _parse_ymd(band[0]) else None,
                "mahadasha": selected.get("mahadasha"),
                "antardasha": selected.get("antardasha"),
                "pratyantardasha": selected.get("pratyantardasha"),
                "mechanism_summary": _mechanism_summary(selected),
                "activation_strength": selected.get("activation_strength"),
                "display_mode": display_mode,
                "activated_houses": [],
            },
            "pd_handoff": pd_handoff,
        }

    start_dt = _parse_ymd(band[0])
    return {
        "status": "ready",
        "peak": {
            "peak_start": band[0],
            "peak_end": band[1],
            "days_until_start": max((start_dt.date() - as_of).days, 0) if start_dt else None,
            "mahadasha": selected.get("mahadasha"),
            "antardasha": selected.get("antardasha"),
            "pratyantardasha": selected.get("pratyantardasha"),
            "mechanism_summary": _mechanism_summary(selected),
            "activation_strength": selected.get("activation_strength"),
            "display_mode": display_mode,
            "activated_houses": activated_houses,
        },
        "pd_handoff": pd_handoff,
    }
