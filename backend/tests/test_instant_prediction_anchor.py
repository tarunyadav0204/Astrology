from chat.instant_prediction_anchor import (
    build_prediction_anchor_from_packet,
    is_prediction_anchor_eligible,
    prediction_anchor_answer_mode,
)


def test_anchor_is_limited_to_prediction_and_timing_routes():
    assert is_prediction_anchor_eligible({"answer_mode": "event_prediction"})
    assert is_prediction_anchor_eligible({"answer_mode": "comparison_choice"})
    assert not is_prediction_anchor_eligible({"answer_mode": "potential_capacity"})
    assert not is_prediction_anchor_eligible({"answer_mode": "topic_reading"})
    assert not is_prediction_anchor_eligible({"answer_mode": "remedy_action"})


def test_anchor_honors_router_prediction_mode_when_legacy_answer_mode_is_broad():
    intent = {
        "category": "education",
        "answer_mode": "ANALYZE_TOPIC_POTENTIAL",
        "mode": "LIFESPAN_EVENT_TIMING",
        "non_daily_mode": "PREDICT_EVENT_TIMING",
    }
    assert is_prediction_anchor_eligible(intent)
    assert prediction_anchor_answer_mode(intent) == "event_prediction"


def test_anchor_keeps_only_compact_prediction_evidence():
    packet = {
        "query_plan": {
            "category": "children",
            "answer_mode": "event_prediction",
            "user_goal": "timing",
            "time_scope": {"as_of": "2026-10-29", "horizon_end": "2028-12-31"},
        },
        "verdict": {
            "direction": "supported_with_conditions",
            "confidence": 0.82,
            "ranked_windows": [{
                "start": "2027-10-17",
                "end": "2027-12-03",
                "chain": "Jupiter-Mercury-Mars",
                "why": ["Calculated fifth-house activation"],
                "raw_calculator_dump": "must not be passed",
            }],
        },
        "answer_spec": {
            "event_rules": {
                "required_material_windows": ["2027-10-17 to 2027-12-03"],
                "dasha_level_terms": {"MD": "major period"},
                "claim_contract": {"allowed": True},
                "internal_only": "must not be passed",
            },
        },
        "evidence_ledger": {
            "records": [
                {
                    "kind": "natal_promise",
                    "strength": "primary",
                    "value": {"summary": "Natal support", "full_chart": {"Sun": "large raw payload"}},
                },
                {
                    "kind": "primary_drivers",
                    "strength": "primary",
                    "value": ["Event timing verdict: future_window_available_current_not_prominent"],
                },
                {
                    "kind": "current_transits",
                    "strength": "supporting",
                    "value": {"planets": "not an approved reason row"},
                },
            ],
        },
    }

    anchor = build_prediction_anchor_from_packet(packet)

    assert anchor["verdict"]["direction"] == "supported_with_conditions"
    assert anchor["ranked_windows"][0]["chain"] == "Jupiter-Mercury-Mars"
    assert "raw_calculator_dump" not in anchor["ranked_windows"][0]
    assert anchor["calculated_reasons"][0]["kind"] == "natal_promise"
    assert "full_chart" not in anchor["calculated_reasons"][0]["finding"]
    assert "internal_only" not in anchor["prediction_rules"]
    assert anchor["immediate_outcome_rule"]["posture"] == "no_positive_immediate_prediction"
