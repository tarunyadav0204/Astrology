import base64
import subprocess
from types import SimpleNamespace

import pytest

from reel_studio import worker
from reel_studio.presenter import validate_presenter_beats, video_prompt
from reel_studio import presenter


def test_direct_video_request_is_five_seconds_360p_with_same_reference(monkeypatch):
    payloads = []
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, *, headers, json):
            payloads.append(json)
            return SimpleNamespace(is_error=False, json=lambda: {'steps': [{'content': [{'type': 'video', 'data': base64.b64encode(b'video').decode()}]}], 'usage': {'total_output_tokens': 123}})
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    monkeypatch.setattr(worker.httpx, 'Client', Client)
    for role in ('opening', 'closing'):
        assert worker._run_video(video_prompt('Your chart guides your next step.', 'hi', role), image=b'same-face')[0] == b'video'
    for payload in payloads:
        assert payload['model'] == 'gemini-omni-1.1-flash'
        assert payload['response_format'] == {'type': 'video', 'aspect_ratio': '9:16', 'resolution': '360p', 'duration': '5s'}
        assert payload['input'][0]['data'] == base64.b64encode(b'same-face').decode()
        assert 'natural Hindi' in payload['input'][1]['text']
        assert all(part['type'] != 'audio' for part in payload['input'])


def test_presenter_requires_two_short_complete_bookends():
    validate_presenter_beats([{'type': 'opening', 'narration': 'Your career reading begins here.'}, {'type': 'closing', 'narration': 'Build steadily on your strengths.'}])
    with pytest.raises(ValueError):
        validate_presenter_beats([{'type': 'opening', 'narration': 'word ' * 11}, {'type': 'closing', 'narration': 'Done.'}])
    with pytest.raises(ValueError):
        validate_presenter_beats([{'type': 'chart_focus', 'narration': 'Start.'}, {'type': 'closing', 'narration': 'Done.'}])


@pytest.mark.parametrize('status,code', [(500, 'api_error'), (503, 'UNAVAILABLE'), (429, 'rate_limit'), (400, 'api_error')])
def test_temporary_video_errors_retry_the_identical_clip(monkeypatch, status, code):
    payloads, delays = [], []
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, *, headers, json):
            payloads.append(json)
            if len(payloads) < 3:
                return SimpleNamespace(is_error=True, status_code=status, json=lambda: {'error': {'code': code}})
            return SimpleNamespace(is_error=False, json=lambda: {'output_video': {'data': base64.b64encode(b'video').decode()}, 'usage': {}})
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    monkeypatch.setattr(worker.httpx, 'Client', Client)
    monkeypatch.setattr(worker.time, 'sleep', delays.append)
    assert worker._run_video('exact approved line', image=b'same-presenter')[0] == b'video'
    assert len(payloads) == 3 and payloads[0] == payloads[1] == payloads[2]
    assert delays == [2, 4]


@pytest.mark.parametrize('status,code,attempts', [(500, 'api_error', 3), (400, 'invalid_request', 1), (401, 'unauthorized', 1), (422, 'validation_error', 1)])
def test_video_retry_limit_and_permanent_error_behavior(monkeypatch, status, code, attempts):
    calls = []
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(is_error=True, status_code=status, json=lambda: {'error': {'code': code}})
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    monkeypatch.setattr(worker.httpx, 'Client', Client)
    monkeypatch.setattr(worker.time, 'sleep', lambda _: None)
    with pytest.raises(RuntimeError): worker._run_video('approved line', image=b'face')
    assert len(calls) == attempts


def test_composition_keeps_provider_audio_and_middle_narration(tmp_path, monkeypatch):
    ffmpeg = worker.imageio_ffmpeg.get_ffmpeg_exe()
    def run(*args):
        return subprocess.run([ffmpeg, '-nostdin', '-hide_banner', '-y', *args], check=True, capture_output=True)
    first, middle, last = [tmp_path / f'{name}.mp4' for name in ('first', 'middle', 'last')]
    for clip in (first, last):
        run('-f', 'lavfi', '-i', 'color=c=black:s=360x640:r=30', '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=44100', '-t', '5', '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', str(clip))
        worker._validate_presenter_clip(ffmpeg, clip)
    run('-f', 'lavfi', '-i', 'color=c=black:s=180x320:r=30', '-t', '2', '-c:v', 'libx264', str(middle))
    narration = tmp_path / 'narration.wav'
    run('-f', 'lavfi', '-i', 'sine=frequency=880:sample_rate=44100', '-t', '2', str(narration))
    monkeypatch.setattr(worker, 'WIDTH', 180)
    monkeypatch.setattr(worker, 'HEIGHT', 320)
    output = tmp_path / 'final.mp4'
    worker._compose(ffmpeg, [first, middle, last], [None, narration, None], output, source_audio={0, 2})
    assert abs(worker._duration(ffmpeg, output) - 12) < 0.1
    for start in (1, 5.3, 9):
        check = run('-ss', str(start), '-i', str(output), '-t', '0.5', '-vn', '-af', 'volumedetect', '-f', 'null', '-')
        assert b'mean_volume: -inf' not in check.stderr
        assert b'mean_volume:' in check.stderr


def test_invalid_provider_duration_and_missing_audio_are_errors(tmp_path):
    ffmpeg = worker.imageio_ffmpeg.get_ffmpeg_exe()
    clip = tmp_path / 'invalid.mp4'
    for duration in (4, 5):
        subprocess.run([ffmpeg, '-nostdin', '-y', '-f', 'lavfi', '-i', 'color=s=360x640:r=30', '-t', str(duration), '-c:v', 'libx264', str(clip)], check=True, capture_output=True)
        with pytest.raises(RuntimeError, match='five seconds' if duration == 4 else 'no voice track'):
            worker._validate_presenter_clip(ffmpeg, clip)


def test_look_changes_outfit_and_background_but_preserves_reference_identity():
    import random
    from io import BytesIO
    from PIL import Image
    previous = None
    for i in range(30):
        look = presenter.choose_look(previous, rng=random.Random(i))
        if previous:
            assert look['outfit'] != previous['outfit']
            assert look['background'] != previous['background']
        prompt = presenter.portrait_prompt(look)
        assert look['outfit'] in prompt and look['background'] in prompt
        assert 'identity and hairstyle only' in prompt
        assert 'replace its emerald saree' in prompt
        previous = look
    with Image.open(BytesIO(presenter.reference_image())) as source:
        assert source.width > 500 and source.height > source.width
        source.verify()
    video = presenter.video_prompt('Welcome to your reading.', 'en', 'opening')
    assert 'same face, hair, attire, lighting and set' in video
    assert 'burgundy silk saree' not in video


def test_presenter_look_is_saved_and_reused_for_retry(monkeypatch):
    import json
    from contextlib import contextmanager
    previous = presenter.choose_look()
    writes = []
    @contextmanager
    def connect():
        yield SimpleNamespace(commit=lambda: None)
    def execute(conn, sql, params):
        if sql.startswith('SELECT'):
            return SimpleNamespace(fetchall=lambda: [(json.dumps({'presenter_look': previous}),)])
        writes.append(json.loads(params[0]))
    monkeypatch.setattr(presenter, 'get_conn', connect)
    monkeypatch.setattr(presenter, 'execute', execute)
    plan = {}
    source, look = presenter.prepare_presenter(1, 'job-test', plan)
    assert look['outfit'] != previous['outfit']
    assert look['background'] != previous['background']
    assert writes[0]['presenter_look'] == look
    assert presenter.prepare_presenter(1, 'job-test', plan) == (source, look)
    assert len(writes) == 1
    monkeypatch.setattr(presenter, 'reference_image', lambda: b'different character')
    with pytest.raises(RuntimeError, match='reference changed'):
        presenter.prepare_presenter(1, 'job-test', plan)


def test_render_sends_identity_to_gpt_then_same_styled_portrait_to_both_videos(tmp_path, monkeypatch):
    import json
    from contextlib import contextmanager
    import reel_studio.storage as storage
    images, videos = [], []
    look = presenter.choose_look()
    async def image(prompt, **kwargs):
        images.append((prompt, kwargs))
        return b'styled-portrait'
    def video(prompt, *, image):
        videos.append(image)
        return b'clip', {}
    @contextmanager
    def connect():
        yield SimpleNamespace(commit=lambda: None)
    monkeypatch.setattr(worker, 'ROOT', tmp_path)
    monkeypatch.setenv('GEMINI_API_KEY', 'test-no-network')
    monkeypatch.setattr(worker, '_brand_logo', lambda: b'logo')
    monkeypatch.setattr(worker, 'prepare_presenter', lambda *args: (b'approved-character', look))
    monkeypatch.setattr(worker, '_gpt_image', image)
    monkeypatch.setattr(worker, '_run_video', video)
    monkeypatch.setattr(worker, '_validate_presenter_clip', lambda *args: None)
    monkeypatch.setattr(worker, '_duration', lambda *args: 10)
    monkeypatch.setattr(worker, '_compose', lambda ff, clips, audio, output, **kw: output.write_bytes(b'final'))
    monkeypatch.setattr(worker, '_update', lambda *args, **kwargs: None)
    monkeypatch.setattr(worker, 'get_podcast_tts_voices', lambda lang: ('voice', 'other'))
    monkeypatch.setattr(worker, 'get_conn', connect)
    monkeypatch.setattr(worker, 'execute', lambda *args: None)
    monkeypatch.setattr(storage, 'store_reel', lambda *args: None)
    monkeypatch.setattr(storage, 'store_thumbnail', lambda *args: None)
    plan = {'run_id': 'test', 'chart_snapshot': {'valid': True}, 'settings': {'presenter_enabled': True},
            'storyboard': [{'type': 'opening', 'narration': 'Welcome to your reading.'},
                           {'type': 'closing', 'narration': 'Thank you for joining us.'}]}
    assert worker._render_claimed_job('job-test', (1, json.dumps(plan))) == 'completed'
    assert len(images) == 1
    assert images[0][1]['identity_reference'] == b'approved-character'
    assert images[0][1]['quality'] == 'low'
    assert 'logo' not in images[0][1]
    assert look['outfit'] in images[0][0]
    assert videos == [b'styled-portrait', b'styled-portrait']
