"""Classical, auditable foundations used by the professional Jaimini screen.

This module deliberately returns calculations and their derivations.  It does
not attach modern personality text or mix Parashari graha drishti with Jaimini
rashi drishti.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence


SIGN_NAMES: Sequence[str] = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

SIGN_LORDS: Sequence[str] = (
    "Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
    "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter",
)

VISIBLE_GRAHAS: Sequence[str] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)
JAIMINI_GRAHAS = frozenset((*VISIBLE_GRAHAS, "Rahu", "Ketu"))

SEVEN_KARAKAS: Sequence[tuple[str, str]] = (
    ("AK", "Atmakaraka"),
    ("AmK", "Amatyakaraka"),
    ("BK", "Bhratrikaraka"),
    ("MK", "Matrikaraka"),
    ("PK", "Putrakaraka"),
    ("GK", "Gnatikaraka"),
    ("DK", "Darakaraka"),
)

EIGHT_KARAKAS: Sequence[tuple[str, str]] = (
    ("AK", "Atmakaraka"),
    ("AmK", "Amatyakaraka"),
    ("BK", "Bhratrikaraka"),
    ("MK", "Matrikaraka"),
    ("PiK", "Pitrikaraka"),
    ("PK", "Putrakaraka"),
    ("GK", "Gnatikaraka"),
    ("DK", "Darakaraka"),
)

MOVABLE = frozenset((0, 3, 6, 9))
FIXED = frozenset((1, 4, 7, 10))
DUAL = frozenset((2, 5, 8, 11))


class ClassicalJaiminiInputError(ValueError):
    """Raised when a required astronomical position is unavailable."""


def _unwrap_chart(chart: Mapping[str, Any] | None) -> Dict[str, Any]:
    value: Mapping[str, Any] = chart or {}
    nested = value.get("divisional_chart")
    if isinstance(nested, Mapping):
        value = nested
    return dict(value)


def _longitude(data: Mapping[str, Any], subject: str) -> float:
    try:
        return float(data["longitude"]) % 360.0
    except (KeyError, TypeError, ValueError) as exc:
        raise ClassicalJaiminiInputError(f"Longitude is required for {subject}") from exc


def _sign(data: Mapping[str, Any], subject: str) -> int:
    value = data.get("sign")
    if isinstance(value, str):
        try:
            return SIGN_NAMES.index(value.title())
        except ValueError:
            pass
    try:
        numeric = int(value)
        if 0 <= numeric <= 11:
            return numeric
    except (TypeError, ValueError):
        pass
    return int(_longitude(data, subject) // 30.0) % 12


def _degree_text(value: float, *, allow_thirty: bool = False) -> str:
    if allow_thirty and abs(value - 30.0) < 1e-9:
        return "30° 00′ 00″"
    total_seconds = int(round((value % 30.0) * 3600.0))
    if total_seconds >= 30 * 3600:
        total_seconds = 30 * 3600 - 1
    degree, remainder = divmod(total_seconds, 3600)
    minute, second = divmod(remainder, 60)
    return f"{degree}° {minute:02d}′ {second:02d}″"


class ClassicalJaiminiCalculator:
    """Calculate the stable structural parts of a Jaimini worksheet."""

    VERSION = "classical-jaimini-v1"

    def __init__(self, d1_chart: Mapping[str, Any], d9_chart: Mapping[str, Any]):
        self.d1 = _unwrap_chart(d1_chart)
        self.d9 = _unwrap_chart(d9_chart)
        self.d1_planets = self.d1.get("planets") or {}
        self.d9_planets = self.d9.get("planets") or {}
        if not isinstance(self.d1_planets, Mapping) or not self.d1_planets:
            raise ClassicalJaiminiInputError("D1 planets are required")
        if not isinstance(self.d9_planets, Mapping) or not self.d9_planets:
            raise ClassicalJaiminiInputError("D9 planets are required")
        if self.d1.get("ascendant") is None:
            raise ClassicalJaiminiInputError("D1 ascendant is required")
        self.asc_sign = int(float(self.d1["ascendant"]) % 360.0 // 30.0)

    def calculate(self) -> Dict[str, Any]:
        schemes = {
            "seven": self._karaka_scheme(False),
            "eight": self._karaka_scheme(True),
        }
        padas = self._arudha_padas()
        by_house = {row["house"]: row for row in padas}
        return {
            "version": self.VERSION,
            "default_karaka_scheme": "seven",
            "karaka_schemes": schemes,
            "svamsha_karakamsha": {
                key: self._svamsha_karakamsha(value)
                for key, value in schemes.items()
            },
            "principal_padas": {
                "arudha_lagna": by_house[1],
                "darapada": by_house[7],
                "upapada": by_house[12],
            },
            "arudha_padas": padas,
            "rashi_drishti": self._rashi_drishti(),
            "calculation_basis": {
                "karakas": {
                    "reference": "Jaimini Upadesa Sutras 1.1.10–19 (commentarial numbering varies)",
                    "method": (
                        "Seven- and eight-karaka readings are kept separate. In the eight-karaka "
                        "reading Rahu is measured in reverse from 30°; Ketu is not ranked."
                    ),
                },
                "arudha": {
                    "reference": "Jaimini Upadesa Sutras 1.1.29‑32; Brihat Parashara Hora Shastra, Arudha chapter",
                    "method": (
                        "Count from a sign to its classical seven-graha lord and repeat that distance. "
                        "When the lord is 1st or 7th from the source, take the 10th; when it is "
                        "4th or 10th, take the 4th."
                    ),
                    "lordship_convention": "Mars rules Scorpio and Saturn rules Aquarius; nodes are not used as co-lords.",
                },
                "rashi_drishti": {
                    "reference": "Jaimini Upadesa Sutras 1.1.2‑3",
                    "method": (
                        "Movable signs aspect fixed signs except the adjacent fixed sign; fixed signs "
                        "aspect movable signs except the adjacent movable sign; dual signs aspect the other dual signs."
                    ),
                },
                "svamsha": {
                    "reference": "Jaimini Upadesa Sutras, first chapter, Karakamsha section",
                    "method": (
                        "Selected convention: Swamsha is the Navamsha sign occupied by the Atmakaraka; "
                        "Karakamsha uses that sign as a reference in D1. Commentarial terminology varies."
                    ),
                },
            },
        }

    def _planet_row(self, planet: str, effective_degree: float) -> Dict[str, Any]:
        d1 = self.d1_planets[planet]
        d9 = self.d9_planets.get(planet) or {}
        degree = _longitude(d1, planet) % 30.0
        sign = _sign(d1, planet)
        d9_sign = _sign(d9, f"{planet} in D9") if d9 else None
        return {
            "planet": planet,
            "degree_in_sign": round(degree, 8),
            "degree_text": _degree_text(degree),
            "ranking_degree": round(effective_degree, 8),
            "ranking_degree_text": _degree_text(effective_degree, allow_thirty=True),
            "measured_in_reverse": planet == "Rahu",
            "sign_id": sign,
            "sign_name": SIGN_NAMES[sign],
            "house": int(d1.get("house") or ((sign - self.asc_sign) % 12) + 1),
            "d9_sign_id": d9_sign,
            "d9_sign_name": SIGN_NAMES[d9_sign] if d9_sign is not None else None,
        }

    def _karaka_scheme(self, include_rahu: bool) -> Dict[str, Any]:
        roles = EIGHT_KARAKAS if include_rahu else SEVEN_KARAKAS
        planets: Iterable[str] = (*VISIBLE_GRAHAS, "Rahu") if include_rahu else VISIBLE_GRAHAS
        ranked = []
        for planet in planets:
            if planet not in self.d1_planets:
                raise ClassicalJaiminiInputError(f"{planet} is required for the selected Chara Karaka scheme")
            direct_degree = _longitude(self.d1_planets[planet], planet) % 30.0
            effective = 30.0 - direct_degree if planet == "Rahu" else direct_degree
            ranked.append(self._planet_row(planet, effective))
        # Planet name is a deterministic display order only. A true degree tie is
        # disclosed below rather than silently claimed to be resolved by it.
        ranked.sort(key=lambda row: (-row["ranking_degree"], row["planet"]))
        for index, (code, name) in enumerate(roles):
            ranked[index]["rank"] = index + 1
            ranked[index]["karaka_code"] = code
            ranked[index]["karaka_name"] = name
        tie_groups: List[Dict[str, Any]] = []
        for index, row in enumerate(ranked):
            peers = [
                peer["planet"] for peer in ranked
                if peer["planet"] != row["planet"]
                and abs(peer["ranking_degree"] - row["ranking_degree"]) <= (1.0 / 3600.0)
            ]
            if peers and not any(row["planet"] in group["planets"] for group in tie_groups):
                tie_groups.append({
                    "planets": sorted([row["planet"], *peers]),
                    "degree_text": row["ranking_degree_text"],
                    "requires_tradition_specific_resolution": True,
                })
        return {
            "scheme": "eight" if include_rahu else "seven",
            "rows": ranked,
            "atmakaraka": ranked[0]["planet"],
            "tie_groups": tie_groups,
            "is_unambiguous": not tie_groups,
        }

    def _svamsha_karakamsha(self, scheme: Mapping[str, Any]) -> Dict[str, Any]:
        ak = str(scheme["atmakaraka"])
        ak_d9 = self.d9_planets.get(ak)
        if not isinstance(ak_d9, Mapping):
            raise ClassicalJaiminiInputError(f"D9 position is required for Atmakaraka {ak}")
        sign = _sign(ak_d9, f"{ak} in D9")
        return {
            "atmakaraka": ak,
            "sign_id": sign,
            "sign_name": SIGN_NAMES[sign],
            "d1_reference_houses": self._relative_houses(self.d1_planets, sign),
            "d9_reference_houses": self._relative_houses(self.d9_planets, sign),
            "terminology": {
                "svamsha": "The Atmakaraka's Navamsha sign.",
                "karakamsha": "The same sign used as the reference Lagna in D1.",
            },
        }

    @staticmethod
    def _relative_houses(planets: Mapping[str, Any], base_sign: int) -> List[Dict[str, Any]]:
        rows = []
        for house in range(1, 13):
            sign = (base_sign + house - 1) % 12
            occupants = sorted(
                planet for planet, data in planets.items()
                if planet in JAIMINI_GRAHAS
                and isinstance(data, Mapping)
                and _sign(data, planet) == sign
            )
            rows.append({
                "house": house,
                "sign_id": sign,
                "sign_name": SIGN_NAMES[sign],
                "occupants": occupants,
            })
        return rows

    def _arudha_padas(self) -> List[Dict[str, Any]]:
        return [self._arudha_pada(house) for house in range(1, 13)]

    def _arudha_pada(self, house: int) -> Dict[str, Any]:
        source = (self.asc_sign + house - 1) % 12
        lord = SIGN_LORDS[source]
        lord_data = self.d1_planets.get(lord)
        if not isinstance(lord_data, Mapping):
            raise ClassicalJaiminiInputError(f"{lord} position is required to calculate A{house}")
        lord_sign = _sign(lord_data, lord)
        distance = (lord_sign - source) % 12
        raw = (lord_sign + distance) % 12
        exception = None
        if distance in (0, 6):
            result = (source + 9) % 12
            exception = "lord_in_1_or_7_take_10"
        elif distance in (3, 9):
            result = (source + 3) % 12
            exception = "lord_in_4_or_10_take_4"
        else:
            result = raw
        return {
            "house": house,
            "code": f"A{house}",
            "source_sign_id": source,
            "source_sign_name": SIGN_NAMES[source],
            "lord": lord,
            "lord_sign_id": lord_sign,
            "lord_sign_name": SIGN_NAMES[lord_sign],
            "distance_signs": distance + 1,
            "distance_steps": distance,
            "raw_sign_id": raw,
            "raw_sign_name": SIGN_NAMES[raw],
            "sign_id": result,
            "sign_name": SIGN_NAMES[result],
            "house_from_lagna": ((result - self.asc_sign) % 12) + 1,
            "exception": exception,
            "exception_applied": exception is not None,
        }

    @staticmethod
    def _aspected_signs(sign: int) -> List[int]:
        if sign in MOVABLE:
            return [target for target in sorted(FIXED) if target != (sign + 1) % 12]
        if sign in FIXED:
            return [target for target in sorted(MOVABLE) if target != (sign - 1) % 12]
        return [target for target in sorted(DUAL) if target != sign]

    def _rashi_drishti(self) -> List[Dict[str, Any]]:
        occupants = {sign: [] for sign in range(12)}
        for planet, data in self.d1_planets.items():
            if planet in JAIMINI_GRAHAS and isinstance(data, Mapping):
                occupants[_sign(data, planet)].append(planet)
        rows = []
        for sign in range(12):
            targets = self._aspected_signs(sign)
            rows.append({
                "sign_id": sign,
                "sign_name": SIGN_NAMES[sign],
                "modality": "movable" if sign in MOVABLE else "fixed" if sign in FIXED else "dual",
                "occupants": sorted(occupants[sign]),
                "aspected_signs": [
                    {
                        "sign_id": target,
                        "sign_name": SIGN_NAMES[target],
                        "occupants": sorted(occupants[target]),
                    }
                    for target in targets
                ],
            })
        return rows
