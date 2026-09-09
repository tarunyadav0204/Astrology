"""Deterministic evidence foundation for Nakshatra Live answers.

The composer may explain these rows, but it must not choose a different
planet, invent a placement, or turn one nakshatra into an event promise.
"""

from __future__ import annotations

from typing import Any, Mapping

from calculators.nakshatra_calculator import NakshatraCalculator
from calculators.nakshatra_remedy_calculator import NakshatraRemedyCalculator

from .nakshatra import NAKSHATRA_TOPICS, nakshatra_profile, normalize_nakshatra_subtype


_SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
_SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
_PLANETS = {"sun": "Sun", "moon": "Moon", "mars": "Mars", "mercury": "Mercury", "jupiter": "Jupiter", "venus": "Venus", "saturn": "Saturn", "rahu": "Rahu", "ketu": "Ketu"}
_TOPIC_HOUSES = {
    "career": (10,), "relationship": (7,), "wealth": (2, 11),
    "health": (1, 6, 8), "spirituality": (5, 9, 12),
}
_TOPIC_KARAKAS = {
    "career": ("Saturn", "Sun", "Mercury"),
    "relationship": ("Venus", "Jupiter"),
    "wealth": ("Jupiter", "Venus"),
    "health": ("Sun",),
    "spirituality": ("Jupiter", "Ketu"),
}
_TARA_NAMES = ("Janma", "Sampat", "Vipat", "Kshema", "Pratyari", "Sadhana", "Naidhana", "Mitra", "Parama Mitra")


def _dedupe_carriers(rows: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    return [row for row in rows if not (row[0] in seen or seen.add(row[0]))]


def _longitude(value: Any) -> float | None:
    if isinstance(value, Mapping):
        value = value.get("longitude", value.get("full_degree", value.get("degree")))
    try:
        number = float(value)
        return number % 360
    except (TypeError, ValueError):
        return None


def _d1(chart_data: Mapping[str, Any]) -> Mapping[str, Any]:
    charts = chart_data.get("charts") if isinstance(chart_data.get("charts"), Mapping) else {}
    row = charts.get("D1") if isinstance(charts.get("D1"), Mapping) else chart_data
    if isinstance(row.get("calculated_chart"), Mapping):
        row = row["calculated_chart"]
    return row


def _ascendant_longitude(chart: Mapping[str, Any]) -> float | None:
    asc = chart.get("ascendant")
    value = _longitude(asc)
    if value is not None and (isinstance(asc, Mapping) or value > 12):
        return value
    # Some calculated charts expose a one-based ascendant sign plus degree.
    try:
        sign = int(asc)
        degree = float(chart.get("ascendant_degree") or 0)
        if 1 <= sign <= 12:
            return ((sign - 1) * 30 + degree) % 360
    except (TypeError, ValueError):
        pass
    return value


def _planet_rows(chart: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = chart.get("planets") if isinstance(chart.get("planets"), Mapping) else {}
    return {str(name).title(): row for name, row in raw.items() if isinstance(row, Mapping) and _longitude(row) is not None}


def _asc_sign_index(asc_longitude: float | None) -> int | None:
    return int(asc_longitude // 30) if asc_longitude is not None else None


def _house_lord(asc_sign: int | None, house: int) -> str | None:
    return _SIGN_LORDS[(asc_sign + house - 1) % 12] if asc_sign is not None else None


def _navamsha_sign(longitude: float) -> str:
    return _SIGNS[int(longitude / (360 / 108)) % 12]


def _carrier(name: str, longitude: float, calculator: NakshatraCalculator, planets: Mapping[str, Mapping[str, Any]], *, role: str) -> dict[str, Any]:
    info = calculator._get_nakshatra_info(longitude)
    source = planets.get(name) or {}
    lord = str(info["lord"])
    lord_row = planets.get(lord) or {}
    return {
        "carrier": name,
        "role": role,
        "longitude": round(longitude, 6),
        "sign": _SIGNS[int(longitude // 30) % 12],
        "house": source.get("house"),
        "nakshatra_number": info["number"],
        "nakshatra": info["name"],
        "pada": info["pada"],
        "degrees_in_nakshatra": info["degrees_in_nakshatra"],
        "nakshatra_lord": lord,
        "deity": info["deity"],
        "quality": info["quality"],
        "pada_navamsha_sign": _navamsha_sign(longitude),
        "nakshatra_lord_condition": {
            "planet": lord,
            "sign": lord_row.get("sign_name") or (
                _SIGNS[int(lord_row.get("sign")) % 12]
                if str(lord_row.get("sign", "")).lstrip("-").isdigit() else lord_row.get("sign")
            ),
            "house": lord_row.get("house"),
            "dignity": lord_row.get("dignity"),
            "retrograde": lord_row.get("retrograde"),
        },
    }


def _selected_names(*, subtype: str, target_planet: Any, topic: str, asc_sign: int | None, planets: Mapping[str, Mapping[str, Any]], karakas: Mapping[str, Any]) -> list[tuple[str, str]]:
    named = _PLANETS.get(str(target_planet or "").strip().lower())
    if subtype == "ascendant_nakshatra":
        return [("Ascendant", "ascendant")]
    if subtype in {"birth_star_overview", "special_nakshatra_conditions", "naming_syllable"}:
        return [("Moon", "birth_star")]
    if subtype == "full_nakshatra_profile":
        selected = [("Moon", "emotional_mind"), ("Ascendant", "embodied_expression"), ("Sun", "identity_and_purpose")]
        for key, role in (("Atmakaraka", "atmakaraka"), ("Amatyakaraka", "amatyakaraka")):
            planet = str((karakas.get(key) or {}).get("planet") or "") if isinstance(karakas.get(key), Mapping) else ""
            if planet in planets:
                selected.append((planet, role))
        return _dedupe_carriers(selected)
    if named:
        return [(named, "user_selected_planet")]
    if topic in {"personality", "general"}:
        return [("Moon", "emotional_mind"), ("Ascendant", "embodied_expression"), ("Sun", "identity_and_purpose")]
    if topic == "emotions":
        return [("Moon", "emotional_mind")]
    selected: list[tuple[str, str]] = []
    for house in _TOPIC_HOUSES.get(topic, ()):
        lord = _house_lord(asc_sign, house)
        if lord and lord in planets:
            selected.append((lord, f"lord_of_house_{house}"))
    jaimini_key = {"career": "Amatyakaraka", "relationship": "Darakaraka", "spirituality": "Atmakaraka"}.get(topic)
    jaimini_planet = str((karakas.get(jaimini_key) or {}).get("planet") or "") if jaimini_key and isinstance(karakas.get(jaimini_key), Mapping) else ""
    if jaimini_planet in planets:
        selected.append((jaimini_planet, jaimini_key.lower()))
    for planet in _TOPIC_KARAKAS.get(topic, ()):
        if planet in planets:
            selected.append((planet, f"secondary_{topic}_karaka"))
    return _dedupe_carriers(selected) or [("Moon", "birth_star")]


def build_nakshatra_foundation(
    *, chart_data: Mapping[str, Any], normalized_evidence: Mapping[str, Any],
    subtype: Any, target_planet: Any = None, topic: Any = None,
    current_transits: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    subtype = normalize_nakshatra_subtype(subtype)
    profile = nakshatra_profile(subtype)
    topic = str(topic or "general").strip().lower()
    if topic not in NAKSHATRA_TOPICS:
        topic = "general"
    chart = _d1(chart_data)
    planets = _planet_rows(chart)
    asc_longitude = _ascendant_longitude(chart)
    calc_chart = dict(chart)
    calc_chart["planets"] = planets
    if asc_longitude is not None:
        calc_chart["ascendant"] = asc_longitude
    calculator = NakshatraCalculator(chart_data=calc_chart)
    karaka_evidence = normalized_evidence.get("karaka_evidence") if isinstance(normalized_evidence.get("karaka_evidence"), Mapping) else {}
    karakas = karaka_evidence.get("chara_karakas") if isinstance(karaka_evidence.get("chara_karakas"), Mapping) else {}
    names = _selected_names(
        subtype=subtype, target_planet=target_planet, topic=topic,
        asc_sign=_asc_sign_index(asc_longitude), planets=planets, karakas=karakas,
    )
    carriers: list[dict[str, Any]] = []
    for name, role in names:
        longitude = asc_longitude if name == "Ascendant" else _longitude(planets.get(name))
        if longitude is not None:
            carriers.append(_carrier(name, longitude, calculator, planets, role=role))

    moon = next((row for row in carriers if row["carrier"] == "Moon"), None)
    if moon is None and "Moon" in planets:
        moon = _carrier("Moon", _longitude(planets["Moon"]), calculator, planets, role="birth_star")
    special_conditions = calculator.analyze_nakshatra_yogas() if "Moon" in planets else []
    remedy = None
    if subtype == "nakshatra_remedy" and carriers:
        target = carriers[0]
        remedy = NakshatraRemedyCalculator().get_remedy(
            target["carrier"], target["nakshatra"], int(target["pada"]), condition="explicit_nakshatra_remedy_request",
        )
    naming = None
    if subtype == "naming_syllable" and moon:
        naming = {
            "nakshatra": moon["nakshatra"], "pada": moon["pada"],
            "syllable": NakshatraRemedyCalculator.PADA_SYLLABLES.get(moon["nakshatra"], {}).get(int(moon["pada"])),
        }

    current = normalized_evidence.get("current_timing") if isinstance(normalized_evidence.get("current_timing"), Mapping) else {}
    active = current.get("active_dashas") if isinstance(current.get("active_dashas"), Mapping) else {}
    timing_rows = []
    if subtype == "nakshatra_timing" and moon:
        for level, data in active.items():
            planet = str((data or {}).get("planet") or "").title() if isinstance(data, Mapping) else ""
            if planet not in planets:
                continue
            row = _carrier(planet, _longitude(planets[planet]), calculator, planets, role=f"active_{str(level).lower()}_lord")
            distance = (int(row["nakshatra_number"]) - int(moon["nakshatra_number"])) % 27
            row["tara_from_birth_star"] = _TARA_NAMES[distance % 9]
            timing_rows.append(row)
    transit_rows = []
    if subtype == "nakshatra_timing" and moon:
        active_planets = {str(row.get("carrier") or "") for row in timing_rows}
        active_planets.add("Moon")
        for planet in ("Moon", "Saturn", "Jupiter", "Rahu", "Ketu", "Sun"):
            row = (current_transits or {}).get(planet)
            if planet not in active_planets or not isinstance(row, Mapping):
                continue
            star = row.get("nakshatra") if isinstance(row.get("nakshatra"), Mapping) else {}
            try:
                number = int(star.get("index")) + 1
            except (TypeError, ValueError):
                number = None
            transit_rows.append({
                "planet": planet, "sign": row.get("sign"), "house_from_lagna": row.get("house_from_lagna"),
                "nakshatra": star.get("name"), "pada": star.get("pada"),
                "tara_from_birth_star": (
                    _TARA_NAMES[(number - int(moon["nakshatra_number"])) % 27 % 9]
                    if number else None
                ),
                "retrograde": bool(row.get("retrograde")),
            })

    return {
        "schema_version": "nakshatra-foundation/v1",
        "nakshatra_subtype": subtype,
        "topic": topic,
        "requested_target_planet": _PLANETS.get(str(target_planet or "").strip().lower()),
        "charts_required": profile["charts"],
        "carriers": carriers,
        "birth_star": moon,
        "special_conditions": special_conditions if subtype == "special_nakshatra_conditions" else [],
        "timing_carriers": timing_rows,
        "current_transit_nakshatras": transit_rows,
        "remedy": remedy,
        "naming": naming,
        "availability": {
            "d1": bool(planets and asc_longitude is not None),
            "target_carrier": bool(carriers),
            "pada": bool(carriers and all(row.get("pada") for row in carriers)),
            "dispositor": bool(carriers and all(row.get("nakshatra_lord") for row in carriers)),
            "timing": bool(timing_rows) if subtype == "nakshatra_timing" else False,
            "remedy": bool(remedy),
            "naming": bool(naming and naming.get("syllable")),
        },
        "claim_boundaries": [
            "Explain only the selected carrier rows; do not substitute a generic Moon, Rahu, Yogi, or Gandanta statement.",
            "A nakshatra is a qualitative modifier and cannot by itself establish profession, marriage, wealth, health outcome, or an event date.",
            "Gandamoola membership is not an automatic dosha or remedy requirement; distinguish the six-star class from the junction pada.",
            "Do not infer another person's private thoughts, consent, or decisions from the native's nakshatra.",
        ],
    }
