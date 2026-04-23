from marriage.marriage_analysis_execute import (
    MARRIAGE_STRUCTURED_QUESTION,
    attach_marriage_agentic_context,
)


def test_marriage_report_contract_is_world_class_not_five_questions():
    assert "Include exactly 10 questions" in MARRIAGE_STRUCTURED_QUESTION
    assert "promise, timing, manifestation, continuity" in MARRIAGE_STRUCTURED_QUESTION
    assert "marriage_evidence" in MARRIAGE_STRUCTURED_QUESTION
    assert "DK, UL, and A7" in MARRIAGE_STRUCTURED_QUESTION
    assert "marital_status" in MARRIAGE_STRUCTURED_QUESTION
    assert "never use first-marriage wording" in MARRIAGE_STRUCTURED_QUESTION
    assert "What relationship or marriage lifecycle phases are active next?" in MARRIAGE_STRUCTURED_QUESTION
    assert "What is the timeline for major relationship and marriage events?" not in MARRIAGE_STRUCTURED_QUESTION


def test_attach_marriage_agentic_context_is_resilient():
    context = {
        "d1_chart": {"planets": {}, "houses": [], "ascendant": 0},
        "divisional_charts": {},
        "current_dashas": {},
    }
    birth_data = {
        "name": "Test",
        "date": "1990-01-01",
        "time": "12:00",
        "place": "Delhi",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "UTC+5.5",
    }

    out = attach_marriage_agentic_context(context, birth_data)

    assert "marriage_evidence" in out
    assert set(out["marriage_evidence"]) == {"parashari", "jaimini", "nadi"}
