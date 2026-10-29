from chat.instant_prediction_anchor import (
    build_prediction_anchor_from_packet,
    is_prediction_anchor_eligible,
)


def test_anchor_is_limited_to_prediction_and_timing_routes():
    assert is_prediction_anchor_eligible({"answer_mode": "event_prediction"})
    assert is_prediction_anchor_eligible({"answer_mode": "comparison_choice"})
    assert not is_prediction_anchor_eligible({"answer_mode": "potential_capacity"})
    assert not is_prediction_anchor_eligible({"answer_mode": "topic_reading"})
    assert not is_prediction_anchor_eligible({"answer_mode": "remedy_action"})


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
