"""Canonical fact vocabulary for reviewed Deva Keralam rules.

Keys are intentionally narrow and machine-validatable.  Rule extraction may
not invent a nearby key: a key must match one of these definitions or pass
through an explicit reviewed alias in ``draft_compiler``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Pattern, Tuple


ONTOLOGY_VERSION = "deva-keralam-facts/1.3.0"
PLANETS: Tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
DASHA_LEVELS: Tuple[str, ...] = (
    "mahadasha", "antardasha", "pratyantardasha", "sookshma", "prana",
)


@dataclass(frozen=True)
class FactDefinition:
    family: str
    key_pattern: str
    value_type: str
    temporal_scope: str
    description: str

    @property
    def regex(self) -> Pattern[str]:
        return re.compile(self.key_pattern)


_planet = "(?:" + "|".join(PLANETS) + ")"
_dasha = "(?:" + "|".join(DASHA_LEVELS) + ")"

FACT_DEFINITIONS: Tuple[FactDefinition, ...] = (
    FactDefinition("ascendant", r"deva_keralam\.ascendant\.(?:longitude|degree_in_sign)", "number", "natal", "Sidereal Ascendant longitude and degree within its Rashi."),
    FactDefinition("ascendant", r"deva_keralam\.ascendant\.rashi\.(?:index|name|lord|modality)", "scalar", "natal", "Ascendant Rashi identity, lord and modality."),
    FactDefinition("ascendant", r"deva_keralam\.ascendant\.house", "integer", "natal", "Ascendant house, always House 1."),
    FactDefinition("ascendant", r"deva_keralam\.ascendant\.navamsa\.(?:index|name|lord|modality|parity)", "scalar", "natal", "Ascendant Navamsha identity, lord, modality and parity."),
    FactDefinition("nadiamsa", r"deva_keralam\.ascendant\.nadiamsa\.(?:ordinal|name|half|physical_division|sign_index|sign_name|sign_modality|distance_to_division_boundary_arcseconds|distance_to_half_boundary_arcseconds|precision_status|birth_time_precision_warning)", "scalar", "natal", "Source-versioned Ascendant Nadiamsa and precision facts."),
    FactDefinition("planet", rf"deva_keralam\.planet\.({_planet})\.(?:longitude|degree_in_sign|house)", "number", "natal", "Natal planetary longitude, degree within Rashi or whole-sign house."),
    FactDefinition("planet", rf"deva_keralam\.planet\.({_planet})\.rashi\.(?:index|name|lord|modality)", "scalar", "natal", "Natal planetary Rashi identity, dispositor and modality."),
    FactDefinition("planet", rf"deva_keralam\.planet\.({_planet})\.lordships", "integer_list", "natal", "Whole-sign houses ruled by the planet."),
    FactDefinition("house", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.rashi\.(?:index|name|modality)", "scalar", "natal", "Whole-sign Rashi and modality occupying a house."),
    FactDefinition("house", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.(?:lord|lord_house)", "scalar", "natal", "House lord and its natal placement."),
    FactDefinition("house", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.occupants", "text_list", "natal", "Planets occupying the whole-sign house."),
    FactDefinition("house", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.aspected_by_planets", "text_list", "natal", "Planets casting a directional Parashari aspect to the house."),
    FactDefinition("house_lord", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.(?:name|longitude|degree_in_sign|house|vargottama)", "scalar", "natal", "Generic house-lord identity, longitude, placement and Vargottama status."),
    FactDefinition("house_lord", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.rashi\.(?:index|name|lord|modality)", "scalar", "natal", "Generic house-lord Rashi facts."),
    FactDefinition("house_lord", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.navamsa\.(?:index|name|lord|modality|parity)", "scalar", "natal", "Generic house-lord Navamsha facts."),
    FactDefinition("house_lord", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.nadiamsa\.(?:ordinal|name|half|physical_division|sign_index|sign_name|sign_modality|distance_to_division_boundary_arcseconds|distance_to_half_boundary_arcseconds|precision_status|birth_time_precision_warning)", "scalar", "natal", "Source-versioned Nadiamsa facts projected from the planet ruling a house."),
    FactDefinition("house_lord_relation", rf"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.relationship\.(?:conjunction|aspect_to|aspected_by)\.({_planet})\.(?:present|numbers)", "scalar", "natal", "Explicit conjunction or directional aspect between a house lord and another planet."),
    FactDefinition("house_lord_relation", rf"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.relative_to\.({_planet})\.house", "integer", "natal", "House occupied by the house lord when counted from another planet."),
    FactDefinition("planet", rf"deva_keralam\.planet\.({_planet})\.navamsa\.(?:index|name|lord|modality|parity)", "scalar", "natal", "Planetary Navamsha identity, lord, modality and parity."),
    FactDefinition("planet", rf"deva_keralam\.planet\.({_planet})\.vargottama", "boolean", "natal", "Whether D1 Rashi and D9 Navamsha signs are identical."),
    FactDefinition("natural_nature", rf"deva_keralam\.planet\.({_planet})\.natural_nature\.(?:classification|phase|paksha|elongation)", "scalar", "natal", "Classical natural nature kept separate from functional lordship; Moon is phase-dependent."),
    FactDefinition("natural_nature", rf"deva_keralam\.planet\.({_planet})\.natural_nature\.(?:associates|benefic_associates|malefic_associates)", "text_list", "natal", "Mercury's source-qualified conjunction context for its classical natural nature."),
    FactDefinition("avastha", rf"deva_keralam\.planet\.({_planet})\.avastha\.(?:key|label)", "text", "natal", "Baladi Avastha from the existing canonical chart calculator."),
    FactDefinition("dignity", rf"deva_keralam\.planet\.({_planet})\.navamsa\.(?:dignity|lord_natural_nature)", "text", "natal", "Separate Navamsha sign dignity and natural nature of the Navamsha lord."),
    FactDefinition("planet_relation", rf"deva_keralam\.planet\.({_planet})\.(?:conjunct_planets|aspects_planets|aspected_by_planets)", "text_list", "natal", "Explicit lists of conjunction and directional aspect contacts."),
    FactDefinition("planet_relation", rf"deva_keralam\.planet\.({_planet})\.relative_to\.({_planet})\.house", "integer", "natal", "House occupied by the first planet when counted from the second planet."),
    FactDefinition("dispositor", rf"deva_keralam\.planet\.({_planet})\.dispositor\.(?:name|longitude|degree_in_sign|house|vargottama)", "scalar", "natal", "Rashi dispositor identity and natal placement."),
    FactDefinition("dispositor", rf"deva_keralam\.planet\.({_planet})\.dispositor\.rashi\.(?:index|name|lord|modality)", "scalar", "natal", "Rashi placement of the subject planet's dispositor."),
    FactDefinition("dispositor", rf"deva_keralam\.planet\.({_planet})\.dispositor\.navamsa\.(?:index|name|lord|modality|parity)", "scalar", "natal", "Navamsha placement of the subject planet's dispositor."),
    FactDefinition("dispositor", rf"deva_keralam\.planet\.({_planet})\.dispositor\.nadiamsa\.(?:ordinal|name|half|physical_division|sign_index|sign_name|sign_modality|distance_to_division_boundary_arcseconds|distance_to_half_boundary_arcseconds|precision_status|birth_time_precision_warning)", "scalar", "natal", "Nadiamsa placement of the subject planet's Rashi dispositor."),
    FactDefinition("dispositor_relation", rf"deva_keralam\.planet\.({_planet})\.dispositor\.relationship\.(?:conjunction|aspect_to|aspected_by)\.({_planet})\.(?:present|numbers)", "scalar", "natal", "Explicit conjunction or directional aspect between a dispositor and a target planet."),
    FactDefinition("nadiamsa", rf"deva_keralam\.planet\.({_planet})\.nadiamsa\.(?:ordinal|name|half|physical_division|sign_index|sign_name|sign_modality|distance_to_division_boundary_arcseconds|distance_to_half_boundary_arcseconds|precision_status|birth_time_precision_warning)", "scalar", "natal", "Source-versioned planetary Nadiamsa facts."),
    FactDefinition("dignity", rf"deva_keralam\.planet\.({_planet})\.dignity", "text", "natal", "Dignity emitted only by the existing canonical dignity calculator."),
    FactDefinition("house_nature", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.natural_(?:benefic|malefic)_(?:occupants|aspectors)", "text_list", "natal", "Separate natural-benefic and natural-malefic occupation/aspect lists; no aggregate influence score."),
    FactDefinition("house_lord_condition", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.(?:dignity|navamsa_dignity|navamsa_lord_natural_nature)", "text", "natal", "Separate Rashi dignity, Navamsha dignity and Navamsha-lord nature of a house lord."),
    FactDefinition("house_lord_condition", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.natural_nature\.classification", "text", "natal", "Classical natural nature of the house lord, separate from its dignity and Avastha."),
    FactDefinition("house_lord_condition", r"deva_keralam\.house\.(?:[1-9]|1[0-2])\.lord\.avastha\.(?:key|label)", "text", "natal", "Baladi Avastha of the house lord."),
    FactDefinition("conjunction", rf"deva_keralam\.relationship\.conjunction\.({_planet})\.({_planet})\.present", "boolean", "natal", "Same-Rashi planetary conjunction; pair names are canonicalized."),
    FactDefinition("aspect", rf"deva_keralam\.relationship\.aspect\.({_planet})\.({_planet})\.(?:present|numbers)", "scalar", "natal", "Directional whole-sign Parashari graha drishti."),
    FactDefinition("aspect", rf"deva_keralam\.relationship\.aspect\.({_planet})\.house\.(?:[1-9]|1[0-2])\.(?:present|numbers)", "scalar", "natal", "Directional whole-sign Parashari graha drishti to a natal house."),
    FactDefinition("relative_house", rf"deva_keralam\.relationship\.relative_house\.({_planet})\.({_planet})", "integer", "natal", "House occupied by the first planet when counted from the second planet."),
    FactDefinition("aspect", rf"deva_keralam\.planet\.({_planet})\.aspected_houses", "integer_list", "natal", "Natal houses receiving the planet's whole-sign graha drishti."),
    FactDefinition("precision", r"deva_keralam\.precision\.ascendant\.(?:status|longitude_uncertainty_arcseconds|reliable)", "scalar", "natal", "Birth-time precision governing Ascendant Nadiamsa use."),
    FactDefinition("dasha", rf"deva_keralam\.timing\.dasha\.({_dasha})\.(?:lord|ordinal|start|end|active)", "scalar", "timing", "Typed Vimshottari period supplied by the timing calculator contract."),
    FactDefinition("transit", rf"deva_keralam\.timing\.transit\.({_planet})\.(?:longitude|house|rashi_index|rashi_name|aspected_houses|conjunct_natal_planets|aspects_natal_planets|as_of)", "scalar", "timing", "Calculated transit placement and natal contacts."),
    FactDefinition("age", r"deva_keralam\.timing\.native\.age_years", "number", "timing", "Elapsed calendar age in mean tropical years at the requested date."),
    FactDefinition("age", r"deva_keralam\.timing\.native\.(?:completed_age_years|running_year_number|calendar_year)", "integer", "timing", "Typed calendar-age or civil-year value at the requested date."),
    FactDefinition("age", r"deva_keralam\.timing\.native\.(?:birth_date|as_of|completed_age_interval_start|completed_age_interval_end_exclusive|calendar_year_interval_start|calendar_year_interval_end_exclusive)", "text", "timing", "ISO civil-date boundary for explicit age and calendar-year evaluation."),
    FactDefinition("period", r"deva_keralam\.timing\.period\.[1-5]\.(?:system|level|name|lord|start|end_exclusive)", "text", "timing", "Caller-supplied source-neutral period identity and half-open date boundary."),
    FactDefinition("period", r"deva_keralam\.timing\.period\.[1-5]\.active", "boolean", "timing", "Validated active status for a source-neutral period at the supplied evaluation date."),
    FactDefinition("period_phase", r"deva_keralam\.timing\.period\.[1-5]\.(?:duration_days|elapsed_days|remaining_days|start_proximity_days|end_proximity_days|junction_tolerance_days)", "integer", "timing", "Deterministic period duration, offset, or caller-declared boundary window in civil days."),
    FactDefinition("period_phase", r"deva_keralam\.timing\.period\.[1-5]\.progress_fraction", "number", "timing", "Elapsed fraction of an active half-open source period."),
    FactDefinition("period_phase", r"deva_keralam\.timing\.period\.[1-5]\.(?:half|third|junction_boundary)", "text", "timing", "Deterministic fractional phase or nearest declared junction boundary."),
    FactDefinition("period_phase", r"deva_keralam\.timing\.period\.[1-5]\.(?:near_start|near_end|proximity_overlap|near_start_junction|near_end_junction|near_junction)", "boolean", "timing", "Boundary proximity calculated only with a caller-declared window or tolerance."),
)


def definition_for_key(key: str) -> Optional[FactDefinition]:
    value = str(key)
    for definition in FACT_DEFINITIONS:
        if definition.regex.fullmatch(value):
            return definition
    return None


def is_canonical_fact_key(key: str) -> bool:
    return definition_for_key(key) is not None


def ontology_manifest() -> dict:
    return {
        "version": ONTOLOGY_VERSION,
        "planets": list(PLANETS),
        "dasha_levels": list(DASHA_LEVELS),
        "families": [
            {
                "family": row.family,
                "key_pattern": row.key_pattern,
                "value_type": row.value_type,
                "temporal_scope": row.temporal_scope,
                "description": row.description,
            }
            for row in FACT_DEFINITIONS
        ],
    }
