from __future__ import annotations

import sys
from pathlib import Path


BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from chat_history.routes import (
    _is_chart_reading_feedback_challenge,
    _resolve_chart_reading_feedback_intent,
)


def test_chart_reading_complaint_is_not_a_compound_question():
    question = (
        "You have always lied to me, and keep repeating SAV, BAV and dasha. "
        "You have nothing good to tell me about my chart, personal life or professional life."
    )

    assert _is_chart_reading_feedback_challenge(question) is True


def test_ordinary_multi_domain_question_is_not_a_feedback_challenge():
    assert _is_chart_reading_feedback_challenge(
        "Tell me about my career, marriage and finances from my chart."
    ) is False


def test_feedback_challenge_drops_compound_clarification_cards():
    intent = _resolve_chart_reading_feedback_intent({
        "status": "CLARIFY",
        "answer_mode": "compound_plan",
        "clarification_question": "Pick a topic.",
        "clarification_choices": [{"id": "q1"}],
    })

    assert intent["status"] == "READY"
    assert intent["answer_mode"] == "topic_reading"
    assert intent["category"] == "general"
    assert intent["clarification_question"] == ""
    assert intent["clarification_choices"] == []
