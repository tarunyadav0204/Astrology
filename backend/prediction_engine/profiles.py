from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

from .errors import PredictionConfigurationError


@dataclass(frozen=True)
class AstrologyConventions:
    ayanamsha: str
    zodiac: str
    house_system: str
    node_model: str
    node_aspects: Sequence[int]
    dasha_system: str
    father_anchor_house: int
    transit_reference_frames: Sequence[str]
    daily_transit_time_utc: str


@dataclass(frozen=True)
class PredictionProfile:
    key: str
    version: str
    provider_ids: Sequence[str]
    provider_versions: Sequence[Tuple[str, str]]
    event_families: Sequence[str]
    default_horizon_days: int
    minimum_independent_confirmations: int
    require_transit_for_strong: bool
    maximum_candidates: int
    maximum_per_subject: int
    maximum_per_timing_signature: int
    event_family_priority: Sequence[str]
    safety_policy_version: str
    blocked_event_families: Sequence[str]
    require_event_resolution: bool
    conventions: AstrologyConventions


PROFILES: Dict[str, PredictionProfile] = {
    "parashari_fomo_v1": PredictionProfile(
        key="parashari_fomo_v1",
        version="3.1.0",
        provider_ids=(
            "dasha_house_activation",
            "dasha_planet_relationship",
            "dispositor_activation",
            "transit_house",
            "transit_natal_relation",
            "planet_condition",
            "functional_nature",
            "friendship",
            "benefic_malefic_association",
            "conflict_house",
            "badhaka",
            "yogi_avayogi",
            "gandanta",
            "dagdha_tithi",
        ),
        provider_versions=(
            ("dasha_house_activation", "1.0.0"),
            ("dasha_planet_relationship", "1.0.0"),
            ("dispositor_activation", "1.0.0"),
            ("transit_house", "1.0.0"),
            ("transit_natal_relation", "1.0.0"),
            ("planet_condition", "1.1.0"),
            ("functional_nature", "1.0.0"),
            ("friendship", "1.2.0"),
            ("benefic_malefic_association", "1.0.0"),
            ("conflict_house", "1.0.0"),
            ("badhaka", "1.0.0"),
            ("yogi_avayogi", "1.0.0"),
            ("gandanta", "1.1.0"),
            ("dagdha_tithi", "1.0.0"),
        ),
        event_families=tuple(
            (
                "career_authority",
                "money_gains",
                "financial_pressure",
                "partnership_commitment",
                "home_property",
                "children_education",
                "travel_change",
                "workload_health",
                "shared_resources_change",
                "family_responsibility",
                "decision_communication",
            )
        ),
        default_horizon_days=90,
        minimum_independent_confirmations=2,
        require_transit_for_strong=True,
        maximum_candidates=8,
        maximum_per_subject=2,
        maximum_per_timing_signature=2,
        event_family_priority=(
            "career_authority",
            "decision_communication",
            "home_property",
            "money_gains",
            "financial_pressure",
            "partnership_commitment",
            "family_responsibility",
            "travel_change",
            "children_education",
            "workload_health",
            "shared_resources_change",
        ),
        safety_policy_version="fomo_safety.v1",
        blocked_event_families=(),
        require_event_resolution=True,
        conventions=AstrologyConventions(
            ayanamsha="Lahiri (Swiss Ephemeris SIDM_LAHIRI)",
            zodiac="sidereal",
            house_system="whole_sign",
            node_model="mean_node",
            node_aspects=(7,),
            dasha_system="Vimshottari MD-AD-PD",
            father_anchor_house=9,
            transit_reference_frames=("natal_lagna",),
            daily_transit_time_utc="12:00",
        ),
    )
}


def get_profile(key: str) -> PredictionProfile:
    profile = PROFILES.get(key)
    if profile is None:
        raise PredictionConfigurationError(f"Unknown prediction profile: {key}")
    return profile
