from types import SimpleNamespace

import calculators.chart_calculator as chart_module
from calculators.chart_calculator import ChartCalculator
from utils.timezone_service import parse_timezone_offset


def test_iana_offset_uses_historical_birth_date_not_current_season():
    assert parse_timezone_offset("America/Chicago", for_date="1935-01-08") == -6.0
    assert parse_timezone_offset("America/Los_Angeles", for_date="1955-02-24") == -8.0
    assert parse_timezone_offset("Europe/London", for_date="1961-07-01") == 1.0


def test_chart_calculator_passes_birth_date_to_timezone_service(monkeypatch):
    observed = {}

    def capture_timezone(value, latitude, longitude, for_date=None):
        observed.update({"value": value, "latitude": latitude, "longitude": longitude, "for_date": for_date})
        return 5.5

    monkeypatch.setattr(chart_module, "parse_timezone_offset", capture_timezone)
    birth = SimpleNamespace(
        name="Timezone fixture",
        date="1980-04-02",
        time="14:55:00",
        place="Hisar",
        latitude=29.1492,
        longitude=75.7217,
        timezone="Asia/Kolkata",
    )
    ChartCalculator({}).calculate_chart(birth)
    assert observed["for_date"] == "1980-04-02"
