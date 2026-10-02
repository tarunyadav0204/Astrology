"""Private durable storage for generated Partner Portrait assets."""

from __future__ import annotations

import base64
import mimetypes
import os
import shutil
from datetime import timedelta
from pathlib import Path


class PartnerPortraitStorage:
    def __init__(self) -> None:
        self.bucket_name = os.getenv("PARTNER_PORTRAIT_GCS_BUCKET", "").strip()
        self.local_root = Path(os.getenv("PARTNER_PORTRAIT_LOCAL_DIR", "storage/partner_portraits"))
        environment = (os.getenv("ENVIRONMENT") or "development").strip().lower()
        if environment in {"production", "prod"} and not self.bucket_name:
            raise RuntimeError("PARTNER_PORTRAIT_GCS_BUCKET is required in production")

    def _gcs_client(self):
        from google.cloud import storage
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        raw = (os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY") or "").strip()
        if raw:
            info = parse_json_from_env(raw)
            if info:
                return storage.Client(credentials=service_account.Credentials.from_service_account_info(info))
            if os.path.isfile(raw):
                return storage.Client(credentials=service_account.Credentials.from_service_account_file(raw))
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY is neither valid JSON nor a valid file path")
        return storage.Client()

    def save(self, *, user_id: int, job_id: str, kind: str, content: bytes, content_type: str) -> str:
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}.get(content_type, ".webp")
        object_name = f"partner-portraits/{user_id}/{job_id}/{kind}{suffix}"
        if self.bucket_name:
            blob = self._gcs_client().bucket(self.bucket_name).blob(object_name)
            blob.upload_from_string(content, content_type=content_type)
            return f"gs://{self.bucket_name}/{object_name}"
        path = self.local_root / str(user_id) / job_id / f"{kind}{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return f"file://{path.resolve()}"

    def provider_input_uri(self, stored_uri: str) -> str:
        if stored_uri.startswith("gs://"):
            bucket_name, object_name = stored_uri[5:].split("/", 1)
            blob = self._gcs_client().bucket(bucket_name).blob(object_name)
            return blob.generate_signed_url(expiration=timedelta(minutes=20), method="GET", version="v4")
        path = Path(stored_uri.removeprefix("file://"))
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower(), "image/webp")
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

    def display_uri(self, stored_uri: str) -> str:
        if stored_uri.startswith("gs://"):
            bucket_name, object_name = stored_uri[5:].split("/", 1)
            blob = self._gcs_client().bucket(bucket_name).blob(object_name)
            return blob.generate_signed_url(expiration=timedelta(hours=1), method="GET", version="v4")
        return self.provider_input_uri(stored_uri)

    def read(self, stored_uri: str) -> tuple[bytes, str, str]:
        """Read a private portrait for an authenticated application response."""
        if stored_uri.startswith("gs://"):
            bucket_name, object_name = stored_uri[5:].split("/", 1)
            blob = self._gcs_client().bucket(bucket_name).blob(object_name)
            content = blob.download_as_bytes()
            content_type = blob.content_type or mimetypes.guess_type(object_name)[0] or "application/octet-stream"
            return content, content_type, Path(object_name).name
        path = Path(stored_uri.removeprefix("file://"))
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return path.read_bytes(), content_type, path.name

    def delete(self, stored_uri: str) -> None:
        """Delete one generated asset from private storage.

        Missing objects are treated as already deleted so chart/account cleanup is
        idempotent.
        """
        if not stored_uri:
            return
        if stored_uri.startswith("gs://"):
            bucket_name, object_name = stored_uri[5:].split("/", 1)
            blob = self._gcs_client().bucket(bucket_name).blob(object_name)
            blob.delete(if_generation_match=None)
            return
        if stored_uri.startswith("file://"):
            path = Path(stored_uri.removeprefix("file://"))
            path.unlink(missing_ok=True)
            # A job owns its directory, so remove it once both generated files are gone.
            job_dir = path.parent
            if job_dir.exists() and not any(job_dir.iterdir()):
                shutil.rmtree(job_dir, ignore_errors=True)
