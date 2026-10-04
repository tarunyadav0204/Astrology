"""Deterministic natal vulnerability engine for professional Health V2."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, Iterable

from reports.context.health_body_zones import compute_health_body_zone_map

from .constitutional_strength_engine import ConstitutionalStrengthEngine
from .divisional_confirmation_engine import D30HealthConfirmationEngine
from .medical_karaka_engine import calculate_medical_karaka_patterns, calculate_menstrual_cycle_assessment
from .registry import CONDITION_PATTERN_KEYS, classify_zones


ENGINE_VERSION = "health-natal-blueprint/2.7.0-preview"
METHODOLOGY_VERSION = "natal-first-confluence/1.6.0"
SIGN_LORDS = {
    0: "Mars", 1: "Venus", 2: "Mercury", 3: "Moon", 4: "Sun", 5: "Mercury",
    6: "Venus", 7: "Mars", 8: "Jupiter", 9: "Saturn", 10: "Saturn", 11: "Jupiter",
}


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _evidence_grade(confidence: Any, confluence_count: Any) -> str:
    count = int(confluence_count or 0)
    value = str(confidence or "").lower()
    if value == "high" and count >= 3:
        return "strong"
    if value in {"high", "medium"} and count >= 1:
        return "moderate"
    return "directional"


def _without_disputed_node_aspects(chart: Dict[str, Any]) -> Dict[str, Any]:
    """Use a conservative Health V2 aspect policy for the lunar nodes.

    Node occupation and conjunction remain in the chart.  Only Rahu/Ketu
    entries in the precomputed graha-drishti map are removed, preventing a
    school-specific 5th/9th aspect from becoming universal health evidence.
    """
    value = deepcopy(chart)
    drishti = value.get("graha_drishti_by_house")
    if isinstance(drishti, dict):
        value["graha_drishti_by_house"] = {
            house: [
                row for row in rows
                if not isinstance(row, dict) or row.get("planet") not in {"Rahu", "Ketu"}
            ]
            for house, rows in drishti.items()
            if isinstance(rows, list)
        }
    return value


class NatalHealthBlueprintEngine:
    """Build a natal-only health blueprint without using current timing.

    The shared body-zone calculator supplies house/sign/nakshatra anatomy and
    legacy authored patterns.  The medical-karaka engine adds independently
    gated organ-system rules.  This layer groups both into stable families and
    exposes a strict contract for the future timing engine.
    """

    def __init__(
        self,
        chart: Dict[str, Any],
        divisional_charts: Dict[str, Dict[str, Any]] | None = None,
        gender: str | None = None,
    ):
        if not isinstance(chart, dict) or not chart.get("planets") or len(chart.get("houses") or []) < 12:
            raise ValueError("A complete D1 chart with planets and twelve houses is required")
        self.chart = _without_disputed_node_aspects(chart)
        self.divisional_charts = divisional_charts or {}
        self.gender = str(gender or "").strip()

    def calculate(self) -> Dict[str, Any]:
        constitutional = ConstitutionalStrengthEngine(self.chart, self.divisional_charts).calculate()
        planet_conditions = constitutional.get("planet_conditions") or {}
        raw = compute_health_body_zone_map(
            self.chart,
            current_dashas=None,
            divisional_charts=self.divisional_charts,
            planet_conditions=planet_conditions,
            requested_category="constitutional",
        )
        medical_profile = raw.get("medical_profile") or {}
        anatomy = self._anatomical_vulnerabilities(
            raw.get("major_vulnerabilities") or [],
            raw.get("sixth_house_chain") or {},
            planet_conditions,
        )
        karaka_patterns = calculate_medical_karaka_patterns(self.chart, raw, planet_conditions, self.gender)
        menstrual_cycle = calculate_menstrual_cycle_assessment(
            self.chart, raw, planet_conditions, self.gender
        )
        condition_patterns = list(raw.get("event_patterns") or []) + karaka_patterns
        conditions = self._condition_vulnerabilities(condition_patterns, planet_conditions)
        vulnerabilities = self._merge_vulnerabilities(anatomy + conditions)
        d30_confirmation = D30HealthConfirmationEngine(
            self.chart, self.divisional_charts.get("D30")
        ).calculate(vulnerabilities)
        for vulnerability in vulnerabilities:
            vulnerability["d30_confirmation"] = (
                d30_confirmation.get("finding_confirmations", {}).get(vulnerability["stable_id"])
                or {"status": "unavailable", "pressure_factors": [], "protective_factors": []}
            )
        resilience = constitutional.get("overall_resilience") or {}
        for vulnerability in vulnerabilities:
            vulnerability["constitutional_modifier"] = {
                "status": resilience.get("status"),
                "meaning": "modifies manifestation severity and recovery; does not erase the natal susceptibility",
                "protected_pillars": resilience.get("protected_pillars", 0),
                "pressured_pillars": resilience.get("pressured_pillars", 0),
                "jupiter_quality": resilience.get("jupiter_quality"),
            }

        eligible = [row["stable_id"] for row in vulnerabilities if row["eligible_for_timing"]]
        return {
            "schema_version": "health.natal_blueprint.v2",
            "engine_version": ENGINE_VERSION,
            "methodology_version": METHODOLOGY_VERSION,
            "status": "preview",
            "legacy_health_unchanged": True,
            "scope": "natal_vulnerability_only",
            "claim_policy": {
                "clinical_diagnosis": False,
                "timing_used": False,
                "timing_cannot_create_vulnerability": True,
                "named_condition_requires_authored_rule": True,
                "system_finding_requires_anatomical_anchor": True,
                "single_karaka_can_create_finding": False,
                "nodes_can_create_finding": False,
                "dignity_changes_capacity_not_polarity": True,
                "protection_cannot_erase_vulnerability": True,
                "special_lunar_factors_are_secondary_only": True,
                "rahu_ketu_special_aspects_used": False,
                "female_specific_analysis_requires_profile_gender": True,
                "d30_confirmation_only": True,
            },
            "vitality_foundation": self._vitality_foundation(medical_profile),
            "constitutional_protection": constitutional,
            "planet_health_contexts": planet_conditions,
            "female_health": {
                "menstrual_cycle": menstrual_cycle,
            } if menstrual_cycle else None,
            "sixth_house_chain": raw.get("sixth_house_chain") or {},
            "vulnerabilities": vulnerabilities,
            "divisional_health_confirmation": {"D30": d30_confirmation},
            "eligible_vulnerability_ids": eligible,
            "protective_factors": list(dict.fromkeys(
                _list(medical_profile.get("protective_factors"))
                + _list(constitutional.get("protective_factors"))
            )),
            "constitutional_pressure_factors": _list(constitutional.get("pressure_factors")),
            "technical": {
                "house_map": raw.get("house_map") or [],
                "priority_zones": raw.get("priority_zones") or [],
                "raw_condition_patterns": [
                    row for row in condition_patterns
                    if str(row.get("key") or "") in CONDITION_PATTERN_KEYS
                ],
            },
            "limitations": [
                "This preview describes classical astrological susceptibility, not a medical diagnosis.",
                "Dasha and transit timing are intentionally excluded from the natal blueprint.",
                "D30 qualifies severity, intervention pressure and recovery support; it cannot introduce a new body area, condition or timing period.",
            ],
        }

    def _vitality_foundation(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        constitution = profile.get("constitution") or {}
        core_houses = _list(constitution.get("core_houses"))
        return {
            "ascendant_sign": constitution.get("ascendant_sign"),
            "ascendant_lord": constitution.get("ascendant_lord"),
            "ascendant_lord_house": constitution.get("ascendant_lord_house"),
            "sun_house": constitution.get("sun_house"),
            "moon_house": constitution.get("moon_house"),
            "core_houses": core_houses,
            "note": "This is the structural foundation; it is not converted into a generic health score.",
        }

    def _anatomical_vulnerabilities(
        self,
        rows: Iterable[Dict[str, Any]],
        sixth_house_chain: Dict[str, Any],
        planet_conditions: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        for row in rows:
            zone_values = [row.get("zone"), *_list(row.get("anatomical_members")), *_list(row.get("mechanisms"))]
            families = classify_zones(zone_values)
            zone = str(row.get("zone") or "").strip()
            if not zone:
                continue
            systems = list(dict.fromkeys(family.system for family in families))
            family_labels = list(dict.fromkeys(family.label for family in families))
            grade = _evidence_grade(row.get("confidence"), row.get("confluence_count"))
            slug = re.sub(r"[^a-z0-9]+", "_", zone.lower()).strip("_") or "unspecified"
            primary_factors = set(_list(row.get("primary_medical_factors")))
            source_planets = [str(sixth_house_chain.get("sixth_lord") or "").strip()]
            if "sixth_lord_nakshatra" in primary_factors:
                source_planets.append(str(sixth_house_chain.get("sixth_lord_nakshatra_lord") or "").strip())
            source_planets = list(dict.fromkeys(planet for planet in source_planets if planet))
            delivery = [
                self._planet_delivery_context(planet, planet_conditions.get(planet) or {})
                for planet in source_planets if planet_conditions.get(planet)
            ]
            qualifiers = self._finding_qualifiers(delivery)
            results.append({
                "stable_id": f"health.anatomy.{slug}",
                "label": f"{zone[:1].upper() + zone[1:]} may need extra care",
                "system": systems[0] if len(systems) == 1 else "multi_system",
                "possible_systems": systems,
                "possible_family_labels": family_labels,
                "claim_type": "anatomical_vulnerability",
                "description": (
                    f"Several sixth-house body-area indicators point to {zone}. "
                    "This shows an area that may need care; it does not indicate a specific disease."
                ),
                "body_zones": [zone],
                "mechanisms": _list(row.get("mechanisms")),
                "supporting_rules": list(dict.fromkeys(
                    str(reason) for reason in _list(row.get("primary_medical_reasons")) + _list(row.get("why")) if reason
                )),
                "protective_rules": qualifiers["support"],
                "contradicting_rules": qualifiers["pressure"],
                "capacity_modifiers": qualifiers["capacity"],
                "delivery_balance": qualifiers["balance"],
                "source_pattern_ids": [],
                # Preserve the anatomical provenance produced by the shared
                # body-zone engine.  Timing needs this to distinguish, for
                # example, Capricorn in H6 (knees) from the sixth lord's sign
                # or nakshatra (different body areas).
                "primary_medical_factors": list(primary_factors),
                "confluence_count": int(row.get("confluence_count") or 0),
                "standing_weight": int(row.get("standing_weight") or 0),
                "source_planets": source_planets,
                "timing_planets": source_planets,
                "timing_houses": [6],
                "planetary_delivery": delivery,
                "evidence_grade": grade,
                "support_grade": grade,
                "eligible_for_timing": grade in {"moderate", "strong"},
                "birth_time_sensitivity": "requires_review",
            })
        return results

    def _condition_vulnerabilities(
        self,
        patterns: Iterable[Dict[str, Any]],
        planet_conditions: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        results: list[Dict[str, Any]] = []
        for row in patterns:
            key = str(row.get("key") or "")
            if key not in CONDITION_PATTERN_KEYS:
                continue
            evidence = [str(value) for value in _list(row.get("evidence")) if value]
            evidence.extend(
                f"Source: {value}"
                for value in _list(row.get("source_references"))
                if value
            )
            # Authored condition patterns already enforce their own multi-factor
            # threshold.  Preserve the exact evidence rather than re-scoring it.
            grade = "strong" if str(row.get("risk_level") or "").lower() == "elevated" else "moderate"
            source_planets = _list(row.get("contributing_planets"))
            if not source_planets:
                evidence_text = " ".join(evidence)
                source_planets = [planet for planet in planet_conditions if planet in evidence_text]
            delivery = _list(row.get("planetary_delivery")) or [
                self._planet_delivery_context(planet, planet_conditions.get(planet) or {})
                for planet in source_planets if planet_conditions.get(planet)
            ]
            qualifiers = self._finding_qualifiers(delivery)
            results.append({
                "stable_id": f"health.condition.{key}",
                "label": row.get("title") or key.replace("_", " ").title(),
                "system": self._condition_system(key),
                "claim_type": "named_classical_susceptibility",
                "description": row.get("summary"),
                "body_zones": _list(row.get("zones")),
                "mechanisms": [],
                "supporting_rules": evidence,
                "protective_rules": qualifiers["support"],
                "contradicting_rules": qualifiers["pressure"],
                "capacity_modifiers": qualifiers["capacity"],
                "delivery_balance": qualifiers["balance"],
                "source_pattern_ids": [key],
                "source_planets": source_planets,
                "timing_planets": _list(row.get("timing_planets")) or self._condition_timing_planets(key),
                "timing_houses": _list(row.get("timing_houses")) or self._condition_timing_houses(key),
                "planetary_delivery": delivery,
                "evidence_grade": grade,
                "support_grade": grade,
                "eligible_for_timing": True,
                "birth_time_sensitivity": "requires_review",
                "responsible_guidance": row.get("user_framing"),
            })
        return results

    @staticmethod
    def _planet_delivery_context(planet: str, condition: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "planet": planet,
            "house": condition.get("house"),
            "dignity": condition.get("dignity"),
            "sign_relationship": condition.get("sign_relationship"),
            "nakshatra_context": condition.get("nakshatra_context"),
            "delivery_quality": condition.get("delivery_quality"),
            "affliction_details": _list(condition.get("affliction_details")),
            "functional_role": condition.get("functional_role"),
            "natural_nature": condition.get("natural_nature"),
            "vargottama_d1_d9": condition.get("vargottama_d1_d9"),
            "divisional_strength": condition.get("divisional_strength"),
            "special_roles": _list(condition.get("special_roles")),
            "finding_modifiers": condition.get("finding_modifiers") or {},
        }

    @staticmethod
    def _finding_qualifiers(contexts: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        support: list[Dict[str, Any]] = []
        pressure: list[Dict[str, Any]] = []
        capacity: list[Dict[str, Any]] = []
        for context in contexts:
            modifiers = context.get("finding_modifiers") or {}
            support.extend(_list(modifiers.get("support")))
            pressure.extend(_list(modifiers.get("pressure")))
            capacity.extend(_list(modifiers.get("capacity")))
        if support and pressure:
            balance = "support_and_pressure"
        elif support:
            balance = "supportive"
        elif pressure:
            balance = "pressured"
        else:
            balance = "unqualified"
        return {"support": support, "pressure": pressure, "capacity": capacity, "balance": balance}

    @staticmethod
    def _condition_system(key: str) -> str:
        return {
            "vascular_pressure_tone": "cardiovascular",
            "mental_emotional_regulation_susceptibility": "sleep_emotional",
            "metabolic_blood_sugar_susceptibility": "hepatic_metabolic",
            "sinus_face_throat_susceptibility": "respiratory",
            "cardiac_surgery_susceptibility": "cardiovascular",
            "reproductive_hormonal_cycle_susceptibility": "reproductive_hormonal",
            "renal_urinary_susceptibility": "renal_urinary",
            "breast_fluid_regulation_susceptibility": "reproductive_hormonal",
            "respiratory_susceptibility": "respiratory",
            "digestive_intestinal_susceptibility": "digestive",
            "hepatic_metabolic_susceptibility": "hepatic_metabolic",
            "musculoskeletal_susceptibility": "musculoskeletal",
            "neurological_regulation_susceptibility": "neurological",
            "skin_allergic_susceptibility": "skin_allergic",
            "sleep_regulation_susceptibility": "sleep_emotional",
            "blood_inflammatory_susceptibility": "injury_inflammatory",
            "vision_eye_susceptibility": "sensory",
            "throat_glandular_susceptibility": "endocrine_ent",
            "immune_lymphatic_susceptibility": "immune_lymphatic",
            "oral_dental_susceptibility": "oral_dental",
            "hearing_ear_susceptibility": "sensory",
        }.get(key, "general")

    @staticmethod
    def _condition_timing_houses(key: str) -> list[int]:
        """Primary houses allowed to time an authored health pattern.

        These are condition anchors, not every house mentioned in supporting
        evidence. A corroborating placement must not become timing permission.
        """
        return {
            "cardiac_surgery_susceptibility": [4, 5, 8, 12],
            "vascular_pressure_tone": [4, 5, 6],
            "mental_emotional_regulation_susceptibility": [4, 5, 12],
            "metabolic_blood_sugar_susceptibility": [2, 6],
            "sinus_face_throat_susceptibility": [2],
            "accident_injury_susceptibility": [1, 6, 8],
            "surgery_crisis_susceptibility": [6, 8, 12],
            "twelfth_feet_rest_hospitalization": [12],
        }.get(key, [])

    def _house_lord(self, house: int) -> str | None:
        row = next(
            (value for value in (self.chart.get("houses") or []) if int(value.get("house") or 0) == house),
            None,
        )
        try:
            return SIGN_LORDS.get(int(row.get("sign")) % 12) if row else None
        except (TypeError, ValueError):
            return None

    def _condition_timing_planets(self, key: str) -> list[str]:
        """Planets that carry the condition, excluding incidental evidence actors."""
        base, houses = {
            "cardiac_surgery_susceptibility": (["Sun", "Mars"], [4, 5]),
            "vascular_pressure_tone": (["Sun", "Mars"], [4, 5]),
            "mental_emotional_regulation_susceptibility": (["Moon", "Mercury"], [4, 5]),
            "metabolic_blood_sugar_susceptibility": (["Jupiter", "Venus", "Moon"], [2, 6]),
            "sinus_face_throat_susceptibility": (["Mercury"], [2]),
            "accident_injury_susceptibility": (["Mars", "Rahu"], [6]),
            "surgery_crisis_susceptibility": (["Mars"], [6, 8, 12]),
            "twelfth_feet_rest_hospitalization": (["Saturn"], [12]),
        }.get(key, ([], []))
        return list(dict.fromkeys(
            list(base) + [lord for house in houses if (lord := self._house_lord(house))]
        ))

    @staticmethod
    def _merge_vulnerabilities(rows: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        # Named authored patterns stay separate from broad anatomical families.
        # Stable ordering makes chart-to-chart comparison and regression tests reliable.
        order = {"strong": 0, "moderate": 1, "directional": 2}
        return sorted(
            rows,
            key=lambda row: (
                order.get(str(row.get("evidence_grade") or row.get("support_grade")), 9),
                0 if row.get("claim_type") == "named_classical_susceptibility" else 1,
                str(row.get("stable_id")),
            ),
        )
