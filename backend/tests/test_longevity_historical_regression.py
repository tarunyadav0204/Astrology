from datetime import datetime

import pytest

from longevity.calculator import LongevityCalculator
from reports.context.base_context_builder import calculate_chart_for_birth


# Public Astro-Databank records (Rodden A/AA). These fixtures guard deterministic
# date evaluation; they are not statistical proof and are not used to tune rules.
CASES = [
    ({"name": "John F. Kennedy", "date": "1917-05-29", "time": "15:00", "place": "Brookline, Massachusetts, USA", "latitude": 42.3334, "longitude": -71.1200, "timezone": "America/New_York", "gender": "Male"}, datetime(1963, 11, 22), {"vimshottari": True, "shoola": True, "transit_bav": True}),
    ({"name": "Elvis Presley", "date": "1935-01-08", "time": "04:35", "place": "Tupelo, Mississippi, USA", "latitude": 34.2576, "longitude": -88.7034, "timezone": "America/Chicago", "gender": "Male"}, datetime(1977, 8, 16), {"vimshottari": True, "shoola": False, "transit_bav": True}),
    ({"name": "Steve Jobs", "date": "1955-02-24", "time": "19:15", "place": "San Francisco, California, USA", "latitude": 37.7749, "longitude": -122.4194, "timezone": "America/Los_Angeles", "gender": "Male"}, datetime(2011, 10, 5), {"vimshottari": True, "shoola": False, "transit_bav": False}),
    ({"name": "Diana, Princess of Wales", "date": "1961-07-01", "time": "19:45", "place": "Sandringham, England", "latitude": 52.8333, "longitude": 0.5000, "timezone": "Europe/London", "gender": "Female"}, datetime(1997, 8, 31), {"vimshottari": True, "shoola": False, "transit_bav": True}),
    ({"name": "Marilyn Monroe", "date": "1926-06-01", "time": "09:30", "place": "Los Angeles, California, USA", "latitude": 34.0522, "longitude": -118.2437, "timezone": "America/Los_Angeles", "gender": "Female"}, datetime(1962, 8, 5), {"vimshottari": True, "shoola": False, "transit_bav": True}),
]


@pytest.mark.parametrize("birth,event,expected", CASES, ids=[case[0]["name"] for case in CASES])
def test_public_chart_event_date_regression_is_explicit_and_non_numeric(birth, event, expected):
    result = LongevityCalculator(birth, calculate_chart_for_birth(birth)).calculate(as_of=event, horizon_years=1)
    stamp = event.strftime("%Y-%m-%d")
    window = next(row for row in result["activation_windows"] if row["start_date"] <= stamp <= row["end_date"])

    assert window["components"] == expected
    assert window["convergence"]["confirmed_systems"] == sum(expected.values())
    assert "score" not in window
    assert window["dasha_period"]["boundary_type"] == "actual_antardasha"
