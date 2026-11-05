"""Small, opt-in client for Sarvam Prism's typed Decisions API."""
from __future__ import annotations

from typing import Any, Mapping

import httpx

_DECISIONS_URL = "https://api.sarvam.ai/v2/systemone"


def is_prism_enabled() -> bool:
    from utils.admin_settings import get_setting
    return str(get_setting("sarvam_prism_enabled") or "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _timeout_seconds() -> float:
    from utils.admin_settings import get_setting
    try:
        return max(1.0, min(10.0, float(get_setting("sarvam_prism_timeout_seconds") or 3)))
    except (TypeError, ValueError):
        return 3.0


async def decide(*, state: Mapping[str, Any], questions: Mapping[str, Any]) -> dict[str, Any]:
    """Call Prism without logging the input state or API key.

    Prism returns typed decisions rather than generated text.  Callers should
    treat any transport/API failure as a signal to use their existing router.
    """
    from utils.admin_settings import get_sarvam_api_key
    api_key = get_sarvam_api_key()
    if not api_key:
        raise RuntimeError("Sarvam API key is not configured in Admin Settings")
    payload = {"model": "sarvam-prism", "state": dict(state), "questions": dict(questions)}
    headers = {"api-subscription-key": api_key, "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(_timeout_seconds())) as client:
        response = await client.post(_DECISIONS_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("answers"), dict):
        raise ValueError("Sarvam Prism response did not include typed answers")
    return data
