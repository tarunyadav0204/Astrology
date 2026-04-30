from chat_history.routes import (
    _attach_completed_status_payload,
    _should_preserve_completed_message,
)


def test_should_preserve_completed_message_only_when_completed_and_non_empty():
    assert _should_preserve_completed_message("completed", "Detailed answer") is True
    assert _should_preserve_completed_message("completed", "   ") is False
    assert _should_preserve_completed_message("failed", "Detailed answer") is False


def test_attach_completed_status_payload_parses_metadata():
    response = {"status": "failed", "message_type": "answer"}
    completed = _attach_completed_status_payload(
        response,
        content="Your answer is ready",
        completed_at="2026-04-30T10:00:00",
        terms='["dasha"]',
        glossary='{"dasha":"period"}',
        summary_image="https://example.com/summary.png",
        follow_up_questions='["Ask about timing"]',
        gate_metadata='{"intent_gate":"career"}',
    )

    assert completed["status"] == "completed"
    assert completed["content"] == "Your answer is ready"
    assert completed["terms"] == ["dasha"]
    assert completed["glossary"] == {"dasha": "period"}
    assert completed["summary_image"] == "https://example.com/summary.png"
    assert completed["follow_up_questions"] == ["Ask about timing"]
    assert completed["intent_gate"] == "career"
