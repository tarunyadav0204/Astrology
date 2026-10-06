"""Deterministic phase and boundary facts for explicit source periods."""

from __future__ import annotations

from datetime import date
from typing import Any, Mapping

from .age_timing import AgeTimingInputError, parse_civil_date
from .period_timing import PeriodTimingInputError, SourcePeriod, named_period_expression


PERIOD_PHASE_VERSION = "deva-keralam-period-phase/1.0.0"
WINDOW_FIELDS = (
    "start_proximity_days",
    "end_proximity_days",
    "junction_tolerance_days",
)


def _window_config(raw: Any, slot: int) -> dict[str, int]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise PeriodTimingInputError(f"source_periods[{slot}].phase_window must be an object")
    unknown = set(raw) - set(WINDOW_FIELDS)
    if unknown:
        raise PeriodTimingInputError(
            f"source_periods[{slot}].phase_window has unknown fields: {sorted(unknown)!r}"
        )
    values: dict[str, int] = {}
    for field, value in raw.items():
        if type(value) is not int or value < 0:
            raise PeriodTimingInputError(
                f"source_periods[{slot}].phase_window.{field} must be a non-negative integer"
            )
        values[field] = value
    return values


def calculate_period_phase_facts(
    period: SourcePeriod, *, as_of: Any, phase_window: Any = None,
) -> dict[str, Any]:
    try:
        current = parse_civil_date(as_of, "timing.as_of")
    except AgeTimingInputError as exc:
        raise PeriodTimingInputError(str(exc)) from exc
    windows = _window_config(phase_window, period.slot)
    duration = (period.end_exclusive - period.start).days
    elapsed = (current - period.start).days
    remaining = (period.end_exclusive - current).days
    active_progress = elapsed / duration if period.active else None
    values: dict[str, Any] = {
        "duration_days": duration,
        "elapsed_days": elapsed,
        "remaining_days": remaining,
        "progress_fraction": None if active_progress is None else round(active_progress, 12),
        "half": (
            "outside" if active_progress is None else
            ("first" if active_progress < 0.5 else "second")
        ),
        "third": (
            "outside" if active_progress is None else
            ("first" if active_progress < (1 / 3) else ("middle" if active_progress < (2 / 3) else "last"))
        ),
    }

    if "start_proximity_days" in windows:
        tolerance = windows["start_proximity_days"]
        values["start_proximity_days"] = tolerance
        values["near_start"] = abs(elapsed) <= tolerance
    if "end_proximity_days" in windows:
        tolerance = windows["end_proximity_days"]
        values["end_proximity_days"] = tolerance
        values["near_end"] = abs(remaining) <= tolerance
    if "near_start" in values and "near_end" in values:
        values["proximity_overlap"] = bool(values["near_start"] and values["near_end"])

    if "junction_tolerance_days" in windows:
        tolerance = windows["junction_tolerance_days"]
        near_start = abs(elapsed) <= tolerance
        near_end = abs(remaining) <= tolerance
        values.update({
            "junction_tolerance_days": tolerance,
            "near_start_junction": near_start,
            "near_end_junction": near_end,
            "near_junction": near_start or near_end,
            "junction_boundary": (
                "both" if near_start and near_end else
                ("start" if near_start else ("end" if near_end else "none"))
            ),
        })
    return values


def period_phase_expression(
    *, slot: int, system: str, level: str, name: str, lord: str,
    half: str | None = None, third: str | None = None,
) -> dict[str, Any]:
    if (half is None) == (third is None):
        raise PeriodTimingInputError("choose exactly one of half or third")
    if half is not None and half not in {"first", "second"}:
        raise PeriodTimingInputError("half must be first or second")
    if third is not None and third not in {"first", "middle", "last"}:
        raise PeriodTimingInputError("third must be first, middle, or last")
    selector = named_period_expression(slot=slot, system=system, level=level, name=name, lord=lord)
    suffix, value = ("half", half) if half is not None else ("third", third)
    return {
        "op": "all",
        "children": [
            selector,
            {
                "op": "fact",
                "key": f"deva_keralam.timing.period.{slot}.{suffix}",
                "comparator": "equals",
                "value": value,
            },
        ],
    }


def period_proximity_expression(
    *, slot: int, system: str, level: str, name: str, lord: str,
    boundary: str, window_days: int,
) -> dict[str, Any]:
    if boundary not in {"start", "end"}:
        raise PeriodTimingInputError("boundary must be start or end")
    if type(window_days) is not int or window_days < 0:
        raise PeriodTimingInputError("window_days must be a non-negative integer")
    selector = named_period_expression(slot=slot, system=system, level=level, name=name, lord=lord)
    prefix = f"deva_keralam.timing.period.{slot}"
    return {
        "op": "all",
        "children": [
            selector,
            {"op": "fact", "key": f"{prefix}.{boundary}_proximity_days", "comparator": "equals", "value": window_days},
            {"op": "fact", "key": f"{prefix}.near_{boundary}", "comparator": "equals", "value": True},
        ],
    }


def period_junction_expression(
    *, slot: int, system: str, level: str, name: str, lord: str,
    boundary: str, tolerance_days: int,
) -> dict[str, Any]:
    if boundary not in {"start", "end", "either"}:
        raise PeriodTimingInputError("junction boundary must be start, end, or either")
    if type(tolerance_days) is not int or tolerance_days < 0:
        raise PeriodTimingInputError("tolerance_days must be a non-negative integer")
    selector = named_period_expression(slot=slot, system=system, level=level, name=name, lord=lord)
    prefix = f"deva_keralam.timing.period.{slot}"
    fact = "near_junction" if boundary == "either" else f"near_{boundary}_junction"
    return {
        "op": "all",
        "children": [
            selector,
            {"op": "fact", "key": f"{prefix}.junction_tolerance_days", "comparator": "equals", "value": tolerance_days},
            {"op": "fact", "key": f"{prefix}.{fact}", "comparator": "equals", "value": True},
        ],
    }
