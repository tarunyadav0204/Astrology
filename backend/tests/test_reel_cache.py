import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from reel_studio import routes, storage

JOB = "job_" + "a" * 32


def test_bucket_store_and_restore_uses_podcast_bucket(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_CACHE_BUCKET", "podcast-test")
    monkeypatch.setenv("REEL_LOCAL_OUTPUT_DIR", str(tmp_path))
    objects = {}

    class Blob:
        def __init__(self, name): self.name = name
        def exists(self): return self.name in objects
        def upload_from_filename(self, path, **kwargs):
            from pathlib import Path
            assert kwargs["content_type"] == "video/mp4"
            objects[self.name] = Path(path).read_bytes()
        def download_to_filename(self, path, **kwargs):
            from pathlib import Path
            Path(path).write_bytes(objects[self.name])

    class Client:
        def bucket(self, name):
            assert name == "podcast-test"
            return SimpleNamespace(blob=Blob)

    monkeypatch.setattr(storage, "_gcs_client", Client)
    path = storage.local_path(18, JOB)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"test-video")
    storage.store_reel(18, JOB, path)
    path.unlink()
    assert storage.load_reel(18, JOB).read_bytes() == b"test-video"
    assert storage.load_reel(19, JOB) is None
    assert len(objects) == 1


def test_storage_failure_is_not_silently_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("PODCAST_CACHE_BUCKET", "podcast-test")
    def unavailable(): raise RuntimeError("Storage unavailable")
    monkeypatch.setattr(storage, "_gcs_client", unavailable)
    with pytest.raises(RuntimeError, match="Storage unavailable"):
        storage.store_reel(18, JOB, tmp_path / "video.mp4")


def mock_jobs(monkeypatch, rows):
    @contextmanager
    def conn(): yield SimpleNamespace(commit=lambda: None)
    def execute(_conn, sql, args):
        assert "user_id=%s AND source_message_id=%s" in sql
        assert args == (18, 42)
        return SimpleNamespace(fetchall=lambda: rows)
    monkeypatch.setattr(routes, "get_conn", conn)
    monkeypatch.setattr(routes, "_ensure_tables", lambda _: None)
    monkeypatch.setattr(routes, "execute", execute)


def test_saved_lookup_reopens_existing_reel_without_planning(monkeypatch):
    raw = json.dumps({"settings": {"language": "en"}})
    mock_jobs(monkeypatch, [(JOB, "completed", "/download", None, raw)])
    result = routes.saved_reel(42, None, SimpleNamespace(userid=18))
    assert result["job"]["job_id"] == JOB
    assert result["job"]["cached"] is True


def test_saved_lookup_skips_failed_recreation(monkeypatch):
    raw = json.dumps({"settings": {"language": "en"}})
    mock_jobs(monkeypatch, [("failed", "failed", None, "error", raw), (JOB, "completed", "/download", None, raw)])
    assert routes.saved_reel(42, None, SimpleNamespace(userid=18))["job"]["job_id"] == JOB
    assert routes.saved_reel(42, "hi", SimpleNamespace(userid=18))["job"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("byte_range,expected,code", [(None, b"0123456789", 200), ("bytes=2-5", b"2345", 206), ("bytes=-3", b"789", 206), ("bytes=7-", b"789", 206)])
async def test_video_seek_ranges(tmp_path, byte_range, expected, code):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"0123456789")
    response = routes._video_response(path, byte_range)
    assert response.status_code == code
    assert int(response.headers["content-length"]) == len(expected)
    assert b"".join([chunk async for chunk in response.body_iterator]) == expected


def test_invalid_video_range(tmp_path):
    path = tmp_path / "video.mp4"
    path.write_bytes(b"0123456789")
    with pytest.raises(HTTPException) as error:
        routes._video_response(path, "bytes=100-")
    assert error.value.status_code == 416
