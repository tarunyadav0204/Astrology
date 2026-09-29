"""Google Gemini image generation for Partner Portrait.

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
    # The feature-specific key permits independent rotation in production. The
    # existing Gemini key remains a documented credential alias for deployments
    # that use one Google AI project.
    return (os.getenv("PARTNER_PORTRAIT_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()


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
    candidates = payload.get("candidates") or []
    for candidate in candidates:
        parts = ((candidate or {}).get("content") or {}).get("parts") or []
        for part in parts:
            inline_data = (part or {}).get("inlineData") or (part or {}).get("inline_data")
            if not inline_data or not inline_data.get("data"):
                continue
            try:
                content = base64.b64decode(inline_data["data"], validate=True)
            except (ValueError, TypeError) as exc:
                raise RuntimeError("Google returned invalid image data") from exc
            return GeneratedImage(content=content, content_type=inline_data.get("mimeType") or "image/png")

    block_reason = ((payload.get("promptFeedback") or {}).get("blockReason") or "").strip()
    if block_reason:
        raise RuntimeError(f"Google did not generate the image: {block_reason}")
    raise RuntimeError("Google returned no image")


class GooglePartnerPortraitProvider:
    """Generate a portrait and an identity-consistent full-body companion image."""

    provider_name = "google_gemini"

    def __init__(self) -> None:
        self.api_key = _api_key()
        if not self.api_key:
            raise RuntimeError("Partner Portrait image provider is not configured")
        self.model = os.getenv("PARTNER_PORTRAIT_IMAGE_MODEL", "gemini-3.1-flash-image").strip()
        self.image_size = os.getenv("PARTNER_PORTRAIT_IMAGE_SIZE", "1K").strip().upper()
        self.base_url = os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta").rstrip("/")

    @property
    def metadata(self) -> dict[str, str]:
        return {"provider": self.provider_name, "model": self.model, "image_size": self.image_size}

    async def _generate(self, prompt: str, aspect_ratio: str, reference: tuple[bytes, str] | None = None) -> GeneratedImage:
        parts: list[dict[str, Any]] = [{"text": prompt}]
        if reference:
            content, mime_type = reference
            parts.append(
                {
                    "inlineData": {
                        "mimeType": mime_type,
                        "data": base64.b64encode(content).decode("ascii"),
                    }
                }
            )
        request = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {"aspectRatio": aspect_ratio, "imageSize": self.image_size},
            },
        }
        url = f"{self.base_url}/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=httpx.Timeout(240.0), follow_redirects=True) as client:
            response = await client.post(url, headers={"x-goog-api-key": self.api_key}, json=request)
        if response.is_error:
            try:
                message = ((response.json().get("error") or {}).get("message") or "").strip()
            except (ValueError, AttributeError):
                message = ""
            detail = message or f"HTTP {response.status_code}"
            raise RuntimeError(f"Google image generation failed: {detail}")
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
        # Gemini image generation currently does not expose a seed. Identity is
        # established by passing this generated image into the second request.
        del seed
        return await self._generate(prompt, "4:5")

    async def generate_full_body(self, prompt: str, portrait_uri: str, seed: int) -> GeneratedImage:
        del seed
        reference = await self._load_reference(portrait_uri)
        identity_prompt = (
            f"{prompt}\n\nUse the supplied portrait as the identity reference. Preserve the same adult person's "
            "facial structure, skin tone, hair, apparent age and overall identity exactly."
        )
        return await self._generate(identity_prompt, "3:4", reference)
