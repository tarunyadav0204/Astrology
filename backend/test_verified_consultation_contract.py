from chat.verified_consultation import (
    verified_consultation_instruction,
    verified_final_delivery_instruction,
)
from chat.verified_event_timing import event_timing_contract


def test_verified_shared_voice_requires_a_human_direct_reading():
    contract = verified_consultation_instruction()

    assert "READABLE CONSULTATION, NOT AN AUDIT" in contract
    assert "DECISION BEFORE DEFENCE" in contract
    assert "Do not begin with \"Thank you for consulting\"" in contract
    assert "Do not volunteer \"consult a doctor\"" in contract
    assert "Medical astrology disclaimer" in contract
    assert "astrological susceptibility or prediction" in contract
    assert "WARMTH, PERSONALIZATION, AND ASTROLOGICAL LANGUAGE" in contract
    assert "PERSONAL, PLEASURABLE, FULL-DEPTH READING" in contract
    assert "psychologically insightful and human-friendly" in contract
    assert "Never call them \"the" in contract


def test_verified_timing_contract_has_concise_ranked_structure():
    contract = event_timing_contract("technical")

    assert "## The promise and what shapes its timing" in contract
    assert "## When this becomes most likely" in contract
    assert "## How to hold the present period" in contract
    assert "not a separate \"Bottom line\"" in contract
    assert "every deterministic candidate window in its exact calculated rank order" in contract
    assert "fragmented all-systems report" in contract


def test_verified_final_delivery_override_applies_to_every_intent():
    contract = verified_final_delivery_instruction()

    assert "ALL VERIFIED QUESTIONS" in contract
    assert "as many useful Markdown" in contract
    assert "Do not greet, thank the user" in contract
    assert "Select and organize evidence" in contract
    assert "warmth and personal presence" in contract
    assert "chat-sentiment-positive" in contract
    assert "chat-sentiment-negative" in contract


def test_verified_final_delivery_requires_a_named_human_opening_when_available():
    contract = verified_final_delivery_instruction("Diksha Dwivedi")

    assert "Diksha Dwivedi" in contract
    assert "NON-NEGOTIABLE VOICE CHECK" in contract
    assert "Support ·" in contract


def test_every_verified_final_writer_ends_with_the_shared_delivery_override():
    from chat.verified_chat_pipeline import _verified_final_writer_instruction

    for mode in ("FACTUAL_LOOKUP", "PREDICT_PERIOD_OUTLOOK", "CHART_DASHA_ANALYSIS", "DEFAULT"):
        prompt = _verified_final_writer_instruction("technical", mode)
        assert "FINAL VISIBLE-ANSWER DELIVERY OVERRIDE — ALL VERIFIED QUESTIONS" in prompt
