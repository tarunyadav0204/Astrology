"""Private reel MP4 cache, using the podcast bucket and credentials."""
import os
import re
import tempfile
from pathlib import Path

from tts.podcast_cache import _gcs_client


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
        _gcs_client().bucket(bucket).blob(_object_name(user_id, job_id)).upload_from_filename(
            str(path), content_type="video/mp4", timeout=180,
        )


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
