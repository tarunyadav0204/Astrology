from ai.intent_router import IntentRouter
from utils.query_context import normalize_query_context


def test_speech_follow_up_offer_is_preserved_and_bounded():
    normalized = normalize_query_context({
        "timezone_name": "Asia/Kolkata",
        "speech_follow_up_offer": "  What will happen in my career this year?  ",
        "speech_follow_up_invitation": "  Would you like me to explain how your career will be this year?  ",
    })

    assert normalized["speech_follow_up_offer"] == "What will happen in my career this year?"
    assert normalized["speech_follow_up_invitation"] == "Would you like me to explain how your career will be this year?"
    assert normalized["timezone_name"] == "Asia/Kolkata"

    oversized = normalize_query_context({"speech_follow_up_offer": "x" * 900})
    assert len(oversized["speech_follow_up_offer"]) == 600

    oversized_invitation = normalize_query_context({"speech_follow_up_invitation": "x" * 900})
    assert len(oversized_invitation["speech_follow_up_invitation"]) == 600


def test_compact_router_receives_spoken_invitation_and_requires_resolved_question():
    context = (
        'PENDING SPOKEN FOLLOW-UP:\n'
        '- Exact invitation Tara spoke: "Would you like me to explain how your career will be this year?"\n'
        '- Canonical question Tara offered to answer: "How will my career be this year?"'
    )
    prompt = IntentRouter.__new__(IntentRouter)._build_compact_instant_router_prompt(
        user_question="yes",
        latest_user_reply="yes",
        history_text="User: How is my career?",
        app_language="english",
        current_date="2026-09-12",
        current_year=2026,
        current_month="September",
        clarification_limit_text="",
        force_ready_instruction="",
        force_clarify_instruction="",
        dialogue_state_text="{}",
        speech_follow_up_context_text=context,
    )

    assert "Exact invitation Tara spoke" in prompt
    assert "How will my career be this year?" in prompt
    assert "resolved_question" in prompt
    assert "Classify every remaining field from resolved_question" in prompt
