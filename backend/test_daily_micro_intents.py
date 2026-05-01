from daily.daily_micro_intents import classify_daily_micro_intent


def test_classify_interview_meeting():
    result = classify_daily_micro_intent("How will my interview and client meeting go today?", category="career")
    assert result["name"] == "interview_meeting"
    assert 10 in result["houses"]
    assert "Mercury" in result["fast_planets"]


def test_classify_relationship_outreach():
    result = classify_daily_micro_intent("Should I message my partner today and try to patch up?", category="relationship")
    assert result["name"] == "relationship_outreach"
    assert 7 in result["houses"]
    assert "Venus" in result["fast_planets"]


def test_reduce_daily_context_includes_micro_intent():
    try:
        from daily.daily_context_reducer import reduce_daily_context
    except ModuleNotFoundError as exc:
        if "swisseph" in str(exc):
            return
        raise
    context = {
        "intent": {
            "mode": "PREDICT_DAILY",
            "category": "career",
            "analysis_type": "DAILY_PREDICTION",
            "extracted_context": {
                "specific_date": "2026-04-30",
            },
        },
        "birth_details": {
            "name": "Tarun",
            "date": "1990-01-01",
            "time": "12:00:00",
            "place": "Delhi",
            "timezone": "UTC+5:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
        },
        "d1_chart": {
            "ascendant_sign": "Virgo",
            "planets": {
                "Moon": {"sign_name": "Capricorn", "house": 5},
            },
        },
        "daily_prediction_spine": {
            "target_date": "2026-04-30",
        },
        "current_dashas": {},
        "current_date_info": {},
    }
    reduced = reduce_daily_context(
        context,
        user_question="Should I attend the interview today?",
        conversation_history=[],
    )
    assert reduced["daily_micro_intent"]["name"] == "interview_meeting"
    assert reduced["intent"]["daily_micro_intent"]["name"] == "interview_meeting"


if __name__ == "__main__":
    test_classify_interview_meeting()
    test_classify_relationship_outreach()
    test_reduce_daily_context_includes_micro_intent()
    print("daily micro intent tests passed")
