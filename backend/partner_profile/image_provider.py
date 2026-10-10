"""OpenAI GPT image generation for Partner Portrait.

The provider receives only the resolved visual prompt produced by the classical
profile engine. Birth data, chart identifiers and the native's name are never
sent to the image service.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class GeneratedImage:
    content: bytes
    content_type: str = "image/png"


def _api_key() -> str:
    # Reuse the chat credential unless a dedicated image key is configured.
    return (os.getenv("PARTNER_PORTRAIT_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()


def partner_portrait_provider_configured() -> bool:
    return bool(_api_key())

def _decode_data_uri(uri: str) -> tuple[bytes, str] | None:
    if not uri.startswith("data:") or ";base64," not in uri:
        return None
    header, encoded = uri.split(",", 1)
    mime_type = header[5:].split(";", 1)[0] or "image/png"
    try:
        return base64.b64decode(encoded, validate=True), mime_type
    except (ValueError, TypeError) as exc:
        raise RuntimeError("Stored portrait is not a valid image") from exc

def _extract_image(payload: dict[str, Any]) -> GeneratedImage:
    for item in payload.get("data") or []:
        encoded = (item or {}).get("b64_json")
        if not encoded:
            continue
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as exc:
            raise RuntimeError("OpenAI returned invalid image data") from exc
        if content:
            return GeneratedImage(content=content)
    raise RuntimeError("OpenAI returned no image")


class OpenAIPartnerPortraitProvider:
    """Generate a portrait and an identity-consistent full-body companion image."""

    provider_name = "openai"

    def __init__(self) -> None:
        self.api_key = _api_key()
        if not self.api_key:
            raise RuntimeError("Partner Portrait image provider is not configured")
        self.model = os.getenv("PARTNER_PORTRAIT_IMAGE_MODEL", "gpt-image-2").strip()
        self.image_size = os.getenv("PARTNER_PORTRAIT_IMAGE_SIZE", "1024x1536").strip()
        self.quality = os.getenv("PARTNER_PORTRAIT_IMAGE_QUALITY", "medium").strip().lower()
        self.base_url = "https://api.openai.com/v1"

    @property
    def metadata(self) -> dict[str, str]:
        return {"provider": self.provider_name, "model": self.model,
                "image_size": self.image_size, "quality": self.quality}

    async def _generate(self, prompt: str, reference: tuple[bytes, str] | None = None) -> GeneratedImage:
        request = {"model": self.model, "prompt": prompt, "size": self.image_size,
                   "quality": self.quality, "n": 1, "output_format": "png"}
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(240.0), follow_redirects=True) as client:
            if reference:
                content, mime_type = reference
                extension = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime_type, "png")
                response = await client.post(
                    f"{self.base_url}/images/edits", headers=headers,
                    data={key: str(value) for key, value in request.items()},
                    files={"image": (f"portrait.{extension}", content, mime_type)},
                )
            else:
                response = await client.post(
                    f"{self.base_url}/images/generations", headers=headers, json=request,
                )
        if response.is_error:
            try:
                message = ((response.json().get("error") or {}).get("message") or "").strip()
            except (ValueError, AttributeError):
                message = ""
            raise RuntimeError(f"OpenAI image generation failed: {message or f'HTTP {response.status_code}'}")
        return _extract_image(response.json())

    async def _load_reference(self, portrait_uri: str) -> tuple[bytes, str]:
        embedded = _decode_data_uri(portrait_uri)
        if embedded:
            return embedded
        if not portrait_uri.startswith("https://"):
            raise RuntimeError("Stored portrait is not available to the image provider")
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            response = await client.get(portrait_uri)
            response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png").split(";", 1)[0]
        return response.content, content_type

    async def generate_portrait(self, prompt: str, seed: int) -> GeneratedImage:
        # GPT image generation does not expose a seed. Identity is
        # established by passing this generated image into the second request.
        del seed
        return await self._generate(prompt)

    async def generate_full_body(self, prompt: str, portrait_uri: str, seed: int) -> GeneratedImage:
        del seed
        reference = await self._load_reference(portrait_uri)
        identity_prompt = (
            f"{prompt}\n\nUse the supplied portrait as the identity reference. Preserve the same adult person's "
            "facial structure, skin tone, hair, apparent age and overall identity exactly."
        )
        return await self._generate(identity_prompt, reference)
