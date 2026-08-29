from instant_chat_v2.translated_astrology import (
    build_translated_astrology_contract,
    translated_astrology_prompt_rule,
    validate_translated_astrology_answer,
)


def _context(*facts, answer_mode="topic_reading", claim_permission="answer"):
    return {
        "query_plan": {"answer_mode": answer_mode},
        "verdict": {"direction": "qualified_support"},
        "evidence": {
            "domain_foundation": {
                "route_synthesis": {
                    "required_visible_facts": list(facts),
                }
            }
        },
        "answer_contract": {
            "knowledge_graph_policy": {"claim_permission": claim_permission},
        },
    }


def test_contract_selects_planet_from_calculated_fact_not_generic_folklore():
    context = _context(
        {
            "planet": "Jupiter",
            "condition": "Jupiter supports the selected learning carrier in both required chart layers",
            "effect": "deep understanding is stronger than rote recall",
        },
        {
            "planet": "Saturn",
            "condition": "Saturn qualifies continuity in the selected route",
            "effect": "progress improves through structure but can pause under pressure",
        },
    )

    contract = build_translated_astrology_contract(
        context,
        question="What does my chart show about education?",
        language="english",
    )

    assert contract["required"] is True
    assert contract["allowed_planets"][:2] == ["Jupiter", "Saturn"]
    assert "deep understanding" in contract["reason_anchors"][0]["source_fact"]
    assert "ordinary life language" not in contract["reason_anchors"][0]["source_fact"]


def test_hindi_contract_uses_familiar_graha_names():
    contract = build_translated_astrology_contract(
        _context({"planet": "Jupiter", "reason": "Jupiter supports sustained understanding"}),
        question="Meri padhai kaisi rahegi?",
        language="hindi",
    )

    assert contract["reason_anchors"][0]["display_name"] == "Guru"
    assert validate_translated_astrology_answer(
        "Guru gehri samajh ko support karta hai, isliye practice se clarity badhti hai.",
        contract,
    ) == []
    assert validate_translated_astrology_answer(
        "गुरु गहरी समझ को सहारा देता है, इसलिए अभ्यास से स्पष्टता बढ़ती है।",
        contract,
    ) == []


def test_validator_rejects_generic_jargon_and_unsupported_planets():
    contract = build_translated_astrology_contract(
        _context({"planet": "Jupiter", "reason": "Jupiter supports careful judgment"}),
        question="What is my strongest wealth path?",
        language="english",
    )

    assert validate_translated_astrology_answer(
        "You can grow steadily by staying disciplined.", contract
    ) == ["missing translated planetary reason"]
    assert validate_translated_astrology_answer(
        "Mars gives drive, while Jupiter supports careful judgment.", contract
    ) == ["unsupported planet reason(s): Mars"]
    assert validate_translated_astrology_answer(
        "Jupiter in D24 and Gandanta supports careful judgment.", contract
    ) == ["technical astrology leaked into the main answer"]
    assert validate_translated_astrology_answer(
        "Jupiter supports careful judgment, so patient choices suit you better than impulsive ones.",
        contract,
    ) == []


def test_validator_limits_visible_answer_to_two_planet_reasons():
    contract = build_translated_astrology_contract(
        _context(
            {"planet": "Jupiter", "reason": "Jupiter supports understanding"},
            {"planet": "Saturn", "reason": "Saturn adds structure"},
            {"planet": "Mercury", "reason": "Mercury supports analysis"},
        ),
        question="What does my chart show?",
        language="english",
    )

    assert validate_translated_astrology_answer(
        "Jupiter supports understanding, Saturn adds structure, and Mercury supports analysis.",
        contract,
    ) == ["too many planet reasons: 3 (maximum 2)"]


def test_explicit_technical_question_allows_technical_terms():
    contract = build_translated_astrology_contract(
        _context({"planet": "Jupiter", "reason": "Jupiter is the calculated carrier"}),
        question="Show me the technical D24 and dasha logic.",
        language="english",
    )

    assert contract["technical_detail_allowed"] is True
    assert validate_translated_astrology_answer(
        "Jupiter is the carrier in D24 and the Antardasha supports it.", contract
    ) == []


def test_handoff_and_boundary_answers_do_not_require_planet_dressing():
    handoff = build_translated_astrology_contract(
        _context(
            {"planet": "Venus", "reason": "Venus is present in retained context"},
            answer_mode="dedicated_partnership_flow",
        ),
        question="Compare our two charts.",
        language="english",
    )
    boundary = build_translated_astrology_contract(
        _context(
            {"planet": "Venus", "reason": "Venus is present in retained context"},
            claim_permission="boundary_handoff",
        ),
        question="Will my child become a doctor?",
        language="english",
    )

    assert handoff["required"] is False
    assert boundary["required"] is False
    assert "Do not invent" in translated_astrology_prompt_rule(handoff)


def test_retrospective_selection_flow_may_show_period_level_terms():
    context = _context({"planet": "Venus", "reason": "Venus carries the selected marriage phase"})
    context["query_plan"]["time_scope"] = {"retrospective": True}
    contract = build_translated_astrology_contract(
        context,
        question="When did I get married?",
        language="english",
    )

    assert contract["technical_detail_allowed"] is True
    assert validate_translated_astrology_answer(
        "Venus supports commitment in this MD-AD-PD selection window.", contract
    ) == []
