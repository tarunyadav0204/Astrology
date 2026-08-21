from datetime import date

from prediction_engine.homepage_next_peak import (
    _background_house_scores,
    _display_house_reasons,
    _house_scores_from_period,
    _pd_handoff_payload,
    _period_peak_band,
    _rank_display_houses,
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
    assert scores[10] == scores[7]
    assert scores[10] >= 100


def test_house_scores_ignore_broad_activated_focus_fallback():
    scores = _house_scores_from_period({
        "peak_activation_windows": [{
            "strength": "high",
            "trigger_score": 6,
            "delivered_event_houses": [{"native_house": 10}],
            "activated_focus_houses": [2, 6, 7, 10, 11],
        }],
        "activated_focus_houses": [2, 6, 7, 10, 11],
    })
    assert scores == {10: 106}


def test_display_houses_are_capped_at_three_and_drop_weak_tail():
    rows = _rank_display_houses(
        {10: 220, 11: 180, 2: 140, 6: 80, 7: 20},
        state="fully_reinforced",
        direct=True,
    )
    assert [row["house"] for row in rows] == [10, 11, 2]


def test_background_scores_use_pd_carrier_only():
    scores = _background_house_scores({
        "pratyantardasha": "Mercury",
        "carrier_planets": [
            {"planet": "Saturn", "dasha_levels": ["md"], "natal_event_houses": [2, 11]},
            {"planet": "Mercury", "dasha_levels": ["pd"], "natal_event_houses": [2, 8, 10, 11]},
        ],
    })
    assert scores == {2: 30, 8: 30, 10: 30, 11: 30}
    rows = _rank_display_houses(scores, state="pd_background", direct=False)
    assert len(rows) == 3


def test_background_scores_rank_pd_occupation_before_lordship_and_aspect():
    scores = _background_house_scores({
        "pratyantardasha": "Mercury",
        "carrier_planets": [{
            "planet": "Mercury",
            "dasha_levels": ["PD"],
            "event_links": [
                {"house": 10, "mechanisms": ["natal_aspect"]},
                {"house": 2, "mechanisms": ["lordship"]},
                {"house": 8, "mechanisms": ["natal_occupation"]},
                {"house": 11, "mechanisms": ["lordship", "natal_aspect"]},
            ],
        }],
    })
    rows = _rank_display_houses(scores, state="pd_background", direct=False)
    assert [row["house"] for row in rows] == [11, 8, 2]


def test_display_reasons_are_structured_for_translation():
    rows = _display_house_reasons(
        {
            "pratyantardasha": "Mercury",
            "carrier_planets": [{
                "planet": "Saturn",
                "dasha_levels": ["MD", "PD"],
                "natal_placement_house": 2,
                "event_links": [{
                    "native_house": 10,
                    "mechanisms": ["natal_aspect"],
                }],
            }],
            "peak_activation_windows": [{
                "strength": "high",
                "planet": "Mercury",
                "dasha_levels": ["PD"],
                "transit_native_house": 4,
                "delivered_event_houses": [{
                    "native_house": 10,
                    "mechanism": "transit_aspect",
                }],
            }],
        },
        [{"house": 10, "score": 105, "state": "fully_reinforced"}],
        display_mode="highly_active",
    )
    assert rows[0]["reason"] == {
        "kind": "direct_transit",
        "transit": {
            "planet": "Mercury",
            "house": 4,
            "mechanism": "transit_aspect",
            "dasha_levels": ["PD"],
        },
        "natal_support": [{
            "planet": "Saturn",
            "dasha_levels": ["MD", "PD"],
            "natal_house": 2,
            "mechanisms": ["natal_aspect"],
        }],
    }


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
            "activation_strength": "highly_active",
            "start": "2026-02-01",
            "end": "2026-03-01",
            "peak_activation_windows": [{"start": "2026-02-05", "end": "2026-02-15", "strength": "high", "trigger_score": 4}],
            "relevance_score": 10,
        },
    ]
    selected = _select_period(periods, as_of=date(2026, 1, 1), pd_handoff_soon=True)
    assert selected is not None
    assert selected["time_status"] == "future"


def test_select_period_uses_current_pd_as_background_when_no_high_peak():
    periods = [
        {
            "time_status": "current",
            "activation_strength": "active",
            "start": "2026-01-01",
            "end": "2026-02-01",
            "relevance_score": 8,
        },
        {
            "time_status": "future",
            "activation_strength": "active",
            "start": "2026-02-01",
            "end": "2026-03-01",
            "relevance_score": 20,
        },
    ]
    selected = _select_period(periods, as_of=date(2026, 1, 10), pd_handoff_soon=False)
    assert selected is periods[0]


def test_select_period_accepts_high_peak_already_underway():
    period = {
        "time_status": "current",
        "activation_strength": "highly_active",
        "start": "2026-01-01",
        "end": "2026-02-01",
        "peak_activation_windows": [{
            "start": "2026-01-05",
            "end": "2026-01-20",
            "strength": "high",
            "trigger_score": 5,
            "delivered_event_houses": [{"native_house": 10}],
        }],
    }
    selected = _select_period([period], as_of=date(2026, 1, 10), pd_handoff_soon=False)
    assert selected is period


def test_select_period_rejects_high_label_without_direct_house_delivery():
    high_without_delivery = {
        "time_status": "current",
        "activation_strength": "highly_active",
        "start": "2026-01-01",
        "end": "2026-02-01",
        "peak_activation_windows": [{
            "start": "2026-01-10",
            "end": "2026-01-20",
            "strength": "high",
            "trigger_score": 8,
            "activated_focus_houses": [2, 6, 10, 11],
        }],
        "carrier_planets": [{
            "planet": "Mercury",
            "dasha_levels": ["pd"],
            "natal_event_houses": [2, 10],
        }],
        "pratyantardasha": "Mercury",
    }
    selected = _select_period(
        [high_without_delivery],
        as_of=date(2026, 1, 10),
        pd_handoff_soon=False,
    )
    assert selected is high_without_delivery


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
