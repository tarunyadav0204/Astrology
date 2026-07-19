"""Janam Kundli report context — calculator fact pack only (no narrative invention)."""

from __future__ import annotations

import logging
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.base_calculator import BaseCalculator
from calculators.chart_calculator import ChartCalculator
from calculators.color_calculator import ColorCalculator
from calculators.friendship_calculator import FriendshipCalculator
from calculators.nakshatra_remedy_calculator import NakshatraRemedyCalculator
from calculators.navatara_calculator import NavataraCalculator
from calculators.panchang_calculator import PanchangCalculator
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.remedy_engine import RemedyEngine
from calculators.yoga_calculator import YogaCalculator
from calculators.yogi_calculator import YogiCalculator
from marriage_matching.constants import NAKSHATRA_GANA, NAKSHATRA_NADI, NAKSHATRA_YONI
from shared.dasha_calculator import DashaCalculator
from vedic_predictions.config.functional_nature import (
    FUNCTIONAL_BENEFICS,
    FUNCTIONAL_MALEFICS,
    FUNCTIONAL_NEUTRALS,
)
from vedic_predictions.config.nakshatra_data import NAKSHATRA_DATA, PADA_CHARACTERISTICS

from ..assembly.shodashvarga import SHODASHVARGA_DIVISIONS
from .base_context_builder import calculate_chart_for_birth, calculate_divisional_chart
from .shared_branch_context import build_nakshatra_context
from ..cache.report_hash import normalize_birth_data, normalize_language

logger = logging.getLogger(__name__)

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = BaseCalculator.SIGN_LORDS

CORE_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
# Classical Panchadha Maitri matrices use the seven grahas (same as Relationships tab).
FRIENDSHIP_MATRIX_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
    "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

HOUSE_THEMES = {
    1: "self, vitality, and personal direction",
    2: "wealth, family, and speech",
    3: "courage, siblings, and initiative",
    4: "home, mother, and emotional roots",
    5: "intelligence, creativity, and children",
    6: "service, health strain, and obstacles",
    7: "partnerships and marriage",
    8: "transformation, research, and shared resources",
    9: "dharma, fortune, and mentors",
    10: "career, status, and public role",
    11: "gains, networks, and fulfillment",
    12: "release, foreign links, and spirituality",
}

ELEMENT_BY_SIGN = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}


class JanamKundliContextError(RuntimeError):
    """Raised when a required calculator output is missing or invalid."""


def _birth_dict(birth_data: Any) -> Dict[str, Any]:
    if hasattr(birth_data, "model_dump"):
        return birth_data.model_dump()
    if hasattr(birth_data, "dict"):
        return birth_data.dict()
    return dict(birth_data) if not isinstance(birth_data, dict) else birth_data


def _require(value: Any, label: str) -> Any:
    if value is None:
        raise JanamKundliContextError(f"Missing required fact: {label}")
    if isinstance(value, dict) and value.get("error"):
        raise JanamKundliContextError(f"Calculator error for {label}: {value.get('error')}")
    return value


def _lon_to_sign_0based(longitude: Any) -> Optional[int]:
    try:
        return int(float(longitude) // 30) % 12
    except Exception:
        return None


def _asc_sign_0based(chart: Dict[str, Any]) -> int:
    asc = chart.get("ascendant")
    if isinstance(asc, (int, float)):
        sign = _lon_to_sign_0based(asc)
        if sign is None:
            raise JanamKundliContextError("Invalid ascendant longitude")
        return sign
    if isinstance(asc, dict):
        if asc.get("sign") is not None:
            return int(asc["sign"]) % 12
        if asc.get("longitude") is not None:
            sign = _lon_to_sign_0based(asc.get("longitude"))
            if sign is not None:
                return sign
    raise JanamKundliContextError("Ascendant unavailable in chart")


def _planet_sign_0based(pdata: Any) -> Optional[int]:
    if isinstance(pdata, (int, float)):
        return _lon_to_sign_0based(pdata)
    if not isinstance(pdata, dict):
        return None
    if pdata.get("sign") is not None:
        return int(pdata["sign"]) % 12
    if pdata.get("longitude") is not None:
        return _lon_to_sign_0based(pdata.get("longitude"))
    return None


def _house_from_signs(planet_sign: int, reference_sign: int) -> int:
    return ((int(planet_sign) - int(reference_sign)) % 12) + 1


def _lord_of_house(chart: Dict[str, Any], house: int) -> str:
    from calculators.base_calculator import BaseCalculator

    asc = _asc_sign_0based(chart)
    sign_0based = (asc + house - 1) % 12
    lord = BaseCalculator.SIGN_LORDS.get(sign_0based)
    if not lord:
        raise JanamKundliContextError(f"House lord unavailable for house {house}")
    return lord


def _age_years(birth_date: str, as_of: Optional[datetime] = None) -> int:
    as_of = as_of or datetime.now()
    try:
        y, m, d = [int(x) for x in str(birth_date).split("-")[:3]]
        born = datetime(y, m, d)
    except Exception as exc:
        raise JanamKundliContextError(f"Invalid birth date for age: {birth_date}") from exc
    years = as_of.year - born.year - ((as_of.month, as_of.day) < (born.month, born.day))
    return max(0, int(years))


def _age_bracket(age: int) -> str:
    if age <= 17:
        return "0_17"
    if age <= 28:
        return "18_28"
    if age <= 50:
        return "29_50"
    return "51_plus"


def _dt_iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _build_moon_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    planets = chart.get("planets") or {}
    moon = planets.get("Moon")
    if not isinstance(moon, dict):
        raise JanamKundliContextError("Moon data missing for Chandra Kundli")
    moon_sign = _planet_sign_0based(moon)
    if moon_sign is None:
        raise JanamKundliContextError("Moon sign unavailable for Chandra Kundli")

    rotated_planets: Dict[str, Any] = {}
    for name, pdata in planets.items():
        if not isinstance(pdata, dict):
            continue
        psign = _planet_sign_0based(pdata)
        if psign is None:
            continue
        row = dict(pdata)
        row["house"] = _house_from_signs(psign, moon_sign)
        row["sign"] = psign
        row["sign_name"] = pdata.get("sign_name") or SIGN_NAMES[psign]
        row["_place_by_house"] = True
        rotated_planets[name] = row

    return {
        "planets": rotated_planets,
        "ascendant": float(moon_sign * 30),
        "houses": [{"sign": (moon_sign + i) % 12, "sign_name": SIGN_NAMES[(moon_sign + i) % 12]} for i in range(12)],
        "ayanamsa": chart.get("ayanamsa"),
        "_chart_label": "Chandra Kundli",
        "_reference": "moon",
        "_place_by_house": True,
    }


def _build_chalit_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Bhava Chalit chart for PDF: same lagna/sign layout as D1, planet houses from Placidus bhavas."""
    bhav = chart.get("bhav_chalit") or {}
    if not isinstance(bhav, dict) or not bhav:
        raise JanamKundliContextError("Bhav Chalit data missing")
    chalit_planets = bhav.get("planets") if isinstance(bhav.get("planets"), dict) else {}
    if not chalit_planets:
        raise JanamKundliContextError("Bhav Chalit planets missing")

    d1_planets = chart.get("planets") or {}
    merged: Dict[str, Any] = {}
    for name in CORE_PLANETS:
        base = d1_planets.get(name) if isinstance(d1_planets.get(name), dict) else {}
        cdata = chalit_planets.get(name) if isinstance(chalit_planets.get(name), dict) else {}
        if not base and not cdata:
            continue
        row = dict(base)
        row.update({k: v for k, v in cdata.items() if v is not None})
        if cdata.get("house") is not None:
            row["house"] = int(cdata["house"])
        elif base.get("house") is not None:
            row["house"] = int(base["house"])
        if row.get("sign") is None and row.get("longitude") is not None:
            try:
                row["sign"] = int(float(row["longitude"]) / 30.0) % 12
            except Exception:
                pass
        if row.get("sign") is not None and not row.get("sign_name"):
            row["sign_name"] = SIGN_NAMES[int(row["sign"]) % 12]
        # Marker so PDF house-map uses bhava house only (no whole-sign fallback).
        row["_place_by_house"] = True
        merged[name] = row

    if not merged:
        raise JanamKundliContextError("Bhav Chalit chart empty after merge")

    houses = chart.get("houses")
    if not isinstance(houses, list) or len(houses) < 12:
        asc = chart.get("ascendant")
        if asc is None:
            asc = bhav.get("ascendant")
        try:
            asc_sign = int(float(asc) / 30.0) % 12
        except Exception:
            asc_sign = 0
        houses = [
            {"house_number": i + 1, "sign": (asc_sign + i) % 12, "sign_name": SIGN_NAMES[(asc_sign + i) % 12]}
            for i in range(12)
        ]

    return {
        "planets": merged,
        "houses": houses,
        "ascendant": chart.get("ascendant") if chart.get("ascendant") is not None else bhav.get("ascendant"),
        "ayanamsa": chart.get("ayanamsa"),
        "cusps": bhav.get("cusps"),
        "_chart_label": "Bhava Chalit",
        "_reference": "chalit",
        "_place_by_house": True,
    }


def _build_chalit_shift_notes(chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    bhav = chart.get("bhav_chalit") or {}
    if not isinstance(bhav, dict) or not bhav:
        return []
    chalit_planets = bhav.get("planets") or bhav
    notes: List[Dict[str, Any]] = []
    d1_planets = chart.get("planets") or {}
    for planet, pdata in d1_planets.items():
        if planet not in CORE_PLANETS or not isinstance(pdata, dict):
            continue
        d1_house = pdata.get("house")
        cdata = chalit_planets.get(planet) if isinstance(chalit_planets, dict) else None
        if not isinstance(cdata, dict):
            continue
        chalit_house = cdata.get("house") or cdata.get("bhava") or cdata.get("bhava_number")
        if d1_house is None or chalit_house is None:
            continue
        if int(d1_house) != int(chalit_house):
            notes.append({
                "planet": planet,
                "d1_house": int(d1_house),
                "chalit_house": int(chalit_house),
            })
    return notes


# Same category expansion order as astroroshni_mobile YogaScreen (POST /api/yogas/).
_YOGA_CATEGORY_ORDER = [
    "raj_yogas",
    "dhana_yogas",
    "mahapurusha_yogas",
    "neecha_bhanga_yogas",
    "gaja_kesari_yogas",
    "amala_yogas",
    "viparita_raja_yogas",
    "dharma_karma_yogas",
    "nabhasa_yogas",
    "chandra_yogas",
    "surya_yogas",
    "parivartana_yogas",
    "career_specific_yogas",
    "health_yogas",
    "education_yogas",
    "marriage_yogas",
]

_YOGA_NESTED_ORDER = {
    "nabhasa_yogas": ["sankhya_yogas", "akriti_yogas", "ashraya_yogas"],
    "parivartana_yogas": ["maha_yogas", "dainya_yogas", "khala_yogas", "other_parivartana_yogas"],
}

_CHALLENGING_YOGA_KEYS = {
    "parivartana_yogas_dainya_yogas",
    "parivartana_yogas_khala_yogas",
}

_CHALLENGING_ITEM_TYPES = {
    "affliction",
    "challenging",
    "dosha",
    "negative",
    "malefic",
    "aristha",
}

_AUSPICIOUS_ITEM_TYPES = {
    "beneficial",
    "auspicious",
    "positive",
    "healing",
    "protective",
}


def _yoga_polarity(category_key: str, item: Optional[Dict[str, Any]] = None) -> str:
    """
    Classify yoga polarity.

    Health yogas mix afflictions (Aristha) and protective/healing yogas (Ayur,
    Chandra Sukha, Vipareeta Raja Health) — use the item's own `type` when present.
    """
    item_type = str((item or {}).get("type") or "").strip().lower()
    if item_type in _CHALLENGING_ITEM_TYPES:
        return "challenging"
    if item_type in _AUSPICIOUS_ITEM_TYPES:
        return "auspicious"

    name = str((item or {}).get("name") or "").strip().lower()
    # Explicit dosha names that sometimes land in marriage/health buckets.
    if "dosha" in name or "aristha" in name:
        return "challenging"

    if category_key in _CHALLENGING_YOGA_KEYS or category_key.endswith("dainya_yogas") or category_key.endswith("khala_yogas"):
        return "challenging"
    return "auspicious"


def _normalize_yoga_item(item: Dict[str, Any], category_key: str) -> Optional[Dict[str, Any]]:
    name = str(item.get("name") or item.get("yoga") or "").strip()
    if not name:
        return None
    return {
        "name": name,
        "category": category_key,
        "type": category_key,
        "item_type": item.get("type"),
        "polarity": _yoga_polarity(category_key, item),
        "strength": item.get("strength"),
        "planets": item.get("planets") or ([] if not item.get("planet") else [item.get("planet")]),
        "houses": item.get("houses") or ([] if item.get("house") is None else [item.get("house")]),
        "description": str(item.get("description") or item.get("effect") or "").strip(),
    }


def _catalog_all_yogas(yogas: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten full YogaCalculator.calculate_all_yogas() output like the mobile Yogas screen."""
    collected: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def _add_list(category_key: str, rows: Any) -> None:
        if not isinstance(rows, list):
            return
        for item in rows:
            if not isinstance(item, dict):
                continue
            normalized = _normalize_yoga_item(item, category_key)
            if not normalized:
                continue
            dedupe = (normalized["category"], normalized["name"].lower())
            if dedupe in seen:
                continue
            seen.add(dedupe)
            collected.append(normalized)

    for key in _YOGA_CATEGORY_ORDER:
        value = yogas.get(key)
        if key in _YOGA_NESTED_ORDER and isinstance(value, dict):
            for sub in _YOGA_NESTED_ORDER[key]:
                _add_list(f"{key}_{sub}", value.get(sub))
            # Any unexpected nested lists still included.
            for sub, rows in value.items():
                if sub in _YOGA_NESTED_ORDER[key]:
                    continue
                _add_list(f"{key}_{sub}", rows)
            continue
        _add_list(key, value)

    # Include any extra top-level list categories the engine may add later (except doshas).
    for key, value in yogas.items():
        if key in _YOGA_CATEGORY_ORDER or key == "major_doshas":
            continue
        if isinstance(value, list):
            _add_list(key, value)
        elif isinstance(value, dict):
            for sub, rows in value.items():
                _add_list(f"{key}_{sub}", rows)
    return collected


def _flatten_positive_yogas(yogas: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
    """Legacy helper: first N auspicious yogas (kept for LLM headline prioritization)."""
    auspicious = [y for y in _catalog_all_yogas(yogas) if y.get("polarity") == "auspicious"]
    return auspicious[:limit] if limit else auspicious


def _nakshatra_pada_from_longitude(longitude: Any) -> tuple[Optional[str], Optional[int]]:
    try:
        lon = float(longitude) % 360.0
    except Exception:
        return None, None
    slice_deg = 360.0 / 27.0
    idx = int(lon / slice_deg) % 27
    pada = int((lon % slice_deg) / (slice_deg / 4.0)) + 1
    return NAKSHATRA_NAMES[idx], pada


def _houses_ruled_by_planet(asc_sign: int, planet: str) -> List[int]:
    houses: List[int] = []
    for house in range(1, 13):
        sign = (asc_sign + house - 1) % 12
        if SIGN_LORDS.get(sign) == planet:
            houses.append(house)
    return houses


def _functional_nature_for_planet(asc_sign: int, planet: str) -> str:
    if planet in (FUNCTIONAL_BENEFICS.get(asc_sign) or []):
        return "benefic"
    if planet in (FUNCTIONAL_MALEFICS.get(asc_sign) or []):
        return "malefic"
    if planet in (FUNCTIONAL_NEUTRALS.get(asc_sign) or []):
        return "neutral"
    return "neutral"


def _natural_relation(friendship_calc: FriendshipCalculator, planet: str, other: str) -> str:
    if planet == other:
        return "self"
    if other in friendship_calc.NATURAL_FRIENDS.get(planet, []):
        return "friend"
    if other in friendship_calc.NATURAL_ENEMIES.get(planet, []):
        return "enemy"
    return "neutral"


def _temporal_relation(planet_sign: int, other_sign: int) -> str:
    diff = (other_sign - planet_sign) % 12
    return "friend" if diff in {1, 2, 3, 9, 10, 11} else "enemy"


def _friendship_matrices(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Build natural / temporal / compound planet×planet friendship matrices."""
    friendship_calc = FriendshipCalculator()
    planets_data = chart.get("planets") or {}
    signs: Dict[str, int] = {}
    for planet in FRIENDSHIP_MATRIX_PLANETS:
        pdata = planets_data.get(planet) if isinstance(planets_data.get(planet), dict) else {}
        try:
            signs[planet] = int(pdata.get("sign", 0)) % 12
        except Exception:
            signs[planet] = 0

    natural: Dict[str, Dict[str, str]] = {}
    temporal: Dict[str, Dict[str, str]] = {}
    compound: Dict[str, Dict[str, str]] = {}
    for p1 in FRIENDSHIP_MATRIX_PLANETS:
        natural[p1] = {}
        temporal[p1] = {}
        compound[p1] = {}
        for p2 in FRIENDSHIP_MATRIX_PLANETS:
            if p1 == p2:
                natural[p1][p2] = "self"
                temporal[p1][p2] = "self"
                compound[p1][p2] = "self"
                continue
            natural[p1][p2] = _natural_relation(friendship_calc, p1, p2)
            temporal[p1][p2] = _temporal_relation(signs[p1], signs[p2])
            compound[p1][p2] = friendship_calc.calculate_compound_relation(
                p1, p2, signs[p1], signs[p2]
            )
    return {
        "planets": list(FRIENDSHIP_MATRIX_PLANETS),
        "natural": natural,
        "temporal": temporal,
        "compound": compound,
    }


def _short_avastha(raw: str) -> str:
    text = (raw or "").strip()
    if not text or text.upper() == "N/A":
        return "—"
    token = text.split()[0].replace("(", "").strip()
    aliases = {
        "Bal": "Bal",
        "Baal": "Bal",
        "Kumar": "Kumar",
        "Yuva": "Yuva",
        "Vriddha": "Vriddha",
        "Mrit": "Mrit",
    }
    return aliases.get(token, token)


def _compact_aspects(aspects_received: Any) -> str:
    if not isinstance(aspects_received, dict):
        return "—"
    names = []
    for item in aspects_received.get("aspects") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("aspecting_planet")
        if name and name not in names:
            names.append(str(name))
    return ", ".join(names[:6]) if names else "—"


def _compact_special_roles(special: Any) -> str:
    if not isinstance(special, dict):
        return "—"
    tags = []
    if special.get("is_yogi_lord"):
        tags.append("Yogi")
    if special.get("is_avayogi_lord"):
        tags.append("Avayogi")
    if special.get("is_tithi_shunya_lord"):
        tags.append("Tithi Shunya")
    if special.get("is_dagdha_lord"):
        tags.append("Dagdha")
    if special.get("is_badhaka_lord"):
        tags.append("Badhaka")
    return "; ".join(tags) if tags else "—"


def _planet_matrix(
    chart: Dict[str, Any],
    birth_payload: Dict[str, Any],
    nak_positions: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    analyzer = PlanetAnalyzer(chart, birth_payload, compute_shadbala=False)
    friendship_calc = FriendshipCalculator()
    chart_calc = ChartCalculator({})
    nak_positions = nak_positions or {}
    asc_sign = _asc_sign_0based(chart)
    lord_sign_of = {planet: [] for planet in CORE_PLANETS}
    for planet in CORE_PLANETS:
        lord_sign_of[planet] = _houses_ruled_by_planet(asc_sign, planet)

    rows: List[Dict[str, Any]] = []
    for planet in CORE_PLANETS:
        pdata = (chart.get("planets") or {}).get(planet)
        if not isinstance(pdata, dict):
            raise JanamKundliContextError(f"Planet missing in D1: {planet}")
        analysis = analyzer.analyze_planet(planet)
        if not isinstance(analysis, dict):
            raise JanamKundliContextError(f"Planet analysis failed: {planet}")
        basic = analysis.get("basic_info") if isinstance(analysis.get("basic_info"), dict) else {}
        combust = analysis.get("combustion_status") or {}
        dignity_analysis = analysis.get("dignity_analysis") if isinstance(analysis.get("dignity_analysis"), dict) else {}
        dignity_label = dignity_analysis.get("dignity") or dignity_analysis.get("status")
        gandanta = analysis.get("gandanta_analysis") if isinstance(analysis.get("gandanta_analysis"), dict) else {}
        special = analysis.get("special_lordships") if isinstance(analysis.get("special_lordships"), dict) else {}
        nak_row = nak_positions.get(planet) if isinstance(nak_positions.get(planet), dict) else {}
        longitude = pdata.get("longitude") if pdata.get("longitude") is not None else basic.get("longitude")
        sign = pdata.get("sign") if pdata.get("sign") is not None else basic.get("sign")
        try:
            sign_i = int(sign) % 12
        except Exception:
            sign_i = 0
        degree = pdata.get("degree") if pdata.get("degree") is not None else basic.get("degree")
        try:
            degree_f = float(degree if degree is not None else (float(longitude or 0) % 30))
        except Exception:
            degree_f = 0.0

        nakshatra = (
            basic.get("nakshatra")
            or nak_row.get("nakshatra_name")
            or nak_row.get("nakshatra")
            or pdata.get("nakshatra")
        )
        pada = nak_row.get("pada")
        if pada is None and isinstance(analysis.get("nakshatra_pada"), dict):
            pada = analysis["nakshatra_pada"].get("pada")
        if not nakshatra or pada is None:
            derived_nak, derived_pada = _nakshatra_pada_from_longitude(longitude)
            nakshatra = nakshatra or derived_nak
            if pada is None:
                pada = derived_pada

        dispositor = SIGN_LORDS.get(sign_i)
        natural = _natural_relation(friendship_calc, planet, dispositor) if dispositor else "neutral"
        temporal = "self"
        compound = "self"
        if dispositor and dispositor != planet:
            disp_data = (chart.get("planets") or {}).get(dispositor) or {}
            try:
                disp_sign = int(disp_data.get("sign", sign_i)) % 12
            except Exception:
                disp_sign = sign_i
            temporal = _temporal_relation(sign_i, disp_sign)
            compound = friendship_calc.calculate_compound_relation(planet, dispositor, sign_i, disp_sign)
        elif dispositor == planet:
            natural, temporal, compound = "self", "self", "own_sign"

        combust_status = "normal"
        if isinstance(combust, dict):
            if combust.get("is_cazimi"):
                combust_status = "cazimi"
            elif combust.get("is_combust"):
                combust_status = "combust"
            else:
                status = str(combust.get("status") or "normal").lower()
                combust_status = status if status in {"combust", "cazimi", "normal"} else "normal"

        avastha_raw = chart_calc.get_baladi_avastha(planet, degree_f, sign_i)
        functional = dignity_analysis.get("functional_nature") or _functional_nature_for_planet(asc_sign, planet)

        rows.append({
            "planet": planet,
            "longitude": longitude,
            "degree": round(degree_f, 2),
            "sign": sign_i,
            "sign_name": pdata.get("sign_name") or basic.get("sign_name") or SIGN_NAMES[sign_i],
            "house": pdata.get("house") if pdata.get("house") is not None else basic.get("house"),
            "retrograde": bool(pdata.get("retrograde") or (analysis.get("retrograde_analysis") or {}).get("is_retrograde")),
            "nakshatra": nakshatra,
            "pada": pada,
            "dignity": dignity_label,
            "is_combust": combust_status == "combust",
            "combustion_status": combust_status,
            "functional_nature": functional,
            "dispositor": dispositor,
            "houses_ruled": lord_sign_of.get(planet) or [],
            "natural_friendship": natural,
            "temporal_friendship": temporal,
            "compound_friendship": compound,
            "aspects_received": _compact_aspects(analysis.get("aspects_received")),
            "gandanta": bool(gandanta.get("is_gandanta")),
            "gandanta_intensity": gandanta.get("intensity") if gandanta.get("is_gandanta") else None,
            "special_roles": _compact_special_roles(special),
            "avastha": _short_avastha(avastha_raw),
        })
        if not rows[-1].get("nakshatra"):
            raise JanamKundliContextError(f"Nakshatra missing for planet: {planet}")
    return rows


def _divisional_planet_matrix(divisional_wrapper: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Short planet rows for D9/D10 charts (placement + dignity + nakshatra/pada)."""
    chart = divisional_wrapper.get("divisional_chart") if isinstance(divisional_wrapper, dict) else None
    if not isinstance(chart, dict):
        chart = divisional_wrapper if isinstance(divisional_wrapper, dict) else {}
    planets = chart.get("planets") or {}
    rows: List[Dict[str, Any]] = []
    for planet in CORE_PLANETS:
        pdata = planets.get(planet)
        if not isinstance(pdata, dict):
            continue
        sign = pdata.get("sign")
        try:
            sign_i = int(sign) % 12
        except Exception:
            sign_i = 0
        longitude = pdata.get("longitude")
        nakshatra, pada = _nakshatra_pada_from_longitude(longitude)
        rows.append({
            "planet": planet,
            "sign": sign_i,
            "sign_name": pdata.get("sign_name") or SIGN_NAMES[sign_i],
            "house": pdata.get("house"),
            "degree": round(float(pdata.get("degree") or 0), 2) if pdata.get("degree") is not None else None,
            "dignity": pdata.get("dignity") or "neutral",
            "nakshatra": nakshatra,
            "pada": pada,
            "retrograde": bool(pdata.get("retrograde")),
        })
    return rows


def _nak_number_1based(row: Dict[str, Any]) -> Optional[int]:
    raw = row.get("nakshatra_number") or row.get("number")
    if raw is not None:
        try:
            num = int(raw)
            if 1 <= num <= 27:
                return num
            if 0 <= num <= 26:
                return num + 1
        except Exception:
            pass
    name = str(row.get("nakshatra_name") or row.get("nakshatra") or row.get("name") or "").strip()
    if not name:
        return None
    for idx, item in enumerate(NAKSHATRA_NAMES, start=1):
        if item.lower() == name.lower():
            return idx
    return None


def _enrich_nakshatra_body(row: Dict[str, Any], *, role: str) -> Dict[str, Any]:
    """Moon/Lagna (or planet) nakshatra row with catalog + gana/nadi/yoni + pada details."""
    num = _nak_number_1based(row)
    catalog = NAKSHATRA_DATA.get(num) if num else None
    catalog = catalog if isinstance(catalog, dict) else {}
    pada = row.get("pada")
    try:
        pada_i = int(pada) if pada is not None else None
    except Exception:
        pada_i = None
    pada_lords = catalog.get("pada_lords") or []
    pada_lord = None
    if pada_i and 1 <= pada_i <= len(pada_lords):
        pada_lord = pada_lords[pada_i - 1]
    pada_meta = PADA_CHARACTERISTICS.get(pada_i) if pada_i else None
    pada_meta = pada_meta if isinstance(pada_meta, dict) else {}

    name = (
        row.get("nakshatra_name")
        or row.get("nakshatra")
        or row.get("name")
        or catalog.get("name")
    )
    remedy_calc = NakshatraRemedyCalculator()
    syllable = ""
    if name and pada_i:
        syllable = (remedy_calc.PADA_SYLLABLES.get(str(name)) or {}).get(pada_i, "") or ""

    return {
        "role": role,
        "nakshatra": name,
        "nakshatra_number": num,
        "pada": pada_i,
        "lord": row.get("nakshatra_lord") or row.get("lord") or catalog.get("lord"),
        "deity": row.get("nakshatra_deity") or row.get("deity") or catalog.get("deity"),
        "quality": row.get("nakshatra_quality") or row.get("quality"),
        "degrees_in_nakshatra": row.get("degrees_in_nakshatra"),
        "pada_lord": pada_lord,
        "pada_element": pada_meta.get("element"),
        "pada_nature": pada_meta.get("nature"),
        "pada_syllable": syllable,
        "element": catalog.get("element"),
        "guna": catalog.get("guna"),
        "animal": catalog.get("animal"),
        "symbol": catalog.get("symbol"),
        "nature": catalog.get("nature"),
        "characteristics": list(catalog.get("characteristics") or [])[:6],
        "gana": NAKSHATRA_GANA.get(num) if num else None,
        "nadi": NAKSHATRA_NADI.get(num) if num else None,
        "yoni": NAKSHATRA_YONI.get(num) if num else None,
    }


def _moon_remedy_strip(moon_enriched: Dict[str, Any]) -> Dict[str, Any]:
    name = moon_enriched.get("nakshatra")
    pada = moon_enriched.get("pada") or 1
    if not name:
        return {}
    try:
        payload = NakshatraRemedyCalculator().get_remedy("Moon", str(name), int(pada))
    except Exception:
        return {}
    if not isinstance(payload, dict) or payload.get("error"):
        return {}
    return {
        "deity": payload.get("deity"),
        "shakti": payload.get("shakti"),
        "vriksha": payload.get("vriksha"),
        "mantra": payload.get("mantra"),
        "pada_syllable": payload.get("pada_syllable"),
        "aligned_activity": payload.get("aligned_activity"),
        "optimal_direction": payload.get("optimal_direction"),
        "dietary": payload.get("remedy_tier_4_dietary"),
        "sound": payload.get("remedy_tier_2_sound"),
    }


def _dasha_tara_bal(
    moon_num_1based: Optional[int],
    positions: Dict[str, Any],
    dasha_current: Dict[str, Any],
) -> Dict[str, Any]:
    """Tara Bal of current MD/AD/PD lords from natal Moon nakshatra (NavataraCalculator)."""
    if not moon_num_1based:
        return {}
    calc = NavataraCalculator(moon_num_1based - 1)
    out: Dict[str, Any] = {
        "birth_moon_nakshatra_number": moon_num_1based,
        "levels": [],
    }
    for level_key, label in (
        ("mahadasha", "Mahadasha"),
        ("antardasha", "Antardasha"),
        ("pratyantardasha", "Pratyantardasha"),
    ):
        row = dasha_current.get(level_key) if isinstance(dasha_current, dict) else None
        if not isinstance(row, dict):
            continue
        planet = row.get("planet")
        if not planet:
            continue
        pos = positions.get(str(planet)) if isinstance(positions, dict) else None
        if not isinstance(pos, dict):
            continue
        target_num = _nak_number_1based(pos)
        if not target_num:
            continue
        tara = calc.calculate_tara(target_num - 1)
        effect = str(tara.get("effect") or "neutral")
        quality = "challenging" if effect == "bad" else ("excellent" if effect == "excellent" else ("supportive" if effect == "good" else "neutral"))
        out["levels"].append({
            "level": level_key,
            "level_label": label,
            "planet": planet,
            "nakshatra": pos.get("nakshatra_name") or pos.get("nakshatra"),
            "nakshatra_number": target_num,
            "tara_number": tara.get("tara_number") or tara.get("number"),
            "tara_name": tara.get("name"),
            "tara_effect": effect,
            "tara_quality": quality,
            "description": tara.get("description"),
            "distance": tara.get("distance"),
        })
    return out


def _build_nakshatra_deep_dive(
    nakshatra_branch: Dict[str, Any],
    dasha_pack: Dict[str, Any],
) -> Dict[str, Any]:
    positions = nakshatra_branch.get("positions") if isinstance(nakshatra_branch.get("positions"), dict) else {}
    moon_raw = nakshatra_branch.get("moon") if isinstance(nakshatra_branch.get("moon"), dict) else positions.get("Moon") or {}
    asc_raw = nakshatra_branch.get("ascendant") if isinstance(nakshatra_branch.get("ascendant"), dict) else {}
    if not moon_raw:
        raise JanamKundliContextError("Moon nakshatra missing for deep-dive page")

    moon = _enrich_nakshatra_body(moon_raw, role="Moon")
    asc = _enrich_nakshatra_body(asc_raw, role="Ascendant") if asc_raw else {}
    yogas = nakshatra_branch.get("yogas") if isinstance(nakshatra_branch.get("yogas"), list) else []
    yoga_flags = []
    for y in yogas:
        if isinstance(y, dict) and y.get("name"):
            yoga_flags.append({
                "name": y.get("name"),
                "strength": y.get("strength"),
                "description": str(y.get("description") or "")[:160],
            })

    planet_matrix = []
    for planet in CORE_PLANETS:
        pos = positions.get(planet)
        if not isinstance(pos, dict):
            continue
        planet_matrix.append({
            "planet": planet,
            "nakshatra": pos.get("nakshatra_name") or pos.get("nakshatra"),
            "pada": pos.get("pada"),
            "lord": pos.get("nakshatra_lord") or pos.get("lord"),
            "deity": pos.get("nakshatra_deity") or pos.get("deity"),
            "quality": pos.get("nakshatra_quality") or pos.get("quality"),
        })

    dasha_current = (dasha_pack.get("current") or {}) if isinstance(dasha_pack, dict) else {}
    # Prefer raw current levels if present on pack
    if not dasha_current and isinstance(dasha_pack.get("raw_current"), dict):
        dasha_current = dasha_pack["raw_current"]
    tara_bal = _dasha_tara_bal(moon.get("nakshatra_number"), positions, dasha_current)

    return {
        "moon": moon,
        "ascendant": asc,
        "yoga_flags": yoga_flags,
        "planet_matrix": planet_matrix,
        "remedy": _moon_remedy_strip(moon),
        "tara_bal": tara_bal,
    }


def _special_points_pack(chart: Dict[str, Any], birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    yogi = YogiCalculator(chart).calculate_yogi_points(birth_payload)
    if not isinstance(yogi, dict):
        raise JanamKundliContextError("Yogi points calculation failed")

    def _point(key: str) -> Dict[str, Any]:
        raw = yogi.get(key) if isinstance(yogi.get(key), dict) else {}
        sign = raw.get("sign")
        try:
            sign_i = int(sign) % 12 if sign is not None else None
        except Exception:
            sign_i = None
        return {
            "lord": raw.get("lord"),
            "sign": sign_i,
            "sign_name": raw.get("sign_name") or (SIGN_NAMES[sign_i] if sign_i is not None else None),
            "degree": raw.get("degree"),
            "longitude": raw.get("longitude"),
        }

    return {
        "yogi": _point("yogi"),
        "avayogi": _point("avayogi"),
        "dagdha_rashi": _point("dagdha_rashi"),
        "tithi_shunya_rashi": _point("tithi_shunya_rashi"),
        "avayogi_tithi_shunya_overlap": yogi.get("avayogi_tithi_shunya_overlap") or {},
    }


def _bav_house_row(chart_row: Dict[str, Any], asc: int, planet_label: str) -> Dict[str, Any]:
    """Convert sign-indexed bindus into houses counted from lagna."""
    bindus = chart_row.get("bindus") or {}
    houses: List[int] = []
    for house in range(1, 13):
        sign = (asc + house - 1) % 12
        raw = bindus.get(sign)
        if raw is None:
            raw = bindus.get(str(sign), 0)
        houses.append(int(raw or 0))
    total = chart_row.get("total")
    if total is None:
        total = sum(houses)
    return {
        "planet": planet_label,
        "houses": houses,
        "total": int(total),
    }


def _ashtakavarga_pack(chart: Dict[str, Any], birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    sav = AshtakavargaCalculator(birth_payload, chart).calculate_sarvashtakavarga()
    bindus_raw = _require(sav.get("sarvashtakavarga"), "sarvashtakavarga")
    house_scores: List[Dict[str, Any]] = []
    asc = _asc_sign_0based(chart)
    for sign_key, score in bindus_raw.items():
        sign = int(sign_key)
        house = ((sign - asc) % 12) + 1
        house_scores.append({
            "sign": sign,
            "sign_name": SIGN_NAMES[sign],
            "house": house,
            "bindus": int(score),
        })
    if not house_scores:
        raise JanamKundliContextError("Empty Ashtakavarga scores")
    ranked = sorted(house_scores, key=lambda r: r["bindus"], reverse=True)

    bhinnashtakavarga: List[Dict[str, Any]] = []
    individual = sav.get("individual_charts") or {}
    for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        row = individual.get(planet)
        if isinstance(row, dict):
            bhinnashtakavarga.append(_bav_house_row(row, asc, planet))
    lagna_chart = sav.get("lagna_chart")
    if isinstance(lagna_chart, dict):
        bhinnashtakavarga.append(_bav_house_row(lagna_chart, asc, "Lagna"))

    return {
        "sarvashtakavarga": sav,
        "house_scores": house_scores,
        "strongest": ranked[0],
        "weakest": ranked[-1],
        "total_bindus": int(sav.get("total_bindus") or sum(r["bindus"] for r in house_scores)),
        "bhinnashtakavarga": bhinnashtakavarga,
    }


def _dasha_pack(birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    calc = DashaCalculator()
    current = calc.calculate_current_dashas(birth_payload)
    if not isinstance(current, dict) or current.get("error"):
        raise JanamKundliContextError(f"Vimshottari dasha failed: {current.get('error') if isinstance(current, dict) else current}")
    maha = current.get("mahadasha") or {}
    antar = current.get("antardasha") or {}
    if not maha.get("planet") or not antar.get("planet"):
        raise JanamKundliContextError("Current mahadasha/antardasha unavailable")

    def _antar_rows(maha_row: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        try:
            listed = calc.list_antardashas(maha_row) or []
        except Exception as exc:
            raise JanamKundliContextError(
                f"Antardasha listing failed for {maha_row.get('planet')}: {exc}"
            ) from exc
        for ad in listed:
            if not isinstance(ad, dict) or not ad.get("planet"):
                continue
            rows.append({
                "planet": ad.get("planet"),
                "start": _dt_iso(ad.get("start")),
                "end": _dt_iso(ad.get("end")),
            })
        return rows

    maha_list = []
    for row in current.get("maha_dashas") or []:
        if not isinstance(row, dict) or not row.get("planet"):
            continue
        maha_list.append({
            "planet": row.get("planet"),
            "start": _dt_iso(row.get("start")),
            "end": _dt_iso(row.get("end")),
            "years": row.get("years"),
            "antardashas": _antar_rows(row),
        })

    # Keep current-MD antardashas for present_phase / metrics consumers.
    current_planet = maha.get("planet")
    current_antardashas = []
    for maha_row in maha_list:
        if maha_row.get("planet") == current_planet:
            current_antardashas = list(maha_row.get("antardashas") or [])
            break
    if not current_antardashas:
        current_antardashas = _antar_rows(maha)

    return {
        "current": {
            "mahadasha": {
                "planet": maha.get("planet"),
                "start": _dt_iso(maha.get("start")),
                "end": _dt_iso(maha.get("end")),
            },
            "antardasha": {
                "planet": antar.get("planet"),
                "start": _dt_iso(antar.get("start")),
                "end": _dt_iso(antar.get("end")),
            },
            "pratyantardasha": {
                "planet": (current.get("pratyantardasha") or {}).get("planet"),
                "start": _dt_iso((current.get("pratyantardasha") or {}).get("start")),
                "end": _dt_iso((current.get("pratyantardasha") or {}).get("end")),
            },
        },
        "maha_dashas": maha_list,
        "current_antardashas": current_antardashas,
        "raw_current": current,
    }


def _sade_sati_pack(birth_payload: Dict[str, Any]) -> Dict[str, Any]:
    from transits.routes import _get_sade_sati_periods

    ns = SimpleNamespace(
        date=birth_payload.get("date"),
        time=birth_payload.get("time") or "12:00",
        latitude=float(birth_payload.get("latitude")),
        longitude=float(birth_payload.get("longitude")),
    )
    periods = _get_sade_sati_periods(ns)
    if not isinstance(periods, list):
        raise JanamKundliContextError("Sade Sati calculation returned invalid data")
    current = next((p for p in periods if p.get("is_current")), None)
    upcoming = next(
        (p for p in periods if not p.get("is_current") and str(p.get("start_date") or "") >= datetime.now().date().isoformat()),
        None,
    )
    return {
        "periods": periods,
        "current_period": current,
        "upcoming_period": upcoming,
        "moon_sign_basis": "Saturn transit over Moon sign and adjacent signs (12th/1st/2nd from Moon)",
    }


# Classical weekday + preferred window for planetary upayas (narrative remedies page).
PLANET_REMEDY_TIMING: Dict[str, Dict[str, str]] = {
    "Sun": {
        "weekday": "Sunday",
        "best_time": "Morning after sunrise, facing East",
        "best_time_hi": "रविवार सूर्योदय के बाद, पूर्व मुख",
    },
    "Moon": {
        "weekday": "Monday",
        "best_time": "Evening / night, calm mind",
        "best_time_hi": "सोमवार शाम या रात्रि, शांत मन से",
    },
    "Mars": {
        "weekday": "Tuesday",
        "best_time": "Morning after sunrise",
        "best_time_hi": "मंगलवार सूर्योदय के बाद प्रातः",
    },
    "Mercury": {
        "weekday": "Wednesday",
        "best_time": "Morning, before midday",
        "best_time_hi": "बुधवार प्रातः, दोपहर से पहले",
    },
    "Jupiter": {
        "weekday": "Thursday",
        "best_time": "Morning after sunrise",
        "best_time_hi": "गुरुवार सूर्योदय के बाद प्रातः",
    },
    "Venus": {
        "weekday": "Friday",
        "best_time": "Morning or early evening",
        "best_time_hi": "शुक्रवार प्रातः या प्रारंभिक संध्या",
    },
    "Saturn": {
        "weekday": "Saturday",
        "best_time": "Evening after sunset",
        "best_time_hi": "शनिवार सूर्यास्त के बाद संध्या",
    },
    "Rahu": {
        "weekday": "Saturday",
        "best_time": "Evening after sunset (avoid Rahu Kaal start for new work)",
        "best_time_hi": "शनिवार सूर्यास्त के बाद (राहु काल में नया कार्य न शुरू करें)",
    },
    "Ketu": {
        "weekday": "Tuesday",
        "best_time": "Morning, quiet space",
        "best_time_hi": "मंगलवार प्रातः, शांत स्थान पर",
    },
}

MANTRA_COUNT_DEFAULT = 108
MANTRA_MALA_NOTE = "Use a Rudraksha or Tulsi mala; complete 108 repetitions in one sitting when possible."
MANTRA_MALA_NOTE_HI = "रुद्राक्ष या तुलसी माला से एक बैठक में १०८ जाप पूरे करें।"

CHARITY_HI = {
    "Sun": "रविवार को गेहूँ, ताँबा दान करें या पिता/मार्गदर्शक की सेवा करें।",
    "Moon": "सोमवार को दूध, सफेद वस्त्र, चावल दान करें या मातृ-पक्ष की सेवा करें।",
    "Mars": "मंगलवार को मसूर, गुड़ दान करें या रक्तदान/शारीरिक सेवा करें।",
    "Mercury": "बुधवार को हरी सब्जी, पुस्तकें, स्टेशनरी दान करें या विद्यार्थियों की मदद करें।",
    "Jupiter": "गुरुवार को हल्दी, पीला भोजन दान करें या गुरु/बच्चों की सेवा करें।",
    "Venus": "शुक्रवार को सफेद मिठाई, वस्त्र दान करें या कला/सद्भाव का समर्थन करें।",
    "Saturn": "शनिवार को काले तिल, कंबल दान करें या वृद्ध/मजदूरों की मदद करें।",
    "Rahu": "गहरे कंबल, सरसों तेल दान करें या उपेक्षित समुदायों की सेवा करें।",
    "Ketu": "कंबल, तिल दान करें या मंदिर/आवारा पशु/आध्यात्मिक अध्ययन का समर्थन करें।",
}

SEVA_HI = {
    "Sun": "बड़ों और अधिकारियों की ईमानदारी से सेवा करें; वचन निभाएँ।",
    "Moon": "माता-पक्ष, घर की शांति और भावनात्मक स्थिरता का ध्यान रखें।",
    "Mars": "ऊर्जा को अनुशासित व्यायाम और रक्षात्मक सेवा में लगाएँ।",
    "Mercury": "वाणी संयमित रखें; लेखन/शिक्षण/संवाद से मदद करें।",
    "Jupiter": "गुरु, मार्गदर्शक और धार्मिक अध्ययन का समर्थन करें।",
    "Venus": "नारी सम्मान, कला और संबंधों में शिष्टाचार अपनाएँ।",
    "Saturn": "धैर्यपूर्ण श्रम, निरंतरता और व्यावहारिक मदद से सेवा करें।",
    "Rahu": "असामान्य/संकटपूर्ण सेवा में नाटकीयता के बिना सहयोग करें।",
    "Ketu": "बिना श्रेय की चाह के शांत आध्यात्मिक सेवा करें।",
}


def _split_color_phrases(raw: Any) -> List[str]:
    return [p.strip() for p in str(raw or "").split(",") if p.strip()]


def _avoid_colors_for_planets(
    malefics: List[str],
    *,
    exclude_planets: Optional[set] = None,
    favored_color_blobs: Optional[List[str]] = None,
    limit: int = 6,
) -> str:
    """Build avoid list from malefic planets, never repeating favored/current-dasha colors."""
    exclude = set(exclude_planets or set())
    favored_keys = {
        phrase.lower()
        for blob in (favored_color_blobs or [])
        for phrase in _split_color_phrases(blob)
    }
    out: List[str] = []
    seen = set()
    for planet in malefics or []:
        if planet in exclude or planet not in RemedyEngine.COLORS:
            continue
        for phrase in _split_color_phrases(RemedyEngine.COLORS.get(planet)):
            key = phrase.lower()
            if key in favored_keys or key in seen:
                continue
            seen.add(key)
            out.append(phrase)
            if len(out) >= limit:
                return ", ".join(out)
    return ", ".join(out)


def _actionable_remedy_card(planet: str, *, role: str, malefics: List[str]) -> Dict[str, Any]:
    """One planet's step-by-step upaya: day/time, mantra count, charity, colors."""
    timing = PLANET_REMEDY_TIMING.get(planet) or {
        "weekday": "Any day",
        "best_time": "Morning after sunrise",
        "best_time_hi": "सूर्योदय के बाद प्रातः",
    }
    wear = RemedyEngine.COLORS.get(planet) or ""
    avoid = _avoid_colors_for_planets(
        malefics,
        exclude_planets={planet},
        favored_color_blobs=[wear],
        limit=4,
    )
    return {
        "planet": planet,
        "role": role,
        "weekday": timing.get("weekday"),
        "best_time": timing.get("best_time"),
        "best_time_hi": timing.get("best_time_hi"),
        "mantra": RemedyEngine.MANTRAS.get(planet),
        "mantra_count": MANTRA_COUNT_DEFAULT,
        "mala_note": MANTRA_MALA_NOTE,
        "mala_note_hi": MANTRA_MALA_NOTE_HI,
        "charity": RemedyEngine.CHARITY.get(planet),
        "charity_hi": CHARITY_HI.get(planet),
        "seva": RemedyEngine.SEVA.get(planet),
        "seva_hi": SEVA_HI.get(planet),
        "diet": RemedyEngine.DIET.get(planet),
        "wear_colors": wear,
        "avoid_colors": avoid,
        "direction": RemedyEngine.DIRECTIONS.get(planet),
        "gemstone": RemedyEngine.GEMSTONES.get(planet),
    }


def _build_actionable_remedies(
    priority_order: List[str],
    md: Optional[str],
    ad: Optional[str],
    malefics: List[str],
) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    seen = set()
    ordered = []
    for p in [md, ad, *(priority_order or [])]:
        if p and p not in seen and p in RemedyEngine.MANTRAS:
            seen.add(p)
            ordered.append(p)
    for planet in ordered[:4]:
        if planet == md:
            role = "Mahadasha lord"
        elif planet == ad:
            role = "Antardasha lord"
        else:
            role = "Priority planet"
        cards.append(_actionable_remedy_card(planet, role=role, malefics=malefics))
    return cards


def _strip_gemstone_suitability(raw: Any) -> str:
    text = str(raw or "").strip()
    suffix = ", only if suitability checks support it"
    if text.endswith(suffix):
        return text[: -len(suffix)].strip()
    if suffix in text:
        return text.split(suffix)[0].strip().rstrip(",")
    return text


def _gemstone_name_for_planet(planet: Optional[str]) -> Optional[str]:
    """Clean stone name without the engine's English suitability suffix."""
    if not planet:
        return None
    return _strip_gemstone_suitability(RemedyEngine.GEMSTONES.get(planet)) or None


def _gemstone_remedy_pack(chart: Dict[str, Any], dasha: Dict[str, Any]) -> Dict[str, Any]:
    asc = _asc_sign_0based(chart)
    benefics = list(FUNCTIONAL_BENEFICS.get(asc) or [])
    malefics = list(FUNCTIONAL_MALEFICS.get(asc) or [])
    if not benefics:
        raise JanamKundliContextError("Functional benefics unavailable for ascendant")
    lagna_lord = _lord_of_house(chart, 1)
    ninth_lord = _lord_of_house(chart, 9)
    fifth_lord = _lord_of_house(chart, 5)
    life_stone_planet = lagna_lord if lagna_lord in RemedyEngine.GEMSTONES else benefics[0]
    lucky_stone_planet = fifth_lord if fifth_lord in RemedyEngine.GEMSTONES else (benefics[1] if len(benefics) > 1 else benefics[0])
    bhagya_planet = ninth_lord if ninth_lord in RemedyEngine.GEMSTONES else benefics[0]
    avoid = [p for p in malefics if p in RemedyEngine.GEMSTONES]

    md = ((dasha.get("current") or {}).get("mahadasha") or {}).get("planet")
    ad = ((dasha.get("current") or {}).get("antardasha") or {}).get("planet")
    focus_planets = [p for p in (md, ad, lagna_lord) if p]
    engine = RemedyEngine(chart)
    blueprint = engine.build_remedy_blueprint(
        question="Janam Kundli remedial guidance from chart lords and current dasha",
        category="general",
        instant_parashari={"focus_houses": [1, 6, 9, 10]},
        normalized_evidence={},
        current_dashas_context={
            "md": {"planet": md},
            "ad": {"planet": ad},
        },
    )
    priority_order = list(blueprint.get("priority_order") or focus_planets)
    sections = blueprint.get("remedy_sections") or {}
    actionable = _build_actionable_remedies(priority_order, md, ad, malefics)
    lifestyle = ColorCalculator(chart).calculate(current_md=md, current_ad=ad)
    return {
        "ascendant_sign": asc,
        "ascendant_sign_name": SIGN_NAMES[asc],
        "functional_benefics": benefics,
        "functional_malefics": malefics,
        "life_stone": {
            "planet": life_stone_planet,
            "gemstone": _gemstone_name_for_planet(life_stone_planet),
            "role": "Lagna lord / life stone candidate",
            "role_hi": "लग्न स्वामी — जीवन रत्न उम्मीदवार",
            "meaning": "Supports vitality, body, and overall life direction (1st house lord).",
            "meaning_hi": "शरीर, जीवनशक्ति और जीवन दिशा का आधार (प्रथम भाव स्वामी)।",
        },
        "lucky_stone": {
            "planet": lucky_stone_planet,
            "gemstone": _gemstone_name_for_planet(lucky_stone_planet),
            "role": "5th lord / luck stone candidate",
            "role_hi": "पंचमेश — भाग्य/सुख रत्न उम्मीदवार",
            "meaning": "Linked with intelligence, creativity, and gains from past merit (5th house lord).",
            "meaning_hi": "बुद्धि, सृजन और पुण्य से लाभ से जुड़ा (पंचम भाव स्वामी)।",
        },
        "bhagya_ratna": {
            "planet": bhagya_planet,
            "gemstone": _gemstone_name_for_planet(bhagya_planet),
            "role": "9th lord / bhagya ratna candidate",
            "role_hi": "नवमेश — भाग्यरत्न उम्मीदवार",
            "meaning": "Supports fortune, dharma, and long-term grace (9th house lord).",
            "meaning_hi": "भाग्य, धर्म और दीर्घकालिक अनुग्रह का सहारा (नवम भाव स्वामी)।",
        },
        "avoid_stones": [
            {
                "planet": p,
                "gemstone": _gemstone_name_for_planet(p),
                "reason": "Functional malefic for this lagna",
                "reason_hi": "इस लग्न के लिए कार्यात्मक पाप ग्रह — साधारणतः न पहनें",
            }
            for p in avoid
        ],
        "priority_planets": focus_planets,
        "actionable_remedies": actionable,
        "lifestyle_colors": lifestyle,
        "remedy_blueprint": {
            "priority_order": priority_order,
            "candidate_planets": blueprint.get("candidate_planets") or [],
            "mantras": sections.get("mantras") or [],
            "charity": sections.get("charity") or [],
            "seva": sections.get("seva") or [],
            "diet": sections.get("diet") or [],
            "color_and_clothing": sections.get("color_and_clothing") or [],
            "direction_and_timing": sections.get("direction_and_timing") or [],
            "caution": blueprint.get("caution"),
        },
        "suitability_note": "Gemstones are conditional candidates from functional nature and lords; wear only after personal suitability confirmation.",
    }


def _life_theme_facts(chart: Dict[str, Any], planet_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_planet = {r["planet"]: r for r in planet_rows}
    lords = {
        "lagna_lord": _lord_of_house(chart, 1),
        "second_lord": _lord_of_house(chart, 2),
        "fourth_lord": _lord_of_house(chart, 4),
        "fifth_lord": _lord_of_house(chart, 5),
        "sixth_lord": _lord_of_house(chart, 6),
        "seventh_lord": _lord_of_house(chart, 7),
        "ninth_lord": _lord_of_house(chart, 9),
        "tenth_lord": _lord_of_house(chart, 10),
        "eleventh_lord": _lord_of_house(chart, 11),
    }
    placements = {}
    for key, planet in lords.items():
        row = by_planet.get(planet) or {}
        placements[key] = {
            "planet": planet,
            "sign_name": row.get("sign_name"),
            "house": row.get("house"),
            "nakshatra": row.get("nakshatra"),
            "dignity": row.get("dignity"),
            "retrograde": row.get("retrograde"),
        }
    return {
        "lords": lords,
        "placements": placements,
        "venus": by_planet.get("Venus") or {},
        "mercury": by_planet.get("Mercury") or {},
        "jupiter": by_planet.get("Jupiter") or {},
        "mars": by_planet.get("Mars") or {},
        "saturn": by_planet.get("Saturn") or {},
        "moon": by_planet.get("Moon") or {},
        "sun": by_planet.get("Sun") or {},
        "rahu": by_planet.get("Rahu") or {},
        "ketu": by_planet.get("Ketu") or {},
    }


def build_janam_kundli_report_context(request: Any) -> Dict[str, Any]:
    person = normalize_birth_data(request.birth_data)
    birth_payload = _birth_dict(request.birth_data)
    if not birth_payload.get("date") or birth_payload.get("latitude") is None or birth_payload.get("longitude") is None:
        raise JanamKundliContextError("Birth date and coordinates are required")

    chart = _require(calculate_chart_for_birth(request.birth_data), "D1 chart")
    if not (chart.get("planets") or {}).get("Moon"):
        raise JanamKundliContextError("D1 chart missing Moon")

    # Full classical Shodashvarga set for continuous PDF chart atlas.
    shodashvarga_charts: Dict[int, Any] = {1: chart}
    for division in SHODASHVARGA_DIVISIONS:
        if division == 1:
            continue
        shodashvarga_charts[division] = _require(
            calculate_divisional_chart(chart, division),
            f"D{division}",
        )
    d9 = shodashvarga_charts[9]
    d10 = shodashvarga_charts[10]
    moon_chart = _build_moon_chart(chart)
    chalit_chart = _build_chalit_chart(chart)
    chalit_shifts = _build_chalit_shift_notes(chart)

    panchang_calc = PanchangCalculator()
    panchang = panchang_calc.calculate_birth_panchang(birth_payload)
    if not isinstance(panchang, dict) or panchang.get("error"):
        raise JanamKundliContextError(f"Birth panchang failed: {panchang.get('error') if isinstance(panchang, dict) else panchang}")

    # Sunrise/sunset are not in birth-panchang anga calc; attach civil timings for the birth date.
    try:
        timings = panchang_calc.get_local_sunrise_sunset(
            birth_payload.get("date"),
            float(birth_payload.get("latitude") or 0),
            float(birth_payload.get("longitude") or 0),
            birth_payload.get("timezone") or "UTC+0",
        )
        if isinstance(timings, dict):
            panchang = dict(panchang)
            panchang["sunrise"] = timings.get("sunrise")
            panchang["sunset"] = timings.get("sunset")
            panchang["moonrise"] = timings.get("moonrise")
            panchang["moonset"] = timings.get("moonset")
    except Exception:
        pass

    nakshatra = build_nakshatra_context(chart)
    nak_positions = (nakshatra.get("positions") or {}) if isinstance(nakshatra, dict) else {}
    planet_rows = _planet_matrix(chart, birth_payload, nak_positions)
    d9_planet_rows = _divisional_planet_matrix(d9)
    d10_planet_rows = _divisional_planet_matrix(d10)
    friendship_matrices = _friendship_matrices(chart)
    special_points = _special_points_pack(chart, birth_payload)
    ashtakavarga = _ashtakavarga_pack(chart, birth_payload)

    yoga_calc = YogaCalculator(birth_payload, chart)
    yogas = yoga_calc.calculate_all_yogas()
    if not isinstance(yogas, dict):
        raise JanamKundliContextError("Yoga calculation failed")
    doshas = yogas.get("major_doshas") or yoga_calc.calculate_major_doshas()
    yogas_catalog = _catalog_all_yogas(yogas)
    positive_yogas = [y for y in yogas_catalog if y.get("polarity") == "auspicious"]
    challenging_yogas = [y for y in yogas_catalog if y.get("polarity") == "challenging"]

    dasha = _dasha_pack(birth_payload)
    sade_sati = _sade_sati_pack(birth_payload)
    remedies = _gemstone_remedy_pack(chart, dasha)
    life_themes = _life_theme_facts(chart, planet_rows)
    nakshatra_deep = _build_nakshatra_deep_dive(nakshatra if isinstance(nakshatra, dict) else {}, dasha)

    age = _age_years(str(birth_payload.get("date")))
    bracket = _age_bracket(age)
    asc_sign = _asc_sign_0based(chart)
    asc_name = SIGN_NAMES[asc_sign]
    moon_row = next(r for r in planet_rows if r["planet"] == "Moon")

    # Attach D1 Moon/Lagna placement onto the deep-dive identity rows.
    if isinstance(nakshatra_deep.get("moon"), dict):
        nakshatra_deep["moon"]["sign_name"] = moon_row.get("sign_name")
        nakshatra_deep["moon"]["house"] = moon_row.get("house")
    if isinstance(nakshatra_deep.get("ascendant"), dict) and nakshatra_deep["ascendant"]:
        nakshatra_deep["ascendant"]["sign_name"] = asc_name

    fact_pack = {
        "person": person,
        "age_years": age,
        "age_bracket": bracket,
        "ascendant": {
            "sign": asc_sign,
            "sign_name": asc_name,
            "element": ELEMENT_BY_SIGN.get(asc_name),
            "lord": _lord_of_house(chart, 1),
        },
        "moon": moon_row,
        "panchang": panchang,
        "ayanamsa": chart.get("ayanamsa"),
        "planet_matrix": planet_rows,
        "d9_planet_matrix": d9_planet_rows,
        "d10_planet_matrix": d10_planet_rows,
        "friendship_matrices": friendship_matrices,
        "special_points": special_points,
        "chalit_house_shifts": chalit_shifts,
        "ashtakavarga": {
            "house_scores": ashtakavarga["house_scores"],
            "strongest": ashtakavarga["strongest"],
            "weakest": ashtakavarga["weakest"],
            "total_bindus": ashtakavarga["total_bindus"],
            "bhinnashtakavarga": ashtakavarga.get("bhinnashtakavarga") or [],
        },
        "yogas_catalog": yogas_catalog,
        "yogas_top": positive_yogas,  # full auspicious list (same engine as mobile Yogas screen)
        "yogas_challenging": challenging_yogas,
        "doshas": doshas,
        "dasha": {
            "current": dasha["current"],
            "maha_dashas": dasha["maha_dashas"],
            "current_antardashas": dasha["current_antardashas"],
        },
        "sade_sati": sade_sati,
        "life_themes": life_themes,
        "house_themes": HOUSE_THEMES,
        "remedies": remedies,
        "nakshatra_summary": nakshatra.get("summary") if isinstance(nakshatra, dict) else None,
        "nakshatra_deep_dive": nakshatra_deep,
    }

    return {
        "report_type": "janam_kundli",
        "language": normalize_language(getattr(request, "language", "english")),
        "chart_style": getattr(request, "chart_style", "both"),
        "person": person,
        "chart": chart,
        "moon_chart": moon_chart,
        "chalit_chart": chalit_chart,
        "d9_chart": d9,
        "d10_chart": d10,
        "shodashvarga_charts": shodashvarga_charts,
        "bhav_chalit": chart.get("bhav_chalit") or {},
        "branches": {
            "nakshatra": nakshatra,
            "d9": d9,
            "d10": d10,
            "ashtakavarga": ashtakavarga["sarvashtakavarga"],
            "yogas": yogas,
            "dasha": dasha["raw_current"],
            "shodashvarga": {f"D{d}": True for d in SHODASHVARGA_DIVISIONS},
        },
        "fact_pack": fact_pack,
        "current_dashas": dasha["raw_current"],
    }
