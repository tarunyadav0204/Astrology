"""Retrospective validation utilities for the longevity calculator.

This module measures deterministic behavior and date discrimination. It does not
turn astrological activations into medical probabilities and must not be used to
tune rules against the same records later reported as validation evidence.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from longevity.calculator import AYU_RANGES, LongevityCalculator
from reports.context.base_context_builder import calculate_chart_for_birth


DEFAULT_DATASET = Path(__file__).with_name("validation_data") / "public_figures_v1.json"


@dataclass(frozen=True)
class ValidationConfig:
    observation_years: int = 5
    event_exclusion_days: int = 60
    convergence_threshold: int = 2
    birth_time_offsets_minutes: tuple[int, ...] = (-15, -5, 0, 5, 15)


def load_cases(path: Path | str = DEFAULT_DATASET) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(cases, list) or not cases:
        raise ValueError("validation dataset must contain a non-empty cases list")
    required = {"id", "name", "birth", "event", "birth_rating", "cause_group", "source_url"}
    for row in cases:
        missing = required.difference(row)
        if missing:
            raise ValueError(f"{row.get('id', '<unknown>')} missing fields: {sorted(missing)}")
    return cases


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)


def _event_window(windows: Iterable[Mapping[str, Any]], event: datetime) -> Mapping[str, Any]:
    stamp = event.strftime("%Y-%m-%d")
    return next(row for row in windows if row["start_date"] <= stamp <= row["end_date"])


def _iter_dates(start: date, end: date) -> Iterable[date]:
    cursor = start
    while cursor <= end:
        yield cursor
        cursor += timedelta(days=1)


def _daily_convergence(windows: Iterable[Mapping[str, Any]], start: date, end: date) -> Dict[date, int]:
    daily: Dict[date, int] = {}
    for row in windows:
        row_start = max(start, date.fromisoformat(row["start_date"]))
        row_end = min(end, date.fromisoformat(row["end_date"]))
        if row_end < row_start:
            continue
        count = int(row["convergence"]["confirmed_systems"])
        for day in _iter_dates(row_start, row_end):
            # A boundary date can appear in adjacent dasha rows. Retain the more
            # conservative maximum and expose boundary overlap separately.
            daily[day] = max(count, daily.get(day, 0))
    return daily


def _shift_birth_time(birth: Mapping[str, Any], minutes: int) -> Dict[str, Any]:
    shifted = dict(birth)
    stamp = datetime.fromisoformat(f"{str(birth['date'])[:10]}T{str(birth['time'])[:8]}") + timedelta(minutes=minutes)
    shifted["date"] = stamp.strftime("%Y-%m-%d")
    shifted["time"] = stamp.strftime("%H:%M:%S")
    return shifted


def _compartment_contains_age(label: str, age: float) -> bool:
    if label == "Alpayu":
        return age <= 36
    if label == "Madhyayu":
        return 36 <= age <= 72
    return age >= 72


def evaluate_case(case: Mapping[str, Any], config: ValidationConfig) -> Dict[str, Any]:
    birth = dict(case["birth"])
    event = _parse_date(case["event"])
    observation_start = event - timedelta(days=round(config.observation_years * 365.2425))
    chart = calculate_chart_for_birth(birth)
    calculator = LongevityCalculator(birth, chart)
    result = calculator.calculate(as_of=observation_start, horizon_years=config.observation_years + 1)
    event_row = _event_window(result["activation_windows"], event)

    start_day = observation_start.date()
    end_day = event.date()
    daily = _daily_convergence(result["activation_windows"], start_day, end_day)
    control_end = end_day - timedelta(days=config.event_exclusion_days + 1)
    control_days = [day for day in _iter_dates(start_day, control_end) if day in daily]
    positive_control_days = sum(daily[day] >= config.convergence_threshold for day in control_days)

    birth_date = date.fromisoformat(str(birth["date"])[:10])
    event_age = (end_day - birth_date).days / 365.2425
    compartment = result["verdict"]["compartment"]

    sensitivity = []
    for offset in config.birth_time_offsets_minutes:
        shifted_birth = _shift_birth_time(birth, offset)
        shifted_chart = calculate_chart_for_birth(shifted_birth)
        shifted = LongevityCalculator(shifted_birth, shifted_chart).calculate(as_of=event, horizon_years=1)
        shifted_event = _event_window(shifted["activation_windows"], event)
        sensitivity.append({
            "offset_minutes": offset,
            "compartment": shifted["verdict"]["compartment"]["label"],
            "components": shifted_event["components"],
            "confirmed_systems": shifted_event["convergence"]["confirmed_systems"],
        })

    return {
        "id": case["id"],
        "name": case["name"],
        "birth_rating": case["birth_rating"],
        "cause_group": case["cause_group"],
        "source_url": case["source_url"],
        "event_date": event.strftime("%Y-%m-%d"),
        "event_age": round(event_age, 2),
        "compartment": compartment["label"],
        "compartment_contains_event_age": _compartment_contains_age(compartment["label"], event_age),
        "event_components": event_row["components"],
        "event_confirmed_systems": event_row["convergence"]["confirmed_systems"],
        "event_hit": event_row["convergence"]["confirmed_systems"] >= config.convergence_threshold,
        "control_days": len(control_days),
        "positive_control_days": positive_control_days,
        "control_positive_rate": round(positive_control_days / len(control_days), 6) if control_days else None,
        "birth_time_sensitivity": sensitivity,
        "birth_time_stable": len({(row["compartment"], row["confirmed_systems"]) for row in sensitivity}) == 1,
    }


def _group_metrics(rows: Sequence[Mapping[str, Any]], threshold: int) -> Dict[str, Any]:
    events = len(rows)
    hits = sum(bool(row["event_hit"]) for row in rows)
    control_days = sum(int(row["control_days"]) for row in rows)
    positive_control_days = sum(int(row["positive_control_days"]) for row in rows)
    event_capture = hits / events if events else 0.0
    control_rate = positive_control_days / control_days if control_days else 0.0
    return {
        "cases": events,
        "threshold": f">={threshold}_of_3_systems",
        "event_hits": hits,
        "event_capture_rate": round(event_capture, 6),
        "control_days": control_days,
        "positive_control_days": positive_control_days,
        "control_positive_rate": round(control_rate, 6),
        "event_lift_over_control_person_time": round(event_capture / control_rate, 4) if control_rate else None,
        "compartment_contains_event_age": sum(bool(row["compartment_contains_event_age"]) for row in rows),
        "birth_time_stable_cases": sum(bool(row["birth_time_stable"]) for row in rows),
    }


def run_validation(cases: Sequence[Mapping[str, Any]], config: ValidationConfig | None = None) -> Dict[str, Any]:
    config = config or ValidationConfig()
    rows = [evaluate_case(case, config) for case in cases]
    groups: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row["cause_group"])].append(row)
    return {
        "schema_version": "longevity.validation.v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "method": {
            "observation_years": config.observation_years,
            "event_exclusion_days": config.event_exclusion_days,
            "convergence_threshold": config.convergence_threshold,
            "birth_time_offsets_minutes": list(config.birth_time_offsets_minutes),
            "warning": "Retrospective descriptive validation only; not a medical or mortality probability model.",
        },
        "overall": _group_metrics(rows, config.convergence_threshold),
        "by_cause_group": {name: _group_metrics(group_rows, config.convergence_threshold) for name, group_rows in sorted(groups.items())},
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run longevity retrospective validation")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--observation-years", type=int, default=5)
    parser.add_argument("--event-exclusion-days", type=int, default=60)
    parser.add_argument("--threshold", type=int, choices=(1, 2, 3), default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = ValidationConfig(
        observation_years=args.observation_years,
        event_exclusion_days=args.event_exclusion_days,
        convergence_threshold=args.threshold,
    )
    report = run_validation(load_cases(args.dataset), config)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
