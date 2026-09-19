"""Deterministic Tājika primitives for the Hāyanaratna Prashna profile.

The module does astronomy-free interpretation of an already cast chart.  Every
public record names the rule it implements; callers must not turn an absent
match into a negative judgement.
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, Iterable, List, Optional

from prashna.source_ledger import TAJIKA_SOURCES


PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
SIGN_RULERS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
               "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
ORBS = {"Sun": 15.0, "Moon": 12.0, "Mars": 8.0, "Mercury": 7.0,
        "Jupiter": 9.0, "Venus": 7.0, "Saturn": 9.0}
ASPECTS = {0: "conjunction", 2: "sextile", 3: "square", 4: "trine", 6: "opposition",
           8: "trine", 9: "square", 10: "sextile"}
FRIENDLY_ASPECTS = {"sextile", "trine"}
HOSTILE_ASPECTS = {"square", "opposition"}
ANGLES = {1, 4, 7, 10}
SUCCEDENTS = {2, 5, 8, 11}
CADENTS = {3, 6, 9, 12}

DOMICILES = {
    "Sun": {4}, "Moon": {3}, "Mars": {0, 7}, "Mercury": {2, 5},
    "Jupiter": {8, 11}, "Venus": {1, 6}, "Saturn": {9, 10},
}
EXALTATION = {"Sun": (0, 10), "Moon": (1, 3), "Mars": (9, 28),
              "Mercury": (5, 15), "Jupiter": (3, 5), "Venus": (11, 27),
              "Saturn": (6, 20)}
FALL_SIGNS = {name: (sign + 6) % 12 for name, (sign, _) in EXALTATION.items()}
# Hayanaratna 2.4.1 lists several friendship schemes.  This calculator uses
# the explicitly tabulated, constant twofold scheme and exposes that choice in
# every dignity record; it must not silently substitute the later compound
# friendship table used by many natal calculators.
CONSTANT_FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mars", "Jupiter"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Venus", "Saturn"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}
MALE_PLANETS = {"Sun", "Mars", "Jupiter"}
HADDAS = (
    (("Jupiter", 6), ("Venus", 6), ("Mercury", 8), ("Mars", 5), ("Saturn", 5)),
    (("Venus", 8), ("Mercury", 6), ("Jupiter", 8), ("Saturn", 5), ("Mars", 3)),
    (("Mercury", 6), ("Venus", 6), ("Jupiter", 5), ("Mars", 7), ("Saturn", 6)),
    (("Mars", 7), ("Venus", 6), ("Mercury", 6), ("Jupiter", 7), ("Saturn", 4)),
    (("Jupiter", 6), ("Venus", 5), ("Saturn", 7), ("Mercury", 6), ("Mars", 6)),
    (("Mercury", 7), ("Venus", 10), ("Jupiter", 4), ("Mars", 7), ("Saturn", 2)),
    (("Saturn", 6), ("Mercury", 8), ("Jupiter", 7), ("Venus", 7), ("Mars", 2)),
    (("Mars", 7), ("Venus", 4), ("Mercury", 8), ("Jupiter", 5), ("Saturn", 6)),
    (("Jupiter", 12), ("Venus", 5), ("Mercury", 4), ("Mars", 5), ("Saturn", 4)),
    (("Mercury", 7), ("Jupiter", 7), ("Venus", 8), ("Saturn", 4), ("Mars", 4)),
    (("Mercury", 7), ("Venus", 6), ("Jupiter", 7), ("Mars", 5), ("Saturn", 5)),
    (("Venus", 12), ("Jupiter", 4), ("Mercury", 3), ("Mars", 9), ("Saturn", 2)),
)
DECANS = (
    ("Mars", "Sun", "Venus"), ("Mercury", "Moon", "Saturn"), ("Jupiter", "Mars", "Sun"),
    ("Venus", "Mercury", "Moon"), ("Saturn", "Jupiter", "Mars"), ("Sun", "Venus", "Mercury"),
    ("Moon", "Saturn", "Jupiter"), ("Mars", "Sun", "Venus"), ("Mercury", "Moon", "Saturn"),
    ("Jupiter", "Mars", "Sun"), ("Venus", "Mercury", "Moon"), ("Saturn", "Jupiter", "Mars"),
)
NAVAMSA_STARTS = (0, 9, 6, 3, 0, 9, 6, 3, 0, 9, 6, 3)


def signed_delta(value: float) -> float:
    return (value + 180.0) % 360.0 - 180.0


class TajikaClassicalEngine:
    """Calculate source-addressed contacts, conditions and sixteen yogas."""

    def __init__(self, chart: Dict):
        self.chart = chart
        self.planets = {name: dict(chart["planets"][name]) for name in PLANETS}
        for row in self.planets.values():
            row.setdefault("sign", int(row["longitude"] // 30))
            row.setdefault("degree", row["longitude"] % 30)
        self.ascendant = float(chart["ascendant"])
        self.asc_sign = int(self.ascendant // 30)
        self._contacts: Dict[tuple, Dict] = {}
        phase = (self.planets["Moon"]["longitude"] - self.planets["Sun"]["longitude"]) % 360
        self.benefics = {"Jupiter", "Venus"}
        if 0 < phase < 180:
            self.benefics.add("Moon")
        if not any(self.same_sign("Mercury", name) for name in ("Sun", "Mars", "Saturn")):
            self.benefics.add("Mercury")
        self.malefics = set(PLANETS) - self.benefics

    def house_lord(self, house: int) -> str:
        houses = self.chart.get("houses") or []
        if len(houses) == 12 and "cusp_sign" in houses[house - 1]:
            return SIGN_RULERS[int(houses[house - 1]["cusp_sign"])]
        return SIGN_RULERS[(self.asc_sign + house - 1) % 12]

    def house(self, name: str) -> int:
        return int((self.planets if name in self.planets else self.chart["planets"])[name]["house"])

    def same_sign(self, first: str, second: str) -> bool:
        return self.planets[first]["sign"] == self.planets[second]["sign"]

    def dignity(self, name: str) -> Dict:
        row = self.planets[name]
        sign, degree = int(row["sign"]), float(row["degree"])
        sign_ruler = SIGN_RULERS[sign]
        if sign_ruler == name:
            sign_relation = "own"
        elif sign_ruler in CONSTANT_FRIENDS[name]:
            sign_relation = "friend"
        else:
            sign_relation = "enemy"
        dignities: List[str] = []
        if sign in DOMICILES[name]:
            dignities.append("domicile")
        if sign == EXALTATION[name][0]:
            dignities.append("exaltation")
        elapsed = 0.0
        for ruler, span in HADDAS[sign]:
            elapsed += span
            if degree < elapsed or abs(degree - 30.0) < 1e-10:
                if ruler == name:
                    dignities.append("hadda")
                break
        if DECANS[sign][min(int(degree // 10), 2)] == name:
            dignities.append("decan")
        navamsa_sign = (NAVAMSA_STARTS[sign] + min(int(degree / (30.0 / 9.0)), 8)) % 12
        if SIGN_RULERS[navamsa_sign] == name:
            dignities.append("navamsa")
        if {"domicile", "exaltation"} & set(dignities):
            grade = "superior"
        elif dignities:
            grade = "middling"
        elif sign == FALL_SIGNS[name] or sign_relation == "enemy":
            grade = "inferior"
        else:
            grade = "neutral"
        points = sum({"domicile": 7.5, "exaltation": 5.0, "hadda": 3.75,
                      "decan": 2.5, "navamsa": 1.25}[item] for item in dignities)
        return {"grade": grade, "dignities": dignities, "points": round(points, 4),
                "fall": sign == FALL_SIGNS[name], "sign_ruler": sign_ruler,
                "sign_relation": sign_relation,
                "friendship_scheme": "Hayanaratna 2.4.1 constant twofold",
                "navamsa_sign": navamsa_sign}

    def contact(self, first: str, second: str) -> Dict:
        key = tuple(sorted((first, second)))
        if key in self._contacts:
            return self._contacts[key]
        if first == second:
            return {"first": first, "second": second, "state": "same_planet", "aspect": None,
                    "within_orb": True, "applying": False, "separating": False}
        a, b = self.planets[first], self.planets[second]
        current = (float(b["longitude"]) - float(a["longitude"])) % 360
        aspect_targets = {0: "conjunction", 60: "sextile", 90: "square", 120: "trine",
                          180: "opposition", 240: "trine", 270: "square", 300: "sextile", 360: "conjunction"}
        target = min(aspect_targets, key=lambda angle: abs(current - angle))
        aspect = aspect_targets[target]
        candidates = [angle for angle, label in aspect_targets.items() if label == aspect]
        target = min(candidates, key=lambda angle: abs(signed_delta(current - angle)))
        error = signed_delta(current - target)
        relative_speed = float(b.get("speed", 0)) - float(a.get("speed", 0))
        future = (current + relative_speed * 0.01) % 360
        future_error = min((signed_delta(future - angle) for angle in candidates), key=abs)
        applying = abs(error) > 1e-7 and abs(future_error) < abs(error)
        separating = abs(error) > 1e-7 and not applying
        swifter = max((first, second), key=lambda name: abs(float(self.planets[name].get("speed", 0))))
        orb = ORBS[swifter]
        distance = abs(error)
        within = distance <= orb
        if distance <= 1e-7:
            state = "exact"
        elif within and applying:
            state = "itthasala"
        elif within and separating and distance >= 1.0:
            state = "isarapha"
        elif within and separating:
            state = "perfected_itthasala"
        else:
            state = "none"
        strength = max(0.0, min(20.0, (orb - distance) / orb * 20.0)) if state in {"itthasala", "exact", "perfected_itthasala"} else None
        record = {"first": first, "second": second, "state": state, "aspect": aspect,
                  "distance": round(distance, 6), "orb": orb, "swifter": swifter,
                  "within_orb": within, "applying": state in {"itthasala", "exact"},
                  "separating": state in {"isarapha", "perfected_itthasala"},
                  "strength": round(strength, 6) if strength is not None else None}
        self._contacts[key] = record
        return record

    def aspects(self, first: str, second: str) -> bool:
        return self.contact(first, second)["state"] != "none"

    def applies(self, first: str, second: str) -> bool:
        return self.contact(first, second)["state"] in {"itthasala", "exact"}

    def afflictions(self, name: str) -> List[str]:
        row = self.planets[name]
        reasons = []
        if row.get("retrograde"):
            reasons.append("retrograde")
        if self.dignity(name)["fall"]:
            reasons.append("fall")
        if self.solar_condition(name) in {"set", "under_rays"}:
            reasons.append(self.solar_condition(name))
        if self.house(name) in {6, 8, 12}:
            reasons.append(f"cadent_or_difficult_house_{self.house(name)}")
        for malefic in sorted(self.malefics - {name}):
            link = self.contact(name, malefic)
            if link["state"] != "none" and link["aspect"] in HOSTILE_ASPECTS | {"conjunction"}:
                reasons.append(f"hostile_contact_{malefic}")
        for node in ("Rahu", "Ketu"):
            if node in self.chart.get("planets", {}) and int(self.chart["planets"][node]["sign"]) == int(row["sign"]):
                reasons.append(f"with_{node}")
        return reasons

    def solar_condition(self, name: str) -> str:
        if name == "Sun":
            return "visible"
        distance = abs(signed_delta(self.planets[name]["longitude"] - self.planets["Sun"]["longitude"]))
        limits = {"Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11, "Venus": 10, "Saturn": 15}
        if distance <= 3:
            return "set"
        if distance <= limits[name]:
            return "under_rays"
        return "visible"

    def time_strength(self, name: str) -> float:
        """Day/night strength from Hāyanaratna 2.6.3, on a 0..60 scale."""
        signs = ((self.ascendant - self.planets["Sun"]["longitude"]) % 360.0) / 30.0
        if name in MALE_PLANETS:
            points = signs * 20.0 if signs <= 3 else (6 - signs) * 20.0 if signs < 6 else 0.0
        else:
            points = 0.0 if signs < 6 else (signs - 6) * 20.0 if signs <= 9 else (12 - signs) * 20.0
        return round(max(0.0, min(60.0, points)), 6)

    def aspects_longitude(self, name: str, longitude: float) -> bool:
        row = self.planets[name]
        delta = (longitude - row["longitude"]) % 360.0
        distances = [abs(signed_delta(delta - angle)) for angle in (0, 60, 90, 120, 180, 240, 270, 300)]
        return min(distances) <= ORBS[name]

    def _gairikambula_helpers(self, first: str, second: str, direct: Dict) -> List[str]:
        moon = self.planets["Moon"]
        if direct["state"] not in {"itthasala", "exact"} or any(self.aspects("Moon", p) for p in (first, second)):
            return []
        speed = float(moon.get("speed", 0))
        if speed <= 0:
            return []
        ingress = (30.0 - float(moon["degree"])) / speed
        end = ingress + 30.0 / speed
        next_sign = (int(moon["sign"]) + 1) % 12
        helpers = []
        for target in PLANETS:
            if target == "Moon":
                continue
            dignity = self.dignity(target)
            if self.planets[target]["sign"] != next_sign or not ({"domicile", "exaltation"} & set(dignity["dignities"])):
                continue
            for step in range(1, 101):
                day = ingress + (end - ingress) * step / 100.0
                projected = {name: {**row, "longitude": (row["longitude"] + row.get("speed", 0) * day) % 360}
                             for name, row in self.planets.items()}
                for row in projected.values():
                    row["sign"], row["degree"] = int(row["longitude"] // 30), row["longitude"] % 30
                future_chart = {**self.chart, "planets": {**self.chart.get("planets", {}), **projected}}
                if TajikaClassicalEngine(future_chart).applies("Moon", target):
                    helpers.append(target)
                    break
        return helpers

    def _record(self, name: str, matched: bool, participants: Iterable[str] = (), **evidence) -> Dict:
        return {"name": name, "matched": bool(matched), "participants": list(participants),
                "source": TAJIKA_SOURCES[name], "evidence": evidence}

    def all_configurations(self, first: str, second: str, matter_house: Optional[int] = None) -> List[Dict]:
        direct = self.contact(first, second)
        records = [
            self._record("ikkavala", all(self.house(p) in ANGLES | SUCCEDENTS for p in PLANETS), PLANETS),
            self._record("induvara", all(self.house(p) in CADENTS for p in PLANETS), PLANETS),
            self._record("itthasala", direct["state"] in {"itthasala", "exact"}, (first, second), contact=direct),
            self._record("isarapha", direct["state"] == "isarapha", (first, second), contact=direct),
        ]
        intermediaries = [p for p in PLANETS if p not in {first, second}]
        def transfers(p):
            states = {self.contact(p, first)["state"], self.contact(p, second)["state"]}
            applying = bool(states & {"itthasala", "exact"})
            separating = bool(states & {"isarapha", "perfected_itthasala", "exact"})
            return applying and separating
        nakta = [p for p in intermediaries if transfers(p)
                 and abs(self.planets[p]["speed"]) > max(abs(self.planets[first]["speed"]), abs(self.planets[second]["speed"]))]
        yamaya = [p for p in intermediaries if transfers(p)
                  and abs(self.planets[p]["speed"]) < min(abs(self.planets[first]["speed"]), abs(self.planets[second]["speed"]))]
        gairi_helpers = self._gairikambula_helpers(first, second, direct)
        records.extend([
            self._record("nakta", bool(nakta) and direct["state"] == "none", (first, second, *nakta), intermediaries=nakta),
            self._record("yamaya", bool(yamaya) and direct["state"] == "none", (first, second, *yamaya), intermediaries=yamaya),
        ])
        manau = []
        swifter_significator = max((first, second), key=lambda p: abs(self.planets[p]["speed"]))
        if direct["state"] in {"itthasala", "exact"}:
            for malefic in ("Mars", "Saturn"):
                if malefic in {first, second}:
                    continue
                hostile_link = self.contact(malefic, swifter_significator)
                takes_light = hostile_link["state"] != "none" and hostile_link["aspect"] in HOSTILE_ASPECTS | {"conjunction"}
                occupies_matter = matter_house is not None and self.house(malefic) == matter_house and hostile_link["within_orb"]
                if takes_light or occupies_matter:
                    manau.append(malefic)
        moon_links = [p for p in (first, second) if self.applies("Moon", p)]
        kambula = direct["state"] in {"itthasala", "exact"} and bool(moon_links)
        records.extend([
            self._record("manau", bool(manau), (first, second, *manau), malefics=manau),
            self._record("kambula", kambula, (first, second, "Moon"), moon_links=moon_links,
                         grades={p: self.dignity(p)["grade"] for p in {first, second, "Moon"}}),
            self._record("gairikambula", bool(gairi_helpers), (first, second, "Moon", *gairi_helpers),
                         helpers=gairi_helpers, method="true-motion projection to Moon's next sign"),
            self._record("khallasara", direct["state"] in {"itthasala", "exact"} and not moon_links,
                         (first, second, "Moon"), contact=direct),
        ])
        receiver = second if abs(self.planets[first]["speed"]) > abs(self.planets[second]["speed"]) else first
        radda_reasons = self.afflictions(receiver) if direct["state"] in {"itthasala", "exact"} else []
        swift = direct.get("swifter")
        slow = second if swift == first else first
        duh = bool(swift and direct["state"] in {"itthasala", "exact"}
                   and self.dignity(swift)["grade"] in {"neutral", "inferior"}
                   and self.dignity(slow)["grade"] in {"superior", "middling"})
        weak_pair = all(self.dignity(p)["grade"] in {"neutral", "inferior"} for p in (first, second))
        helpers = [p for p in intermediaries if self.dignity(p)["grade"] in {"superior", "middling"}
                   and self.aspects(p, first) and self.aspects(p, second)]
        tambira_helpers = []
        for significator in (first, second):
            tambira_helpers.extend(p for p in intermediaries if self.planets[significator]["degree"] >= 27
                and self.planets[p]["sign"] == (self.planets[significator]["sign"] + 1) % 12
                and self.applies(significator, p) and self.dignity(p)["grade"] in {"superior", "middling"})
        tambira_helpers = sorted(set(tambira_helpers))
        records.extend([
            self._record("radda", bool(radda_reasons), (first, receiver), receiver=receiver, reasons=radda_reasons),
            self._record("duhphalikutta", duh, (first, second), swifter=swift, slower=slow),
            self._record("dutthotthadabira", weak_pair and bool(helpers), (first, second, *helpers), helpers=helpers),
            self._record("tambira", direct["state"] == "none" and bool(tambira_helpers), (first, *tambira_helpers), helpers=tambira_helpers),
        ])
        kuttha = {}
        duruhpha = {}
        for p in (first, second):
            benefic_support = any(self.aspects(p, b) for b in self.benefics - {p})
            bad = self.afflictions(p)
            kuttha[p] = (self.dignity(p)["grade"] in {"superior", "middling"} and self.house(p) in ANGLES
                         and self.aspects_longitude(p, self.ascendant)
                         and benefic_support and not self.planets[p].get("retrograde")
                         and self.solar_condition(p) == "visible" and self.time_strength(p) > 0 and not bad)
            duruhpha[p] = bad
        records.extend([
            self._record("kuttha", any(kuttha.values()), (first, second), planets=kuttha,
                         time_strength={p: self.time_strength(p) for p in (first, second)}),
            self._record("duruhpha", any(duruhpha.values()), (first, second), planets=duruhpha),
        ])
        return records

    def contact_records(self) -> List[Dict]:
        for first, second in combinations(PLANETS, 2):
            self.contact(first, second)
        return list(self._contacts.values())
