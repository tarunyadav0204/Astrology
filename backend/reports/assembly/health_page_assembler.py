"""Assemble 27-page Health Report pages from LLM sections + deterministic evidence."""

from __future__ import annotations

from typing import Any, Dict, List

from reports.constants import MEDICAL_DISCLAIMER
from ..models import ReportMetric, ReportPage


HEALTH_PAGE_BLUEPRINT = [
    {"num": 1, "key": "cover", "title": "Health Report", "subtitle": "Master Vedic wellness study", "charts": []},
    {"num": 2, "key": "executive_verdict", "title": "Executive Health Verdict", "subtitle": "Vitality, risk tone, and near-term focus", "charts": []},
    {"num": 3, "key": "score_architecture", "title": "How Health Layers Fit Together", "subtitle": "D1 houses, D9 resilience, D30 confirmation, dasha timing", "charts": []},
    {"num": 4, "key": "constitution_dosha", "title": "Constitution and Dosha Tone", "subtitle": "Elemental balance and Ayurvedic leaning", "charts": []},
    {"num": 5, "key": "vitality_immunity", "title": "Vitality and Immunity", "subtitle": "Lagna lord, Sun, Mars, and 6th-house resilience", "charts": ["native_d1"]},
    {"num": 6, "key": "health_houses_d1", "title": "Core Health Houses", "subtitle": "1st, 6th, 8th, and 12th house reading", "charts": ["native_d1"]},
    {"num": 7, "key": "planet_body_systems", "title": "Your Body Map", "subtitle": "Priority zones from house × rashi × lord patterns", "charts": []},
    {"num": 8, "key": "mental_emotional_health", "title": "Mental and Emotional Health", "subtitle": "Moon, Mercury, 4th house, and rest recovery", "charts": []},
    {"num": 9, "key": "digestion_metabolism_recovery", "title": "Digestion, Metabolism, Recovery", "subtitle": "Agni, vitality, and bounce-back capacity", "charts": []},
    {"num": 10, "key": "acute_vs_chronic_pattern", "title": "Acute vs Chronic Pattern", "subtitle": "Flare, persistence, sensitivity, or preventive tone", "charts": []},
    {"num": 11, "key": "health_yogas_afflictions", "title": "Health Yogas and Afflictions", "subtitle": "Supportive combinations and vulnerability markers", "charts": []},
    {"num": 12, "key": "lifestyle_triggers", "title": "Lifestyle Triggers", "subtitle": "Sleep, stress, pace, and recovery habits", "charts": []},
    {"num": 13, "key": "d9_resilience", "title": "D9 Resilience", "subtitle": "Navamsa durability and recovery tone", "charts": ["native_d9"]},
    {"num": 14, "key": "d30_confirmation", "title": "D30 Confirmation", "subtitle": "Trimsamsa refinement of vulnerability themes", "charts": ["native_d30"]},
    {"num": 15, "key": "badhaka_mrityu_bhaga", "title": "Badhaka and Mrityu Bhaga", "subtitle": "Obstruction and sensitive degree cues", "charts": []},
    {"num": 16, "key": "kp_health_materialization", "title": "KP Health Materialization", "subtitle": "Whether 1/6/8 themes tend to show in lived experience", "charts": []},
    {"num": 17, "key": "nakshatra_health_nature", "title": "Nakshatra Health Nature", "subtitle": "Moon and Lagna-lord nakshatra wellness tone", "charts": []},
    {"num": 18, "key": "current_dasha_health_theme", "title": "Current Dasha Health Theme", "subtitle": "MD, AD, and PD wellness job right now", "charts": []},
    {"num": 19, "key": "twelve_month_overview", "title": "Next 12 Months Overview", "subtitle": "The year's health climate by dasha", "charts": []},
    {"num": 20, "key": "quarter_q1", "title": "Months 1–3", "subtitle": "First quarter health timing", "charts": []},
    {"num": 21, "key": "quarter_q2", "title": "Months 4–6", "subtitle": "Second quarter health timing", "charts": []},
    {"num": 22, "key": "quarter_q3", "title": "Months 7–9", "subtitle": "Third quarter health timing", "charts": []},
    {"num": 23, "key": "quarter_q4", "title": "Months 10–12", "subtitle": "Fourth quarter health timing", "charts": []},
    {"num": 24, "key": "peak_caution_windows", "title": "Peak and Caution Windows", "subtitle": "Best support and highest caution windows this year", "charts": []},
    {"num": 25, "key": "action_plan_remedies", "title": "Action Plan and Remedies", "subtitle": "Behavioral plan plus safe Vedic habits", "charts": []},
    {"num": 26, "key": "ninety_day_checklist", "title": "90-Day Wellness Checklist", "subtitle": "Concrete priorities for the next quarter", "charts": []},
    {"num": 27, "key": "safety_and_next_steps", "title": "Safety and Next Steps", "subtitle": "What astrology is not — and when to see a doctor", "charts": []},
]


def _clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text or fallback


def _constitution_label(health: Dict[str, Any], agent: Dict[str, Any] | None = None) -> str:
    direct = _clean(health.get("constitution_type"))
    if direct:
        return direct
    agent = agent or {}
    ct = agent.get("ct")
    if isinstance(ct, dict):
        return _clean(ct.get("type") or ct.get("label"), "--")
    if isinstance(ct, str):
        return _clean(ct, "--")
    return "--"


def _element_balance_table(element_balance: Any) -> Dict[str, Any] | None:
    if not isinstance(element_balance, dict) or not element_balance:
        return None
    order = ("Fire", "Water", "Air", "Earth")
    headers = [key for key in order if key in element_balance]
    if not headers:
        headers = [str(key) for key in element_balance.keys()]
    values = []
    for key in headers:
        raw = element_balance.get(key)
        try:
            values.append(f"{float(raw):.0f}%")
        except (TypeError, ValueError):
            values.append(_clean(raw, "--"))
    return {
        "title": "Element balance",
        "rows": [headers, values],
    }


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value:
        return [value]
    return []


def _metric(label: str, value: Any, tone: str | None = None) -> Dict[str, Any]:
    return ReportMetric(label=label, value=_clean(value, "--"), tone=tone).model_dump()


def _page(num: int, title: str, subtitle: str, summary: str, *, bullets=None, metrics=None, chart_refs=None, tables=None, notes=None, cta=None) -> Dict[str, Any]:
    return ReportPage(
        page_number=num,
        title=title,
        subtitle=subtitle,
        summary=_clean(summary) or None,
        bullets=[_clean(item) for item in (bullets or []) if _clean(item)],
        metrics=list(metrics or []),
        chart_refs=[_clean(ref) for ref in (chart_refs or []) if _clean(ref)],
        tables=list(tables or []),
        notes=[_clean(item) for item in (notes or []) if _clean(item)],
        cta=cta,
    ).model_dump()


def _sections(premium_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        _clean(section.get("key")): section
        for section in _as_list(premium_report.get("sections"))
        if isinstance(section, dict) and _clean(section.get("key"))
    }


def _section_text(section: Dict[str, Any] | None, *keys: str, fallback: str = "") -> str:
    section = section or {}
    for key in keys:
        text = _clean(section.get(key))
        if text and text != "--":
            return text
    return fallback


def _section_bullets(section: Dict[str, Any] | None, limit: int = 5) -> List[str]:
    section = section or {}
    takeaways = [_clean(item) for item in _as_list(section.get("key_takeaways")) if _clean(item)]
    if takeaways:
        return takeaways[:limit]
    guidance = _clean(section.get("practical_guidance"))
    return [guidance] if guidance else []


def _section_notes(section: Dict[str, Any] | None) -> List[str]:
    section = section or {}
    notes = []
    for key in ("astrological_basis", "interpretation", "practical_guidance"):
        text = _clean(section.get(key))
        if text:
            notes.append(text)
    return notes[:3]


def _quarter_table(months: List[Dict[str, Any]], start_idx: int) -> Dict[str, Any]:
    rows = []
    for month in months[start_idx:start_idx + 3]:
        rows.append([
            _clean(month.get("label"), "--"),
            _clean(month.get("mahadasha"), "--"),
            _clean(month.get("antardasha"), "--"),
            _clean(month.get("pratyantardasha"), "--"),
        ])
    return {
        "title": "Dasha by month",
        "headers": ["Month", "MD", "AD", "PD"],
        "rows": rows,
    }


def build_health_chart_manifest(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    style = context.get("chart_style") or "both"
    refs = ["native_d1", "native_d9", "native_d30"]
    return [{"ref": ref, "style": style} for ref in refs]


def assemble_health_pages(
    context: Dict[str, Any],
    premium_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    person = context.get("person") or {}
    name = _clean(person.get("name"), "Native")
    health = context.get("health") or {}
    score = health.get("health_score")
    constitution = _constitution_label(health, context.get("health_agent") or {})
    dashas = context.get("current_dashas") or {}
    months = context.get("twelve_month_dasha") or []
    disclaimer = _clean(
        premium_report.get("medical_disclaimer") or context.get("medical_disclaimer"),
        MEDICAL_DISCLAIMER,
    )
    sections = _sections(premium_report)
    default_summary = (
        premium_report.get("health_verdict")
        or premium_report.get("headline")
        or f"This health report studies {name}'s vitality, vulnerabilities, and timing climate."
    )

    pages: List[Dict[str, Any]] = []
    for blueprint in HEALTH_PAGE_BLUEPRINT:
        key = blueprint["key"]
        section = sections.get(key) or {}
        summary = _section_text(
            section,
            "opening_summary",
            "interpretation",
            "static_summary",
            fallback=default_summary if blueprint["num"] in {1, 2, 27} else f"This chapter studies {blueprint['subtitle'].lower()} for {name}.",
        )
        bullets = _section_bullets(section, 5)
        notes = _section_notes(section)
        metrics: List[Dict[str, Any]] = []
        tables: List[Dict[str, Any]] = []

        if key == "cover":
            metrics = [
                _metric("Health score", score if score is not None else "--"),
                _metric("Constitution", constitution),
                _metric(
                    "Current MD",
                    (dashas.get("mahadasha") or {}).get("planet") or "--",
                ),
            ]
            bullets = bullets or [
                "Read constitution and houses first, then D9/D30 confirmation, then the 12-month dasha plan.",
                "Reopening a saved report is free; regenerate charges again.",
            ]
            notes = [disclaimer] + notes
        elif key == "executive_verdict":
            metrics = [
                _metric("Health score", score if score is not None else "--"),
                _metric("Constitution", constitution),
            ]
            notes = notes + [disclaimer]
        elif key == "constitution_dosha":
            metrics = [
                _metric("Constitution", constitution),
            ]
            eb_table = _element_balance_table(health.get("element_balance"))
            if eb_table:
                tables = [eb_table]
            else:
                metrics.append(_metric("Element balance", "--"))
        elif key == "planet_body_systems":
            zone_map = context.get("body_zone_map") or {}
            priority = zone_map.get("priority_zones") or []
            patterns = zone_map.get("event_patterns") or []
            zone_rows = []
            for row in priority[:6]:
                zone_rows.append([
                    _clean(row.get("zone"), "--"),
                    ", ".join([_clean(s) for s in (row.get("sources") or [])[:3]]) or "--",
                    _clean((row.get("why") or [None])[0], "--")[:90],
                ])
            pattern_rows = []
            for row in patterns[:5]:
                pattern_rows.append([
                    _clean(row.get("title"), "--"),
                    ", ".join([_clean(z) for z in (row.get("zones") or [])[:3]]) or "--",
                    _clean(row.get("summary"), "--")[:100],
                ])
            tables = []
            if zone_rows:
                tables.append({
                    "title": "Priority body zones (chart susceptibilities)",
                    "headers": ["Zone", "Sources", "Why"],
                    "rows": zone_rows,
                })
            if pattern_rows:
                tables.append({
                    "title": "Event-pattern themes (not diagnoses)",
                    "headers": ["Pattern", "Zones", "Reading"],
                    "rows": pattern_rows,
                })
            if not tables:
                ranks = context.get("planet_system_ranks") or []
                rows = []
                for row in ranks[:9]:
                    systems = row.get("systems") or []
                    rows.append([
                        _clean(row.get("planet"), "--"),
                        ", ".join([_clean(s) for s in systems[:3]]) or "--",
                        _clean(row.get("impact_summary"), "--")[:80],
                    ])
                if rows:
                    tables = [{"title": "Planet → body systems", "headers": ["Planet", "Systems", "Cue"], "rows": rows}]
            if zone_map.get("disclaimer"):
                notes = notes + [_clean(zone_map.get("disclaimer"))]
        elif key == "health_houses_d1":
            houses = context.get("attention_houses") or []
            rows = []
            for h in houses[:6]:
                fused = ""
                zone_map = context.get("body_zone_map") or {}
                for item in zone_map.get("house_map") or []:
                    if item.get("house") == h.get("house"):
                        fused = ", ".join([_clean(z) for z in (item.get("fused_zones") or [])[:3]])
                        break
                rows.append([
                    _clean(h.get("house"), "--"),
                    _clean(h.get("significance"), "--")[:40],
                    fused or "--",
                ])
            if rows:
                tables = [{"title": "Health houses × body flavour", "headers": ["House", "Focus", "Zones"], "rows": rows}]
        elif key == "current_dasha_health_theme":
            metrics = [
                _metric("Mahadasha", (dashas.get("mahadasha") or {}).get("planet") or "--"),
                _metric("Antardasha", (dashas.get("antardasha") or {}).get("planet") or "--"),
                _metric("Pratyantardasha", (dashas.get("pratyantardasha") or {}).get("planet") or "--"),
            ]
        elif key == "twelve_month_overview":
            rows = [
                [
                    _clean(m.get("label"), "--"),
                    _clean(m.get("mahadasha"), "--"),
                    _clean(m.get("antardasha"), "--"),
                    _clean(m.get("pratyantardasha"), "--"),
                ]
                for m in months
            ]
            tables = [{"title": "Next 12 months dasha strip", "headers": ["Month", "MD", "AD", "PD"], "rows": rows}]
        elif key == "quarter_q1":
            tables = [_quarter_table(months, 0)]
        elif key == "quarter_q2":
            tables = [_quarter_table(months, 3)]
        elif key == "quarter_q3":
            tables = [_quarter_table(months, 6)]
        elif key == "quarter_q4":
            tables = [_quarter_table(months, 9)]
        elif key == "nakshatra_health_nature":
            lords = context.get("lords_nakshatra") or {}
            lagna = lords.get("lagna_lord") or {}
            moon = lords.get("moon") or {}
            metrics = [
                _metric("Lagna lord", lagna.get("planet") or "--"),
                _metric("Lagna nakshatra", (lagna.get("nakshatra") or {}).get("nakshatra") or "--"),
                _metric("Moon nakshatra", (moon.get("nakshatra") or {}).get("nakshatra") or "--"),
            ]
        elif key in ("action_plan_remedies", "safety_and_next_steps"):
            notes = notes + [disclaimer]
            if key == "safety_and_next_steps" and not bullets:
                bullets = [
                    "Use this report for prevention, pacing, and self-care awareness.",
                    "Seek medical care for persistent symptoms, emergencies, or diagnosed conditions.",
                ]

        pages.append(
            _page(
                blueprint["num"],
                blueprint["title"],
                blueprint["subtitle"],
                summary,
                bullets=bullets,
                metrics=metrics,
                chart_refs=blueprint.get("charts") or [],
                tables=tables,
                notes=notes,
            )
        )
    return pages
