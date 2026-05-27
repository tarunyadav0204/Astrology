from chat_history.routes import (
    _attach_completed_status_payload,
    _processing_started_at_age_minutes,
    _should_preserve_completed_message,
    _timestamp_is_future,
)
from datetime import datetime, timedelta


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


def test_processing_started_at_age_minutes_handles_datetimes():
    age = _processing_started_at_age_minutes(datetime.now() - timedelta(minutes=15))

    assert age is not None
    assert age >= 14.9


def test_processing_started_at_age_minutes_ignores_bad_values():
    assert _processing_started_at_age_minutes(None) is None
    assert _processing_started_at_age_minutes("not-a-date") is None


def test_timestamp_is_future():
    assert _timestamp_is_future(datetime.now() + timedelta(minutes=1)) is True
    assert _timestamp_is_future(datetime.now() - timedelta(minutes=1)) is False
    assert _timestamp_is_future("not-a-date") is False
