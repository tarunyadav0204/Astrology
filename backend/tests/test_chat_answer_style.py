from __future__ import annotations

import asyncio
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from chat.answer_style import normalize_chat_answer_style
import user_settings
from user_settings import ChatAnswerStylePreference


@pytest.mark.parametrize("value", [None, "", "simple", "SIMPLE", "detailed", "concise"])
def test_public_chat_defaults_every_nontechnical_value_to_simple(value):
    assert normalize_chat_answer_style(value) == "simple"


def test_public_chat_requires_explicit_technical_selection():
    assert normalize_chat_answer_style(" Technical ") == "technical"


def test_account_preference_accepts_only_public_styles():
    assert ChatAnswerStylePreference(answer_style="simple").answer_style == "simple"
    assert ChatAnswerStylePreference(answer_style="technical").answer_style == "technical"
    with pytest.raises(ValidationError):
        ChatAnswerStylePreference(answer_style="detailed")


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ('"simple"', "simple"),
        ('"technical"', "technical"),
        (" SIMPLE ", "simple"),
        ("detailed", None),
        (None, None),
    ],
)
def test_parse_stored_answer_style_for_admin_and_account_reads(stored, expected):
    assert user_settings.parse_stored_chat_answer_style(stored) == expected


def test_missing_account_preference_requests_one_time_selection(monkeypatch):
    monkeypatch.setattr(user_settings, "get_conn", lambda: nullcontext(object()))
    monkeypatch.setattr(user_settings, "_read_setting", lambda *_: None)
    result = asyncio.run(
        user_settings.get_chat_answer_style(
            current_user=SimpleNamespace(userid=42),
        )
    )
    assert result == {
        "answer_style": None,
        "selection_required": True,
        "default_answer_style": "simple",
    }


def test_saved_account_preference_skips_future_selection(monkeypatch):
    monkeypatch.setattr(user_settings, "get_conn", lambda: nullcontext(object()))
    monkeypatch.setattr(user_settings, "_read_setting", lambda *_: "technical")
    result = asyncio.run(
        user_settings.get_chat_answer_style(
            current_user=SimpleNamespace(userid=42),
        )
    )
    assert result["answer_style"] == "technical"
    assert result["selection_required"] is False
