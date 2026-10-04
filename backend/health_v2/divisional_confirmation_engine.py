"""D30 confirmation for an already-established D1 health vulnerability.

Trimsamsa is a qualifier here. It may repeat pressure, intervention potential
or protection, but it never creates anatomy, a condition, or a dated window.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable


VISIBLE_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
NODES = {"Rahu", "Ketu"}
DUSTHANA = {6, 8, 12}
SUPPORTIVE_DIGNITIES = {"own_sign", "exalted", "moolatrikona"}
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}
MEDICAL_HOUSE_SOURCE = {
    "author": "Dr K. S. Charak",
    "work": "Essentials of Medical Astrology",
    "chapter": 4,
    "section": "Significations of Houses",
}

# Medical house anatomy used by Dr K. S. Charak in Essentials of Medical
# Astrology, chapter 4.  Keep this separate from the concise Kalapurusha limb
# labels used by chart headers: this table exists to explain why a D30
# house-lord placement repeats a *previously established* D1 health area.
D30_HOUSE_ANATOMY = {
    1: ("head", "brain", "body", "vitality"),
    2: ("face", "eyes", "teeth", "tongue", "mouth", "nose", "nails"),
    3: ("ears", "throat", "neck", "shoulders", "arms", "trachea", "oesophagus"),
    4: ("chest", "lungs", "heart", "thoracic blood vessels", "breasts"),
    5: ("heart", "upper abdomen", "stomach", "liver", "gall bladder", "spleen", "pancreas", "duodenum"),
    6: ("small intestine", "mesentery", "appendix", "large intestine", "kidneys", "upper ureters"),
    7: ("large intestine", "rectum", "anal canal", "lower urinary tract", "uterus", "ovaries", "testes", "prostate", "groins"),
    8: ("external genitalia", "perineum", "anal orifice"),
    9: ("hips", "thighs", "femoral arteries"),
    10: ("knees", "patella", "popliteal fossa"),
    11: ("legs", "left ear"),
    12: ("feet", "left eye", "sleep", "hospitalisation"),
}

# A planet qualifies how an already-matched anatomical D30 bridge may express.
# These are broad astrological mechanisms, not diagnoses.
PLANET_PATHOLOGY = {
    "Sun": ("heat", "inflammation", "circulation"),
    "Moon": ("fluids", "swelling", "cyclical variation"),
    "Mars": ("inflammation", "suppuration", "tissue injury", "surgical intervention"),
    "Mercury": ("nerves", "skin", "ducts", "branching tracts"),
    "Jupiter": ("growth", "metabolism", "recovery capacity"),
    "Venus": ("reproductive", "urinary", "venous", "glandular"),
    "Saturn": ("chronicity", "obstruction", "hardening", "delayed healing"),
}

ANATOMY_ALIASES = {
    "anorectal": {"rectum", "anal canal", "anal orifice", "perineum"},
    "anus": {"anal canal", "anal orifice"},
    "anal": {"anal canal", "anal orifice"},
    "pelvic": {"pelvis", "perineum", "rectum", "anal canal", "anal orifice", "reproductive"},
    "pelvis": {"pelvis", "perineum", "rectum", "anal canal", "anal orifice", "reproductive"},
    "intestinal": {"small intestine", "large intestine", "rectum"},
    "intestines": {"small intestine", "large intestine", "rectum"},
    "digestive": {"stomach", "liver", "gall bladder", "spleen", "pancreas", "duodenum", "small intestine", "large intestine"},
    "urinary": {"kidneys", "upper ureters", "lower urinary tract"},
    "reproductive": {"uterus", "ovaries", "testes", "prostate", "external genitalia"},
    "knee": {"knees", "patella", "popliteal fossa"},
    "knees": {"knees", "patella", "popliteal fossa"},
}


def _planet(chart: Dict[str, Any], name: str) -> Dict[str, Any]:
    value = (chart.get("planets") or {}).get(name)
    return value if isinstance(value, dict) else {}


def _house(chart: Dict[str, Any], name: str) -> int | None:
    try:
        value = int(_planet(chart, name).get("house"))
        return value if 1 <= value <= 12 else None
    except (TypeError, ValueError):
        return None


def _sign(chart: Dict[str, Any], name: str) -> int | None:
    try:
        return int(_planet(chart, name).get("sign")) % 12
    except (TypeError, ValueError):
        return None


def _dignity(chart: Dict[str, Any], name: str) -> str:
    return str(_planet(chart, name).get("dignity") or "neutral")


def _residents(chart: Dict[str, Any], house: int | None) -> list[str]:
    if not house:
        return []
    return [name for name in (*VISIBLE_PLANETS, "Rahu", "Ketu") if _house(chart, name) == house]


def _ascendant_sign(chart: Dict[str, Any]) -> int | None:
    try:
        return int(float(chart.get("ascendant")) // 30) % 12
    except (TypeError, ValueError):
        return None


def _house_sign(chart: Dict[str, Any], house: int) -> int | None:
    for row in chart.get("houses") or []:
        if not isinstance(row, dict):
            continue
        try:
            if int(row.get("house") or row.get("house_number")) == house:
                return int(row.get("sign")) % 12
        except (TypeError, ValueError):
            continue
    ascendant_sign = _ascendant_sign(chart)
    return ((ascendant_sign + house - 1) % 12) if ascendant_sign is not None else None


def _canonical_anatomy(values: Iterable[Any]) -> set[str]:
    """Resolve reader-facing body labels to stable anatomical concepts."""
    concepts: set[str] = set()
    known = {value for values in D30_HOUSE_ANATOMY.values() for value in values}
    for raw in values:
        text = re.sub(r"[^a-z]+", " ", str(raw or "").lower()).strip()
        if not text:
            continue
        for concept in known:
            if concept in text or text in concept:
                concepts.add(concept)
        for token, aliases in ANATOMY_ALIASES.items():
            if token in text:
                concepts.update(aliases)
    return concepts


class D30HealthConfirmationEngine:
    """Qualify D1 findings with D30 pressure and protection."""

    def __init__(self, d1: Dict[str, Any], d30: Dict[str, Any] | None):
        self.d1 = d1
        self.d30 = d30 or {}

    def calculate(self, vulnerabilities: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        if not (self.d30.get("planets") and self.d30.get("ascendant") is not None):
            return {
                "available": False,
                "role": "confirmation_only",
                "finding_confirmations": {},
                "intervention_markers": [],
                "pressure_factors": [],
                "protective_factors": [],
            }

        house_lord_links = self._house_lord_links()
        intervention = self._intervention_markers(house_lord_links)
        pressure, protection = self._chart_context()
        finding_confirmations = {}
        for finding in vulnerabilities:
            stable_id = str(finding.get("stable_id") or "")
            if stable_id:
                finding_confirmations[stable_id] = self._finding_confirmation(
                    finding, house_lord_links
                )

        if pressure and protection:
            overall = "pressure_with_protection"
        elif pressure:
            overall = "pressure_repeated"
        elif protection:
            overall = "protection_repeated"
        else:
            overall = "no_distinct_confirmation"
        return {
            "available": True,
            "role": "confirmation_only",
            "cannot_create_vulnerability": True,
            "cannot_create_timing": True,
            "overall": overall,
            "intervention_markers": intervention,
            "pressure_factors": pressure,
            "protective_factors": protection,
            "finding_confirmations": finding_confirmations,
            "house_lord_links": house_lord_links,
            "anatomy_source": MEDICAL_HOUSE_SOURCE,
            "node_policy": "Rahu and Ketu sharing a D30 house count as one nodal-axis pressure factor.",
        }

    def _house_lord_links(self) -> list[Dict[str, Any]]:
        """Describe every D30 house lord's destination without chart-specific rules."""
        links: list[Dict[str, Any]] = []
        for source_house in range(1, 13):
            source_sign = _house_sign(self.d30, source_house)
            lord = SIGN_LORDS.get(source_sign) if source_sign is not None else None
            destination_house = _house(self.d30, lord) if lord else None
            if not lord or not destination_house:
                continue
            source_anatomy = list(D30_HOUSE_ANATOMY[source_house])
            destination_anatomy = list(D30_HOUSE_ANATOMY[destination_house])
            links.append({
                "type": "d30_house_lord_anatomical_bridge",
                "source_house": source_house,
                "source_sign": source_sign,
                "planet": lord,
                "destination_house": destination_house,
                "source_anatomy": source_anatomy,
                "destination_anatomy": destination_anatomy,
                "pathology": list(PLANET_PATHOLOGY.get(lord, ())),
                "source": MEDICAL_HOUSE_SOURCE,
                "meaning": (
                    f"In D30, {lord}, lord of House {source_house}, occupies House {destination_house}. "
                    f"This connects the body areas {', '.join(source_anatomy[:3])} with "
                    f"{', '.join(destination_anatomy[:3])}."
                ),
            })
        return links

    def _intervention_markers(
        self, house_lord_links: Iterable[Dict[str, Any]]
    ) -> list[Dict[str, Any]]:
        markers: list[Dict[str, Any]] = []
        d1_mars, d30_mars = _house(self.d1, "Mars"), _house(self.d30, "Mars")
        if d1_mars in {8, 12} and d30_mars in {8, 12}:
            markers.append({
                "type": "mars_intervention_repetition",
                "planet": "Mars",
                "d1_house": d1_mars,
                "d30_house": d30_mars,
                "meaning": (
                    f"Mars repeats in House {d1_mars} in D1 and House {d30_mars} in D30, "
                    "strengthening an acute or intervention-oriented expression when timing independently activates it."
                ),
            })
        elif d30_mars in DUSTHANA:
            markers.append({
                "type": "d30_mars_dusthana",
                "planet": "Mars",
                "d30_house": d30_mars,
                "meaning": (
                    f"Mars occupies D30 House {d30_mars}, adding intervention pressure when an established D1 pattern is activated."
                ),
            })
        if d30_mars in {8, 12} and _house(self.d30, "Sun") == d30_mars:
            markers.append({
                "type": "sun_mars_intervention_confluence",
                "planets": ["Sun", "Mars"],
                "d30_house": d30_mars,
                "meaning": f"Sun and Mars join in D30 House {d30_mars}, reinforcing acute physical intervention pressure.",
            })
        for link in house_lord_links:
            if (
                link.get("planet") == "Mars"
                and int(link.get("source_house") or 0) in DUSTHANA
                and (
                    int(link.get("destination_house") or 0) in DUSTHANA
                    or _canonical_anatomy(link.get("destination_anatomy") or [])
                    & {"rectum", "anal canal", "anal orifice", "perineum"}
                )
            ):
                markers.append({
                    **link,
                    "type": "d30_mars_dusthana_lord_anatomical_bridge",
                    "meaning": (
                        f"In D30, Mars, lord of House {link['source_house']}, occupies "
                        f"House {link['destination_house']}. It connects the body areas "
                        f"{', '.join(link['source_anatomy'][:3])} with "
                        f"{', '.join(link['destination_anatomy'][:3])} and adds an inflammatory "
                        "or intervention-oriented expression when timing independently activates Mars."
                    ),
                })
        return list({row["meaning"]: row for row in markers}.values())

    def _chart_context(self) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
        pressure: list[Dict[str, Any]] = []
        protection: list[Dict[str, Any]] = []
        asc_sign = int(float(self.d30["ascendant"]) // 30) % 12
        lagna_lord = SIGN_LORDS.get(asc_sign)
        if lagna_lord:
            lord_house = _house(self.d30, lagna_lord)
            residents = set(_residents(self.d30, lord_house))
            if residents & NODES:
                pressure.append({
                    "type": "d30_lagna_lord_nodal_pressure",
                    "planet": lagna_lord,
                    "house": lord_house,
                    "meaning": f"D30 Lagna lord {lagna_lord} shares House {lord_house} with the nodal axis, increasing adversity pressure.",
                })
            if lord_house in DUSTHANA:
                pressure.append({
                    "type": "d30_lagna_lord_dusthana",
                    "planet": lagna_lord,
                    "house": lord_house,
                    "meaning": f"D30 Lagna lord {lagna_lord} occupies health-sensitive House {lord_house}.",
                })
            if _dignity(self.d30, lagna_lord) in SUPPORTIVE_DIGNITIES:
                protection.append({
                    "type": "d30_lagna_lord_dignity",
                    "planet": lagna_lord,
                    "house": lord_house,
                    "meaning": f"D30 Lagna lord {lagna_lord} retains {_dignity(self.d30, lagna_lord).replace('_', ' ')} support.",
                })
            if "Jupiter" in residents and _dignity(self.d30, "Jupiter") in SUPPORTIVE_DIGNITIES:
                protection.append({
                    "type": "d30_jupiter_protects_lagna_lord",
                    "planet": "Jupiter",
                    "house": lord_house,
                    "meaning": f"Jupiter joins the D30 Lagna lord in House {lord_house} with {_dignity(self.d30, 'Jupiter').replace('_', ' ')} strength, qualifying the pressure with protection.",
                })
        for planet in ("Jupiter", "Venus"):
            if _dignity(self.d30, planet) in SUPPORTIVE_DIGNITIES:
                protection.append({
                    "type": "d30_benefic_dignity",
                    "planet": planet,
                    "house": _house(self.d30, planet),
                    "meaning": f"{planet} has {_dignity(self.d30, planet).replace('_', ' ')} strength in D30, supporting resilience and recovery.",
                })
        return pressure, list({row["meaning"]: row for row in protection}.values())

    def _finding_confirmation(
        self,
        finding: Dict[str, Any],
        house_lord_links: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        pressure: list[Dict[str, Any]] = []
        protection: list[Dict[str, Any]] = []
        finding_anatomy = _canonical_anatomy([
            finding.get("label"),
            *(finding.get("body_zones") or []),
            *(finding.get("anatomical_members") or []),
            *(finding.get("mechanisms") or []),
        ])
        finding_planets = {
            str(value) for value in (
                finding.get("timing_planets") or finding.get("source_planets") or []
            ) if value
        }
        anatomical_links: list[Dict[str, Any]] = []
        for link in house_lord_links:
            source_match = finding_anatomy & _canonical_anatomy(link.get("source_anatomy") or [])
            destination_match = finding_anatomy & _canonical_anatomy(link.get("destination_anatomy") or [])
            if not (source_match or destination_match):
                continue
            # Every D30 necessarily has a lord for every house.  A placement is
            # finding-specific only when the same planet already carries the
            # D1 vulnerability, or when both ends independently repeat the
            # same anatomical field.  This prevents D30 from "confirming"
            # every possible body area in every chart.
            if link.get("planet") not in finding_planets and not (
                source_match and destination_match
            ):
                continue
            # If only the destination matches, retain the bridge only when a
            # health/adversity house carries its lord there.  Otherwise every
            # ordinary lordship sharing that destination would add noise.
            if (
                destination_match
                and not source_match
                and int(link.get("source_house") or 0) not in DUSTHANA
            ):
                continue
            anatomical_links.append({
                **link,
                "matched_source_anatomy": sorted(source_match),
                "matched_destination_anatomy": sorted(destination_match),
                "repeat_strength": "source_and_destination" if source_match and destination_match else "single_side",
            })
        for planet in dict.fromkeys(finding.get("timing_planets") or finding.get("source_planets") or []):
            house = _house(self.d30, str(planet))
            if not house:
                continue
            residents = set(_residents(self.d30, house)) - {str(planet)}
            if house in DUSTHANA:
                pressure.append({
                    "type": "d30_source_dusthana",
                    "planet": planet,
                    "house": house,
                    "meaning": f"{planet}, a carrier of this D1 finding, occupies D30 House {house}.",
                })
            if residents & NODES:
                pressure.append({
                    "type": "d30_source_nodal_pressure",
                    "planet": planet,
                    "house": house,
                    "meaning": f"{planet}, a carrier of this D1 finding, shares D30 House {house} with the nodal axis.",
                })
            dignity = _dignity(self.d30, str(planet))
            if dignity == "debilitated":
                pressure.append({
                    "type": "d30_source_debilitated",
                    "planet": planet,
                    "house": house,
                    "meaning": f"{planet}, a carrier of this D1 finding, is debilitated in D30.",
                })
            elif dignity in SUPPORTIVE_DIGNITIES:
                protection.append({
                    "type": "d30_source_dignity",
                    "planet": planet,
                    "house": house,
                    "meaning": f"{planet}, a carrier of this D1 finding, has {dignity.replace('_', ' ')} strength in D30.",
                })
            if "Jupiter" in residents and _dignity(self.d30, "Jupiter") in SUPPORTIVE_DIGNITIES:
                protection.append({
                    "type": "d30_jupiter_source_protection",
                    "planet": "Jupiter",
                    "protected_planet": planet,
                    "house": house,
                    "meaning": f"Strong Jupiter joins {planet} in D30 House {house}, adding protection to this vulnerability.",
                })
        if pressure and protection:
            status = "pressure_with_protection"
        elif pressure:
            status = "pressure_repeated"
        elif anatomical_links and protection:
            status = "anatomy_repeated_with_protection"
        elif anatomical_links:
            status = "anatomy_repeated"
        elif protection:
            status = "protection_repeated"
        else:
            status = "not_distinctly_repeated"
        return {
            "status": status,
            "anatomical_links": anatomical_links,
            "pressure_factors": pressure,
            "protective_factors": protection,
        }
