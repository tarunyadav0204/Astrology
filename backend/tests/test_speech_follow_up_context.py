from utils.query_context import normalize_query_context


def test_speech_follow_up_offer_is_preserved_and_bounded():
    normalized = normalize_query_context({
        "timezone_name": "Asia/Kolkata",
        "speech_follow_up_offer": "  What will happen in my career this year?  ",
    })

    assert normalized["speech_follow_up_offer"] == "What will happen in my career this year?"
    assert normalized["timezone_name"] == "Asia/Kolkata"

    oversized = normalize_query_context({"speech_follow_up_offer": "x" * 900})
    assert len(oversized["speech_follow_up_offer"]) == 600
