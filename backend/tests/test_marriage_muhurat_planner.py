import sys
from datetime import date, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calculators.marriage_muhurat_calculator import MarriageMuhuratCalculator
from muhurat_routes import MarriageMuhuratRequest


def test_marriage_request_accepts_an_explicit_overnight_ceremony_window():
    request = MarriageMuhuratRequest(
        start_date="2027-01-10", end_date="2027-01-12",
        venue_latitude=28.6139, venue_longitude=77.2090,
        allowed_start="20:00", allowed_end="01:00",
    )
    assert request.allowed_end == "01:00"


@pytest.mark.parametrize(
    "patch",
    [
        {"end_date": "2027-01-09"},
        {"end_date": "2027-07-10"},
        {"allowed_start": "not-a-time"},
    ],
)
def test_marriage_request_rejects_invalid_search_constraints(patch):
    base = {
        "start_date": "2027-01-10", "end_date": "2027-01-12",
        "venue_latitude": 28.6139, "venue_longitude": 77.2090,
    }
    with pytest.raises(ValueError):
        MarriageMuhuratRequest(**{**base, **patch})


def test_overnight_window_belongs_to_the_selected_ceremony_date():
    start, finish = MarriageMuhuratCalculator._time_window(
        date(2027, 1, 10), time(20, 0), time(1, 0), ZoneInfo("Asia/Kolkata"),
    )
    assert start.date().isoformat() == "2027-01-10"
    assert finish.date().isoformat() == "2027-01-11"
