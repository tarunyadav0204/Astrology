"""
Public GCS uploads for chat summary images (locational maps, etc.).

Mirrors blog chart upload: object is made public and an https URL is returned
for storage in chat_messages.images / summary_image.
"""

from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

_SAFE = re.compile(r"[^a-zA-Z0-9._-]+")
_client = None


def _get_storage_client():
    global _client
    if _client is not None:
        return _client
    from google.cloud import storage
    from google.oauth2 import service_account

    from utils.env_json import parse_json_from_env

    gcp_key = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
    if gcp_key:
        gcp_key = gcp_key.strip()
        credentials_info = parse_json_from_env(gcp_key)
        if credentials_info:
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            _client = storage.Client(credentials=credentials)
        elif os.path.isfile(gcp_key):
            credentials = service_account.Credentials.from_service_account_file(gcp_key)
            _client = storage.Client(credentials=credentials)
        else:
            raise ValueError(
                "GOOGLE_SERVICE_ACCOUNT_KEY is set but could not be parsed as JSON "
                "and is not a valid file path"
            )
    else:
        _client = storage.Client()
    return _client


def chat_summary_image_bucket_name() -> str:
    return (
        (os.getenv("CHAT_SUMMARY_IMAGE_GCS_BUCKET") or "").strip()
        or (os.getenv("CHAT_IMAGE_GCS_BUCKET") or "").strip()
        # Same public bucket used for generated blog charts.
        or "astroroshni-blog-charts"
    )


def upload_chat_summary_png(
    content: bytes,
    *,
    filename_stem: str = "summary",
    folder: str = "chat-summary",
) -> Optional[str]:
    """
    Upload PNG bytes to GCS, make public, return https URL.

    Returns None if upload is unavailable or fails.
    """
    if not content:
        return None
    bucket_name = chat_summary_image_bucket_name()
    if not bucket_name:
        logger.warning("chat_summary_image_upload_skipped missing_bucket")
        return None

    safe_stem = _SAFE.sub("_", (filename_stem or "summary").strip())[:80] or "summary"
    date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
    unique = uuid.uuid4().hex[:12]
    object_name = f"{folder.strip('/')}/{date_path}/{safe_stem}-{unique}.png"

    try:
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)
        blob.upload_from_string(content, content_type="image/png")
        try:
            blob.make_public()
        except Exception as exc:
            # Uniform bucket-level access may disallow ACL make_public; URL may still work
            # if the bucket is publicly readable via IAM.
            logger.warning("chat_summary_image_make_public_failed object=%s err=%s", object_name, exc)
        public_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
        logger.info(
            "chat_summary_image_uploaded url=%s bytes=%s",
            public_url,
            len(content),
        )
        return public_url
    except Exception:
        logger.exception("chat_summary_image_upload_failed bucket=%s", bucket_name)
        return None
