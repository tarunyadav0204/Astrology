from chat.verified_chat_pipeline import build_verified_conversation_context


def test_verified_context_carries_bounded_user_facts_separately_from_chart_evidence():
    context = build_verified_conversation_context(
        history=[],
        intent={
            "_verified_user_facts": {
                "career": ["Works in design", "Preparing for a promotion"],
                "family": ["Married in 2020"],
            }
        },
    )

    assert context["relevant_user_stated_facts"] == {
        "career": ["Works in design", "Preparing for a promotion"],
        "family": ["Married in 2020"],
    }
    assert "not astrological evidence" in context["rule"]


def test_verified_context_caps_large_fact_histories():
    context = build_verified_conversation_context(
        history=[],
        intent={"_verified_user_facts": {"career": [f"Fact {index}" for index in range(20)]}},
    )

    assert len(context["relevant_user_stated_facts"]["career"]) == 5
