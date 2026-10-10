import asyncio
import base64

import httpx
import pytest

from partner_profile.image_provider import (
    OpenAIPartnerPortraitProvider,
    _decode_data_uri,
    _extract_image,
    partner_portrait_provider_configured,
)


def test_provider_accepts_feature_key_or_shared_chat_key(monkeypatch):
    monkeypatch.delenv("PARTNER_PORTRAIT_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "google-key")
    assert partner_portrait_provider_configured() is False
    monkeypatch.setenv("OPENAI_API_KEY", "shared-key")
    assert partner_portrait_provider_configured() is True
    assert OpenAIPartnerPortraitProvider().api_key == "shared-key"
    monkeypatch.setenv("PARTNER_PORTRAIT_OPENAI_API_KEY", "feature-key")
    provider = OpenAIPartnerPortraitProvider()
    assert provider.api_key == "feature-key"
    assert provider.metadata["provider"] == "openai"


def test_extracts_openai_image():
    content = b"generated-image"
    result = _extract_image({"data": [{"b64_json": base64.b64encode(content).decode()}]})
    assert result.content == content
    assert result.content_type == "image/png"


@pytest.mark.parametrize("payload", [{}, {"data": [{"b64_json": ""}]}, {"data": [{"b64_json": "invalid!"}]}])
def test_missing_or_invalid_image_is_a_visible_failure(payload):
    with pytest.raises(RuntimeError, match="OpenAI returned"):
        _extract_image(payload)


def test_data_uri_round_trip_and_invalid_data():
    content = b"portrait"
    uri = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
    assert _decode_data_uri(uri) == (content, "image/png")
    with pytest.raises(RuntimeError, match="valid image"):
        _decode_data_uri("data:image/png;base64,not-base64")


def test_generation_and_identity_reference_requests(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "chat-key")
    monkeypatch.delenv("PARTNER_PORTRAIT_OPENAI_API_KEY", raising=False)
    for name in ("PARTNER_PORTRAIT_IMAGE_MODEL", "PARTNER_PORTRAIT_IMAGE_SIZE", "PARTNER_PORTRAIT_IMAGE_QUALITY"):
        monkeypatch.delenv(name, raising=False)
    calls = []

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(b"image").decode()}]})

    monkeypatch.setattr("partner_profile.image_provider.httpx.AsyncClient", FakeClient)
    provider = OpenAIPartnerPortraitProvider()
    asyncio.run(provider.generate_portrait("face prompt", 1))
    uri = "data:image/png;base64," + base64.b64encode(b"same-face").decode()
    asyncio.run(provider.generate_full_body("body prompt", uri, 1))
    url, request = calls[0]
    assert url.endswith("/images/generations")
    assert request["headers"]["Authorization"] == "Bearer chat-key"
    assert request["json"] == {"model": "gpt-image-2", "prompt": "face prompt", "size": "1024x1536", "quality": "medium", "n": 1, "output_format": "png"}
    url, request = calls[1]
    assert url.endswith("/images/edits")
    assert request["files"]["image"] == ("portrait.png", b"same-face", "image/png")
    assert "identity reference" in request["data"]["prompt"]
    assert request["data"]["quality"] == "medium"


def test_openai_api_error_is_visible(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "chat-key")

    class FakeClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def post(self, *args, **kwargs):
            return httpx.Response(403, json={"error": {"message": "Model access denied"}})

    monkeypatch.setattr("partner_profile.image_provider.httpx.AsyncClient", FakeClient)
    with pytest.raises(RuntimeError, match="Model access denied"):
        asyncio.run(OpenAIPartnerPortraitProvider().generate_portrait("prompt", 1))
