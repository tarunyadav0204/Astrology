"""
Short-lived Gemini CachedContent helpers for multi-call fan-out (chat branches, report chapters).

Create once per request, reuse across parallel generate calls, then delete.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return bool(default)
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def gemini_context_cache_ttl_s(*, env_name: str = "ASTRO_GEMINI_CONTEXT_CACHE_TTL_S", default: int = 300) -> int:
    # Explicitly deleted after each request; TTL is only a fallback.
    try:
        return max(300, int(os.getenv(env_name, str(default)) or default))
    except Exception:
        return max(300, default)


def _json_compact(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


async def create_gemini_context_cache(
    *,
    llm_provider: str,
    model_name: str,
    cache_payload: Dict[str, Any],
    cache_label: str,
    cache_enabled_env: str = "ASTRO_GEMINI_CONTEXT_CACHE",
    system_instruction: str = "Use cached shared context for all reasoning in this request.",
    ttl_env_name: str = "ASTRO_GEMINI_CONTEXT_CACHE_TTL_S",
) -> Tuple[Optional[Any], Optional[Any], int, int]:
    """
    Create a short-lived Gemini CachedContent resource.

    Returns: (cache_resource, cached_model, setup_chars, setup_tokens)
    """
    if str(llm_provider or "").strip().lower() != "gemini" or not env_bool(cache_enabled_env, default=True):
        return None, None, 0, 0
    try:
        from google.generativeai import caching as genai_caching
        import google.generativeai as genai

        cache_text = f"{cache_label.upper()}_SHARED_CONTEXT_JSON:\n{_json_compact(cache_payload)}"
        cache_setup_input_chars = len(cache_text)
        cache_setup_input_tokens = max(1, int(round(cache_setup_input_chars / 4.0)))
        ttl_s = gemini_context_cache_ttl_s(env_name=ttl_env_name)
        logger.info(
            "%s_CACHE create model=%s ttl_s=%s context_chars=%s",
            cache_label.upper(),
            model_name,
            ttl_s,
            cache_setup_input_chars,
        )
        cache_resource = await asyncio.to_thread(
            genai_caching.CachedContent.create,
            model=model_name,
            display_name=f"{cache_label}-{int(time.time())}",
            system_instruction=system_instruction,
            contents=[cache_text],
            ttl=ttl_s,
        )
        cached_model = await asyncio.to_thread(
            genai.GenerativeModel.from_cached_content,
            cache_resource,
        )
        logger.info(
            "%s_CACHE created name=%s",
            cache_label.upper(),
            getattr(cache_resource, "name", "unknown"),
        )
        return cache_resource, cached_model, cache_setup_input_chars, cache_setup_input_tokens
    except Exception as e:
        logger.warning("%s_CACHE failed; continuing without cache: %s", cache_label.upper(), e)
        return None, None, 0, 0


async def delete_gemini_context_cache(cache_resource: Optional[Any], *, cache_label: str) -> None:
    if cache_resource is None:
        return
    try:
        await asyncio.to_thread(cache_resource.delete)
        logger.info("%s_CACHE deleted", cache_label.upper())
    except Exception as e:
        logger.warning("%s_CACHE delete failed: %s", cache_label.upper(), e)
