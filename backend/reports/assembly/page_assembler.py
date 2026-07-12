from __future__ import annotations

from typing import Any, Dict, Iterable, List

from ..models import ReportMetric, ReportPage


MASTER_PAGE_BLUEPRINT = [
    {"num": 1, "key": "cover", "title": "Partnership Compatibility Report", "subtitle": "Master Vedic relationship study", "charts": []},
    {"num": 2, "key": "executive_verdict", "title": "Executive Verdict", "subtitle": "The clear go / no-go judgement", "charts": []},
    {"num": 3, "key": "score_architecture", "title": "How Compatibility Layers Fit Together", "subtitle": "Why the final reading is more than Guna Milan alone", "charts": []},
    {"num": 4, "key": "nakshatra_moon_nature", "title": "Moon Nakshatra Nature", "subtitle": "Core emotional character of each Moon nakshatra and pada", "charts": []},
    {"num": 5, "key": "nakshatra_venus_seventh_lord", "title": "Venus and 7th Lord Nakshatra", "subtitle": "Desire style and partner-seeking nature by nakshatra and pada", "charts": []},
    {"num": 6, "key": "moon_emotional_rhythm", "title": "Moon and Emotional Rhythm", "subtitle": "How both people feel, react, and seek comfort", "charts": []},
    {"num": 7, "key": "communication_mental_rapport", "title": "Communication and Mental Rapport", "subtitle": "Graha Maitri, Varna, Mercury, and daily repair style", "charts": []},
    {"num": 8, "key": "physical_chemistry_biology", "title": "Physical Chemistry and Biological Compatibility", "subtitle": "Venus, Mars, attraction flow, and Nadi", "charts": []},
    {"num": 9, "key": "person_a_d1_marriage_foundation", "title": "{boy_name}: D1 Marriage Foundation", "subtitle": "Rashi chart promise and visible relationship karma", "charts": ["boy_d1"]},
    {"num": 10, "key": "person_b_d1_marriage_foundation", "title": "{girl_name}: D1 Marriage Foundation", "subtitle": "Rashi chart promise and visible relationship karma", "charts": ["girl_d1"]},
    {"num": 11, "key": "jaimini_upapada_environment", "title": "Jaimini Upapada Lagna", "subtitle": "The inner marriage environment", "charts": []},
    {"num": 12, "key": "darapada_a7_manifestation", "title": "Darapada A7 Manifestation", "subtitle": "How the relationship becomes visible in real life", "charts": []},
    {"num": 13, "key": "person_a_d9_navamsa", "title": "{boy_name}: D9 Navamsa", "subtitle": "How marriage matures for this person", "charts": ["boy_d9"]},
    {"num": 14, "key": "person_b_d9_navamsa", "title": "{girl_name}: D9 Navamsa", "subtitle": "How marriage matures for this person", "charts": ["girl_d9"]},
    {"num": 15, "key": "navamsa_pair_durability", "title": "Navamsa Pair Durability", "subtitle": "Whether the bond grows together or drifts apart", "charts": []},
    {"num": 16, "key": "wealth_financial_synergy", "title": "Wealth and Financial Synergy", "subtitle": "Savings, risk appetite, joint assets, and gains", "charts": []},
    {"num": 17, "key": "d2_kp_wealth_manifestation", "title": "D2 and KP Wealth Manifestation", "subtitle": "Whether prosperity physically materializes", "charts": ["boy_d2", "girl_d2"]},
    {"num": 18, "key": "progeny_family_expansion", "title": "Progeny and Family Expansion", "subtitle": "5th house, 9th house, Jupiter, and Nadi", "charts": []},
    {"num": 19, "key": "d7_parenting_legacy", "title": "D7 Saptamsha and Parenting", "subtitle": "Children, parenting style, and family legacy", "charts": ["boy_d7", "girl_d7"]},
    {"num": 20, "key": "career_public_life", "title": "Career, Ambition, and Public Life", "subtitle": "How the partnership affects status and work", "charts": []},
    {"num": 21, "key": "beliefs_intellect_dharma", "title": "Beliefs, Intellect, and Shared Dharma", "subtitle": "5th and 9th house alignment in real life", "charts": []},
    {"num": 22, "key": "dosha_demystification", "title": "Dosha Demystification", "subtitle": "Manglik, Bhakoot, Gana, Nadi, and cancellations", "charts": []},
    {"num": 23, "key": "d60_karmic_layer", "title": "D60 Karmic Layer", "subtitle": "Soul residue and repeated patterns", "charts": []},
    {"num": 24, "key": "kp_event_materialization", "title": "KP Event Materialization", "subtitle": "Whether formal alliance can happen physically", "charts": []},
    {"num": 25, "key": "dasha_transit_timing", "title": "Dasha and Transit Timing", "subtitle": "Best windows for engagement and marriage", "charts": []},
    {"num": 26, "key": "action_plan_remedies", "title": "Action Plan and Remedies", "subtitle": "Behavioral and Vedic guidance", "charts": []},
]


def _clean(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).replace("\r", " ").replace("\n", " ").strip()
    return text or fallback


def _humanize_label(value: Any, fallback: str = "--") -> str:
    text = _clean(value, "")
    if not text or text == "--":
        return fallback
    if "_" in text or text == text.lower():
        return " ".join(part.capitalize() for part in text.replace("_", " ").split()) or fallback
    return text


def _confidence_label(score: Dict[str, Any], recommendation: Dict[str, Any]) -> str:
    explicit = _clean(recommendation.get("confidence"))
    if explicit and explicit != "--":
        return _humanize_label(explicit)
    grade = _clean(score.get("grade")).lower()
    pct = score.get("percentage")
    try:
        pct_val = float(pct)
    except Exception:
        pct_val = None
    if grade in {"excellent", "good"} or (pct_val is not None and pct_val >= 70):
        return "High"
    if grade in {"average"} or (pct_val is not None and pct_val >= 55):
        return "Moderate"
    if grade in {"delicate", "challenging"} or (pct_val is not None and pct_val < 55):
        return "Cautious"
    if recommendation.get("proceed") is True:
        return "Moderate"
    if recommendation.get("proceed") is False:
        return "Cautious"
    return "Moderate"


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


def _section_bullets(section: Dict[str, Any] | None, limit: int = 6) -> List[str]:
    section = section or {}
    out: List[str] = []
    for key in ("key_takeaways", "facts", "supporting_points", "cautions"):
        for item in _as_list(section.get(key)):
            text = _clean(item)
            if text and text not in out and not _looks_like_raw_score(text):
                out.append(text)
    return out[:limit]


def _looks_like_raw_score(text: str) -> bool:
    lowered = text.lower()
    scoreish = ("score:", "score is", "/100", "/36", "/10", "%")
    if any(token in lowered for token in scoreish) and len(text) < 80:
        return True
    return False


def _section_narrative(section: Dict[str, Any] | None) -> List[str]:
    section = section or {}
    parts: List[str] = []
    for key in (
        "interpretation",
        "astrological_basis",
        "practical_guidance",
        "decision_guidance",
        "practical_meaning",
        "ai_interpretation",
    ):
        text = _clean(section.get(key))
        if text and text not in parts:
            parts.append(text)
    return parts


def _evidence(engine_result: Dict[str, Any], key: str, limit: int = 4) -> List[str]:
    return [_clean(item) for item in _as_list((engine_result.get("evidence_summary") or {}).get(key))[:limit] if _clean(item)]


def _window_rows(shared: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    current = shared.get("current_window") or {}
    if current:
        rows.append({
            "Window": "Current period",
            "Climate": _clean(current.get("climate"), "--"),
            "Guidance": _clean(current.get("reason") or current.get("description"), "Use for talks, clarity, and formal planning."),
        })
    for window in _as_list(shared.get("next_favorable_windows"))[:5]:
        if isinstance(window, dict):
            rows.append({
                "Window": f"{_clean(window.get('start_date'), '--')} to {_clean(window.get('end_date'), '--')}",
                "Climate": _clean(window.get("climate"), "--"),
                "Guidance": _clean(window.get("reason") or window.get("description"), "Joint timing support"),
            })
    return rows


def _layer_meaning_rows(score: Dict[str, Any], cross: Dict[str, Any], ashtakoota: Dict[str, Any], shared: Dict[str, Any]) -> List[Dict[str, Any]]:
    moon_band = _clean((cross.get("moon_element_match") or {}).get("band") or (cross.get("moon_element_match") or {}).get("score"), "See Moon chapter")
    chem_band = _clean((cross.get("venus_to_mars") or {}).get("band") or (cross.get("venus_to_mars") or {}).get("score"), "See chemistry chapter")
    return [
        {
            "Layer": "Blended reading",
            "Plain meaning": f"{_clean(score.get('grade'), 'Mixed')} overall tone — a synthesis of matching, chemistry, durability, dosha, and timing rather than one calculator.",
        },
        {
            "Layer": "Guna Milan",
            "Plain meaning": f"Traditional guna support sits near {_clean(ashtakoota.get('effective_total_score'), '--')}/36 after exceptions; useful, but incomplete alone.",
        },
        {
            "Layer": "Emotional rhythm",
            "Plain meaning": f"Moon comfort and stress language read as {moon_band}.",
        },
        {
            "Layer": "Physical chemistry",
            "Plain meaning": f"Venus-Mars attraction and passion response read as {chem_band}.",
        },
        {
            "Layer": "Joint timing",
            "Plain meaning": f"Current shared climate readiness is {_clean(shared.get('joint_readiness_score'), '--')}% — see the timing chapter for windows.",
        },
    ]


def _ashtakoota_meaning_notes(ashtakoota: Dict[str, Any], limit: int = 6) -> List[str]:
    notes: List[str] = []
    for item in _as_list(ashtakoota.get("kootas") or ashtakoota.get("breakdown")):
        if not isinstance(item, dict):
            continue
        name = _clean(item.get("name") or item.get("koota"), "Koota")
        meaning = _clean(item.get("meaning") or item.get("interpretation"))
        if meaning:
            notes.append(f"{name}: {meaning}")
        elif item.get("score") is not None:
            notes.append(
                f"{name} contributes {_clean(item.get('score'))} of {_clean(item.get('max_score') or item.get('max'), '—')} toward traditional guna support."
            )
    if not notes:
        notes.append(
            f"Effective Ashtakoota after exceptions is {_clean(ashtakoota.get('effective_total_score'), '--')}/36 — use this as one traditional layer, not the whole verdict."
        )
    return notes[:limit]


def _profile_notes(engine_result: Dict[str, Any], boy_name: str, girl_name: str, *, only: str | None = None, limit: int = 8) -> List[str]:
    notes: List[str] = []
    profiles = engine_result.get("profiles", {}) or {}
    people = []
    if only in (None, "boy"):
        people.append((boy_name, "boy"))
    if only in (None, "girl"):
        people.append((girl_name, "girl"))
    for label, key in people:
        profile = profiles.get(key, {}) or {}
        seventh = profile.get("seventh_house", {}) or {}
        navamsa = profile.get("navamsa_synthesis", {}) or {}
        d1_band = _clean((seventh.get("d1_strength") or {}).get("band") or (seventh.get("d1_strength") or {}).get("score"), "mixed")
        d9_band = _clean((seventh.get("d9_strength") or {}).get("band") or (seventh.get("d9_strength") or {}).get("score"), "mixed")
        nav_band = _clean(navamsa.get("band") or navamsa.get("score"), "mixed")
        root_fruit = _clean(navamsa.get("root_vs_fruit"), "consistent")
        notes.append(f"{label}: D1 marriage promise reads {d1_band}; D9 maturity reads {d9_band}; Navamsa overall is {nav_band} ({root_fruit} root vs fruit).")
        for item in _as_list(navamsa.get("supportive_factors"))[:2]:
            text = _clean(item)
            if text:
                notes.append(f"{label} support: {text}")
        for item in _as_list(navamsa.get("challenging_factors"))[:2]:
            text = _clean(item)
            if text:
                notes.append(f"{label} caution: {text}")
    return notes[:limit]


def _branch_notes(summaries: Dict[str, Any], boy_name: str, girl_name: str, *, only: str | None = None, limit: int = 8) -> List[str]:
    notes: List[str] = []
    people = []
    if only in (None, "boy"):
        people.append((boy_name, "boy"))
    if only in (None, "girl"):
        people.append((girl_name, "girl"))
    for label, person_key in people:
        person = summaries.get(person_key, {}) or {}
        for branch, field in (("Jaimini", "relationship_note"), ("KP", "materialization_note"), ("Nakshatra", "emotional_note"), ("Nadi", "relationship_note"), ("D60", "summary")):
            data = person.get(branch.lower(), {}) or {}
            finding = _clean(data.get(field) or data.get("summary"))
            if finding:
                notes.append(f"{label} · {branch}: {finding}")
    return notes[:limit]


def _nakshatra_row_note(label: str, role: str, row: Dict[str, Any]) -> str:
    if not isinstance(row, dict) or not row.get("nakshatra"):
        return ""
    planet = _clean(row.get("planet"), role)
    parts = [f"{label}: {planet} in {_clean(row.get('nakshatra'))} pada {_clean(row.get('pada'), '--')}"]
    if row.get("nature"):
        parts.append(f"nature {_clean(row.get('nature'))}")
    if row.get("pada_nature"):
        parts.append(f"pada {_clean(row.get('pada_nature'))}")
    chars = [_clean(c) for c in _as_list(row.get("characteristics")) if _clean(c)][:3]
    if chars:
        parts.append("traits " + ", ".join(chars))
    return " — ".join(parts)


def _nakshatra_nature_notes(premium_report: Dict[str, Any], boy_name: str, girl_name: str, key: str, limit: int = 6) -> List[str]:
    evidence = premium_report.get("relationship_nakshatra") or {}
    if not evidence:
        section = (_sections(premium_report).get(key) or {})
        return [_clean(item) for item in _as_list(section.get("facts")) if _clean(item)][:limit]
    notes: List[str] = []
    person_a = evidence.get("person_a") or {}
    person_b = evidence.get("person_b") or {}
    if key == "nakshatra_moon_nature":
        for label, block in ((boy_name, person_a), (girl_name, person_b)):
            note = _nakshatra_row_note(label, "Moon", block.get("moon") or {})
            if note:
                notes.append(note)
    else:
        for label, block in ((boy_name, person_a), (girl_name, person_b)):
            for role, field in (("Venus", "venus"), ("7th lord", "seventh_lord")):
                note = _nakshatra_row_note(label, role, block.get(field) or {})
                if note:
                    notes.append(note)
    if not notes:
        fact_key = "moon_facts" if key == "nakshatra_moon_nature" else "venus_seventh_facts"
        notes = [_clean(item) for item in _as_list(evidence.get(fact_key)) if _clean(item)]
    return notes[:limit]


def assemble_partnership_pages(context: Dict[str, Any], premium_report: Dict[str, Any], engine_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    pair = context["pair"]
    boy = pair["boy"]
    girl = pair["girl"]
    boy_name = _clean(boy.get("name"), "Person A")
    girl_name = _clean(girl.get("name"), "Person B")
    summaries = context.get("summaries", {}) or {}
    score = engine_result.get("overall_score", {}) or {}
    recommendation = engine_result.get("recommendation", {}) or {}
    timing = engine_result.get("timing_overlay", {}) or {}
    shared = timing.get("shared", {}) or {}
    cross = (engine_result.get("relationship_indicators", {}) or {}).get("cross_chart", {}) or {}
    ashtakoota = engine_result.get("ashtakoota", {}) or {}
    sections = _sections(premium_report)
    positive = _evidence(engine_result, "positive_factors")
    caution = _evidence(engine_result, "caution_factors")
    priority_actions = [_clean(item) for item in _as_list(premium_report.get("priority_actions")) if _clean(item)]

    default_summary = (
        premium_report.get("compatibility_verdict")
        or premium_report.get("headline")
        or recommendation.get("verdict")
        or "This chapter combines classical Vedic evidence with a clear reading of how the relationship may feel in daily life."
    )

    pages: List[Dict[str, Any]] = []
    for blueprint in MASTER_PAGE_BLUEPRINT:
        key = blueprint["key"]
        section = sections.get(key) or {}
        title = blueprint["title"].format(boy_name=boy_name, girl_name=girl_name)
        subtitle = blueprint["subtitle"]
        summary = _section_text(
            section,
            "opening_summary",
            "interpretation",
            "ai_interpretation",
            "static_summary",
            fallback=default_summary if blueprint["num"] in {1, 2, 26} else f"This chapter studies {subtitle.lower()} for {boy_name} and {girl_name}.",
        )
        bullets = _section_bullets(section, 5)
        metrics: List[Dict[str, Any]] = []
        tables: List[Dict[str, Any]] = []
        notes = _section_narrative(section)

        if key == "cover":
            metrics = [
                _metric("Overall reading", score.get("grade", recommendation.get("verdict", "--"))),
                _metric("Match tone", recommendation.get("verdict", premium_report.get("headline", "--"))),
                _metric("Guna Milan", f"{_clean(ashtakoota.get('effective_total_score'), '--')}/36"),
                _metric("Timing", _humanize_label((shared.get("current_window") or {}).get("climate"), "See timing")),
            ]
            bullets = [
                "Read the chapters for nakshatra nature, Moon comfort, chemistry, D1/D9 marriage promise, doshas, and timing — not only the cover chips.",
                "This report is a decision document written in astrology language, not a raw calculator printout.",
            ]
            notes = notes or [
                _clean(premium_report.get("compatibility_verdict") or premium_report.get("final_summary") or recommendation.get("verdict")),
            ]
        elif key == "executive_verdict":
            bullets = bullets or [*positive[:3], *caution[:2]]
            metrics = [
                _metric("Confidence", _confidence_label(score, recommendation)),
                _metric("Timing climate", _humanize_label((shared.get("current_window") or {}).get("climate"), "See timing")),
            ]
        elif key == "score_architecture":
            tables = [{"title": "What each compatibility layer means", "rows": _layer_meaning_rows(score, cross, ashtakoota, shared)}]
            if not notes:
                notes = [
                    "Guna Milan is the traditional first filter. Nakshatra nature, Moon rhythm, Venus-Mars chemistry, D1/D9 marriage promise, dosha cancellations, and dasha timing each answer a different question about married life.",
                    "A strong or weak number on one layer does not cancel the rest. Use the chapters that follow to understand how the couple may actually live together.",
                ]
        elif key in {"nakshatra_moon_nature", "nakshatra_venus_seventh_lord"}:
            if not notes:
                notes = _nakshatra_nature_notes(premium_report, boy_name, girl_name, key)
            if not bullets:
                bullets = _section_bullets(section, 5) or list((sections.get(key) or {}).get("facts") or [])[:4]
        elif key in {"moon_emotional_rhythm", "communication_mental_rapport", "physical_chemistry_biology"}:
            if not notes:
                notes = _ashtakoota_meaning_notes(ashtakoota, 5)
        elif key == "dosha_demystification":
            if not notes:
                notes = _ashtakoota_meaning_notes(ashtakoota, 6)
            manglik = ((engine_result.get("manglik") or {}).get("compatibility") or {})
            manglik_note = _clean(manglik.get("description"))
            if manglik_note and manglik_note not in notes:
                notes.insert(0, manglik_note)
        elif key in {"person_a_d1_marriage_foundation", "person_a_d9_navamsa"}:
            if not notes:
                notes = _profile_notes(engine_result, boy_name, girl_name, only="boy")
        elif key in {"person_b_d1_marriage_foundation", "person_b_d9_navamsa"}:
            if not notes:
                notes = _profile_notes(engine_result, boy_name, girl_name, only="girl")
        elif key == "navamsa_pair_durability":
            if not notes:
                notes = _profile_notes(engine_result, boy_name, girl_name)
        elif key in {"jaimini_upapada_environment", "darapada_a7_manifestation", "kp_event_materialization", "d60_karmic_layer"}:
            if not notes:
                notes = _branch_notes(summaries, boy_name, girl_name)
        elif key == "dasha_transit_timing":
            tables = [{"title": "Timing windows", "rows": _window_rows(shared)}]
        elif key == "action_plan_remedies":
            bullets = bullets or [*priority_actions[:6], "Use gemstones only after a personal consultation confirms suitability."]
            tables = [{"title": "Practical next steps", "rows": [
                {"Priority": "Before commitment", "Action": "Discuss family, finances, roles, and conflict rules.", "Why": "Practical clarity prevents chart friction from becoming daily resentment."},
                {"Priority": "During favorable timing", "Action": "Use good windows for formal decisions.", "Why": "Supportive timing helps decisions land cleanly."},
                {"Priority": "During stress periods", "Action": "Slow down and repair communication.", "Why": "Difficult periods exaggerate manageable issues."},
            ]}]
            if "Gemstone suggestions must remain conditional unless a dedicated gemstone safety check is performed." not in notes:
                notes.append("Gemstone suggestions must remain conditional unless a dedicated gemstone safety check is performed.")

        # Deduplicate notes that repeat the opening summary.
        notes = [item for item in notes if item and item != summary]
        if not bullets:
            bullets = [item for item in (
                _section_text(section, "practical_guidance"),
                _section_text(section, "decision_guidance"),
            ) if item and item != summary][:3]

        pages.append(_page(
            blueprint["num"],
            title,
            subtitle,
            summary,
            bullets=bullets,
            metrics=metrics,
            chart_refs=blueprint["charts"],
            tables=tables,
            notes=notes,
            cta="Use this final page as the couple's practical next-step plan." if key == "action_plan_remedies" else None,
        ))
    return pages


def build_chart_manifest(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    style = context.get("chart_style", "both")
    slots = [
        {"slot": "boy_d1", "chart": "D1", "style": "north", "person": "boy"},
        {"slot": "girl_d1", "chart": "D1", "style": "south", "person": "girl"},
        {"slot": "boy_d9", "chart": "D9", "style": "north", "person": "boy"},
        {"slot": "girl_d9", "chart": "D9", "style": "south", "person": "girl"},
        {"slot": "boy_d2", "chart": "D2", "style": "north", "person": "boy"},
        {"slot": "girl_d2", "chart": "D2", "style": "south", "person": "girl"},
        {"slot": "boy_d7", "chart": "D7", "style": "north", "person": "boy"},
        {"slot": "girl_d7", "chart": "D7", "style": "south", "person": "girl"},
        {"slot": "d60_summary", "chart": "D60", "style": "summary"},
    ]
    if style == "north":
        return [slot for slot in slots if slot["style"] in {"north", "summary"}]
    if style == "south":
        return [slot for slot in slots if slot["style"] in {"south", "summary"}]
    return slots
