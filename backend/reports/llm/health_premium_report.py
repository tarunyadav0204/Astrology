"""Premium Health Report LLM chapters — single native, chapter-cache pattern."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ai.structured_analyzer import StructuredAnalysisAnalyzer
from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from reports.cache.report_hash import build_subject_hash, normalize_language
from reports.constants import MEDICAL_DISCLAIMER

logger = logging.getLogger(__name__)

HEALTH_CHAPTER_PROMPT_VERSION = "health_chapters_v5"

HEALTH_CHAPTER_GROUPS: List[Dict[str, Any]] = [
    {
        "key": "executive",
        "section_keys": ["cover", "executive_verdict", "score_architecture"],
        "focus": (
            "Cover with medical disclaimer, executive vitality verdict naming the top priority body zones "
            "from body_zone_map, and how D1/D9/D30/dasha layers fit together."
        ),
    },
    {
        "key": "constitution_vitality",
        "section_keys": [
            "constitution_dosha",
            "vitality_immunity",
            "health_houses_d1",
            "planet_body_systems",
        ],
        "focus": (
            "Constitution/dosha, vitality/immunity, houses 1/6/8/12 with correct aspects only, and especially "
            "planet_body_systems: narrate body_zone_map.priority_zones and event_patterns with concrete anatomy "
            "(e.g. sinuses, vascular pressure tone, feet/rest via 12th, surgery susceptibility). "
            "Fuse house meaning × sign on house × lord company. Never confuse lord affliction with house aspect."
        ),
    },
    {
        "key": "domains",
        "section_keys": [
            "mental_emotional_health",
            "digestion_metabolism_recovery",
            "acute_vs_chronic_pattern",
            "health_yogas_afflictions",
            "lifestyle_triggers",
        ],
        "focus": (
            "Mental/emotional, digestion, acute vs chronic, yogas, lifestyle — always tie flares back to "
            "body_zone_map event_patterns and named zones (sinus/face, vascular tone, 6th-lord accident themes) when evidence supports."
        ),
    },
    {
        "key": "confirmation",
        "section_keys": [
            "d9_resilience",
            "d30_confirmation",
            "badhaka_mrityu_bhaga",
            "kp_health_materialization",
            "nakshatra_health_nature",
        ],
        "focus": (
            "D9/D30/Badhaka/KP/nakshatra confirmation of the SAME priority body zones — do not invent new unrelated anatomy."
        ),
    },
    {
        "key": "timing_theme",
        "section_keys": ["current_dasha_health_theme", "twelve_month_overview"],
        "focus": (
            "Current MD/AD/PD health theme with supplied dates; say which priority zones the dasha planets activate. "
            "Use only supplied dasha facts — never invent periods."
        ),
    },
    {
        "key": "quarters",
        "section_keys": ["quarter_q1", "quarter_q2", "quarter_q3", "quarter_q4"],
        "focus": (
            "Narrate each quarter using supplied month dasha tables and name which body zones need pacing. "
            "Do not invent MD/AD/PD names or dates."
        ),
    },
    {
        "key": "action",
        "section_keys": [
            "peak_caution_windows",
            "action_plan_remedies",
            "ninety_day_checklist",
            "safety_and_next_steps",
        ],
        "focus": (
            "Action and checklist must target the top body_zone_map zones (e.g. sinus care, vascular pacing, "
            "limb/joint protection). Repeat medical disclaimer; never claim the native 'has' a disease."
        ),
    },
]


def _ensure_health_chapter_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_health_premium_report_chapters (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            subject_hash TEXT NOT NULL,
            language TEXT NOT NULL,
            chapter_key TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            chapter_data TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, subject_hash, language, chapter_key, prompt_version)
        )
        """,
    )


def get_cached_health_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    get_conn: Any,
    execute_fn: Any,
) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        _ensure_health_chapter_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT chapter_data FROM ai_health_premium_report_chapters
            WHERE userid = %s AND subject_hash = %s AND language = %s
              AND chapter_key = %s AND prompt_version = %s
            """,
            (userid, subject_hash, language, chapter_key, HEALTH_CHAPTER_PROMPT_VERSION),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def upsert_health_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    chapter_data: Dict[str, Any],
    get_conn: Any,
    execute_fn: Any,
) -> None:
    with get_conn() as conn:
        _ensure_health_chapter_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_health_premium_report_chapters
                (userid, subject_hash, language, chapter_key, prompt_version, chapter_data, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (userid, subject_hash, language, chapter_key, prompt_version)
            DO UPDATE SET chapter_data = EXCLUDED.chapter_data, updated_at = CURRENT_TIMESTAMP
            """,
            (
                userid,
                subject_hash,
                language,
                chapter_key,
                HEALTH_CHAPTER_PROMPT_VERSION,
                json.dumps(chapter_data),
            ),
        )
        conn.commit()


def build_static_health_report(context: Dict[str, Any]) -> Dict[str, Any]:
    person = context.get("person") or {}
    health = context.get("health") or {}
    score = health.get("health_score")
    constitution = health.get("constitution_type")
    months = context.get("twelve_month_dasha") or []
    dashas = context.get("current_dashas") or {}
    name = person.get("name") or "Native"
    disclaimer = context.get("medical_disclaimer") or MEDICAL_DISCLAIMER

    sections = []
    for chapter in HEALTH_CHAPTER_GROUPS:
        for key in chapter["section_keys"]:
            sections.append({
                "key": key,
                "static_summary": f"Deterministic health evidence for {name} — chapter {key}.",
                "facts": {
                    "medical_disclaimer": disclaimer,
                    "health_score": score,
                    "constitution_type": constitution,
                    "element_balance": health.get("element_balance"),
                    "yoga_analysis": health.get("yoga_analysis"),
                    "health_remedies": health.get("health_remedies"),
                    "health_agent": context.get("health_agent"),
                    "vitality_analysis": context.get("vitality_analysis"),
                    "disease_indicators": context.get("disease_indicators"),
                    "mental_health": context.get("mental_health"),
                    "body_parts": context.get("body_parts"),
                    "badhaka_analysis": context.get("badhaka_analysis"),
                    "mrityu_bhaga_analysis": context.get("mrityu_bhaga_analysis"),
                    "d30_analysis": context.get("d30_analysis"),
                    "lords_nakshatra": context.get("lords_nakshatra"),
                    "planet_system_ranks": context.get("planet_system_ranks"),
                    "attention_houses": context.get("attention_houses"),
                    "body_zone_map": context.get("body_zone_map"),
                    "current_dashas": {
                        "mahadasha": (dashas.get("mahadasha") or {}).get("planet"),
                        "antardasha": (dashas.get("antardasha") or {}).get("planet"),
                        "pratyantardasha": (dashas.get("pratyantardasha") or {}).get("planet"),
                    },
                    "twelve_month_dasha": months,
                    "jaimini_summary": context.get("summaries", {}).get("jaimini"),
                    "kp_summary": context.get("summaries", {}).get("kp"),
                },
            })

    return {
        "person": person,
        "headline": f"Health report for {name}",
        "health_verdict": f"Health score context: {score}; constitution: {constitution}",
        "medical_disclaimer": disclaimer,
        "sections": sections,
        "follow_up_questions": [
            "Which months in the next year need extra rest and recovery care?",
            "How should I support digestion and sleep during the current dasha?",
            "What lifestyle habits best match this constitution?",
        ],
    }


def _chapter_prompt(chapter: Dict[str, Any]) -> str:
    section_keys = chapter["section_keys"]
    section_examples = [
        {
            "key": key,
            "opening_summary": "One concise premium paragraph for this page, 70 to 110 words.",
            "astrological_basis": "Specific chart evidence for this page, 50 to 90 words.",
            "interpretation": "Master astrologer wellness interpretation in the requested language, 90 to 130 words.",
            "practical_guidance": "Concrete lifestyle guidance (not medical advice), 50 to 90 words.",
            "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
        }
        for key in section_keys
    ]
    return f"""
Generate only this health-report chapter.

Return ONLY valid JSON:
{{
  "chapter_key": "{chapter['key']}",
  "headline": "Optional chapter headline",
  "sections": {json.dumps(section_examples, ensure_ascii=False)}
}}

Chapter focus: {chapter['focus']}

Rules:
1. Return exactly these section keys: {', '.join(section_keys)}.
2. Use only supplied deterministic evidence. Do not invent placements, yogas, dashas, or dates.
3. Write in the requested language.
4. NEVER diagnose disease, prescribe medicine, or claim medical certainty.
5. Always treat this as astrological wellness guidance. Include a short reminder of the medical disclaimer
   on cover, executive_verdict, action_plan_remedies, and safety_and_next_steps.
6. Remedies: sleep, diet rhythm, stress hygiene, exercise pacing, and safe Vedic habits first; gemstones only as optional and conditional.
7. JSON safety: no markdown fences, no raw tables.
8. Exactly 3 short key_takeaways per section.
9. Narrative first — readable health astrology, not calculator dump.
10. Timing chapters must copy MD/AD/PD names from twelve_month_dasha / current_dashas evidence.
11. ASPECT ACCURACY IS CRITICAL. Use attention_houses[*].aspecting_planets and attention_houses[*].residents
    as the only source for who aspects or occupies a house.
    - "Planet aspects house H" only if that planet appears in house H's aspecting_planets list.
    - "Planet occupies house H" only if it appears in residents.
    - Affliction to a house lord is NOT the same as an aspect on that house. If Saturn aspects the
      Lagna lord in another house, say that explicitly — do NOT write "1st house is aspected by Saturn"
      unless Saturn is listed under house 1 aspecting_planets.
    - Never invent Saturn/Rahu/Mars aspects on houses 1/6/8/12 that are missing from the evidence.
12. BODY PERSONALIZATION IS MANDATORY. Use body_zone_map as the anatomy source of truth:
    - Name concrete zones from priority_zones / top_zone_names (sinuses, throat, vascular/blood-pressure tone,
      hips/thighs/feet, nerves, etc.) — not only generic "systems".
    - Narrate event_patterns when present (accident/injury, surgery, sinus/face, vascular pressure,
      12th feet/rest/hospitalization, chronic/hidden) as chart susceptibilities with evidence,
      never as "you have disease X".
    - Explain links the way a jyotishi would: e.g. 6th lord with Mars/Rahu → accident risk;
      2nd-house malefics → sinus/face/throat flares; Mars with dusthana pressure → surgery themes;
      12th house × rashi → feet/rest/hospitalization; 6th-house rashi → disease-site flavour;
      9th → hips/thighs only (Kalapurusha). Never map 9th lord to feet — that is not classical.
    - Executive verdict, planet_body_systems, acute_vs_chronic, timing, and action chapters must all reuse the
      same top zones so the report feels like one personalized reading.
    - Phrase as "chart indicates susceptibility / attention themes" + lifestyle monitoring — never diagnose.
"""


def _chapter_context(
    static_report: Dict[str, Any],
    context: Dict[str, Any],
    chapter: Dict[str, Any],
    *,
    shared_context_cached: bool = False,
) -> Dict[str, Any]:
    sections_by_key = {
        s.get("key"): s for s in (static_report.get("sections") or []) if s.get("key")
    }
    selected = [sections_by_key[k] for k in chapter["section_keys"] if k in sections_by_key]
    payload: Dict[str, Any] = {
        "person": static_report.get("person"),
        "chapter_key": chapter["key"],
        "chapter_focus": chapter["focus"],
        "selected_static_sections": selected,
        "medical_disclaimer": static_report.get("medical_disclaimer") or MEDICAL_DISCLAIMER,
    }
    if shared_context_cached:
        payload["shared_context_cached"] = True
        payload["shared_context_keys"] = [
            "person",
            "medical_disclaimer",
            "health_score",
            "constitution_type",
            "yoga_analysis",
            "health_agent",
            "vitality_analysis",
            "disease_indicators",
            "mental_health",
            "body_parts",
            "body_zone_map",
            "d30_analysis",
            "badhaka_analysis",
            "mrityu_bhaga_analysis",
            "lords_nakshatra",
            "current_dashas",
            "twelve_month_dasha",
            "static_sections_by_key",
        ]
        return payload

    health = context.get("health") or {}
    payload.update({
        "health_score": health.get("health_score"),
        "constitution_type": health.get("constitution_type"),
        "element_balance": health.get("element_balance"),
        "yoga_analysis": health.get("yoga_analysis"),
        "health_remedies": health.get("health_remedies"),
        "health_agent": context.get("health_agent"),
        "vitality_analysis": context.get("vitality_analysis"),
        "disease_indicators": context.get("disease_indicators"),
        "mental_health": context.get("mental_health"),
        "body_parts": context.get("body_parts"),
        "body_zone_map": context.get("body_zone_map"),
        "d30_analysis": context.get("d30_analysis"),
        "badhaka_analysis": context.get("badhaka_analysis"),
        "mrityu_bhaga_analysis": context.get("mrityu_bhaga_analysis"),
        "lords_nakshatra": context.get("lords_nakshatra"),
        "planet_system_ranks": context.get("planet_system_ranks"),
        "attention_houses": context.get("attention_houses"),
        "current_dashas": context.get("current_dashas"),
        "twelve_month_dasha": context.get("twelve_month_dasha"),
        "jaimini_summary": (context.get("summaries") or {}).get("jaimini"),
        "kp_summary": (context.get("summaries") or {}).get("kp"),
    })
    return payload


def _shared_chapter_cache_payload(static_report: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    sections = {}
    for section in static_report.get("sections") or []:
        key = section.get("key")
        if not key:
            continue
        sections[key] = {
            "title": section.get("title"),
            "static_summary": section.get("static_summary"),
            "facts": section.get("facts") or [],
        }
    health = context.get("health") or {}
    return {
        "person": static_report.get("person"),
        "headline": static_report.get("headline"),
        "health_verdict": static_report.get("health_verdict"),
        "medical_disclaimer": static_report.get("medical_disclaimer") or MEDICAL_DISCLAIMER,
        "health_score": health.get("health_score"),
        "constitution_type": health.get("constitution_type"),
        "element_balance": health.get("element_balance"),
        "yoga_analysis": health.get("yoga_analysis"),
        "health_remedies": health.get("health_remedies"),
        "health_agent": context.get("health_agent"),
        "vitality_analysis": context.get("vitality_analysis"),
        "disease_indicators": context.get("disease_indicators"),
        "mental_health": context.get("mental_health"),
        "body_parts": context.get("body_parts"),
        "body_zone_map": context.get("body_zone_map"),
        "d30_analysis": context.get("d30_analysis"),
        "badhaka_analysis": context.get("badhaka_analysis"),
        "mrityu_bhaga_analysis": context.get("mrityu_bhaga_analysis"),
        "lords_nakshatra": context.get("lords_nakshatra"),
        "planet_system_ranks": context.get("planet_system_ranks"),
        "attention_houses": context.get("attention_houses"),
        "current_dashas": context.get("current_dashas"),
        "twelve_month_dasha": context.get("twelve_month_dasha"),
        "jaimini_summary": (context.get("summaries") or {}).get("jaimini"),
        "kp_summary": (context.get("summaries") or {}).get("kp"),
        "static_sections_by_key": sections,
    }


def _chapter_concurrency() -> int:
    try:
        return max(1, min(10, int(os.getenv("ASTRO_HEALTH_CHAPTER_CONCURRENCY", "5") or 5)))
    except Exception:
        return 5


async def generate_health_premium_report(
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

    from ai.gemini_context_cache import create_gemini_context_cache, delete_gemini_context_cache
    from utils.admin_settings import CHAT_LLM_GEMINI

    resolved_language = normalize_language(language)
    person = context.get("person") or {}
    subject_hash = build_subject_hash(person, "health", resolved_language)
    static_report = build_static_health_report(context)
    bypass = bool(force_regenerate)

    analyzer = StructuredAnalysisAnalyzer(llm_lane="report")
    chapter_payloads: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    chapters_from_db = 0

    for chapter in HEALTH_CHAPTER_GROUPS:
        if not bypass:
            cached = get_cached_health_chapter(
                userid, subject_hash, resolved_language, chapter["key"], get_conn, execute_fn
            )
            if cached:
                chapters_from_db += 1
                chapter_payloads.append(cached)
                continue
        missing.append(chapter)

    cache_resource = None
    cached_model = None
    shared_context_cached = False
    cache_setup_input_tokens = 0
    if missing and getattr(analyzer, "vendor", None) == CHAT_LLM_GEMINI:
        cache_resource, cached_model, cache_chars, cache_setup_input_tokens = await create_gemini_context_cache(
            llm_provider=str(getattr(analyzer, "vendor", "") or ""),
            model_name=str(getattr(analyzer, "model_name", "") or ""),
            cache_payload=_shared_chapter_cache_payload(static_report, context),
            cache_label="health_chapters",
            cache_enabled_env="ASTRO_HEALTH_REPORT_CONTEXT_CACHE",
            system_instruction=(
                "You are writing chapters of a premium Vedic health and wellness report for one native. "
                "Use the cached shared evidence for health score, constitution, D30, dashas, and body-system cues. "
                "Never invent placements, yogas, or dasha dates. Never diagnose disease or prescribe medicine. "
                "Return only the requested chapter JSON."
            ),
            ttl_env_name="ASTRO_HEALTH_REPORT_CACHE_TTL_S",
        )
        shared_context_cached = cached_model is not None
        if shared_context_cached:
            logger.info(
                "health_chapters cache active chars=%s setup_tokens=%s missing_chapters=%s",
                cache_chars,
                cache_setup_input_tokens,
                len(missing),
            )

    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "non_cached_input_tokens": 0,
        "cache_setup_input_tokens": int(cache_setup_input_tokens or 0) if shared_context_cached else 0,
        "total_tokens": 0,
        "model": str(getattr(analyzer, "model_name", "") or ""),
        "vendor": str(getattr(analyzer, "vendor", "") or ""),
        "gemini_context_cache": shared_context_cached,
    }

    async def _one(chapter: Dict[str, Any]) -> Dict[str, Any]:
        ai_result: Optional[Dict[str, Any]] = None
        for attempt in range(2):
            try:
                ai_result = await analyzer.generate_structured_report(
                    _chapter_prompt(chapter),
                    _chapter_context(
                        static_report,
                        context,
                        chapter,
                        shared_context_cached=shared_context_cached,
                    ),
                    resolved_language,
                    model_override=cached_model,
                    shared_context_cached=shared_context_cached,
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
        payload["_llm_usage"] = usage
        return payload

    try:
        if missing:
            sem = asyncio.Semaphore(_chapter_concurrency())

            async def _guarded(ch: Dict[str, Any]) -> Dict[str, Any]:
                async with sem:
                    return await _one(ch)

            generated = await asyncio.gather(*[_guarded(ch) for ch in missing])
            by_key = {p.get("chapter_key"): p for p in generated}
            for chapter in missing:
                payload = by_key.get(chapter["key"]) or {"chapter_key": chapter["key"], "sections": []}
                payload.pop("_llm_usage", None)
                upsert_health_chapter(
                    userid, subject_hash, resolved_language, chapter["key"], payload, get_conn, execute_fn
                )

            chapter_payloads = []
            for chapter in HEALTH_CHAPTER_GROUPS:
                cached = get_cached_health_chapter(
                    userid, subject_hash, resolved_language, chapter["key"], get_conn, execute_fn
                )
                chapter_payloads.append(cached or {"chapter_key": chapter["key"], "sections": []})
    finally:
        await delete_gemini_context_cache(cache_resource, cache_label="health_chapters")

    sections: List[Dict[str, Any]] = []
    for payload in chapter_payloads:
        for section in payload.get("sections") or []:
            if isinstance(section, dict) and section.get("key"):
                sections.append(section)

    report = {
        **static_report,
        "sections": sections,
        "headline": static_report.get("headline"),
        "health_verdict": static_report.get("health_verdict"),
        "medical_disclaimer": static_report.get("medical_disclaimer") or MEDICAL_DISCLAIMER,
        "llm_usage": {
            **usage_totals,
            "chapters_generated": len(missing),
            "chapters_from_db_cache": chapters_from_db,
            "document_cache_hit": False,
        },
        "chapter_cache": {
            "enabled": True,
            "prompt_version": HEALTH_CHAPTER_PROMPT_VERSION,
            "chapters": [chapter["key"] for chapter in HEALTH_CHAPTER_GROUPS],
            "gemini_context_cache": shared_context_cached,
            "concurrency": _chapter_concurrency(),
            "chapters_generated": len(missing),
            "chapters_from_db_cache": chapters_from_db,
        },
    }

    if spend_on_success and effective_cost and credit_service:
        credit_service.spend_credits(
            userid,
            effective_cost,
            "health_report",
            f"Health report for {person.get('name') or 'native'}",
        )

    return {"ok": True, "report": report}
