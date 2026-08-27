import pytest

from credits.web_continue import (
    ensure_continue_link_environment_is_safe,
    normalize_continue_token,
)


def test_normalize_continue_token_strips_whatsapp_trailing_period():
    token = "apaJY04cwmeYnjVRag_n85Cgl1i5oQFS"

    assert normalize_continue_token(f"{token}.") == token


def test_normalize_continue_token_keeps_urlsafe_token_unchanged():
    token = "apaJY04cwmeYnjVRag_n85Cgl1i5oQFS"

    assert normalize_continue_token(token) == token


def test_normalize_continue_token_does_not_hide_arbitrary_suffix():
    altered = "apaJY04cwmeYnjVRag_n85Cgl1i5oQFS.other"

    assert normalize_continue_token(altered) == altered


def test_development_cannot_mint_production_bound_link(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("ALLOW_EXTERNAL_WEB_CONTINUE_LINKS", raising=False)
    monkeypatch.setenv("PUBLIC_WEB_BASE_URL", "https://astroroshni.com")

    with pytest.raises(RuntimeError, match="token created on localhost"):
        ensure_continue_link_environment_is_safe()


def test_production_can_mint_production_bound_link(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("PUBLIC_WEB_BASE_URL", "https://astroroshni.com")

    ensure_continue_link_environment_is_safe()
