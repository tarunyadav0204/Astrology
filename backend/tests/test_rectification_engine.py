from __future__ import annotations

from datetime import date

import pytest

from rectification.contracts import CreateRectificationEventRequest
from rectification.engine import CandidateEvaluation, RectificationEngine, SparseAstrologyEvaluator
from rectification.registry import EVENT_DEFINITIONS, get_event_definition


def _events(count=4):
    rows = [
        {
            "id": 1, "event_type": "marriage", "date_start": "2005-11-18",
            "date_end": "2005-11-18", "precision": "exact_day",
            "source_reliability": "documented",
        },
        {
            "id": 2, "event_type": "career_change", "date_start": "2008-06-01",
            "date_end": "2008-06-30", "precision": "month",
            "source_reliability": "confident_memory",
        },
        {
            "id": 3, "event_type": "childbirth", "date_start": "2010-07-10",
            "date_end": "2010-07-10", "precision": "exact_day",
            "source_reliability": "documented",
        },
        {
            "id": 4, "event_type": "relocation", "date_start": "2014-01-01",
            "date_end": "2014-12-31", "precision": "year",
            "source_reliability": "approximate_memory",
        },
    ]
    return rows[:count]


class FakeEvaluator:
    def evaluate(self, *, chart_input, candidate_time, events):
        minute = int(candidate_time.split(":")[1])
        # Two contiguous evidence regions. The later one is the clear winner.
        fingerprint = "early" if minute < 2 else "late"
        score = 55.0 if fingerprint == "early" else 82.0
        details = {
            "candidate_local_time": candidate_time,
            "relative_fit": score,
            "events": [
                {
                    "event_id": event["id"],
                    "score": score - index,
                    "reliability_weight": 1.0,
                }
                for index, event in enumerate(events)
            ],
        }
        return CandidateEvaluation(
            local_time=candidate_time,
            score=score,
            weighted_score=score * len(events),
            event_weight_total=float(len(events)),
            fingerprint=fingerprint,
            details=details,
        )


def test_registry_has_only_complete_phase_one_definitions():
    assert {
        "marriage", "childbirth", "career_change", "promotion",
        "education", "relocation", "property_purchase",
    } == set(EVENT_DEFINITIONS)
    for definition in EVENT_DEFINITIONS.values():
        assert definition.anchor_houses
        assert definition.varga in {4, 7, 9, 10, 24}
        assert definition.varga_houses
        assert definition.karakas


def test_candidate_generation_includes_non_aligned_end_without_crossing_day():
    assert RectificationEngine.candidate_times(3600, 3725, minute_step=1) == (
        "01:00:00", "01:01:00", "01:02:00", "01:02:05",
    )
    with pytest.raises(ValueError, match="one local civil day"):
        RectificationEngine.candidate_times(86300, 86400)


def test_engine_clusters_adjacent_candidates_and_ranks_supported_window():
    result = RectificationEngine(evaluator=FakeEvaluator()).run(
        chart_input={"date": "1980-04-02"},
        events=_events(),
        window_start_seconds=12 * 3600,
        window_end_seconds=12 * 3600 + 3 * 60,
    )
    assert result["result_kind"] == "relative_fit_not_probability"
    assert result["candidate_count"] == 4
    assert result["best_window"] == {
        "start_local_time": "12:02:00",
        "end_local_time": "12:03:00",
        "best_local_time": "12:02:00",
        "relative_fit": 82.0,
    }
    assert result["confidence_label"] == "clear_relative_leader"
    assert result["clusters"][0]["candidate_count"] == 2


def test_engine_refuses_single_event_and_unknown_event_types():
    engine = RectificationEngine(evaluator=FakeEvaluator())
    with pytest.raises(ValueError, match="At least two"):
        engine.run(
            chart_input={}, events=_events(1),
            window_start_seconds=0, window_end_seconds=60,
        )
    bad = _events(2)
    bad[1] = {**bad[1], "event_type": "personality_guess"}
    with pytest.raises(ValueError, match="Unsupported"):
        engine.run(
            chart_input={}, events=bad,
            window_start_seconds=0, window_end_seconds=60,
        )


def test_sparse_real_calculator_emits_traceable_bounded_score():
    evaluator = SparseAstrologyEvaluator()
    candidate = evaluator.evaluate(
        chart_input={
            "name": "Reference",
            "date": "1980-04-02",
            "time": "14:55:00",
            "latitude": 29.1492,
            "longitude": 75.7217,
            "timezone": "Asia/Kolkata",
            "place": "Hisar",
            "gender": "",
        },
        candidate_time="14:55:00",
        events=_events(2),
    )
    assert 0 <= candidate.score <= 100
    assert len(candidate.details["events"]) == 2
    marriage = candidate.details["events"][0]
    assert marriage["varga_confirmation"]["chart"] == "D9"
    assert "cusp_promise" in marriage["kp_confirmation"]
    assert marriage["dasha_delivery"]["active_lords"].keys() == {
        "mahadasha", "antardasha", "pratyantardasha"
    }
    career = candidate.details["events"][1]
    assert career["inspection_aggregation"] == "mean_across_uncertainty_range"
    assert len(career["inspection_samples"]) == 3


def test_repeated_event_type_normalizes_static_promise_layers():
    evaluator = SparseAstrologyEvaluator()
    chart = {
        "name": "Reference",
        "date": "1980-04-02",
        "latitude": 29.1492,
        "longitude": 75.7217,
        "timezone": "Asia/Kolkata",
        "place": "Hisar",
    }
    repeated = [_events(1)[0], {**_events(1)[0], "id": 9, "date_start": "2008-01-12", "date_end": "2008-01-12"}]
    candidate = evaluator.evaluate(chart_input=chart, candidate_time="14:55:00", events=repeated)
    first, second = candidate.details["events"]
    assert first["structural_promise"]["occurrence_count"] == 2
    assert second["structural_promise"]["occurrence_count"] == 2
    assert first["structural_promise"]["score"] * 2 == pytest.approx(
        first["structural_promise"]["raw_score_before_occurrence_normalization"]
    )
    assert first["kp_confirmation"]["cusp_promise_score"] * 2 == pytest.approx(
        first["kp_confirmation"]["raw_cusp_promise_score"]
    )


def test_unknown_registry_key_fails_closed():
    with pytest.raises(ValueError, match="Unsupported"):
        get_event_definition("appearance")


def test_approximate_event_precision_expands_to_the_actual_calendar_window():
    month = CreateRectificationEventRequest(
        event_type="promotion", date_start=date(2024, 2, 18), precision="month"
    )
    assert month.date_start == date(2024, 2, 1)
    assert month.date_end == date(2024, 2, 29)

    year = CreateRectificationEventRequest(
        event_type="education", date_start=date(2012, 8, 1), precision="year"
    )
    assert year.date_start == date(2012, 1, 1)
    assert year.date_end == date(2012, 12, 31)


def test_phase_one_rejects_unimplemented_subjects_and_open_ranges():
    with pytest.raises(ValueError, match="native only"):
        CreateRectificationEventRequest(
            event_type="childbirth", date_start=date(2010, 1, 1), subject="child"
        )
    with pytest.raises(ValueError, match="date_end is required"):
        CreateRectificationEventRequest(
            event_type="relocation", date_start=date(2014, 1, 1), precision="range"
        )
