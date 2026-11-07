import asyncio
from types import SimpleNamespace

from reel_studio import worker


def test_reel_audio_uses_direct_plain_google_tts(monkeypatch):
    calls = {}

    class FakeClient:
        def __init__(self, credentials):
            calls["credentials"] = credentials

        def synthesize_speech(self, *, input, voice, audio_config, retry, timeout):
            assert retry is None
            assert timeout == 120
            calls["text"] = input.text
            calls["voice"] = voice
            calls["audio_config"] = audio_config
            return SimpleNamespace(audio_content=b"mp3")

    monkeypatch.setattr(worker, "_segment_text_to_plain", lambda text: f"plain:{text}")
    monkeypatch.setattr(worker, "_get_google_credentials", lambda: "credentials")
    monkeypatch.setattr(worker, "_build_voice_and_config", lambda *args: ("voice", "audio-config"))
    monkeypatch.setattr(worker.texttospeech, "TextToSpeechClient", FakeClient)

    audio, voice_name = asyncio.run(worker._podcast_audio("narration", "hi", "hi-IN-Chirp-HD-F"))

    assert (audio, voice_name) == (b"mp3", "hi-IN-Chirp-HD-F")
    assert calls["text"] == "plain:narration"
    assert calls["credentials"] == "credentials"


def test_reel_transition_pauses_are_semantic_with_legacy_default():
    assert worker._transition_pause_seconds({"pause_after": "none"}) == 0.0
    assert worker._transition_pause_seconds({"pause_after": "medium"}) == 0.6
    assert worker._transition_pause_seconds({"pause_after": "long"}) == 0.9
    assert worker._transition_pause_seconds({}) == 0.35
    assert worker._transition_pause_seconds({"pause_after": "unexpected"}) == 0.35
