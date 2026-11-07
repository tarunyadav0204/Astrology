from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import subprocess

import pytest
from fastapi import HTTPException
from PIL import Image

from reel_studio import storage, routes

JOB = 'job_' + 'c' * 32


def test_cover_roundtrip_preserves_entire_scene_and_uses_private_podcast_bucket(monkeypatch, tmp_path):
    monkeypatch.setenv('REEL_LOCAL_OUTPUT_DIR', str(tmp_path / 'reels'))
    monkeypatch.setenv('PODCAST_CACHE_BUCKET', 'podcast-test')
    objects = {}

    class Blob:
        def __init__(self, name): self.name = name
        def exists(self): return self.name in objects
        def upload_from_filename(self, path, **kwargs):
            assert kwargs['content_type'] == 'image/jpeg'
            objects[self.name] = Path(path).read_bytes()
        def download_to_filename(self, path, **kwargs): Path(path).write_bytes(objects[self.name])

    class Client:
        def bucket(self, name):
            assert name == 'podcast-test'
            return SimpleNamespace(blob=Blob)

    monkeypatch.setattr(storage, '_gcs_client', Client)
    source = tmp_path / 'scene.png'
    Image.new('RGB', (800, 800), 'red').save(source)
    cover = storage.store_thumbnail(18, JOB, source)
    with Image.open(cover) as image:
        assert image.size == (360, 640)
        assert image.getpixel((180, 320))[0] > 240
        # Square content is padded, not cropped or stretched to 9:16.
        assert image.getpixel((180, 10))[0] < 60
    saved = cover.read_bytes()
    cover.unlink()
    assert storage.load_thumbnail(18, JOB).read_bytes() == saved
    assert list(objects) == [f'reels/18/{JOB}/cover.jpg']


def test_old_reel_cover_is_extracted_once_without_generation(monkeypatch, tmp_path):
    import imageio_ffmpeg
    monkeypatch.setenv('REEL_LOCAL_OUTPUT_DIR', str(tmp_path))
    monkeypatch.delenv('PODCAST_CACHE_BUCKET', raising=False)
    path = storage.local_path(18, JOB)
    path.parent.mkdir(parents=True)
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-y', '-f', 'lavfi', '-i',
                    'color=c=red:s=180x320:d=0.2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(path)],
                   check=True, capture_output=True, timeout=20)
    cover = storage.load_thumbnail(18, JOB)
    assert Image.open(cover).size == (360, 640)
    assert Image.open(cover).getpixel((180, 320))[0] > 240
    path.unlink()
    assert storage.load_thumbnail(18, JOB) == cover


@pytest.mark.parametrize('row', [None, (18, 'queued'), (18, 'failed')])
def test_thumbnail_requires_owned_completed_job_before_reading_storage(monkeypatch, row):
    @contextmanager
    def connection(): yield object()
    def execute(conn, sql, args):
        assert 'id=%s AND user_id=%s' in sql
        assert args == (JOB, 18)
        return SimpleNamespace(fetchone=lambda: row)
    monkeypatch.setattr(routes, 'get_conn', connection)
    monkeypatch.setattr(routes, 'execute', execute)
    monkeypatch.setattr(storage, 'load_thumbnail', lambda *_: pytest.fail('Must authorize before reading storage'))
    with pytest.raises(HTTPException) as error:
        routes.reel_thumbnail(JOB, SimpleNamespace(userid=18))
    assert error.value.status_code == 404


def test_thumbnail_upload_failure_does_not_publish_local_cover(monkeypatch, tmp_path):
    monkeypatch.setenv('REEL_LOCAL_OUTPUT_DIR', str(tmp_path / 'reels'))
    monkeypatch.setenv('PODCAST_CACHE_BUCKET', 'podcast-test')
    def unavailable(): raise RuntimeError('Storage unavailable')
    monkeypatch.setattr(storage, '_gcs_client', unavailable)
    source = tmp_path / 'scene.png'
    Image.new('RGB', (90, 160)).save(source)
    with pytest.raises(RuntimeError, match='Storage unavailable'):
        storage.store_thumbnail(18, JOB, source)
    assert not storage.thumbnail_path(18, JOB).exists()
