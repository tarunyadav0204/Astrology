"""Gemma HTTP client: JSON sanitization (Gemma-only; Gemini path untouched)."""

import json
from datetime import date, datetime, timezone

import pytest

from ai.gemma_chat_client import gemma_sanitize_json_value, _normalize_gemma_url


def test_gemma_sanitize_datetime_nested():
    dt = datetime(2024, 6, 1, 12, 30, tzinfo=timezone.utc)
    d = date(2024, 1, 15)
    payload = {
        "chat_prompt": "x",
        "astrological_context": {"as_of": dt, "day": d, "nested": [{"t": dt}]},
    }
    out = gemma_sanitize_json_value(payload)
    json.dumps(out, allow_nan=False)
    assert out["astrological_context"]["as_of"] == dt.isoformat()
    assert out["astrological_context"]["day"] == "2024-01-15"
    assert out["astrological_context"]["nested"][0]["t"] == dt.isoformat()


def test_gemma_sanitize_decimal_and_set():
    from decimal import Decimal

    payload = {"x": Decimal("1.25"), "s": {1, 2, 3}}
    out = gemma_sanitize_json_value(payload)
    json.dumps(out, allow_nan=False)
    assert out["x"] == "1.25"
    assert sorted(out["s"]) == [1, 2, 3]


def test_normalize_gemma_url_removes_spaces():
    assert _normalize_gemma_url("  http://8.231.104.209 :8000/foo  ") == "http://8.231.104.209:8000/foo"
