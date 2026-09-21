import os
import sys

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat_history.clarification_cards import (
    build_clarification_next_action,
    is_compound_choice_followup,
)


def test_compound_clarification_builds_theme_cards():
    action = build_clarification_next_action(
        {
            "status": "CLARIFY",
            "answer_mode": "compound_plan",
            "clarification_question": "Which one first?",
            "clarification_choices": [
                {"id": "q1", "label": "Marriage", "submit_text": "When will I get married?"},
                {"id": "q2", "label": "Career", "submit_text": "How is my career looking?"},
            ],
        },
        original_question="When will I get married? Also how is my career?",
    )
    assert action["type"] == "clarification_choice"
    assert "title" not in action
    assert len(action["options"]) == 2
    assert action["original_question"].startswith("When will I get married?")
    assert action["options"][0]["submit_text"] == "When will I get married?"


def test_compound_clarification_falls_back_to_question_parts():
    action = build_clarification_next_action({
        "status": "CLARIFY",
        "answer_mode": "compound_plan",
        "clarification_question": "Pick one card.",
        "evidence_plan": {
            "question_parts": [
                {"part_id": "p1", "life_domain": "marriage", "text": "Will I get married this year?"},
                {"part_id": "p2", "life_domain": "career", "text": "Should I change jobs?"},
            ]
        },
    })
    assert action is not None
    assert [option["id"] for option in action["options"]] == ["p1", "p2"]


def test_compound_clarification_requires_two_cards():
    assert build_clarification_next_action({
        "status": "CLARIFY",
        "answer_mode": "compound_plan",
        "clarification_choices": [
            {"id": "q1", "label": "Marriage", "submit_text": "When will I get married?"},
        ],
    }) is None


def test_compound_choice_followup_detects_card_tap():
    assert is_compound_choice_followup({"follow_up_type": "clarification_choice"})
    assert is_compound_choice_followup(None, {"answer_mode": "compound_plan"})
    assert is_compound_choice_followup(
        None,
        {"instant_dialogue": {"pending_choice_kind": "compound_plan"}},
    )
    assert not is_compound_choice_followup({"follow_up_type": "remedy_action"})
    assert not is_compound_choice_followup(None, {"answer_mode": "topic_reading"})


if __name__ == "__main__":
    test_compound_clarification_builds_theme_cards()
    test_compound_clarification_falls_back_to_question_parts()
    test_compound_clarification_requires_two_cards()
    test_compound_choice_followup_detects_card_tap()
    print("clarification card tests passed")
