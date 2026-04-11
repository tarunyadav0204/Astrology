"""
Classify whether the user is asking about another person's birth chart (needs a new native)
vs asking about their own chart / timing. Used before expensive chat routing.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict

import google.generativeai as genai


def _default_gate_result() -> Dict[str, Any]:
    return {
        "primary_intent": "general_chart_question",
        "confidence": 1.0,
        "show_create_native_cta": False,
        "user_facing_explanation": "",
        "extracted_birth_hint": {"name": None, "date": None, "time": None, "place": None},
        "clarify_question": None,
    }


def _parse_json_response(text: str) -> Dict[str, Any]:
    if not text:
        return _default_gate_result()
    cleaned = text.replace("```json", "").replace("```", "").strip()
    m = re.search(r"\{[\s\S]*\}", cleaned)
    if m:
        cleaned = m.group(0)
    return json.loads(cleaned)


async def classify_subject_native_gate(
    user_question: str,
    current_native_name: str = "",
    language: str = "english",
) -> Dict[str, Any]:
    """
    Returns keys:
      primary_intent: third_party_birth_chart_request | natal_timeline_question |
                      general_chart_question | unclear
      confidence: 0..1
      show_create_native_cta: bool
      user_facing_explanation: str (shown when gating; should match user's language when possible)
      extracted_birth_hint: {name, date, time, place} (nullable strings)
      clarify_question: str | null
    """
    q = (user_question or "").strip()
    if len(q) < 12:
        return _default_gate_result()

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ subject_native_gate: no GEMINI_API_KEY, skipping gate")
        return _default_gate_result()

    genai.configure(api_key=api_key)
    from utils.admin_settings import get_gemini_chat_model, DEFAULT_GEMINI_CHAT_MODEL

    model_name = get_gemini_chat_model()
    gen_config = genai.GenerationConfig(temperature=0, top_p=0.95, top_k=40)
    try:
        model = genai.GenerativeModel(model_name, generation_config=gen_config)
    except Exception as e:
        print(f"⚠️ subject_native_gate model {model_name} unavailable ({e}), using default")
        model = genai.GenerativeModel(DEFAULT_GEMINI_CHAT_MODEL, generation_config=gen_config)

    lang_note = (
        f"Write user_facing_explanation and clarify_question in {language} when that language is not english."
        if (language or "").lower() != "english"
        else "Write user_facing_explanation and clarify_question in clear English."
    )

    prompt = f"""You route messages for an astrology app. The app answers using ONE selected birth chart
(the "current native": {current_native_name or "user's saved profile"}) unless the user adds another saved profile.

User message:
\"\"\"{q}\"\"\"

Return ONLY valid JSON (no markdown fences):
{{
  "primary_intent": "third_party_birth_chart_request" | "natal_timeline_question" | "general_chart_question" | "unclear",
  "confidence": <number 0-1>,
  "show_create_native_cta": <boolean>,
  "user_facing_explanation": "<short paragraph explaining we need a saved profile for the OTHER person>",
  "extracted_birth_hint": {{"name": <string or null>, "date": <string or null>, "time": <string or null>, "place": <string or null>}},
  "clarify_question": <string or null>
}}

Definitions:
- third_party_birth_chart_request: User gives or implies birth details (date/time/place) for SOMEONE ELSE
  (child, spouse, friend, baby, "my daughter") and wants a reading for THAT person's chart — not the same as
  asking what happened to ME on a date.
- natal_timeline_question: A date/time period is about the USER's own life, transits, dasha, "what was happening
  for me", solar return, events in MY chart — NOT setting up a new person's natal chart.
- general_chart_question: Normal question about the current native with no conflicting third-party birth story.
- unclear: Genuinely ambiguous between third-party birth vs own timeline.

Rules:
- show_create_native_cta MUST be true ONLY if primary_intent is third_party_birth_chart_request AND confidence >= 0.75.
- If primary_intent is unclear (or third_party with confidence 0.55-0.74), set clarify_question to ONE short question
  offering two paths: (1) analyzing the current native around that date vs (2) adding another person's birth profile.
  Otherwise clarify_question MUST be null.
- Never set show_create_native_cta for natal_timeline_question or general_chart_question.
- {lang_note}
"""

    t0 = time.time()
    try:
        resp = await model.generate_content_async(prompt)
        raw = (resp.text or "").strip()
        result = _parse_json_response(raw)
        elapsed = time.time() - t0
        print(f"✅ subject_native_gate: intent={result.get('primary_intent')} conf={result.get('confidence')} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"❌ subject_native_gate failed: {e}")
        return _default_gate_result()

    # Normalize
    out = _default_gate_result()
    pi = result.get("primary_intent") or "general_chart_question"
    if pi not in (
        "third_party_birth_chart_request",
        "natal_timeline_question",
        "general_chart_question",
        "unclear",
    ):
        pi = "general_chart_question"
    out["primary_intent"] = pi
    try:
        out["confidence"] = float(result.get("confidence", 0))
    except (TypeError, ValueError):
        out["confidence"] = 0.0
    out["confidence"] = max(0.0, min(1.0, out["confidence"]))

    cta = bool(result.get("show_create_native_cta"))
    if pi != "third_party_birth_chart_request" or out["confidence"] < 0.75:
        cta = False
    out["show_create_native_cta"] = cta

    expl = (result.get("user_facing_explanation") or "").strip()
    if not expl and cta:
        expl = (
            "It sounds like you're asking about another person's birth chart. "
            "Add them as a saved birth profile (a \"native\") first so we can calculate their chart accurately."
        )
    out["user_facing_explanation"] = expl

    hint = result.get("extracted_birth_hint") or {}
    if not isinstance(hint, dict):
        hint = {}
    out["extracted_birth_hint"] = {
        "name": hint.get("name"),
        "date": hint.get("date"),
        "time": hint.get("time"),
        "place": hint.get("place"),
    }

    cq = result.get("clarify_question")
    out["clarify_question"] = (cq.strip() if isinstance(cq, str) and cq.strip() else None)

    if out["show_create_native_cta"]:
        out["clarify_question"] = None

    return out
