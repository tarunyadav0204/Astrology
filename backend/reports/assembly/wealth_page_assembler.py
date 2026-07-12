"""Assemble 27-page Wealth Report pages from LLM sections + deterministic evidence."""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import ReportMetric, ReportPage


WEALTH_PAGE_BLUEPRINT = [
    {"num": 1, "key": "cover", "title": "Wealth Report", "subtitle": "Master Vedic money study", "charts": []},
    {"num": 2, "key": "executive_verdict", "title": "Executive Wealth Verdict", "subtitle": "Clear reading of capacity, risk, and opportunity", "charts": []},
    {"num": 3, "key": "score_architecture", "title": "How Wealth Layers Fit Together", "subtitle": "D1 promise, D2 manifestation, D10 income, dasha timing", "charts": []},
    {"num": 4, "key": "d1_wealth_foundation", "title": "D1 Wealth Foundation", "subtitle": "2nd, 11th, Lagna, and 9th house money promise", "charts": ["native_d1"]},
    {"num": 5, "key": "dhana_money_yogas", "title": "Dhana and Money Yogas", "subtitle": "Named combinations that shape prosperity", "charts": []},
    {"num": 6, "key": "indu_arudha_image", "title": "Indu Lagna and Money Image", "subtitle": "Indu Lagna, Arudha, and Hora Lagna", "charts": []},
    {"num": 7, "key": "money_psychology", "title": "Money Psychology", "subtitle": "Moon, Venus, and Mercury earn-spend style", "charts": []},
    {"num": 8, "key": "jupiter_saturn_karma", "title": "Jupiter and Saturn Money Karma", "subtitle": "Growth, ethics, delay, and compounding", "charts": []},
    {"num": 9, "key": "income_engines", "title": "Income Engines", "subtitle": "Sun, Mars, Rahu, and Ketu wealth channels", "charts": []},
    {"num": 10, "key": "d2_hora_manifestation", "title": "D2 Hora Manifestation", "subtitle": "Whether wealth physically sticks", "charts": ["native_d2"]},
    {"num": 11, "key": "d10_career_income", "title": "D10 Career–Income Axis", "subtitle": "How profession converts into cashflow", "charts": ["native_d10"]},
    {"num": 12, "key": "sources_of_wealth", "title": "Sources of Wealth", "subtitle": "Primary, supportive, and avoid channels", "charts": []},
    {"num": 13, "key": "assets_property_inheritance", "title": "Assets, Property, and Inheritance", "subtitle": "4th, 8th, and 9th house wealth", "charts": []},
    {"num": 14, "key": "debt_loss_sudden", "title": "Debt, Loss, and Sudden Money", "subtitle": "6th, 8th, and 12th leakage and windfalls", "charts": []},
    {"num": 15, "key": "kp_wealth_materialization", "title": "KP Wealth Materialization", "subtitle": "Whether gains land in the physical world", "charts": []},
    {"num": 16, "key": "nakshatra_2_11_lords", "title": "Nakshatra of 2nd and 11th Lords", "subtitle": "How you earn and spend by nature", "charts": []},
    {"num": 17, "key": "spouse_joint_finances", "title": "Spouse and Joint Finances", "subtitle": "7th house and D9 money patterns", "charts": ["native_d9"]},
    {"num": 18, "key": "speculation_vs_investing", "title": "Speculation vs Long-Term Investing", "subtitle": "5th house, Rahu, Mercury, and trading tone", "charts": []},
    {"num": 19, "key": "current_dasha_theme", "title": "Current Dasha Wealth Theme", "subtitle": "MD, AD, and PD money job right now", "charts": []},
    {"num": 20, "key": "twelve_month_overview", "title": "Next 12 Months Overview", "subtitle": "The year's money story by dasha", "charts": []},
    {"num": 21, "key": "quarter_q1", "title": "Months 1–3", "subtitle": "First quarter wealth timing", "charts": []},
    {"num": 22, "key": "quarter_q2", "title": "Months 4–6", "subtitle": "Second quarter wealth timing", "charts": []},
    {"num": 23, "key": "quarter_q3", "title": "Months 7–9", "subtitle": "Third quarter wealth timing", "charts": []},
    {"num": 24, "key": "quarter_q4", "title": "Months 10–12", "subtitle": "Fourth quarter wealth timing", "charts": []},
    {"num": 25, "key": "peak_caution_windows", "title": "Peak and Caution Windows", "subtitle": "Best and riskiest money windows this year", "charts": []},
    {"num": 26, "key": "action_plan_remedies", "title": "Action Plan and Remedies", "subtitle": "Behavioral plan plus safe Vedic guidance", "charts": []},
    {"num": 27, "key": "wealth_roadmap_checklist", "title": "Wealth Roadmap Checklist", "subtitle": "90-day actions and 12-month priorities", "charts": []},
]


def _clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text or fallback


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


def build_wealth_chart_manifest(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    style = context.get("chart_style") or "both"
    refs = ["native_d1", "native_d2", "native_d9", "native_d10"]
    return [{"ref": ref, "style": style} for ref in refs]


def assemble_wealth_pages(
    context: Dict[str, Any],
    premium_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    person = context.get("person") or {}
    name = _clean(person.get("name"), "Native")
    wealth = context.get("wealth") or {}
    score = wealth.get("wealth_score")
    dashas = context.get("current_dashas") or {}
    months = context.get("twelve_month_dasha") or []
    px = context.get("px_wealth") or {}
    sections = _sections(premium_report)
    default_summary = (
        premium_report.get("wealth_verdict")
        or premium_report.get("headline")
        or f"This wealth report studies {name}'s capacity to earn, save, and grow assets."
    )

    pages: List[Dict[str, Any]] = []
    for blueprint in WEALTH_PAGE_BLUEPRINT:
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
                _metric("Wealth score", score if score is not None else "--"),
                _metric("Income mode", (px.get("mode") or "--")),
                _metric("Risk band", ((px.get("risk") or {}).get("band") if isinstance(px.get("risk"), dict) else px.get("risk")) or "--"),
                _metric(
                    "Current MD",
                    (dashas.get("mahadasha") or {}).get("planet") or "--",
                ),
            ]
            bullets = bullets or [
                "Read foundation, yogas, D2/D10 manifestation, then the 12-month dasha plan.",
                "Reopening a saved report is free; regenerate charges again.",
            ]
        elif key == "executive_verdict":
            metrics = [
                _metric("Wealth score", score if score is not None else "--"),
                _metric("Mode", px.get("mode") or "--"),
            ]
        elif key == "current_dasha_theme":
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
        elif key == "nakshatra_2_11_lords":
            lords = context.get("lords_nakshatra") or {}
            second = lords.get("second_lord") or {}
            eleventh = lords.get("eleventh_lord") or {}
            metrics = [
                _metric("2nd lord", second.get("planet") or "--"),
                _metric("2nd nakshatra", (second.get("nakshatra") or {}).get("nakshatra") or "--"),
                _metric("11th lord", eleventh.get("planet") or "--"),
                _metric("11th nakshatra", (eleventh.get("nakshatra") or {}).get("nakshatra") or "--"),
            ]
        elif key == "speculation_vs_investing":
            trading = context.get("trading_luck") or {}
            metrics = [
                _metric("Trading tone", trading.get("recommendation") or trading.get("signal") or "--"),
                _metric("Luck score", trading.get("final_score") or trading.get("score") or "--"),
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
