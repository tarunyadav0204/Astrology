import json
from types import SimpleNamespace

import pytest

from tts import routes


@pytest.mark.asyncio
async def test_podcast_status_uses_history_languages_without_downloading_audio(monkeypatch):
    monkeypatch.setattr(
        routes,
        "_podcast_history_languages",
        lambda userid, message_id: ["hi"],
    )

    def fail_if_audio_is_downloaded(*_args, **_kwargs):
        raise AssertionError("status lookup must not download podcast audio")

    monkeypatch.setattr(routes, "get_cached_audio", fail_if_audio_is_downloaded)

    response = await routes.podcast_check_cache(
        message_id="321",
        lang="en",
        current_user=SimpleNamespace(userid=18),
    )
    payload = json.loads(response.body)

    assert payload == {
        "cached": False,
        "ready": True,
        "languages": ["hi"],
    }


@pytest.mark.asyncio
async def test_podcast_status_marks_requested_owned_language_cached(monkeypatch):
    monkeypatch.setattr(
        routes,
        "_podcast_history_languages",
        lambda userid, message_id: ["en", "hi"],
    )

    response = await routes.podcast_check_cache(
        message_id="321",
        lang="hi",
        current_user=SimpleNamespace(userid=18),
    )
    payload = json.loads(response.body)

    assert payload["cached"] is True
    assert payload["ready"] is True
    assert payload["languages"] == ["en", "hi"]
