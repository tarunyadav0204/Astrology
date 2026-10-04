"""Reviewed vocabulary used by the professional natal-health blueprint.

The registry classifies deterministic anatomical evidence.  It does not infer
clinical diagnoses.  A named condition is emitted only by an authored
condition rule from the shared health evidence calculator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DiseaseFamily:
    stable_id: str
    label: str
    system: str
    zone_terms: tuple[str, ...]
    description: str


DISEASE_FAMILIES: tuple[DiseaseFamily, ...] = (
    DiseaseFamily(
        "health.family.cardiovascular",
        "Cardiovascular and circulatory vulnerability",
        "cardiovascular",
        ("heart", "blood", "circulation", "vascular", "blood pressure"),
        "The repeated body-area pattern concerns the heart, vascular tone and circulation.",
    ),
    DiseaseFamily(
        "health.family.respiratory",
        "Respiratory vulnerability",
        "respiratory",
        ("lungs", "respiratory", "breath", "chest", "sinus"),
        "The repeated body-area pattern concerns breathing passages, lungs or chest regulation.",
    ),
    DiseaseFamily(
        "health.family.digestive",
        "Digestive and intestinal vulnerability",
        "digestive",
        ("stomach", "digestion", "digestive", "intestines", "abdomen", "gut"),
        "The repeated body-area pattern concerns digestion, stomach or intestinal regulation.",
    ),
    DiseaseFamily(
        "health.family.hepatic_metabolic",
        "Hepatic and metabolic vulnerability",
        "hepatic_metabolic",
        ("liver", "metabolic", "blood sugar", "pancreatic", "fat", "growth"),
        "The repeated field concerns liver, growth, metabolic or blood-sugar regulation.",
    ),
    DiseaseFamily(
        "health.family.renal_urinary",
        "Renal and urinary vulnerability",
        "renal_urinary",
        ("kidney", "renal", "urinary", "excretory"),
        "The repeated body-area pattern concerns kidney, urinary or excretory regulation.",
    ),
    DiseaseFamily(
        "health.family.reproductive_hormonal",
        "Reproductive and hormonal vulnerability",
        "reproductive_hormonal",
        ("reproductive", "hormonal", "hormone", "private parts", "pelvis", "groin"),
        "The repeated body-area pattern concerns reproductive, pelvic or hormonal regulation.",
    ),
    DiseaseFamily(
        "health.family.musculoskeletal",
        "Musculoskeletal vulnerability",
        "musculoskeletal",
        ("bone", "joint", "spine", "back", "knee", "teeth", "muscle", "shoulder"),
        "The repeated body-area pattern concerns bones, joints, spine, muscles or supporting structure.",
    ),
    DiseaseFamily(
        "health.family.neurological",
        "Neurological and nervous-system vulnerability",
        "neurological",
        ("brain", "nerve", "nervous", "mind", "speech", "communication"),
        "The repeated body-area pattern concerns nerves, neurological regulation or mental processing.",
    ),
    DiseaseFamily(
        "health.family.skin_allergic",
        "Skin and allergic vulnerability",
        "skin_allergic",
        ("skin", "allergic", "toxin", "nails", "hair"),
        "The repeated body-area pattern concerns skin, allergic or toxic reactivity.",
    ),
    DiseaseFamily(
        "health.family.sleep_emotional",
        "Sleep and emotional-regulation vulnerability",
        "sleep_emotional",
        ("sleep", "emotional", "mind", "recovery sleep"),
        "The repeated field concerns sleep, emotional regulation or psychological strain.",
    ),
    DiseaseFamily(
        "health.family.injury_inflammatory",
        "Injury and inflammatory vulnerability",
        "injury_inflammatory",
        ("injury", "accident", "inflammation", "blood", "muscles", "surgery"),
        "The repeated field concerns acute injury, heat, inflammation or procedural themes.",
    ),
    DiseaseFamily(
        "health.family.sensory",
        "Eye, ear and sensory vulnerability",
        "sensory",
        ("eye", "vision", "ear", "hearing"),
        "The repeated body-area pattern concerns sight, hearing or the sensory organs.",
    ),
    DiseaseFamily(
        "health.family.endocrine_ent",
        "Throat and glandular vulnerability",
        "endocrine_ent",
        ("throat", "neck", "thyroid", "glandular"),
        "The repeated body-area pattern concerns the throat, neck or glandular regulation.",
    ),
    DiseaseFamily(
        "health.family.immune_lymphatic",
        "Immune and lymphatic vulnerability",
        "immune_lymphatic",
        ("immunity", "lymph", "recovery capacity"),
        "The repeated body-area pattern concerns immunity, lymph or recovery capacity.",
    ),
    DiseaseFamily(
        "health.family.oral_dental",
        "Oral and dental vulnerability",
        "oral_dental",
        ("mouth", "teeth", "dental", "gums", "jaw"),
        "The repeated body-area pattern concerns the mouth, teeth, gums or jaw.",
    ),
)


CONDITION_PATTERN_KEYS = frozenset({
    "vascular_pressure_tone",
    "mental_emotional_regulation_susceptibility",
    "metabolic_blood_sugar_susceptibility",
    "sinus_face_throat_susceptibility",
    "cardiac_surgery_susceptibility",
    "reproductive_hormonal_cycle_susceptibility",
    "renal_urinary_susceptibility",
    "breast_fluid_regulation_susceptibility",
    "respiratory_susceptibility",
    "digestive_intestinal_susceptibility",
    "hepatic_metabolic_susceptibility",
    "musculoskeletal_susceptibility",
    "neurological_regulation_susceptibility",
    "skin_allergic_susceptibility",
    "sleep_regulation_susceptibility",
    "blood_inflammatory_susceptibility",
    "vision_eye_susceptibility",
    "throat_glandular_susceptibility",
    "immune_lymphatic_susceptibility",
    "oral_dental_susceptibility",
    "hearing_ear_susceptibility",
})


def classify_zones(values: Iterable[str]) -> list[DiseaseFamily]:
    """Return families matched by explicit anatomical terms, preserving order."""
    text = " ".join(str(value or "").strip().lower() for value in values)
    return [family for family in DISEASE_FAMILIES if any(term in text for term in family.zone_terms)]
