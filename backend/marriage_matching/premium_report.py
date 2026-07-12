"""Premium compatibility report pipeline: deterministic base + AI enrichment."""

from __future__ import annotations

import hashlib
import json
import os
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
7. JSON safety: every value must be a plain string or array item. Do not use unescaped double quotes inside text. Do not use markdown tables, bullet characters, or multi-line strings.
8. Prefer the section keys provided in premium_static_report.sections. For each section, return opening_summary, astrological_basis, interpretation, practical_guidance, and key_takeaways.
"""

PARTNERSHIP_CHAPTER_PROMPT_VERSION = "partnership_chapters_v6_nakshatra_nature"

PARTNERSHIP_CHAPTER_GROUPS = [
    {
        "key": "executive",
        "section_keys": ["cover", "executive_verdict", "score_architecture"],
        "focus": "Executive decision in plain language, how compatibility layers fit together, strongest supports, strongest risks. Prefer readable astrology narrative over raw scores.",
    },
    {
        "key": "nakshatra_nature",
        "section_keys": ["nakshatra_moon_nature", "nakshatra_venus_seventh_lord"],
        "focus": (
            "Dedicated nakshatra chapter for both natives. For Moon, Venus, and the 7th lord, explain the core nature "
            "and behavioral characteristics of that nakshatra and the specific pada coloring — not deity name-drops alone. "
            "Show how each person's Moon nakshatra/pada shapes daily emotional style, how Venus nakshatra/pada shapes "
            "desire and affection, and how 7th-lord nakshatra/pada shapes partner-seeking and bond style. Then contrast "
            "the pair: where the two natures mesh, where they friction, and how to live with the difference. "
            "Use the supplied relationship_nakshatra evidence. Keep each placement named to its native."
        ),
    },
    {
        "key": "emotional_physical",
        "section_keys": ["moon_emotional_rhythm", "communication_mental_rapport", "physical_chemistry_biology"],
        "focus": "Emotional language, communication repair style, Moon rhythm, Venus-Mars attraction, and biological compatibility without fetal-sex prediction.",
    },
    {
        "key": "person_a_d1",
        "section_keys": ["person_a_d1_marriage_foundation"],
        "native_role": "boy",
        "focus": "Write only about person_one / the boy native. Use only their D1 7th house, 7th lord, Venus/Jupiter, and marriage-support evidence. Never mention or borrow the other person's planets or houses.",
    },
    {
        "key": "person_b_d1",
        "section_keys": ["person_b_d1_marriage_foundation"],
        "native_role": "girl",
        "focus": "Write only about person_two / the girl native. Use only their D1 7th house, 7th lord, Venus/Jupiter, and marriage-support evidence. Never mention or borrow the other person's planets or houses.",
    },
    {
        "key": "jaimini_manifestation",
        "section_keys": ["jaimini_upapada_environment", "darapada_a7_manifestation"],
        "focus": "Jaimini UL and A7 for both people. Every UL/A7 statement must explicitly name which person it belongs to.",
    },
    {
        "key": "person_a_d9",
        "section_keys": ["person_a_d9_navamsa"],
        "native_role": "boy",
        "focus": "Write only about person_one / the boy native D9 Navamsa maturity. Never attribute the other person's D9 placements to them.",
    },
    {
        "key": "person_b_d9",
        "section_keys": ["person_b_d9_navamsa"],
        "native_role": "girl",
        "focus": "Write only about person_two / the girl native D9 Navamsa maturity. Never attribute the other person's D9 placements to them.",
    },
    {
        "key": "navamsa_pair",
        "section_keys": ["navamsa_pair_durability"],
        "focus": "Pair-level D9 durability. When citing either native, keep their name attached to their own root-vs-fruit and support factors.",
    },
    {
        "key": "life_domains",
        "section_keys": ["wealth_financial_synergy", "d2_kp_wealth_manifestation", "progeny_family_expansion", "d7_parenting_legacy", "career_public_life", "beliefs_intellect_dharma"],
        "focus": "Married-life wealth, D2, progeny and D7, career support, beliefs, intellect, and shared dharma.",
    },
    {
        "key": "karma_timing_remedies",
        "section_keys": ["dosha_demystification", "d60_karmic_layer", "kp_event_materialization", "dasha_transit_timing", "action_plan_remedies"],
        "focus": "Dosha cancellation, D60 karma, KP event materialization, dasha/transit timing, behavioral remedies, and safe Vedic remedies.",
    },
]


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
    execute_fn(
        conn,
        """
        CREATE TABLE IF NOT EXISTS ai_compatibility_premium_report_chapters (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            pair_hash TEXT NOT NULL,
            language TEXT NOT NULL,
            chapter_key TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            chapter_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(userid, pair_hash, language, chapter_key, prompt_version)
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


def get_cached_report_chapter(
    userid: int,
    pair_hash: str,
    language: str,
    chapter_key: str,
    get_conn: Any,
    execute_fn: Any,
) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        ensure_compatibility_premium_reports_table(conn, execute_fn)
        cur = execute_fn(
            conn,
            """
            SELECT chapter_data
            FROM ai_compatibility_premium_report_chapters
            WHERE userid = %s
              AND pair_hash = %s
              AND language = %s
              AND chapter_key = %s
              AND prompt_version = %s
            """,
            (userid, pair_hash, language, chapter_key, PARTNERSHIP_CHAPTER_PROMPT_VERSION),
        )
        row = cur.fetchone()
    return json.loads(row[0]) if row else None


def upsert_report_chapter(
    userid: int,
    pair_hash: str,
    language: str,
    chapter_key: str,
    chapter_data: Dict[str, Any],
    get_conn: Any,
    execute_fn: Any,
) -> None:
    with get_conn() as conn:
        ensure_compatibility_premium_reports_table(conn, execute_fn)
        execute_fn(
            conn,
            """
            INSERT INTO ai_compatibility_premium_report_chapters
                (userid, pair_hash, language, chapter_key, prompt_version, chapter_data, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (userid, pair_hash, language, chapter_key, prompt_version)
            DO UPDATE SET chapter_data = EXCLUDED.chapter_data,
                          updated_at = EXCLUDED.updated_at
            """,
            (
                userid,
                pair_hash,
                language,
                chapter_key,
                PARTNERSHIP_CHAPTER_PROMPT_VERSION,
                json.dumps(chapter_data),
            ),
        )
        conn.commit()


def _window_summary(window: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "start_date": window.get("start_date"),
        "end_date": window.get("end_date"),
        "score": window.get("score"),
        "climate": window.get("climate"),
        "boy_context": window.get("boy_context"),
        "girl_context": window.get("girl_context"),
    }


def _prefix_named_facts(name: str, items: Any, limit: int = 6) -> List[str]:
    out: List[str] = []
    native = str(name or "Native").strip() or "Native"
    for item in items or []:
        text = str(item or "").replace("\r", " ").replace("\n", " ").strip()
        if not text:
            continue
        if text.lower().startswith(native.lower() + ":") or text.lower().startswith(native.lower() + "'"):
            out.append(text)
        else:
            out.append(f"{native}: {text}")
        if len(out) >= limit:
            break
    return out


def _nakshatra_catalog_entry(nakshatra_name: Any, nakshatra_number: Any = None) -> Dict[str, Any]:
    """Lookup classical nature/characteristics from existing NAKSHATRA_DATA (no new calculator)."""
    try:
        from vedic_predictions.config.nakshatra_data import NAKSHATRA_DATA, PADA_CHARACTERISTICS
    except Exception:
        return {}
    entry: Dict[str, Any] = {}
    if isinstance(nakshatra_number, int) and nakshatra_number in NAKSHATRA_DATA:
        entry = dict(NAKSHATRA_DATA[nakshatra_number])
    else:
        target = str(nakshatra_name or "").strip().lower()
        for row in NAKSHATRA_DATA.values():
            if str(row.get("name") or "").strip().lower() == target:
                entry = dict(row)
                break
    if not entry:
        return {}
    return {
        "nature": entry.get("nature"),
        "characteristics": list(entry.get("characteristics") or [])[:4],
        "pada_lords": list(entry.get("pada_lords") or []),
        "guna": entry.get("guna"),
        "element": entry.get("element"),
        "pada_natures": {
            str(pada): (PADA_CHARACTERISTICS.get(pada) or {}).get("nature")
            for pada in (1, 2, 3, 4)
        },
    }


def _planet_nakshatra_row(positions: Dict[str, Any], planet: Optional[str]) -> Dict[str, Any]:
    if not planet:
        return {}
    row = positions.get(planet) or {}
    if not isinstance(row, dict) or not row.get("nakshatra_name"):
        return {"planet": planet}
    nak_name = row.get("nakshatra_name")
    pada = row.get("pada")
    catalog = _nakshatra_catalog_entry(nak_name, row.get("nakshatra_number"))
    pada_lords = catalog.get("pada_lords") or []
    pada_lord = None
    if isinstance(pada, int) and 1 <= pada <= len(pada_lords):
        pada_lord = pada_lords[pada - 1]
    pada_nature = None
    if isinstance(pada, int):
        pada_nature = (catalog.get("pada_natures") or {}).get(str(pada))
    return {
        "planet": planet,
        "nakshatra": nak_name,
        "nakshatra_number": row.get("nakshatra_number"),
        "pada": pada,
        "nakshatra_lord": row.get("nakshatra_lord"),
        "deity": row.get("nakshatra_deity"),
        "quality": row.get("nakshatra_quality"),
        "nature": catalog.get("nature"),
        "characteristics": catalog.get("characteristics") or [],
        "pada_lord": pada_lord,
        "pada_nature": pada_nature,
        "guna": catalog.get("guna"),
        "element": catalog.get("element"),
    }


def build_person_relationship_nakshatra(name: str, chart: Optional[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Moon / Venus / 7th-lord nakshatra+pada using existing NakshatraCalculator via build_nakshatra_context."""
    if not chart:
        return {"name": name, "moon": {}, "venus": {}, "seventh_lord": {}}
    try:
        from reports.context.shared_branch_context import build_nakshatra_context
    except Exception:
        return {"name": name, "moon": {}, "venus": {}, "seventh_lord": {}}
    try:
        nak_ctx = build_nakshatra_context(chart)
    except Exception:
        return {"name": name, "moon": {}, "venus": {}, "seventh_lord": {}}
    positions = nak_ctx.get("positions") or {}
    lord7 = ((profile.get("seventh_house") or {}).get("lord"))
    return {
        "name": name,
        "moon": _planet_nakshatra_row(positions, "Moon"),
        "venus": _planet_nakshatra_row(positions, "Venus"),
        "seventh_lord_planet": lord7,
        "seventh_lord": _planet_nakshatra_row(positions, lord7),
    }


def _format_nakshatra_fact(native: str, role: str, row: Dict[str, Any]) -> str:
    if not row or not row.get("nakshatra"):
        return f"{native}: {role} nakshatra unavailable"
    display = role or row.get("planet") or "Planet"
    parts = [
        f"{native}: {display} in {row.get('nakshatra')} pada {row.get('pada', '--')}",
    ]
    if row.get("nature"):
        parts.append(f"nature {row.get('nature')}")
    pada_bits = []
    if row.get("pada_lord"):
        pada_bits.append(f"pada lord {row.get('pada_lord')}")
    if row.get("pada_nature"):
        pada_bits.append(str(row.get("pada_nature")))
    if pada_bits:
        parts.append("; ".join(pada_bits))
    chars = row.get("characteristics") or []
    if chars:
        parts.append("traits " + ", ".join(str(c) for c in chars[:3]))
    return " — ".join(parts)


def build_relationship_nakshatra_evidence(
    boy_chart: Optional[Dict[str, Any]],
    girl_chart: Optional[Dict[str, Any]],
    boy_birth: Dict[str, Any],
    girl_birth: Dict[str, Any],
    full: Dict[str, Any],
) -> Dict[str, Any]:
    boy_name = boy_birth.get("name", "Person 1")
    girl_name = girl_birth.get("name", "Person 2")
    profiles = full.get("profiles") or {}
    boy_block = build_person_relationship_nakshatra(boy_name, boy_chart, profiles.get("boy") or {})
    girl_block = build_person_relationship_nakshatra(girl_name, girl_chart, profiles.get("girl") or {})
    moon_facts = [
        _format_nakshatra_fact(boy_name, "Moon", boy_block.get("moon") or {}),
        _format_nakshatra_fact(girl_name, "Moon", girl_block.get("moon") or {}),
    ]
    venus_seventh_facts = [
        _format_nakshatra_fact(boy_name, "Venus", boy_block.get("venus") or {}),
        _format_nakshatra_fact(girl_name, "Venus", girl_block.get("venus") or {}),
        _format_nakshatra_fact(
            boy_name,
            f"7th lord ({boy_block.get('seventh_lord_planet') or 'unknown'})",
            boy_block.get("seventh_lord") or {},
        ),
        _format_nakshatra_fact(
            girl_name,
            f"7th lord ({girl_block.get('seventh_lord_planet') or 'unknown'})",
            girl_block.get("seventh_lord") or {},
        ),
    ]
    return {
        "person_a": boy_block,
        "person_b": girl_block,
        "moon_facts": moon_facts,
        "venus_seventh_facts": venus_seventh_facts,
    }


def _person_d1_facts(name: str, profile: Dict[str, Any]) -> List[str]:
    seventh = (profile.get("seventh_house") or {}).get("d1_strength") or {}
    navamsa = profile.get("navamsa_synthesis") or {}
    return [
        f"{name}: D1 7th house reads {seventh.get('band', 'Unknown')} ({seventh.get('score', '--')}%)",
        *_prefix_named_facts(name, seventh.get("evidence") or [], limit=4),
        *_prefix_named_facts(name, navamsa.get("supportive_factors") or [], limit=2),
        *_prefix_named_facts(name, navamsa.get("challenging_factors") or [], limit=2),
    ]


def _person_d9_facts(name: str, profile: Dict[str, Any]) -> List[str]:
    seventh = (profile.get("seventh_house") or {}).get("d9_strength") or {}
    navamsa = profile.get("navamsa_synthesis") or {}
    return [
        f"{name}: D9 7th house reads {seventh.get('band', 'Unknown')} ({seventh.get('score', '--')}%)",
        f"{name}: Navamsa overall reads {navamsa.get('band', 'Unknown')} ({navamsa.get('score', '--')}%)",
        f"{name}: root vs fruit is {navamsa.get('root_vs_fruit', 'consistent')}",
        *_prefix_named_facts(name, seventh.get("evidence") or [], limit=3),
        *_prefix_named_facts(name, navamsa.get("supportive_factors") or [], limit=2),
        *_prefix_named_facts(name, navamsa.get("challenging_factors") or [], limit=2),
    ]


def build_static_compatibility_report(
    full: Dict[str, Any],
    boy_birth: Dict[str, Any],
    girl_birth: Dict[str, Any],
    boy_chart: Optional[Dict[str, Any]] = None,
    girl_chart: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ashtakoota = full.get("ashtakoota", {})
    manglik = ((full.get("manglik") or {}).get("compatibility") or {})
    cross = ((full.get("relationship_indicators") or {}).get("cross_chart") or {})
    timing = full.get("timing_overlay") or {}
    shared = timing.get("shared") or {}
    boy = (full.get("profiles") or {}).get("boy") or {}
    girl = (full.get("profiles") or {}).get("girl") or {}
    recommendation = full.get("recommendation") or {}
    evidence = full.get("evidence_summary") or {}
    boy_name = boy_birth.get("name", "Person 1")
    girl_name = girl_birth.get("name", "Person 2")
    nakshatra_evidence = build_relationship_nakshatra_evidence(
        boy_chart, girl_chart, boy_birth, girl_birth, full
    )

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
            "title": f"{boy_name} Marriage Support",
            "static_summary": f"{boy_name}: D1 7th house is {boy.get('seventh_house', {}).get('d1_strength', {}).get('band', 'Unknown')} and Navamsa is {boy.get('navamsa_synthesis', {}).get('band', 'Unknown')}.",
            "facts": _person_d1_facts(boy_name, boy),
        },
        {
            "key": "person_two_marriage_support",
            "title": f"{girl_name} Marriage Support",
            "static_summary": f"{girl_name}: D1 7th house is {girl.get('seventh_house', {}).get('d1_strength', {}).get('band', 'Unknown')} and Navamsa is {girl.get('navamsa_synthesis', {}).get('band', 'Unknown')}.",
            "facts": _person_d1_facts(girl_name, girl),
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

    master_sections = [
        ("cover", "Cover", "Premium relationship report identity and systems used.", []),
        ("executive_verdict", "Executive Verdict", recommendation.get("verdict"), [*(evidence.get("positive_factors") or [])[:3], *(evidence.get("caution_factors") or [])[:3]]),
        ("score_architecture", "Score Architecture", "Explains why the blended verdict differs from raw Guna Milan.", [f"Overall score: {full.get('overall_score', {}).get('percentage', '--')}%", f"Effective Guna: {ashtakoota.get('effective_total_score', '--')}/36", f"Joint readiness: {shared.get('joint_readiness_score', '--')}%"]),
        (
            "nakshatra_moon_nature",
            "Moon Nakshatra Nature",
            "Each Moon nakshatra and pada shows the core emotional character and how the two minds meet day to day.",
            list(nakshatra_evidence.get("moon_facts") or [])
            + [f"Moon harmony layer: {cross.get('moon_element_match', {}).get('score', '--')}%"],
        ),
        (
            "nakshatra_venus_seventh_lord",
            "Venus and 7th Lord Nakshatra",
            "Venus nakshatra/pada colors desire and affection; 7th-lord nakshatra/pada colors partner-seeking and bond style.",
            list(nakshatra_evidence.get("venus_seventh_facts") or []),
        ),
        ("moon_emotional_rhythm", "Moon and Emotional Rhythm", "Moon signs and nakshatra rhythm show emotional comfort and stress response.", [f"Moon harmony: {cross.get('moon_element_match', {}).get('score', '--')}%", *((ashtakoota.get('effective_critical_issues') or [])[:2])]),
        ("communication_mental_rapport", "Communication and Mental Rapport", "Graha Maitri, Varna, Mercury, and speech houses describe daily repair style.", [f"Rule profile: {full.get('rule_profile', {}).get('label', 'Unknown')}", *((evidence.get("positive_factors") or [])[:2])]),
        ("physical_chemistry_biology", "Physical Chemistry and Biological Compatibility", "Venus, Mars, and Nadi describe attraction flow and biological rhythm.", [f"Venus to Mars: {cross.get('venus_to_mars', {}).get('score', '--')}%", f"Mars to Venus: {cross.get('mars_to_venus', {}).get('score', '--')}%", f"Nadi issues: {ashtakoota.get('nadi', {}).get('score', '--') if isinstance(ashtakoota.get('nadi'), dict) else '--'}"]),
        ("person_a_d1_marriage_foundation", f"{boy_name}: D1 Marriage Foundation", f"This page is only about {boy_name}'s D1 marriage promise.", _person_d1_facts(boy_name, boy)),
        ("person_b_d1_marriage_foundation", f"{girl_name}: D1 Marriage Foundation", f"This page is only about {girl_name}'s D1 marriage promise.", _person_d1_facts(girl_name, girl)),
        ("jaimini_upapada_environment", "Jaimini Upapada Lagna", "UL describes the inner marital environment and continuity of marriage.", []),
        ("darapada_a7_manifestation", "Darapada A7 Manifestation", "A7 describes how relationship desire becomes physical/social reality.", []),
        ("person_a_d9_navamsa", f"{boy_name}: D9 Navamsa", f"This page is only about {boy_name}'s D9 maturity.", _person_d9_facts(boy_name, boy)),
        ("person_b_d9_navamsa", f"{girl_name}: D9 Navamsa", f"This page is only about {girl_name}'s D9 maturity.", _person_d9_facts(girl_name, girl)),
        ("navamsa_pair_durability", "Navamsa Pair Durability", "D9 pair support forecasts whether the bond grows together or drifts.", [f"Pair Navamsa support: {cross.get('navamsa_pair_support', '--')}%", f"{boy_name} root vs fruit: {boy.get('navamsa_synthesis', {}).get('root_vs_fruit', '--')}", f"{girl_name} root vs fruit: {girl.get('navamsa_synthesis', {}).get('root_vs_fruit', '--')}"]),
        ("wealth_financial_synergy", "Wealth and Financial Synergy", "2nd, 8th, and 11th house themes show family wealth, joint assets, and gains.", []),
        ("d2_kp_wealth_manifestation", "D2 and KP Wealth Manifestation", "D2 and KP 2nd/11th cusps refine prosperity manifestation.", []),
        ("progeny_family_expansion", "Progeny and Family Expansion", "5th, 9th, Jupiter, Nadi, and lineage factors show family expansion themes without fetal-sex prediction.", []),
        ("d7_parenting_legacy", "D7 Saptamsha and Parenting", "D7 refines progeny promise, parenting rhythm, and family legacy.", []),
        ("career_public_life", "Career, Ambition, and Public Life", "10th-house themes show whether the relationship supports public status and professional goals.", []),
        ("beliefs_intellect_dharma", "Beliefs, Intellect, and Shared Dharma", "5th and 9th houses show worldview, ethics, creativity, and shared optimism.", []),
        ("dosha_demystification", "Dosha Demystification", manglik.get("description") or "Doshas must be read with cancellation and practical risk.", [f"Manglik status: {manglik.get('status', 'Unknown')}", f"Manglik score: {manglik.get('score', '--')}/10", *((ashtakoota.get("effective_critical_issues") or [])[:3])]),
        ("d60_karmic_layer", "D60 Karmic Layer", "D60 is used as a subtle karmic residue layer, not as the sole verdict.", []),
        ("kp_event_materialization", "KP Event Materialization", "KP 7th cusp star/sub lord confirms whether formal alliance can materialize.", []),
        ("dasha_transit_timing", "Dasha and Transit Timing", recommendation.get("timing_note"), [f"Joint readiness: {shared.get('joint_readiness_score', '--')}%", f"Current climate: {shared.get('current_window', {}).get('climate', 'Unknown')}", *[f"{row.get('start_date')} to {row.get('end_date')} ({row.get('score')}%)" for row in (shared.get("next_favorable_windows") or [])[:3]]]),
        ("action_plan_remedies", "Action Plan and Remedies", "Behavioral remedies, timing strategy, and safe Vedic practices should dominate; gemstones require personal consultation.", [*(recommendation.get("remedies") or [])[:4]]),
    ]
    existing_keys = {section.get("key") for section in sections}
    for key, title, summary, facts in master_sections:
        if key not in existing_keys:
            sections.append({"key": key, "title": title, "static_summary": summary, "facts": facts})

    return {
        "report_version": "compatibility_premium_v1",
        "generated_at": datetime.now().isoformat(),
        "pair": {
            "person_one_name": boy_name,
            "person_two_name": girl_name,
        },
        "headline": recommendation.get("verdict"),
        "compatibility_verdict": recommendation.get("verdict"),
        "sections": sections,
        "priority_actions": recommendation.get("remedies") or [],
        "static_summary": evidence,
        "relationship_nakshatra": nakshatra_evidence,
        "timing_snapshot": {
            "current_window": _window_summary(shared.get("current_window") or {}),
            "next_favorable_windows": [_window_summary(row) for row in (shared.get("next_favorable_windows") or [])[:3]],
        },
    }


def _merge_section_fields(base: Dict[str, Any], ai_section: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **base,
        "opening_summary": ai_section.get("opening_summary") or base.get("opening_summary") or "",
        "astrological_basis": ai_section.get("astrological_basis") or base.get("astrological_basis") or "",
        "interpretation": ai_section.get("interpretation") or base.get("interpretation") or "",
        "practical_guidance": ai_section.get("practical_guidance") or base.get("practical_guidance") or "",
        "key_takeaways": ai_section.get("key_takeaways") or base.get("key_takeaways") or [],
        "ai_interpretation": ai_section.get("ai_interpretation") or base.get("ai_interpretation") or "",
        "practical_meaning": ai_section.get("practical_meaning") or base.get("practical_meaning") or "",
        "decision_guidance": ai_section.get("decision_guidance") or base.get("decision_guidance") or "",
    }


def merge_premium_ai_report(static_report: Dict[str, Any], ai_payload: Dict[str, Any], terms: Optional[List[Dict[str, Any]]] = None, glossary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ai_sections = {row.get("key"): row for row in (ai_payload.get("sections") or []) if row.get("key")}
    merged_sections = []
    used_keys = set()
    for section in static_report.get("sections", []):
        key = section.get("key")
        if key:
            used_keys.add(key)
        ai_section = ai_sections.get(key, {}) if key else {}
        merged_sections.append(_merge_section_fields(section, ai_section))

    # Chapter-based partnership reports emit page keys (executive_verdict, etc.)
    # that are not in the legacy static section list. Keep those so PDF assembly
    # can render the regenerated AI text instead of deterministic placeholders.
    for key, ai_section in ai_sections.items():
        if key in used_keys:
            continue
        merged_sections.append(
            _merge_section_fields(
                {
                    "key": key,
                    "title": ai_section.get("title") or str(key).replace("_", " ").title(),
                    "static_summary": ai_section.get("opening_summary") or "",
                    "facts": ai_section.get("key_takeaways") or [],
                },
                ai_section,
            )
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


def _sections_by_key(static_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        section.get("key"): section
        for section in static_report.get("sections", [])
        if section.get("key")
    }


def _chapter_prompt(chapter: Dict[str, Any]) -> str:
    section_keys = chapter["section_keys"]
    section_examples = [
        {
            "key": key,
            "opening_summary": "One concise premium paragraph for this page, 70 to 110 words.",
            "astrological_basis": "Specific chart evidence used for this page, 50 to 90 words.",
            "interpretation": "Master astrologer interpretation in the requested language, 90 to 130 words.",
            "practical_guidance": "Concrete advice for the couple, 50 to 90 words.",
            "key_takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
        }
        for key in section_keys
    ]
    return f"""
Generate only this relationship-report chapter.

Return ONLY valid JSON:
{{
  "chapter_key": "{chapter['key']}",
  "headline": "Optional chapter headline",
  "sections": {json.dumps(section_examples, ensure_ascii=False)}
}}

Chapter focus: {chapter['focus']}

Rules:
1. Return exactly these section keys and no unrelated sections: {', '.join(section_keys)}.
2. Each section should be deep but bounded. Do not exceed 420 words per section total.
3. Use only the supplied deterministic evidence. Do not invent placements, dates, scores, dashas, or chart facts.
4. Write in the requested language.
5. For progeny, never predict fetal sex or child gender.
6. For remedies, keep gemstones conditional and prefer behavioral, mantra, charity, and timing-based remedies.
7. JSON safety: no markdown tables, no bullet characters, no raw double quotes inside text.
8. No glossary unless it is explicitly present in the schema above. Do not add extra top-level keys.
9. Keep key_takeaways to exactly 3 short strings per section. Write them as plain-language relationship insights, not raw scores.
10. Narrative first: explain Moon, houses, Venus-Mars, doshas, dashas, and practical married-life meaning in readable prose. Mention numeric scores only when they clarify a point, never as the main content.
11. Prefer classical meaning over calculator printouts. Readers should understand the relationship pattern without knowing what 72/100 or 24/36 means.
12. If evidence is thin for a section, say the available evidence is limited and interpret cautiously. Do not ramble.
13. PERSON ATTRIBUTION IS CRITICAL. Never assign one native's planets, houses, UL, A7, or dignity to the other native. If the section is about one named person, every placement must belong to that person only.
14. When subject_native is provided in the context, write exclusively about that native and ignore the other chart completely.
15. Repeat the native's name when stating placements, for example: "For Tarun, benefic Venus occupies the 7th" rather than an unowned "Mercury occupies the 7th".
16. For nakshatra sections: lead with the nakshatra's core nature, behavioral characteristics, and the specific pada's coloring. Deity, symbol, or animal may support the reading but must not replace character analysis. Always name Moon, Venus, or 7th lord with the native and their pada.
"""


def _chapter_context(
    static_report: Dict[str, Any],
    full: Dict[str, Any],
    chapter: Dict[str, Any],
    *,
    shared_context_cached: bool = False,
) -> Dict[str, Any]:
    sections = _sections_by_key(static_report)
    selected_sections = [
        sections[key]
        for key in chapter["section_keys"]
        if key in sections
    ]
    # Never fall back to the full section dump for person-scoped chapters; that
    # is what caused Tarun's D1 page to inherit Deepika's 7th-house Mercury text.
    if not selected_sections and not chapter.get("native_role"):
        selected_sections = list(static_report.get("sections") or [])

    pair = static_report.get("pair") or {}
    profiles = full.get("profiles") or {}
    manglik = full.get("manglik") or {}
    inputs = full.get("inputs") or {}
    native_role = chapter.get("native_role")

    score_summary: Dict[str, Any] = {
        "overall_score": full.get("overall_score"),
        "recommendation": full.get("recommendation"),
        "rule_profile": full.get("rule_profile"),
    }

    if native_role == "boy":
        subject_name = pair.get("person_one_name") or (inputs.get("boy") or {}).get("name") or "Person 1"
        score_summary.update({
            "profiles": {"boy": profiles.get("boy")},
            "manglik": {"boy": manglik.get("boy")},
            "subject_native": {
                "role": "person_a",
                "name": subject_name,
                "birth": inputs.get("boy"),
            },
        })
    elif native_role == "girl":
        subject_name = pair.get("person_two_name") or (inputs.get("girl") or {}).get("name") or "Person 2"
        score_summary.update({
            "profiles": {"girl": profiles.get("girl")},
            "manglik": {"girl": manglik.get("girl")},
            "subject_native": {
                "role": "person_b",
                "name": subject_name,
                "birth": inputs.get("girl"),
            },
        })
    else:
        # When shared pair evidence is already in Gemini cache, omit the heavy
        # pair-level blocks from every chapter prompt (keep only chapter focus).
        if not shared_context_cached:
            score_summary.update({
                "ashtakoota": full.get("ashtakoota"),
                "manglik": manglik,
                "relationship_indicators": full.get("relationship_indicators"),
                "timing_overlay": full.get("timing_overlay"),
                "evidence_summary": full.get("evidence_summary"),
                "profiles": profiles,
                "person_labels": {
                    "person_a": pair.get("person_one_name"),
                    "person_b": pair.get("person_two_name"),
                },
            })
        else:
            score_summary.update({
                "person_labels": {
                    "person_a": pair.get("person_one_name"),
                    "person_b": pair.get("person_two_name"),
                },
            })

    context: Dict[str, Any] = {
        "pair": pair,
        "chapter_key": chapter["key"],
        "chapter_focus": chapter["focus"],
        "selected_static_sections": selected_sections,
        "score_summary": score_summary,
    }
    if chapter["key"] == "nakshatra_nature" and not shared_context_cached:
        context["relationship_nakshatra"] = static_report.get("relationship_nakshatra") or {}
    if shared_context_cached:
        context["shared_context_cached"] = True
        context["shared_context_keys"] = [
            "pair",
            "overall_score",
            "recommendation",
            "ashtakoota",
            "manglik",
            "relationship_indicators",
            "timing_overlay",
            "evidence_summary",
            "relationship_nakshatra",
            "static_sections_by_key",
        ]
    return context


def _shared_chapter_cache_payload(static_report: Dict[str, Any], full: Dict[str, Any]) -> Dict[str, Any]:
    """Pair-level evidence reused across chapter LLM calls. Omit full profiles to protect attribution."""
    pair = static_report.get("pair") or {}
    person_scoped = {
        "person_a_d1_marriage_foundation",
        "person_b_d1_marriage_foundation",
        "person_a_d9_navamsa",
        "person_b_d9_navamsa",
    }
    sections = {}
    for section in static_report.get("sections") or []:
        key = section.get("key")
        if not key:
            continue
        # Person-scoped facts stay in the chapter prompt only (avoids cross-attribution via cache).
        if key in person_scoped:
            sections[key] = {
                "title": section.get("title"),
                "static_summary": section.get("static_summary"),
                "facts": [],
            }
        else:
            sections[key] = {
                "title": section.get("title"),
                "static_summary": section.get("static_summary"),
                "facts": section.get("facts") or [],
            }
    return {
        "pair": pair,
        "person_labels": {
            "person_a": pair.get("person_one_name"),
            "person_b": pair.get("person_two_name"),
        },
        "overall_score": full.get("overall_score"),
        "recommendation": full.get("recommendation"),
        "rule_profile": full.get("rule_profile"),
        "ashtakoota": full.get("ashtakoota"),
        "manglik": full.get("manglik"),
        "relationship_indicators": full.get("relationship_indicators"),
        "timing_overlay": full.get("timing_overlay"),
        "evidence_summary": full.get("evidence_summary"),
        "relationship_nakshatra": static_report.get("relationship_nakshatra"),
        "timing_snapshot": static_report.get("timing_snapshot"),
        "priority_actions": static_report.get("priority_actions") or [],
        "static_sections_by_key": sections,
    }


def _chapter_concurrency() -> int:
    try:
        return max(1, min(12, int(os.getenv("ASTRO_PARTNERSHIP_CHAPTER_CONCURRENCY", "6") or 6)))
    except Exception:
        return 6


async def generate_cached_chapter_report(
    *,
    userid: int,
    pair_hash: str,
    language: str,
    static_report: Dict[str, Any],
    full: Dict[str, Any],
    analyzer: StructuredAnalysisAnalyzer,
    get_conn: Any,
    execute_fn: Any,
    bypass_chapter_cache: bool = False,
) -> Dict[str, Any]:
    import asyncio
    import logging

    from ai.gemini_context_cache import create_gemini_context_cache, delete_gemini_context_cache
    from utils.admin_settings import CHAT_LLM_GEMINI

    logger = logging.getLogger(__name__)
    chapter_payloads: List[Dict[str, Any]] = []
    terms: List[Dict[str, Any]] = []
    glossary: Dict[str, Any] = {}
    missing_chapters: List[Dict[str, Any]] = []
    chapters_from_db_cache = 0
    avoided_input = 0
    avoided_output = 0
    avoided_cached = 0
    avoided_non_cached = 0

    def _add_avoided(usage: Optional[Dict[str, Any]]) -> None:
        nonlocal avoided_input, avoided_output, avoided_cached, avoided_non_cached
        if not isinstance(usage, dict):
            return
        avoided_input += int(usage.get("input_tokens") or 0)
        avoided_output += int(usage.get("output_tokens") or 0)
        avoided_cached += int(usage.get("cached_tokens") or usage.get("cached_input_tokens") or 0)
        avoided_non_cached += int(
            usage.get("non_cached_input_tokens")
            or max(int(usage.get("input_tokens") or 0) - int(usage.get("cached_tokens") or usage.get("cached_input_tokens") or 0), 0)
        )

    for chapter in PARTNERSHIP_CHAPTER_GROUPS:
        if not bypass_chapter_cache:
            cached = get_cached_report_chapter(userid, pair_hash, language, chapter["key"], get_conn, execute_fn)
            if cached:
                chapters_from_db_cache += 1
                _add_avoided(cached.get("_llm_usage") if isinstance(cached, dict) else None)
                chapter_payloads.append(cached)
                continue
        missing_chapters.append(chapter)

    cache_resource = None
    cached_model = None
    shared_context_cached = False
    cache_setup_input_tokens = 0
    if missing_chapters and getattr(analyzer, "vendor", None) == CHAT_LLM_GEMINI:
        cache_resource, cached_model, cache_chars, cache_setup_input_tokens = await create_gemini_context_cache(
            llm_provider=str(getattr(analyzer, "vendor", "") or ""),
            model_name=str(getattr(analyzer, "model_name", "") or ""),
            cache_payload=_shared_chapter_cache_payload(static_report, full),
            cache_label="partnership_chapters",
            cache_enabled_env="ASTRO_PARTNERSHIP_REPORT_CONTEXT_CACHE",
            system_instruction=(
                "You are writing chapters of a premium Vedic partnership compatibility report. "
                "Use the cached shared pair evidence for scores, timing, ashtakoota, chemistry, "
                "and nakshatra facts. Obey person attribution: never assign one native's placements "
                "to the other. Return only the requested chapter JSON."
            ),
            ttl_env_name="ASTRO_PARTNERSHIP_REPORT_CACHE_TTL_S",
        )
        shared_context_cached = cached_model is not None
        if shared_context_cached:
            logger.info(
                "partnership_chapters cache active chars=%s setup_tokens=%s missing_chapters=%s",
                cache_chars,
                cache_setup_input_tokens,
                len(missing_chapters),
            )

    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_input_tokens": 0,
        "non_cached_input_tokens": 0,
        "cache_setup_input_tokens": int(cache_setup_input_tokens or 0) if shared_context_cached else 0,
        "total_tokens": 0,
    }

    def _accumulate_usage(usage: Optional[Dict[str, Any]]) -> None:
        if not isinstance(usage, dict):
            return
        inp = int(usage.get("input_tokens") or 0)
        out = int(usage.get("output_tokens") or 0)
        cached = int(usage.get("cached_tokens") or usage.get("cached_input_tokens") or 0)
        non_cached = int(usage.get("non_cached_input_tokens") or max(inp - cached, 0))
        usage_totals["input_tokens"] += inp
        usage_totals["output_tokens"] += out
        usage_totals["cached_input_tokens"] += cached
        usage_totals["non_cached_input_tokens"] += non_cached
        usage_totals["total_tokens"] += int(usage.get("total_tokens") or (inp + out))

    async def _generate_one_chapter(chapter: Dict[str, Any]) -> Dict[str, Any]:
        ai_result: Optional[Dict[str, Any]] = None
        retry_delay = 5
        for attempt in range(2):
            try:
                ai_result = await analyzer.generate_structured_report(
                    _chapter_prompt(chapter),
                    _chapter_context(
                        static_report,
                        full,
                        chapter,
                        shared_context_cached=shared_context_cached,
                    ),
                    language or "english",
                    model_override=cached_model,
                    shared_context_cached=shared_context_cached,
                )
            except Exception as exc:
                ai_result = {"success": False, "error": str(exc)}

            if ai_result and ai_result.get("success") and not ai_result.get("is_raw"):
                break
            # Count tokens from failed / malformed attempts (we still paid for them).
            _accumulate_usage((ai_result or {}).get("usage"))
            if ai_result and ai_result.get("success") and ai_result.get("is_raw"):
                ai_result = {"success": False, "error": f"Chapter {chapter['key']} returned malformed JSON"}

            err_raw = (ai_result or {}).get("error", "") or ""
            if transient_gemini_error(err_raw) and attempt < 1:
                await asyncio.sleep(retry_delay * (2**attempt))
                continue
            break

        if not ai_result or not ai_result.get("success") or ai_result.get("is_raw"):
            raise RuntimeError(
                user_facing_gemini_error(
                    (ai_result or {}).get("error", "") or f"Chapter {chapter['key']} could not be generated"
                )
            )
        else:
            payload = ai_result.get("data") or {}
            chapter_usage = ai_result.get("usage") if isinstance(ai_result.get("usage"), dict) else {}
            _accumulate_usage(chapter_usage)
            payload["_terms"] = ai_result.get("terms") or []
            payload["_glossary"] = ai_result.get("glossary") or {}
            payload["_llm_usage"] = {
                "input_tokens": int(chapter_usage.get("input_tokens") or 0),
                "output_tokens": int(chapter_usage.get("output_tokens") or 0),
                "cached_tokens": int(chapter_usage.get("cached_tokens") or 0),
                "non_cached_input_tokens": int(chapter_usage.get("non_cached_input_tokens") or 0),
                "total_tokens": int(chapter_usage.get("total_tokens") or 0),
                "model": str(getattr(analyzer, "model_name", "") or ""),
            }
            return payload

    try:
        if missing_chapters:
            semaphore = asyncio.Semaphore(_chapter_concurrency())

            async def _guarded(chapter: Dict[str, Any]) -> Dict[str, Any]:
                async with semaphore:
                    return await _generate_one_chapter(chapter)

            generated_payloads = await asyncio.gather(*[_guarded(chapter) for chapter in missing_chapters])
            generated_by_key = {payload.get("chapter_key"): payload for payload in generated_payloads}

            for chapter in missing_chapters:
                payload = generated_by_key.get(chapter["key"]) or {"chapter_key": chapter["key"], "sections": []}
                terms.extend(payload.pop("_terms", []) or [])
                glossary.update(payload.pop("_glossary", {}) or {})
                upsert_report_chapter(userid, pair_hash, language, chapter["key"], payload, get_conn, execute_fn)
    finally:
        await delete_gemini_context_cache(cache_resource, cache_label="partnership_chapters")

    if missing_chapters:
        chapter_payloads = [
            get_cached_report_chapter(userid, pair_hash, language, chapter["key"], get_conn, execute_fn) or {"chapter_key": chapter["key"], "sections": []}
            for chapter in PARTNERSHIP_CHAPTER_GROUPS
        ]

    combined_sections: List[Dict[str, Any]] = []
    headline = ""
    for payload in chapter_payloads:
        if not headline and payload.get("headline"):
            headline = payload.get("headline")
        combined_sections.extend(payload.get("sections") or [])

    merged = merge_premium_ai_report(
        static_report,
        {
            "headline": headline or static_report.get("headline"),
            "compatibility_verdict": static_report.get("compatibility_verdict"),
            "sections": combined_sections,
            "priority_actions": static_report.get("priority_actions") or [],
            "follow_up_questions": [
                "Which timing window should we prioritize?",
                "Which emotional pattern needs the most care?",
                "Which remedy should we start with first?",
            ],
            "final_summary": static_report.get("compatibility_verdict") or static_report.get("headline") or "",
        },
        terms=terms,
        glossary=glossary,
    )
    llm_usage = {
        "model": str(getattr(analyzer, "model_name", "") or ""),
        "vendor": str(getattr(analyzer, "vendor", "") or ""),
        "input_tokens": int(usage_totals["input_tokens"]),
        "output_tokens": int(usage_totals["output_tokens"]),
        "cached_input_tokens": int(usage_totals["cached_input_tokens"]),
        "non_cached_input_tokens": int(usage_totals["non_cached_input_tokens"]),
        "cache_setup_input_tokens": int(usage_totals["cache_setup_input_tokens"]),
        "total_tokens": int(usage_totals["total_tokens"]) + int(usage_totals["cache_setup_input_tokens"]),
        "chapters_generated": len(missing_chapters),
        "chapters_from_db_cache": chapters_from_db_cache,
        "gemini_context_cache": shared_context_cached,
        "document_cache_hit": False,
        "avoided_by_chapter_cache": {
            "input_tokens": avoided_input,
            "output_tokens": avoided_output,
            "cached_input_tokens": avoided_cached,
            "non_cached_input_tokens": avoided_non_cached,
        },
    }
    return merged | {
        "ai_generated": True,
        "llm_usage": llm_usage,
        "chapter_cache": {
            "enabled": True,
            "prompt_version": PARTNERSHIP_CHAPTER_PROMPT_VERSION,
            "chapters": [chapter["key"] for chapter in PARTNERSHIP_CHAPTER_GROUPS],
            "gemini_context_cache": shared_context_cached,
            "concurrency": _chapter_concurrency(),
            "chapters_generated": len(missing_chapters),
            "chapters_from_db_cache": chapters_from_db_cache,
        },
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
    spend_on_success: bool = True,
) -> Dict[str, Any]:
    pair_hash = compatibility_pair_hash(boy_birth, girl_birth)

    if not force_regenerate:
        cached = get_cached_compatibility_report(userid, pair_hash, get_conn, execute_fn)
        if cached:
            out = dict(cached)
            out["cached"] = True
            original_usage = out.get("llm_usage") if isinstance(out.get("llm_usage"), dict) else {}
            out["llm_usage"] = {
                "model": original_usage.get("model") or "",
                "vendor": original_usage.get("vendor") or "",
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_input_tokens": 0,
                "non_cached_input_tokens": 0,
                "cache_setup_input_tokens": 0,
                "total_tokens": 0,
                "chapters_generated": 0,
                "chapters_from_db_cache": int(original_usage.get("chapters_generated") or 0)
                + int(original_usage.get("chapters_from_db_cache") or 0),
                "gemini_context_cache": False,
                "document_cache_hit": True,
                "avoided_by_chapter_cache": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_input_tokens": 0,
                    "non_cached_input_tokens": 0,
                },
                "avoided_by_document_cache": {
                    "input_tokens": int(original_usage.get("input_tokens") or 0),
                    "output_tokens": int(original_usage.get("output_tokens") or 0),
                    "cached_input_tokens": int(original_usage.get("cached_input_tokens") or 0),
                    "non_cached_input_tokens": int(original_usage.get("non_cached_input_tokens") or 0),
                    "cache_setup_input_tokens": int(original_usage.get("cache_setup_input_tokens") or 0),
                },
            }
            return {"ok": True, "report": out, "cached": True}

    full = KundliMatchingEngine().analyze(boy_chart, girl_chart, boy_birth, girl_birth)
    static_report = build_static_compatibility_report(
        full, boy_birth, girl_birth, boy_chart=boy_chart, girl_chart=girl_chart
    )
    context = {
        "pair": static_report["pair"],
        "compatibility_engine": full,
        "premium_static_report": static_report,
    }

    analyzer = StructuredAnalysisAnalyzer()
    try:
        merged = await generate_cached_chapter_report(
            userid=userid,
            pair_hash=pair_hash,
            language=language or "english",
            static_report=static_report,
            full=full,
            analyzer=analyzer,
            get_conn=get_conn,
            execute_fn=execute_fn,
            bypass_chapter_cache=bool(force_regenerate),
        )
    except Exception as exc:
        return {"ok": False, "error": user_facing_gemini_error(str(exc))}

    if spend_on_success:
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
