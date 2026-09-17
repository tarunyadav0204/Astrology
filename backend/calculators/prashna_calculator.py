"""Classical Vedic Prashna (horary) engine.

Schools are stacked as labeled layers, never blended into one score:

1. Prashna Marga — vitality / readability gates, Lagnesha vs Karyesha, Moon.
2. Tajika Neelakanthi — Ithasala / Easarpha / Nakta / Yamaya / Kamboola
   with deeptamsa orbs. Applying uses remaining degrees to exact aspect and
   actual/mean motion (including retrograde), not ``deg_fast < deg_slow``.
3. Jaimini — Arudha of Lagna (A1) and of the karya house (appearance vs udaya).
4. Optional KP — querent number 1–249 as a vimshottari-sub overlay. It does
   not replace the question-time chart and does not override the Tajika verdict.

The chart clock is the moment and place of the question. This module never
invents longitudes; it only reads a calculated D1 dict.

Chat can later consume ``analyze()`` / ``to_chat_evidence()`` without importing
chat code from here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

from calculators.gandanta_calculator import GandantaCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator
from calculators.vedic_graha_drishti import GRAHA_HOUSE_ASPECTS


SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_LORDS = [
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
]
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_LORDS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
] * 3
VIMSHOTTARI_YEARS: List[Tuple[str, int]] = [
    ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
    ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
]
DEEPTAMSA = {
    "Sun": 15, "Moon": 12, "Mars": 8, "Mercury": 7,
    "Jupiter": 9, "Venus": 7, "Saturn": 9, "Rahu": 5, "Ketu": 5,
}
MEAN_DAILY_MOTION = {
    "Moon": 13.176, "Sun": 0.9856, "Mercury": 1.383, "Venus": 1.2,
    "Mars": 0.524, "Jupiter": 0.0831, "Saturn": 0.0335,
    "Rahu": -0.0529, "Ketu": -0.0529,
}
COMBUSTION_ORBS = {
    "Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15,
}
TAJIKA_ASPECTS: List[Tuple[float, str]] = [
    (0, "Conjunction"),
    (60, "Sextile"),
    (90, "Square"),
    (120, "Trine"),
    (180, "Opposition"),
    (240, "Trine"),
    (270, "Square"),
    (300, "Sextile"),
]
CLASSICAL_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
SKIP_BODIES = {"Gulika", "Mandi", "InduLagna", "Ascendant"}
DUSTHANA = {6, 8, 12}
KENDRA_TRIKONA_LABHA = {1, 4, 5, 7, 9, 10, 11}
MOVABLE_SIGNS = {0, 3, 6, 9}
FIXED_SIGNS = {1, 4, 7, 10}

# House of the matter. Keys are matched against category id or question text.
TOPIC_HOUSES = {
    "job": 10, "career": 10, "promotion": 10, "business": 10, "work": 10, "fame": 10,
    "love": 7, "relationship": 7, "marriage": 7, "partner": 7, "spouse": 7, "contract": 7,
    "wealth": 2, "money": 2, "finance": 2, "lost": 2, "family": 2, "income": 2,
    "health": 6, "disease": 6, "illness": 6, "enemy": 6, "court": 6, "legal": 6,
    "competition": 6, "litigation": 6,
    "property": 4, "home": 4, "house": 4, "vehicle": 4, "mother": 4, "land": 4,
    "child": 5, "children": 5, "pregnancy": 5, "education": 5, "speculation": 5, "exam": 5,
    "travel": 9, "visa": 9, "foreign": 9, "dharma": 9, "guru": 9,
    "gain": 11, "friend": 11, "wish": 11, "success": 11, "general": 11,
    "loss": 12, "hospital": 12, "foreign_settlement": 12, "moksha": 12,
}
HOUSE_MATTER = {
    1: "you and your body or vitality",
    2: "money, family, or something lost",
    3: "effort, siblings, or short travel",
    4: "home, property, mother, or a vehicle",
    5: "children, pregnancy, romance, or studies",
    6: "health, a dispute, debt, or an opponent",
    7: "marriage, a partner, or a contract",
    8: "a crisis, inheritance, or something hidden",
    9: "travel, a visa, luck, or a teacher",
    10: "career, work, status, or a public result",
    11: "a wish, gains, friends, or success",
    12: "loss, a hospital stay, or going abroad",
}
CATEGORY_MATTER = {
    "health": "this health question",
    "disease": "this health question",
    "illness": "this health question",
    "career": "this work or career result",
    "job": "this work or career result",
    "promotion": "this promotion or public result",
    "business": "this business result",
    "work": "this work or career result",
    "marriage": "this marriage or partnership",
    "love": "this relationship",
    "relationship": "this relationship",
    "partner": "this partnership",
    "wealth": "money or family matters",
    "money": "money or family matters",
    "finance": "money or family matters",
    "property": "home or property",
    "home": "home or property",
    "child": "children or pregnancy",
    "children": "children or pregnancy",
    "education": "studies or an exam",
    "exam": "studies or an exam",
    "travel": "travel or a visa",
    "visa": "travel or a visa",
    "legal": "this dispute or legal matter",
    "court": "this dispute or legal matter",
    "general": "what you asked",
}
CONFIDENCE_LABEL = {
    "high": "Clear",
    "medium": "Fairly clear",
    "low": "Tentative",
}


def _ordinal_house(house_num: int) -> str:
    n = int(house_num or 0)
    if n == 1:
        return "1st"
    if n == 2:
        return "2nd"
    if n == 3:
        return "3rd"
    return f"{n}th"


def _fmt_degree(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    degrees = int(number)
    minutes = int(round((number - degrees) * 60))
    if minutes == 60:
        degrees += 1
        minutes = 0
    return f"{degrees}°{minutes:02d}′"


def infer_category(question_text: str, category: Optional[str] = None) -> Tuple[str, int]:
    """Return (category_id, karya_house). Explicit category wins if mapped."""
    if category:
        key = str(category).strip().lower().replace(" ", "_")
        if key in TOPIC_HOUSES:
            return key, TOPIC_HOUSES[key]
    text = (question_text or "").lower()
    for key, house in TOPIC_HOUSES.items():
        if key.replace("_", " ") in text or key in text:
            return key, house
    return "general", 11


def _norm_lon(value: float) -> float:
    return float(value) % 360.0


def _sep(a: float, b: float) -> float:
    diff = abs(_norm_lon(a) - _norm_lon(b))
    return diff if diff <= 180 else 360 - diff


def _nakshatra_index(longitude: float) -> int:
    return int(_norm_lon(longitude) / (360.0 / 27.0)) % 27


def _pada(longitude: float) -> int:
    span = 360.0 / 27.0
    return int((_norm_lon(longitude) % span) / (span / 4.0)) + 1


@lru_cache(maxsize=1)
def kp_vimshottari_subs() -> Tuple[Dict[str, Any], ...]:
    """243 unequal vimshottari star-subs around the zodiac.

    KP asks for 1–249. Numbers 244–249 wrap the same table (the extra six
    come from Krishnamurti's published numbering, not equal 360/249 slices).
    """
    nak_span = 360.0 / 27.0
    rows: List[Dict[str, Any]] = []
    for n in range(27):
        start = n * nak_span
        star_lord = NAKSHATRA_LORDS[n]
        lord_idx = next(i for i, (planet, _) in enumerate(VIMSHOTTARI_YEARS) if planet == star_lord)
        order = VIMSHOTTARI_YEARS[lord_idx:] + VIMSHOTTARI_YEARS[:lord_idx]
        pos = start
        for planet, years in order:
            span = nak_span * years / 120.0
            rows.append({
                "index": len(rows) + 1,
                "nakshatra": NAKSHATRA_NAMES[n],
                "nakshatra_index": n,
                "star_lord": star_lord,
                "sub_lord": planet,
                "start_longitude": round(pos % 360, 6),
                "end_longitude": round((pos + span) % 360, 6),
                "span": round(span, 6),
            })
            pos += span
    return tuple(rows)


def kp_sub_for_number(number: int) -> Dict[str, Any]:
    subs = kp_vimshottari_subs()
    n = int(number)
    if n < 1 or n > 249:
        raise ValueError("horary_number must be between 1 and 249")
    row = dict(subs[(n - 1) % len(subs)])
    row["number"] = n
    row["table_size"] = len(subs)
    row["wrapped"] = n > len(subs)
    return row


def kp_sub_at_longitude(longitude: float) -> Dict[str, Any]:
    lon = _norm_lon(longitude)
    nak_span = 360.0 / 27.0
    for row in kp_vimshottari_subs():
        start = row["start_longitude"]
        end = start + row["span"]
        if end <= 360:
            if start <= lon < end:
                return dict(row)
        else:
            if lon >= start or lon < (end % 360):
                return dict(row)
    # Last sub of Revati closes the circle.
    last = dict(kp_vimshottari_subs()[-1])
    last["nakshatra"] = NAKSHATRA_NAMES[int(lon / nak_span) % 27]
    return last


class PrashnaCalculator:
    """Read a question-time D1 and return sequential Prashna evidence."""

    ORBS = DEEPTAMSA
    TOPIC_MAP = TOPIC_HOUSES

    def __init__(self, chart_data: Dict[str, Any]):
        self.chart = chart_data or {}
        self.planets = self.chart.get("planets") or {}
        self.ascendant = float(self.chart.get("ascendant") or 0.0)
        self.houses = self.chart.get("houses") or []
        self.asc_sign = int(self.ascendant / 30) % 12
        self.lagna_lord_name = SIGN_LORDS[self.asc_sign]
        self.lagna_lord = self._planet(self.lagna_lord_name)

    def analyze(
        self,
        question_text: str = "",
        category: Optional[str] = None,
        horary_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        category_id, karya_house = infer_category(question_text, category)
        karyesha_name = self._house_lord_name(karya_house)
        karyesha = self._planet(karyesha_name)
        moon = self._planet("Moon")

        gates = self._readability_gates(karya_house, karyesha_name)
        blocked = any(gate["status"] == "block" for gate in gates)

        tajika = self._tajika_stack(self.lagna_lord, karyesha, moon)
        parashari = self._parashari_sambandha(self.lagna_lord_name, karyesha_name)
        arudha = self._arudha_layer(karya_house)
        same_lord = self.lagna_lord_name == karyesha_name

        verdict = self._verdict(
            blocked=blocked,
            gates=gates,
            tajika=tajika,
            same_lord=same_lord,
            karyesha=karyesha,
            parashari=parashari,
        )
        timing = self._timing(tajika, karyesha)
        kp_overlay = self._kp_overlay(horary_number, karya_house) if horary_number else None

        payload = {
            "question": {
                "text": question_text or "",
                "category": category_id,
                "karya_house": karya_house,
            },
            "readable": not blocked,
            "gates": gates,
            "significators": {
                "lagnesha": self._describe_planet(self.lagna_lord_name, role="Lagnesha (querent)"),
                "karyesha": self._describe_planet(
                    karyesha_name,
                    role=f"Karyesha (lord of house {karya_house})",
                ),
                "moon": self._describe_planet("Moon", role="Moon (co-significator)"),
                "same_planet": same_lord,
            },
            "tajika": tajika,
            "parashari_sambandha": parashari,
            "arudha": arudha,
            "verdict": verdict,
            "timing": timing,
            "kp_overlay": kp_overlay,
            "layers": self._layer_index(kp_overlay is not None),
            "chart_snapshot": self._chart_snapshot(),
        }
        payload["explanation"] = self._build_explanation(payload)
        payload["chat_evidence"] = self.to_chat_evidence(payload)
        return payload

    def analyze_question(
        self,
        question_category: str = "job",
        question_text: str = "",
        horary_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Back-compat wrapper. Prefer ``analyze()``."""
        return self.analyze(
            question_text=question_text,
            category=question_category,
            horary_number=horary_number,
        )

    @staticmethod
    def to_chat_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Compact packet Instant/live chat can attach later. Not wired yet."""
        verdict = payload.get("verdict") or {}
        tajika = payload.get("tajika") or {}
        direct = tajika.get("direct") or {}
        return {
            "kind": "prashna",
            "clock": "question",
            "readable": payload.get("readable"),
            "answer": verdict.get("answer"),
            "confidence": verdict.get("confidence"),
            "summary": (payload.get("explanation") or {}).get("why") or verdict.get("summary"),
            "headline": (payload.get("explanation") or {}).get("headline"),
            "reasons": list(verdict.get("reasons") or []),
            "category": (payload.get("question") or {}).get("category"),
            "karya_house": (payload.get("question") or {}).get("karya_house"),
            "lagnesha": ((payload.get("significators") or {}).get("lagnesha") or {}).get("planet"),
            "karyesha": ((payload.get("significators") or {}).get("karyesha") or {}).get("planet"),
            "tajika_yoga": direct.get("type"),
            "tajika_aspect": direct.get("aspect"),
            "remaining_degrees": direct.get("remaining_degrees"),
            "gates": [
                {"id": gate.get("id"), "status": gate.get("status"), "label": gate.get("label")}
                for gate in (payload.get("gates") or [])
            ],
            "timing": payload.get("timing"),
            "has_kp_overlay": payload.get("kp_overlay") is not None,
        }

    def _planet(self, name: Optional[str]) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        data = self.planets.get(name)
        if not isinstance(data, dict):
            return None
        row = dict(data)
        row["name"] = name
        if "longitude" in row:
            row["longitude"] = _norm_lon(row["longitude"])
            if "degree" not in row:
                row["degree"] = row["longitude"] % 30
            if "sign" not in row:
                row["sign"] = int(row["longitude"] / 30) % 12
        return row

    def _house_sign(self, house_num: int) -> int:
        idx = int(house_num) - 1
        if 0 <= idx < len(self.houses) and isinstance(self.houses[idx], dict):
            sign = self.houses[idx].get("sign")
            if sign is not None:
                return int(sign) % 12
        return (self.asc_sign + idx) % 12

    def _house_lord_name(self, house_num: int) -> str:
        return SIGN_LORDS[self._house_sign(house_num)]

    def _signed_speed(self, planet: Optional[Dict[str, Any]]) -> float:
        if not planet:
            return 0.0
        if planet.get("speed") is not None:
            try:
                return float(planet["speed"])
            except (TypeError, ValueError):
                pass
        name = planet.get("name") or ""
        mean = MEAN_DAILY_MOTION.get(name, 0.5)
        if name in {"Rahu", "Ketu"}:
            return mean
        if planet.get("retrograde"):
            return -abs(mean)
        return mean

    def _describe_planet(self, name: str, role: str) -> Dict[str, Any]:
        planet = self._planet(name) or {}
        longitude = float(planet.get("longitude") or 0)
        sign = int(planet.get("sign") if planet.get("sign") is not None else longitude / 30) % 12
        nak_idx = _nakshatra_index(longitude)
        return {
            "planet": name,
            "role": role,
            "sign": sign,
            "sign_name": SIGN_NAMES[sign],
            "degree": round(float(planet.get("degree") if planet.get("degree") is not None else longitude % 30), 4),
            "longitude": round(longitude, 4),
            "house": int(planet.get("house") or self._house_of_sign(sign)),
            "retrograde": bool(planet.get("retrograde")),
            "nakshatra": NAKSHATRA_NAMES[nak_idx],
            "nakshatra_lord": NAKSHATRA_LORDS[nak_idx],
            "pada": _pada(longitude),
            "dignity": self._dignity(name, sign, float(planet.get("degree") or longitude % 30)),
            "combust": self._is_combust(name, longitude),
        }

    def _house_of_sign(self, sign: int) -> int:
        return ((int(sign) - self.asc_sign) % 12) + 1

    def _dignity(self, name: str, sign: int, degree: float) -> str:
        exalt = {
            "Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6,
        }
        debil = {
            "Sun": 6, "Moon": 7, "Mars": 3, "Mercury": 11, "Jupiter": 9, "Venus": 5, "Saturn": 0,
        }
        own = {
            "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
            "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
        }
        if exalt.get(name) == sign:
            return "exalted"
        if debil.get(name) == sign:
            return "debilitated"
        if sign in own.get(name, set()):
            return "own_sign"
        return "neutral"

    def _is_combust(self, name: str, longitude: float) -> bool:
        if name in {"Sun", "Rahu", "Ketu"}:
            return False
        sun = self._planet("Sun")
        if not sun:
            return False
        orb = COMBUSTION_ORBS.get(name)
        if not orb:
            return False
        return _sep(longitude, float(sun.get("longitude") or 0)) <= orb

    def _readability_gates(self, karya_house: int, karyesha_name: str) -> List[Dict[str, Any]]:
        gates: List[Dict[str, Any]] = []
        lagna_deg = self.ascendant % 30
        if lagna_deg <= 0.5 or lagna_deg >= 29.5:
            gates.append(self._gate(
                "lagna_sandhi", "block", "prashna_marga",
                "Lagna is in sandhi — the chart is not fit to read.",
                f"Lagna at {lagna_deg:.2f}° of {SIGN_NAMES[self.asc_sign]}",
            ))
        elif lagna_deg <= 1.0 or lagna_deg >= 29.0:
            gates.append(self._gate(
                "lagna_sandhi", "warn", "prashna_marga",
                "Lagna is near a sign junction. Read with caution.",
                f"Lagna at {lagna_deg:.2f}° of {SIGN_NAMES[self.asc_sign]}",
            ))
        else:
            gates.append(self._gate(
                "lagna_sandhi", "pass", "prashna_marga",
                "Lagna is clear of sign sandhi.",
                f"Lagna at {lagna_deg:.2f}° of {SIGN_NAMES[self.asc_sign]}",
            ))

        try:
            gandanta = GandantaCalculator(self.chart).calculate_gandanta_analysis()
        except Exception:
            gandanta = {}
        lagna_g = gandanta.get("lagna_gandanta") or {}
        lagna_g_name = (lagna_g.get("gandanta_info") or {}).get("gandanta_name") or lagna_g.get("gandanta_name")
        if lagna_g.get("is_gandanta"):
            gates.append(self._gate(
                "lagna_gandanta", "block", "prashna_marga",
                "Lagna is in gandanta — wait and ask again.",
                lagna_g_name or "gandanta",
            ))
        else:
            gates.append(self._gate(
                "lagna_gandanta", "pass", "prashna_marga",
                "Lagna is not in gandanta.",
            ))

        moon = self._planet("Moon") or {}
        moon_house = int(moon.get("house") or 0)
        moon_g = gandanta.get("moon_gandanta") or {}
        moon_g_name = (moon_g.get("gandanta_info") or {}).get("gandanta_name") or moon_g.get("gandanta_name")
        if moon_house in DUSTHANA:
            gates.append(self._gate(
                "moon_dusthana", "warn", "prashna_marga",
                "Moon occupies a dusthana (6/8/12). The matter is obstructed or hidden.",
                f"Moon in house {moon_house}",
            ))
        else:
            gates.append(self._gate(
                "moon_dusthana", "pass", "prashna_marga",
                "Moon is not in 6, 8, or 12.",
                f"Moon in house {moon_house}" if moon_house else None,
            ))
        if moon_g.get("is_gandanta"):
            gates.append(self._gate(
                "moon_gandanta", "warn", "prashna_marga",
                "Moon is in gandanta.",
                moon_g_name,
            ))

        voc = self._moon_void_of_course(moon)
        if voc.get("void"):
            gates.append(self._gate(
                "moon_void_of_course", "warn", "tajika",
                "Moon is void of course — no applying aspect before it leaves the sign.",
                voc.get("detail"),
            ))
        else:
            gates.append(self._gate(
                "moon_void_of_course", "pass", "tajika",
                "Moon still applies to a planet before changing sign.",
                voc.get("detail"),
            ))

        for upagraha in ("Gulika", "Mandi"):
            body = self._planet(upagraha) or {}
            house = int(body.get("house") or 0)
            if house in {1, karya_house}:
                gates.append(self._gate(
                    f"{upagraha.lower()}_obstruction", "warn", "prashna_marga",
                    f"{upagraha} sits on Lagna or the karya house — delay or poison around the matter.",
                    f"{upagraha} in house {house}",
                ))

        for name, label in ((self.lagna_lord_name, "Lagnesha"), (karyesha_name, "Karyesha")):
            planet = self._planet(name) or {}
            if self._is_combust(name, float(planet.get("longitude") or 0)):
                gates.append(self._gate(
                    f"{label.lower()}_combust", "warn", "prashna_marga",
                    f"{label} ({name}) is combust — the significator is weakened.",
                ))

        return gates

    @staticmethod
    def _gate(gate_id: str, status: str, school: str, label: str, detail: Optional[str] = None) -> Dict[str, Any]:
        row = {"id": gate_id, "status": status, "school": school, "label": label}
        if detail:
            row["detail"] = detail
        return row

    def _moon_void_of_course(self, moon: Dict[str, Any]) -> Dict[str, Any]:
        if not moon:
            return {"void": False, "detail": "Moon missing"}
        remaining_in_sign = 30.0 - float(moon.get("degree") if moon.get("degree") is not None else (moon.get("longitude") or 0) % 30)
        speed = self._signed_speed(moon)
        if speed <= 0:
            remaining_in_sign = float(moon.get("degree") or 0)
        nearest = None
        for name in CLASSICAL_PLANETS:
            if name == "Moon":
                continue
            other = self._planet(name)
            if not other:
                continue
            link = self._tajika_link(moon, other)
            if link.get("type") != "Ithasala":
                continue
            remaining = float(link.get("remaining_degrees") or 99)
            if nearest is None or remaining < nearest["remaining_degrees"]:
                nearest = {
                    "planet": name,
                    "remaining_degrees": remaining,
                    "aspect": link.get("aspect"),
                }
        if not nearest:
            return {"void": True, "detail": "Moon has no applying Tajika aspect"}
        if nearest["remaining_degrees"] > remaining_in_sign:
            return {
                "void": True,
                "detail": (
                    f"Next aspect to {nearest['planet']} is {nearest['remaining_degrees']:.2f}°, "
                    f"but only {remaining_in_sign:.2f}° remain in the sign"
                ),
            }
        return {
            "void": False,
            "detail": f"Moon applies to {nearest['planet']} ({nearest['aspect']}, {nearest['remaining_degrees']:.2f}° left)",
        }

    def _tajika_stack(
        self,
        lagnesha: Optional[Dict[str, Any]],
        karyesha: Optional[Dict[str, Any]],
        moon: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        direct = self._tajika_link(lagnesha, karyesha)
        moon_lagnesha = self._tajika_link(moon, lagnesha)
        moon_karyesha = self._tajika_link(moon, karyesha)
        kamboola = (
            direct.get("type") == "Ithasala"
            and moon_lagnesha.get("type") == "Ithasala"
            and moon_karyesha.get("type") == "Ithasala"
        )
        transfer = None
        if direct.get("type") not in {"Ithasala", "Easarpha"}:
            if moon_lagnesha.get("type") == "Ithasala" and moon_karyesha.get("type") == "Ithasala":
                transfer = {
                    "type": "Nakta",
                    "via": "Moon",
                    "detail": "Moon applies to both significators and carries the light.",
                }
            else:
                transfer = self._nakta_or_yamaya(lagnesha, karyesha)
        return {
            "direct": direct,
            "moon_to_lagnesha": moon_lagnesha,
            "moon_to_karyesha": moon_karyesha,
            "kamboola": kamboola,
            "transfer": transfer,
        }

    def _tajika_link(
        self,
        planet_a: Optional[Dict[str, Any]],
        planet_b: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not planet_a or not planet_b:
            return {"type": "None", "aspect": "None", "remaining_degrees": None, "orb": 0, "detail": "Missing planet"}
        if planet_a.get("name") == planet_b.get("name"):
            return {
                "type": "SamePlanet",
                "aspect": "Identity",
                "remaining_degrees": 0.0,
                "orb": 0,
                "detail": "Lagnesha and Karyesha are the same graha.",
            }

        orb = (DEEPTAMSA.get(planet_a.get("name"), 8) + DEEPTAMSA.get(planet_b.get("name"), 8)) / 2.0
        lon_a = float(planet_a.get("longitude") or 0)
        lon_b = float(planet_b.get("longitude") or 0)
        spd_a = self._signed_speed(planet_a)
        spd_b = self._signed_speed(planet_b)
        rel = (lon_a - lon_b) % 360.0
        rel_spd = spd_a - spd_b

        best_applying = None
        best_separating = None
        for aspect_angle, aspect_name in TAJIKA_ASPECTS:
            if abs(rel_spd) < 1e-6:
                dist = min(abs(rel - aspect_angle) % 360.0, 360.0 - abs(rel - aspect_angle) % 360.0)
                if dist <= orb:
                    best_separating = {
                        "type": "Easarpha",
                        "aspect": aspect_name,
                        "remaining_degrees": round(dist, 4),
                        "orb": round(orb, 4),
                        "detail": "Relative motion is stationary; the aspect is not applying.",
                    }
                continue
            if rel_spd > 0:
                to_exact = (aspect_angle - rel) % 360.0
            else:
                to_exact = (rel - aspect_angle) % 360.0
            from_exact = (360.0 - to_exact) % 360.0
            if to_exact <= orb and to_exact <= from_exact:
                candidate = {
                    "type": "Ithasala",
                    "aspect": aspect_name,
                    "remaining_degrees": round(to_exact, 4),
                    "orb": round(orb, 4),
                    "detail": f"Applying {aspect_name.lower()} within deeptamsa ({orb:.1f}°).",
                    "faster": planet_a.get("name") if abs(spd_a) >= abs(spd_b) else planet_b.get("name"),
                }
                if best_applying is None or to_exact < best_applying["remaining_degrees"]:
                    best_applying = candidate
            elif from_exact <= orb:
                candidate = {
                    "type": "Easarpha",
                    "aspect": aspect_name,
                    "remaining_degrees": round(from_exact, 4),
                    "orb": round(orb, 4),
                    "detail": f"Separating {aspect_name.lower()} — the contact has already peaked.",
                }
                if best_separating is None or from_exact < best_separating["remaining_degrees"]:
                    best_separating = candidate

        if best_applying:
            return best_applying
        if best_separating:
            return best_separating
        return {
            "type": "None",
            "aspect": "None",
            "remaining_degrees": None,
            "orb": round(orb, 4),
            "detail": "No Tajika aspect within deeptamsa.",
        }

    def _nakta_or_yamaya(
        self,
        lagnesha: Optional[Dict[str, Any]],
        karyesha: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not lagnesha or not karyesha:
            return None
        lon_a = float(lagnesha.get("longitude") or 0)
        lon_b = float(karyesha.get("longitude") or 0)
        span = (lon_b - lon_a) % 360.0
        names = {lagnesha.get("name"), karyesha.get("name")}
        for name in CLASSICAL_PLANETS:
            if name in names:
                continue
            other = self._planet(name)
            if not other:
                continue
            rel = (float(other.get("longitude") or 0) - lon_a) % 360.0
            if not (0 < rel < span or (span == 0)):
                if span < 180:
                    continue
                # Take the shorter arc between significators.
                span_short = min(span, 360.0 - span)
                if span_short <= 0 or rel >= span_short:
                    continue
            link_a = self._tajika_link(other, lagnesha)
            link_b = self._tajika_link(other, karyesha)
            if link_a.get("type") != "Ithasala" or link_b.get("type") != "Ithasala":
                continue
            other_spd = abs(self._signed_speed(other))
            pair_spd = min(abs(self._signed_speed(lagnesha)), abs(self._signed_speed(karyesha)))
            yoga = "Yamaya" if other_spd >= pair_spd else "Nakta"
            return {
                "type": yoga,
                "via": name,
                "detail": f"{yoga}: {name} applies to both significators and interpolates the light.",
            }
        return None

    def _parashari_sambandha(self, lagnesha_name: str, karyesha_name: str) -> Dict[str, Any]:
        lagna_p = self._planet(lagnesha_name) or {}
        karya_p = self._planet(karyesha_name) or {}
        h1 = int(lagna_p.get("house") or 0)
        h2 = int(karya_p.get("house") or 0)
        mutual = self._casts_drishti(lagnesha_name, h1, h2) and self._casts_drishti(karyesha_name, h2, h1)
        one_way = self._casts_drishti(lagnesha_name, h1, h2) or self._casts_drishti(karyesha_name, h2, h1)
        together = h1 and h1 == h2
        exchange = (
            SIGN_LORDS[int(lagna_p.get("sign") or 0)] == karyesha_name
            and SIGN_LORDS[int(karya_p.get("sign") or 0)] == lagnesha_name
            and lagnesha_name != karyesha_name
        )
        return {
            "school": "parashari",
            "conjunction": together,
            "mutual_drishti": mutual,
            "one_way_drishti": one_way and not mutual,
            "parivartana": exchange,
            "detail": (
                "Mutual graha drishti"
                if mutual
                else "Conjunction"
                if together
                else "Parivartana"
                if exchange
                else "One-way graha drishti"
                if one_way
                else "No Parashari sambandha"
            ),
        }

    @staticmethod
    def _casts_drishti(planet_name: str, from_house: int, to_house: int) -> bool:
        if not from_house or not to_house:
            return False
        for step in GRAHA_HOUSE_ASPECTS.get(planet_name, [1, 7]):
            target = (from_house + step - 2) % 12 + 1
            if target == to_house:
                return True
        return False

    def _arudha_layer(self, karya_house: int) -> Dict[str, Any]:
        try:
            jaimini = JaiminiPointCalculator(self.chart, {}, "")
            a1 = jaimini.calculate_house_arudha(1)
            ak = jaimini.calculate_house_arudha(karya_house)
        except Exception:
            a1 = {"sign_id": self.asc_sign, "sign_name": SIGN_NAMES[self.asc_sign], "name": "A1"}
            ak = {"sign_id": self._house_sign(karya_house), "sign_name": SIGN_NAMES[self._house_sign(karya_house)], "name": f"A{karya_house}"}
        a1_house = self._house_of_sign(int(a1.get("sign_id") or 0))
        ak_house = self._house_of_sign(int(ak.get("sign_id") or 0))
        return {
            "school": "jaimini",
            "udaya_lagna": {"sign": self.asc_sign, "sign_name": SIGN_NAMES[self.asc_sign], "degree": round(self.ascendant % 30, 4)},
            "arudha_lagna": {**a1, "house": a1_house, "dusthana": a1_house in DUSTHANA},
            "karya_arudha": {**ak, "house": ak_house, "dusthana": ak_house in DUSTHANA},
            "detail": (
                "Arudha Lagna in a dusthana — the matter may stay hidden or delayed in appearance."
                if a1_house in DUSTHANA
                else "Arudha Lagna is visible; compare appearance (A1) with udaya (question Lagna)."
            ),
        }

    def _verdict(
        self,
        *,
        blocked: bool,
        gates: List[Dict[str, Any]],
        tajika: Dict[str, Any],
        same_lord: bool,
        karyesha: Optional[Dict[str, Any]],
        parashari: Dict[str, Any],
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        if blocked:
            reasons = [gate["label"] for gate in gates if gate["status"] == "block"]
            return {
                "answer": "unclear",
                "label": "Unclear",
                "confidence": "low",
                "summary": "The Prashna chart is not fit to give a yes or no. Ask again after a short wait.",
                "reasons": reasons,
            }

        warns = [gate["label"] for gate in gates if gate["status"] == "warn"]
        direct = tajika.get("direct") or {}
        transfer = tajika.get("transfer")
        kamboola = bool(tajika.get("kamboola"))

        if same_lord:
            house = int((karyesha or {}).get("house") or 0)
            if house in KENDRA_TRIKONA_LABHA:
                answer, label, confidence = "yes", "Yes", "medium"
                summary = f"Lagnesha and Karyesha are the same graha, placed in house {house} — the matter sits with the querent."
            elif house in DUSTHANA:
                answer, label, confidence = "no", "No", "medium"
                summary = f"Lagnesha and Karyesha are the same graha, placed in dusthana house {house}."
            else:
                answer, label, confidence = "unclear", "Unclear", "low"
                summary = "Lagnesha and Karyesha are the same graha, but the house does not decide the matter cleanly."
            reasons = [summary, *warns]
            return {
                "answer": answer, "label": label, "confidence": confidence,
                "summary": summary, "reasons": reasons,
            }

        if direct.get("type") == "Ithasala":
            confidence = "high" if kamboola or float(direct.get("remaining_degrees") or 9) <= 3 else "medium"
            if kamboola:
                confidence = "high"
            summary = (
                f"Ithasala ({direct.get('aspect')}) between Lagnesha and Karyesha"
                f"{' with Kamboola (Moon completing the yoga)' if kamboola else ''}."
            )
            reasons = [summary, *warns]
            if warns and confidence == "high":
                confidence = "medium"
            return {
                "answer": "yes", "label": "Yes", "confidence": confidence,
                "summary": summary, "reasons": reasons,
            }

        if direct.get("type") == "Easarpha":
            summary = "Easarpha — the significators are separating. The moment has passed or the matter recedes."
            reasons = [summary, *warns]
            return {
                "answer": "no", "label": "No", "confidence": "medium",
                "summary": summary, "reasons": reasons,
            }

        if transfer:
            summary = transfer.get("detail") or f"{transfer.get('type')} yoga transfers the light."
            reasons = [summary, *warns]
            return {
                "answer": "yes", "label": "Yes", "confidence": "medium",
                "summary": summary, "reasons": reasons,
            }

        if parashari.get("mutual_drishti") or parashari.get("parivartana") or parashari.get("conjunction"):
            summary = f"No Tajika Ithasala, but Parashari sambandha is present ({parashari.get('detail')})."
            reasons = [summary, *warns]
            return {
                "answer": "yes", "label": "Yes", "confidence": "low",
                "summary": summary, "reasons": reasons,
            }

        karya_name = (karyesha or {}).get("name") or "the matter’s lord"
        summary = (
            f"{self.lagna_lord_name} stands for you and {karya_name} stands for the matter. "
            "They are not applying toward each other, so this does not look ready to happen now."
        )
        reasons = [summary, *warns]
        return {
            "answer": "no", "label": "No", "confidence": "low",
            "summary": summary, "reasons": reasons,
        }

    def _build_explanation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Plain-language reading for the screen (and later, chat)."""
        question = payload.get("question") or {}
        verdict = payload.get("verdict") or {}
        tajika = payload.get("tajika") or {}
        direct = tajika.get("direct") or {}
        you = (payload.get("significators") or {}).get("lagnesha") or {}
        matter = (payload.get("significators") or {}).get("karyesha") or {}
        moon = (payload.get("significators") or {}).get("moon") or {}
        karya_house = int(question.get("karya_house") or 11)
        matter_phrase = CATEGORY_MATTER.get(question.get("category")) or HOUSE_MATTER.get(
            karya_house, "what you asked"
        )
        you_name = you.get("planet") or self.lagna_lord_name
        matter_name = matter.get("planet") or "the matter’s planet"
        answer = verdict.get("answer")
        confidence = verdict.get("confidence") or "low"
        snapshot = payload.get("chart_snapshot") or {}
        lagna = snapshot.get("ascendant") or {}
        lagna_sign = lagna.get("sign_name") or SIGN_NAMES[self.asc_sign]
        lagna_deg = _fmt_degree(lagna.get("degree") if lagna.get("degree") is not None else self.ascendant % 30)
        you_place = f"{_fmt_degree(you.get('degree'))} {you.get('sign_name')}, {_ordinal_house(you.get('house'))} house"
        matter_place = f"{_fmt_degree(matter.get('degree'))} {matter.get('sign_name')}, {_ordinal_house(matter.get('house'))} house"
        moon_place = f"{_fmt_degree(moon.get('degree'))} {moon.get('sign_name')}, {_ordinal_house(moon.get('house'))} house"

        if answer == "yes":
            headline = "Yes — this looks like it can happen"
        elif answer == "unclear":
            headline = "Unclear — wait and ask again"
        else:
            headline = "No — not at this moment"

        setup = (
            f"The rising sign at the moment of asking is {lagna_sign} {lagna_deg}. "
            f"That makes {you_name} the planet that stands for you. "
            f"The question is read from the {_ordinal_house(karya_house)} house ({matter_phrase}), "
            f"so {matter_name} stands for the matter."
        )

        yoga = direct.get("type")
        aspect = str(direct.get("aspect") or "contact").lower()
        remaining = direct.get("remaining_degrees")
        remaining_bit = f", about {remaining}° apart" if remaining is not None else ""
        transfer = tajika.get("transfer")
        if answer == "unclear" and not payload.get("readable"):
            blocks = [gate.get("label") for gate in (payload.get("gates") or []) if gate.get("status") == "block"]
            why = (
                "This chart is not fit to give a firm yes or no. "
                + (" ".join(blocks) if blocks else "The rising sign is too unstable.")
                + " Ask the same question again after a short wait."
            )
        elif yoga == "Ithasala":
            why = (
                f"{you_name} (you) and {matter_name} (the matter) are still moving toward "
                f"an exact {aspect}{remaining_bit}. "
                "That applying contact is the main signature of a future yes."
            )
            if tajika.get("kamboola"):
                why += " The Moon is also applying to both, which strengthens the yes."
        elif yoga == "Easarpha":
            why = (
                f"{you_name} (you) and {matter_name} (the matter) have already passed their exact aspect "
                "and are moving apart. That usually means the moment has gone by, or the matter is receding."
            )
        elif transfer:
            why = (
                f"{you_name} and {matter_name} are not applying to each other directly, "
                f"but {transfer.get('via', 'another planet')} is carrying the contact between them. "
                "That is a weaker yes."
            )
        elif (payload.get("parashari_sambandha") or {}).get("mutual_drishti") or (
            payload.get("parashari_sambandha") or {}
        ).get("conjunction") or (payload.get("parashari_sambandha") or {}).get("parivartana"):
            why = (
                f"{you_name} and {matter_name} are not still moving toward an exact meeting, "
                "but they do have a Vedic link (aspect, conjunction, or exchange). "
                "That is only a supporting argument, so the yes is cautious."
            )
        elif (payload.get("significators") or {}).get("same_planet"):
            house_n = int(you.get("house") or 0)
            if house_n in KENDRA_TRIKONA_LABHA:
                house_lean = "That placement is generally supportive, so this leans yes."
            elif house_n in DUSTHANA:
                house_lean = "That placement is generally obstructive, so this leans no."
            else:
                house_lean = "That house does not decide this cleanly."
            why = (
                f"The same planet, {you_name}, stands for both you and {matter_phrase}, "
                f"sitting in the {_ordinal_house(you.get('house'))} house. {house_lean}"
            )
        else:
            why = (
                f"{you_name} stands for you. {matter_name} stands for {matter_phrase}. "
                "For a yes, those two planets need to still be moving toward an exact meeting — "
                "the sky closing on the question. They are not doing that, and the Moon is not "
                "carrying the contact from one to the other. So this does not look ready to happen now."
            )

        warns = [gate for gate in (payload.get("gates") or []) if gate.get("status") == "warn"]
        if payload.get("readable") and not warns:
            readable = (
                "The chart itself is fit to read: the rising sign is not on a junction, "
                "and the Moon is not in a 6th, 8th, or 12th house."
            )
        elif payload.get("readable"):
            readable = (
                "The chart can be read, with caution: "
                + " ".join(gate.get("label") for gate in warns)
            )
        else:
            readable = "Do not force a yes or no from this chart. Wait, then ask again."

        caveat = (
            "This is not a lifetime verdict. It is a snapshot of this question, at this time and place. "
            "If the situation is still live, you can ask again later."
            if answer != "unclear"
            else "Come back to the same question after the rising sign has moved a little."
        )

        confidence_why = {
            "high": "The two planets that decide this question are applying closely, so the signal is strong.",
            "medium": "There is a real applying contact, but it is not the tightest possible meeting.",
            "low": "The two planets are not moving toward each other, so this is a lean rather than a loud verdict.",
        }.get(confidence, "")
        if answer == "unclear":
            confidence_why = "The chart is not stable enough for a firm answer."

        timing = payload.get("timing") or {}
        timing_text = None
        if timing.get("available") and answer == "yes":
            timing_text = (
                f"If it happens, the remaining gap suggests a window of about {timing.get('prediction', '').replace('Within ', '')} "
                f"({timing.get('scale')})."
            )

        kp = payload.get("kp_overlay")
        kp_text = None
        if kp:
            lagna_kp = kp.get("lagna") or {}
            kp_text = (
                f"You also gave KP number {kp.get('number')}. That only marks a KP sub starting at "
                f"{lagna_kp.get('sign_name')} {_fmt_degree(lagna_kp.get('degree'))} "
                f"({lagna_kp.get('star_lord')}/{lagna_kp.get('sub_lord')}). "
                "It is a second school’s overlay and does not override this yes or no."
            )

        arudha = payload.get("arudha") or {}
        arudha_text = None
        if (arudha.get("arudha_lagna") or {}).get("dusthana"):
            arudha_text = (
                "How the matter appears (Arudha Lagna) falls in a 6th, 8th, or 12th house, "
                "so even if something happens it may stay hidden or delayed in public view."
            )

        return {
            "headline": headline,
            "answer": answer,
            "confidence_label": CONFIDENCE_LABEL.get(confidence, "Tentative"),
            "confidence_why": confidence_why,
            "setup": setup,
            "why": why,
            "readable": readable,
            "caveat": caveat,
            "timing": timing_text,
            "kp": kp_text,
            "arudha": arudha_text,
            "you": {
                "title": "You in this chart",
                "body": (
                    f"{you_name} stands for you because {lagna_sign} is rising. "
                    f"It sits at {you_place}."
                ),
            },
            "matter": {
                "title": "The matter",
                "body": (
                    f"{matter_name} stands for {matter_phrase} as lord of the "
                    f"{_ordinal_house(karya_house)} house. It sits at {matter_place}."
                ),
            },
            "moon": {
                "title": "The Moon",
                "body": (
                    f"The Moon shows how the question is flowing. It sits at {moon_place}."
                    + (
                        " It is not in a 6th, 8th, or 12th house, which is a good sign for a readable chart."
                        if int(moon.get("house") or 0) not in DUSTHANA
                        else " It is in a 6th, 8th, or 12th house, so the matter may feel obstructed or hidden."
                    )
                ),
            },
        }

    def _timing(self, tajika: Dict[str, Any], karyesha: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        direct = tajika.get("direct") or {}
        remaining = direct.get("remaining_degrees")
        if remaining is None:
            transfer = tajika.get("transfer") or {}
            for key in ("moon_to_karyesha", "moon_to_lagnesha"):
                rem = (tajika.get(key) or {}).get("remaining_degrees")
                if rem is not None:
                    remaining = rem
                    break
            if remaining is None:
                return {
                    "available": False,
                    "detail": "No applying aspect from which to time the event.",
                }
        sign = int((karyesha or {}).get("sign") or self.asc_sign) % 12
        if sign in MOVABLE_SIGNS:
            unit, scale = "days", "chara (movable) sign"
        elif sign in FIXED_SIGNS:
            unit, scale = "months", "sthira (fixed) sign"
        else:
            unit, scale = "weeks", "dvisvabhava (dual) sign"
        value = round(float(remaining), 1)
        return {
            "available": True,
            "value": value,
            "unit": unit,
            "scale": scale,
            "prediction": f"Within {value} {unit}",
            "basis": "Remaining degrees to exact Tajika aspect, scaled by the karya lord's sign (chara/sthira/dvisvabhava).",
        }

    def _kp_overlay(self, horary_number: int, karya_house: int) -> Dict[str, Any]:
        sub = kp_sub_for_number(int(horary_number))
        lagna_lon = float(sub["start_longitude"])
        lagna_sign = int(lagna_lon / 30) % 12
        karya_lon = (lagna_lon + (int(karya_house) - 1) * 30) % 360
        karya_sub = kp_sub_at_longitude(karya_lon)
        return {
            "school": "kp",
            "number": int(horary_number),
            "note": (
                "KP overlay only. The question-time chart remains the Prashna D1. "
                "Number 1–249 selects a vimshottari sub as a cuspal lagna, not a digit-to-planet map."
            ),
            "lagna_sub": sub,
            "lagna": {
                "longitude": round(lagna_lon, 4),
                "sign": lagna_sign,
                "sign_name": SIGN_NAMES[lagna_sign],
                "degree": round(lagna_lon % 30, 4),
                "nakshatra": NAKSHATRA_NAMES[_nakshatra_index(lagna_lon)],
                "star_lord": sub["star_lord"],
                "sub_lord": sub["sub_lord"],
            },
            "karya_cusp_sub": {
                "house": karya_house,
                "longitude": round(karya_lon, 4),
                "star_lord": karya_sub.get("star_lord"),
                "sub_lord": karya_sub.get("sub_lord"),
                "nakshatra": karya_sub.get("nakshatra"),
            },
        }

    def _layer_index(self, has_kp: bool) -> List[Dict[str, str]]:
        layers = [
            {"id": "prashna_marga", "label": "Prashna Marga", "role": "Readability gates, Lagnesha, Karyesha, Moon"},
            {"id": "tajika", "label": "Tajika Neelakanthi", "role": "Ithasala family of yogas and timing"},
            {"id": "parashari", "label": "Parashari", "role": "Supporting graha drishti / parivartana only"},
            {"id": "jaimini", "label": "Jaimini", "role": "Arudha (appearance) vs Udaya (question lagna)"},
        ]
        if has_kp:
            layers.append({"id": "kp", "label": "KP", "role": "Optional 1–249 cuspal-sub overlay"})
        return layers

    def _chart_snapshot(self) -> Dict[str, Any]:
        planets = []
        for name in CLASSICAL_PLANETS:
            if name in self.planets:
                planets.append(self._describe_planet(name, role=""))
        extras = []
        for name in ("Gulika", "Mandi"):
            if name in self.planets:
                extras.append(self._describe_planet(name, role=name))
        return {
            "ascendant": {
                "longitude": round(self.ascendant, 4),
                "sign": self.asc_sign,
                "sign_name": SIGN_NAMES[self.asc_sign],
                "degree": round(self.ascendant % 30, 4),
                "nakshatra": NAKSHATRA_NAMES[_nakshatra_index(self.ascendant)],
            },
            "planets": planets,
            "upagrahas": extras,
        }
