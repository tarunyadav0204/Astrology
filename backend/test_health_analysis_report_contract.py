from health.health_analysis_execute import HEALTH_STRUCTURED_QUESTION, attach_health_agent_context


def test_health_report_contract_is_not_limited_to_five_questions():
    assert "Include exactly 10 questions" in HEALTH_STRUCTURED_QUESTION
    assert "health_agent" in HEALTH_STRUCTURED_QUESTION
    assert "D30/Trimsamsa" in HEALTH_STRUCTURED_QUESTION
    assert "What should I not ignore?" in HEALTH_STRUCTURED_QUESTION


def test_attach_health_agent_context_is_resilient():
    context = {
        "d1_chart": {"planets": {}, "houses": [], "ascendant": 0},
        "divisional_charts": {},
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

    out = attach_health_agent_context(context, birth_data)

    assert "health_agent" in out
    assert out["health_agent"]["a"] == "health"
