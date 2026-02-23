"""
Guard to detect and refuse questions related to death, time of death,
celestial abode, or transiting to non-physical. Used to avoid AI answering
such questions regardless of model behavior.
"""

import re
from typing import Tuple

# Single consistent refusal message used everywhere (API and system prompt)
REFUSAL_MESSAGE = (
    "I'm not able to answer questions about death or the timing of passing. "
    "I'm here for astrological insights on life and choices."
)

# Phrases and keywords (case-insensitive) that indicate a death-related query.
# Include English and common Sanskrit/Hindi terms used in astrology apps.
_DEATH_PATTERNS = [
    r"\bdeath\b",
    r"\bdie\b",
    r"\bdying\b",
    r"\bwhen\s+(will|do)\s+i\s+die",
    r"\btime\s+of\s+death\b",
    r"\bdate\s+of\s+death\b",
    r"\bcelestial\s+abode\b",
    r"\btransit(?:ing)?\s+to\s+non[-\s]?physical\b",
    r"\bnon[-\s]?physical\s+transit\b",
    r"\bleav(e|ing)\s+(the\s+)?body\b",
    r"\bleav(e|ing)\s+(this\s+)?world\b",
    r"\bwhen\s+will\s+i\s+go\s+(to\s+)?(heaven|abode|celestial)\b",
    r"\bend\s+of\s+(my\s+)?life\b",
    r"\blifespan\s+end\b",
    r"\bmrityu\b",
    r"\bmaran\b",
    r"\bantim\s+samay\b",
    r"\bantya\s+samay\b",
    r"\bwhen\s+will\s+i\s+pass\s+(away)?\b",
    r"\bpass\s+away\b",
    r"\bwhen\s+will\s+.*\s+die\b",
    r"\bhow\s+long\s+will\s+i\s+live\b",
    r"\bhow\s+many\s+years\s+(left|to\s+live)\b",
    r"\bdeceased\s+.*\s+chart\b",  # "when will I become deceased" style
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _DEATH_PATTERNS]


def is_death_related(question: str) -> bool:
    """
    Returns True if the question appears to be about death, time of death,
    celestial abode, or transiting to non-physical. Uses keyword/phrase
    matching only (no LLM call).
    """
    if not question or not isinstance(question, str):
        return False
    text = question.strip()
    if not text:
        return False
    return any(rx.search(text) for rx in _COMPILED)


def check_and_refusal(question: str) -> Tuple[bool, str]:
    """
    Returns (is_death_related, refusal_message).
    If is_death_related is True, refusal_message is the standard refusal; otherwise "".
    """
    if is_death_related(question):
        return True, REFUSAL_MESSAGE
    return False, ""
