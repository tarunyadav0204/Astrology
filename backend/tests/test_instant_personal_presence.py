from chat.instant_chat_pipeline import (
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _build_personal_presence_contract,
    _fit_composer_brief,
    _instant_personal_presence_rewrite_rule,
    _instant_relational_voice_contract,
)


def test_personal_presence_uses_only_first_name_and_keeps_it_optional() -> None:
    contract = _build_personal_presence_contract(
        birth={
            "name": "Tarun Yadav",
            "date": "1980-04-02",
            "latitude": 29.15,
            "longitude": 75.72,
        },
        intent={"category": "property", "answer_mode": "timing_window"},
        query_plan={"user_goal": "decide whether to buy now"},
    )

    assert contract["first_name"] == "Tarun"
    assert contract["name_use"] == "optional_once"
    serialized = repr(contract)
    assert "Yadav" not in serialized
    assert "1980-04-02" not in serialized
    assert "29.15" not in serialized
    assert "75.72" not in serialized


def test_personal_presence_avoids_name_for_factual_lookup() -> None:
    contract = _build_personal_presence_contract(
        birth={"name": "Deepika New"},
        intent={"category": "general", "answer_mode": "factual_chart_lookup"},
        query_plan={},
    )

    assert contract["name_use"] == "avoid"
    assert "first_name" not in contract


def test_personal_presence_cannot_change_astrology_or_manipulate_engagement() -> None:
    contract = _build_personal_presence_contract(
        birth={"name": "Tarun"},
        intent={"category": "property", "answer_mode": "topic_reading"},
        query_plan={},
    )
    forbidden = " ".join(contract["forbidden"])

    assert "never change the verdict" in contract["verdict_fidelity"]
    assert "withholding or weakening the answer" in forbidden
    assert "encouraging emotional dependency" in forbidden
    assert "generic psychology presented as if it were calculated astrology" in forbidden


def test_shared_voice_requires_ethical_personal_presence() -> None:
    voice = _instant_relational_voice_contract()

    assert "answer_contract.personal_presence" in voice
    assert "chart-specific human sentence" in voice
    assert "Give the complete useful answer before the closing question" in voice
    assert "manufacture urgency or fear" in voice
    assert "generic psychology" in voice


def test_composer_context_carries_personal_presence_without_changing_verdict() -> None:
    verdict = {"direction": "wait_for_stronger_window", "confidence": "high"}
    brief = _build_instant_composer_context(
        {
            "birth_summary": {"name": "Tarun Yadav"},
            "intent_summary": {"category": "property", "answer_mode": "topic_reading"},
            "normalized_evidence": {"natal_promise": {"status": "supported"}},
        },
        {
            "query_plan": {
                "category": "property",
                "answer_mode": "topic_reading",
                "user_goal": "decide whether to wait",
            },
            "verdict": verdict,
            "answer_spec": {},
            "user_derivation": {},
        },
    )

    assert brief["answer_contract"]["personal_presence"]["first_name"] == "Tarun"
    assert brief["verdict"]["direction"] == verdict["direction"]
    assert brief["verdict"]["confidence"] == verdict["confidence"]


def test_prompt_fitting_restores_personal_presence_contract() -> None:
    personal = _build_personal_presence_contract(
        birth={"name": "Tarun Yadav"},
        intent={"category": "property", "answer_mode": "timing_window"},
        query_plan={},
    )
    fitted = _fit_composer_brief(
        {
            "query_plan": {"category": "property"},
            "verdict": {"direction": "supported"},
            "answer_contract": {"personal_presence": personal},
            "evidence": {"noise": ["x" * 500 for _ in range(100)]},
        },
        target_chars=500,
    )

    assert fitted["answer_contract"]["personal_presence"] == personal


def test_home_prompt_requires_human_bridge_and_rejects_generic_property_question() -> None:
    personal = _build_personal_presence_contract(
        birth={"name": "Tarun Yadav"},
        intent={"category": "home_property", "answer_mode": "event_timing"},
        query_plan={"user_goal": "decide whether to buy now"},
    )
    prompt = _build_instant_composer_prompt_v3(
        "Is this a good period to buy a house?",
        {
            "context_profile": "instant_composer_v3",
            "query_plan": {"category": "home_property", "answer_mode": "event_timing"},
            "verdict": {"direction": "wait_for_stronger_window"},
            "answer_contract": {
                "personal_presence": personal,
                "knowledge_graph_policy": {"live": True, "domain": "home_property"},
            },
            "evidence": {},
        },
        "english",
    )

    assert "PERSONAL DELIVERY IS MANDATORY" in prompt
    assert "This human bridge cannot be replaced by more chart facts" in prompt
    assert "A generic “What property type?”" in prompt


def test_fact_correction_personal_rule_preserves_emotional_delivery() -> None:
    personal = _build_personal_presence_contract(
        birth={"name": "Tarun Yadav"},
        intent={"category": "home_property", "answer_mode": "event_timing"},
        query_plan={"user_goal": "decide whether to buy now"},
    )
    rule = _instant_personal_presence_rewrite_rule(personal)

    assert '"first_name":"Tarun"' in rule
    assert "one or two natural human-bridge sentences" in rule
    assert "separate from the technical proof" in rule
    assert "generic question about property type" in rule
    assert "must never alter, omit, soften, or strengthen" in rule
