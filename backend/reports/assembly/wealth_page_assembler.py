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


def _yoga_label(item: Any) -> str:
    if isinstance(item, dict):
        return _clean(item.get("name") or item.get("yoga") or item.get("title") or item.get("type"), "Yoga")
    return _clean(item, "Yoga")


def _yoga_note(item: Any) -> str:
    if isinstance(item, dict):
        return _clean(item.get("description") or item.get("summary") or item.get("effect") or item.get("interpretation"), "--")[:120]
    return "--"


def _wealth_score_breakdown_table(wealth: Dict[str, Any]) -> Dict[str, Any] | None:
    breakdown = wealth.get("wealth_score_breakdown") or []
    rows = []
    for line in _as_list(breakdown)[:14]:
        text = _clean(line)
        if not text:
            continue
        if ":" in text:
            left, right = text.split(":", 1)
            rows.append([left.strip(), right.strip()])
        else:
            rows.append([text, ""])
    if not rows:
        return None
    return {
        "title": "Wealth score calculation",
        "headers": ["Component", "Contribution"],
        "rows": rows,
    }


def _wealth_houses_table(wealth: Dict[str, Any]) -> Dict[str, Any] | None:
    house_analysis = wealth.get("house_analysis") or {}
    if not isinstance(house_analysis, dict):
        return None
    rows = []
    for house_num in (2, 11, 9, 5, 8, 4, 10, 1):
        key = house_num if house_num in house_analysis else str(house_num)
        row = house_analysis.get(key) or house_analysis.get(house_num)
        if not isinstance(row, dict):
            continue
        rows.append([
            f"{house_num}th",
            _clean(row.get("wealth_significance"), "--")[:50],
            _clean(row.get("wealth_interpretation"), "--")[:90],
        ])
    if not rows:
        return None
    return {
        "title": "Wealth houses (D1)",
        "headers": ["House", "Focus", "Reading"],
        "rows": rows,
    }


def _wealth_yogas_table(wealth: Dict[str, Any]) -> Dict[str, Any] | None:
    yoga = wealth.get("yoga_analysis") or {}
    if not isinstance(yoga, dict):
        return None
    rows = []
    for label, key in (
        ("Dhana", "dhana_yogas"),
        ("Lakshmi / Gaja-Kesari", "lakshmi_yogas"),
        ("Raja", "raja_yogas"),
        ("Viparita Raja", "viparita_yogas"),
    ):
        for item in _as_list(yoga.get(key))[:4]:
            rows.append([label, _yoga_label(item), _yoga_note(item)])
    if not rows:
        total = yoga.get("total_beneficial")
        if total is None:
            return None
        rows.append(["Beneficial yogas counted", str(total), "See narrative for named combinations."])
    return {
        "title": "Money yogas detected",
        "headers": ["Family", "Yoga", "Note"],
        "rows": rows[:12],
    }


def _income_sources_table(wealth: Dict[str, Any]) -> Dict[str, Any] | None:
    sources = wealth.get("income_sources") or []
    rows = []
    for idx, item in enumerate(_as_list(sources)[:8], start=1):
        rows.append([str(idx), _clean(item)[:140]])
    if not rows:
        return None
    return {
        "title": "Income source cues",
        "headers": ["#", "Source"],
        "rows": rows,
    }


def _planet_wealth_table(wealth: Dict[str, Any]) -> Dict[str, Any] | None:
    planet_analysis = wealth.get("planet_analysis") or {}
    if not isinstance(planet_analysis, dict):
        return None
    rows = []
    for planet, row in planet_analysis.items():
        if not isinstance(row, dict):
            continue
        impact = row.get("wealth_impact") or {}
        if isinstance(impact, dict):
            impact_type = _clean(impact.get("impact_type") or impact.get("level"), "--")
            note = _clean(impact.get("summary") or impact.get("description"), "--")[:80]
        else:
            impact_type = _clean(impact, "--")
            note = "--"
        systems = row.get("wealth_systems") or []
        rows.append([
            _clean(planet),
            impact_type,
            ", ".join([_clean(s) for s in _as_list(systems)[:3]]) or "--",
            note,
        ])
    if not rows:
        return None
    return {
        "title": "Planet wealth impact",
        "headers": ["Planet", "Impact", "Systems", "Cue"],
        "rows": rows[:10],
    }


def _lords_nakshatra_table(lords: Dict[str, Any]) -> Dict[str, Any] | None:
    rows = []
    for key, label in (("second_lord", "2nd lord"), ("eleventh_lord", "11th lord")):
        block = lords.get(key) or {}
        nak = block.get("nakshatra") or {}
        if isinstance(nak, dict):
            nak_name = _clean(nak.get("nakshatra") or nak.get("nakshatra_name"), "--")
            pada = _clean(nak.get("pada"), "--")
            deity = _clean(nak.get("deity"), "--")
        else:
            nak_name, pada, deity = "--", "--", "--"
        rows.append([
            label,
            _clean(block.get("planet"), "--"),
            _clean(block.get("house"), "--"),
            nak_name,
            pada,
            deity,
        ])
    if not any(r[1] != "--" for r in rows):
        return None
    return {
        "title": "2nd & 11th lord nakshatra",
        "headers": ["Role", "Planet", "House", "Nakshatra", "Pada", "Deity"],
        "rows": rows,
    }


def _spouse_finance_table(hints: Dict[str, Any]) -> Dict[str, Any] | None:
    if not isinstance(hints, dict) or not hints:
        return None
    rows = [
        ["7th lord", _clean(hints.get("seventh_lord"), "--"), _clean(hints.get("seventh_lord_house"), "--")],
        ["Venus house", "Venus", _clean(hints.get("venus_house"), "--")],
        ["Jupiter house", "Jupiter", _clean(hints.get("jupiter_house"), "--")],
    ]
    return {
        "title": "Spouse & joint-finance markers",
        "headers": ["Point", "Planet", "House"],
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
            score_table = _wealth_score_breakdown_table(wealth)
            if score_table:
                tables.append(score_table)
        elif key == "score_architecture":
            score_table = _wealth_score_breakdown_table(wealth)
            if score_table:
                tables.append(score_table)
            houses = _wealth_houses_table(wealth)
            if houses:
                tables.append(houses)
            yogas = _wealth_yogas_table(wealth)
            if yogas:
                tables.append(yogas)
        elif key == "d1_wealth_foundation":
            houses = _wealth_houses_table(wealth)
            if houses:
                tables.append(houses)
            planets = _planet_wealth_table(wealth)
            if planets:
                tables.append(planets)
        elif key == "dhana_money_yogas":
            yogas = _wealth_yogas_table(wealth)
            if yogas:
                tables.append(yogas)
        elif key == "money_psychology":
            planets = _planet_wealth_table(wealth)
            if planets:
                # Prefer Moon/Venus/Mercury rows when present
                filtered = [r for r in (planets.get("rows") or []) if r and r[0] in {"Moon", "Venus", "Mercury", "Jupiter"}]
                if filtered:
                    tables.append({
                        "title": "Earn–spend psychology planets",
                        "headers": planets.get("headers"),
                        "rows": filtered,
                    })
                else:
                    tables.append(planets)
        elif key == "income_engines":
            planets = _planet_wealth_table(wealth)
            if planets:
                tables.append(planets)
        elif key == "sources_of_wealth":
            sources = _income_sources_table(wealth)
            if sources:
                tables.append(sources)
        elif key == "assets_property_inheritance":
            houses = _wealth_houses_table(wealth)
            if houses:
                focus = [r for r in (houses.get("rows") or []) if r and str(r[0]).startswith(("4", "8", "9"))]
                if focus:
                    tables.append({
                        "title": "Assets / inheritance houses",
                        "headers": houses.get("headers"),
                        "rows": focus,
                    })
                else:
                    tables.append(houses)
        elif key == "debt_loss_sudden":
            houses = _wealth_houses_table(wealth)
            if houses:
                focus = [r for r in (houses.get("rows") or []) if r and str(r[0]).startswith(("6", "8", "12", "5"))]
                if focus:
                    tables.append({
                        "title": "Leakage & sudden-money houses",
                        "headers": houses.get("headers"),
                        "rows": focus,
                    })
                else:
                    tables.append(houses)
        elif key == "current_dasha_theme":
            metrics = [
                _metric("Mahadasha", (dashas.get("mahadasha") or {}).get("planet") or "--"),
                _metric("Antardasha", (dashas.get("antardasha") or {}).get("planet") or "--"),
                _metric("Pratyantardasha", (dashas.get("pratyantardasha") or {}).get("planet") or "--"),
            ]
            if months[:3]:
                tables.append(_quarter_table(months, 0))
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
            lord_table = _lords_nakshatra_table(lords)
            if lord_table:
                tables.append(lord_table)
        elif key == "spouse_joint_finances":
            spouse = _spouse_finance_table(context.get("spouse_finance_hints") or {})
            if spouse:
                tables.append(spouse)
        elif key == "speculation_vs_investing":
            trading = context.get("trading_luck") or {}
            metrics = [
                _metric("Trading tone", trading.get("recommendation") or trading.get("signal") or "--"),
                _metric("Luck score", trading.get("final_score") or trading.get("score") or "--"),
            ]
            trading_rows = []
            for label, field in (
                ("Signal", "signal"),
                ("Recommendation", "recommendation"),
                ("Score", "final_score"),
                ("Risk note", "risk_note"),
            ):
                if field == "final_score":
                    val = trading.get("final_score") or trading.get("score")
                else:
                    val = trading.get(field)
                if val:
                    trading_rows.append([label, _clean(val)[:100]])
            if trading_rows:
                tables.append({
                    "title": "Speculation vs investing snapshot",
                    "headers": ["Metric", "Value"],
                    "rows": trading_rows,
                })
        elif key == "action_plan_remedies":
            sources = _income_sources_table(wealth)
            if sources:
                tables.append(sources)
        elif key == "wealth_roadmap_checklist":
            score_table = _wealth_score_breakdown_table(wealth)
            if score_table:
                tables.append(score_table)

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
