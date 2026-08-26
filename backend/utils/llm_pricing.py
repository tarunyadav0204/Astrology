"""Shared provider pricing helpers used by admin cost estimates.

DeepSeek V4 uses time-of-day pricing.  Keep this in one module so the Chat QA
and Credits dashboards cannot silently diverge again.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional


_DEEPSEEK_FLASH_ALIASES = {
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-chat-3.2",
    "deepseek-v4-flash",
}


def _as_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        raw = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            parsed = datetime.now(timezone.utc)
    else:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        # PostgreSQL timestamps in this application are stored in UTC.
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def deepseek_rate_usd_per_million(
    model_name: Optional[str],
    *,
    priced_at: Any = None,
) -> Optional[Dict[str, Any]]:
    """Return official DeepSeek V4 token rates for the request's UTC window.

    Peak windows are 01:00-04:00 and 06:00-10:00 UTC, Monday-Friday.
    Legacy chat/reasoner ids are billed as V4 Flash because those endpoints
    were the non-thinking/thinking aliases of that model generation.
    """

    model = str(model_name or "").strip().lower()
    if model.startswith("models/"):
        model = model.split("/", 1)[1]
    if model not in _DEEPSEEK_FLASH_ALIASES and model != "deepseek-v4-pro":
        return None

    at_utc = _as_utc(priced_at)
    hour = at_utc.hour
    peak = at_utc.weekday() < 5 and (1 <= hour < 4 or 6 <= hour < 10)

    if model == "deepseek-v4-pro":
        off_peak = {"input": 0.66, "cached_input": 0.022, "output": 1.98}
        multiplier = 2.0 if peak else 1.0
        canonical = "deepseek-v4-pro"
    else:
        off_peak = {"input": 0.22, "cached_input": 0.007, "output": 0.66}
        multiplier = 2.0 if peak else 1.0
        canonical = "deepseek-v4-flash"

    return {
        "input": off_peak["input"] * multiplier,
        "cached_input": off_peak["cached_input"] * multiplier,
        "output": off_peak["output"] * multiplier,
        "tier": "deepseek_peak" if peak else "deepseek_off_peak",
        "resolved_model": canonical,
        "priced_at_utc": at_utc.isoformat(),
    }


def mixed_stage_cost_usd(
    raw_usage: Any,
    *,
    fallback_model_name: Optional[str],
    priced_at: Any = None,
    rate_resolver: Any,
) -> Optional[Dict[str, float]]:
    """Price recorded parallel stages by their actual model rather than merge label."""

    if not raw_usage:
        return None
    try:
        usage = json.loads(raw_usage) if isinstance(raw_usage, str) else raw_usage
    except Exception:
        return None
    if not isinstance(usage, dict) or not isinstance(usage.get("stages"), list):
        return None

    result = {
        "input_non_cached": 0.0,
        "input_cached": 0.0,
        "cache_setup": 0.0,
        "output": 0.0,
    }
    priced_any = False
    for stage in usage["stages"]:
        if not isinstance(stage, dict):
            continue
        model = str(stage.get("llm_model") or fallback_model_name or "").strip() or None
        input_tokens = max(0, int(stage.get("input_tokens") or 0))
        cached_tokens = max(0, int(stage.get("cached_tokens") or 0))
        non_cached_tokens = max(0, int(stage.get("non_cached_input_tokens") or 0))
        output_tokens = max(0, int(stage.get("output_tokens") or 0))
        if non_cached_tokens <= 0 and input_tokens > 0:
            non_cached_tokens = max(input_tokens - cached_tokens, 0)
        rates = rate_resolver(model, max(input_tokens, non_cached_tokens), priced_at=priced_at)
        result["input_non_cached"] += non_cached_tokens / 1_000_000.0 * float(rates["input"])
        result["input_cached"] += cached_tokens / 1_000_000.0 * float(
            rates.get("cached_input") or rates["input"]
        )
        result["output"] += output_tokens / 1_000_000.0 * float(rates["output"])
        priced_any = priced_any or input_tokens > 0 or output_tokens > 0

    totals = usage.get("totals") if isinstance(usage.get("totals"), dict) else {}
    targets = totals.get("cache_setup_targets")
    if isinstance(targets, list):
        for target in targets:
            if not isinstance(target, dict):
                continue
            tokens = max(0, int(target.get("input_tokens") or 0))
            if tokens <= 0:
                continue
            model = str(target.get("llm_model") or fallback_model_name or "").strip() or None
            rates = rate_resolver(model, tokens, priced_at=priced_at)
            result["cache_setup"] += tokens / 1_000_000.0 * float(rates["input"])
    else:
        for token_key, model_key in (
            ("cache_setup_input_tokens_standard", "cache_setup_llm_model_standard"),
            ("cache_setup_input_tokens_premium", "cache_setup_llm_model_premium"),
        ):
            tokens = max(0, int(totals.get(token_key) or 0))
            if tokens <= 0:
                continue
            model = str(totals.get(model_key) or fallback_model_name or "").strip() or None
            rates = rate_resolver(model, tokens, priced_at=priced_at)
            result["cache_setup"] += tokens / 1_000_000.0 * float(rates["input"])

    if result["cache_setup"] <= 0:
        tokens = max(0, int(totals.get("cache_setup_input_tokens") or 0))
        if tokens > 0:
            rates = rate_resolver(fallback_model_name, tokens, priced_at=priced_at)
            result["cache_setup"] += tokens / 1_000_000.0 * float(rates["input"])

    return result if priced_any else None
