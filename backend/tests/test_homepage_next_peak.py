from datetime import date

from prediction_engine.homepage_next_peak import (
    _house_scores_from_period,
    _pd_handoff_payload,
    _period_peak_band,
    _select_period,
)


def test_house_scores_from_period_uses_peak_deliveries():
    period = {
        "peak_activation_windows": [
            {
                "strength": "high",
                "trigger_score": 8,
                "delivered_event_houses": [{"native_house": 10}, {"native_house": 7}],
                "activated_focus_houses": [10, 7],
            }
        ],
        "activated_focus_houses": [10],
    }
    scores = _house_scores_from_period(period)
    assert scores[10] > scores[7]
    assert scores[10] >= 100


def test_select_period_skips_current_when_pd_handoff_soon():
    periods = [
        {
            "time_status": "current",
            "activation_strength": "highly_active",
            "start": "2026-01-01",
            "end": "2026-02-01",
            "peak_activation_windows": [{"start": "2026-01-10", "end": "2026-01-20", "strength": "high", "trigger_score": 5}],
            "relevance_score": 20,
        },
        {
            "time_status": "future",
            "activation_strength": "active",
            "start": "2026-02-01",
            "end": "2026-03-01",
            "peak_activation_windows": [{"start": "2026-02-05", "end": "2026-02-15", "strength": "high", "trigger_score": 4}],
            "relevance_score": 10,
        },
    ]
    selected = _select_period(periods, as_of=date(2026, 1, 1), pd_handoff_soon=True)
    assert selected is not None
    assert selected["time_status"] == "future"


def test_pd_handoff_payload_within_window():
    payload = _pd_handoff_payload(
        {"pratyantardasha": {"planet": "Saturn", "end": "2026-01-15"}},
        as_of=date(2026, 1, 1),
    )
    assert payload["show"] is True
    assert payload["days_until_pd_change"] == 14


def test_period_peak_band_from_peaks():
    band = _period_peak_band(
        {
            "peak_activation_windows": [
                {"start": "2026-03-08", "end": "2026-03-20"},
                {"start": "2026-03-10", "end": "2026-04-02"},
            ]
        }
    )
    assert band == ("2026-03-08", "2026-04-02")
