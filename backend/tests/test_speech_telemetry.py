import asyncio
import logging
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from speech.routes import (
    SpeechTelemetryRequest,
    _fallback_voice_guide,
    _filter_recent_guide_lines,
    speech_telemetry,
)


def test_speech_telemetry_logs_only_allowlisted_metadata(caplog):
    request = SpeechTelemetryRequest(
        event="first_spoken_audio_ms",
        platform="web",
        value_ms=999_999,
        success=True,
        metadata={
            "provider": "google",
            "language": "hindi",
            "transcript": "private spoken content",
            "answer": "private answer content",
        },
    )

    with caplog.at_level(logging.INFO, logger="speech.routes"):
        result = asyncio.run(speech_telemetry(request, SimpleNamespace(userid=42)))

    assert result == {"ok": True}
    assert "value_ms=600000" in caplog.text
    assert '"provider": "google"' in caplog.text
    assert "private spoken content" not in caplog.text
    assert "private answer content" not in caplog.text


def test_speech_telemetry_rejects_unknown_events():
    request = SpeechTelemetryRequest(event="raw_transcript")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(speech_telemetry(request, SimpleNamespace(userid=42)))

    assert exc_info.value.status_code == 400


def test_processing_bridge_has_no_repetitive_static_fallback():
    assert _fallback_voice_guide("processing", language="hi")["lines"] == []
    assert _fallback_voice_guide("processing", language="en")["lines"] == []


def test_processing_bridge_filters_recent_and_in_batch_paraphrases():
    lines = [
        "I am checking the relevant houses for your career question.",
        "I’m checking the relevant houses for your career question now.",
        "Next I am comparing the active timing periods.",
    ]
    recent = ["I am checking the relevant houses for your career question now."]

    assert _filter_recent_guide_lines(lines, recent, 3) == [
        "Next I am comparing the active timing periods."
    ]
