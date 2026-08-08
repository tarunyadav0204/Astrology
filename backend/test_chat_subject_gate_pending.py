"""Pending native-gate abandon + new-question escape hatch."""

from ai.chat_subject_gate import should_abandon_pending_gate_for_new_question


def test_job_question_abandons_partnership_gate():
    pending = {
        "intent_gate": "partnership_offer",
        "original_question": "When will I get married and what kind of partner will I have?",
        "user_message": (
            "To give you the most accurate insights about your marriage timing and the kind of "
            "partner you will have, I need to analyze your birth chart in conjunction with your "
            "potential partner's chart. Would you like to proceed with a Partnership Analysis?"
        ),
    }
    msg = (
        "Is there any job change chance in next 12 months? "
        "Will there be any job issues after current project ends in October 2026?"
    )
    assert should_abandon_pending_gate_for_new_question(msg, pending) is True


def test_short_yes_keeps_partnership_gate():
    pending = {"intent_gate": "partnership_offer", "original_question": "Will I marry soon?"}
    assert should_abandon_pending_gate_for_new_question("yes", pending) is False
    assert should_abandon_pending_gate_for_new_question("Continue with my chart", pending) is False


def test_relationship_followup_keeps_partnership_gate():
    pending = {
        "intent_gate": "partnership_offer",
        "original_question": "Tell me about my marriage",
    }
    assert should_abandon_pending_gate_for_new_question(
        "I want partnership analysis with my partner's chart",
        pending,
    ) is False


def test_health_question_abandons_marriage_gate():
    pending = {
        "intent_gate": "partnership_offer",
        "original_question": "When will I marry?",
    }
    assert should_abandon_pending_gate_for_new_question(
        "How will my health be over the next year?",
        pending,
    ) is True


def test_topic_mismatch_vs_original_question():
    pending = {
        "intent_gate": "create_subject_chart",
        "original_question": "Tell me about my friend's education",
    }
    assert should_abandon_pending_gate_for_new_question(
        "What about my own career promotion this year?",
        pending,
    ) is True
