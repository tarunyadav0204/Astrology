from daily.daily_micro_intents import (
    build_daily_micro_intent_from_facets,
    classify_daily_micro_intent,
)


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


def test_semantic_podcast_facets_build_public_communication_event_without_text_matching():
    result = build_daily_micro_intent_from_facets(
        [
            "spoken_communication", "public_performance", "teaching_advisory",
            "media_recording", "audience_response",
        ],
        activity_label="astrology podcast",
        category="career",
    )
    assert result["name"] == "semantic_activity"
    assert result["activity_label"] == "astrology podcast"
    assert set((2, 3, 5, 9, 10, 11)).issubset(result["houses"])
    assert result["source"] == "llm_semantic_event_facets"


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
