"""
Shared heuristics for user question shape (intent router + chat prompts).
"""

from __future__ import annotations

import re


# Broad life-area cues (Latin + Devanagari fragments). Used to detect one message with many topics.
_TOPIC_GROUP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("marriage_timing", re.compile(
        r"shaadi|shadi|sadi|vivah|married|marriage|विवाह|शादी|kab\s+hui|kab\s+hoi|कब\s+हुई",
        re.I,
    )),
    ("spouse", re.compile(
        r"\bwife\b|\bhusband\b|spouse|partner|patni|pati|पत्नी|पति|दाम्पत्य",
        re.I,
    )),
    ("career", re.compile(
        r"career|job|naukri|business|promotion|karier|profession|करियर|नौकरी|व्यापार",
        re.I,
    )),
    ("wealth", re.compile(
        r"money|wealth|paisa|finance|salary|income|earning|dhan|धन|कमाई|माल",
        re.I,
    )),
    ("children", re.compile(r"child|children|son|daughter|pregnancy|संतान", re.I)),
    ("health", re.compile(r"health|disease|illness|swasthya|स्वास्थ्य|बीमारी", re.I)),
)


def _distinct_topic_hits(text: str) -> int:
    """How many different life-area groups match (substring / script-agnostic)."""
    if not text or not text.strip():
        return 0
    n = 0
    for _name, pat in _TOPIC_GROUP_PATTERNS:
        if pat.search(text):
            n += 1
    return n


def looks_like_many_questions(user_question: str) -> bool:
    """
    Heuristic: user bundled several distinct asks in one message.
    Used by intent router (clarification nudge), route-layer CLARIFY, and logging.

    Hindi/Hinglish often uses full stops between questions instead of \"?\" — we also
    split on danda and count clauses, and use multi-topic keyword groups.
    """
    t = (user_question or "").strip()
    if len(t) < 28:
        return False
    if t.count("?") >= 2:
        return True
    low = t.lower()
    if any(
        p in low
        for p in (
            "another question",
            "few questions",
            "multiple questions",
            "two questions",
            "three questions",
            "four questions",
            "so many questions",
            "ek saath",
            "एक साथ",
        )
    ):
        return True
    if re.search(r"(?m)^\s*\d+[\).]\s+.+\?", t):
        hits = len(re.findall(r"(?m)^\s*\d+[\).]\s+.+\?", t))
        if hits >= 2:
            return True
    if (";" in t or " also " in f" {low} ") and "?" in t and len(t) > 80:
        return True

    # Period / Hindi danda / newlines — multiple sentences, common in Roman Hindi without "?"
    raw_parts = re.split(r"[.?\n।|]+", t)
    parts = [p.strip() for p in raw_parts if p.strip() and len(p.strip()) >= 6]
    if len(parts) >= 3:
        return True
    if len(parts) >= 2 and _distinct_topic_hits(t) >= 2:
        return True

    # Several life areas named in one line (e.g. marriage + career + money)
    if _distinct_topic_hits(t) >= 3:
        return True
    if _distinct_topic_hits(t) >= 2 and len(t) >= 50:
        return True

    return False


