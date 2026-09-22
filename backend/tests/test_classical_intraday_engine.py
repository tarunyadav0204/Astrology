from types import SimpleNamespace

import pytest

from calculators.chart_calculator import ChartCalculator
from calculators.trading import ClassicalIntradayTradingEngine
from calculators.trading.market_calendar import MarketSessionCalendar


@pytest.fixture(scope="module")
def engine():
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar",
    }
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    return ClassicalIntradayTradingEngine(chart, birth)


@pytest.fixture(scope="module")
def location():
    return {"latitude": 28.4595, "longitude": 77.0266, "timezone": "Asia/Kolkata", "name": "Gurugram"}


def test_full_four_gate_packet_has_no_shortcut_layers(engine, location):
    row = engine.calculate("2026-09-22", current_location=location)
    assert row["available"] is True
    assert row["market_open"] is True
    assert row["natal_baseline"]["d2_retention_evidence"]
    assert [x["level"] for x in row["period_permission"]["active_periods"]] == ["mahadasha", "antardasha", "pratyantardasha"]
    assert row["daily_climate"]["tara_bala"]["name"]
    assert row["daily_climate"]["chandra_bala"]["house_from_natal_moon"]
    assert row["daily_climate"]["ashtakavarga"]
    assert row["windows"]
    assert "D5" in row["excluded_layers"] and "Indu Lagna" in row["excluded_layers"] and "KP" in row["excluded_layers"]
    assert "luck_score" not in row


def test_every_window_combines_all_required_muhurta_layers(engine, location):
    row = engine.calculate("2026-09-22", current_location=location)
    for window in row["windows"]:
        assert window["hora_lord"]
        assert window["choghadiya"]
        assert isinstance(window["ascendant_sign"], int)
        assert len(window["trading_house_lords"]) == 3
        assert window["panchanga"]["tithi"]["name"]
        assert window["verdict"] in {"supportive", "neutral", "avoid"}


def test_current_location_is_required_and_birthplace_is_not_silently_used(engine):
    row = engine.calculate("2026-09-22", current_location=None)
    assert row["available"] is False
    assert row["participation"] == "sit_out"
    assert "Current trading location" in row["reason"]


def test_market_calendar_covers_holiday_and_verified_sunday_session():
    calendar = MarketSessionCalendar()
    assert calendar.session("2026-10-02")["market_open"] is False
    budget = calendar.session("2026-02-01")
    assert budget["market_open"] is True
    assert (budget["open"], budget["close"]) == ("09:15", "15:30")


def test_unknown_calendar_year_fails_closed(engine, location):
    row = engine.calculate("2027-09-22", current_location=location)
    assert row["market_open"] is False
    assert row["market"]["calendar_verified"] is False


def test_natal_baseline_is_stable_but_daily_layer_changes(engine, location):
    first = engine.calculate("2026-09-22", current_location=location)
    second = engine.calculate("2026-09-23", current_location=location)
    assert first["natal_baseline"] == second["natal_baseline"]
    assert first["daily_climate"] != second["daily_climate"]


def test_no_supportive_window_can_override_sit_out(engine, location):
    row = engine.calculate("2026-09-22", current_location=location)
    if row["participation"] == "sit_out":
        assert not row["entry_windows"]
        assert all(window["usable_for_new_entry"] is False for window in row["windows"])
