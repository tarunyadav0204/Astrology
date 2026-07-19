"""Assemble 24-page Janam Kundli pages from fact pack + constrained LLM synthesis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import ReportMetric, ReportPage
from .janam_kundli_i18n import age_title, is_hindi, page_title_subtitle, t, yes_no
from .janam_kundli_labels import (
    format_clock,
    label_activity,
    label_avastha,
    label_colors,
    label_combust,
    label_deity,
    label_dignity,
    label_direction,
    label_element,
    label_friendship,
    label_functional,
    label_gana,
    label_gemstone,
    label_guna,
    label_karana,
    label_nadi,
    label_nakshatra,
    label_nakshatra_quality,
    label_pada_nature,
    label_planet,
    label_planet_abbr,
    label_reason,
    label_remedy_role,
    label_shakti,
    label_sign,
    label_special_roles,
    label_strength,
    label_symbol,
    label_tara,
    label_tara_quality,
    label_tithi,
    label_vara,
    label_vriksha,
    label_weekday,
    label_yoga,
    label_yoni,
    label_yoga_name,
    localize_evidence_text,
)

# Shadbala omitted; honest 24-page blueprint keys (titles localized at assemble time).
JANAM_KUNDLI_PAGE_BLUEPRINT = [
    {"num": 1, "key": "cover", "charts": ["native_d1"]},
    # Merged into cover for PDF density; kept in blueprint for API/LLM section keys.
    {"num": 2, "key": "birth_panchang", "charts": [], "skip_render": True},
    {"num": 3, "key": "primary_charts", "charts": ["native_moon"]},
    {"num": 4, "key": "navamsha", "charts": ["native_d9"]},
    {"num": 5, "key": "planetary_positions", "charts": []},
    {"num": 6, "key": "chalit_chart", "charts": ["native_chalit"]},
    {"num": 7, "key": "dashamsha", "charts": ["native_d10"]},
    {"num": 8, "key": "ashtakavarga", "charts": []},
    {"num": 9, "key": "past_life_blueprint", "charts": []},
    {"num": 10, "key": "personality", "charts": []},
    {"num": 11, "key": "emotional_blueprint", "charts": []},
    {"num": 12, "key": "education_intellect", "charts": []},
    {"num": 13, "key": "career_profession", "charts": ["native_d10"]},
    {"num": 14, "key": "wealth_finances", "charts": []},
    {"num": 15, "key": "love_relationships", "charts": ["native_d9"]},
    {"num": 16, "key": "health_profiles", "charts": []},
    {"num": 17, "key": "major_yogas", "charts": []},
    {"num": 18, "key": "dosha_checks", "charts": []},
    {"num": 19, "key": "sade_sati", "charts": []},
    {"num": 20, "key": "dasha_tree", "charts": []},
    {"num": 21, "key": "present_phase", "charts": []},
    {"num": 22, "key": "gemstones", "charts": []},
    {"num": 23, "key": "practical_remedies", "charts": []},
    {"num": 24, "key": "closing_guidance", "charts": []},
]

AGE_HEADER_KEYS = {
    "education_intellect",
    "career_profession",
    "wealth_finances",
    "love_relationships",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value:
        return [value]
    return []


def _metric(label: str, value: Any, tone: str | None = None) -> Dict[str, Any]:
    text = _clean(value)
    return ReportMetric(label=label, value=text if text else "—", tone=tone).model_dump()


def _page(
    num: int,
    title: str,
    subtitle: str,
    summary: Optional[str],
    *,
    bullets=None,
    metrics=None,
    chart_refs=None,
    tables=None,
    notes=None,
    section_key: str | None = None,
    skip_render: bool = False,
) -> Dict[str, Any]:
    return ReportPage(
        page_number=num,
        title=title,
        subtitle=subtitle or None,
        summary=_clean(summary) or None,
        bullets=[_clean(item) for item in (bullets or []) if _clean(item)],
        metrics=list(metrics or []),
        chart_refs=[_clean(ref) for ref in (chart_refs or []) if _clean(ref)],
        tables=list(tables or []),
        notes=[_clean(item) for item in (notes or []) if _clean(item)],
        cta=None,
        section_key=section_key,
        skip_render=skip_render,
    ).model_dump()


def _sections(premium_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        _clean(section.get("key")): section
        for section in _as_list(premium_report.get("sections"))
        if isinstance(section, dict) and _clean(section.get("key"))
    }


def _section_text(section: Dict[str, Any] | None, *keys: str) -> str:
    section = section or {}
    for key in keys:
        text = _clean(section.get(key))
        if text:
            return text
    return ""


def _section_bullets(section: Dict[str, Any] | None, limit: int = 5) -> List[str]:
    section = section or {}
    takeaways = [_clean(item) for item in _as_list(section.get("key_takeaways")) if _clean(item)]
    return takeaways[:limit]


def _panchang_table(
    panchang: Dict[str, Any],
    fact_pack: Dict[str, Any],
    language: str,
    *,
    compact: bool = False,
) -> Dict[str, Any]:
    asc = fact_pack.get("ascendant") or {}
    moon = fact_pack.get("moon") or {}
    sun_sign = (fact_pack.get("life_themes") or {}).get("sun", {}).get("sign_name")
    labels = [
        (t(language, "Tithi", "तिथि"), label_tithi(panchang.get("tithi") or panchang.get("tithi_name"), language)),
        (t(language, "Vara", "वार"), label_vara(panchang.get("vara") or panchang.get("weekday") or panchang.get("day"), language)),
        (
            t(language, "Nakshatra", "नक्षत्र"),
            label_nakshatra(
                _nested_or_plain(panchang.get("nakshatra") or panchang.get("nakshatra_name") or moon.get("nakshatra")),
                language,
            ),
        ),
        (t(language, "Yoga", "योग"), label_yoga(panchang.get("yoga") or panchang.get("yoga_name"), language)),
        (t(language, "Karana", "करण"), label_karana(panchang.get("karana") or panchang.get("karana_name"), language)),
        (t(language, "Sun sign", "सूर्य राशि"), label_sign(sun_sign, language)),
        (t(language, "Moon sign", "चंद्र राशि"), label_sign(moon.get("sign_name"), language)),
        (t(language, "Ascendant", "लग्न"), label_sign(asc.get("sign_name"), language)),
    ]
    if not compact:
        labels.extend([
            (t(language, "Sunrise", "सूर्योदय"), format_clock(panchang.get("sunrise") or panchang.get("sunrise_local"))),
            (t(language, "Sunset", "सूर्यास्त"), format_clock(panchang.get("sunset") or panchang.get("sunset_local"))),
            (t(language, "Ayanamsa", "अयनांश"), _clean(fact_pack.get("ayanamsa"))),
        ])
    rows = [[label, value or "—"] for label, value in labels]
    return {
        "title": t(language, "Birth Panchang", "जन्म पंचांग"),
        "headers": [t(language, "Factor", "तथ्य"), t(language, "Value", "मान")],
        "rows": rows,
        "compact": True,
    }


def _nested_or_plain(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("nakshatra_name") or "").strip()
    return _clean(value)


def _nak_pada_cell(row: Dict[str, Any], language: str) -> str:
    nak = label_nakshatra(row.get("nakshatra"), language) or "—"
    pada = row.get("pada")
    if pada is None or pada == "":
        return nak
    return f"{nak} · {pada}"


def _sign_house_cell(row: Dict[str, Any], language: str) -> str:
    sign = label_sign(row.get("sign_name"), language) or "—"
    house = row.get("house")
    if house is None or house == "":
        return sign
    return f"{sign} / {house}"


def _friendship_cell(row: Dict[str, Any], language: str) -> str:
    natural = label_friendship(row.get("natural_friendship"), language) or "—"
    temporal = label_friendship(row.get("temporal_friendship"), language) or "—"
    compound = label_friendship(row.get("compound_friendship"), language) or "—"
    if is_hindi(language):
        return f"प्राकृतिक {natural} · तात्कालिक {temporal} → {compound}"
    return f"N {natural} · T {temporal} → {compound}"


def _houses_ruled_cell(row: Dict[str, Any]) -> str:
    houses = row.get("houses_ruled") or []
    if not houses:
        return "—"
    return ", ".join(str(h) for h in houses)


def _aspects_cell(row: Dict[str, Any], language: str) -> str:
    raw = _clean(row.get("aspects_received"))
    if not raw or raw == "—":
        return "—"
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return ", ".join(label_planet_abbr(p, language) for p in parts) or "—"


def _planet_placement_table(rows: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    table_rows = []
    for row in rows:
        table_rows.append([
            label_planet(row.get("planet"), language) or "—",
            _sign_house_cell(row, language),
            _clean(row.get("degree")) or "—",
            _nak_pada_cell(row, language),
            label_dignity(row.get("dignity"), language) or "—",
            yes_no(language, bool(row.get("retrograde"))),
            label_combust(row.get("combustion_status"), language),
        ])
    return {
        "title": t(language, "Planet analysis — placement & dignity", "ग्रह विश्लेषण — स्थिति और बल"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Sign / House", "राशि / भाव"),
            t(language, "Deg", "अंश"),
            t(language, "Nakshatra · Pada", "नक्षत्र · पद"),
            t(language, "Dignity", "दशा"),
            t(language, "Retro", "वक्री"),
            t(language, "Combust", "अस्त"),
        ],
        "rows": table_rows,
    }


def _planet_relations_table(rows: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    table_rows = []
    for row in rows:
        gandanta = (
            yes_no(language, True)
            if row.get("gandanta")
            else "—"
        )
        if row.get("gandanta") and row.get("gandanta_intensity"):
            intensity = label_strength(row.get("gandanta_intensity"), language) or _clean(row.get("gandanta_intensity"))
            gandanta = f"{gandanta} ({intensity})"
        table_rows.append([
            label_planet(row.get("planet"), language) or "—",
            _friendship_cell(row, language),
            label_functional(row.get("functional_nature"), language) or "—",
            _houses_ruled_cell(row),
            label_planet(row.get("dispositor"), language) or "—",
            _aspects_cell(row, language),
            gandanta,
            label_special_roles(row.get("special_roles"), language),
            label_avastha(row.get("avastha"), language),
        ])
    return {
        "title": t(language, "Planet analysis — relations & conditions", "ग्रह विश्लेषण — संबंध और अवस्था"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Friendship (vs dispositor)", "मित्रता (भावेश से)"),
            t(language, "Functional", "कार्यात्मक"),
            t(language, "Lordship", "स्वामित्व"),
            t(language, "Dispositor", "नियामक"),
            t(language, "Aspects ←", "दृष्टि ←"),
            t(language, "Gandanta", "गंडांत"),
            t(language, "Special", "विशेष"),
            t(language, "Avastha", "अवस्था"),
        ],
        "rows": table_rows,
    }


def _planet_table(rows: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
    """Full D1 planet analysis as two compact tables."""
    if not rows:
        return []
    return [_planet_placement_table(rows, language), _planet_relations_table(rows, language)]


def _planet_short_table(rows: List[Dict[str, Any]], language: str, *, title_en: str, title_hi: str) -> Dict[str, Any]:
    table_rows = []
    for row in rows:
        table_rows.append([
            label_planet(row.get("planet"), language) or "—",
            _sign_house_cell(row, language),
            label_dignity(row.get("dignity"), language) or "—",
            _nak_pada_cell(row, language),
        ])
    return {
        "title": t(language, title_en, title_hi),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Sign / House", "राशि / भाव"),
            t(language, "Dignity", "दशा"),
            t(language, "Nakshatra · Pada", "नक्षत्र · पद"),
        ],
        "rows": table_rows,
    }


def _special_points_table(points: Dict[str, Any], language: str) -> Dict[str, Any]:
    def _row(label_en: str, label_hi: str, key: str) -> List[str]:
        raw = points.get(key) if isinstance(points.get(key), dict) else {}
        lord = label_planet(raw.get("lord"), language) or "—"
        sign = label_sign(raw.get("sign_name"), language) or "—"
        return [t(language, label_en, label_hi), f"{lord} · {sign}"]

    rows = [
        _row("Yogi", "योगी", "yogi"),
        _row("Avayogi", "अवयोगी", "avayogi"),
        _row("Tithi Shunya", "तिथि शून्य", "tithi_shunya_rashi"),
        _row("Dagdha Rashi", "दग्ध राशि", "dagdha_rashi"),
    ]
    overlap = points.get("avayogi_tithi_shunya_overlap") if isinstance(points.get("avayogi_tithi_shunya_overlap"), dict) else {}
    if overlap.get("is_active"):
        planet = label_planet(overlap.get("planet"), language) or "—"
        rows.append([
            t(language, "Avayogi = Tithi Shunya", "अवयोगी = तिथि शून्य"),
            planet,
        ])
    return {
        "title": t(language, "Special points", "विशेष बिंदु"),
        "headers": [t(language, "Point", "बिंदु"), t(language, "Lord · Sign", "स्वामी · राशि")],
        "rows": rows,
    }


def _sav_table(scores: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    ordered = sorted(scores, key=lambda r: int(r.get("house") or 0))
    return {
        "title": t(language, "Sarvashtakavarga by house", "भावानुसार सर्वाष्टकवर्ग"),
        "headers": [
            t(language, "House", "भाव"),
            t(language, "Sign", "राशि"),
            t(language, "Bindus", "बिंदु"),
        ],
        "rows": [
            [str(r.get("house")), label_sign(r.get("sign_name"), language) or "—", str(r.get("bindus"))]
            for r in ordered
        ],
    }


def _bhinnashtakavarga_table(bav_rows: List[Dict[str, Any]], language: str) -> Optional[Dict[str, Any]]:
    """Planet × house bindu matrix (houses counted from lagna)."""
    if not bav_rows:
        return None
    house_headers = [str(h) for h in range(1, 13)]
    rows = []
    for row in bav_rows:
        houses = row.get("houses") or []
        if len(houses) != 12:
            continue
        rows.append([
            label_planet(row.get("planet"), language) or _clean(row.get("planet")) or "—",
            *[str(v) for v in houses],
            str(row.get("total") if row.get("total") is not None else sum(int(x) for x in houses)),
        ])
    if not rows:
        return None
    return {
        "title": t(
            language,
            "Bhinnashtakavarga (bindus by house from lagna)",
            "भिन्नाष्टकवर्ग (लग्न से भावानुसार बिंदु)",
        ),
        "headers": [
            t(language, "Planet", "ग्रह"),
            *house_headers,
            t(language, "Total", "योग"),
        ],
        "rows": rows,
        "compact": True,
    }


def _nakshatra_identity_table(moon: Dict[str, Any], asc: Dict[str, Any], language: str) -> Dict[str, Any]:
    def _body_rows(body: Dict[str, Any], role_en: str, role_hi: str) -> List[List[str]]:
        if not body:
            return []
        deg = body.get("degrees_in_nakshatra")
        deg_s = f"{deg}°" if deg is not None and deg != "" else "—"
        house_label = (
            f"भाव {body.get('house')}" if is_hindi(language) else f"H{body.get('house')}"
        ) if body.get("house") else ""
        sign_house = " · ".join(
            p for p in [
                label_sign(body.get("sign_name"), language) or "",
                house_label,
            ] if p
        ) or "—"
        return [
            [t(language, role_en, role_hi), label_nakshatra(body.get("nakshatra"), language) or "—"],
            [t(language, f"{role_en} pada", f"{role_hi} पद"), str(body.get("pada") or "—")],
            [t(language, f"{role_en} lord", f"{role_hi} स्वामी"), label_planet(body.get("lord"), language) or "—"],
            [t(language, f"{role_en} deity", f"{role_hi} देवता"), label_deity(body.get("deity"), language) or "—"],
            [t(language, f"{role_en} degrees", f"{role_hi} अंश"), deg_s],
            [t(language, f"{role_en} sign / house", f"{role_hi} राशि / भाव"), sign_house],
        ]

    rows = _body_rows(moon, "Moon", "चंद्र") + _body_rows(asc, "Ascendant", "लग्न")
    return {
        "title": t(language, "Nakshatra identity", "नक्षत्र पहचान"),
        "headers": [t(language, "Fact", "तथ्य"), t(language, "Value", "मान")],
        "rows": rows,
    }


def _nakshatra_nature_table(moon: Dict[str, Any], language: str) -> Dict[str, Any]:
    rows = [
        [t(language, "Gana", "गण"), label_gana(moon.get("gana"), language) or "—"],
        [t(language, "Nadi", "नाड़ी"), label_nadi(moon.get("nadi"), language) or "—"],
        [t(language, "Yoni", "योनि"), label_yoni(moon.get("yoni"), language) or "—"],
        [t(language, "Guna", "गुण"), label_guna(moon.get("guna"), language) or "—"],
        [t(language, "Element", "तत्त्व"), label_element(moon.get("element"), language) or "—"],
        [
            t(language, "Quality", "प्रकृति"),
            label_nakshatra_quality(moon.get("quality"), language)
            or _clean(moon.get("quality") or moon.get("nature"))
            or "—",
        ],
        [t(language, "Symbol", "प्रतीक"), label_symbol(moon.get("symbol"), language) or "—"],
        [t(language, "Animal", "पशु"), label_yoni(moon.get("animal"), language) or _clean(moon.get("animal")) or "—"],
    ]
    return {
        "title": t(language, "Moon nakshatra nature", "चंद्र नक्षत्र स्वभाव"),
        "headers": [t(language, "Trait", "लक्षण"), t(language, "Value", "मान")],
        "rows": rows,
    }


def _nakshatra_pada_table(moon: Dict[str, Any], language: str) -> Dict[str, Any]:
    return {
        "title": t(language, "Pada details", "पद विवरण"),
        "headers": [t(language, "Fact", "तथ्य"), t(language, "Value", "मान")],
        "rows": [
            [t(language, "Pada", "पद"), str(moon.get("pada") or "—")],
            [t(language, "Pada lord", "पद स्वामी"), label_planet(moon.get("pada_lord"), language) or "—"],
            [t(language, "Pada element", "पद तत्त्व"), label_element(moon.get("pada_element"), language) or "—"],
            [t(language, "Pada nature", "पद स्वभाव"), label_pada_nature(moon.get("pada_nature"), language) or "—"],
            [t(language, "Pada syllable", "पद अक्षर"), _clean(moon.get("pada_syllable")) or "—"],
        ],
    }


def _dasha_level_label(level_label: Any, language: str) -> str:
    key = _clean(level_label)
    mapping = {
        "Mahadasha": ("Mahadasha", "महादशा"),
        "Antardasha": ("Antardasha", "अन्तर्दशा"),
        "Pratyantardasha": ("Pratyantardasha", "प्रत्यन्तर्दशा"),
    }
    pair = mapping.get(key)
    if pair:
        return t(language, pair[0], pair[1])
    return key or "—"


def _tara_bal_table(tara_bal: Dict[str, Any], language: str) -> Optional[Dict[str, Any]]:
    levels = tara_bal.get("levels") if isinstance(tara_bal, dict) else None
    if not isinstance(levels, list) or not levels:
        return None
    rows = []
    for row in levels:
        if not isinstance(row, dict):
            continue
        rows.append([
            _dasha_level_label(row.get("level_label") or row.get("level"), language),
            label_planet(row.get("planet"), language) or "—",
            label_nakshatra(row.get("nakshatra"), language) or "—",
            label_tara(row.get("tara_name"), language) or "—",
            label_tara_quality(row.get("tara_quality") or row.get("tara_effect"), language) or "—",
        ])
    if not rows:
        return None
    return {
        "title": t(language, "Tara Bal (Navatara) — current dasha", "तारा बल (नव तारा) — वर्तमान दशा"),
        "headers": [
            t(language, "Level", "स्तर"),
            t(language, "Planet", "ग्रह"),
            t(language, "Nakshatra", "नक्षत्र"),
            t(language, "Tara", "तारा"),
            t(language, "Effect", "प्रभाव"),
        ],
        "rows": rows,
    }


def _nakshatra_planet_matrix_table(rows: List[Dict[str, Any]], language: str) -> Optional[Dict[str, Any]]:
    if not rows:
        return None
    table_rows = []
    for row in rows:
        table_rows.append([
            label_planet(row.get("planet"), language) or "—",
            label_nakshatra(row.get("nakshatra"), language) or "—",
            str(row.get("pada") or "—"),
            label_planet(row.get("lord"), language) or "—",
            label_deity(row.get("deity"), language) or "—",
        ])
    return {
        "title": t(language, "All-planet nakshatra matrix", "सभी ग्रहों की नक्षत्र सारिणी"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Nakshatra", "नक्षत्र"),
            t(language, "Pada", "पद"),
            t(language, "Lord", "स्वामी"),
            t(language, "Deity", "देवता"),
        ],
        "rows": table_rows,
    }


def _nakshatra_remedy_table(remedy: Dict[str, Any], language: str) -> Optional[Dict[str, Any]]:
    if not isinstance(remedy, dict) or not remedy:
        return None
    rows = [
        [t(language, "Deity", "देवता"), label_deity(remedy.get("deity"), language) or "—"],
        [t(language, "Shakti", "शक्ति"), label_shakti(remedy.get("shakti"), language) or "—"],
        [t(language, "Mantra", "मंत्र"), _clean(remedy.get("mantra")) or "—"],
        [t(language, "Tree (vriksha)", "वृक्ष"), label_vriksha(remedy.get("vriksha"), language) or "—"],
        [t(language, "Pada syllable", "पद अक्षर"), _clean(remedy.get("pada_syllable")) or "—"],
        [t(language, "Direction", "दिशा"), label_direction(remedy.get("optimal_direction"), language) or "—"],
        [
            t(language, "Aligned activity", "अनुकूल कर्म"),
            label_activity(remedy.get("aligned_activity"), language) or "—",
        ],
    ]
    return {
        "title": t(language, "Moon nakshatra remedy strip", "चंद्र नक्षत्र उपाय"),
        "headers": [t(language, "Item", "विषय"), t(language, "Detail", "विवरण")],
        "rows": rows,
    }


def _yoga_category_label(category_key: Any, language: str) -> str:
    key = _clean(category_key)
    labels = {
        "raj_yogas": ("Raj Yogas", "राज योग"),
        "dhana_yogas": ("Dhana Yogas", "धन योग"),
        "mahapurusha_yogas": ("Panch Mahapurusha", "पंच महापुरुष"),
        "neecha_bhanga_yogas": ("Neecha Bhanga", "नीच भंग"),
        "gaja_kesari_yogas": ("Gaja Kesari", "गज केसरी"),
        "amala_yogas": ("Amala Yogas", "अमल योग"),
        "viparita_raja_yogas": ("Viparita Raja", "विपरीत राज"),
        "dharma_karma_yogas": ("Dharma-Karma", "धर्म-कर्म"),
        "nabhasa_yogas_sankhya_yogas": ("Nabhasa · Sankhya", "नाभस · संख्या"),
        "nabhasa_yogas_akriti_yogas": ("Nabhasa · Akriti", "नाभस · आकृति"),
        "nabhasa_yogas_ashraya_yogas": ("Nabhasa · Ashraya", "नाभस · आश्रय"),
        "chandra_yogas": ("Chandra Yogas", "चंद्र योग"),
        "surya_yogas": ("Surya Yogas", "सूर्य योग"),
        "parivartana_yogas_maha_yogas": ("Parivartana · Maha", "परिवर्तन · महा"),
        "parivartana_yogas_dainya_yogas": ("Parivartana · Dainya", "परिवर्तन · दैन्य"),
        "parivartana_yogas_khala_yogas": ("Parivartana · Khala", "परिवर्तन · खल"),
        "parivartana_yogas_other_parivartana_yogas": ("Parivartana · Other", "परिवर्तन · अन्य"),
        "career_specific_yogas": ("Career Yogas", "करियर योग"),
        "health_yogas": ("Health Yogas", "स्वास्थ्य योग"),
        "education_yogas": ("Education Yogas", "शिक्षा योग"),
        "marriage_yogas": ("Marriage Yogas", "विवाह योग"),
    }
    pair = labels.get(key)
    if pair:
        return t(language, pair[0], pair[1])
    pretty = key.replace("_", " ").strip().title() or "—"
    return pretty


def _yoga_polarity_label(polarity: Any, language: str) -> str:
    if str(polarity or "").lower() == "challenging":
        return t(language, "Challenging", "चुनौतीपूर्ण")
    return t(language, "Auspicious", "शुभ")


def _yoga_table(yogas: List[Dict[str, Any]], language: str, *, title_en: str, title_hi: str) -> Dict[str, Any]:
    return {
        "title": t(language, title_en, title_hi),
        "headers": [
            t(language, "Category", "वर्ग"),
            t(language, "Yoga", "योग"),
            t(language, "Type", "प्रकार"),
            t(language, "Strength", "बल"),
            t(language, "Evidence", "आधार"),
        ],
        "rows": [
            [
                _yoga_category_label(y.get("category") or y.get("type"), language),
                label_yoga_name(y.get("name"), language) or "—",
                _yoga_polarity_label(y.get("polarity"), language),
                label_strength(y.get("strength"), language) or "—",
                localize_evidence_text(_clean(y.get("description"))[:180], language) or "—",
            ]
            for y in yogas
        ],
    }


def _dosha_table(doshas: Dict[str, Any], language: str) -> Dict[str, Any]:
    mangal = doshas.get("mangal_dosha") or {}
    kaal = doshas.get("kaal_sarp_dosha") or {}
    pitra = doshas.get("pitra_dosha") or {}
    def _dosha_detail(row: Dict[str, Any]) -> str:
        raw = _clean(row.get("type") or row.get("note") or row.get("strength"))
        if not raw:
            return "—"
        return label_strength(raw, language) or localize_evidence_text(raw, language) or raw

    rows = [
        [
            t(language, "Manglik (Mangal Dosha)", "मांगलिक (मंगल दोष)"),
            yes_no(language, bool(mangal.get("present"))),
            _dosha_detail(mangal if isinstance(mangal, dict) else {}),
        ],
        [
            t(language, "Kaal Sarp Dosha", "काल सर्प दोष"),
            yes_no(language, bool(kaal.get("present"))),
            _dosha_detail(kaal if isinstance(kaal, dict) else {}),
        ],
    ]
    if isinstance(pitra, dict):
        rows.append([
            t(language, "Pitra Dosha check", "पितृ दोष जाँच"),
            yes_no(language, bool(pitra.get("present"))),
            _dosha_detail(pitra),
        ])
    return {
        "title": t(language, "Dosha checklist", "दोष जाँच सूची"),
        "headers": [
            t(language, "Dosha", "दोष"),
            t(language, "Present", "उपस्थिति"),
            t(language, "Detail", "विवरण"),
        ],
        "rows": rows,
    }


def _dasha_table(maha_dashas: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    return {
        "title": t(language, "Mahadasha timeline", "महादशा समयरेखा"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Start", "आरंभ"),
            t(language, "End", "समाप्ति"),
        ],
        "rows": [
            [label_planet(r.get("planet"), language) or "—", _clean(r.get("start")) or "—", _clean(r.get("end")) or "—"]
            for r in maha_dashas[:12]
        ],
    }


def _best_time_cell(row: Dict[str, Any], language: str) -> str:
    if is_hindi(language):
        return _clean(row.get("best_time_hi") or row.get("best_time")) or "—"
    return _clean(row.get("best_time")) or "—"


def _charity_cell(row: Dict[str, Any], language: str) -> str:
    if is_hindi(language):
        return _clean(row.get("charity_hi") or row.get("charity")) or "—"
    return _clean(row.get("charity")) or "—"


def _seva_cell(row: Dict[str, Any], language: str) -> str:
    if is_hindi(language):
        return _clean(row.get("seva_hi") or row.get("seva")) or "—"
    return _clean(row.get("seva")) or "—"


def _actionable_remedies_table(cards: List[Dict[str, Any]], language: str) -> Optional[Dict[str, Any]]:
    if not cards:
        return None
    rows = []
    for card in cards[:4]:
        if not isinstance(card, dict):
            continue
        count = card.get("mantra_count") or 108
        mantra = _clean(card.get("mantra")) or "—"
        rows.append([
            label_planet(card.get("planet"), language) or "—",
            label_remedy_role(card.get("role"), language) or "—",
            label_weekday(card.get("weekday"), language) or "—",
            _best_time_cell(card, language),
            f"{mantra} × {count}",
            _charity_cell(card, language),
        ])
    if not rows:
        return None
    return {
        "title": t(language, "Step-by-step planetary remedies", "ग्रहानुसार चरणबद्ध उपाय"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Role", "भूमिका"),
            t(language, "Best day", "उत्तम दिन"),
            t(language, "Best time", "उत्तम समय"),
            t(language, "Mantra × count", "मंत्र × संख्या"),
            t(language, "Charity / donation", "दान"),
        ],
        "rows": rows,
    }


def _lifestyle_colors_table(lifestyle: Dict[str, Any], language: str) -> Optional[Dict[str, Any]]:
    if not isinstance(lifestyle, dict) or not lifestyle:
        return None
    wear = label_colors(lifestyle.get("wear_colors"), language) or "—"
    support = label_colors(lifestyle.get("support_colors"), language) or "—"
    avoid = label_colors(lifestyle.get("avoid_colors"), language) or "—"
    note = (
        _clean(lifestyle.get("note_hi"))
        if is_hindi(language)
        else _clean(lifestyle.get("note"))
    ) or "—"
    return {
        "title": t(language, "Color therapy (current dasha)", "रंग चिकित्सा (वर्तमान दशा)"),
        "headers": [t(language, "Item", "विषय"), t(language, "Guidance", "मार्गदर्शन")],
        "rows": [
            [
                t(language, "Wear / favor (MD)", "धारण / अनुकूल (महादशा)"),
                wear,
            ],
            [
                t(language, "Support (AD)", "सहायक (अन्तर्दशा)"),
                support,
            ],
            [
                t(language, "Soften / avoid", "कम रखें / बचें"),
                avoid,
            ],
            [
                t(language, "How to use", "कैसे अपनाएँ"),
                note,
            ],
        ],
    }


def _mantra_practice_table(cards: List[Dict[str, Any]], language: str) -> Optional[Dict[str, Any]]:
    if not cards:
        return None
    first = next((c for c in cards if isinstance(c, dict)), None)
    if not first:
        return None
    mala = _clean(first.get("mala_note_hi") if is_hindi(language) else first.get("mala_note")) or "—"
    rows = []
    for card in cards[:4]:
        if not isinstance(card, dict):
            continue
        rows.append([
            label_planet(card.get("planet"), language) or "—",
            _clean(card.get("mantra")) or "—",
            str(card.get("mantra_count") or 108),
            label_direction(card.get("direction"), language) or "—",
            _seva_cell(card, language),
        ])
    return {
        "title": t(language, "Mantra practice details", "मंत्र अभ्यास विवरण"),
        "headers": [
            t(language, "Planet", "ग्रह"),
            t(language, "Mantra", "मंत्र"),
            t(language, "Count", "संख्या"),
            t(language, "Face", "दिशा"),
            t(language, "Lifestyle seva", "सेवा / आदत"),
        ],
        "rows": rows,
        # PDF ignores unknown keys; keep mala tip in assembler notes instead.
        "_mala_note": mala,
    }


def _sade_sati_table(periods: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
    rows = []
    for p in periods[:8]:
        rows.append([
            _clean(p.get("start_date")) or "—",
            _clean(p.get("end_date")) or "—",
            t(language, "Current", "वर्तमान") if p.get("is_current") else "—",
        ])
    return {
        "title": t(language, "Sade Sati periods", "साढ़े साती काल"),
        "headers": [
            t(language, "Start", "आरंभ"),
            t(language, "End", "समाप्ति"),
            t(language, "Status", "स्थिति"),
        ],
        "rows": rows,
    }


def assemble_janam_kundli_pages(context: Dict[str, Any], premium_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    fact = context.get("fact_pack") or {}
    person = context.get("person") or fact.get("person") or {}
    language = _clean(context.get("language") or fact.get("language") or "english") or "english"
    hi = is_hindi(language)
    name = _clean(person.get("name")) or t(language, "Native", "जातक")
    sections = _sections(premium_report)
    bracket = _clean(fact.get("age_bracket")) or "29_50"
    pages: List[Dict[str, Any]] = []

    for bp in JANAM_KUNDLI_PAGE_BLUEPRINT:
        key = bp["key"]
        section = sections.get(key)
        title, subtitle = page_title_subtitle(key, language)
        if key in AGE_HEADER_KEYS:
            title = age_title(key, bracket, language, title)

        summary = _section_text(section, "opening_summary", "interpretation", "static_summary")
        bullets = _section_bullets(section)
        notes = []
        for nk in ("astrological_basis", "practical_guidance", "interpretation"):
            text = _section_text(section, nk)
            if text and text != summary:
                notes.append(text)

        metrics: List[Dict[str, Any]] = []
        tables: List[Dict[str, Any]] = []

        if key == "cover":
            asc = fact.get("ascendant") or {}
            moon = fact.get("moon") or {}
            dasha = (fact.get("dasha") or {}).get("current") or {}
            summary = summary or _clean(premium_report.get("headline")) or (
                f"{name} की जन्म कुंडली" if hi else f"Janam Kundli for {name}"
            )
            metrics = [
                _metric(t(language, "Ascendant", "लग्न"), label_sign(asc.get("sign_name"), language)),
                _metric(t(language, "Moon", "चंद्र"), label_sign(moon.get("sign_name"), language)),
                _metric(
                    t(language, "Current MD", "वर्तमान महादशा"),
                    label_planet((dasha.get("mahadasha") or {}).get("planet"), language),
                ),
                _metric(
                    t(language, "Current AD", "वर्तमान अन्तर्दशा"),
                    label_planet((dasha.get("antardasha") or {}).get("planet"), language),
                ),
            ]
            bullets = bullets or [
                f"{t(language, 'Birth date', 'जन्म तिथि')}: {_clean(person.get('date'))}",
                f"{t(language, 'Birth time', 'जन्म समय')}: {_clean(person.get('time'))}",
                f"{t(language, 'Birth place', 'जन्म स्थान')}: {_clean(person.get('place'))}",
            ]
            # Cover PDF: compact panchang | D1, plus a short planet overview if it fits.
            tables = [_panchang_table(fact.get("panchang") or {}, fact, language, compact=True)]
            planet_rows = fact.get("planet_matrix") or []
            if planet_rows:
                tables.append(
                    _planet_short_table(
                        planet_rows,
                        language,
                        title_en="D1 planet overview",
                        title_hi="डी-१ ग्रह सारिणी",
                    )
                )

        elif key == "birth_panchang":
            tables = [_panchang_table(fact.get("panchang") or {}, fact, language)]
            if not summary:
                summary = (
                    f"{name} के जन्म क्षण से गणना किए गए पंचांग तथ्य।"
                    if hi
                    else f"Birth panchang factors calculated for {name} from the recorded birth moment."
                )

        elif key == "primary_charts":
            tables = _planet_table(fact.get("planet_matrix") or [], language)
            special = fact.get("special_points") or {}
            if special:
                tables = list(tables) + [_special_points_table(special, language)]
            if not summary:
                summary = (
                    "चंद्र कुंडली चंद्र से भावों को पुनः व्यवस्थित करती है; नीचे ग्रह विश्लेषण दी गई है।"
                    if hi
                    else "The Moon chart re-frames houses from the Moon; planetary analysis follows below."
                )
            notes = notes or [
                (
                    "नीचे ग्रह विश्लेषण तालिकाएँ डी-१ स्थितियों पर आधारित हैं; मित्रता नियामक (राशि स्वामी) के सापेक्ष है।"
                    if hi
                    else "Planet analysis tables below are from D1 placements; friendship is scored versus the dispositor (sign lord)."
                ),
            ]

        elif key == "navamsha":
            d9_rows = fact.get("d9_planet_matrix") or []
            if d9_rows:
                tables = [
                    _planet_short_table(
                        d9_rows,
                        language,
                        title_en="D-9 planet matrix",
                        title_hi="डी-९ ग्रह सारिणी",
                    )
                ]
            if not summary:
                summary = (
                    "डी-९ नवांश उसी जन्म आँकड़ों से ग्रह बल तथा गहरे संबंध/मध्यायु संकेत की पुष्टि करता है।"
                    if hi
                    else "D-9 Navamsha confirms planetary dignity and deeper relationship/mid-life strength from the same birth data."
                )

        elif key == "planetary_positions":
            tables = _planet_table(fact.get("planet_matrix") or [], language)
            if not summary:
                summary = (
                    "डी-१ से ग्रह स्थिति, नक्षत्र-पद, दशा, मित्रता, दृष्टि, गंडांत और विशेष भूमिकाएँ।"
                    if hi
                    else "D1 planet placement, nakshatra-pada, dignity, friendship, aspects, gandanta, and special roles."
                )

        elif key == "chalit_chart":
            shifts = fact.get("chalit_house_shifts") or []
            if shifts:
                tables = [{
                    "title": t(language, "D1 vs Chalit house shifts", "डी-१ बनाम चलित भाव परिवर्तन"),
                    "headers": [
                        t(language, "Planet", "ग्रह"),
                        t(language, "D1 house", "डी-१ भाव"),
                        t(language, "Chalit house", "चलित भाव"),
                    ],
                    "rows": [
                        [label_planet(s.get("planet"), language), str(s.get("d1_house")), str(s.get("chalit_house"))]
                        for s in shifts
                    ],
                }]
                if not summary:
                    summary = (
                        f"इस कुंडली में {len(shifts)} ग्रह डी-१ और चलित में भाव बदलते हैं।"
                        if hi
                        else f"{len(shifts)} planet(s) change house between D1 and Chalit for this chart."
                    )
            else:
                if not summary:
                    summary = (
                        "गणना किए गए भाव चलित में कोई ग्रह डी-१ से भाव नहीं बदलता।"
                        if hi
                        else "No planet changes house between D1 and Chalit in the calculated bhava chalita for this chart."
                    )
                bullets = bullets or [
                    (
                        "मुख्य ग्रहों के लिए डी-१ और चलित भाव स्थान मेल खाते हैं।"
                        if hi
                        else "D1 house placements and Chalit house placements match for the core planets."
                    )
                ]

        elif key == "dashamsha":
            d10_rows = fact.get("d10_planet_matrix") or []
            if d10_rows:
                tables = [
                    _planet_short_table(
                        d10_rows,
                        language,
                        title_en="D-10 planet matrix",
                        title_hi="डी-१० ग्रह सारिणी",
                    )
                ]
            if not summary:
                summary = (
                    "डी-१० दशांश उसी जन्म आँकड़ों से व्यावसायिक अधिकार कुंडली है।"
                    if hi
                    else "D-10 Dashamsha is the professional authority chart derived from the same birth data."
                )

        elif key == "ashtakavarga":
            av = fact.get("ashtakavarga") or {}
            tables = [_sav_table(av.get("house_scores") or [], language)]
            bav_table = _bhinnashtakavarga_table(av.get("bhinnashtakavarga") or [], language)
            if bav_table:
                tables.append(bav_table)
            strong = av.get("strongest") or {}
            weak = av.get("weakest") or {}
            def _house_metric(house: Any, bindus: Any) -> str:
                if house is None or house == "":
                    return "—"
                prefix = "भाव" if hi else "H"
                return f"{prefix} {house} ({bindus})" if hi else f"H{house} ({bindus})"

            metrics = [
                _metric(
                    t(language, "Strongest house", "सबसे बलवान भाव"),
                    _house_metric(strong.get("house"), strong.get("bindus")),
                    "positive",
                ),
                _metric(
                    t(language, "Weakest house", "सबसे दुर्बल भाव"),
                    _house_metric(weak.get("house"), weak.get("bindus")),
                    "caution",
                ),
                _metric(t(language, "Total bindus", "कुल बिंदु"), av.get("total_bindus")),
            ]
            if not summary:
                summary = (
                    f"सर्वाष्टकवर्ग में सर्वोच्च अंक भाव {strong.get('house')} "
                    f"({label_sign(strong.get('sign_name'), language)}, {strong.get('bindus')} बिंदु) है; "
                    f"न्यूनतम भाव {weak.get('house')} ({label_sign(weak.get('sign_name'), language)}, {weak.get('bindus')} बिंदु)। "
                    f"नीचे भिन्नाष्टकवर्ग ग्रह-वार बिंदु दिखाता है।"
                    if hi
                    else (
                        f"Highest Sarvashtakavarga score is house {strong.get('house')} "
                        f"({strong.get('sign_name')}, {strong.get('bindus')} bindus); "
                        f"lowest is house {weak.get('house')} ({weak.get('sign_name')}, {weak.get('bindus')} bindus). "
                        f"Bhinnashtakavarga below shows planet-wise bindus by house from lagna."
                    )
                )

        elif key == "major_yogas":
            catalog = fact.get("yogas_catalog") or []
            if not catalog:
                # Backward compatible with older fact packs that only stored yogas_top.
                catalog = list(fact.get("yogas_top") or []) + list(fact.get("yogas_challenging") or [])
            auspicious = [y for y in catalog if str(y.get("polarity") or "auspicious") != "challenging"]
            challenging = [y for y in catalog if str(y.get("polarity") or "") == "challenging"]
            tables = []
            if auspicious:
                tables.append(
                    _yoga_table(
                        auspicious,
                        language,
                        title_en=f"Auspicious yogas ({len(auspicious)})",
                        title_hi=f"शुभ योग ({len(auspicious)})",
                    )
                )
            if challenging:
                tables.append(
                    _yoga_table(
                        challenging,
                        language,
                        title_en=f"Challenging yogas ({len(challenging)})",
                        title_hi=f"चुनौतीपूर्ण योग ({len(challenging)})",
                    )
                )
            if not catalog and not summary:
                summary = (
                    "योग स्क्रीन वाले इंजन से इस कुंडली में कोई योग नहीं मिला।"
                    if hi
                    else "No yogas were returned by the same yoga engine used on the Yogas screen."
                )
            elif not summary:
                summary = (
                    f"योग स्क्रीन वाले कैलकुलेटर से {len(auspicious)} शुभ और {len(challenging)} चुनौतीपूर्ण योग।"
                    if hi
                    else (
                        f"{len(auspicious)} auspicious and {len(challenging)} challenging yoga(s) "
                        "from the same calculator as the mobile Yogas screen."
                    )
                )

        elif key == "emotional_blueprint":
            deep = fact.get("nakshatra_deep_dive") or {}
            moon_nak = deep.get("moon") if isinstance(deep.get("moon"), dict) else {}
            asc_nak = deep.get("ascendant") if isinstance(deep.get("ascendant"), dict) else {}
            tara_bal = deep.get("tara_bal") if isinstance(deep.get("tara_bal"), dict) else {}
            remedy = deep.get("remedy") if isinstance(deep.get("remedy"), dict) else {}
            yoga_flags = deep.get("yoga_flags") if isinstance(deep.get("yoga_flags"), list) else []

            metrics = [
                _metric(
                    t(language, "Moon nakshatra", "चंद्र नक्षत्र"),
                    label_nakshatra(moon_nak.get("nakshatra"), language) or "—",
                ),
                _metric(t(language, "Pada", "पद"), moon_nak.get("pada") or "—"),
                _metric(
                    t(language, "Nakshatra lord", "नक्षत्र स्वामी"),
                    label_planet(moon_nak.get("lord"), language) or "—",
                ),
                _metric(
                    t(language, "Gana · Nadi", "गण · नाड़ी"),
                    " · ".join(
                        p for p in [
                            label_gana(moon_nak.get("gana"), language),
                            label_nadi(moon_nak.get("nadi"), language),
                        ] if p
                    ) or "—",
                ),
            ]
            first_tara = (tara_bal.get("levels") or [None])[0] if tara_bal else None
            if isinstance(first_tara, dict) and first_tara.get("tara_name"):
                metrics.append(
                    _metric(
                        t(language, "MD Tara Bal", "महादशा तारा बल"),
                        f"{label_tara(first_tara.get('tara_name'), language)} "
                        f"({label_tara_quality(first_tara.get('tara_quality'), language)})",
                    )
                )

            tables = []
            if moon_nak or asc_nak:
                tables.append(_nakshatra_identity_table(moon_nak, asc_nak, language))
            if moon_nak:
                tables.append(_nakshatra_nature_table(moon_nak, language))
                tables.append(_nakshatra_pada_table(moon_nak, language))
            tara_table = _tara_bal_table(tara_bal, language)
            if tara_table:
                tables.append(tara_table)
            matrix_table = _nakshatra_planet_matrix_table(deep.get("planet_matrix") or [], language)
            if matrix_table:
                tables.append(matrix_table)
            remedy_table = _nakshatra_remedy_table(remedy, language)
            if remedy_table:
                tables.append(remedy_table)

            if yoga_flags and not bullets:
                bullets = [
                    f"{_clean(y.get('name'))}: {_clean(y.get('description'))}"
                    for y in yoga_flags
                    if isinstance(y, dict) and y.get("name")
                ]
            if remedy.get("sound") and not notes:
                notes = [_clean(remedy.get("sound"))]
            if not summary:
                chars = ", ".join(_clean(c) for c in (moon_nak.get("characteristics") or [])[:4] if c)
                summary = (
                    (
                        f"जन्म चंद्र {label_nakshatra(moon_nak.get('nakshatra'), language)} "
                        f"पद {moon_nak.get('pada') or '—'} — {chars}."
                        if chars
                        else f"जन्म चंद्र {label_nakshatra(moon_nak.get('nakshatra'), language)} "
                        f"पद {moon_nak.get('pada') or '—'} पर आधारित भावनात्मक खाका।"
                    )
                    if hi
                    else (
                        f"Emotional blueprint from Moon in "
                        f"{moon_nak.get('nakshatra') or '—'} pada {moon_nak.get('pada') or '—'} — {chars}."
                        if chars
                        else (
                            f"Emotional blueprint from Moon in "
                            f"{moon_nak.get('nakshatra') or '—'} pada {moon_nak.get('pada') or '—'}."
                        )
                    )
                )

        elif key == "dosha_checks":
            tables = [_dosha_table(fact.get("doshas") or {}, language)]
            if not summary:
                summary = (
                    "मंगल, काल सर्प और संबंधित प्रमुख दोष कैलकुलेटर से दोष जाँच सूची।"
                    if hi
                    else "Dosha checklist from Mangal, Kaal Sarp, and related major-dosha calculators."
                )

        elif key == "sade_sati":
            ss = fact.get("sade_sati") or {}
            tables = [_sade_sati_table(ss.get("periods") or [], language)]
            current = ss.get("current_period")
            upcoming = ss.get("upcoming_period")
            metrics = [
                _metric(
                    t(language, "Current", "वर्तमान"),
                    (
                        f"{current.get('start_date')} → {current.get('end_date')}"
                        if current
                        else t(language, "Not active", "सक्रिय नहीं")
                    ),
                ),
                _metric(
                    t(language, "Upcoming", "आगामी"),
                    f"{upcoming.get('start_date')} → {upcoming.get('end_date')}" if upcoming else "—",
                ),
            ]
            if not summary:
                summary = (
                    "जन्म चंद्र राशि तथा उससे १२वें/१वें/२वें भाव पर शनि गोचर से साढ़े साती काल।"
                    if hi
                    else (
                        _clean(ss.get("moon_sign_basis"))
                        or "Sade Sati periods from Saturn transit relative to natal Moon sign."
                    )
                )

        elif key == "dasha_tree":
            dasha = fact.get("dasha") or {}
            tables = [_dasha_table(dasha.get("maha_dashas") or [], language)]
            cur = dasha.get("current") or {}
            metrics = [
                _metric(
                    t(language, "Mahadasha", "महादशा"),
                    label_planet((cur.get("mahadasha") or {}).get("planet"), language),
                ),
                _metric(
                    t(language, "Antardasha", "अन्तर्दशा"),
                    label_planet((cur.get("antardasha") or {}).get("planet"), language),
                ),
            ]
            if not summary:
                summary = (
                    "जन्म चंद्र नक्षत्र से गणना की गई विंशोत्तरी महादशा समयरेखा।"
                    if hi
                    else "Vimshottari Mahadasha timeline calculated from natal Moon nakshatra."
                )

        elif key == "gemstones":
            rem = fact.get("remedies") or {}
            life = rem.get("life_stone") or {}
            lucky = rem.get("lucky_stone") or {}
            bhagya = rem.get("bhagya_ratna") or {}
            metrics = [
                _metric(
                    t(language, "Life stone", "जीवन रत्न"),
                    f"{label_planet(life.get('planet'), language)}: {label_gemstone(life.get('gemstone'), language)}",
                ),
                _metric(
                    t(language, "Lucky stone", "भाग्य रत्न"),
                    f"{label_planet(lucky.get('planet'), language)}: {label_gemstone(lucky.get('gemstone'), language)}",
                ),
                _metric(
                    t(language, "Bhagya ratna", "भाग्यरत्न"),
                    f"{label_planet(bhagya.get('planet'), language)}: {label_gemstone(bhagya.get('gemstone'), language)}",
                ),
            ]
            avoid = rem.get("avoid_stones") or []
            bullets = bullets or [
                (
                    (
                        f"वर्जित उम्मीदवार: {label_planet(a.get('planet'), language)} — "
                        f"{label_gemstone(a.get('gemstone'), language)} "
                        f"({label_reason(a.get('reason'), language)})"
                    )
                    if hi
                    else (
                        f"Avoid candidate: {a.get('planet')} — {a.get('gemstone')} "
                        f"({a.get('reason')})"
                    )
                )
                for a in avoid
            ]
            suitability = _clean(rem.get("suitability_note"))
            if hi and suitability:
                suitability = (
                    "रत्न कार्यात्मक स्वभाव और भावेशों से सशर्त उम्मीदवार हैं; व्यक्तिगत उपयुक्तता की पुष्टि के बाद ही धारण करें।"
                )
            notes = notes or ([suitability] if suitability else [])
            benefics = [label_planet(p, language) for p in (rem.get("functional_benefics") or [])]
            if not summary:
                summary = (
                    f"{label_sign(rem.get('ascendant_sign_name'), language)} लग्न के लिए कार्यात्मक शुभ: "
                    f"{', '.join(benefics)}."
                    if hi
                    else (
                        f"Functional benefics for {_clean((rem.get('ascendant_sign_name')))} lagna: "
                        f"{', '.join(rem.get('functional_benefics') or [])}."
                    )
                )

        elif key == "practical_remedies":
            remedies_pack = fact.get("remedies") or {}
            rem = remedies_pack.get("remedy_blueprint") or {}
            cards = remedies_pack.get("actionable_remedies") or []
            lifestyle = remedies_pack.get("lifestyle_colors") or {}
            priority = rem.get("priority_order") or []
            priority_labels = [label_planet(p, language) for p in priority] if priority else []
            first_card = next((c for c in cards if isinstance(c, dict)), {}) or {}
            metrics = [
                _metric(
                    t(language, "Priority planets", "प्राथमिक ग्रह"),
                    ", ".join(priority_labels) if priority_labels else "—",
                ),
                _metric(
                    t(language, "Mantra count", "मंत्र संख्या"),
                    f"{first_card.get('mantra_count') or 108} ×",
                ),
                _metric(
                    t(language, "MD colors", "महादशा रंग"),
                    label_colors(lifestyle.get("wear_colors"), language) or "—",
                ),
            ]
            tables = []
            step_table = _actionable_remedies_table(cards, language)
            if step_table:
                tables.append(step_table)
            mantra_table = _mantra_practice_table(cards, language)
            if mantra_table:
                mala_note = mantra_table.pop("_mala_note", None)
                tables.append(mantra_table)
                if mala_note and not notes:
                    notes = [mala_note]
            color_table = _lifestyle_colors_table(lifestyle, language)
            if color_table:
                tables.append(color_table)
            if not bullets:
                for card in cards[:3]:
                    if not isinstance(card, dict):
                        continue
                    day = label_weekday(card.get("weekday"), language)
                    mantra = _clean(card.get("mantra"))
                    count = card.get("mantra_count") or 108
                    charity = _charity_cell(card, language)
                    if hi:
                        bullets.append(
                            f"{label_planet(card.get('planet'), language)}: {day} — "
                            f"{mantra} × {count}; {charity}"
                        )
                    else:
                        bullets.append(
                            f"{card.get('planet')}: {day} — {mantra} × {count}; {charity}"
                        )
            if not summary:
                summary = (
                    "वर्तमान महादशा/अन्तर्दशा स्वामियों के लिए दिन, समय, १०८ जाप, दान और रंग मार्गदर्शन।"
                    if hi
                    else (
                        "Step-by-step remedies for current Mahadasha/Antardasha lords: "
                        "best day/time, 108 mantra repetitions, charity, and dasha color therapy."
                    )
                )

        pages.append(
            _page(
                bp["num"],
                title,
                subtitle,
                summary,
                bullets=bullets,
                metrics=metrics,
                chart_refs=bp.get("charts") or [],
                tables=tables,
                notes=notes,
                section_key=key,
                skip_render=bool(bp.get("skip_render")),
            )
        )

    return pages


def build_janam_kundli_chart_manifest(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    style = context.get("chart_style") or "both"
    return [
        {"ref": "native_d1", "style": style},
        {"ref": "native_moon", "style": style},
        {"ref": "native_chalit", "style": style},
        {"ref": "native_d9", "style": style},
        {"ref": "native_d10", "style": style},
    ]
