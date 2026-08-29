"""Deterministic Vata / Pitta / Kapha prakriti from a Vedic D1 chart.

Three layers, then fixed focal weights (sum 100):

* Graha dosha D_G
* Rashi dosha D_R
* Nakshatra dosha D_N (Moon placement)

Each planetary focal point is ``0.5 * D_G + 0.5 * D_R``. Moon's placement
half is the average of rashi and nakshatra. This is a chart tendency, not a
medical prakriti diagnosis.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Optional

DOSHAS = ("Vata", "Pitta", "Kapha")

SIGN_LORDS = {
    0: "Mars",
    1: "Venus",
    2: "Mercury",
    3: "Moon",
    4: "Sun",
    5: "Mercury",
    6: "Venus",
    7: "Mars",
    8: "Jupiter",
    9: "Saturn",
    10: "Saturn",
    11: "Jupiter",
}

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# Brihat Parashara / Saravali graha dosha. Mercury is tridoshic unless conjunct.
GRAHA_DOSHA: dict[str, dict[str, float]] = {
    "Sun": {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},
    "Mars": {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},
    "Saturn": {"Vata": 1.0, "Pitta": 0.0, "Kapha": 0.0},
    "Rahu": {"Vata": 1.0, "Pitta": 0.0, "Kapha": 0.0},
    "Ketu": {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},
    "Jupiter": {"Vata": 0.0, "Pitta": 0.0, "Kapha": 1.0},
    "Venus": {"Vata": 0.3, "Pitta": 0.0, "Kapha": 0.7},
    "Moon": {"Vata": 0.3, "Pitta": 0.0, "Kapha": 0.7},
    "Mercury": {"Vata": 0.33, "Pitta": 0.33, "Kapha": 0.34},
}

# Fire → Pitta, Water → Kapha, Air → Vata, Earth → Vata+Kapha.
RASHI_DOSHA: dict[int, dict[str, float]] = {
    0: {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},   # Aries
    1: {"Vata": 0.5, "Pitta": 0.0, "Kapha": 0.5},   # Taurus
    2: {"Vata": 1.0, "Pitta": 0.0, "Kapha": 0.0},   # Gemini
    3: {"Vata": 0.0, "Pitta": 0.0, "Kapha": 1.0},   # Cancer
    4: {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},   # Leo
    5: {"Vata": 0.5, "Pitta": 0.0, "Kapha": 0.5},   # Virgo
    6: {"Vata": 1.0, "Pitta": 0.0, "Kapha": 0.0},   # Libra
    7: {"Vata": 0.0, "Pitta": 0.0, "Kapha": 1.0},   # Scorpio
    8: {"Vata": 0.0, "Pitta": 1.0, "Kapha": 0.0},   # Sagittarius
    9: {"Vata": 0.5, "Pitta": 0.0, "Kapha": 0.5},   # Capricorn
    10: {"Vata": 1.0, "Pitta": 0.0, "Kapha": 0.0},  # Aquarius
    11: {"Vata": 0.0, "Pitta": 0.0, "Kapha": 1.0},  # Pisces
}

NAKSHATRA_ORDER = (
    "ashwini", "bharani", "krittika", "rohini", "mrigashira", "ardra",
    "punarvasu", "pushya", "ashlesha", "magha", "purvaphalguni", "uttaraphalguni",
    "hasta", "chitra", "swati", "vishakha", "anuradha", "jyeshtha",
    "mula", "purvaashadha", "uttaraashadha", "shravana", "dhanishta",
    "shatabhisha", "purvabhadrapada", "uttarabhadrapada", "revati",
)

_VATA_NAKSHATRAS = {
    "ashwini", "ardra", "punarvasu", "uttaraphalguni", "hasta", "swati",
    "mula", "shatabhisha", "purvabhadrapada",
}
_PITTA_NAKSHATRAS = {
    "bharani", "mrigashira", "pushya", "purvaphalguni", "chitra", "vishakha",
    "purvaashadha", "dhanishta", "uttarabhadrapada",
}
_KAPHA_NAKSHATRAS = {
    "krittika", "rohini", "ashlesha", "magha", "anuradha", "jyeshtha",
    "uttaraashadha", "shravana", "revati",
}

NAKSHATRA_ALIASES = {
    "aswini": "ashwini",
    "asvini": "ashwini",
    "krttika": "krittika",
    "mrigasira": "mrigashira",
    "mrgasira": "mrigashira",
    "mrgashira": "mrigashira",
    "aslesha": "ashlesha",
    "aslesa": "ashlesha",
    "pusya": "pushya",
    "poorvaphalguni": "purvaphalguni",
    "uttaraphalguni": "uttaraphalguni",
    "poorvaashada": "purvaashadha",
    "purvashada": "purvaashadha",
    "purvaashada": "purvaashadha",
    "purvaashadha": "purvaashadha",
    "uttarashada": "uttaraashadha",
    "uttaraashada": "uttaraashadha",
    "uttaraashadha": "uttaraashadha",
    "moola": "mula",
    "sravana": "shravana",
    "dhanista": "dhanishta",
    "satabhisha": "shatabhisha",
    "shatabhishak": "shatabhisha",
    "poorvabhadrapada": "purvabhadrapada",
    "purvabhadra": "purvabhadrapada",
    "uttarabhadra": "uttarabhadrapada",
}

FOCAL_WEIGHTS = {
    "lagna_sign": 20.0,
    "lagna_lord": 20.0,
    "moon": 20.0,
    "sun": 15.0,
    "sixth": 10.0,
    "Mars": 3.0,
    "Mercury": 3.0,
    "Jupiter": 3.0,
    "Venus": 3.0,
    "Saturn": 3.0,
}

_GRAHA_SET = set(GRAHA_DOSHA)
_REMAINING_PLANETS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _empty() -> dict[str, float]:
    return {"Vata": 0.0, "Pitta": 0.0, "Kapha": 0.0}


def _vec(vata: float, pitta: float, kapha: float) -> dict[str, float]:
    return {"Vata": float(vata), "Pitta": float(pitta), "Kapha": float(kapha)}


def _copy(vector: Mapping[str, float] | None) -> dict[str, float]:
    if not isinstance(vector, Mapping):
        return _empty()
    return {
        "Vata": float(vector.get("Vata") or 0),
        "Pitta": float(vector.get("Pitta") or 0),
        "Kapha": float(vector.get("Kapha") or 0),
    }


def _scale(vector: Mapping[str, float], weight: float) -> dict[str, float]:
    return {name: float(vector.get(name) or 0) * weight for name in DOSHAS}


def _add(*vectors: Mapping[str, float]) -> dict[str, float]:
    out = _empty()
    for vector in vectors:
        for name in DOSHAS:
            out[name] += float(vector.get(name) or 0)
    return out


def _blend(left: Mapping[str, float], right: Mapping[str, float], left_w: float = 0.5) -> dict[str, float]:
    right_w = 1.0 - left_w
    return _add(_scale(left, left_w), _scale(right, right_w))


def _nakshatra_key(value: Any) -> str:
    key = re.sub(r"[^a-z]", "", str(value or "").lower())
    return NAKSHATRA_ALIASES.get(key, key)


def nakshatra_dosha(name: Any) -> Optional[dict[str, float]]:
    key = _nakshatra_key(name)
    if key in _VATA_NAKSHATRAS:
        return _vec(1, 0, 0)
    if key in _PITTA_NAKSHATRAS:
        return _vec(0, 1, 0)
    if key in _KAPHA_NAKSHATRAS:
        return _vec(0, 0, 1)
    return None


def nakshatra_from_longitude(longitude: Any) -> Optional[str]:
    try:
        lon = float(longitude) % 360.0
    except (TypeError, ValueError):
        return None
    return NAKSHATRA_ORDER[int(lon * 27 / 360.0) % 27]


def rashi_dosha(sign: Any) -> Optional[dict[str, float]]:
    index = _sign_index(sign)
    if index is None:
        return None
    return _copy(RASHI_DOSHA.get(index))


def _sign_index(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        if 0 <= value <= 11:
            return value
        if 1 <= value <= 12:
            return value - 1
        return None
    if isinstance(value, float):
        if 0 <= value < 12:
            return int(value)
        return None
    text = str(value).strip()
    if text.isdigit():
        return _sign_index(int(text))
    lowered = text.lower()
    for index, name in enumerate(SIGN_NAMES):
        if name.lower() == lowered:
            return index
    return None


def _planet_row(planets: Mapping[str, Any], name: str) -> dict[str, Any]:
    row = planets.get(name)
    return row if isinstance(row, dict) else {}


def _planet_sign(row: Mapping[str, Any]) -> Optional[int]:
    for key in ("sign", "sign_index", "rashi"):
        index = _sign_index(row.get(key))
        if index is not None:
            return index
    index = _sign_index(row.get("sign_name"))
    if index is not None:
        return index
    try:
        lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        return None
    return int(lon % 360.0 // 30)


def _planet_longitude(row: Mapping[str, Any]) -> Optional[float]:
    for key in ("longitude", "full_degree", "lon"):
        try:
            return float(row[key]) % 360.0
        except (TypeError, ValueError, KeyError):
            continue
    return None


def _lagna_sign(chart: Mapping[str, Any], houses: list[Any]) -> Optional[int]:
    house1 = _house_sign(houses, 1)
    if house1 is not None:
        return house1
    raw = chart.get("ascendant")
    if isinstance(raw, Mapping):
        return _sign_index(raw.get("sign")) or _sign_index(raw.get("sign_name"))
    try:
        return int(float(raw) % 360.0 // 30)
    except (TypeError, ValueError):
        return _sign_index(raw)


def _house_sign(houses: list[Any], house_num: int) -> Optional[int]:
    for row in houses:
        if not isinstance(row, dict):
            continue
        number = row.get("house") or row.get("house_number") or row.get("number")
        try:
            if int(number) != house_num:
                continue
        except (TypeError, ValueError):
            continue
        return _sign_index(row.get("sign")) or _sign_index(row.get("sign_name"))
    if houses and house_num == 1:
        row = houses[0] if isinstance(houses[0], dict) else {}
        return _sign_index(row.get("sign")) or _sign_index(row.get("sign_name"))
    return None


def _houses(chart: Mapping[str, Any]) -> list[Any]:
    houses = chart.get("houses")
    return list(houses) if isinstance(houses, list) else []


def graha_dosha(
    planet: str,
    planets: Mapping[str, Any] | None = None,
) -> Optional[dict[str, float]]:
    if planet == "Mercury":
        return _copy(mercury_dosha(planets or {}))
    return _copy(GRAHA_DOSHA.get(planet))


def mercury_dosha(planets: Mapping[str, Any]) -> dict[str, float]:
    """Isolated Mercury is tridoshic; same-sign conjunction inherits that graha."""
    mercury = _planet_row(planets, "Mercury")
    mercury_sign = _planet_sign(mercury)
    mercury_lon = _planet_longitude(mercury)
    if mercury_sign is None:
        return _copy(GRAHA_DOSHA["Mercury"])

    closest: Optional[tuple[float, str]] = None
    for name, row in planets.items():
        if name == "Mercury" or name not in _GRAHA_SET or not isinstance(row, dict):
            continue
        if _planet_sign(row) != mercury_sign:
            continue
        other_lon = _planet_longitude(row)
        if mercury_lon is None or other_lon is None:
            distance = 0.0
        else:
            delta = abs(mercury_lon - other_lon) % 360.0
            distance = min(delta, 360.0 - delta)
        if closest is None or distance < closest[0] or (
            distance == closest[0] and name < closest[1]
        ):
            closest = (distance, name)
    if closest is None:
        return _copy(GRAHA_DOSHA["Mercury"])
    return _copy(GRAHA_DOSHA[closest[1]])


def _placement_vector(
    planet: str,
    planets: Mapping[str, Any],
    include_nakshatra: bool = False,
) -> Optional[dict[str, float]]:
    if planet not in planets:
        return None
    graha = graha_dosha(planet, planets)
    row = _planet_row(planets, planet)
    sign = _planet_sign(row)
    rashi = rashi_dosha(sign) if sign is not None else None
    if graha is None:
        return rashi
    if rashi is None and not include_nakshatra:
        return graha

    nak = None
    if include_nakshatra:
        nak_name = row.get("nakshatra")
        if isinstance(nak_name, dict):
            nak_name = nak_name.get("name") or nak_name.get("nakshatra")
        nak = nakshatra_dosha(nak_name) if nak_name else None
        if nak is None:
            nak = nakshatra_dosha(nakshatra_from_longitude(_planet_longitude(row)))

    if include_nakshatra and rashi is not None and nak is not None:
        placement = _blend(rashi, nak)
        return _blend(graha, placement)
    if include_nakshatra and nak is not None and rashi is None:
        return _blend(graha, nak)
    if rashi is None:
        return graha
    return _blend(graha, rashi)


def _component(component_id: str, weight: float, vector: Optional[Mapping[str, float]], note: str) -> dict[str, Any]:
    clean = _copy(vector)
    score = _scale(clean, weight) if vector is not None else _empty()
    return {
        "id": component_id,
        "weight": weight,
        "vector": clean if vector is not None else None,
        "score": {name: round(score[name], 4) for name in DOSHAS},
        "note": note,
        "applied": vector is not None,
    }


def constitution_profile_from_doshas(doshas: Mapping[str, Any] | None) -> dict[str, Any]:
    """Classify a Vata / Pitta / Kapha mix after renormalizing to 100."""
    raw = doshas if isinstance(doshas, Mapping) else {}
    scores = {
        "Vata": float(raw.get("Vata") or 0),
        "Pitta": float(raw.get("Pitta") or 0),
        "Kapha": float(raw.get("Kapha") or 0),
    }
    total = sum(scores.values())
    if total > 0:
        scores = {name: round(value / total * 100, 1) for name, value in scores.items()}
    else:
        scores = {"Vata": 0.0, "Pitta": 0.0, "Kapha": 0.0}

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    primary, primary_pct = ranked[0]
    secondary, secondary_pct = ranked[1]
    tertiary, tertiary_pct = ranked[2]
    gap = round(primary_pct - secondary_pct, 1)
    cues = {
        "Vata": "Movement, nerves, and irregularity when out of balance.",
        "Pitta": "Heat, digestion, and inflammation when out of balance.",
        "Kapha": "Stability, fluids, and congestion when out of balance.",
    }
    pair_order = {"Vata": 0, "Pitta": 1, "Kapha": 2}

    def dual_display(left: str, right: str) -> str:
        ordered = sorted((left, right), key=lambda name: pair_order[name])
        return f"{ordered[0]}-{ordered[1]}"

    in_band = all(28.0 <= scores[name] <= 38.0 for name in DOSHAS)

    if primary_pct >= 50:
        kind = "primary"
        label = primary
        display = f"Pure {primary}"
        summary = f"This chart leans {primary}. {cues[primary]}"
        secondary_name = None
    elif in_band:
        kind = "tridoshic"
        label = "Tridoshic"
        display = "Tridoshic (Vata-Pitta-Kapha)"
        summary = "The three doshas are relatively even in this chart (Sama)."
        secondary_name = secondary
    elif gap <= 10 and primary_pct > 35 and secondary_pct > 35:
        kind = "dual"
        label = dual_display(primary, secondary)
        display = label
        summary = (
            f"This chart blends {display}. "
            f"{cues[primary]} {cues[secondary]}"
        )
        secondary_name = secondary
    elif primary_pct >= 40 and gap > 10:
        kind = "primary"
        label = primary
        display = primary
        summary = f"This chart leans {primary}. {cues[primary]}"
        secondary_name = None
    else:
        kind = "dual"
        label = dual_display(primary, secondary)
        display = label
        summary = (
            f"This chart blends {display}. "
            f"{cues[primary]} {cues[secondary]}"
        )
        secondary_name = secondary

    return {
        "label": label,
        "display": display,
        "kind": kind,
        "primary": primary if primary_pct else None,
        "secondary": secondary_name,
        "tertiary": tertiary if kind == "tridoshic" else None,
        "dosha_balance": scores,
        "summary": summary,
        "disclaimer": (
            "Ayurvedic prakriti tendency from Lagna, Lagna lord, Moon, Sun, "
            "the 6th house, and remaining grahas — not a medical diagnosis."
        ),
    }


def compute_constitution_profile(chart: Mapping[str, Any] | None) -> dict[str, Any]:
    """Score prakriti from D1 chart data using the fixed 100-point focal model."""
    data = chart if isinstance(chart, Mapping) else {}
    planets_raw = data.get("planets") or {}
    planets = planets_raw if isinstance(planets_raw, Mapping) else {}
    houses = _houses(data)
    lagna = _lagna_sign(data, houses)
    if lagna is None and houses:
        lagna = _house_sign(houses, 1)

    components: list[dict[str, Any]] = []

    lagna_rashi = rashi_dosha(lagna)
    components.append(_component(
        "lagna_sign",
        FOCAL_WEIGHTS["lagna_sign"],
        lagna_rashi,
        f"Lagna in {SIGN_NAMES[lagna]}" if lagna is not None else "Lagna sign unavailable",
    ))

    lagna_lord = SIGN_LORDS.get(lagna) if lagna is not None else None
    lord_vector = _placement_vector(lagna_lord, planets) if lagna_lord else None
    lord_sign = _planet_sign(_planet_row(planets, lagna_lord)) if lagna_lord else None
    components.append(_component(
        "lagna_lord",
        FOCAL_WEIGHTS["lagna_lord"],
        lord_vector,
        (
            f"{lagna_lord} occupies {SIGN_NAMES[lord_sign]}"
            if lagna_lord and lord_sign is not None
            else f"{lagna_lord} placement unavailable" if lagna_lord else "Lagna lord unavailable"
        ),
    ))

    moon_vector = _placement_vector("Moon", planets, include_nakshatra=True)
    moon_row = _planet_row(planets, "Moon")
    moon_nak = nakshatra_from_longitude(_planet_longitude(moon_row)) or moon_row.get("nakshatra")
    if isinstance(moon_nak, dict):
        moon_nak = moon_nak.get("name")
    moon_sign = _planet_sign(moon_row)
    components.append(_component(
        "moon",
        FOCAL_WEIGHTS["moon"],
        moon_vector,
        (
            f"Moon in {SIGN_NAMES[moon_sign] if moon_sign is not None else '—'}, "
            f"{moon_nak or 'nakshatra unavailable'}"
        ),
    ))

    sun_vector = _placement_vector("Sun", planets)
    sun_sign = _planet_sign(_planet_row(planets, "Sun"))
    components.append(_component(
        "sun",
        FOCAL_WEIGHTS["sun"],
        sun_vector,
        f"Sun in {SIGN_NAMES[sun_sign]}" if sun_sign is not None else "Sun placement unavailable",
    ))

    sixth_sign = _house_sign(houses, 6)
    if sixth_sign is None and lagna is not None:
        sixth_sign = (lagna + 5) % 12
    sixth_lord = SIGN_LORDS.get(sixth_sign) if sixth_sign is not None else None
    sixth_house_vec = rashi_dosha(sixth_sign)
    sixth_lord_vec = _placement_vector(sixth_lord, planets) if sixth_lord else None
    if sixth_house_vec is not None and sixth_lord_vec is not None:
        sixth_vec = _blend(sixth_house_vec, sixth_lord_vec)
        sixth_note = (
            f"6th house {SIGN_NAMES[sixth_sign]}, 6th lord {sixth_lord}"
        )
    elif sixth_house_vec is not None:
        sixth_vec = sixth_house_vec
        sixth_note = f"6th house {SIGN_NAMES[sixth_sign]}"
    else:
        sixth_vec = sixth_lord_vec
        sixth_note = f"6th lord {sixth_lord}" if sixth_lord else "6th house unavailable"
    components.append(_component(
        "sixth",
        FOCAL_WEIGHTS["sixth"],
        sixth_vec,
        sixth_note,
    ))

    for planet in _REMAINING_PLANETS:
        vector = _placement_vector(planet, planets)
        sign = _planet_sign(_planet_row(planets, planet))
        note = f"{planet} in {SIGN_NAMES[sign]}" if sign is not None else f"{planet} placement unavailable"
        if planet == "Mercury" and vector is not None:
            inherited = mercury_dosha(planets)
            isolated = GRAHA_DOSHA["Mercury"]
            if inherited != isolated:
                donor = next(
                    (
                        name for name, row in planets.items()
                        if name != "Mercury"
                        and name in _GRAHA_SET
                        and isinstance(row, dict)
                        and _planet_sign(row) == _planet_sign(_planet_row(planets, "Mercury"))
                    ),
                    None,
                )
                if donor:
                    note = f"{note}; Mercury inherits {donor}"
        components.append(_component(planet.lower(), FOCAL_WEIGHTS[planet], vector, note))

    raw = _empty()
    for row in components:
        if row["applied"]:
            raw = _add(raw, row["score"])

    profile = constitution_profile_from_doshas(raw)
    profile["method"] = "prakriti_v1"
    profile["components"] = components
    profile["raw_scores"] = {name: round(raw[name], 4) for name in DOSHAS}
    return profile
