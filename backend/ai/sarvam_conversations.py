"""Opt-in Sarvam conversational composer for low-latency Instant Chat."""
from __future__ import annotations

import asyncio
import json
from typing import Any, Callable, Dict, Optional

import httpx

_CHAT_URL = "https://api.sarvam.ai/v1/chat/completions"
_MODEL = "sarvam-105b-conversations"


def _max_tokens() -> int:
    from utils.admin_settings import get_setting
    try:
        return max(120, min(1200, int(get_setting("sarvam_chat_max_tokens") or 420)))
    except (TypeError, ValueError):
        return 300


async def compose(
    *,
    prompt: str,
    system_prompt: str,
    model: Optional[str] = None,
    stream_callback: Optional[Callable[[str, str], None]] = None,
    timeout_s: float = 20.0,
) -> Dict[str, Any]:
    """Generate a concise response, streaming visible text when requested."""
    from utils.admin_settings import get_sarvam_api_key
    api_key = get_sarvam_api_key()
    if not api_key:
        raise RuntimeError("Sarvam API key is not configured in Admin Settings")
    payload: Dict[str, Any] = {
        "model": str(model or _MODEL).strip() or _MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "reasoning_effort": None,
        "max_tokens": _max_tokens(),
        "stream": stream_callback is not None,
    }
    headers = {"api-subscription-key": api_key, "Accept": "application/json"}
    timeout = httpx.Timeout(max(1.0, min(45.0, float(timeout_s))))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if stream_callback is None:
            response = await client.post(_CHAT_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            text = str((((choices[0] if choices else {}).get("message") or {}).get("content") or "")).strip()
            if not text:
                raise RuntimeError("Sarvam returned blank response content")
            return {"text": text, "usage": _usage(data.get("usage"))}

        parts: list[str] = []
        published = ""
        usage: Dict[str, Any] = {}
        async with client.stream("POST", _CHAT_URL, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                usage = _usage(event.get("usage")) or usage
                choices = event.get("choices") or []
                delta = str((((choices[0] if choices else {}).get("delta") or {}).get("content") or ""))
                if not delta:
                    continue
                parts.append(delta)
                full = "".join(parts)
                if len(full) - len(published) >= 24:
                    await asyncio.to_thread(stream_callback, full[len(published):], full)
                    published = full
        text = "".join(parts).strip()
        if not text:
            raise RuntimeError("Sarvam returned blank streaming response content")
        if text != published:
            await asyncio.to_thread(stream_callback, text[len(published):], text)
        return {"text": text, "usage": usage}


def _usage(value: Any) -> Dict[str, Any]:
    row = value if isinstance(value, dict) else {}
    prompt_tokens = int(row.get("prompt_tokens") or 0)
    completion_tokens = int(row.get("completion_tokens") or 0)
    total_tokens = int(row.get("total_tokens") or (prompt_tokens + completion_tokens))
    return {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "cached_tokens": 0,
        "non_cached_input_tokens": prompt_tokens,
    }
