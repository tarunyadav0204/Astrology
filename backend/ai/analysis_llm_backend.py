"""
Non-chat analysis, Reports Studio, & event-timeline LLM routing (Gemini vs DeepSeek) from admin_settings.

Provides a small adapter so existing code can keep calling ``.generate_content`` /
``.generate_content_async`` while honoring ``analysis_llm_vendor``, ``report_llm_vendor``,
and ``timeline_llm_vendor``.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from typing import Any, Dict, Optional, Tuple

from utils.admin_settings import (
    CHAT_LLM_DEEPSEEK,
    CHAT_LLM_GEMINI,
    GEMINI_MODEL_OPTIONS,
    get_analysis_llm_vendor,
    get_deepseek_analysis_model,
    get_deepseek_report_model,
    get_deepseek_timeline_model,
    get_event_timeline_model,
    get_gemini_analysis_model,
    get_gemini_report_model,
    get_report_llm_vendor,
    get_timeline_llm_vendor,
)


class _GeminiUsageMetadata:
    __slots__ = (
        "prompt_token_count",
        "candidates_token_count",
        "cached_content_token_count",
        "total_token_count",
    )

    def __init__(self, prompt_token_count: int, candidates_token_count: int) -> None:
        self.prompt_token_count = int(prompt_token_count or 0)
        self.candidates_token_count = int(candidates_token_count or 0)
        self.cached_content_token_count = 0
        self.total_token_count = self.prompt_token_count + self.candidates_token_count


def _deepseek_sync_text(model_id: str, prompt: str) -> Tuple[str, Dict[str, int]]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "The 'openai' package is required for DeepSeek analysis. "
            "Install with: pip install 'openai>=1.40.0'"
        ) from e

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is not set")

    base_url = (os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip().rstrip("/")
    client = OpenAI(api_key=api_key, base_url=f"{base_url}/v1", timeout=600.0)
    mid = (model_id or "").strip() or "deepseek-chat"
    resp = client.chat.completions.create(
        model=mid,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=8192,
    )
    if not resp.choices:
        raise RuntimeError("Empty DeepSeek choices")
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise RuntimeError("Blank DeepSeek response content")
    usage_obj = getattr(resp, "usage", None)
    inp = int(getattr(usage_obj, "prompt_tokens", 0) or 0)
    out = int(getattr(usage_obj, "completion_tokens", 0) or 0)
    total = int(getattr(usage_obj, "total_tokens", 0) or (inp + out))
    return content, {"input_tokens": inp, "output_tokens": out, "total_tokens": total}


class DeepSeekGenerativeAdapter:
    """
    Minimal subset of google.generativeai.GenerativeModel used by analysis/timeline code:
    - ``model_name`` for logging
    - ``generate_content(prompt, generation_config=..., safety_settings=...)``
    - ``generate_content_async(...)``
    """

    __slots__ = ("model_name",)

    def __init__(self, model_id: str) -> None:
        self.model_name = (model_id or "").strip() or "deepseek-chat"

    def generate_content(
        self,
        prompt: Any,
        generation_config: Any = None,
        safety_settings: Any = None,
        **kwargs: Any,
    ) -> Any:
        text_in = prompt if isinstance(prompt, str) else str(prompt)
        text, usage = _deepseek_sync_text(self.model_name, text_in)
        um = _GeminiUsageMetadata(usage["input_tokens"], usage["output_tokens"])
        return SimpleNamespace(text=text, usage_metadata=um)

    async def generate_content_async(
        self,
        prompt: Any,
        request_options: Any = None,
        **kwargs: Any,
    ) -> Any:
        return await asyncio.to_thread(self.generate_content, prompt, **kwargs)


def _build_gemini_with_fallbacks(preferred: str) -> Tuple[Any, str]:
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    genai.configure(api_key=api_key)
    fallbacks = [m[0] for m in GEMINI_MODEL_OPTIONS if m[0] != preferred]
    last_err: Optional[Exception] = None
    for name in [preferred] + fallbacks:
        try:
            return genai.GenerativeModel(name), name
        except Exception as e:
            last_err = e
            continue
    raise ValueError(f"No available Gemini model (last error: {last_err})")


def build_analysis_llm_model() -> Tuple[Any, str, str]:
    """
    Model for health/wealth/karma/structured analysis/etc.

    Returns:
        (model, resolved_model_id, vendor) where vendor is ``gemini`` or ``deepseek``.
    """
    vendor = get_analysis_llm_vendor()
    if vendor == CHAT_LLM_DEEPSEEK:
        mid = get_deepseek_analysis_model()
        return DeepSeekGenerativeAdapter(mid), mid, CHAT_LLM_DEEPSEEK
    preferred = get_gemini_analysis_model()
    m, name = _build_gemini_with_fallbacks(preferred)
    return m, name, CHAT_LLM_GEMINI


def build_report_llm_model() -> Tuple[Any, str, str]:
    """
    Model for Reports Studio PDF chapters (partnership, wealth, etc.).

    Returns:
        (model, resolved_model_id, vendor) where vendor is ``gemini`` or ``deepseek``.
    """
    vendor = get_report_llm_vendor()
    if vendor == CHAT_LLM_DEEPSEEK:
        mid = get_deepseek_report_model()
        return DeepSeekGenerativeAdapter(mid), mid, CHAT_LLM_DEEPSEEK
    preferred = get_gemini_report_model()
    m, name = _build_gemini_with_fallbacks(preferred)
    return m, name, CHAT_LLM_GEMINI


def build_timeline_llm_model() -> Tuple[Any, str, str]:
    """
    Model for yearly/monthly event timeline (EventPredictor).

    Returns:
        (model, resolved_model_id, vendor) where vendor is ``gemini`` or ``deepseek``.
    """
    vendor = get_timeline_llm_vendor()
    if vendor == CHAT_LLM_DEEPSEEK:
        mid = get_deepseek_timeline_model()
        return DeepSeekGenerativeAdapter(mid), mid, CHAT_LLM_DEEPSEEK
    preferred = get_event_timeline_model()
    m, name = _build_gemini_with_fallbacks(preferred)
    return m, name, CHAT_LLM_GEMINI
