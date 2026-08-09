from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from prediction_engine.contracts import PredictionWindow
from prediction_engine.transit_returns import (
    EXACT_NATAL_RETURN_ORB_DEGREES,
    build_exact_natal_return_passes,
)


def _synthetic_state(knots):
    ordered = sorted(knots)

    def state_at(at, _planet):
        at = at.astimezone(timezone.utc)
        if at <= ordered[0][0]:
            left, right = ordered[0], ordered[1]
        elif at >= ordered[-1][0]:
            left, right = ordered[-2], ordered[-1]
        else:
            left, right = next(
                (ordered[index], ordered[index + 1])
                for index in range(len(ordered) - 1)
                if ordered[index][0] <= at <= ordered[index + 1][0]
            )
        fraction = (at - left[0]).total_seconds() / (
            right[0] - left[0]
        ).total_seconds()
        longitude = left[1] + ((right[1] - left[1]) * fraction)
        speed = (right[1] - left[1]) / (
            (right[0] - left[0]).total_seconds() / 86400.0
        )
        return longitude % 360.0, speed

    return state_at


def test_exact_return_reports_direct_retrograde_direct_passes_and_defined_orb():
    start = date(2026, 1, 1)
    end = date(2026, 1, 7)
    noon = lambda day: datetime(2026, 1, day, 12, tzinfo=timezone.utc)
    knots = [
        (datetime(2026, 1, 1, tzinfo=timezone.utc), 98.5),
        (noon(1), 99.0),
        (noon(2), 100.5),
        (noon(3), 101.4),
        (noon(4), 99.4),
        (noon(5), 98.8),
        (noon(6), 100.6),
        (noon(7), 102.0),
        (datetime(2026, 1, 8, tzinfo=timezone.utc), 102.5),
    ]
    daily = {
        date(2026, 1, day).isoformat(): {
            "Jupiter": {"longitude": dict(knots)[noon(day)]}
        }
        for day in range(1, 8)
    }
    window = PredictionWindow(
        start.isoformat(), end.isoformat(), "Jupiter", "Jupiter", "Jupiter", "sig"
    )

    result = build_exact_natal_return_passes(
        {"planets": {"Jupiter": {"longitude": 100.0}}},
        (window,), daily, start, end, state_at=_synthetic_state(knots),
    )

    passes = result["Jupiter"]
    assert [row["motion"] for row in passes] == ["direct", "retrograde", "direct"]
    assert [row["pass_number"] for row in passes] == [1, 2, 3]
    assert all(row["orb_degrees"] == EXACT_NATAL_RETURN_ORB_DEGREES for row in passes)
    assert all(row["exact_distance_degrees"] < 0.0001 for row in passes)
    assert all(row["start_at"] < row["exact_at"] < row["end_at"] for row in passes)
    assert passes[0]["pass_sequence"] == "Direct → Retrograde → Direct"


def test_station_split_finds_two_passes_hidden_between_same_side_daily_samples():
    start = date(2026, 1, 1)
    end = date(2026, 1, 2)
    knots = [
        (datetime(2026, 1, 1, tzinfo=timezone.utc), 98.0),
        (datetime(2026, 1, 1, 12, tzinfo=timezone.utc), 99.0),
        (datetime(2026, 1, 2, tzinfo=timezone.utc), 101.0),
        (datetime(2026, 1, 2, 12, tzinfo=timezone.utc), 99.0),
        (datetime(2026, 1, 3, tzinfo=timezone.utc), 98.0),
    ]
    daily = {
        "2026-01-01": {"Jupiter": {"longitude": 99.0, "speed": 1.0}},
        "2026-01-02": {"Jupiter": {"longitude": 99.0, "speed": -1.0}},
    }
    window = PredictionWindow(
        start.isoformat(), end.isoformat(), "Jupiter", "Jupiter", "Jupiter", "sig"
    )

    passes = build_exact_natal_return_passes(
        {"planets": {"Jupiter": {"longitude": 100.0}}},
        (window,), daily, start, end, state_at=_synthetic_state(knots),
    )["Jupiter"]

    assert [row["motion"] for row in passes] == ["direct", "retrograde"]
    assert passes[0]["pass_sequence"] == "Direct → Retrograde"
