"""
Podcast audio cache on Google Cloud Storage.
Store generated podcast MP3 by message_id + language so replay and share don't regenerate (no extra Gemini/TTS cost).

Setup: Create a GCS bucket, set env PODCAST_CACHE_BUCKET=<bucket-name>. Use the same
GOOGLE_SERVICE_ACCOUNT_KEY as elsewhere; the key must have storage.objects.create and get.
"""

import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Env: bucket name for podcast cache. If unset, caching is disabled.
PODCAST_CACHE_BUCKET_ENV = "PODCAST_CACHE_BUCKET"

# Sanitize for GCS object name: alphanumeric, dash, underscore only
def _safe_key_part(s: str, max_len: int = 200) -> str:
    if not s:
        return "unknown"
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", s)
    return safe[:max_len] if len(safe) > max_len else safe


def get_cached_audio(message_id: str, lang: str) -> Optional[bytes]:
    """Return cached podcast MP3 bytes if present, else None."""
    bucket_name = os.getenv(PODCAST_CACHE_BUCKET_ENV)
    if not bucket_name or not bucket_name.strip():
        return None
    message_id = _safe_key_part(str(message_id))
    lang = _safe_key_part(str(lang), 10)
    object_name = f"podcast/{message_id}_{lang}.mp3"
    try:
        from google.cloud import storage
        from utils.env_json import parse_json_from_env
        from google.oauth2 import service_account

        gcp_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
        if gcp_key:
            gcp_key = gcp_key.strip()
            credentials_info = parse_json_from_env(gcp_key)
            if credentials_info:
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                client = storage.Client(credentials=credentials)
            elif os.path.isfile(gcp_key):
                credentials = service_account.Credentials.from_service_account_file(gcp_key)
                client = storage.Client(credentials=credentials)
            else:
                client = storage.Client()
        else:
            client = storage.Client()

        bucket = client.bucket(bucket_name.strip())
        blob = bucket.blob(object_name)
        if not blob.exists():
            return None
        data = blob.download_as_bytes()
        logger.info("Podcast cache hit: %s", object_name)
        return data
    except Exception as e:
        logger.warning("Podcast cache get failed (%s): %s", object_name, e)
        return None


def put_cached_audio(message_id: str, lang: str, audio_bytes: bytes) -> None:
    """Store podcast MP3 in GCS. No-op if bucket not configured or upload fails."""
    bucket_name = os.getenv(PODCAST_CACHE_BUCKET_ENV)
    if not bucket_name or not bucket_name.strip():
        return
    message_id = _safe_key_part(str(message_id))
    lang = _safe_key_part(str(lang), 10)
    object_name = f"podcast/{message_id}_{lang}.mp3"
    try:
        from google.cloud import storage
        from utils.env_json import parse_json_from_env
        from google.oauth2 import service_account

        gcp_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
        if gcp_key:
            gcp_key = gcp_key.strip()
            credentials_info = parse_json_from_env(gcp_key)
            if credentials_info:
                credentials = service_account.Credentials.from_service_account_info(credentials_info)
                client = storage.Client(credentials=credentials)
            elif os.path.isfile(gcp_key):
                credentials = service_account.Credentials.from_service_account_file(gcp_key)
                client = storage.Client(credentials=credentials)
            else:
                client = storage.Client()
        else:
            client = storage.Client()

        bucket = client.bucket(bucket_name.strip())
        blob = bucket.blob(object_name)
        blob.upload_from_string(audio_bytes, content_type="audio/mpeg")
        logger.info("Podcast cache stored: %s", object_name)
    except Exception as e:
        logger.warning("Podcast cache put failed (%s): %s", object_name, e)
