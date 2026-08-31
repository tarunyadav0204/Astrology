from __future__ import annotations

import asyncio
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import user_settings
from user_settings import AppThemePreference, normalize_app_theme_id


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("refinedEarth", "refinedEarth"),
        ("heritage", "heritage"),
        ("dark", "midnight"),
        ("light", "heritage"),
        ("yellow", None),
        ("", None),
        (None, None),
    ],
)
def test_normalize_app_theme_id(value, expected):
    assert normalize_app_theme_id(value) == expected


def test_unknown_theme_is_rejected():
    preference = AppThemePreference(theme_id="not-a-theme")
    with pytest.raises(HTTPException) as raised:
        preference.normalized_theme_id()
    assert raised.value.status_code == 422


def test_missing_account_theme_returns_null(monkeypatch):
    monkeypatch.setattr(user_settings, "get_conn", lambda: nullcontext(object()))
    monkeypatch.setattr(user_settings, "_read_setting", lambda *_: None)
    result = asyncio.run(
        user_settings.get_app_theme(
            current_user=SimpleNamespace(userid=42),
        )
    )
    assert result == {
        "theme_id": None,
        "default_theme_id": "heritage",
    }


def test_saved_account_theme_is_returned(monkeypatch):
    monkeypatch.setattr(user_settings, "get_conn", lambda: nullcontext(object()))
    monkeypatch.setattr(user_settings, "_read_setting", lambda *_: "refinedEarth")
    result = asyncio.run(
        user_settings.get_app_theme(
            current_user=SimpleNamespace(userid=42),
        )
    )
    assert result["theme_id"] == "refinedEarth"
    assert result["default_theme_id"] == "heritage"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('"refinedEarth"', "refinedEarth"),
        ("refinedEarth", "refinedEarth"),
        ('"dark"', "midnight"),
        (None, None),
        ("", None),
        ('"yellow"', None),
    ],
)
def test_parse_stored_app_theme(value, expected):
    assert user_settings.parse_stored_app_theme(value) == expected


def test_app_theme_label():
    assert user_settings.app_theme_label("refinedEarth") == "Refined Earth"
    assert user_settings.app_theme_label(None) is None
    assert user_settings.app_theme_label("unknownTheme") == "unknownTheme"
