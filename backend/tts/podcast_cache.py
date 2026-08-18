"""
Podcast audio cache: in-memory fallback + optional Google Cloud Storage.
Store generated podcast MP3 by message_id + language so replay and share don't regenerate (no extra charge).

- When PODCAST_CACHE_BUCKET is set: use GCS (persists across restarts).
- Always also write a local disk copy so emulator/history replay survives backend reload
  when GCS is not configured.
"""

import os
import re
import logging
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)

# Env: bucket name for podcast cache. If unset, use memory + local disk.
PODCAST_CACHE_BUCKET_ENV = "PODCAST_CACHE_BUCKET"

# Bump when synthesis/prosody changes so stale MP3s are not replayed for new generates.
# Lookups still fall back to previous versions so podcast history can replay.
PODCAST_AUDIO_VERSION = "v6"
_PREVIOUS_AUDIO_VERSIONS = ("v5", "v4", "v3", "v2", "v1")


# In-memory cache when GCS is not configured. Key: (message_id_str, lang_str, version) -> bytes. Max entries.
_MEMORY_CACHE: dict[tuple[str, str, str], bytes] = {}
_MEMORY_CACHE_MAX = 500


def _safe_key_part(s: str, max_len: int = 200) -> str:
    """Sanitize for GCS object name: alphanumeric, dash, underscore only."""
    if not s:
        return "unknown"
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
    return safe[:max_len] if len(safe) > max_len else safe


def _cache_key(message_id: str, lang: str, version: Optional[str] = None) -> tuple[str, str, str]:
    return (
        str(message_id).strip() or "unknown",
        (lang or "en").strip()[:10],
        version or PODCAST_AUDIO_VERSION,
    )


def _object_name(message_id: str, lang: str, version: Optional[str] = None) -> str:
    message_id_safe = _safe_key_part(str(message_id))
    lang_safe = _safe_key_part(str(lang), 10)
    ver = version or PODCAST_AUDIO_VERSION
    return f"podcast/{message_id_safe}_{lang_safe}_{ver}.mp3"


def _disk_dir() -> str:
    override = (os.getenv("PODCAST_CACHE_DIR") or "").strip()
    return override or os.path.join(tempfile.gettempdir(), "astroroshni_podcast_cache")


def _disk_path(message_id: str, lang: str, version: Optional[str] = None) -> str:
    return os.path.join(_disk_dir(), os.path.basename(_object_name(message_id, lang, version)))


def _remember(message_id: str, lang: str, audio_bytes: bytes, version: Optional[str] = None) -> None:
    key = _cache_key(message_id, lang, version)
    if len(_MEMORY_CACHE) < _MEMORY_CACHE_MAX or key in _MEMORY_CACHE:
        _MEMORY_CACHE[key] = audio_bytes


def _read_disk(message_id: str, lang: str, version: Optional[str] = None) -> Optional[bytes]:
    path = _disk_path(message_id, lang, version)
    try:
        if not os.path.isfile(path):
            return None
        with open(path, "rb") as handle:
            data = handle.read()
        if data:
            logger.info("Podcast cache hit (disk): %s", path)
        return data or None
    except Exception as e:
        logger.warning("Podcast cache disk get failed (%s): %s", path, e)
        return None


def _write_disk(message_id: str, lang: str, audio_bytes: bytes) -> None:
    path = _disk_path(message_id, lang)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(audio_bytes)
        logger.info("Podcast cache stored (disk): %s", path)
    except Exception as e:
        logger.warning("Podcast cache disk put failed (%s): %s", path, e)


def _gcs_client():
    from google.cloud import storage
    from utils.env_json import parse_json_from_env
    from google.oauth2 import service_account

    gcp_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
    if gcp_key:
        gcp_key = gcp_key.strip()
        credentials_info = parse_json_from_env(gcp_key)
        if credentials_info:
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            return storage.Client(credentials=credentials)
        if os.path.isfile(gcp_key):
            credentials = service_account.Credentials.from_service_account_file(gcp_key)
            return storage.Client(credentials=credentials)
    return storage.Client()


def _read_gcs(message_id: str, lang: str, version: Optional[str] = None) -> Optional[bytes]:
    bucket_name = os.getenv(PODCAST_CACHE_BUCKET_ENV)
    if not bucket_name or not bucket_name.strip():
        return None
    object_name = _object_name(message_id, lang, version)
    try:
        bucket = _gcs_client().bucket(bucket_name.strip())
        blob = bucket.blob(object_name)
        if not blob.exists():
            return None
        data = blob.download_as_bytes()
        logger.info("Podcast cache hit (GCS): %s", object_name)
        return data
    except Exception as e:
        logger.warning("Podcast cache get failed (%s): %s", object_name, e)
        return None


def get_cached_audio(message_id: str, lang: str) -> Optional[bytes]:
    """Return cached podcast MP3 bytes if present (memory, disk, GCS), else None."""
    versions = (PODCAST_AUDIO_VERSION, *_PREVIOUS_AUDIO_VERSIONS)
    for version in versions:
        key = _cache_key(message_id, lang, version)
        cached = _MEMORY_CACHE.get(key)
        if cached:
            logger.info("Podcast cache hit (memory): %s_%s_%s", key[0], key[1], version)
            return cached
        cached = _read_disk(message_id, lang, version)
        if cached:
            _remember(message_id, lang, cached, version)
            return cached
        cached = _read_gcs(message_id, lang, version)
        if cached:
            _remember(message_id, lang, cached, version)
            return cached
    return None


def put_cached_audio(message_id: str, lang: str, audio_bytes: bytes) -> None:
    """Store podcast MP3 in memory, on disk, and in GCS when a bucket is configured."""
    _remember(message_id, lang, audio_bytes)
    logger.info("Podcast cache stored (memory): %s_%s", str(message_id).strip(), (lang or "en"))
    _write_disk(message_id, lang, audio_bytes)

    bucket_name = os.getenv(PODCAST_CACHE_BUCKET_ENV)
    if not bucket_name or not bucket_name.strip():
        return
    object_name = _object_name(message_id, lang)
    try:
        bucket = _gcs_client().bucket(bucket_name.strip())
        blob = bucket.blob(object_name)
        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
        logger.info("Podcast cache stored (GCS): %s", object_name)
    except Exception as e:
        logger.warning("Podcast cache put failed (%s): %s", object_name, e)
