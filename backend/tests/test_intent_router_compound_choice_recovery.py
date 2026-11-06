from ai.intent_router import IntentRouter


def test_resolved_compound_choice_recovery_preserves_model_topic_and_makes_ready():
    raw_model_result = {
        "status": "CLARIFY",
        "route_action": "clarify",
        "mode": "ANALYZE_TOPIC_POTENTIAL",
        "answer_mode": "compound_plan",
        "category": "career",
        "divisional_charts": ["D1", "D9", "D10"],
        "clarification_question": "Which topic would you like to explore?",
        "clarification_choices": [{"id": "q1", "label": "Growth", "submit_text": "Growth"}],
        "dialogue_state": {
            "known_facts": {"selected_topic": "Growth"},
            "unresolved_facts": ["compound_topic_choice"],
            "pending_choice_kind": "compound_plan",
            "ready_to_calculate": False,
        },
    }

    recovered = IntentRouter._recover_resolved_compound_choice(raw_model_result)

    assert recovered["status"] == "READY"
    assert recovered["route_action"] == "answer"
    assert recovered["answer_mode"] == "topic_reading"
    assert recovered["category"] == "career"
    assert recovered["divisional_charts"] == ["D1", "D9", "D10"]
    assert recovered["clarification_question"] == ""
    assert recovered["clarification_choices"] == []
    assert recovered["dialogue_state"]["unresolved_facts"] == []
    assert recovered["dialogue_state"]["ready_to_calculate"] is True
    assert "pending_choice_kind" not in recovered["dialogue_state"]
