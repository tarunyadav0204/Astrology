"""
Private GCS storage for admin expense invoice attachments (not public URLs).
Uses GOOGLE_SERVICE_ACCOUNT_KEY (same as blog) and EXPENSE_INVOICE_GCS_BUCKET.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_GS_URI_RE = re.compile(r"^gs://([^/]+)/(.+)$")

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
                "GOOGLE_SERVICE_ACCOUNT_KEY is set but could not be parsed as JSON and is not a valid file path"
            )
    else:
        _client = storage.Client()
    return _client


def expense_invoice_bucket_name() -> str:
    return (os.getenv("EXPENSE_INVOICE_GCS_BUCKET") or "").strip()


def parse_gs_uri(uri: str) -> Optional[Tuple[str, str]]:
    m = _GS_URI_RE.match((uri or "").strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def upload_invoice_bytes(
    content: bytes,
    *,
    object_suffix: str,
    content_type: str,
) -> str:
    """
    Upload to gs://{bucket}/admin-expenses/YYYY/MM/{object_suffix}.
    Object is private (no make_public). Returns gs:// URI stored in DB.
    """
    bucket_name = expense_invoice_bucket_name()
    if not bucket_name:
        raise RuntimeError("EXPENSE_INVOICE_GCS_BUCKET is not set")

    date_path = datetime.now(timezone.utc).strftime("%Y/%m")
    object_name = f"admin-expenses/{date_path}/{object_suffix}"

    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(content, content_type=content_type)
    uri = f"gs://{bucket_name}/{object_name}"
    logger.info("Uploaded expense invoice to %s (%s bytes)", uri, len(content))
    return uri


def download_invoice_bytes(gs_uri: str) -> Tuple[bytes, str]:
    """Return (content, content_type)."""
    parsed = parse_gs_uri(gs_uri)
    if not parsed:
        raise ValueError("Invalid gs:// URI")
    bucket_name, object_name = parsed
    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    if not blob.exists():
        raise FileNotFoundError(gs_uri)
    content_type = (blob.content_type or "application/octet-stream").strip()
    data = blob.download_as_bytes()
    return data, content_type


def delete_invoice_object(gs_uri: str) -> None:
    parsed = parse_gs_uri(gs_uri)
    if not parsed:
        raise ValueError("Invalid gs:// URI")
    bucket_name, object_name = parsed
    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    if blob.exists():
        blob.delete()
    logger.info("Deleted expense invoice %s", gs_uri)
