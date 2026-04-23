from career_analysis.career_analysis_execute import (
    CAREER_STRUCTURED_QUESTION,
    attach_career_agentic_context,
)


def test_career_report_contract_forces_concrete_field_and_role_guidance():
    assert "Include exactly 10 questions" in CAREER_STRUCTURED_QUESTION
    assert "career_evidence" in CAREER_STRUCTURED_QUESTION
    assert "What exactly will I do day-to-day?" in CAREER_STRUCTURED_QUESTION
    assert "Rank the top 3 fields only" in CAREER_STRUCTURED_QUESTION
    assert "do not list more than 3 top fields" in CAREER_STRUCTURED_QUESTION


def test_attach_career_agentic_context_is_resilient():
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

    out = attach_career_agentic_context(context, birth_data)

    assert "career_evidence" in out
    assert set(out["career_evidence"]) == {"parashari", "jaimini", "nadi"}
