from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from ..context.house_context_builder import build_house_summary_rows
from ..models import ReportMetric, ReportPage


def _metric(label: str, value: Any, tone: str | None = None) -> Dict[str, Any]:
    return ReportMetric(label=label, value=str(value), tone=tone).model_dump()


def _page(num: int, title: str, subtitle: str | None = None, summary: str | None = None, bullets=None, metrics=None, chart_refs=None, tables=None, notes=None, cta=None) -> Dict[str, Any]:
    return ReportPage(
        page_number=num,
        title=title,
        subtitle=subtitle,
        summary=summary,
        bullets=bullets or [],
        metrics=metrics or [],
        chart_refs=chart_refs or [],
        tables=tables or [],
        notes=notes or [],
        cta=cta,
    ).model_dump()


def assemble_partnership_pages(context: Dict[str, Any], premium_report: Dict[str, Any], engine_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    pair = context["pair"]
    boy = pair["boy"]
    girl = pair["girl"]
    summaries = context.get("summaries", {}) or {}
    faq_items = context.get("faq_items", []) or []
    boy_summary = summaries.get("boy", {}) or {}
    girl_summary = summaries.get("girl", {}) or {}
    score = engine_result.get("overall_score", {})
    recommendation = engine_result.get("recommendation", {})
    timing = engine_result.get("timing_overlay", {}) or {}
    shared = timing.get("shared", {}) or {}
    cross = (engine_result.get("relationship_indicators", {}) or {}).get("cross_chart", {}) or {}
    ashtakoota = engine_result.get("ashtakoota", {}) or {}
    boy_profile = (engine_result.get("profiles", {}) or {}).get("boy", {}) or {}
    girl_profile = (engine_result.get("profiles", {}) or {}).get("girl", {}) or {}

    sections = {section.get("key"): section for section in premium_report.get("sections", [])}

    pages = [
        _page(
            1,
            "Partnership Compatibility Report",
            f"{boy.get('name', 'Person A')} vs {girl.get('name', 'Person B')}",
            premium_report.get("headline") or recommendation.get("verdict"),
            metrics=[
                _metric("Overall score", f"{round(score.get('percentage', 0))}/100"),
                _metric("Verdict", recommendation.get("verdict", "--")),
                _metric("Guna Milan", f"{ashtakoota.get('effective_total_score', '--')}/36"),
            ],
            chart_refs=["d1_north", "d1_south"],
        ),
        _page(
            2,
            "Executive Summary",
            "Should you proceed?",
            recommendation.get("verdict"),
            bullets=[
                *(engine_result.get("evidence_summary", {}).get("positive_factors", [])[:2]),
                *(engine_result.get("evidence_summary", {}).get("caution_factors", [])[:2]),
            ],
            metrics=[
                _metric("Current climate", shared.get("current_window", {}).get("climate", "--")),
                _metric("Joint readiness", f"{shared.get('joint_readiness_score', '--')}%"),
            ],
            notes=[recommendation.get("timing_note")] if recommendation.get("timing_note") else [],
        ),
        _page(
            3,
            "Compatibility Breakdown",
            "Score dimensions",
            "Traditional score plus deeper compatibility layers.",
            metrics=[
                _metric("Emotional", cross.get("moon_element_match", {}).get("score", "--")),
                _metric("Communication", cross.get("overall_relationship_quality", {}).get("score", "--")),
                _metric("Physical / Intimacy", cross.get("venus_to_mars", {}).get("score", "--")),
                _metric("Values / Goals", cross.get("marriage_alignment", {}).get("score", "--")),
                _metric("Karma / Destiny", cross.get("navamsa_pair_support", "--")),
            ],
            chart_refs=["radar_chart"],
        ),
        _page(
            4,
            "D1 Chart Overlay",
            "Person A and Person B",
            "Side-by-side D1 charts with core partnership overlays.",
            bullets=[
                "Show North Indian and South Indian chart images here.",
                f"{boy.get('name', 'Person A')} Jaimini note: {boy_summary.get('jaimini', {}).get('relationship_note', '--')}",
                f"{girl.get('name', 'Person B')} Jaimini note: {girl_summary.get('jaimini', {}).get('relationship_note', '--')}",
            ],
            chart_refs=["d1_north", "d1_south"],
        ),
        _page(
            5,
            "D1 Chart Overlay",
            "Key house contacts",
            "Cross-chart house relationships and planetary placements.",
            bullets=[
                f"{boy.get('name', 'Person A')} KP: {boy_summary.get('kp', {}).get('materialization_note', '--')}",
                f"{girl.get('name', 'Person B')} KP: {girl_summary.get('kp', {}).get('materialization_note', '--')}",
            ],
            chart_refs=["d1_cross_house_table"],
        ),
        _page(
            6,
            "Navamsa / D9",
            f"{boy.get('name', 'Person A')}",
            "Soul-level marriage support.",
            bullets=[
                boy_summary.get("nakshatra", {}).get("emotional_note", "--"),
                boy_summary.get("d60", {}).get("summary", "--"),
                *(sections.get("person_one_marriage_support", {}).get("facts", [])[:2]),
            ],
            chart_refs=["d9_north", "d9_south"],
        ),
        _page(
            7,
            "Navamsa / D9",
            f"{girl.get('name', 'Person B')}",
            "Soul-level marriage support.",
            bullets=[
                girl_summary.get("nakshatra", {}).get("emotional_note", "--"),
                girl_summary.get("d60", {}).get("summary", "--"),
                *(sections.get("person_two_marriage_support", {}).get("facts", [])[:2]),
            ],
            chart_refs=["d9_north", "d9_south"],
        ),
        _page(
            8,
            "Dasha Comparison",
            "2026-2035 timeline",
            "Major life-period comparison.",
            bullets=[
                sections.get("timing_and_marriage_windows", {}).get("static_summary") or "--",
                *(sections.get("timing_and_marriage_windows", {}).get("facts", [])[:4]),
            ],
            chart_refs=["dasha_timeline"],
        ),
        _page(
            9,
            "Dasha Comparison",
            "Joint windows",
            "When both charts are supportive together.",
            bullets=[
                f"{window.get('start_date')} to {window.get('end_date')} ({window.get('climate')})"
                for window in (shared.get("next_favorable_windows", []) or [])[:3]
            ],
            chart_refs=["dasha_overlap"],
        ),
        _page(
            10,
            "Guna Milan + AI Score",
            "Traditional and modern",
            sections.get("ashtakoota_and_exceptions", {}).get("static_summary"),
            bullets=[
                *(sections.get("ashtakoota_and_exceptions", {}).get("facts", [])[:4]),
                f"Surface score: {ashtakoota.get('total_score', '--')}/36",
                f"Effective score: {ashtakoota.get('effective_total_score', '--')}/36",
            ],
        ),
        _page(
            11,
            "Strengths",
            "Why this pair works",
            sections.get("overall_foundation", {}).get("ai_interpretation") or recommendation.get("verdict"),
            bullets=[
                *(engine_result.get("evidence_summary", {}).get("positive_factors", [])[:3]),
                *(sections.get("overall_foundation", {}).get("facts", [])[:3]),
            ],
        ),
        _page(
            12,
            "Challenges",
            "Friction points",
            sections.get("contradictions_and_hidden_factors", {}).get("static_summary"),
            bullets=[
                *(engine_result.get("evidence_summary", {}).get("caution_factors", [])[:3]),
                f"Nadi note: {boy_summary.get('nadi', {}).get('relationship_note', '--')}",
            ],
        ),
        _page(
            13,
            "Solutions and Remedies",
            "Practical fixes",
            sections.get("final_guidance_and_remedies", {}).get("ai_interpretation"),
            bullets=[
                *(premium_report.get("priority_actions", [])[:3]),
                *(engine_result.get("recommendation", {}).get("remedies", [])[:3]),
            ],
        ),
        _page(
            14,
            "Timing",
            "Best and avoid windows",
            sections.get("timing_and_marriage_windows", {}).get("static_summary"),
            bullets=[
                sections.get("timing_and_marriage_windows", {}).get("static_summary") or "--",
                *(sections.get("timing_and_marriage_windows", {}).get("facts", [])[:4]),
                boy_summary.get("kp", {}).get("materialization_note", "--"),
            ],
        ),
        _page(
            15,
            "Future Analysis",
            "Marriage / business outcomes",
            "What the partnership tends to grow into.",
            bullets=[
                boy_summary.get("d60", {}).get("summary", "--"),
                girl_summary.get("d60", {}).get("summary", "--"),
                *(premium_report.get("follow_up_questions", [])[:2]),
            ],
        ),
        _page(
            16,
            "D60 / Past Life Karma",
            "Hidden karmic layer",
            boy_summary.get("d60", {}).get("summary") or "D60 indicates deeper karmic residue.",
            bullets=[
                boy_summary.get("d60", {}).get("lagna_deity", "--"),
                boy_summary.get("d60", {}).get("atmakaraka_deity", "--"),
                girl_summary.get("d60", {}).get("lagna_deity", "--"),
                girl_summary.get("d60", {}).get("atmakaraka_deity", "--"),
            ],
            chart_refs=["d60_summary"],
        ),
        _page(
            17,
            "House-wise Synthesis",
            "1st through 12th houses",
            "Structural synthesis across all houses.",
            tables=[{
                "title": "House synthesis",
                "rows": build_house_summary_rows(engine_result),
            }],
        ),
        _page(
            18,
            "Remedies Summary",
            "Top 3 actions",
            "Keep only the strongest remedies.",
            bullets=premium_report.get("priority_actions", [])[:3],
        ),
        _page(
            19,
            "FAQ",
            "Questions and answers",
            "Common user questions about the report.",
            bullets=[
                f"Q: {item.get('question')}\nA: {item.get('answer')}"
                for item in faq_items[:5]
            ]
            or [f"Q: {question}" for question in premium_report.get("follow_up_questions", [])[:5]],
        ),
        _page(
            20,
            "Next Steps",
            "Continue with the app",
            "Recommended actions after reading the report.",
            cta="Download the AstroRoshni app, book a consultation, or explore deeper reports.",
        ),
    ]
    return pages


def build_chart_manifest(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    style = context.get("chart_style", "both")
    slots = [
        {"slot": "d1_north", "chart": "D1", "style": "north"},
        {"slot": "d1_south", "chart": "D1", "style": "south"},
        {"slot": "d9_north", "chart": "D9", "style": "north"},
        {"slot": "d9_south", "chart": "D9", "style": "south"},
        {"slot": "d60_summary", "chart": "D60", "style": "summary"},
    ]
    if style == "north":
        return [slot for slot in slots if slot["style"] in {"north", "summary"}]
    if style == "south":
        return [slot for slot in slots if slot["style"] in {"south", "summary"}]
    return slots
