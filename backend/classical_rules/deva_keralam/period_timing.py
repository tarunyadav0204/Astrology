"""Source-neutral named-period facts for reviewed Deva Keralam timing rules.

The caller must identify the period system. Nothing in this module defaults to
Vimshottari or maps numbered Nadi periods to a modern Dasha sequence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

from .age_timing import AgeTimingInputError, parse_civil_date
from .ontology import PLANETS


PERIOD_TIMING_VERSION = "deva-keralam-source-periods/1.0.0"
MAX_PERIOD_LEVELS = 5


class PeriodTimingInputError(ValueError):
    """A source-neutral period chain is incomplete or contradictory."""


def _required_text(row: Mapping[str, Any], field: str, slot: int) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PeriodTimingInputError(f"source_periods[{slot}].{field} is required")
    return value.strip()


@dataclass(frozen=True)
class SourcePeriod:
    slot: int
    system: str
    level: str
    name: str
    lord: str
    start: date
    end_exclusive: date
    active: bool

    def fact_values(self) -> dict[str, Any]:
        return {
            "system": self.system,
            "level": self.level,
            "name": self.name,
            "lord": self.lord,
            "start": self.start.isoformat(),
            "end_exclusive": self.end_exclusive.isoformat(),
            "active": self.active,
        }


def normalize_source_period_chain(raw_periods: Any, *, as_of: Any) -> tuple[SourcePeriod, ...]:
    if not isinstance(raw_periods, Sequence) or isinstance(raw_periods, (str, bytes)) or not raw_periods:
        raise PeriodTimingInputError("timing.source_periods must be a non-empty ordered list")
    if len(raw_periods) > MAX_PERIOD_LEVELS:
        raise PeriodTimingInputError(f"timing.source_periods supports at most {MAX_PERIOD_LEVELS} nested levels")
    if as_of is None:
        raise PeriodTimingInputError("timing.as_of is required with timing.source_periods")
    try:
        current = parse_civil_date(as_of, "timing.as_of")
    except AgeTimingInputError as exc:
        raise PeriodTimingInputError(str(exc)) from exc

    periods: list[SourcePeriod] = []
    declared_system: str | None = None
    for index, raw in enumerate(raw_periods, start=1):
        if not isinstance(raw, Mapping):
            raise PeriodTimingInputError(f"source_periods[{index}] must be an object")
        system = _required_text(raw, "system", index)
        level = _required_text(raw, "level", index)
        name = _required_text(raw, "name", index)
        lord = _required_text(raw, "lord", index)
        if lord not in PLANETS:
            raise PeriodTimingInputError(f"source_periods[{index}].lord must be a canonical planet")
        if type(raw.get("active")) is not bool:
            raise PeriodTimingInputError(f"source_periods[{index}].active must be a boolean")
        try:
            start = parse_civil_date(raw.get("start"), f"source_periods[{index}].start")
            end = parse_civil_date(raw.get("end_exclusive"), f"source_periods[{index}].end_exclusive")
        except AgeTimingInputError as exc:
            raise PeriodTimingInputError(str(exc)) from exc
        if start >= end:
            raise PeriodTimingInputError(f"source_periods[{index}] requires start before end_exclusive")
        expected_active = start <= current < end
        if raw["active"] is not expected_active:
            raise PeriodTimingInputError(
                f"source_periods[{index}].active contradicts its half-open interval at timing.as_of"
            )
        if declared_system is None:
            declared_system = system
        elif system != declared_system:
            raise PeriodTimingInputError("nested source periods must declare the same period system")
        if periods and (start < periods[-1].start or end > periods[-1].end_exclusive):
            raise PeriodTimingInputError(
                f"source_periods[{index}] must be contained within its parent interval"
            )
        periods.append(SourcePeriod(index, system, level, name, lord, start, end, raw["active"]))
    return tuple(periods)


def named_period_expression(
    *, slot: int, system: str, level: str, name: str, lord: str,
) -> dict[str, Any]:
    """Require one explicitly identified active period and its boundaries."""
    if type(slot) is not int or not 1 <= slot <= MAX_PERIOD_LEVELS:
        raise PeriodTimingInputError(f"slot must be between 1 and {MAX_PERIOD_LEVELS}")
    values = {"system": system, "level": level, "name": name, "lord": lord}
    for field, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise PeriodTimingInputError(f"{field} is required")
    if lord not in PLANETS:
        raise PeriodTimingInputError("lord must be a canonical planet")
    prefix = f"deva_keralam.timing.period.{slot}"
    return {
        "op": "all",
        "children": [
            *(
                {"op": "fact", "key": f"{prefix}.{field}", "comparator": "equals", "value": value.strip()}
                for field, value in values.items()
            ),
            {"op": "fact", "key": f"{prefix}.start", "comparator": "exists", "value": True},
            {"op": "fact", "key": f"{prefix}.end_exclusive", "comparator": "exists", "value": True},
            {"op": "fact", "key": f"{prefix}.active", "comparator": "equals", "value": True},
        ],
    }


def named_period_chain_expression(*periods: Mapping[str, Any]) -> dict[str, Any]:
    if not periods:
        raise PeriodTimingInputError("at least one named period is required")
    return {
        "op": "all",
        "children": [named_period_expression(**dict(period)) for period in periods],
    }
