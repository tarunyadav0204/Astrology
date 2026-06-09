"""
LLM-based classifier: whether the user is asking for fetal / unborn sex or gender prediction.

Uses semantic understanding across languages (no regex keyword lists). Intended to enforce
Indian legal / ethical restrictions (e.g. PCPNDT) and product policy: do not answer
sex-determination questions for a pregnancy or unborn child.

On model errors or timeouts, fails open (returns not blocked) so chat stays available.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict

import google.generativeai as genai

logger = logging.getLogger(__name__)

FETAL_SEX_REFUSAL_MESSAGE = (
    "I'm not able to answer questions about determining an unborn baby's sex or gender. "
    "That kind of prediction isn't something we can provide. "
    "I can still help with general pregnancy or family timing, children's houses, or well-being "
    "from the chart—without predicting the baby's sex."
)


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = (text or "").replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _normalize_result(raw: Dict[str, Any]) -> tuple[bool, str]:
    """
    Returns (should_block, reason).
    Block when the model says this is a fetal sex determination request with high or medium confidence.
    """
    if not isinstance(raw, dict):
        return False, "invalid_json"
    flag = raw.get("fetal_sex_determination_request")
    if isinstance(flag, str):
        flag = flag.strip().lower() in ("true", "yes", "1")
    elif not isinstance(flag, bool):
        flag = False
    conf = str(raw.get("confidence") or "low").strip().lower()
    reason = str(raw.get("reason") or "").strip()[:200]
    if not flag:
        return False, reason or "not_requested"
    if conf not in {"high", "medium"}:
        return False, reason or "low_confidence"
    return True, reason or "blocked"


class FetalSexQueryClassifier:
    """Gemini flash-lite gate: multilingual intent for fetal sex / gender of unborn."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        from utils.admin_settings import get_setting

        model_name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
        if "pro" in model_name.lower():
            model_name = "models/gemini-2.5-flash-lite"
        config = genai.GenerationConfig(temperature=0, top_p=0.95, top_k=40)
        try:
            self.model = genai.GenerativeModel(model_name, generation_config=config)
        except Exception:
            self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite-001", generation_config=config)

    async def classify(self, *, question: str, language: str = "english") -> Dict[str, Any]:
        q = (question or "").strip()
        if not q:
            return {"blocked": False, "confidence": "low", "reason": "empty"}

        prompt = f"""You are a safety classifier for an astrology app. The user's message may be in ANY language or script.

Task: Decide whether the user's PRIMARY intent is to learn or predict the **biological sex / gender of an unborn fetus or baby still in utero** (including euphemisms, coded language, or ultrasound-style questions), which must NOT be answered (legal/ethical restrictions in India and app policy).

Set fetal_sex_determination_request = true ONLY when the message is mainly asking for:
- Whether the pregnancy is a boy or a girl / son or daughter
- Sex or gender of the baby before birth / in the womb
- Garbha / fetus gender, "ladka ya ladki" **in a pregnancy or unborn-baby sense**, "pink or blue", ultrasound-style guessing from astrology, etc.

Set fetal_sex_determination_request = false when:
- **Another woman / third party / affair / extramarital involvement** (e.g. Hindi "mere aur mere pati/pati ke beech koi ladki hai", "koi aur aurat", "relationship mein koi aur hai") — words like ladki/aurat/ladka here refer to **people already born**, not fetal sex. These are relationship-trust questions, NOT fetal sex; always false here.
- General children / progeny / pregnancy timing without asking for sex (e.g. "when will I conceive", "will I have kids")
- Questions about **already-born** children (their life, health, education) even if words like "son" or "daughter" appear
- Chart technique, houses of children, remedies, general family outlook
- User or partner's own gender identity (not about predicting an unborn child's sex)
- Any topic where sex/gender of an **unborn** child is not the main ask

confidence:
- high: clear fetal sex determination request
- medium: likely but some ambiguity
- low: unlikely, unrelated, or unclear

User language hint (for context only): {language}

User message:
{q}

Return ONLY valid JSON (no markdown):
{{
  "fetal_sex_determination_request": true or false,
  "confidence": "high" or "medium" or "low",
  "reason": "short internal label in English"
}}
"""
        try:
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt, request_options={"timeout": 10}),
                timeout=12,
            )
            raw = _extract_json(getattr(response, "text", "") or "")
            blocked, reason = _normalize_result(raw)
            return {"blocked": blocked, "confidence": raw.get("confidence"), "reason": reason}
        except Exception as exc:
            logger.warning("fetal sex query classifier failed; allowing question: %s", exc)
            return {"blocked": False, "confidence": "low", "reason": "classifier_error"}


async def should_refuse_fetal_sex_determination(*, question: str, language: str = "english") -> bool:
    """True => caller should return FETAL_SEX_REFUSAL_MESSAGE and skip the main model."""
    result = await FetalSexQueryClassifier().classify(question=question, language=language or "english")
    return bool(result.get("blocked"))
