from datetime import datetime

from chat.instant_chat_pipeline import _window_dasha_segments_for_period


class _FakeTransitCalculator:
    def __init__(self, positions):
        self.positions = positions

    def get_planet_position(self, at: datetime, planet: str):
        return self.positions.get((planet, at.strftime("%Y-%m-%d")), 121.0)

    @staticmethod
    def calculate_house_from_longitude(longitude: float, ascendant_longitude: float) -> int:
        return ((int(longitude / 30.0) - int(ascendant_longitude / 30.0)) % 12) + 1


def _chart():
    return {
        "planets": {
            "Saturn": {"house": 1, "sign": 0, "degree": 1.0, "longitude": 1.0},
            "Rahu": {"house": 4, "sign": 3, "degree": 5.0, "longitude": 95.0},
            "Jupiter": {"house": 4, "sign": 3, "degree": 5.0, "longitude": 95.0},
        }
    }


def _periods():
    return [{
        "start_date": "2026-08-01",
        "end_date": "2026-08-20",
        "mahadasha": "Saturn",
        "antardasha": "Rahu",
        "pratyantardasha": "Jupiter",
    }]


def test_window_scan_finds_dated_return_that_is_not_at_segment_midpoint():
    result = _window_dasha_segments_for_period(
        birth_data={},
        chart_data=_chart(),
        house_lordships={"Saturn": [10], "Rahu": [2], "Jupiter": [9]},
        period_window={"start": "2026-08-01", "end": "2026-08-20"},
        focus_houses=[10],
        transit_calc=_FakeTransitCalculator({("Saturn", "2026-08-08"): 1.0}),
        ascendant_longitude=0.0,
        category="career",
        raw_periods=_periods(),
    )

    segment = result["segments"][0]
    assert segment["natal_promise_status"] == "supported_by_active_dasha_carriers"
    assert segment["activation_strength"] == "highly_active"
    assert any(
        peak["start"] == "2026-08-08"
        and "exact_degree_return" in peak["trigger_kinds"]
        and "exact_natal_nakshatra_return" in peak["trigger_kinds"]
        for peak in segment["peak_activation_windows"]
    )
    assert result["activation_timeline"]["peak_windows"]


def test_same_nakshatra_lord_alone_is_secondary_not_a_high_activity_peak():
    result = _window_dasha_segments_for_period(
        birth_data={},
        chart_data=_chart(),
        house_lordships={"Saturn": [10], "Rahu": [2], "Jupiter": [9]},
        period_window={"start": "2026-08-01", "end": "2026-08-07"},
        focus_houses=[10],
        transit_calc=_FakeTransitCalculator({}),
        ascendant_longitude=0.0,
        category="career",
        raw_periods=_periods(),
    )

    segment = result["segments"][0]
    assert segment["activation_strength"] == "background"
    assert not segment["peak_activation_windows"]
    assert any(
        "same_nakshatra_lord" in row["trigger_kinds"]
        for row in segment["transit_trigger_windows"]
    )


def test_transit_cannot_create_event_when_dasha_carriers_lack_natal_permission():
    result = _window_dasha_segments_for_period(
        birth_data={},
        chart_data=_chart(),
        house_lordships={"Saturn": [4], "Rahu": [2], "Jupiter": [9]},
        period_window={"start": "2026-08-01", "end": "2026-08-20"},
        focus_houses=[6],
        transit_calc=_FakeTransitCalculator({("Saturn", "2026-08-08"): 1.0}),
        ascendant_longitude=0.0,
        category="career",
        raw_periods=_periods(),
    )

    segment = result["segments"][0]
    assert segment["natal_promise_status"] == "not_established_for_this_dasha_chain"
    assert segment["activation_strength"] == "not_established"
    assert not segment["peak_activation_windows"]
