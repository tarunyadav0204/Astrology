"""
Map internal / vendor exception text to short user-facing copy for mobile and web.
Never expose stack traces, gRPC details, or raw Gemini quota strings in persisted job errors.
"""
from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT = (
    "We couldn't finish this analysis right now. Please try again in a few minutes. "
    "If you were charged, use Load saved or contact support."
)
_BUSY = (
    "Our prediction service is temporarily busy. Please try again in a few minutes."
)
_UNAVAILABLE = (
    "This feature is temporarily unavailable. Please try again later."
)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, BaseException):
        return f"{type(value).__name__}: {value}"
    return str(value)


def user_facing_message_from_any(value: Any) -> str:
    """
    Turn an exception or technical string into safe copy for API `error` / DB `error_message`.
    Logs the original at WARNING once (truncated) for ops — full detail should use logger.exception at call site.
    """
    text = _as_text(value).strip()
    if not text:
        return _DEFAULT

    lower = text.lower()

    # Log truncated original for support (call sites may also logger.exception).
    if len(text) > 400 or any(
        x in lower
        for x in (
            "resourceexhausted",
            "429",
            "quota",
            "rate limit",
            "generativelanguage",
            "cachedcontent",
            "grpc",
            "violations {",
            "traceback",
            "file \"",
        )
    ):
        logger.warning("user_facing_errors: suppressed technical message (len=%s): %s", len(text), text[:500])

    if any(
        x in lower
        for x in (
            "resourceexhausted",
            "429",
            "quota exceeded",
            "rate limit",
            "too many requests",
        )
    ):
        return _BUSY

    if any(
        x in lower
        for x in (
            "cachedcontent",
            "totalcachedcontent",
            "context cache",
            "createcachedcontent",
        )
    ):
        return _UNAVAILABLE

    if any(x in lower for x in ("generativelanguage", "google.api_core", "gemini api", "gemini")):
        return _BUSY

    if "birth chart" in lower and "not found" in lower:
        return "Your birth chart could not be found. Please re-select your chart and try again."

    if "credit deduction failed" in lower:
        return "We could not confirm your credits. Please check your balance and try again."

    # Looks like a stack trace or protobuf dump
    if "\n" in text or re.search(r"\b0x[0-9a-f]{6,}\b", lower):
        return _DEFAULT

    if len(text) > 220:
        return _DEFAULT

    # Short validation-style messages from our own code — still a bit internal; soften
    if any(
        x in lower
        for x in (
            "raw prediction preview",
            "merged monthly",
            "merged quarterly",
            "minimum 20",
            "minimum 6",
            "shard",
            "quarter q",
            "timeline json",
            "invalid timeline",
            "timeline json parse",
            "timeline llm request failed",
            "json parse error",
            "json decode",
        )
    ):
        return _DEFAULT

    return text
