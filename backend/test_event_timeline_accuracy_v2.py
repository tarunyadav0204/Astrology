import json
from datetime import datetime

from calculators.event_predictor_ai import EventPredictor
from calculators.event_timeline_accuracy_v2 import (
    ACCURACY_ENGINE_VERSION,
    LEGACY_ENGINE_VERSION,
    build_evidence_ledger,
    build_month_transit_facts,
    build_target_month_dasha_facts,
    build_target_year_dasha_facts,
    selected_engine_version,
    validate_v2_payload,
)


class StubDasha:
    def calculate_current_dashas(self, _birth, dt=None, strict=False):
        dt = dt or datetime.now()
        return {
            "mahadasha": {"planet": "Jupiter"},
            "antardasha": {"planet": "Saturn" if dt.month < 7 else "Mercury"},
            "pratyantardasha": {"planet": "Venus"},
            "sookshma": {"planet": "Moon"},
        }


class StubTransit:
    def _calculate_natal_positions(self, _birth):
        return {"ascendant_longitude": 0.0}

    def get_planet_state(self, dt, planet):
        base = {
            "Saturn": 330.0, "Rahu": 300.0, "Ketu": 120.0, "Jupiter": 60.0,
            "Mars": 90.0, "Sun": 0.0, "Moon": 0.0, "Mercury": 30.0, "Venus": 45.0,
        }[planet]
        # A deterministic ingress on the 16th proves daily change detection.
        lon = base + (31.0 if planet == "Jupiter" and dt.day >= 16 else 0.0)
        return {"longitude": lon % 360, "retrograde": False}

    def calculate_house_from_longitude(self, lon, asc):
        return ((int(lon / 30) - int(asc / 30)) % 12) + 1

    def get_nakshatra_from_longitude(self, lon):
        idx = int(lon / (360 / 27)) % 27
        return {"name": f"N{idx}", "index": idx, "pada": 1}

    def get_slow_planet_transits(self, _birth, **_kwargs):
        return {"Jupiter": [], "Saturn": [], "Rahu": [], "Ketu": []}


def _context():
    return {
        "d1_chart": {
            "planets": {
                "Moon": {"longitude": 10.0, "house": 1},
                "Jupiter": {"longitude": 65.0, "house": 3},
                "Saturn": {"longitude": 335.0, "house": 12},
                "Mercury": {"longitude": 35.0, "house": 2},
                "Venus": {"longitude": 45.0, "house": 2},
            }
        },
        "house_lordships": {"Jupiter": [1, 10], "Saturn": [11, 12], "Mercury": [4, 7], "Venus": [2, 9]},
        "ashtakavarga": {"d1_rashi": {"sarvashtakavarga": {"sarvashtakavarga": {str(i): 28 for i in range(12)}}}},
    }


def test_engine_version_is_reversible(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_ENGINE_VERSION", "legacy_v1")
    assert selected_engine_version() == LEGACY_ENGINE_VERSION
    monkeypatch.setenv("EVENT_TIMELINE_ENGINE_VERSION", "accuracy_v2")
    assert selected_engine_version() == ACCURACY_ENGINE_VERSION
    monkeypatch.setenv("EVENT_TIMELINE_ENGINE_VERSION", "typo")
    assert selected_engine_version() == LEGACY_ENGINE_VERSION


def test_target_year_facts_use_requested_year_and_daily_changes():
    dasha = build_target_year_dasha_facts(StubDasha(), {}, 2035)
    assert dasha["year"] == 2035
    assert dasha["samples"]["middle"]["antardasha"] == "Mercury"
    assert any(row["date"] == "2035-07-01" for row in dasha["changes"])

    transit = build_month_transit_facts(StubTransit(), {}, 2035, 1)
    assert transit["year"] == 2035
    assert "2035-01-16" in transit["planets"]["Jupiter"]["change_dates"]


def test_month_only_scan_matches_same_month_from_year_scan():
    year_dasha = build_target_year_dasha_facts(StubDasha(), {}, 2035)
    month_dasha = build_target_month_dasha_facts(StubDasha(), {}, 2035, 7)
    month_transit = build_month_transit_facts(StubTransit(), {}, 2035, 7)
    yearly = build_evidence_ledger(
        _context(), 2035, year_dasha, {"7": month_transit}, month_ids=[7]
    )
    monthly = build_evidence_ledger(
        _context(), 2035, month_dasha, {"7": month_transit}, month_ids=[7]
    )
    assert yearly["months"]["7"] == monthly["months"]["7"]
    assert list(monthly["months"]) == ["7"]


def test_integrated_ledger_retains_late_month_fast_planet_segments():
    dasha = {
        "samples": {"start": {"mahadasha": "Sun", "antardasha": "Sun", "pratyantardasha": "Sun", "sookshma": "Sun"}},
        "changes": [{
            "date": "2035-09-18",
            "to": {"mahadasha": "Sun", "antardasha": "Sun", "pratyantardasha": "Mercury", "sookshma": "Sun"},
        }],
    }
    early = [
        {"date": f"2035-09-{day:02d}", "end_date": f"2035-09-{day:02d}", "house": 1, "sign": 1, "nakshatra_index": 0}
        for day in range(1, 9)
    ]
    late = {"date": "2035-09-18", "end_date": "2035-09-30", "house": 12, "sign": 12, "nakshatra_index": 1}
    transits = {"9": {"planets": {"Mercury": {"segments": [*early, late]}}}}

    rollback = build_evidence_ledger(_context(), 2035, dasha, transits, month_ids=[9])
    integrated = build_evidence_ledger(
        _context(), 2035, dasha, transits, month_ids=[9],
        max_transit_segments_per_planet=None,
    )
    assert not rollback["months"]["9"]["evidence"]
    assert any(
        row["planet"] == "Mercury" and row["transit_house"] == 12
        for row in integrated["months"]["9"]["evidence"]
    )


def test_ledger_and_validator_fail_closed_on_uncited_events():
    dasha = build_target_year_dasha_facts(StubDasha(), {}, 2035)
    transits = {str(month): build_month_transit_facts(StubTransit(), {}, 2035, month) for month in range(1, 13)}
    ledger = build_evidence_ledger(_context(), 2035, dasha, transits)
    evidence_id = ledger["months"]["1"]["evidence"][0]["evidence_id"]
    payload = {
        "macro_trends": [],
        "monthly_predictions": [{
            "month_id": 1,
            "events": [
                {
                    "prediction": "A focused professional development may become more likely.",
                    "evidence_ids": [evidence_id],
                    "start_date": "2035-01-01",
                    "end_date": "2035-01-15",
                    "intensity": "High",
                },
                {
                    "prediction": "This guaranteed event has no evidence.",
                    "evidence_ids": ["invented"],
                    "start_date": "2035-01-01",
                    "end_date": "2035-01-02",
                    "intensity": "High",
                },
            ],
        }],
    }
    checked, warnings = validate_v2_payload(payload, ledger, year=2035, selected_month=1)
    assert len(checked["monthly_predictions"][0]["events"]) == 1
    assert checked["monthly_predictions"][0]["events"][0]["evidence_ids"] == [evidence_id]
    assert any("without valid deterministic evidence" in warning for warning in warnings)


def test_prepare_yearly_data_replaces_now_context(monkeypatch):
    from chat.chat_context_builder import ChatContextBuilder

    monkeypatch.setattr(
        ChatContextBuilder,
        "build_complete_context",
        lambda *args, **kwargs: {**_context(), "current_dashas": {"mahadasha": {"planet": "Sun"}}},
    )
    monkeypatch.setattr(ChatContextBuilder, "augment_current_dashas_with_chart_hints", lambda *args, **kwargs: None)
    predictor = EventPredictor.__new__(EventPredictor)
    predictor.engine_version = ACCURACY_ENGINE_VERSION
    predictor.dasha_calc = StubDasha()
    predictor.transit_calc = StubTransit()
    predictor._last_accuracy_ledger = {}
    raw = predictor._prepare_yearly_data(
        {"date": "1990-01-15", "time": "10:30", "latitude": 0, "longitude": 0, "timezone": 0},
        2035,
    )
    context = json.loads(raw)
    assert context["target_period_integrity"]["selected_year"] == 2035
    assert context["current_dashas"]["mahadasha"]["planet"] == "Jupiter"
    assert context["macro_transits_meta"]["start"] == "2035-01-01"
    assert context["nadi_age_activation"]["age"] == 45
