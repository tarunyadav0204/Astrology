"""
Gemini-personalized campaign copy: admin writes a base prompt, we frame one
{title, body, question} per user from their resolved parameters.

Modeled on chat_nudge_suggestion (same model preference + JSON contract); on
any failure callers fall back to plain template rendering.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)

_PARAM_LABELS = {
    "name": "User name",
    "sun_sign": "Sun sign (sidereal)",
    "moon_sign": "Moon sign (sidereal)",
    "current_dasha": "Current Vimshottari dasha (MD-AD)",
    "last_question_topic": "Last chat question topic",
    "days_since_last_chat": "Days since last chat",
    "questions_asked": "Total questions asked",
    "credits_balance": "Credit balance",
    "free_question_available": "Free question available",
}


def _format_user_context(params: Mapping[str, Any]) -> str:
    lines = []
    for key, label in _PARAM_LABELS.items():
        value = str(params.get(key) or "").strip()
        if value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines) or "- (no extra context available)"


def frame_campaign_copy(
    *,
    base_prompt: str,
    params: Mapping[str, Any],
    fallback_title: str,
    fallback_body: str,
    fallback_question: Optional[str] = None,
) -> Dict[str, str]:
    """
    Return {title, body, question} personalized via Gemini.
    Raises RuntimeError when Gemini is unavailable or returns unusable output;
    callers should catch and use the fallback copy.
    """
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    import google.generativeai as genai

    from .chat_nudge_suggestion import (
        _extract_json_object,
        _gemini_response_text,
        _nudge_suggestion_model_names,
    )

    genai.configure(api_key=api_key)
    model = None
    for name in _nudge_suggestion_model_names():
        try:
            model = genai.GenerativeModel(name)
            break
        except Exception:
            continue
    if not model:
        raise RuntimeError("No Gemini model available")

    prompt = f"""You write short mobile push notifications for an astrology app (AstroRoshni).

Campaign brief from the marketing admin:
{(base_prompt or '').strip()[:2000]}

Reference copy (use as tone/length guide, do not copy verbatim):
- title: {fallback_title[:120]}
- body: {fallback_body[:240]}

Personalize ONE nudge for this specific user:
{_format_user_context(params)}

Rules:
- Lock-screen safe: no private details verbatim in the title.
- Encourage continuing in chat with a focused astrological follow-up.
- Return ONLY valid JSON with exactly these keys:
  "title": string, max 90 characters.
  "body": string, max 190 characters.
  "question": string, max 480 characters, ONE suggested chat message the user could send.
"""

    response = model.generate_content(prompt, request_options={"timeout": 60})
    data = _extract_json_object(_gemini_response_text(response))
    if not isinstance(data, dict):
        raise RuntimeError("Gemini did not return parseable JSON")

    title = str(data.get("title") or "").strip()[:100]
    body = str(data.get("body") or "").strip()[:200]
    question = str(data.get("question") or "").strip()[:500]
    if not title or not body:
        raise RuntimeError("Gemini JSON missing title or body")
    return {
        "title": title,
        "body": body,
        "question": question or (fallback_question or ""),
    }
