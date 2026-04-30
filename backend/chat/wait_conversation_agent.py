import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai

from chat.engagement_agent import _compact_d1, _compact_dashas, _compact_transits, _clip

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def chat_wait_side_conversation_enabled() -> bool:
    return _env_bool("CHAT_WAIT_SIDE_CONVERSATION_ENABLED", default=False)


def chat_wait_side_gemini_cache_enabled() -> bool:
    return _env_bool("CHAT_WAIT_SIDE_GEMINI_CACHE_ENABLED", default=True)


def chat_wait_side_cache_ttl_s() -> int:
    try:
        return max(300, int(os.getenv("CHAT_WAIT_SIDE_GEMINI_CACHE_TTL_S", "900") or 900))
    except Exception:
        return 900


def get_wait_side_model_name() -> str:
    try:
        from utils.admin_settings import get_setting

        model_name = (get_setting("gemini_intent_model") or "models/gemini-2.5-flash-lite").strip()
    except Exception:
        model_name = "models/gemini-2.5-flash-lite"
    if "pro" in model_name.lower():
        return "models/gemini-2.5-flash-lite"
    return model_name


def build_wait_side_cache_payload(
    *,
    question: str,
    context: Dict[str, Any],
    intent: Dict[str, Any],
    language: str,
    user_facts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "today": datetime.now().strftime("%Y-%m-%d"),
        "original_question": _clip(question, 1200),
        "language": _clip(language or "english", 80),
        "intent": {
            "mode": (intent or {}).get("mode"),
            "category": (intent or {}).get("category"),
            "context_type": (intent or {}).get("context_type"),
        },
        "d1": _compact_d1(context or {}),
        "dashas": _compact_dashas(context or {}),
        "transit_activations": _compact_transits(context or {}),
        "known_user_facts": user_facts or {},
    }


def _clean_text(text: str, limit: int = 700) -> str:
    cleaned = (text or "").replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return ""
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            cleaned = str(parsed.get("text") or parsed.get("message") or "").strip()
    except Exception:
        pass
    return _clip(cleaned, limit)


def _side_system_instruction() -> str:
    return """
You are a side conversation assistant for an astrology chat app.
The user's final detailed answer is being prepared by another agent.

Your job:
- Keep the user engaged in a short, useful conversation while they wait.
- Use the cached chart context: D1, house placements, current/upcoming dashas, transit activations, intent/category, and original question.
- Ask curiosity-generating questions tied to chart signals, especially activated houses and dasha/transit themes.
- Do not give the final answer, predictions with exact timing, remedies, medical/legal/financial directives, or certainty-heavy claims.
- Keep each reply under 70 words.
- Match the user's language/script as best as possible.
- If the user answers your question, acknowledge it and ask one relevant next question or briefly explain why it matters for the reading.
""".strip()


async def create_wait_side_cache(
    *,
    cache_payload: Dict[str, Any],
    cache_label: str = "chat_wait_side",
) -> Tuple[Optional[str], str, Optional[datetime], Optional[Any]]:
    model_name = get_wait_side_model_name()
    if not chat_wait_side_gemini_cache_enabled():
        return None, model_name, None, None
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None, model_name, None, None

    genai.configure(api_key=api_key)
    try:
        from google.generativeai import caching as genai_caching

        ttl_s = chat_wait_side_cache_ttl_s()
        cache_text = f"CHAT_WAIT_SIDE_CONTEXT_JSON:\n{json.dumps(cache_payload, ensure_ascii=False, default=str)}"
        cache_resource = await asyncio.to_thread(
            genai_caching.CachedContent.create,
            model=model_name,
            display_name=f"{cache_label}-{int(datetime.now().timestamp())}",
            system_instruction=_side_system_instruction(),
            contents=[cache_text],
            ttl=ttl_s,
        )
        cached_model = await asyncio.to_thread(genai.GenerativeModel.from_cached_content, cache_resource)
        return getattr(cache_resource, "name", None), model_name, datetime.now() + timedelta(seconds=ttl_s), cached_model
    except Exception as exc:
        logger.info("wait side cache create skipped: %s", str(exc)[:200])
        return None, model_name, None, None


async def delete_wait_side_cache(cache_name: Optional[str]) -> None:
    if not cache_name:
        return
    try:
        from google.generativeai import caching as genai_caching

        cache_resource = await asyncio.to_thread(genai_caching.CachedContent.get, cache_name)
        await asyncio.to_thread(cache_resource.delete)
    except Exception as exc:
        logger.info("wait side cache delete skipped name=%s: %s", cache_name, str(exc)[:200])


async def _model_from_cache(cache_name: Optional[str]) -> Optional[Any]:
    if not cache_name:
        return None
    try:
        from google.generativeai import caching as genai_caching

        cache_resource = await asyncio.to_thread(genai_caching.CachedContent.get, cache_name)
        return await asyncio.to_thread(genai.GenerativeModel.from_cached_content, cache_resource)
    except Exception as exc:
        logger.info("wait side cache load skipped name=%s: %s", cache_name, str(exc)[:200])
        return None


async def generate_wait_side_reply(
    *,
    user_text: Optional[str],
    conversation_history: List[Dict[str, Any]],
    cache_name: Optional[str],
    cache_payload: Optional[Dict[str, Any]] = None,
    closing: bool = False,
) -> str:
    if not chat_wait_side_conversation_enabled():
        return ""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""

    genai.configure(api_key=api_key)
    model = await _model_from_cache(cache_name)
    prompt_payload = {
        "side_conversation_history": conversation_history[-8:],
        "latest_user_reply": _clip(user_text, 800),
        "closing": closing,
    }
    if closing:
        prompt = (
            "The final detailed answer is ready now. Write one graceful closing line for the wait "
            "conversation and tell the user the full answer is coming below. If they just gave context, "
            "acknowledge it briefly. Return plain text only.\n\n"
            f"{json.dumps(prompt_payload, ensure_ascii=False, default=str)}"
        )
    else:
        prompt = (
            "Write the next side-conversation assistant message. Use cached chart context. "
            "If this is the first assistant message, identify one or two active house/dasha/transit themes "
            "and ask a useful curiosity question related to the user's original question. Return plain text only.\n\n"
            f"{json.dumps(prompt_payload, ensure_ascii=False, default=str)}"
        )

    if model is None:
        model_name = get_wait_side_model_name()
        inline_context = {"cached_context_fallback": cache_payload or {}, **prompt_payload}
        prompt = f"{_side_system_instruction()}\n\n{prompt}\n\nContext:\n{json.dumps(inline_context, ensure_ascii=False, default=str)}"
        model = genai.GenerativeModel(
            model_name,
            generation_config=genai.GenerationConfig(temperature=0.45, top_p=0.9, top_k=40),
        )

    try:
        response = await model.generate_content_async(prompt, request_options={"timeout": 8})
        return _clean_text(response.text or "")
    except Exception as exc:
        logger.info("wait side reply skipped: %s", str(exc)[:200])
        return ""
