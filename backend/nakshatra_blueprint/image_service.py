"""Private image generation and storage for illustrated Nakshatra Blueprints."""

from __future__ import annotations

import base64
import os
from datetime import timedelta
from pathlib import Path
from typing import Any

import httpx


def _api_key() -> str:
    return (os.getenv("NAKSHATRA_BLUEPRINT_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()


def image_provider_configured() -> bool:
    return bool(_api_key())


class NakshatraBlueprintImageProvider:
    """Creates symbolic chart art only; no likeness or birth data is sent."""

    def __init__(self) -> None:
        self.api_key = _api_key()
        if not self.api_key:
            raise RuntimeError("Nakshatra Blueprint image provider is not configured")
        self.model = os.getenv("NAKSHATRA_BLUEPRINT_IMAGE_MODEL", "gpt-image-2").strip()
        self.image_size = os.getenv("NAKSHATRA_BLUEPRINT_IMAGE_SIZE", "1024x1024").strip()
        # Four editorial illustrations are generated per Blueprint, so use the
        # lowest cost/latency tier unless operations explicitly overrides it.
        self.quality = os.getenv("NAKSHATRA_BLUEPRINT_IMAGE_QUALITY", "low").strip().lower()

    @property
    def metadata(self) -> dict[str, str]:
        return {"provider": "openai", "model": self.model, "image_size": self.image_size, "quality": self.quality}

    async def generate(self, prompt: str) -> tuple[bytes, str]:
        request = {"model": self.model, "prompt": prompt, "size": self.image_size, "quality": self.quality, "n": 1, "output_format": "png"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(240.0), follow_redirects=True) as client:
            response = await client.post("https://api.openai.com/v1/images/generations", headers={"Authorization": f"Bearer {self.api_key}"}, json=request)
        if response.is_error:
            try:
                detail = ((response.json().get("error") or {}).get("message") or "").strip()
            except (AttributeError, ValueError):
                detail = ""
            raise RuntimeError(f"Nakshatra Blueprint image generation failed: {detail or f'HTTP {response.status_code}'}")
        for item in response.json().get("data") or []:
            encoded = (item or {}).get("b64_json")
            if encoded:
                try:
                    return base64.b64decode(encoded, validate=True), "image/png"
                except (ValueError, TypeError) as exc:
                    raise RuntimeError("Nakshatra Blueprint image provider returned invalid image data") from exc
        raise RuntimeError("Nakshatra Blueprint image provider returned no image")


class NakshatraBlueprintStorage:
    """Durable private storage; only short-lived display URLs leave the API."""

    def __init__(self) -> None:
        self.bucket_name = (os.getenv("NAKSHATRA_BLUEPRINT_GCS_BUCKET") or os.getenv("PARTNER_PORTRAIT_GCS_BUCKET") or "").strip()
        self.local_root = Path(os.getenv("NAKSHATRA_BLUEPRINT_LOCAL_DIR", "storage/nakshatra_blueprints"))
        if (os.getenv("ENVIRONMENT") or "development").strip().lower() in {"production", "prod"} and not self.bucket_name:
            raise RuntimeError("NAKSHATRA_BLUEPRINT_GCS_BUCKET is required in production")

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

    def save(self, *, user_id: int, blueprint_id: str, kind: str, content: bytes, content_type: str) -> str:
        object_name = f"nakshatra-blueprints/{user_id}/{blueprint_id}/{kind}.png"
        if self.bucket_name:
            blob = self._gcs_client().bucket(self.bucket_name).blob(object_name)
            blob.upload_from_string(content, content_type=content_type)
            return f"gs://{self.bucket_name}/{object_name}"
        path = self.local_root / str(user_id) / blueprint_id / f"{kind}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return f"file://{path.resolve()}"

    def display_uri(self, stored_uri: str) -> str:
        if stored_uri.startswith("gs://"):
            bucket_name, object_name = stored_uri[5:].split("/", 1)
            return self._gcs_client().bucket(bucket_name).blob(object_name).generate_signed_url(expiration=timedelta(hours=1), method="GET", version="v4")
        path = Path(stored_uri.removeprefix("file://"))
        return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
