"""Premium compatibility report pipeline: deterministic base + AI enrichment."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.gemini_errors import transient_gemini_error, user_facing_gemini_error
from ai.structured_analyzer import StructuredAnalysisAnalyzer
from marriage_matching import KundliMatchingEngine


COMPATIBILITY_PREMIUM_REPORT_PROMPT = """
As an expert Vedic astrologer, enrich this premium compatibility report for two charts.

CRITICAL: Return ONLY valid JSON.
{
  "headline": "One-line premium verdict",
  "compatibility_verdict": "Clear relationship decision-grade summary",
  "sections": [
    {
      "key": "overall_foundation",
      "ai_interpretation": "Interpret the static evidence in plain but premium language.",
      "practical_meaning": "What this means in real life for the couple.",
      "decision_guidance": "How they should use this insight."
    },
    {
      "key": "ashtakoota_and_exceptions",
      "ai_interpretation": "Interpret raw vs effective guna score, doshas, and exceptions.",
      "practical_meaning": "What the score does and does not prove.",
      "decision_guidance": "How much weight to give it."
    },
    {
      "key": "manglik_and_dosha_handling",
      "ai_interpretation": "Interpret Manglik pairing and cancellation logic.",
      "practical_meaning": "Practical risk level in married life.",
      "decision_guidance": "What care is actually needed."
    },
    {
      "key": "cross_chart_chemistry",
      "ai_interpretation": "Interpret Moon, Venus-Mars, and attraction chemistry.",
      "practical_meaning": "Emotional rhythm, attraction, and conflict pattern.",
      "decision_guidance": "What helps this chemistry mature."
    },
    {
      "key": "person_one_marriage_support",
      "ai_interpretation": "Interpret D1, D9, and marriage promise for person one.",
      "practical_meaning": "What this person brings into marriage.",
      "decision_guidance": "How their chart should be understood."
    },
    {
      "key": "person_two_marriage_support",
      "ai_interpretation": "Interpret D1, D9, and marriage promise for person two.",
      "practical_meaning": "What this person brings into marriage.",
      "decision_guidance": "How their chart should be understood."
    },
    {
      "key": "navamsa_and_long_term_stability",
      "ai_interpretation": "Interpret D9 maturity, fruit of marriage, and continuity.",
      "practical_meaning": "Long-term stability and adjustment pattern.",
      "decision_guidance": "What kind of maturity this match needs."
    },
    {
      "key": "timing_and_marriage_windows",
      "ai_interpretation": "Interpret current climate, individual readiness, and joint windows.",
      "practical_meaning": "Whether now is supportive or whether delay improves outcomes.",
      "decision_guidance": "What timing strategy is wise."
    },
    {
      "key": "contradictions_and_hidden_factors",
      "ai_interpretation": "Resolve contradictions: e.g. low score but deeper support, or high score but hidden strain.",
      "practical_meaning": "The hidden truth users might miss.",
      "decision_guidance": "What should dominate the final judgment."
    },
    {
      "key": "final_guidance_and_remedies",
      "ai_interpretation": "Synthesize final guidance, behavioral advice, and remedies.",
      "practical_meaning": "How to move forward intelligently.",
      "decision_guidance": "Final decision-grade guidance."
    }
  ],
  "final_summary": "Complete final summary covering promise, compatibility, timing, and practical path forward.",
  "priority_actions": ["Action 1", "Action 2", "Action 3"],
  "follow_up_questions": ["Question 1", "Question 2", "Question 3", "Question 4"]
}

Rules:
1. Use all static evidence provided. Do not invent unsupported astrology facts.
2. Every section must feel premium, specific, and decision-grade.
3. Do not repeat the static evidence mechanically; interpret it.
4. Be balanced: high score is not automatic success, low score is not automatic failure.
5. Use classical vocabulary when relevant but explain what it means in practical life.
6. Cover emotional, physical, family, continuity, and timing angles across the report.
"""


def compatibility_pair_hash(boy_birth: Dict[str, Any], girl_birth: Dict[str, Any]) -> str:
    normalized = json.dumps(
        {
            "boy": {
                "date": boy_birth.get("date"),
                "time": boy_birth.get("time"),
                "place": str(boy_birth.get("place", "")).strip().lower(),
                "latitude": boy_birth.get("latitude"),
                "longitude": boy_birth.get("longitude"),
            },
            "girl": {
                "date": girl_birth.get("date"),
                "time": girl_birth.get("time"),
                "place": str(girl_birth.get("place", "")).strip().lower(),
                "latitude": girl_birth.get("latitude"),
                "longitude": girl_birth.get("longitude"),
            },
        },
        sort_keys=True,
    )
    return hashlib.md5(normalized.encode()).hexdigest()


def ensure_compatibility_premium_reports_table(conn: Any, execute_fn: Any) -> None:
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_compatibility_premium_reports (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            pair_hash TEXT NOT NULL,
            report_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, pair_hash)
        )
        """,
    )


def get_cached_compatibility_report(userid: int, pair_hash: str, get_conn: Any, execute_fn: Any) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_compatibility_premium_reports_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT report_data
            FROM ai_compatibility_premium_reports
            WHERE userid = %s AND pair_hash = %s
            """,
            (userid, pair_hash),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def _window_summary(window: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "start_date": window.get("start_date"),
        "end_date": window.get("end_date"),
        "score": window.get("score"),
        "climate": window.get("climate"),
        "boy_context": window.get("boy_context"),
        "girl_context": window.get("girl_context"),
    }


def build_static_compatibility_report(full: Dict[str, Any], boy_birth: Dict[str, Any], girl_birth: Dict[str, Any]) -> Dict[str, Any]:
    ashtakoota = full.get("ashtakoota", {})
    manglik = ((full.get("manglik") or {}).get("compatibility") or {})
    cross = ((full.get("relationship_indicators") or {}).get("cross_chart") or {})
    timing = full.get("timing_overlay") or {}
    shared = timing.get("shared") or {}
    boy = (full.get("profiles") or {}).get("boy") or {}
    girl = (full.get("profiles") or {}).get("girl") or {}
    recommendation = full.get("recommendation") or {}
    evidence = full.get("evidence_summary") or {}

    sections: List[Dict[str, Any]] = [
        {
            "key": "overall_foundation",
            "title": "Overall Foundation",
            "static_summary": recommendation.get("verdict"),
            "facts": [
                f"Overall compatibility score: {full.get('overall_score', {}).get('percentage', '--')}%",
                f"Engine grade: {full.get('overall_score', {}).get('grade', 'Unknown')}",
                f"Rule profile: {full.get('rule_profile', {}).get('label', 'Unknown')}",
            ],
        },
        {
            "key": "ashtakoota_and_exceptions",
            "title": "Ashtakoota and Exceptions",
            "static_summary": f"Raw guna score is {ashtakoota.get('total_score', '--')}/36 and effective score is {ashtakoota.get('effective_total_score', '--')}/36.",
            "facts": [
                f"Raw total: {ashtakoota.get('total_score', '--')}/36",
                f"Effective total: {ashtakoota.get('effective_total_score', '--')}/36",
                *(ashtakoota.get("effective_critical_issues") or []),
                *(
                    reason
                    for key in ("nadi", "bhakoot")
                    for reason in (((ashtakoota.get("exceptions") or {}).get(key) or {}).get("reasons") or [])
                ),
            ],
        },
        {
            "key": "manglik_and_dosha_handling",
            "title": "Manglik and Dosha Handling",
            "static_summary": manglik.get("description"),
            "facts": [
                f"Pair status: {manglik.get('status', 'Unknown')}",
                f"Pair score: {manglik.get('score', '--')}/10",
                *((manglik.get("exception_reasons") or [])[:4]),
            ],
        },
        {
            "key": "cross_chart_chemistry",
            "title": "Cross-Chart Chemistry",
            "static_summary": f"Cross-chart chemistry is in the {str(cross.get('band', 'Unknown')).lower()} band.",
            "facts": [
                f"Moon harmony: {cross.get('moon_element_match', {}).get('score', '--')}%",
                f"Venus to Mars: {cross.get('venus_to_mars', {}).get('score', '--')}%",
                f"Mars to Venus: {cross.get('mars_to_venus', {}).get('score', '--')}%",
                f"Navamsa pair support: {cross.get('navamsa_pair_support', '--')}%",
                *((cross.get("positive_factors") or [])[:2]),
                *((cross.get("caution_factors") or [])[:2]),
            ],
        },
        {
            "key": "person_one_marriage_support",
            "title": f"{boy_birth.get('name', 'Person 1')} Marriage Support",
            "static_summary": f"D1 7th house is {boy.get('seventh_house', {}).get('d1_strength', {}).get('band', 'Unknown')} and Navamsa is {boy.get('navamsa_synthesis', {}).get('band', 'Unknown')}.",
            "facts": [
                f"D1 7th house score: {boy.get('seventh_house', {}).get('d1_strength', {}).get('score', '--')}%",
                f"D9 7th house score: {boy.get('seventh_house', {}).get('d9_strength', {}).get('score', '--')}%",
                f"Navamsa score: {boy.get('navamsa_synthesis', {}).get('score', '--')}%",
                *((boy.get("navamsa_synthesis", {}).get("supportive_factors") or [])[:2]),
                *((boy.get("navamsa_synthesis", {}).get("challenging_factors") or [])[:2]),
            ],
        },
        {
            "key": "person_two_marriage_support",
            "title": f"{girl_birth.get('name', 'Person 2')} Marriage Support",
            "static_summary": f"D1 7th house is {girl.get('seventh_house', {}).get('d1_strength', {}).get('band', 'Unknown')} and Navamsa is {girl.get('navamsa_synthesis', {}).get('band', 'Unknown')}.",
            "facts": [
                f"D1 7th house score: {girl.get('seventh_house', {}).get('d1_strength', {}).get('score', '--')}%",
                f"D9 7th house score: {girl.get('seventh_house', {}).get('d9_strength', {}).get('score', '--')}%",
                f"Navamsa score: {girl.get('navamsa_synthesis', {}).get('score', '--')}%",
                *((girl.get("navamsa_synthesis", {}).get("supportive_factors") or [])[:2]),
                *((girl.get("navamsa_synthesis", {}).get("challenging_factors") or [])[:2]),
            ],
        },
        {
            "key": "navamsa_and_long_term_stability",
            "title": "Navamsa and Long-Term Stability",
            "static_summary": "D9 shows how the marriage promise matures after commitment and over time.",
            "facts": [
                f"{boy_birth.get('name', 'Person 1')} root vs fruit: {boy.get('navamsa_synthesis', {}).get('root_vs_fruit', 'consistent')}",
                f"{girl_birth.get('name', 'Person 2')} root vs fruit: {girl.get('navamsa_synthesis', {}).get('root_vs_fruit', 'consistent')}",
                f"Pair Navamsa support: {cross.get('navamsa_pair_support', '--')}%",
            ],
        },
        {
            "key": "timing_and_marriage_windows",
            "title": "Timing and Marriage Windows",
            "static_summary": recommendation.get("timing_note"),
            "facts": [
                f"Joint readiness: {shared.get('joint_readiness_score', '--')}%",
                f"Current climate: {shared.get('current_window', {}).get('climate', 'Unknown')}",
                *(
                    [
                        "Next favorable windows:",
                        *[
                            f"{row.get('start_date')} to {row.get('end_date')} ({row.get('score')}%)"
                            for row in (shared.get("next_favorable_windows") or [])[:3]
                        ],
                    ]
                    if shared.get("next_favorable_windows")
                    else []
                ),
            ],
        },
        {
            "key": "contradictions_and_hidden_factors",
            "title": "Contradictions and Hidden Factors",
            "static_summary": "This section resolves where the raw score and the deeper chart evidence disagree.",
            "facts": [
                *((evidence.get("contradictions") or [])[:4]),
                *((evidence.get("caution_factors") or [])[:2]),
            ],
        },
        {
            "key": "final_guidance_and_remedies",
            "title": "Final Guidance and Remedies",
            "static_summary": "Use the deterministic engine verdict, remedies, and timing guidance together before making a decision.",
            "facts": [
                *(recommendation.get("remedies") or []),
                *((evidence.get("positive_factors") or [])[:2]),
            ],
        },
    ]

    return {
        "report_version": "compatibility_premium_v1",
        "generated_at": datetime.now().isoformat(),
        "pair": {
            "person_one_name": boy_birth.get("name", "Person 1"),
            "person_two_name": girl_birth.get("name", "Person 2"),
        },
        "headline": recommendation.get("verdict"),
        "compatibility_verdict": recommendation.get("verdict"),
        "sections": sections,
        "priority_actions": recommendation.get("remedies") or [],
        "static_summary": evidence,
        "timing_snapshot": {
            "current_window": _window_summary(shared.get("current_window") or {}),
            "next_favorable_windows": [_window_summary(row) for row in (shared.get("next_favorable_windows") or [])[:3]],
        },
    }


def merge_premium_ai_report(static_report: Dict[str, Any], ai_payload: Dict[str, Any], terms: Optional[List[Dict[str, Any]]] = None, glossary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ai_sections = {row.get("key"): row for row in (ai_payload.get("sections") or []) if row.get("key")}
    merged_sections = []
    for section in static_report.get("sections", []):
        ai_section = ai_sections.get(section.get("key"), {})
        merged_sections.append(
            {
                **section,
                "ai_interpretation": ai_section.get("ai_interpretation", ""),
                "practical_meaning": ai_section.get("practical_meaning", ""),
                "decision_guidance": ai_section.get("decision_guidance", ""),
            }
        )
    return {
        **static_report,
        "headline": ai_payload.get("headline") or static_report.get("headline"),
        "compatibility_verdict": ai_payload.get("compatibility_verdict") or static_report.get("compatibility_verdict"),
        "final_summary": ai_payload.get("final_summary", ""),
        "priority_actions": ai_payload.get("priority_actions") or static_report.get("priority_actions") or [],
        "follow_up_questions": ai_payload.get("follow_up_questions") or [],
        "sections": merged_sections,
        "terms": terms or [],
        "glossary": glossary or {},
        "ai_generated": True,
    }


async def generate_compatibility_premium_report(
    userid: int,
    boy_chart: Dict[str, Any],
    girl_chart: Dict[str, Any],
    boy_birth: Dict[str, Any],
    girl_birth: Dict[str, Any],
    *,
    language: str,
    force_regenerate: bool,
    effective_cost: int,
    credit_service: Any,
    get_conn: Any,
    execute_fn: Any,
) -> Dict[str, Any]:
    pair_hash = compatibility_pair_hash(boy_birth, girl_birth)

    if not force_regenerate:
        cached = get_cached_compatibility_report(userid, pair_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            return {"ok": True, "report": out, "cached": True}

    full = KundliMatchingEngine().analyze(boy_chart, girl_chart, boy_birth, girl_birth)
    static_report = build_static_compatibility_report(full, boy_birth, girl_birth)
    context = {
        "pair": static_report["pair"],
        "compatibility_engine": full,
        "premium_static_report": static_report,
    }

    analyzer = StructuredAnalysisAnalyzer()
    ai_result: Optional[Dict[str, Any]] = None
    retry_delay = 10
    for attempt in range(3):
        try:
            ai_result = await analyzer.generate_structured_report(
                COMPATIBILITY_PREMIUM_REPORT_PROMPT,
                context,
                language or "english",
            )
        except Exception as exc:
            ai_result = {"success": False, "error": str(exc)}

        if ai_result and ai_result.get("success") and not ai_result.get("is_raw"):
            break
        if ai_result and ai_result.get("success") and ai_result.get("is_raw"):
            ai_result = {"success": False, "error": "Premium compatibility report returned malformed JSON"}

        err_raw = (ai_result or {}).get("error", "") or ""
        if transient_gemini_error(err_raw) and attempt < 2:
            import asyncio
            await asyncio.sleep(retry_delay * (2**attempt))
            continue
        break

    if not ai_result or not ai_result.get("success"):
        err = user_facing_gemini_error((ai_result or {}).get("error", "") or "No response from AI")
        return {"ok": False, "error": err}

    if ai_result.get("is_raw"):
        return {"ok": False, "error": "Premium compatibility report could not be structured."}

    merged = merge_premium_ai_report(
        static_report,
        ai_result.get("data") or {},
        terms=ai_result.get("terms") or [],
        glossary=ai_result.get("glossary") or {},
    )

    if not credit_service.spend_credits(
        userid,
        effective_cost,
        "compatibility_premium_report",
        f"Premium compatibility report for {boy_birth.get('name', 'Person 1')} and {girl_birth.get('name', 'Person 2')}",
    ):
        return {"ok": False, "error": "Credit deduction failed"}

    with get_conn() as conn:
        ensure_compatibility_premium_reports_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_compatibility_premium_reports (userid, pair_hash, report_data, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (userid, pair_hash)
            DO UPDATE SET report_data = EXCLUDED.report_data,
                          updated_at = EXCLUDED.updated_at
            """,
            (userid, pair_hash, json.dumps(merged)),
        )
        conn.commit()

    return {"ok": True, "report": merged, "cached": False, "engine": full}
