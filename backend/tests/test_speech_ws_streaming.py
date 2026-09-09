import asyncio
from types import SimpleNamespace

import pytest

from speech import ws_routes


@pytest.mark.asyncio
async def test_poll_answer_publishes_new_processing_content_as_deltas(monkeypatch):
    payloads = iter(
        [
            {"status": "processing", "partial_content": "First sentence."},
            {"status": "processing", "partial_content": "First sentence. Second sentence."},
            {"status": "completed", "content": "First sentence. Second sentence."},
        ]
    )
    sent = []

    async def fake_status(_message_id, _user):
        return next(payloads)

    async def fake_send(_websocket, event_type, **payload):
        sent.append((event_type, payload))

    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(ws_routes, "check_message_status", fake_status)
    monkeypatch.setattr(ws_routes, "_send", fake_send)
    monkeypatch.setattr(ws_routes.asyncio, "sleep", no_sleep)

    stream_state = {"content": "", "index": 0}
    result = await ws_routes._poll_answer(
        42,
        SimpleNamespace(userid=18),
        asyncio.Event(),
        object(),
        "turn-1",
        stream_state,
    )

    chunks = [payload for event, payload in sent if event == "answer_chunk"]
    assert [chunk["text"] for chunk in chunks] == ["First sentence.", " Second sentence."]
    assert all(chunk["validated"] is False for chunk in chunks)
    assert stream_state["content"] == "First sentence. Second sentence."
    assert result["status"] == "completed"


def test_split_answer_chunks_keeps_sentence_boundaries():
    chunks = ws_routes._split_answer_chunks(
        "One short sentence. Another sentence follows. Final sentence.",
        max_chars=35,
    )

    assert chunks == ["One short sentence.", "Another sentence follows.", "Final sentence."]


def test_visible_stream_checkpoint_hides_composer_metadata():
    assert ws_routes._visible_stream_checkpoint(
        'Visible answer.\nNEXT_ACTION_META: {"type":"none"}'
    ) == "Visible answer."


def test_visible_stream_checkpoint_never_exposes_evidence_markers():
    assert ws_routes._visible_stream_checkpoint(
        "लाभ का घर मजबूत है। [[SH_D1_H11_OCC_VENUS]] आगे का उत्तर।"
    ) == "लाभ का घर मजबूत है। आगे का उत्तर।"
    assert ws_routes._visible_stream_checkpoint(
        "लाभ का घर मजबूत है। [[SH_D1_H11_OCC_"
    ) == "लाभ का घर मजबूत है।"
    assert ws_routes._visible_stream_checkpoint(
        "लाभ का घर मजबूत है। [[SH_"
    ) == "लाभ का घर मजबूत है।"


@pytest.mark.parametrize(
    ("validation_enabled", "speech_opt_in", "expected"),
    [
        (True, False, False),
        (True, True, True),
        (False, False, True),
    ],
)
def test_provisional_chunks_are_playable_only_when_configured(
    monkeypatch, validation_enabled, speech_opt_in, expected
):
    monkeypatch.setattr(
        ws_routes,
        "is_instant_response_validation_enabled",
        lambda: validation_enabled,
    )
    monkeypatch.setattr(
        ws_routes,
        "is_speech_unvalidated_streaming_enabled",
        lambda: speech_opt_in,
    )

    assert ws_routes._provisional_speech_chunks_playable() is expected


@pytest.mark.asyncio
async def test_handle_ask_does_not_resend_already_streamed_prefix(monkeypatch):
    sent = []

    async def fake_send(_websocket, event_type, **payload):
        sent.append((event_type, payload))

    async def fake_invoke(_request, _user):
        return {"status": "processing", "message_id": 77}

    async def fake_poll(_message_id, _user, _cancel, _websocket, _turn_id, stream_state):
        stream_state["content"] = "Already shown."
        stream_state["index"] = 1
        return {"status": "completed", "content": "Already shown. Final sentence."}

    monkeypatch.setattr(ws_routes, "_send", fake_send)
    monkeypatch.setattr(ws_routes, "_invoke_chat_v2", fake_invoke)
    monkeypatch.setattr(ws_routes, "_poll_answer", fake_poll)

    await ws_routes._handle_ask(
        object(),
        SimpleNamespace(userid=18),
        {
            "turn_id": "turn-2",
            "session_id": "session-1",
            "question": "Question",
            "birth_details": {"name": "ABC"},
        },
        asyncio.Event(),
    )

    validated = [payload for event, payload in sent if event == "answer_chunk"]
    assert [payload["text"] for payload in validated] == ["Final sentence."]
    assert validated[0]["content"] == "Already shown. Final sentence."
    assert sent[-1][0] == "turn_completed"
