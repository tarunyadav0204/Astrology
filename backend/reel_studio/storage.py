"""Private reel MP4 cache, using the podcast bucket and credentials."""
import os
import re
import tempfile
import subprocess
import threading
from pathlib import Path

from tts.podcast_cache import _gcs_client
from reel_studio import costs

_thumbnail_locks = [threading.Lock() for _ in range(32)]


def thumbnail_path(user_id: int, job_id: str) -> Path:
    return local_path(user_id, job_id).with_name("cover.jpg")


def store_thumbnail(user_id: int, job_id: str, image: Path) -> Path:
    """Reuse a generated scene; no image-provider call is needed for a cover."""
    from PIL import Image, ImageOps
    target = thumbnail_path(user_id, job_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image) as original:
        cover = ImageOps.pad(original.convert("RGB"), (360, 640), color="#200e18")
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".jpg", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            cover.save(temporary, "JPEG", quality=82, optimize=True)
            bucket = os.getenv("PODCAST_CACHE_BUCKET", "").strip()
            if bucket:
                name = _object_name(user_id, job_id).replace("final-reel.mp4", "cover.jpg")
                with costs.attempt('storage', 'gcs', asset='thumbnail') as event:
                    _gcs_client().bucket(bucket).blob(name).upload_from_filename(str(temporary), content_type="image/jpeg", timeout=60)
                    event.finish({'bytes': temporary.stat().st_size, 'writes': 1})
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return target


def load_thumbnail(user_id: int, job_id: str) -> Path | None:
    """Restore the cover, or backfill older reels from their first video frame."""
    target = thumbnail_path(user_id, job_id)
    with _thumbnail_locks[hash((user_id, job_id)) % len(_thumbnail_locks)]:
        if target.is_file() and target.stat().st_size:
            return target
        bucket = os.getenv("PODCAST_CACHE_BUCKET", "").strip()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix=".jpg", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            if bucket:
                blob = _gcs_client().bucket(bucket).blob(_object_name(user_id, job_id).replace("final-reel.mp4", "cover.jpg"))
                if blob.exists():
                    blob.download_to_filename(str(temporary), timeout=60)
                    temporary.replace(target)
                    return target
            video = load_reel(user_id, job_id)
            if video is None:
                return None
            import imageio_ffmpeg
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-y", "-i", str(video),
                            "-frames:v", "1", "-vf", "scale=360:640:force_original_aspect_ratio=decrease", str(temporary)],
                           check=True, capture_output=True, timeout=45)
            return store_thumbnail(user_id, job_id, temporary)
        finally:
            temporary.unlink(missing_ok=True)


def _object_name(user_id: int, job_id: str) -> str:
    if not re.fullmatch(r"job_[a-f0-9]{32}", job_id):
        raise ValueError("Invalid reel job ID")
    return f"reels/{int(user_id)}/{job_id}/final-reel.mp4"


def local_path(user_id: int, job_id: str) -> Path:
    _object_name(user_id, job_id)
    return Path(os.getenv("REEL_LOCAL_OUTPUT_DIR", "storage/reels")) / str(int(user_id)) / job_id / "final-reel.mp4"


def store_reel(user_id: int, job_id: str, path: Path) -> None:
    """Require successful persistence before marking a configured GCS job ready."""
    bucket = os.getenv("PODCAST_CACHE_BUCKET", "").strip()
    if bucket:
        with costs.attempt('storage', 'gcs', asset='reel') as event:
            _gcs_client().bucket(bucket).blob(_object_name(user_id, job_id)).upload_from_filename(
                str(path), content_type="video/mp4", timeout=180,
            )
            event.finish({'bytes': path.stat().st_size, 'writes': 1})
    else:
        with costs.attempt('storage', 'local', asset='reel') as event:
            event.finish({'bytes': path.stat().st_size, 'writes': 0})


def load_reel(user_id: int, job_id: str) -> Path | None:
    path = local_path(user_id, job_id)
    bucket = os.getenv("PODCAST_CACHE_BUCKET", "").strip()
    if path.is_file() and path.stat().st_size:
        # Also persist reels created before bucket storage was introduced.
        if bucket:
            blob = _gcs_client().bucket(bucket).blob(_object_name(user_id, job_id))
            if not blob.exists():
                store_reel(user_id, job_id, path)
        return path
    if not bucket:
        return None
    blob = _gcs_client().bucket(bucket).blob(_object_name(user_id, job_id))
    if not blob.exists():
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    # Do not expose a partially downloaded MP4 to simultaneous player requests.
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".mp4", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        blob.download_to_filename(str(temporary), timeout=180)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path
