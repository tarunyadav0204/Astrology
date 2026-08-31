from datetime import datetime, timedelta

import pytest

from longevity.calculator import LongevityCalculator
from reports.context.base_context_builder import calculate_chart_for_birth


# Astro-Databank AA birth record: Elvis Presley, 8 Jan 1935, 04:35 CST, Tupelo.
ELVIS = {
    "name": "Elvis Presley",
    "date": "1935-01-08",
    "time": "04:35",
    "place": "Tupelo, Mississippi, USA",
    "latitude": 34.2576,
    "longitude": -88.7034,
    "timezone": "America/Chicago",
    "gender": "Male",
}
EVENT = datetime(1977, 8, 16)


def _at(windows, when):
    stamp = when.strftime("%Y-%m-%d")
    return next(window for window in windows if window["start_date"] <= stamp <= window["end_date"])


@pytest.fixture(scope="module")
def calculator():
    return LongevityCalculator(ELVIS, calculate_chart_for_birth(ELVIS))


def test_same_date_activation_is_independent_of_forecast_start(calculator):
    nearer = calculator.calculate(as_of=EVENT - timedelta(days=180), horizon_years=1)
    earlier = calculator.calculate(as_of=EVENT - timedelta(days=365), horizon_years=2)
    nearer_event = _at(nearer["activation_windows"], EVENT)
    earlier_event = _at(earlier["activation_windows"], EVENT)

    assert nearer_event["components"] == earlier_event["components"]
    assert nearer_event["convergence"]["confirmed_systems"] == earlier_event["convergence"]["confirmed_systems"]
    assert nearer_event["reasons"] == earlier_event["reasons"]
    assert nearer_event["dasha_period"] == earlier_event["dasha_period"]


def test_partial_transit_observations_are_not_counted_as_evidence(calculator):
    result = calculator.calculate(as_of=datetime(1977, 1, 1), horizon_years=1)
    for window in result["activation_windows"]:
        micro = window["convergence"]["micro"]
        if not micro["hit"]:
            assert micro["evidence"] == []
            assert not any(reason in window["reasons"] for reason in micro["non_qualifying_observations"])


def test_contract_contains_counts_not_invented_percentages(calculator):
    result = calculator.calculate(as_of=datetime(1977, 1, 1), horizon_years=1)
    assert result["schema_version"] == "longevity.v2"
    assert "score" not in result["verdict"]["current_activation"]
    assert "score" not in result["verdict"]["primary_threat"]
    assert all("score" not in window for window in result["activation_windows"])
    assert all(0 <= window["convergence"]["confirmed_systems"] <= 3 for window in result["activation_windows"])
