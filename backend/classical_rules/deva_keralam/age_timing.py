"""Explicit calendar-age timing primitives for reviewed Deva Keralam rules.

This module does not interpret phrases from the source. A reviewer must choose
the grammar deliberately: completed age, running year, or civil calendar year.
It neither calculates nor infers any Dasha.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Literal


AGE_TIMING_VERSION = "deva-keralam-age-timing/1.0.0"
FEB_29_ANNIVERSARY_POLICY = "february_28_in_non_leap_years"

AgeTimingKind = Literal[
    "completed_age_equals",
    "completed_age_after",
    "completed_age_at_or_after",
    "completed_age_between",
    "running_year_equals",
    "calendar_year_equals",
    "calendar_year_between",
]


class AgeTimingInputError(ValueError):
    """Supplied dates or interval bounds cannot produce a safe age fact."""


def parse_civil_date(value: Any, label: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError) as exc:
        raise AgeTimingInputError(f"{label} must be an ISO civil date") from exc


def birthday_in_year(birth_date: date, year: int) -> date:
    """Return the civil birthday in ``year`` under the declared leap policy."""
    try:
        return birth_date.replace(year=year)
    except ValueError:
        if birth_date.month == 2 and birth_date.day == 29:
            return date(year, 2, 28)
        raise


def completed_age_interval(birth_date: date, completed_age: int) -> tuple[date, date]:
    """Return the half-open interval for completed age N: [birthday N, N+1)."""
    if type(completed_age) is not int or completed_age < 0:
        raise AgeTimingInputError("completed_age must be a non-negative integer")
    start = birthday_in_year(birth_date, birth_date.year + completed_age)
    end = birthday_in_year(birth_date, birth_date.year + completed_age + 1)
    return start, end


@dataclass(frozen=True)
class AgeTimingWindow:
    birth_date: date
    as_of: date
    completed_age_years: int
    running_year_number: int
    completed_age_interval_start: date
    completed_age_interval_end_exclusive: date
    calendar_year: int
    calendar_year_interval_start: date
    calendar_year_interval_end_exclusive: date

    def fact_values(self) -> dict[str, Any]:
        return {
            "birth_date": self.birth_date.isoformat(),
            "as_of": self.as_of.isoformat(),
            "completed_age_years": self.completed_age_years,
            "running_year_number": self.running_year_number,
            "completed_age_interval_start": self.completed_age_interval_start.isoformat(),
            "completed_age_interval_end_exclusive": self.completed_age_interval_end_exclusive.isoformat(),
            "calendar_year": self.calendar_year,
            "calendar_year_interval_start": self.calendar_year_interval_start.isoformat(),
            "calendar_year_interval_end_exclusive": self.calendar_year_interval_end_exclusive.isoformat(),
        }


def calculate_age_timing_window(birth_value: Any, as_of_value: Any) -> AgeTimingWindow:
    born = parse_civil_date(birth_value, "timing.birth_date")
    current = parse_civil_date(as_of_value, "timing.as_of")
    if current < born:
        raise AgeTimingInputError("timing.as_of cannot precede timing.birth_date")
    anniversary = birthday_in_year(born, current.year)
    completed = current.year - born.year - (current < anniversary)
    start, end = completed_age_interval(born, completed)
    return AgeTimingWindow(
        birth_date=born,
        as_of=current,
        completed_age_years=completed,
        running_year_number=completed + 1,
        completed_age_interval_start=start,
        completed_age_interval_end_exclusive=end,
        calendar_year=current.year,
        calendar_year_interval_start=date(current.year, 1, 1),
        calendar_year_interval_end_exclusive=date(current.year + 1, 1, 1),
    )


def age_timing_expression(kind: AgeTimingKind, start: int, end: int | None = None) -> dict[str, Any]:
    """Build a canonical expression without deciding what source prose means."""
    if type(start) is not int or start < 0:
        raise AgeTimingInputError("start must be a non-negative integer")
    if end is not None and (type(end) is not int or end < start):
        raise AgeTimingInputError("end must be an integer greater than or equal to start")
    definitions = {
        "completed_age_equals": ("completed_age_years", "equals", start),
        "completed_age_after": ("completed_age_years", "gt", start),
        "completed_age_at_or_after": ("completed_age_years", "gte", start),
        "completed_age_between": ("completed_age_years", "between", [start, end]),
        "running_year_equals": ("running_year_number", "equals", start),
        "calendar_year_equals": ("calendar_year", "equals", start),
        "calendar_year_between": ("calendar_year", "between", [start, end]),
    }
    if kind not in definitions:
        raise AgeTimingInputError(f"unknown age timing grammar: {kind!r}")
    if kind.endswith("between") and end is None:
        raise AgeTimingInputError(f"{kind} requires an end value")
    suffix, comparator, value = definitions[kind]
    return {
        "op": "fact",
        "key": f"deva_keralam.timing.native.{suffix}",
        "comparator": comparator,
        "value": value,
    }
