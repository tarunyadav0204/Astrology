"""Progressive, no-leak marriage date narrowing for Instant Chat."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Mapping

from shared.dasha_calculator import DashaCalculator


MARRIAGE_HOUSES = (2, 7, 11)
SELECTION_TYPE = "marriage_timeline_selection"


def _date(value: Any) -> datetime:
    return datetime.strptime(str(value or "")[:10], "%Y-%m-%d")


def _date_label(value: Any) -> str:
    return _date(value).strftime("%d %b %Y")


def _range_label(start: Any, end: Any) -> str:
    return f"{_date_label(start)} – {_date_label(end)}"


def _selection_context(intent: Mapping[str, Any] | None) -> Dict[str, Any]:
    intent = intent if isinstance(intent, Mapping) else {}
    value = intent.get("query_context")
    return dict(value) if isinstance(value, Mapping) else {}


def timeline_selection(intent: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    context = _selection_context(intent)
    if str(context.get("follow_up_type") or "").strip().lower() != SELECTION_TYPE:
        return None
    selected = context.get("marriage_timeline_selection")
    if not isinstance(selected, Mapping):
        return None
    return {
        "stage": str(context.get("marriage_timeline_stage") or "").strip().lower(),
        "selection": dict(selected),
        "disclosure_level": str(
            context.get("marriage_timeline_disclosure") or "period_selected"
        ).strip().lower(),
    }


def apply_timeline_intent_guard(intent: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Keep a structured selection inside retrospective marriage timing."""
    if not isinstance(intent, dict) or timeline_selection(intent) is None:
        return intent
    intent["category"] = "marriage"
    intent["mode"] = "LIFESPAN_EVENT_TIMING"
    intent["answer_mode"] = "event_prediction"
    intent["time_relation"] = "past"
    intent["turn_relation"] = "follow_up"
    intent["needs_transits"] = True
    intent["evidence_plan"] = {
        "question_parts": [{
            "part_id": "marriage-history-refinement",
            "intent_families": ["event_timing"],
            "life_domain": "marriage",
            "event_profile": "marriage",
            "timeframe": {"kind": "open_past"},
        }],
        "evidence_needs": [
            {"kind": "historical_dasha_event_windows", "event_profile": "marriage"},
            {"kind": "historical_transit_event_windows", "event_profile": "marriage"},
            {"kind": "natal_topic_foundation", "event_profile": "marriage"},
        ],
    }
    return intent


def _option(
    *,
    option_id: str,
    label: str,
    detail: str,
    stage: str,
    selection: Mapping[str, Any],
    rank: int | None = None,
) -> Dict[str, Any]:
    submit_text = f"Selected: {label}"
    if stage == "date":
        primary_label = label
        technical_label = ""
        evidence_hint = detail
    else:
        detail_parts = str(detail or "").split(" · ", 1)
        primary_label = detail_parts[0]
        technical_label = label
        evidence_hint = detail_parts[1] if len(detail_parts) > 1 else ""
    return {
        "id": option_id,
        "label": label,
        "detail": detail,
        "primary_label": primary_label,
        "technical_label": technical_label,
        "evidence_hint": evidence_hint,
        "rank": rank,
        "submit_text": submit_text,
        "query_context": {
            "follow_up_type": SELECTION_TYPE,
            "marriage_timeline_stage": stage,
            "marriage_timeline_selection": dict(selection),
            "marriage_timeline_disclosure": (
                "candidate_date_selected" if stage == "date" else "period_selected"
            ),
            "category": "marriage",
            "answer_mode": "event_prediction",
            "suppress_mode_intro": True,
        },
    }


def build_phase_action(verdict: Mapping[str, Any] | None) -> Dict[str, Any] | None:
    verdict = verdict if isinstance(verdict, Mapping) else {}
    rows = [row for row in verdict.get("ranked_windows") or [] if isinstance(row, Mapping)]
    options = []
    for index, row in enumerate(rows[:3], start=1):
        md = str(row.get("mahadasha") or "")
        ad = str(row.get("antardasha") or "")
        start, end = row.get("start"), row.get("end")
        if not (md and ad and start and end):
            continue
        options.append(_option(
            option_id=f"phase-{index}-{md}-{ad}-{start}",
            label=f"{md}–{ad}",
            detail=_range_label(start, end),
            stage="phase",
            rank=index,
            selection={
                "mahadasha": md,
                "antardasha": ad,
                "start": str(start)[:10],
                "end": str(end)[:10],
                "rank": index,
            },
        ))
    if not options:
        return None
    return {
        "type": "timeline_selection",
        "flow": "marriage_date_finder",
        "selection_stage": "phase",
        "title": "Which date range is closest?",
        "reason": "Select the closest range and I’ll narrow it step by step. Your exact date has not been supplied.",
        "confidence": "probabilistic",
        "options": options,
        "disclosure_state": {"exact_date_known": False, "highest_disclosure": "none"},
        "source": "instant_marriage_timeline",
    }


def _kp_planet_houses(birth_data: Mapping[str, Any]) -> Dict[str, set[int]]:
    try:
        from app.kp.services.chart_service import KPChartService

        result = KPChartService.calculate_kp_chart(
            birth_data.get("date"), birth_data.get("time"),
            birth_data.get("latitude"), birth_data.get("longitude"),
            birth_data.get("timezone"),
        )
    except Exception:
        return {}
    raw = result.get("planet_significators") if isinstance(result, Mapping) else {}
    out: Dict[str, set[int]] = {}
    for planet, houses in (raw or {}).items():
        values: set[int] = set()
        for house in houses if isinstance(houses, (list, tuple, set)) else []:
            try:
                values.add(int(house))
            except (TypeError, ValueError):
                pass
        out[str(planet)] = values
    return out


def _coverage(planets: Iterable[str], kp_houses: Mapping[str, set[int]]) -> tuple[int, list[int]]:
    houses: set[int] = set()
    for planet in planets:
        houses.update(kp_houses.get(str(planet), set()))
    matched = sorted(houses.intersection(MARRIAGE_HOUSES))
    return len(matched), matched


def _rank_periods(
    rows: list[Dict[str, Any]],
    *,
    fixed_planets: list[str],
    planet_key: str,
    kp_houses: Mapping[str, set[int]],
) -> list[Dict[str, Any]]:
    ranked = []
    for row in rows:
        planet = str(row.get(planet_key) or row.get("planet") or "")
        direct = sorted(kp_houses.get(planet, set()).intersection(MARRIAGE_HOUSES))
        coverage_count, coverage = _coverage([*fixed_planets, planet], kp_houses)
        ranked.append({
            **row,
            "planet": planet,
            "direct_marriage_houses": direct,
            "chain_marriage_houses": coverage,
            "score": coverage_count * 100 + len(direct) * 20,
        })
    ranked.sort(key=lambda row: (-int(row.get("score") or 0), str(row.get("start") or "")))
    return ranked


def _action(
    *,
    stage: str,
    title: str,
    reason: str,
    options: list[Dict[str, Any]],
    disclosure: str = "period_selected",
) -> Dict[str, Any]:
    return {
        "type": "timeline_selection",
        "flow": "marriage_date_finder",
        "selection_stage": stage,
        "title": title,
        "reason": reason,
        "confidence": "probabilistic",
        "options": options,
        "disclosure_state": {
            "exact_date_known": disclosure == "candidate_date_selected",
            "highest_disclosure": disclosure,
        },
        "source": "instant_marriage_timeline",
    }


def _period_detail(row: Mapping[str, Any]) -> str:
    direct = ", ".join(str(value) for value in row.get("direct_marriage_houses") or [])
    suffix = f" · KP {direct}" if direct else " · background support"
    return f"{_range_label(row.get('start'), row.get('end'))}{suffix}"


def _pd_action(birth_data: Mapping[str, Any], selected: Mapping[str, Any]) -> Dict[str, Any]:
    start, end = _date(selected.get("start")), _date(selected.get("end"))
    md, ad = str(selected.get("mahadasha") or ""), str(selected.get("antardasha") or "")
    raw = DashaCalculator().get_dasha_periods_for_range(dict(birth_data), start, end, strict=True)
    rows = [
        {
            "start": row.get("start_date"), "end": row.get("end_date"),
            "mahadasha": row.get("mahadasha"), "antardasha": row.get("antardasha"),
            "pratyantardasha": row.get("pratyantardasha"),
        }
        for row in raw
        if row.get("mahadasha") == md and row.get("antardasha") == ad
    ]
    ranked = _rank_periods(rows, fixed_planets=[md, ad], planet_key="pratyantardasha", kp_houses=_kp_planet_houses(birth_data))
    options = []
    for rank, row in enumerate(ranked, start=1):
        pd = row["planet"]
        selection = {
            "mahadasha": md, "antardasha": ad, "pratyantardasha": pd,
            "phase_start": str(selected.get("start"))[:10], "phase_end": str(selected.get("end"))[:10],
            "start": row["start"], "end": row["end"], "rank": rank,
        }
        options.append(_option(
            option_id=f"pd-{md}-{ad}-{pd}-{row['start']}",
            label=f"{md}–{ad}–{pd}", detail=_period_detail(row),
            stage="pd", selection=selection, rank=rank,
        ))
    return _action(
        stage="pd", title="Which narrower date range is closest?",
        reason="Choose a range within the period you selected. All choices remain probabilistic.", options=options,
    )


def _resolve_selected_levels(birth_data: Mapping[str, Any], selected: Mapping[str, Any]) -> tuple[DashaCalculator, Dict[str, Any], datetime]:
    start, end = _date(selected.get("start")), _date(selected.get("end"))
    anchor = start + (end - start) / 2
    calc = DashaCalculator()
    return calc, calc._resolve_levels_at(dict(birth_data), anchor, strict=True), anchor


def _micro_action(birth_data: Mapping[str, Any], selected: Mapping[str, Any], *, level: str) -> Dict[str, Any]:
    calc, levels, anchor = _resolve_selected_levels(birth_data, selected)
    md = str(selected.get("mahadasha") or levels["mahadasha"].get("planet") or "")
    ad = str(selected.get("antardasha") or levels["antardasha"].get("planet") or "")
    pd = str(selected.get("pratyantardasha") or levels["pratyantardasha"].get("planet") or "")
    kp = _kp_planet_houses(birth_data)
    if level == "sk":
        raw = calc.list_sookshmas(levels["mahadasha"], levels["antardasha"], levels["pratyantardasha"], anchor)
        rows = [{"start": row["start"], "end": row["end"], "sookshma": row["planet"]} for row in raw]
        ranked = _rank_periods(rows, fixed_planets=[md, ad, pd], planet_key="sookshma", kp_houses=kp)
        options = []
        for rank, row in enumerate(ranked, start=1):
            sk = row["planet"]
            value = {**dict(selected), "sookshma": sk, "start": row["start"], "end": row["end"], "rank": rank}
            options.append(_option(
                option_id=f"sk-{pd}-{sk}-{row['start']}", label=f"Sookshma {sk}",
                detail=_period_detail(row), stage="sookshma", selection=value, rank=rank,
            ))
        return _action(stage="sookshma", title="Narrow it to a shorter date range", reason="Choose the range closest to your life timeline.", options=options)

    sk = str(selected.get("sookshma") or levels["sookshma"].get("planet") or "")
    # Resolve the exact selected SK from the PD timeline before listing Pranas.
    sk_rows = calc.list_sookshmas(levels["mahadasha"], levels["antardasha"], levels["pratyantardasha"])
    selected_sk = next(
        (row for row in sk_rows if row.get("planet") == sk and str(row.get("start"))[:10] == str(selected.get("start"))[:10]),
        levels["sookshma"],
    )
    raw = calc.list_pranas(levels["mahadasha"], levels["antardasha"], levels["pratyantardasha"], selected_sk)
    rows = [{"start": row["start"], "end": row["end"], "prana": row["planet"]} for row in raw]
    ranked = _rank_periods(rows, fixed_planets=[md, ad, pd, sk], planet_key="prana", kp_houses=kp)
    options = []
    for rank, row in enumerate(ranked, start=1):
        prana = row["planet"]
        value = {**dict(selected), "prana": prana, "start": row["start"], "end": row["end"], "rank": rank}
        options.append(_option(
            option_id=f"pr-{sk}-{prana}-{row['start']}", label=f"Prana {prana}",
            detail=_period_detail(row), stage="prana", selection=value, rank=rank,
        ))
    return _action(stage="prana", title="Narrow it one step further", reason="Choose the closest short date range.", options=options)


def _date_action(selected: Mapping[str, Any]) -> Dict[str, Any]:
    start, end = _date(selected.get("start")), _date(selected.get("end"))
    options = []
    current = start.date()
    last = end.date()
    while current <= last and len(options) < 14:
        iso = current.isoformat()
        value = {**dict(selected), "date": iso, "start": iso, "end": iso}
        options.append(_option(
            option_id=f"date-{iso}", label=datetime.combine(current, datetime.min.time()).strftime("%d %B %Y"),
            detail="Candidate day inside the selected Prana window", stage="date", selection=value,
        ))
        current += timedelta(days=1)
    return _action(
        stage="date", title="Choose the closest candidate date",
        reason="These dates come from your selected micro-window; selecting one begins verification, not discovery.",
        options=options,
    )


def _verification_response(birth_data: Mapping[str, Any], selected: Mapping[str, Any]) -> Dict[str, Any]:
    target = _date(selected.get("date") or selected.get("start")).replace(hour=12)
    levels = DashaCalculator()._resolve_levels_at(dict(birth_data), target, strict=True)
    chain = [levels[key].get("planet") for key in ("mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana")]
    kp = _kp_planet_houses(birth_data)
    coverage_count, coverage = _coverage([str(value) for value in chain], kp)
    return {
        "date": target.strftime("%d %B %Y"),
        "chain": "–".join(str(value) for value in chain if value),
        "coverage": coverage,
        "coverage_complete": coverage_count == len(MARRIAGE_HOUSES),
    }


def build_selection_response(
    *, birth_data: Mapping[str, Any], intent: Mapping[str, Any] | None,
) -> Dict[str, Any] | None:
    state = timeline_selection(intent)
    if state is None:
        return None
    stage, selected = state["stage"], state["selection"]
    if stage == "phase":
        action = _pd_action(birth_data, selected)
        body = "Now choose the PD sub-period that is closest to your life timeline."
    elif stage == "pd":
        action = _micro_action(birth_data, selected, level="sk")
        body = "The selected PD is now divided into Sookshma windows."
    elif stage == "sookshma":
        action = _micro_action(birth_data, selected, level="prana")
        body = "The selected Sookshma window is now divided into Prana windows."
    elif stage == "prana":
        action = _date_action(selected)
        body = "This Prana window narrows the search to these candidate calendar dates."
    elif stage == "date":
        verification = _verification_response(birth_data, selected)
        complete = verification["coverage_complete"]
        body = (
            f"You selected {verification['date']}. This is now a user-selected date verification, not a date the chart independently discovered. "
            f"The exact Vimshottari chain is {verification['chain']}. Its KP significators collectively activate marriage houses "
            f"{', '.join(str(value) for value in verification['coverage'])}. "
            + (
                "That completes the core KP 2–7–11 marriage combination."
                if complete else
                "That gives partial KP marriage support, so the date should remain a qualified match."
            )
        )
        action = None
    else:
        return None
    return {"body": body, "next_action": action, "stage": stage}
