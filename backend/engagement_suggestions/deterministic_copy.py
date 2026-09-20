from __future__ import annotations

import re
from typing import Dict

LOCALE_ALIASES = {
    "english": "en", "hindi": "hi", "bengali": "bn", "marathi": "mr",
    "tamil": "ta", "telugu": "te", "gujarati": "gu", "kannada": "kn",
    "malayalam": "ml", "punjabi": "pa", "french": "fr",
}


def normalize_locale(value: object) -> str:
    locale = str(value or "en").strip().lower().replace("_", "-")
    locale = LOCALE_ALIASES.get(locale, locale)
    return (locale.split("-", 1)[0] or "en")[:16]


def clean_question(value: object, *, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return ""
    text = text[:limit].rstrip()
    return text if text.endswith("?") else f"{text.rstrip('.')}?"


def timeless_chat_question(value: object, *, limit: int = 500) -> str:
    """Keep a suggested Chat question from silently imposing today's date.

    Daily calculations may discover a useful subject, but opening that subject in
    Chat must leave the time scope for the user and Tara to establish.
    """
    text = clean_question(value, limit=limit)
    if not text:
        return ""

    # This was the original KP suggestion template. Rewriting the whole clause
    # reads better than merely deleting its final word.
    match = re.fullmatch(
        r"How could (.+?) become relevant today\?",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return f"How could {match.group(1)} develop in this period?"

    # LLM follow-ups and already-persisted presentations can use other forms.
    # Remove the date assertion at the presentation boundary as a final guard.
    text = re.sub(r"\bfor\s+today\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\btoday(?:['’]s)?\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+([,?.!])", r"\1", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return clean_question(text, limit=limit)


def notification_copy(*, chart_name: str, question: str, source_type: str, title: str = "", body: str = "") -> Dict[str, str]:
    name = re.sub(r"\s+", " ", str(chart_name or "")).strip()
    prefix = "Your chart" if not name else (f"{name}'s chart" if not name.lower().endswith("chart") else name)
    short_title = re.sub(r"\s+", " ", str(title or "")).strip()
    if not short_title:
        short_title = {
            "kp_daily": "Today's active theme",
            "monthly_manifestation": "A timely question",
            "chat_followup": "Continue your reading",
        }.get(source_type, "A question to explore")
    if not short_title.lower().startswith(prefix.lower()):
        short_title = f"{prefix}: {short_title}"
    short_body = re.sub(r"\s+", " ", str(body or "")).strip() or question
    return {
        "push_title": short_title[:120],
        "push_body": short_body[:240],
        "whatsapp_body": f"{short_title}\n\n{short_body}\n\nAsk Tara: {question}"[:1200],
        "sms_body": f"{short_title}: {question}"[:300],
        "email_subject": short_title[:180],
        "email_body": f"{short_body}\n\nA useful question to ask Tara:\n{question}"[:4000],
    }
