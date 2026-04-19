"""Parallel chat feature flag (legacy path default)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def test_parallel_chat_disabled_by_default(monkeypatch):
    from ai.parallel_chat.config import parallel_chat_enabled, should_use_parallel_chat

    monkeypatch.delenv("ASTRO_PARALLEL_CHAT", raising=False)
    assert parallel_chat_enabled() is False
    ctx = {"analysis_type": "birth", "intent": {"mode": "birth"}}
    assert should_use_parallel_chat(ctx) is False


def test_parallel_chat_enabled_respects_env(monkeypatch):
    from ai.parallel_chat.config import parallel_chat_enabled, should_use_parallel_chat

    monkeypatch.setenv("ASTRO_PARALLEL_CHAT", "1")
    assert parallel_chat_enabled() is True
    ctx = {"analysis_type": "birth", "intent": {"mode": "birth", "category": "career"}}
    assert should_use_parallel_chat(ctx) is True


def test_parallel_chat_skips_non_birth(monkeypatch):
    from ai.parallel_chat.config import should_use_parallel_chat

    monkeypatch.setenv("ASTRO_PARALLEL_CHAT", "1")
    assert should_use_parallel_chat({"analysis_type": "annual_forecast", "intent": {}}) is False
    assert should_use_parallel_chat({"analysis_type": "birth", "intent": {"mode": "prashna"}}) is False
    assert should_use_parallel_chat({"analysis_type": "synastry", "native": {}, "partner": {}}) is False


def test_parallel_chat_user_allowlist(monkeypatch):
    from ai.parallel_chat.config import should_use_parallel_chat

    monkeypatch.setenv("ASTRO_PARALLEL_CHAT", "1")
    ctx = {"analysis_type": "birth", "intent": {"mode": "birth", "category": "career"}}
    monkeypatch.setenv("ASTRO_PARALLEL_CHAT_USER_IDS", "100, 200")
    assert should_use_parallel_chat(ctx, user_id=100) is True
    assert should_use_parallel_chat(ctx, user_id=200) is True
    assert should_use_parallel_chat(ctx, user_id=3) is False
    assert should_use_parallel_chat(ctx, user_id=None) is False


def test_parallel_chat_allowlist_invalid_ids_means_nobody(monkeypatch):
    from ai.parallel_chat.config import should_use_parallel_chat

    monkeypatch.setenv("ASTRO_PARALLEL_CHAT", "1")
    ctx = {"analysis_type": "birth", "intent": {"mode": "birth"}}
    monkeypatch.setenv("ASTRO_PARALLEL_CHAT_USER_IDS", "not_a_number, also_bad")
    assert should_use_parallel_chat(ctx, user_id=1) is False


def test_looks_like_many_questions_hindi_multi_sentence():
    from ai.question_heuristics import looks_like_many_questions

    msg = (
        "meri saadi kab hui thi. Meri wife kaisi hai. Mera career ke baare mein batao. "
        "Aur paisa kitna hoga."
    )
    assert looks_like_many_questions(msg) is True


def test_looks_like_many_questions_single_when_english():
    from ai.question_heuristics import looks_like_many_questions

    assert looks_like_many_questions("In which year did I get married?") is False
