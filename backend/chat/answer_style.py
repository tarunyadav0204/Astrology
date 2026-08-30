"""Shared public-chat answer-style normalization.

Only an explicit ``technical`` selection opts into the legacy detailed
presentation. Missing, blank and legacy ``detailed`` values use Simple so old
clients remain compatible with the new default.
"""

from __future__ import annotations


def normalize_chat_answer_style(value: object) -> str:
    return "technical" if str(value or "").strip().lower() == "technical" else "simple"

