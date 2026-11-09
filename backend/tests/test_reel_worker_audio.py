import asyncio
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from google.api_core.exceptions import InvalidArgument, ResourceExhausted
from reel_studio import worker, podcast_speech, costs
from tts.routes import _synthesize_podcast_segment


@pytest.mark.parametrize('reject_ssml', [False, True])
def test_reel_matches_podcast_requests_and_keeps_admin_voice(monkeypatch, reject_ssml):
    clients, slots, events = [], [], []
    class FakeClient:
        def __init__(self, credentials=None):
            self.calls = []
            self.closed = False
            self.transport = SimpleNamespace(close=lambda: setattr(self, 'closed', True))
            clients.append(self)
        def synthesize_speech(self, **kwargs):
            self.calls.append((kwargs['input'].text, kwargs['input'].ssml,
                kwargs['voice'].name, kwargs['voice'].language_code,
                kwargs['audio_config'].speaking_rate))
            if reject_ssml and kwargs['input'].ssml:
                raise InvalidArgument('SSML unsupported')
            return SimpleNamespace(audio_content=b'mp3')

    @contextmanager
    def attempt(stage, model, **metadata):
        events.append((stage, model, costs.CURRENT.get(), metadata))
        yield SimpleNamespace(finish=lambda usage: None)

    monkeypatch.setattr(worker, '_get_google_credentials', lambda: None)
    monkeypatch.setattr(worker.texttospeech, 'TextToSpeechClient', FakeClient)
    monkeypatch.setattr(podcast_speech, 'wait_for_tts_slot', lambda: slots.append(True))
    monkeypatch.setattr(costs, 'attempt', attempt)
    voice = 'en-IN-Chirp-HD-O'
    passage = 'आप जान सकते हैं कि भरोसा महत्वपूर्ण है। आप खुल सकते हैं, लेकिन समय लें।'
    direct = FakeClient()
    expected = asyncio.run(_synthesize_podcast_segment(direct, voice, 'female', passage, 'en-IN'))
    marker = ('user', 'run', {})
    token = costs.CURRENT.set(marker)
    try:
        actual = asyncio.run(worker._podcast_audio(passage, 'hi', voice))
    finally:
        costs.CURRENT.reset(token)
    reel = clients[-1]
    assert actual == (expected, voice)
    assert reel.calls == direct.calls
    assert all(call[-1] == 1.0 for call in reel.calls)
    assert len(slots) == len(events) == len(reel.calls)
    assert all(event[2] == marker for event in events)
    assert reel.closed


def test_quota_retry_is_paced_and_keeps_request(monkeypatch):
    calls, slots, cooldowns = [], [], []
    class Client:
        def synthesize_speech(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise ResourceExhausted('quota')
            return SimpleNamespace(audio_content=b'ok')
    monkeypatch.setattr(podcast_speech, 'wait_for_tts_slot', lambda: slots.append(True))
    monkeypatch.setattr(podcast_speech, 'cool_down_tts', cooldowns.append)
    client = podcast_speech.MeteredSpeechClient(Client())
    result = client.synthesize_speech(input=SimpleNamespace(text='पूरा वाक्य।', ssml=''),
        voice=SimpleNamespace(name='en-IN-Chirp-HD-O'), audio_config=None)
    assert result.audio_content == b'ok'
    assert len(slots) == 2 and cooldowns == [15]
    assert calls[0] == calls[1]


def test_reel_transition_pauses_are_semantic_with_legacy_default():
    assert worker._transition_pause_seconds({"pause_after": "none"}) == 0.0
    assert worker._transition_pause_seconds({"pause_after": "medium"}) == 0.6
    assert worker._transition_pause_seconds({"pause_after": "long"}) == 0.9
    assert worker._transition_pause_seconds({}) == 0.35
    assert worker._transition_pause_seconds({"pause_after": "unexpected"}) == 0.35
