"""LLM synthesis for deterministic chart manifestations.

The prediction engine remains authoritative for activation, mapping, tone, timing
and evidence. This module only turns activated house significations into readable
combined-life-theme wording, and caches by house combination + subject + tone.
"""

from __future__ import annotations

import hashlib
import json
import logging
import asyncio
import os
from datetime import date
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from db import execute, get_conn
from utils.admin_settings import (
    CHAT_LLM_DEEPSEEK,
    CHAT_LLM_GEMMA,
    CHAT_LLM_OPENAI,
    get_chat_llm_provider,
    get_deepseek_chat_model,
    get_gemini_chat_model,
    get_openai_chat_model,
)

from .house_significations import HOUSE_SIGNIFICATIONS, relative_house_for_native

logger = logging.getLogger(__name__)
SYNTHESIS_VERSION = "2.4.1"

_TONE_FOR_LLM = {
    "challenging": "pressure",
    "mixed": "mixed",
    "supportive": "constructive",
    "neutral": "unclear",
}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _cache_key(context: Mapping[str, Any], *, locale: str, provider: str, model: str) -> str:
    payload = {
        "version": SYNTHESIS_VERSION,
        "locale": locale,
        "provider": provider,
        "model": model,
        "context": context,
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _model_details() -> tuple[str, str]:
    provider = get_chat_llm_provider()
    if provider == CHAT_LLM_OPENAI:
        return provider, get_openai_chat_model()
    if provider == CHAT_LLM_DEEPSEEK:
        return provider, get_deepseek_chat_model()
    if provider == CHAT_LLM_GEMMA:
        return provider, "gemma-http"
    return provider, get_gemini_chat_model()


def _load(cache_key: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = execute(conn, "SELECT output_json FROM prediction_manifestation_syntheses WHERE cache_key = %s", (cache_key,)).fetchone()
    if not row:
        return None
    value = row[0]
    return value if isinstance(value, dict) else json.loads(value)


def _save(cache_key: str, *, context: Mapping[str, Any], output: Mapping[str, Any], locale: str, provider: str, model: str) -> None:
    with get_conn() as conn:
        execute(conn, """
            INSERT INTO prediction_manifestation_syntheses
              (cache_key, locale, provider, model, input_json, output_json)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb)
            ON CONFLICT (cache_key) DO UPDATE SET
              output_json = EXCLUDED.output_json,
              model = EXCLUDED.model,
              updated_at = CURRENT_TIMESTAMP
        """, (cache_key, locale, provider, model, _canonical(context), _canonical(output)))
        conn.commit()


def _tone_label(tone: Any) -> str:
    value = getattr(tone, "value", tone)
    return _TONE_FOR_LLM.get(str(value or "neutral").lower(), "unclear")


def house_signification_tags(house: int) -> List[str]:
    """Life-theme tags only (body parts are kept in the registry but not sent to the LLM)."""
    row = HOUSE_SIGNIFICATIONS.get(int(house))
    if not row:
        return []
    tags = [str(tag).strip() for tag in (row.significations or ()) if str(tag).strip()]
    if tags:
        return list(dict.fromkeys(tags))
    # Fallback for older registry shapes.
    return [part.strip() for part in str(row.label).split(",") if part.strip()]


def _activated_house_entry(*, subject: str, role: Mapping[str, Any]) -> Tuple[Dict[str, Any], str, str]:
    native = int(role.get("native_house") or 0)
    relative = int(role.get("relative_house") or 0)
    if subject != "self" and not relative and native:
        relative = relative_house_for_native(subject, native)
    signification_house = native if subject == "self" else relative
    tone_key = str(signification_house)
    tone = _tone_label(role.get("outcome_tone"))
    if subject == "self":
        return (
            {
                "house": native,
                "significations": house_signification_tags(native),
            },
            tone_key,
            tone,
        )
    # Relatives: only relative_house + its significations. native_house stays engine-side.
    return (
        {
            "relative_house": relative,
            "significations": house_signification_tags(relative),
        },
        tone_key,
        tone,
    )


def build_minimal_synthesis_context(
    deterministic: Sequence[Mapping[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """Build LLM input from house significations only.

    Returns:
      context: {"themes": [{theme_key, subject, activated_houses, tone_by_house}, ...]}
      theme_by_manifestation_id: join map for merging LLM wording back onto engine rows
    """
    themes: List[Dict[str, Any]] = []
    theme_by_manifestation_id: Dict[str, str] = {}
    seen: Dict[str, str] = {}

    for item in deterministic:
        manifestation_id = str(item.get("manifestation_id") or "")
        if not manifestation_id:
            continue
        subject = str(item.get("subject") or "self")
        activated_houses: List[Dict[str, Any]] = []
        tone_by_house: Dict[str, str] = {}
        for role in item.get("house_roles") or []:
            if not isinstance(role, Mapping):
                continue
            entry, tone_key, tone = _activated_house_entry(subject=subject, role=role)
            if not entry.get("significations"):
                continue
            activated_houses.append(entry)
            tone_by_house[tone_key] = tone
        if not activated_houses:
            continue

        if subject == "self":
            activated_houses.sort(key=lambda row: int(row.get("house") or 0))
        else:
            activated_houses.sort(key=lambda row: int(row.get("relative_house") or 0))

        fingerprint = _canonical({
            "subject": subject,
            "activated_houses": activated_houses,
            "tone_by_house": tone_by_house,
        })
        theme_key = seen.get(fingerprint)
        if theme_key is None:
            theme_key = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
            seen[fingerprint] = theme_key
            themes.append({
                "theme_key": theme_key,
                "subject": subject,
                "activated_houses": activated_houses,
                "tone_by_house": tone_by_house,
            })
        theme_by_manifestation_id[manifestation_id] = theme_key

    themes.sort(key=lambda row: (str(row.get("subject") or ""), str(row.get("theme_key") or "")))
    return {"themes": themes}, theme_by_manifestation_id


def _prompt(context: Mapping[str, Any], locale: str) -> str:
    return f"""You are AstroRoshni's manifestation editor. Your only job is to combine activated house significations into clear, practical life themes.

Rules:
- Combine all activated house significations for each theme.
- Be exhaustive: list as many distinct, plausible bounded life possibilities as the significations allow. Prefer coverage over brevity. Only a few may occur in a person's life, so missing a real possibility makes the tool weaker.
- Cover material, relationship, career/status, family, health/routine, and practical-life angles whenever the house significations support them. Do not stop after 2–3 generic bullets.
- Deduplicate near-identical wording, but keep meaningfully different scenarios.
- Use tone_by_house as authoritative result direction for each house:
  - constructive → favourable / supportive outcomes for that house's significations
  - pressure → difficult, stressful, delayed or obstructive outcomes for that house's significations
  - mixed → both progress and friction are possible for that house
  - unclear → keep wording neutral; do not invent a strongly positive or negative slant
- When houses in one theme have different tones, reflect the mix honestly (e.g. constructive 11 with pressure 6 → gains possible through workload/obligation stress). Do not flatten everything to generic positivity.
- Let the overall theme tone follow the dominant house tones; prefer pressure/mixed wording when those tones are present on key houses.
- Respect the subject. For self, houses are the native houses. For mother, father or spouse, use relative_house significations (how that area reads in the relative's chart), and phrase outcomes about that person.
- Distinguish self, spouse, mother and father clearly.

CRITICAL — Conditional language for relatives:
You do NOT know the user's actual family situation. The user may be unmarried, their spouse may be a homemaker, or a parent may not be alive. You MUST:
  - For spouse: ALWAYS prefix with "If married, …" or "If your spouse is working, …". NEVER write "Your spouse may experience a rise in professional status" — instead write "If married, your spouse may take on a bigger role — whether at work or in managing household responsibilities."
  - For career/authority significations on a spouse: ALWAYS offer BOTH a professional AND a domestic interpretation. Example: "If married, your spouse could face increased responsibilities — a promotion or leadership role if working, or a heavier load managing home and family."
  - For mother/father: use "If applicable, your mother/father may …" when the prediction involves health, travel, or major life changes.
  - The label and summary MUST also use this conditional framing — not just the possibilities list.
- Do not invent houses, planets, dates, dashas, transit facts or unsupported astrological claims.
- Do not mention dasha, transit, evidence or technical house-activation reasoning.
- Keep each possibility practical and conditional: something that may manifest, not a guaranteed event.
- Return JSON only, with exactly one object for each input theme_key.
- Copy each input theme_key exactly into the output. Do not rename keys or wrap the array differently.
- The top-level JSON must be an object with key "themes" (an array). Do not return a bare array.
- Use locale {locale}.

Input:
{_canonical(context)}

JSON shape:
{{"themes":[{{"theme_key":"...","domain":"finance|career|relationship|family|health|property|education|travel|other","label":"...","summary":"...","possibilities":["possibility 1","possibility 2","... as many distinct plausible possibilities as the significations support"],"rationale":["Brief signification-and-tone-based reason only"],"synthesis_strength":"high|well_supported|moderate"}}]}}"""


def _normalize_theme_item(item: Any, *, fallback_theme_key: str = "") -> Optional[Dict[str, Any]]:
    if not isinstance(item, Mapping):
        return None
    theme_key = str(item.get("theme_key") or item.get("manifestation_id") or item.get("id") or fallback_theme_key or "").strip()
    if not theme_key:
        return None
    normalized = dict(item)
    normalized["theme_key"] = theme_key
    # Some models nest the readable fields.
    nested = item.get("theme") if isinstance(item.get("theme"), Mapping) else None
    if nested:
        for key in ("domain", "label", "summary", "possibilities", "rationale", "synthesis_strength"):
            if not normalized.get(key) and nested.get(key):
                normalized[key] = nested[key]
    if isinstance(normalized.get("possibility"), str) and not normalized.get("possibilities"):
        normalized["possibilities"] = [normalized["possibility"]]
    if isinstance(normalized.get("manifestations"), list) and not normalized.get("possibilities"):
        normalized["possibilities"] = normalized["manifestations"]
    return normalized


def _coerce_theme_list(parsed: Any, *, expected_theme_keys: Sequence[str] = ()) -> List[Dict[str, Any]]:
    rows: List[Any] = []
    if isinstance(parsed, list):
        rows = parsed
    elif isinstance(parsed, Mapping):
        for key in (
            "themes",
            "manifestations",
            "life_themes",
            "combined_life_themes",
            "results",
            "items",
            "data",
        ):
            value = parsed.get(key)
            if isinstance(value, list):
                rows = value
                break
            if isinstance(value, Mapping):
                # Single theme object under a known key.
                rows = [value]
                break
        if not rows and any(parsed.get(key) for key in ("label", "summary", "possibilities", "theme_key")):
            rows = [parsed]
    themes: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        fallback = expected_theme_keys[index] if index < len(expected_theme_keys) else ""
        normalized = _normalize_theme_item(row, fallback_theme_key=fallback)
        if normalized:
            themes.append(normalized)
    # If model returned fewer/more items, still try 1:1 positional fill for missing keys.
    if expected_theme_keys and len(themes) == len(expected_theme_keys):
        for index, theme in enumerate(themes):
            if not theme.get("theme_key"):
                theme["theme_key"] = expected_theme_keys[index]
    return themes


def _extract_json(text: str, *, expected_theme_keys: Sequence[str] = ()) -> Dict[str, Any]:
    value = (text or "").strip()
    if value.startswith("```"):
        # Handle ```json / ```JSON fences and trailing fences.
        fence = value.split("\n", 1)
        value = fence[1] if len(fence) > 1 else value[3:]
        value = value.rsplit("```", 1)[0].strip()
    # Prefer object, but also accept a bare array payload.
    obj_start, obj_end = value.find("{"), value.rfind("}")
    arr_start, arr_end = value.find("["), value.rfind("]")
    candidates: List[str] = []
    if obj_start >= 0 and obj_end > obj_start:
        candidates.append(value[obj_start:obj_end + 1])
    if arr_start >= 0 and arr_end > arr_start:
        candidates.append(value[arr_start:arr_end + 1])
    if not candidates:
        raise ValueError("LLM manifestation synthesis did not return JSON")

    last_error: Optional[Exception] = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception as exc:  # noqa: BLE001 - try next candidate
            last_error = exc
            continue
        themes = _coerce_theme_list(parsed, expected_theme_keys=expected_theme_keys)
        if themes:
            return {"themes": themes}
        last_error = ValueError(f"Invalid manifestation synthesis shape: {type(parsed).__name__}")
    if last_error:
        raise ValueError(f"Invalid manifestation synthesis shape ({last_error})") from last_error
    raise ValueError("Invalid manifestation synthesis shape")


def _pick_representative_row(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    today = date.today().isoformat()

    def rank(row: Mapping[str, Any]) -> Tuple[int, str, int]:
        window = row.get("window") if isinstance(row.get("window"), Mapping) else {}
        start = str(window.get("start_date") or "")
        end = str(window.get("end_date") or "")
        contains_today = 0 if start and end and start <= today <= end else 1
        return (contains_today, start, -len(row.get("house_roles") or []))

    return dict(sorted(rows, key=rank)[0])


def _merge(
    deterministic: Sequence[Mapping[str, Any]],
    generated: Mapping[str, Any],
    theme_by_manifestation_id: Mapping[str, str],
) -> Dict[str, Any]:
    """One UI card per LLM theme_key (not one per deterministic window row)."""
    by_theme = {
        str(item.get("theme_key") or item.get("manifestation_id") or ""): item
        for item in (generated.get("themes") or [])
        if isinstance(item, Mapping) and (item.get("theme_key") or item.get("manifestation_id"))
    }
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    orphans: List[Mapping[str, Any]] = []
    for base in deterministic:
        manifestation_id = str(base.get("manifestation_id") or "")
        theme_key = theme_by_manifestation_id.get(manifestation_id)
        if not theme_key:
            orphans.append(base)
            continue
        grouped.setdefault(theme_key, []).append(base)

    merged = []
    for theme_key, rows in grouped.items():
        item = _pick_representative_row(rows)
        candidate = by_theme.get(theme_key, {})
        for key in ("domain", "label", "summary", "possibilities", "rationale", "synthesis_strength"):
            if candidate.get(key):
                item[key] = candidate[key]
        item["theme_key"] = theme_key
        item["source_manifestation_ids"] = [
            str(row.get("manifestation_id"))
            for row in rows
            if row.get("manifestation_id")
        ]
        windows = []
        seen_windows = set()
        for row in rows:
            window = row.get("window") if isinstance(row.get("window"), Mapping) else None
            if not window:
                continue
            marker = f"{window.get('start_date')}:{window.get('end_date')}"
            if marker in seen_windows:
                continue
            seen_windows.add(marker)
            windows.append(dict(window))
        if windows:
            item["related_windows"] = windows
        merged.append(item)

    # Preserve any rows that never entered synthesis (should be rare).
    for base in orphans:
        merged.append(dict(base))

    merged.sort(key=lambda row: (
        str(row.get("subject") or ""),
        str((row.get("window") or {}).get("start_date") or ""),
        str(row.get("label") or ""),
    ))
    return {"manifestations": merged, "synthesis_version": SYNTHESIS_VERSION}


def _theme_cache_payload(theme: Mapping[str, Any]) -> Dict[str, Any]:
    """Stable per-combination cache identity (no chart id, no ephemeral batch)."""
    return {
        "subject": theme.get("subject"),
        "activated_houses": theme.get("activated_houses") or [],
        "tone_by_house": theme.get("tone_by_house") or {},
    }


def _prompt_for_theme(theme: Mapping[str, Any], locale: str) -> str:
    return _prompt({"themes": [theme]}, locale)


def _cached_theme_output(cached: Mapping[str, Any], *, theme_key: str) -> Optional[Dict[str, Any]]:
    if not isinstance(cached, Mapping):
        return None
    if isinstance(cached.get("theme"), Mapping):
        item = dict(cached["theme"])
        item["theme_key"] = theme_key
        return item
    themes = cached.get("themes")
    if isinstance(themes, list) and themes and isinstance(themes[0], Mapping):
        item = dict(themes[0])
        item["theme_key"] = theme_key
        return item
    # Legacy: cached object itself is the theme wording.
    if any(cached.get(key) for key in ("label", "summary", "possibilities", "domain")):
        item = dict(cached)
        item["theme_key"] = theme_key
        return item
    return None


def load_cached_theme_item(theme: Mapping[str, Any], *, locale: str) -> Optional[Dict[str, Any]]:
    """
    Cache-only read for a single theme combination.

    This must not call the LLM; it is used for UI gating (only show cards when
    LLM wording is already cached).
    """
    try:
        provider, model = _model_details()
        theme_key = str(theme.get("theme_key") or "")
        cache_payload = _theme_cache_payload(theme)
        key = _cache_key(cache_payload, locale=locale, provider=provider, model=model)
        cached = _load(key)
        if not cached:
            return None
        return _cached_theme_output(cached, theme_key=theme_key)
    except Exception:
        # Cache gating should be safe: any read issue behaves like a miss.
        logger.exception("Failed to load cached theme item (cache-only)")
        return None


async def _synthesize_single_theme(
    theme: Mapping[str, Any],
    *,
    locale: str,
    provider: str,
    model: str,
) -> Dict[str, Any]:
    theme_key = str(theme.get("theme_key") or "")
    cache_payload = _theme_cache_payload(theme)
    key = _cache_key(cache_payload, locale=locale, provider=provider, model=model)
    cached = await asyncio.to_thread(_load, key)
    if cached:
        hit = _cached_theme_output(cached, theme_key=theme_key)
        if hit:
            if str(os.getenv("ASTRO_LLM_LOG_BODIES") or "").strip().lower() in {"1", "true", "yes", "on"}:
                print(f"[MANIFESTATION_SYNTHESIS] cache hit theme_key={theme_key} cache_key={key[:12]}")
            return hit

    prompt = _prompt_for_theme(theme, locale)
    result = await GeminiChatAnalyzer().generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        llm_log_tag="prediction_manifestation_synthesis",
        request_timeout_s=45,
    )
    if not result.get("success"):
        raise RuntimeError(result.get("error") or "LLM synthesis failed")
    generated = _extract_json(
        result.get("response") or "",
        expected_theme_keys=[theme_key] if theme_key else (),
    )
    themes = generated.get("themes") or []
    if not themes:
        raise ValueError("LLM returned no theme for combination")
    item = dict(themes[0])
    item["theme_key"] = theme_key or str(item.get("theme_key") or "")
    await asyncio.to_thread(
        _save,
        key,
        context=cache_payload,
        output={
            "theme": {
                key_name: item[key_name]
                for key_name in ("domain", "label", "summary", "possibilities", "rationale", "synthesis_strength")
                if item.get(key_name) is not None
            },
            "synthesis_version": SYNTHESIS_VERSION,
        },
        locale=locale,
        provider=provider,
        model=model,
    )
    return item


async def synthesize_manifestations(
    *,
    deterministic: Sequence[Mapping[str, Any]],
    locale: str = "en",
    context: Optional[Mapping[str, Any]] = None,
    theme_by_manifestation_id: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    if context is None or theme_by_manifestation_id is None:
        context, theme_by_manifestation_id = build_minimal_synthesis_context(deterministic)
    themes = [
        theme for theme in (context.get("themes") or [])
        if isinstance(theme, Mapping) and theme.get("theme_key")
    ]
    if not themes:
        return {
            "manifestations": [dict(item) for item in deterministic],
            "synthesis_version": None,
            "synthesis_error": True,
        }

    provider, model = _model_details()
    # Limit concurrency to 2 to avoid exhausting the DB connection pool.
    # Each theme needs a connection for cache read and potentially another for
    # cache write; the pool is typically 4 connections.
    _THEME_SEMAPHORE = asyncio.Semaphore(2)

    async def _throttled(theme):
        async with _THEME_SEMAPHORE:
            return await _synthesize_single_theme(theme, locale=locale, provider=provider, model=model)

    results = await asyncio.gather(
        *[_throttled(theme) for theme in themes],
        return_exceptions=True,
    )

    generated_themes: List[Dict[str, Any]] = []
    failures = 0
    for theme, result in zip(themes, results):
        if isinstance(result, Exception):
            failures += 1
            logger.error(
                "Manifestation synthesis failed for theme_key=%s; leaving deterministic wording",
                theme.get("theme_key"),
                exc_info=result,
            )
            continue
        if isinstance(result, Mapping):
            generated_themes.append(dict(result))

    if not generated_themes:
        return {
            "manifestations": [dict(item) for item in deterministic],
            "synthesis_version": None,
            "synthesis_error": True,
        }

    output = _merge(
        deterministic,
        {"themes": generated_themes},
        theme_by_manifestation_id,
    )
    if failures:
        output["synthesis_error"] = True
        output["synthesis_partial"] = True
    return output
