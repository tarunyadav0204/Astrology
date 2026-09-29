import base64

import pytest

from partner_profile.image_provider import (
    GooglePartnerPortraitProvider,
    _decode_data_uri,
    _extract_image,
    partner_portrait_provider_configured,
)


def test_provider_accepts_feature_key_or_shared_gemini_key(monkeypatch):
    monkeypatch.delenv("PARTNER_PORTRAIT_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert partner_portrait_provider_configured() is False

    monkeypatch.setenv("GEMINI_API_KEY", "shared-key")
    assert partner_portrait_provider_configured() is True

    monkeypatch.setenv("PARTNER_PORTRAIT_GEMINI_API_KEY", "feature-key")
    provider = GooglePartnerPortraitProvider()
    assert provider.api_key == "feature-key"
    assert provider.metadata["provider"] == "google_gemini"


def test_extracts_google_inline_image():
    content = b"generated-image"
    result = _extract_image(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "done"},
                            {
                                "inlineData": {
                                    "mimeType": "image/jpeg",
                                    "data": base64.b64encode(content).decode("ascii"),
                                }
                            },
                        ]
                    }
                }
            ]
        }
    )

    assert result.content == content
    assert result.content_type == "image/jpeg"


def test_google_block_is_a_visible_failure():
    with pytest.raises(RuntimeError, match="SAFETY"):
        _extract_image({"promptFeedback": {"blockReason": "SAFETY"}})


def test_data_uri_round_trip_and_invalid_data():
    content = b"portrait"
    uri = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
    assert _decode_data_uri(uri) == (content, "image/png")

    with pytest.raises(RuntimeError, match="valid image"):
        _decode_data_uri("data:image/png;base64,not-base64")
