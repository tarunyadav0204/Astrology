"""Authored medical-karaka confluence rules for the professional health screen.

These rules describe natal susceptibility fields.  A planet association alone
never creates a finding: every emitted pattern requires a pressured primary
karaka, a matching anatomical field, and either an illness-axis link or an
independent corroborating karaka.  The lunar nodes may corroborate pressure but
may not create a finding by themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


MALEFICS = frozenset({"Mars", "Saturn", "Rahu", "Ketu"})
DUSTHANA = frozenset({6, 8, 12})
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}


@dataclass(frozen=True)
class MedicalSystemRule:
    key: str
    title: str
    system: str
    primary_karakas: tuple[str, ...]
    supporting_karakas: tuple[str, ...]
    houses: tuple[int, ...]
    signs: tuple[int, ...]
    zone_terms: tuple[str, ...]
    zones: tuple[str, ...]
    summary: str
    source_note: str


# The registry is deliberately complete at the organ-system level.  Specific
# diseases require separate authored rules and must not be inferred from these
# broad susceptibility patterns.
MEDICAL_SYSTEM_RULES: tuple[MedicalSystemRule, ...] = (
    MedicalSystemRule(
        "reproductive_hormonal_cycle_susceptibility",
        "Reproductive and hormonal-cycle sensitivity",
        "reproductive_hormonal",
        ("Venus", "Moon"), ("Mars",), (7, 8), (6, 7),
        ("reproductive", "pelvis", "groin", "private parts", "hormone"),
        ("reproductive system", "pelvic region", "hormonal cycle"),
        "The reproductive and hormonal field receives repeated pressure. For a person who menstruates, this can include cycle regularity; it does not identify a particular disorder.",
        "K. S. Charak, Essentials of Medical Astrology — Moon–Mars menstrual-cycle and Venus reproductive/endocrine rule families",
    ),
    MedicalSystemRule(
        "renal_urinary_susceptibility", "Kidney and urinary sensitivity", "renal_urinary",
        ("Venus",), ("Moon", "Saturn"), (7, 8), (6, 7),
        ("kidney", "renal", "urinary", "excretory", "lower back"),
        ("kidneys", "urinary system", "fluid balance"),
        "The kidney, urinary and fluid-balance field receives repeated pressure. This is a preventive-attention theme, not a kidney diagnosis.",
        "K. S. Charak, Essentials of Medical Astrology — Venus, kidney and urinary-system rule family",
    ),
    MedicalSystemRule(
        "breast_fluid_regulation_susceptibility", "Breast and fluid-regulation sensitivity", "reproductive_hormonal",
        ("Moon",), ("Venus", "Mars"), (4,), (3,),
        ("breast", "chest", "fluid"), ("breasts", "chest", "body fluids"),
        "The breast, chest and body-fluid field receives repeated pressure. This does not identify a lump, infection or other medical condition.",
        "K. S. Charak, Essentials of Medical Astrology — Moon, breast, milk and bodily-fluid rule family",
    ),
    MedicalSystemRule(
        "respiratory_susceptibility", "Breathing and lung sensitivity", "respiratory",
        ("Mercury",), ("Moon", "Saturn"), (3, 4), (2, 3),
        ("lung", "breath", "respiratory", "chest"), ("lungs", "breathing passages", "chest"),
        "The breathing and lung field receives repeated pressure. It can show a tendency toward respiratory sensitivity without naming a disease.",
        "Classical medical-astrology correspondence — Mercury, House 3, Gemini and the respiratory field",
    ),
    MedicalSystemRule(
        "digestive_intestinal_susceptibility", "Digestive and intestinal sensitivity", "digestive",
        ("Moon", "Mercury"), ("Mars", "Jupiter"), (4, 5, 6), (3, 5),
        ("stomach", "digest", "intestin", "abdomen", "gut"), ("stomach", "digestion", "intestines"),
        "The stomach, digestion and intestinal field receives repeated pressure. This is a broad digestive tendency, not a named illness.",
        "Classical medical-astrology correspondence — Moon/Mercury and the stomach–intestinal field",
    ),
    MedicalSystemRule(
        "hepatic_metabolic_susceptibility", "Liver and metabolic sensitivity", "hepatic_metabolic",
        ("Jupiter",), ("Venus", "Moon"), (5, 6, 9), (8,),
        ("liver", "metabolic", "fat", "growth"), ("liver", "metabolic regulation", "fat metabolism"),
        "The liver and metabolic field receives repeated pressure. It does not establish fatty liver, diabetes or another diagnosis.",
        "K. S. Charak, Essentials of Medical Astrology — Jupiter, liver, fat and growth rule family",
    ),
    MedicalSystemRule(
        "musculoskeletal_susceptibility", "Bone, joint and structural sensitivity", "musculoskeletal",
        ("Saturn",), ("Mars", "Sun"), (1, 10), (9,),
        ("bone", "joint", "knee", "teeth", "spine", "back"), ("bones", "joints", "knees", "spine", "teeth"),
        "The bones, joints or supporting structure receive repeated pressure. This can describe a constitutional weak area without predicting a specific condition.",
        "K. S. Charak, Essentials of Medical Astrology — Saturn, bones, joints, teeth and chronicity rule family",
    ),
    MedicalSystemRule(
        "neurological_regulation_susceptibility", "Nerve and neurological sensitivity", "neurological",
        ("Mercury",), ("Saturn", "Moon"), (1, 3, 6), (2, 5),
        ("nerve", "brain", "speech", "nervous"), ("nerves", "brain", "neurological regulation"),
        "The nervous-system field receives repeated pressure. This does not identify a neurological disease.",
        "Classical medical-astrology correspondence — Mercury, nerves and neurological coordination, modified by Saturn and the nodes",
    ),
    MedicalSystemRule(
        "skin_allergic_susceptibility", "Skin and reactive sensitivity", "skin_allergic",
        ("Mercury", "Venus"), ("Saturn",), (6,), (5, 6),
        ("skin", "allerg", "toxin", "hair", "nail"), ("skin", "reactive sensitivity", "hair and nails"),
        "The skin and reactive field receives repeated pressure. This is a tendency toward sensitivity and does not name an allergy or skin disease.",
        "Classical medical-astrology correspondence — Mercury/Venus, skin and the Virgo–Libra field",
    ),
    MedicalSystemRule(
        "sleep_regulation_susceptibility", "Sleep and recovery sensitivity", "sleep_emotional",
        ("Moon",), ("Saturn",), (4, 12), (11,),
        ("sleep", "rest", "recovery"), ("sleep", "rest", "recovery rhythm"),
        "The sleep and recovery field receives repeated pressure. It can show uneven rest or recovery without diagnosing a sleep disorder.",
        "Classical medical-astrology correspondence — Moon, House 12 and sleep/recovery",
    ),
    MedicalSystemRule(
        "blood_inflammatory_susceptibility", "Blood and inflammatory sensitivity", "injury_inflammatory",
        ("Mars",), ("Sun", "Moon"), (1, 6, 8), (0,),
        ("blood", "inflamm", "muscle", "injury"), ("blood", "inflammatory response", "muscles"),
        "The blood, heat and inflammatory field receives repeated pressure. It does not establish infection, bleeding or another medical condition.",
        "Classical medical-astrology correspondence — Mars, blood, heat, inflammation and acute injury",
    ),
    MedicalSystemRule(
        "vision_eye_susceptibility", "Eye and vision sensitivity", "sensory",
        ("Sun", "Moon"), ("Venus",), (2, 12), (0, 1, 4),
        ("eye", "vision", "face"), ("eyes", "vision"),
        "The eye and vision field receives repeated pressure. It does not identify an eye disease or loss of sight.",
        "K. S. Charak, Essentials of Medical Astrology — Sun, Moon and Venus as eye/vision significators",
    ),
    MedicalSystemRule(
        "throat_glandular_susceptibility", "Throat and glandular sensitivity", "endocrine_ent",
        ("Venus", "Mercury"), ("Moon",), (2,), (1,),
        ("throat", "neck", "thyroid", "gland"), ("throat", "neck", "glandular regulation"),
        "The throat, neck and glandular field receives repeated pressure. It does not establish a thyroid or throat condition.",
        "Classical medical-astrology correspondence — Taurus/House 2 throat field with Venus and Mercury",
    ),
    MedicalSystemRule(
        "immune_lymphatic_susceptibility", "Immunity and lymphatic sensitivity", "immune_lymphatic",
        ("Jupiter", "Moon"), ("Sun",), (1, 6, 12), (3, 8, 11),
        ("immunity", "lymph", "fluid"), ("immunity", "lymphatic flow", "recovery capacity"),
        "The immunity, lymph and recovery field receives repeated pressure. It does not identify an immune or lymphatic illness.",
        "Classical medical-astrology correspondence — Jupiter/Moon vitality and the House 6–12 immunity, fluid and recovery field",
    ),
    MedicalSystemRule(
        "oral_dental_susceptibility", "Mouth, teeth and dental sensitivity", "oral_dental",
        ("Saturn", "Mercury"), ("Mars",), (2,), (1, 9),
        ("mouth", "teeth", "dental", "gum", "jaw"), ("mouth", "teeth", "gums and jaw"),
        "The mouth, teeth and jaw field receives repeated pressure. It does not identify a dental condition.",
        "Classical medical-astrology correspondence — House 2 mouth/teeth field with Saturn as the hard-tissue significator",
    ),
    MedicalSystemRule(
        "hearing_ear_susceptibility", "Ear and hearing sensitivity", "sensory",
        ("Mercury", "Saturn"), ("Jupiter",), (3, 11), (2, 10),
        ("ear", "hearing"), ("ears", "hearing"),
        "The ear and hearing field receives repeated pressure. It does not identify a hearing disorder or hearing loss.",
        "Classical medical-astrology correspondence — Houses 3 and 11 for the ears, with Mercury/Saturn sensory and nerve support",
    ),
)


def _planet_house(chart: dict[str, Any], planet: str) -> int | None:
    try:
        return int((chart.get("planets") or {}).get(planet, {}).get("house"))
    except (TypeError, ValueError):
        return None


def _planet_sign(chart: dict[str, Any], planet: str) -> int | None:
    try:
        return int((chart.get("planets") or {}).get(planet, {}).get("sign")) % 12
    except (TypeError, ValueError):
        return None


def _house_sign(chart: dict[str, Any], house: int) -> int | None:
    for row in chart.get("houses") or []:
        if int(row.get("house") or 0) == house:
            try:
                return int(row.get("sign")) % 12
            except (TypeError, ValueError):
                return None
    return None


def _lord(chart: dict[str, Any], house: int) -> str | None:
    sign = _house_sign(chart, house)
    return SIGN_LORDS.get(sign) if sign is not None else None


class MedicalKarakaEngine:
    def __init__(
        self,
        chart: dict[str, Any],
        raw_health_map: dict[str, Any],
        planet_conditions: dict[str, Any] | None = None,
        gender: str | None = None,
    ):
        self.chart = chart
        self.raw = raw_health_map
        self.planet_conditions = planet_conditions or {}
        self.gender = str(gender or "").strip().lower()
        self.house_rows = {
            int(row.get("house")): row
            for row in raw_health_map.get("house_map") or []
            if row.get("house")
        }
        self.residents: dict[int, list[str]] = {}
        for planet in (chart.get("planets") or {}):
            house = _planet_house(chart, planet)
            if house:
                self.residents.setdefault(house, []).append(planet)

    def calculate(self) -> list[dict[str, Any]]:
        return [pattern for rule in MEDICAL_SYSTEM_RULES if (pattern := self._evaluate(rule))]

    def _planet_delivery(self, planet: str) -> dict[str, Any] | None:
        condition = self.planet_conditions.get(planet) or {}
        if not condition:
            return None
        return {
            "planet": planet,
            "house": condition.get("house"),
            "dignity": condition.get("dignity"),
            "sign_relationship": condition.get("sign_relationship"),
            "nakshatra_context": condition.get("nakshatra_context"),
            "delivery_quality": condition.get("delivery_quality"),
            "affliction_details": list(condition.get("affliction_details") or []),
            "functional_role": condition.get("functional_role"),
            "natural_nature": condition.get("natural_nature"),
            "vargottama_d1_d9": condition.get("vargottama_d1_d9"),
            "divisional_strength": condition.get("divisional_strength"),
            "special_roles": list(condition.get("special_roles") or []),
            "finding_modifiers": condition.get("finding_modifiers") or {},
        }

    def _combined_modifiers(self, planets: Iterable[str]) -> dict[str, Any]:
        support: list[dict[str, Any]] = []
        pressure: list[dict[str, Any]] = []
        capacity: list[dict[str, Any]] = []
        delivery: list[dict[str, Any]] = []
        for planet in planets:
            context = self._planet_delivery(planet)
            if not context:
                continue
            delivery.append(context)
            modifiers = context.get("finding_modifiers") or {}
            support.extend(modifiers.get("support") or [])
            pressure.extend(modifiers.get("pressure") or [])
            capacity.extend(modifiers.get("capacity") or [])
        return {"delivery": delivery, "support": support, "pressure": pressure, "capacity": capacity}

    def menstrual_cycle_assessment(self) -> dict[str, Any] | None:
        """Assess menstrual-cycle susceptibility for a chart marked female.

        This is kept separate from the broad reproductive-system rule because
        menstruation needs its own confluence: the Moon (cycle and fluids),
        Mars (blood and flow), Venus (female reproductive function), and the
        reproductive anatomy represented by House 8/Scorpio.  No single one
        of these factors is allowed to create a finding.
        """
        if self.gender not in {"female", "f", "woman", "girl"}:
            return None

        moon_pressure = self._planet_pressure("Moon")
        mars_pressure = self._planet_pressure("Mars")
        venus_pressure = self._planet_pressure("Venus")
        moon_house = _planet_house(self.chart, "Moon")
        mars_house = _planet_house(self.chart, "Mars")

        moon_mars_link: list[str] = []
        if moon_house and moon_house == mars_house:
            moon_mars_link.append(f"Moon and Mars are joined in House {moon_house}")
        if moon_house and "Mars" in (self.house_rows.get(moon_house, {}).get("aspecting_planets") or []):
            moon_mars_link.append("Mars aspects the Moon")
        if mars_house and "Moon" in (self.house_rows.get(mars_house, {}).get("aspecting_planets") or []):
            moon_mars_link.append("Moon aspects Mars")

        reproductive_rule = next(
            rule for rule in MEDICAL_SYSTEM_RULES
            if rule.key == "reproductive_hormonal_cycle_susceptibility"
        )
        anatomy = self._anatomy_evidence(reproductive_rule)
        # Occupation of the menstrual/reproductive field is itself an
        # anatomical connection.  The shared anatomy helper intentionally
        # excludes primary karakas to prevent double-counting in broad system
        # findings, but that policy made a Venus–Mars conjunction in H8
        # disappear from this dedicated assessment.
        for planet in ("Moon", "Mars", "Venus"):
            house = _planet_house(self.chart, planet)
            sign = _planet_sign(self.chart, planet)
            if house == 8:
                anatomy.append(f"{planet} occupies House 8, the menstrual and reproductive field")
            if sign == 7:
                anatomy.append(f"{planet} occupies Scorpio, the reproductive and eliminative field")
        anatomy = list(dict.fromkeys(anatomy))
        illness_axis = self._illness_axis_evidence(reproductive_rule)

        factor_groups = {
            "moon_cycle": bool(moon_pressure),
            "mars_blood_flow": bool(mars_pressure or moon_mars_link),
            "venus_reproductive": bool(venus_pressure),
            "reproductive_anatomy": bool(anatomy),
            "illness_axis": bool(illness_axis),
        }
        repeated_domains = sum(factor_groups.values())
        secondary_support = sum(
            factor_groups[key]
            for key in ("mars_blood_flow", "venus_reproductive", "illness_axis")
        )
        if factor_groups["moon_cycle"] and factor_groups["reproductive_anatomy"] and secondary_support >= 2:
            status = "heightened_attention"
            summary = (
                "Several independent chart factors repeat menstrual-cycle sensitivity. "
                "This can show less regular, heavier, more painful or otherwise changeable periods, "
                "but the chart cannot identify which symptom or diagnose its cause."
            )
        elif (
            repeated_domains >= 3
            and factor_groups["reproductive_anatomy"]
            and (factor_groups["moon_cycle"] or factor_groups["venus_reproductive"])
        ):
            status = "some_sensitivity"
            summary = (
                "The chart shows some menstrual-cycle sensitivity, but the full repeated pattern is not strong. "
                "Periods may respond more noticeably to strain, sleep, routine or hormonal changes."
            )
        else:
            status = "no_distinct_pattern"
            summary = (
                "The menstrual factors do not form a clear combined vulnerability in this birth chart. "
                "This does not rule out ordinary or medical menstrual concerns."
            )

        evidence = list(dict.fromkeys(
            [f"Moon: {line}" for line in moon_pressure]
            + [f"Moon–Mars connection: {line}" for line in moon_mars_link]
            + [f"Mars: {line}" for line in mars_pressure]
            + [f"Venus: {line}" for line in venus_pressure]
            + anatomy
            + illness_axis
        ))
        modifiers = self._combined_modifiers(("Moon", "Mars", "Venus"))
        return {
            "analyzed": True,
            "status": status,
            "summary": summary,
            "factor_groups": factor_groups,
            "active_factor_groups": [key for key, active in factor_groups.items() if active],
            "planetary_delivery": modifiers["delivery"],
            "protective_rules": modifiers["support"],
            "pressure_rules": modifiers["pressure"],
            "capacity_modifiers": modifiers["capacity"],
            "evidence": evidence[:10],
            "source_references": [
                "K. S. Charak, Essentials of Medical Astrology — Moon–Mars menstrual-cycle and Venus reproductive-function rule families (edition and page not encoded)"
            ],
            "responsible_guidance": (
                "This is a constitutional sensitivity assessment, not a diagnosis. Persistent pain, unusually "
                "heavy bleeding, missed periods or a marked change in the cycle needs qualified medical care."
            ),
            "rule_version": "female-menstrual-confluence/1.0.0",
        }

    def _planet_pressure(self, planet: str) -> list[str]:
        house = _planet_house(self.chart, planet)
        if not house:
            return []
        company = [p for p in self.residents.get(house, []) if p != planet and p in MALEFICS]
        aspectors = [
            p for p in (self.house_rows.get(house, {}).get("aspecting_planets") or [])
            if p != planet and p in MALEFICS
        ]
        evidence: list[str] = []
        if company:
            evidence.append(f"{planet} is joined by {', '.join(company)} in House {house}")
        if aspectors:
            evidence.append(f"{planet} receives pressure from {', '.join(aspectors)}")
        if house in DUSTHANA:
            evidence.append(f"{planet} occupies health-sensitive House {house}")
        return evidence

    def _direct_house_pressure(self, house: int, excluded: Iterable[str] = ()) -> list[str]:
        row = self.house_rows.get(house, {})
        excluded_set = set(excluded)
        actors = list(dict.fromkeys(
            [p for p in row.get("residents") or [] if p in MALEFICS and p not in excluded_set]
            + [p for p in row.get("aspecting_planets") or [] if p in MALEFICS and p not in excluded_set]
        ))
        return [f"House {house} receives pressure from {', '.join(actors)}"] if actors else []

    def _anatomy_evidence(self, rule: MedicalSystemRule) -> list[str]:
        evidence: list[str] = []
        for house in rule.houses:
            # A pressured house lord can be the same planet already counted as
            # the primary karaka.  Use only direct, independent pressure here.
            pressure = self._direct_house_pressure(house, rule.primary_karakas)
            if pressure:
                evidence.append(f"Anatomical house: {pressure[0]}")
        for sign in rule.signs:
            sign_house = next((h for h in range(1, 13) if _house_sign(self.chart, h) == sign), None)
            if sign_house:
                pressure = self._direct_house_pressure(sign_house, rule.primary_karakas)
                if pressure:
                    evidence.append(f"{SIGN_NAMES[sign]} anatomical field: {pressure[0]}")
        chain = self.raw.get("sixth_house_chain") or {}
        chain_zones = " ".join(
            str(value).lower()
            for key, value in chain.items()
            if key.endswith("_zones")
            for value in (value if isinstance(value, list) else [])
        )
        matched = [term for term in rule.zone_terms if term in chain_zones]
        if matched:
            evidence.append(f"House 6 anatomical chain repeats {', '.join(matched[:3])}")
        return list(dict.fromkeys(evidence))

    def _illness_axis_evidence(self, rule: MedicalSystemRule) -> list[str]:
        evidence: list[str] = []
        illness_lords = {lord for h in DUSTHANA if (lord := _lord(self.chart, h))}
        for planet in rule.primary_karakas + rule.supporting_karakas:
            house = _planet_house(self.chart, planet)
            if house in DUSTHANA:
                evidence.append(f"{planet} connects the system directly with House {house}")
            company = set(self.residents.get(house or 0, [])) - {planet}
            linked_lords = sorted(company & illness_lords)
            if linked_lords:
                evidence.append(f"{planet} is joined by illness-axis lord {', '.join(linked_lords)}")
        for house in rule.houses:
            lord = _lord(self.chart, house)
            lord_house = _planet_house(self.chart, lord) if lord else None
            if lord and lord_house in DUSTHANA:
                evidence.append(f"House {house} lord {lord} occupies health-sensitive House {lord_house}")
        return list(dict.fromkeys(evidence))

    def _evaluate(self, rule: MedicalSystemRule) -> dict[str, Any] | None:
        primary: list[str] = []
        pressured_primary: list[str] = []
        for planet in rule.primary_karakas:
            pressure = self._planet_pressure(planet)
            if pressure:
                pressured_primary.append(planet)
                primary.append(f"Primary significator: {pressure[0]}")
        if not pressured_primary:
            return None

        anatomy = self._anatomy_evidence(rule)
        if not anatomy:
            return None

        corroboration: list[str] = []
        pressured_supporting: list[str] = []
        for planet in rule.supporting_karakas:
            pressure = self._planet_pressure(planet)
            if pressure:
                pressured_supporting.append(planet)
                corroboration.append(f"Independent corroboration: {pressure[0]}")
        illness_axis = self._illness_axis_evidence(rule)
        if not illness_axis and not corroboration:
            return None
        primary_has_independent_pressure = any(
            "health-sensitive House" not in line for line in primary
        )
        # The same dusthana placement cannot count once as karaka pressure and
        # again as illness-axis permission.  It needs a separate corroborator.
        if not primary_has_independent_pressure and not corroboration:
            return None

        factor_classes = ["primary_karaka", "anatomical_field"]
        if illness_axis:
            factor_classes.append("illness_axis")
        if corroboration:
            factor_classes.append("corroborating_karaka")
        evidence = list(dict.fromkeys(primary + anatomy + illness_axis + corroboration))
        contributing_planets = list(dict.fromkeys(pressured_primary + pressured_supporting))
        planetary_delivery = [
            context for planet in contributing_planets
            if (context := self._planet_delivery(planet))
        ]
        return {
            "key": rule.key,
            "title": rule.title,
            "system": rule.system,
            "summary": rule.summary,
            "zones": list(rule.zones),
            "evidence": evidence[:8],
            "factor_classes": factor_classes,
            "contributing_planets": contributing_planets,
            "timing_planets": contributing_planets,
            "timing_houses": list(rule.houses),
            "planetary_delivery": planetary_delivery,
            "risk_level": "elevated" if len(factor_classes) == 4 else "moderate",
            "user_framing": "Use this as a reason for sensible prevention and timely medical assessment when symptoms exist, not as a diagnosis.",
            "source_references": [f"{rule.source_note} (edition and page not encoded)"],
            "rule_version": "medical-karaka-confluence/1.1.0",
        }


def calculate_medical_karaka_patterns(
    chart: dict[str, Any],
    raw_health_map: dict[str, Any],
    planet_conditions: dict[str, Any] | None = None,
    gender: str | None = None,
) -> list[dict[str, Any]]:
    return MedicalKarakaEngine(chart, raw_health_map, planet_conditions, gender).calculate()


def calculate_menstrual_cycle_assessment(
    chart: dict[str, Any],
    raw_health_map: dict[str, Any],
    planet_conditions: dict[str, Any] | None = None,
    gender: str | None = None,
) -> dict[str, Any] | None:
    return MedicalKarakaEngine(chart, raw_health_map, planet_conditions, gender).menstrual_cycle_assessment()
