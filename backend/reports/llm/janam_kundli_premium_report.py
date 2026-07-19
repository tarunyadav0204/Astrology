"""Janam Kundli LLM layer — language/synthesis only from supplied fact pack."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ai.structured_analyzer import StructuredAnalysisAnalyzer
from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error

from reports.cache.report_hash import build_subject_hash, normalize_language

logger = logging.getLogger(__name__)

JANAM_CHAPTER_PROMPT_VERSION = "janam_kundli_chapters_v4"

# Few chapters = low LLM cost. Deterministic pages are assembled without these.
JANAM_CHAPTER_GROUPS = [
    {
        "key": "karma_persona",
        "section_keys": ["past_life_blueprint", "personality", "emotional_blueprint"],
        "focus": (
            "Synthesize Rahu/Ketu axis, retrograde planets, 9th-lord blessings, ascendant element, "
            "and Moon nakshatra/pada (gana, nadi, yoni, pada lord, Tara Bal of current dasha lords) "
            "into clear language. Use only supplied facts; do not invent nakshatra lore beyond the pack."
        ),
    },
    {
        "key": "life_themes_age",
        "section_keys": ["education_intellect", "career_profession", "wealth_finances", "love_relationships", "health_profiles"],
        "focus": (
            "Write age-bracket-aware life theme pages from house lords and planet placements. "
            "For age 0-17 love page, speak only about friendships/peers — never romance/marriage. "
            "Do not invent industries, dates, or yogas not in facts."
        ),
    },
    {
        "key": "present_and_close",
        "section_keys": ["present_phase", "practical_remedies", "closing_guidance"],
        "focus": (
            "Present-phase page must use exact MD/AD planet names and date strings from facts. "
            "For practical_remedies, use actionable_remedies cards: best weekday/time, mantra + 108 count, "
            "charity items, wear/avoid colors from lifestyle_colors — do not invent new remedies. "
            "Closing may summarize current dasha climate; no fake 12-month transit calendar."
        ),
    },
]


def _ensure_chapter_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_janam_kundli_premium_report_chapters (
            userid INTEGER NOT NULL,
            subject_hash TEXT NOT NULL,
            language TEXT NOT NULL,
            chapter_key TEXT NOT NULL,
            prompt_version TEXT NOT NULL DEFAULT 'janam_kundli_chapters_v1',
            chapter_data JSONB NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (userid, subject_hash, language, chapter_key, prompt_version)
        )
        """,
    )


def get_cached_janam_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    get_conn: Any,
    execute_fn: Any,
) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        _ensure_chapter_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT chapter_data FROM ai_janam_kundli_premium_report_chapters
            WHERE userid=%s AND subject_hash=%s AND language=%s AND chapter_key=%s AND prompt_version=%s
            """,
            (userid, subject_hash, language, chapter_key, JANAM_CHAPTER_PROMPT_VERSION),
        )
        row = cur.fetchone()
    if not row:
        return None
    data = row[0] if not isinstance(row, dict) else row.get("chapter_data")
    if isinstance(data, dict):
        return data
    try:
        return json.loads(data)
    except Exception:
        return None


def upsert_janam_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    chapter_data: Dict[str, Any],
    get_conn: Any,
    execute_fn: Any,
) -> None:
    with get_conn() as conn:
        _ensure_chapter_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_janam_kundli_premium_report_chapters
            (userid, subject_hash, language, chapter_key, prompt_version, chapter_data, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb, NOW())
            ON CONFLICT (userid, subject_hash, language, chapter_key, prompt_version)
            DO UPDATE SET chapter_data = EXCLUDED.chapter_data, updated_at = NOW()
            """,
            (
                userid,
                subject_hash,
                language,
                chapter_key,
                JANAM_CHAPTER_PROMPT_VERSION,
                json.dumps(chapter_data),
            ),
        )
        conn.commit()


def build_static_janam_report(context: Dict[str, Any]) -> Dict[str, Any]:
    from reports.assembly.janam_kundli_i18n import is_hindi

    fact = context.get("fact_pack") or {}
    person = context.get("person") or fact.get("person") or {}
    language = context.get("language") or "english"
    hi = is_hindi(language)
    name = person.get("name") or ("जातक" if hi else "Native")
    sections = []
    for chapter in JANAM_CHAPTER_GROUPS:
        for key in chapter["section_keys"]:
            sections.append({
                "key": key,
                "static_summary": (
                    f"{name} हेतु तथ्य-आधारित संश्लेषण — {key}."
                    if hi
                    else f"Fact-backed synthesis target for {name} — {key}."
                ),
                "facts": {
                    "age_years": fact.get("age_years"),
                    "age_bracket": fact.get("age_bracket"),
                    "ascendant": fact.get("ascendant"),
                    "moon": fact.get("moon"),
                    "life_themes": fact.get("life_themes"),
                    "house_themes": fact.get("house_themes"),
                    "dasha_current": (fact.get("dasha") or {}).get("current"),
                    "yogas_catalog": [
                        {
                            "name": y.get("name"),
                            "category": y.get("category") or y.get("type"),
                            "polarity": y.get("polarity"),
                            "strength": y.get("strength"),
                        }
                        for y in (fact.get("yogas_catalog") or fact.get("yogas_top") or [])
                    ],
                    "doshas": fact.get("doshas"),
                    "remedies": fact.get("remedies"),
                    "planet_matrix": fact.get("planet_matrix"),
                    "sade_sati_current": (fact.get("sade_sati") or {}).get("current_period"),
                },
            })
    from reports.assembly.janam_kundli_labels import label_nakshatra, label_sign

    language = "hindi" if hi else "english"
    asc_name = label_sign((fact.get("ascendant") or {}).get("sign_name"), language)
    moon = fact.get("moon") or {}
    moon_sign = label_sign(moon.get("sign_name"), language)
    moon_nak = label_nakshatra(moon.get("nakshatra"), language)
    return {
        "person": person,
        "headline": f"{name} की जन्म कुंडली" if hi else f"Janam Kundli for {name}",
        "janam_verdict": (
            f"लग्न {asc_name}; चंद्र {moon_sign} {moon_nak}".strip()
            if hi
            else f"Ascendant {asc_name}; Moon {moon_sign} {moon_nak}".strip()
        ),
        "sections": sections,
        "follow_up_questions": [],
    }


def _chapter_prompt(chapter: Dict[str, Any]) -> str:
    section_keys = chapter["section_keys"]
    section_examples = [
        {
            "key": key,
            "opening_summary": "One concise paragraph, 70-110 words, using only supplied facts.",
            "astrological_basis": "Cite only supplied placements/lords/dates, 40-80 words.",
            "interpretation": "Readable synthesis in the requested language, 80-120 words.",
            "practical_guidance": "Practical guidance grounded in facts, 40-80 words.",
            "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
        }
        for key in section_keys
    ]
    return f"""
Generate only this Janam Kundli report chapter.

Return ONLY valid JSON:
{{
  "chapter_key": "{chapter['key']}",
  "headline": "Optional chapter headline",
  "sections": {json.dumps(section_examples, ensure_ascii=False)}
}}

Chapter focus: {chapter['focus']}

Hard rules:
1. Return exactly these section keys: {', '.join(section_keys)}.
2. You are an editor/synthesizer, not an astrologer inventing chart data.
3. Use ONLY supplied fact_pack fields. Never invent planets, houses, yogas, dasha dates, gemstones, or transit periods.
4. If a detail is missing from facts, omit it — do not guess.
5. For present_phase: include Mahadasha/Antardasha planet identifiers that match facts.
   Prefer the display names already localized in facts (e.g. शनि / Saturn). English canonical names
   (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu) may appear beside Hindi names.
6. Copy dasha start/end date strings from facts when present.
7. Write in the requested language (english or hindi).
8. When language is Hindi: use Hindi names for signs (मेष/वृषभ/...), nakshatras (अश्विनी/स्वाति/...),
   and planets (सूर्य/चंद्र/मंगल/...). Do NOT leave English names like Cancer, Libra, Swati, Moon, Saturn
   in Hindi prose unless paired in parentheses after the Hindi name.
9. Exactly 3 short key_takeaways per section.
10. No markdown fences, no tables inside JSON strings.
"""


def _chapter_context(static_report: Dict[str, Any], context: Dict[str, Any], chapter: Dict[str, Any]) -> Dict[str, Any]:
    from reports.assembly.janam_kundli_labels import localize_fact_names

    fact = context.get("fact_pack") or {}
    language = normalize_language(context.get("language") or static_report.get("language") or "english")
    sections_by_key = {s.get("key"): s for s in (static_report.get("sections") or []) if s.get("key")}
    selected = [sections_by_key[k] for k in chapter["section_keys"] if k in sections_by_key]
    fact_slice = {
        "age_years": fact.get("age_years"),
        "age_bracket": fact.get("age_bracket"),
        "ascendant": fact.get("ascendant"),
        "moon": fact.get("moon"),
        "life_themes": fact.get("life_themes"),
        "house_themes": fact.get("house_themes"),
        "planet_matrix": fact.get("planet_matrix"),
        "yogas_catalog": [
            {
                "name": y.get("name"),
                "category": y.get("category") or y.get("type"),
                "polarity": y.get("polarity"),
                "strength": y.get("strength"),
            }
            for y in (fact.get("yogas_catalog") or fact.get("yogas_top") or [])
        ],
        "doshas": fact.get("doshas"),
        "dasha": fact.get("dasha"),
        "sade_sati": {
            "current_period": (fact.get("sade_sati") or {}).get("current_period"),
            "upcoming_period": (fact.get("sade_sati") or {}).get("upcoming_period"),
            "moon_sign_basis": (fact.get("sade_sati") or {}).get("moon_sign_basis"),
        },
        "remedies": fact.get("remedies"),
        "ashtakavarga": fact.get("ashtakavarga"),
    }
    if chapter.get("key") == "karma_persona":
        fact_slice["nakshatra_deep_dive"] = fact.get("nakshatra_deep_dive")
        fact_slice["nakshatra_summary"] = fact.get("nakshatra_summary")
    return {
        "person": static_report.get("person"),
        "chapter_key": chapter["key"],
        "chapter_focus": chapter["focus"],
        "language": language,
        "selected_static_sections": selected,
        "fact_pack": localize_fact_names(fact_slice, language),
    }


def _chapter_concurrency() -> int:
    try:
        return max(1, min(4, int(os.getenv("ASTRO_JANAM_CHAPTER_CONCURRENCY", "3") or 3)))
    except Exception:
        return 3


_PLANET_ALIASES = {
    "sun": ("sun", "surya", "सूर्य"),
    "moon": ("moon", "chandra", "चंद्र", "चन्द्र", "चन्द्रमा"),
    "mars": ("mars", "mangal", "मंगल"),
    "mercury": ("mercury", "budh", "बुध"),
    "jupiter": ("jupiter", "guru", "brihaspati", "गुरु", "बृहस्पति"),
    "venus": ("venus", "shukra", "शुक्र"),
    "saturn": ("saturn", "shani", "शनि"),
    "rahu": ("rahu", "राहु"),
    "ketu": ("ketu", "केतु"),
}


def _planet_mentioned(planet: str, blob: str) -> bool:
    key = str(planet or "").strip().lower()
    if not key:
        return True
    aliases = _PLANET_ALIASES.get(key, (key,))
    return any(alias and alias.lower() in blob for alias in aliases)


def _validate_present_phase_section(section: Dict[str, Any], fact: Dict[str, Any]) -> None:
    cur = (fact.get("dasha") or {}).get("current") or {}
    md = str(((cur.get("mahadasha") or {}).get("planet") or "")).strip()
    ad = str(((cur.get("antardasha") or {}).get("planet") or "")).strip()
    blob = " ".join(
        str(section.get(k) or "")
        for k in ("opening_summary", "astrological_basis", "interpretation", "practical_guidance", "key_takeaways")
    ).lower()
    # key_takeaways may be a list — normalize above via str()
    if md and not _planet_mentioned(md, blob):
        raise RuntimeError(f"present_phase missing mahadasha planet '{md}' from facts")
    if ad and not _planet_mentioned(ad, blob):
        raise RuntimeError(f"present_phase missing antardasha planet '{ad}' from facts")


async def generate_janam_kundli_premium_report(
    userid: int,
    context: Dict[str, Any],
    *,
    language: str,
    force_regenerate: bool,
    effective_cost: int,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
    spend_on_success: bool = False,
) -> Dict[str, Any]:
    import asyncio

    resolved_language = normalize_language(language)
    if resolved_language not in {"english", "hindi"}:
        raise RuntimeError("Janam Kundli v1 supports english and hindi only")

    person = context.get("person") or {}
    fact = context.get("fact_pack") or {}
    subject_hash = build_subject_hash(person, "janam_kundli", resolved_language)
    static_report = build_static_janam_report(context)
    bypass = bool(force_regenerate)

    analyzer = StructuredAnalysisAnalyzer(llm_lane="report")
    chapter_payloads: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    chapters_from_db = 0

    for chapter in JANAM_CHAPTER_GROUPS:
        if not bypass:
            cached = get_cached_janam_chapter(
                userid, subject_hash, resolved_language, chapter["key"], get_conn, execute_fn
            )
            if cached:
                chapters_from_db += 1
                chapter_payloads.append(cached)
                continue
        missing.append(chapter)

    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "non_cached_input_tokens": 0,
        "cache_setup_input_tokens": 0,
        "total_tokens": 0,
        "model": str(getattr(analyzer, "model_name", "") or ""),
        "vendor": str(getattr(analyzer, "vendor", "") or ""),
        "gemini_context_cache": False,
    }

    async def _one(chapter: Dict[str, Any]) -> Dict[str, Any]:
        ai_result: Optional[Dict[str, Any]] = None
        for attempt in range(2):
            try:
                ai_result = await analyzer.generate_structured_report(
                    _chapter_prompt(chapter),
                    _chapter_context(static_report, context, chapter),
                    resolved_language,
                )
            except Exception as exc:
                ai_result = {"success": False, "error": str(exc)}
            if ai_result and ai_result.get("success") and not ai_result.get("is_raw"):
                break
            err_raw = (ai_result or {}).get("error", "") or ""
            if transient_gemini_error(err_raw) and attempt < 1:
                await asyncio.sleep(5 * (2**attempt))
                continue
            break
        if not ai_result or not ai_result.get("success") or ai_result.get("is_raw"):
            raise RuntimeError(
                user_facing_gemini_error(
                    (ai_result or {}).get("error", "") or f"Chapter {chapter['key']} failed"
                )
            )
        payload = ai_result.get("data") or {}
        usage = ai_result.get("usage") if isinstance(ai_result.get("usage"), dict) else {}
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        cached = int(usage.get("cached_tokens") or usage.get("cached_input_tokens") or 0)
        usage_totals["input_tokens"] += inp
        usage_totals["output_tokens"] += out
        usage_totals["cached_input_tokens"] += cached
        usage_totals["non_cached_input_tokens"] += max(inp - cached, 0)
        usage_totals["total_tokens"] += int(usage.get("total_tokens") or (inp + out))
        return payload

    if missing:
        sem = asyncio.Semaphore(_chapter_concurrency())

        async def _guarded(ch: Dict[str, Any]) -> Dict[str, Any]:
            async with sem:
                return await _one(ch)

        generated = await asyncio.gather(*[_guarded(ch) for ch in missing])
        by_key = {p.get("chapter_key"): p for p in generated}
        for chapter in missing:
            payload = by_key.get(chapter["key"])
            if not payload:
                raise RuntimeError(f"Missing LLM chapter payload: {chapter['key']}")
            for section in payload.get("sections") or []:
                if isinstance(section, dict) and section.get("key") == "present_phase":
                    _validate_present_phase_section(section, fact)
            upsert_janam_chapter(
                userid, subject_hash, resolved_language, chapter["key"], payload, get_conn, execute_fn
            )

        chapter_payloads = []
        for chapter in JANAM_CHAPTER_GROUPS:
            cached = get_cached_janam_chapter(
                userid, subject_hash, resolved_language, chapter["key"], get_conn, execute_fn
            )
            if not cached:
                raise RuntimeError(f"Chapter cache miss after generation: {chapter['key']}")
            chapter_payloads.append(cached)

    sections: List[Dict[str, Any]] = []
    for payload in chapter_payloads:
        for section in payload.get("sections") or []:
            if isinstance(section, dict) and section.get("key"):
                if section.get("key") == "present_phase":
                    _validate_present_phase_section(section, fact)
                sections.append(section)

    required = {k for ch in JANAM_CHAPTER_GROUPS for k in ch["section_keys"]}
    got = {s.get("key") for s in sections}
    missing_keys = sorted(required - got)
    if missing_keys:
        raise RuntimeError(f"Janam Kundli LLM missing sections: {', '.join(missing_keys)}")

    report = {
        **static_report,
        "sections": sections,
        "headline": static_report.get("headline"),
        "janam_verdict": static_report.get("janam_verdict"),
        "llm_usage": {
            **usage_totals,
            "chapters_generated": len(missing),
            "chapters_from_db_cache": chapters_from_db,
            "document_cache_hit": False,
        },
        "chapter_cache": {
            "enabled": True,
            "prompt_version": JANAM_CHAPTER_PROMPT_VERSION,
            "chapters": [chapter["key"] for chapter in JANAM_CHAPTER_GROUPS],
            "chapters_generated": len(missing),
            "chapters_from_db_cache": chapters_from_db,
        },
    }

    if spend_on_success and effective_cost and credit_service:
        credit_service.spend_credits(
            userid,
            effective_cost,
            "janam_kundli_report",
            f"Janam Kundli report for {person.get('name') or 'native'}",
        )

    return {"ok": True, "report": report}
