"""Build a canonical, presentation-free partner evidence packet."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from calculators.aspect_calculator import AspectCalculator
from calculators.chara_karaka_calculator import CharaKarakaCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from reports.context.shared_branch_context import build_nakshatra_context


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}


def _int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _chart_planets(chart: Mapping[str, Any]) -> Dict[str, Any]:
    direct = chart.get("planets")
    if isinstance(direct, dict):
        return direct
    nested = chart.get("divisional_chart")
    if isinstance(nested, dict) and isinstance(nested.get("planets"), dict):
        return nested["planets"]
    return {}


def _chart_body(chart: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the actual chart object from either a D1 or varga response."""
    nested = chart.get("divisional_chart")
    return nested if isinstance(nested, dict) else chart


def _ascendant_longitude(chart: Mapping[str, Any]) -> float | None:
    for key in ("ascendant", "ascendant_longitude"):
        try:
            if chart.get(key) is not None:
                return float(chart[key])
        except (TypeError, ValueError):
            pass
    nested = chart.get("divisional_chart")
    if isinstance(nested, dict):
        return _ascendant_longitude(nested)
    return None


def _planet_row(chart: Mapping[str, Any], planet: str, nakshatras: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    planets = _chart_planets(chart)
    raw = planets.get(planet) if isinstance(planets.get(planet), dict) else {}
    if not raw:
        return {}
    sign = _int(raw.get("sign"))
    if sign is None and raw.get("longitude") is not None:
        sign = int(float(raw["longitude"]) / 30) % 12
    nak = (nakshatras or {}).get(planet) if isinstance((nakshatras or {}).get(planet), dict) else {}
    return {
        key: value for key, value in {
            "planet": planet,
            "house": _int(raw.get("house")),
            "sign_id": sign,
            "sign": SIGN_NAMES[sign % 12] if sign is not None else raw.get("sign_name"),
            "longitude": raw.get("longitude"),
            "degree_in_sign": round(float(raw.get("longitude")) % 30, 4) if raw.get("longitude") is not None else None,
            "dignity": raw.get("dignity"),
            "retrograde": bool(raw.get("retrograde")) or None,
            "combust": bool(raw.get("combust")) or None,
            "nakshatra": nak.get("nakshatra_name") or nak.get("name") or nak.get("nakshatra"),
            "nakshatra_lord": nak.get("nakshatra_lord") or nak.get("lord"),
            "pada": nak.get("pada"),
        }.items() if value not in (None, "", [], {})
    }


def _occupants(chart: Mapping[str, Any], house: int) -> list[str]:
    return [
        name for name, row in _chart_planets(chart).items()
        if isinstance(row, dict) and _int(row.get("house")) == house and name not in {"Gulika", "Mandi"}
    ]


def _aspecting(chart: Mapping[str, Any], house: int) -> list[str]:
    try:
        # Node drishti varies materially by lineage; conjunctions remain visible
        # as occupants, but this BPHS-bound portrait resolver does not use
        # disputed Rahu/Ketu aspect schemes.
        return [
            planet for planet in (AspectCalculator(dict(chart)).get_aspecting_planets(house) or [])
            if planet not in {"Rahu", "Ketu"}
        ]
    except Exception:
        return []


def build_partner_evidence(chart_data: Dict[str, Any], *, native_gender: str | None = None) -> Dict[str, Any]:
    if not isinstance(chart_data, dict) or not _chart_planets(chart_data):
        raise ValueError("Calculated D1 chart is required")

    d1_nak = build_nakshatra_context(chart_data).get("positions") or {}
    d9_response = DivisionalChartCalculator(chart_data).calculate_divisional_chart(9)
    d9 = dict(_chart_body(d9_response))
    d9_planets = _chart_planets(d9)
    if not d9_planets:
        raise ValueError("D9 calculation did not return planetary positions")

    asc = _ascendant_longitude(chart_data)
    d9_asc = _ascendant_longitude(d9)
    if asc is None or d9_asc is None:
        raise ValueError("D1 and D9 ascendants are required")

    seventh_sign_id = (int(asc / 30) + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign_id]
    d9_seventh_sign_id = (int(d9_asc / 30) + 6) % 12
    d9_seventh_lord = SIGN_LORDS[d9_seventh_sign_id]
    karakas = CharaKarakaCalculator(chart_data).calculate_chara_karakas()
    dk = ((karakas.get("chara_karakas") or {}).get("Darakaraka") or {}).get("planet")
    normalized_gender = str(native_gender or "").strip().lower()
    spouse_karaka = "Jupiter" if normalized_gender in {"female", "woman", "f", "girl"} else "Venus"

    d1_seventh_occupants = _occupants(chart_data, 7)
    d9_seventh_occupants = _occupants(d9, 7)
    d1_seventh_aspectors = _aspecting(chart_data, 7)
    d9_seventh_aspectors = _aspecting(d9, 7)
    return {
        "schema_version": "partner-evidence/v1",
        "scope": "Static natal partner appearance and temperament. No timing or identification of a specific person.",
        "d1": {
            "seventh_house": {
                "house": 7,
                "sign_id": seventh_sign_id,
                "sign": SIGN_NAMES[seventh_sign_id],
                "lord": seventh_lord,
                "occupants": d1_seventh_occupants,
                "aspecting_planets": d1_seventh_aspectors,
            },
            "seventh_lord": _planet_row(chart_data, seventh_lord, d1_nak),
            "seventh_house_occupants": [_planet_row(chart_data, p, d1_nak) for p in d1_seventh_occupants],
            "seventh_house_aspectors": [_planet_row(chart_data, p, d1_nak) for p in d1_seventh_aspectors],
            "darakaraka": _planet_row(chart_data, str(dk or ""), d1_nak) if dk else {},
            "venus": _planet_row(chart_data, "Venus", d1_nak),
            "jupiter": _planet_row(chart_data, "Jupiter", d1_nak),
            "spouse_karaka": _planet_row(chart_data, spouse_karaka, d1_nak),
        },
        "d9": {
            "seventh_house": {
                "house": 7,
                "sign_id": d9_seventh_sign_id,
                "sign": SIGN_NAMES[d9_seventh_sign_id],
                "lord": d9_seventh_lord,
                "occupants": d9_seventh_occupants,
                "aspecting_planets": d9_seventh_aspectors,
            },
            "seventh_lord": _planet_row(d9, d9_seventh_lord),
            "seventh_house_occupants": [_planet_row(d9, p) for p in d9_seventh_occupants],
            "seventh_house_aspectors": [_planet_row(d9, p) for p in d9_seventh_aspectors],
            "d1_seventh_lord": _planet_row(d9, seventh_lord),
            "darakaraka": _planet_row(d9, str(dk or "")) if dk else {},
        },
        "calculation_methods": {
            "zodiac": "Lahiri sidereal chart supplied by the canonical chart calculator",
            "houses": "Whole-sign houses from the calculated chart",
            "darakaraka": karakas.get("calculation_method"),
            "spouse_karaka": (
                "Jupiter for a husband in a female nativity; Venus for a wife in a male nativity"
            ),
        },
        "evidence_complete": bool(seventh_lord and d9_seventh_lord and dk),
    }
