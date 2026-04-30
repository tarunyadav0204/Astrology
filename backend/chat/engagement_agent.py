import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import google.generativeai as genai

logger = logging.getLogger(__name__)

_ALLOWED_TYPES = {"insight", "curiosity", "fact_question"}


def chat_wait_engagement_enabled() -> bool:
    raw = os.getenv("CHAT_WAIT_ENGAGEMENT_ENABLED", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _clip(value: Any, limit: int = 500) -> str:
    text = str(value or "").strip()
    return text[:limit]


def build_initial_wait_engagement_updates(
    *,
    question: str,
    intent: Dict[str, Any] | None = None,
    language: str = "english",
) -> List[Dict[str, str]]:
    """Deterministic first snippet so the UI has something to show immediately."""
    if not chat_wait_engagement_enabled():
        return []

    category = str((intent or {}).get("category") or "").strip().lower()
    q = (question or "").strip()
    is_hindi_like = any("\u0900" <= ch <= "\u097f" for ch in q) or str(language).lower().startswith("hi")

    if is_hindi_like:
        base = "मैं आपका विस्तृत उत्तर तैयार कर रहा हूँ। अभी आपकी कुंडली के मुख्य योग, दशा और गोचर संकेतों को मिलाकर देख रहा हूँ।"
        fact = "जब तक विश्लेषण बन रहा है: क्या यह विषय अभी आपके जीवन में सक्रिय है, या आप भविष्य की योजना के लिए पूछ रहे हैं?"
    else:
        topic = f" for {category}" if category and category != "general" else ""
        base = f"I’m preparing your detailed reading{topic}. I’m first cross-checking the D1 chart, active dasha, and current transit signals."
        fact = "While I work on it: is this question about something already happening, or are you planning ahead?"

    return [
        {"id": "eng_initial_1", "type": "insight", "text": base},
        {"id": "eng_initial_2", "type": "fact_question", "text": fact},
    ]


def _compact_d1(context: Dict[str, Any]) -> Dict[str, Any]:
    d1 = (
        context.get("d1_chart")
        or context.get("chart_data")
        or context.get("birth_chart")
        or context.get("d1")
        or {}
    )
    if not isinstance(d1, dict):
        return {}

    planets = d1.get("planets") or d1.get("planetary_positions") or {}
    compact_planets = {}
    if isinstance(planets, dict):
        for name, row in list(planets.items())[:12]:
            if not isinstance(row, dict):
                continue
            compact_planets[str(name)] = {
                "house": row.get("house") or row.get("house_number"),
                "sign": row.get("sign_name") or row.get("sign"),
                "degree": row.get("degree") or row.get("longitude"),
            }

    asc = context.get("ascendant_info") or d1.get("ascendant") or {}
    return {
        "ascendant": asc,
        "planets": compact_planets,
    }


def _compact_dashas(context: Dict[str, Any]) -> Dict[str, Any]:
    current = context.get("current_dashas") or {}
    requested = context.get("requested_dasha_summary") or {}
    if not isinstance(current, dict):
        current = {}
    if not isinstance(requested, dict):
        requested = {}
    return {
        "current": current,
        "near_term": {
            k: requested.get(k)
            for k in ("vimshottari_sequence", "all_five_levels_sequence", "summary")
            if requested.get(k)
        },
    }


def _compact_transits(context: Dict[str, Any]) -> Any:
    transits = context.get("transit_activations") or context.get("macro_transits_timeline") or []
    if isinstance(transits, list):
        return transits[:8]
    if isinstance(transits, dict):
        return {k: transits[k] for k in list(transits.keys())[:8]}
    return []


def _sanitize_updates(raw: Any) -> List[Dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: List[Dict[str, str]] = []
    for idx, item in enumerate(raw[:3]):
        if not isinstance(item, dict):
            continue
        update_type = str(item.get("type") or "").strip().lower()
        if update_type not in _ALLOWED_TYPES:
            update_type = "insight"
        text = _clip(item.get("text"), 420)
        if not text:
            continue
        out.append(
            {
                "id": f"eng_{idx + 1}",
                "type": update_type,
                "text": text,
            }
        )
    return out


async def generate_wait_engagement_updates(
    *,
    question: str,
    context: Dict[str, Any],
    intent: Dict[str, Any],
    language: str,
    user_facts: Dict[str, Any] | None = None,
) -> List[Dict[str, str]]:
    if not chat_wait_engagement_enabled():
        return []

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []

    genai.configure(api_key=api_key)
    try:
        from utils.admin_settings import get_setting

        model_name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
    except Exception:
        model_name = "models/gemini-2.5-flash-lite"
    if "pro" in model_name.lower():
        model_name = "models/gemini-2.5-flash-lite"

    lean_context = {
        "today": datetime.now().strftime("%Y-%m-%d"),
        "question": _clip(question, 1000),
        "language": _clip(language or "english", 80),
        "intent": {
            "mode": (intent or {}).get("mode"),
            "category": (intent or {}).get("category"),
            "context_type": (intent or {}).get("context_type"),
        },
        "d1": _compact_d1(context or {}),
        "dashas": _compact_dashas(context or {}),
        "major_transits": _compact_transits(context or {}),
        "known_user_facts": user_facts or {},
    }

    prompt = f"""
You are a wait-time engagement assistant for an astrology chat app.

The final detailed answer is still being prepared by specialist agents. Your job is only to give 1-3 short interim snippets that keep the user engaged.

Rules:
- Do NOT answer the user's main question fully.
- Do NOT make strong predictions, exact event timing claims, medical/legal/financial directives, or remedies.
- Use only the lean context JSON below.
- Keep each item under 45 words.
- Match the user's language/script as best as possible.
- Prefer one item related to the question, one optional chart curiosity, and one gentle fact-gathering question if useful.
- Fact questions must ask about user-stated real-life context, not birth details.
- Return JSON array only. No markdown fences.

Allowed item types: insight, curiosity, fact_question.

Lean context JSON:
{json.dumps(lean_context, ensure_ascii=False, default=str)}

Return shape:
[
  {{"type": "insight", "text": "..."}},
  {{"type": "curiosity", "text": "..."}},
  {{"type": "fact_question", "text": "..."}}
]
"""

    try:
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(temperature=0.4, top_p=0.9, top_k=40),
        )
        response = await model.generate_content_async(prompt, request_options={"timeout": 8})
        cleaned = (response.text or "").replace("```json", "").replace("```", "").strip()
        parsed = json.loads(cleaned)
        return _sanitize_updates(parsed)
    except Exception as exc:
        logger.info("wait engagement skipped: %s", str(exc)[:200])
        return []
