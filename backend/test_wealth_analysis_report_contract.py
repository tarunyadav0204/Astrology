from wealth.wealth_enhanced_execute import WEALTH_STRUCTURED_QUESTION, attach_wealth_agentic_context


def test_wealth_report_contract_is_practical_and_risk_aware():
    assert "Include exactly 10 detailed_analysis sections" in WEALTH_STRUCTURED_QUESTION
    assert "wealth_evidence" in WEALTH_STRUCTURED_QUESTION
    assert "Primary Income Source" in WEALTH_STRUCTURED_QUESTION
    assert "Financial Risk and Loss Patterns" in WEALTH_STRUCTURED_QUESTION
    assert "not financial advice" in WEALTH_STRUCTURED_QUESTION


def test_attach_wealth_agentic_context_is_resilient():
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

    out = attach_wealth_agentic_context(context, birth_data)

    assert "wealth_evidence" in out
    assert set(out["wealth_evidence"]) == {"parashari", "nadi"}
