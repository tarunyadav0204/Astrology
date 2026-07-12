"""Premium Wealth Report LLM chapters — single native, chapter-cache pattern."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from ai.structured_analyzer import StructuredAnalysisAnalyzer
from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from reports.cache.report_hash import build_subject_hash, normalize_language

logger = logging.getLogger(__name__)

WEALTH_CHAPTER_PROMPT_VERSION = "wealth_chapters_v1"

WEALTH_CHAPTER_GROUPS: List[Dict[str, Any]] = [
    {
        "key": "executive",
        "section_keys": ["cover", "executive_verdict", "score_architecture"],
        "focus": "Executive wealth verdict in plain language, how D1/D2/D10/dasha layers fit, top supports and risks.",
    },
    {
        "key": "foundation_yogas",
        "section_keys": ["d1_wealth_foundation", "dhana_money_yogas", "indu_arudha_image"],
        "focus": "D1 2nd/11th/lagna/9th foundation, named Dhana/Lakshmi/Raja/Viparita yogas, Indu Lagna and Arudha/HL money image.",
    },
    {
        "key": "psychology_engines",
        "section_keys": ["money_psychology", "jupiter_saturn_karma", "income_engines"],
        "focus": "Moon/Venus/Mercury earn-spend style, Jupiter growth vs Saturn discipline, Sun/Mars/Rahu-Ketu income channels.",
    },
    {
        "key": "manifestation",
        "section_keys": ["d2_hora_manifestation", "d10_career_income", "sources_of_wealth"],
        "focus": "D2 Hora materialization, D10 career-to-cashflow, ranked sources of wealth from evidence.",
    },
    {
        "key": "assets_risk_kp",
        "section_keys": ["assets_property_inheritance", "debt_loss_sudden", "kp_wealth_materialization"],
        "focus": "4th/8th/9th assets and inheritance, 6/8/12 debt and leakage, KP 2nd/11th materialization.",
    },
    {
        "key": "richness",
        "section_keys": ["nakshatra_2_11_lords", "spouse_joint_finances", "speculation_vs_investing"],
        "focus": "2nd and 11th lord nakshatra/pada nature for earn/spend, 7th+D9 spouse/joint finances, speculation vs long-term investing.",
    },
    {
        "key": "timing_theme",
        "section_keys": ["current_dasha_theme", "twelve_month_overview"],
        "focus": "Current MD/AD/PD wealth job with dates; year overview story. Use only supplied dasha facts — never invent periods.",
    },
    {
        "key": "quarters",
        "section_keys": ["quarter_q1", "quarter_q2", "quarter_q3", "quarter_q4"],
        "focus": "Narrate each quarter using the supplied month dasha tables. Do not invent MD/AD/PD names or dates.",
    },
    {
        "key": "action",
        "section_keys": ["peak_caution_windows", "action_plan_remedies", "wealth_roadmap_checklist"],
        "focus": "Peak and caution windows from the year, behavioral remedies first then safe Vedic, 90-day and 12-month checklist.",
    },
]


def _ensure_wealth_chapter_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_wealth_premium_report_chapters (
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


def get_cached_wealth_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    get_conn: Any,
    execute_fn: Any,
) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        _ensure_wealth_chapter_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT chapter_data FROM ai_wealth_premium_report_chapters
            WHERE userid = %s AND subject_hash = %s AND language = %s
              AND chapter_key = %s AND prompt_version = %s
            """,
            (userid, subject_hash, language, chapter_key, WEALTH_CHAPTER_PROMPT_VERSION),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def upsert_wealth_chapter(
    userid: int,
    subject_hash: str,
    language: str,
    chapter_key: str,
    chapter_data: Dict[str, Any],
    get_conn: Any,
    execute_fn: Any,
) -> None:
    with get_conn() as conn:
        _ensure_wealth_chapter_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_wealth_premium_report_chapters
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
                WEALTH_CHAPTER_PROMPT_VERSION,
                json.dumps(chapter_data),
            ),
        )
        conn.commit()


def build_static_wealth_report(context: Dict[str, Any]) -> Dict[str, Any]:
    person = context.get("person") or {}
    wealth = context.get("wealth") or {}
    score = wealth.get("wealth_score")
    yogas = wealth.get("yoga_analysis") or {}
    months = context.get("twelve_month_dasha") or []
    dashas = context.get("current_dashas") or {}
    name = person.get("name") or "Native"

    sections = []
    for chapter in WEALTH_CHAPTER_GROUPS:
        for key in chapter["section_keys"]:
            sections.append({
                "key": key,
                "static_summary": f"Deterministic wealth evidence for {name} — chapter {key}.",
                "facts": {
                    "wealth_score": score,
                    "yogas": yogas,
                    "current_dashas": {
                        "mahadasha": (dashas.get("mahadasha") or {}).get("planet"),
                        "antardasha": (dashas.get("antardasha") or {}).get("planet"),
                        "pratyantardasha": (dashas.get("pratyantardasha") or {}).get("planet"),
                    },
                    "lords_nakshatra": context.get("lords_nakshatra"),
                    "px_wealth": context.get("px_wealth"),
                    "spouse_finance_hints": context.get("spouse_finance_hints"),
                    "indu_lagna": context.get("indu_lagna"),
                    "d10_analysis_keys": list((context.get("d10_analysis") or {}).keys())[:12],
                    "twelve_month_dasha": months,
                    "trading_luck": context.get("trading_luck"),
                    "jaimini_summary": context.get("summaries", {}).get("jaimini"),
                    "kp_summary": context.get("summaries", {}).get("kp"),
                },
            })

    return {
        "person": person,
        "headline": f"Wealth report for {name}",
        "wealth_verdict": f"Wealth score context: {score}",
        "sections": sections,
        "follow_up_questions": [
            "When is the best window to invest in the next 12 months?",
            "How should I balance saving versus growth this year?",
            "What money habits fit this dasha period?",
        ],
    }


def _chapter_prompt(chapter: Dict[str, Any]) -> str:
    section_keys = chapter["section_keys"]
    section_examples = [
        {
            "key": key,
            "opening_summary": "One concise premium paragraph for this page, 70 to 110 words.",
            "astrological_basis": "Specific chart evidence for this page, 50 to 90 words.",
            "interpretation": "Master astrologer interpretation in the requested language, 90 to 130 words.",
            "practical_guidance": "Concrete money advice, 50 to 90 words.",
            "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
        }
        for key in section_keys
    ]
    return f"""
Generate only this wealth-report chapter.

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
4. For remedies: behavioral and timing first; gemstones conditional.
5. JSON safety: no markdown fences, no raw tables.
6. Exactly 3 short key_takeaways per section.
7. Narrative first — readable wealth astrology, not calculator dump.
8. Timing chapters must copy MD/AD/PD names from twelve_month_dasha / current_dashas evidence.
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
    }
    if shared_context_cached:
        # Shared evidence lives in Gemini CachedContent; keep only chapter-local hints.
        payload["shared_context_cached"] = True
        payload["shared_context_keys"] = [
            "person",
            "wealth_score",
            "yoga_analysis",
            "income_sources",
            "lords_nakshatra",
            "current_dashas",
            "twelve_month_dasha",
            "px_wealth",
            "spouse_finance_hints",
            "indu_lagna",
            "jaimini_summary",
            "trading_luck",
            "static_sections_by_key",
        ]
        return payload

    payload.update({
        "wealth_score": (context.get("wealth") or {}).get("wealth_score"),
        "yoga_analysis": (context.get("wealth") or {}).get("yoga_analysis"),
        "income_sources": (context.get("wealth") or {}).get("income_sources"),
        "lords_nakshatra": context.get("lords_nakshatra"),
        "current_dashas": context.get("current_dashas"),
        "twelve_month_dasha": context.get("twelve_month_dasha"),
        "px_wealth": context.get("px_wealth"),
        "spouse_finance_hints": context.get("spouse_finance_hints"),
        "indu_lagna": context.get("indu_lagna"),
        "jaimini_summary": (context.get("summaries") or {}).get("jaimini"),
        "trading_luck": context.get("trading_luck"),
    })
    return payload


def _shared_chapter_cache_payload(static_report: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Native-level evidence reused across wealth chapter LLM calls."""
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
    wealth = context.get("wealth") or {}
    return {
        "person": static_report.get("person"),
        "headline": static_report.get("headline"),
        "wealth_verdict": static_report.get("wealth_verdict"),
        "wealth_score": wealth.get("wealth_score"),
        "yoga_analysis": wealth.get("yoga_analysis"),
        "income_sources": wealth.get("income_sources"),
        "lords_nakshatra": context.get("lords_nakshatra"),
        "current_dashas": context.get("current_dashas"),
        "twelve_month_dasha": context.get("twelve_month_dasha"),
        "px_wealth": context.get("px_wealth"),
        "spouse_finance_hints": context.get("spouse_finance_hints"),
        "indu_lagna": context.get("indu_lagna"),
        "jaimini_summary": (context.get("summaries") or {}).get("jaimini"),
        "trading_luck": context.get("trading_luck"),
        "static_sections_by_key": sections,
    }


def _chapter_concurrency() -> int:
    try:
        return max(1, min(10, int(os.getenv("ASTRO_WEALTH_CHAPTER_CONCURRENCY", "5") or 5)))
    except Exception:
        return 5


async def generate_wealth_premium_report(
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
    subject_hash = build_subject_hash(person, "wealth", resolved_language)
    static_report = build_static_wealth_report(context)
    bypass = bool(force_regenerate)

    analyzer = StructuredAnalysisAnalyzer(llm_lane="report")
    chapter_payloads: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    chapters_from_db = 0

    for chapter in WEALTH_CHAPTER_GROUPS:
        if not bypass:
            cached = get_cached_wealth_chapter(
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
            cache_label="wealth_chapters",
            cache_enabled_env="ASTRO_WEALTH_REPORT_CONTEXT_CACHE",
            system_instruction=(
                "You are writing chapters of a premium Vedic wealth report for one native. "
                "Use the cached shared evidence for wealth score, yogas, dashas, Indu/AL/HL, "
                "and income sources. Never invent placements, yogas, or dasha dates. "
                "Return only the requested chapter JSON."
            ),
            ttl_env_name="ASTRO_WEALTH_REPORT_CACHE_TTL_S",
        )
        shared_context_cached = cached_model is not None
        if shared_context_cached:
            logger.info(
                "wealth_chapters cache active chars=%s setup_tokens=%s missing_chapters=%s",
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
                upsert_wealth_chapter(
                    userid, subject_hash, resolved_language, chapter["key"], payload, get_conn, execute_fn
                )

            chapter_payloads = []
            for chapter in WEALTH_CHAPTER_GROUPS:
                cached = get_cached_wealth_chapter(
                    userid, subject_hash, resolved_language, chapter["key"], get_conn, execute_fn
                )
                chapter_payloads.append(cached or {"chapter_key": chapter["key"], "sections": []})
    finally:
        await delete_gemini_context_cache(cache_resource, cache_label="wealth_chapters")

    sections: List[Dict[str, Any]] = []
    for payload in chapter_payloads:
        for section in payload.get("sections") or []:
            if isinstance(section, dict) and section.get("key"):
                sections.append(section)

    report = {
        **static_report,
        "sections": sections,
        "headline": static_report.get("headline"),
        "wealth_verdict": static_report.get("wealth_verdict"),
        "llm_usage": {
            **usage_totals,
            "chapters_generated": len(missing),
            "chapters_from_db_cache": chapters_from_db,
            "document_cache_hit": False,
        },
        "chapter_cache": {
            "enabled": True,
            "prompt_version": WEALTH_CHAPTER_PROMPT_VERSION,
            "chapters": [chapter["key"] for chapter in WEALTH_CHAPTER_GROUPS],
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
            "wealth_report",
            f"Wealth report for {person.get('name') or 'native'}",
        )

    return {"ok": True, "report": report}
