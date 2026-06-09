"""
Self-hosted Gemma (or compatible) HTTP chat backend.

POST JSON to `{url}` (default from admin `gemma_chat_generate_url` or env
`GEMMA_CHAT_GENERATE_URL`). Response shape is normalized from common keys.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

import requests

logger = logging.getLogger(__name__)


def gemma_sanitize_json_value(obj: Any) -> Any:
    """
    Return a deep copy of nested structures using only JSON-friendly primitives.

    Used only for Gemma HTTP `requests.post(..., json=...)` — Gemini / OpenAI / DeepSeek
    paths are unchanged and never call this.
    """
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, (bytes, bytearray)):
        try:
            return bytes(obj).decode("utf-8", errors="replace")
        except Exception:
            return ""

    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            key = k if isinstance(k, str) else str(k)
            out[key] = gemma_sanitize_json_value(v)
        return out
    if isinstance(obj, (list, tuple)):
        return [gemma_sanitize_json_value(x) for x in obj]
    if isinstance(obj, set):
        return [gemma_sanitize_json_value(x) for x in obj]

    try:
        import numpy as np  # type: ignore

        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, np.ndarray):
            return gemma_sanitize_json_value(obj.tolist())
    except ImportError:
        pass

    # Last resort: stringify so POST never dies on unknown chart types
    return str(obj)


def _normalize_gemma_url(url: str) -> str:
    """Strip whitespace; fix accidental space before port (e.g. `host :8000`)."""
    s = (url or "").strip()
    s = re.sub(r"\s+", "", s)
    return s


def extract_gemma_analysis_text(result: Any) -> str:
    """Parse /generate-analysis style JSON into plain text."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result.strip()
    if not isinstance(result, dict):
        return str(result).strip()

    data = result.get("data")
    if isinstance(data, str) and data.strip():
        return data.strip()
    if isinstance(data, dict):
        for key in ("text", "response", "analysis", "message", "content", "answer"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()

    for key in ("response", "analysis", "message", "content", "answer", "text"):
        v = result.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()

    try:
        dumped = json.dumps(result, ensure_ascii=False, default=str)
        if len(dumped) < 12000:
            logger.warning("gemma_chat_client: unexpected response shape keys=%s", list(result.keys())[:20])
    except Exception:
        pass
    return ""


def _post_json_sync(url: str, payload: dict, timeout_s: float) -> dict:
    connect_timeout = min(30.0, max(5.0, timeout_s * 0.05))
    read_timeout = max(30.0, timeout_s)
    clean = gemma_sanitize_json_value(payload)
    if not isinstance(clean, dict):
        logger.warning("gemma_chat_client: sanitized payload is not a dict; wrapping")
        clean = {"_wrapped": clean}
    # Fail fast with a clear error if anything still cannot encode (should not happen)
    try:
        json.dumps(clean, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"gemma payload still not JSON-serializable after sanitize: {exc}") from exc

    resp = requests.post(
        url,
        json=clean,
        headers={"Content-Type": "application/json"},
        timeout=(connect_timeout, read_timeout),
    )
    resp.raise_for_status()
    if not (resp.text or "").strip():
        return {}
    try:
        return resp.json()
    except ValueError as exc:
        logger.warning("gemma_chat_client: non-JSON body: %s", exc)
        return {"data": resp.text}


async def post_gemma_generate_analysis(
    url: str,
    payload: dict,
    *,
    timeout_s: float = 600.0,
) -> Dict[str, Any]:
    """
    POST payload to Gemma service. Returns dict with keys:
      text, raw, error (optional)
    """
    safe_url = _normalize_gemma_url(url)
    if not safe_url:
        return {"text": "", "raw": None, "error": "gemma_chat_generate_url_empty"}

    def _run() -> Dict[str, Any]:
        try:
            raw = _post_json_sync(safe_url, payload, timeout_s)
            text = extract_gemma_analysis_text(raw)
            return {"text": text, "raw": raw, "error": None if text else "empty_gemma_response"}
        except requests.RequestException as exc:
            logger.warning("gemma_chat_client: request failed: %s", exc)
            return {"text": "", "raw": None, "error": str(exc)}
        except Exception as exc:
            logger.exception("gemma_chat_client: unexpected error")
            return {"text": "", "raw": None, "error": str(exc)}

    return await asyncio.to_thread(_run)
