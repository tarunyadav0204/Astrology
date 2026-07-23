from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence


EVENT_SIGNATURE_REGISTRY_VERSION = "1.1.0"


@dataclass(frozen=True)
class EventSignature:
    """A testable Parashari event combination, not a prose prediction."""

    key: str
    parent_family: str
    label: str
    required_relative_houses: Sequence[int]
    supporting_relative_houses: Sequence[int]
    minimum_supporting_houses: int
    conflict_relative_houses: Sequence[int]
    karakas: Sequence[str]
    required_varga: str
    manifestations: Sequence[str]
    priority: int
    eligibility_rule: str = "always"
    unknown_eligibility_label: str = ""
    safety_allowed: bool = True


EVENT_SIGNATURES: Dict[str, EventSignature] = {
    "promotion_authority": EventSignature(
        "promotion_authority", "career_authority", "career authority milestone",
        (10,), (2, 6, 11), 1, (8, 12), ("Sun", "Saturn", "Mercury"), "D10",
        ("greater responsibility", "recognition", "role or reporting-line change"), 10,
    ),
    "business_expansion": EventSignature(
        "business_expansion", "career_authority", "business expansion decision",
        (10,), (7, 2, 11), 1, (6, 8, 12), ("Mercury", "Jupiter"), "D10",
        ("new commercial responsibility", "business agreement", "expansion decision"), 20,
        eligibility_rule="business_owner",
        unknown_eligibility_label="professional expansion decision",
    ),
    "income_gain": EventSignature(
        "income_gain", "money_gains", "income or gains development",
        (2, 11), (5, 9), 1, (6, 8, 12), ("Jupiter", "Venus", "Mercury"), "D2",
        ("income movement", "gain or collection", "resource decision"), 10,
    ),
    "financial_pressure_or_obligation": EventSignature(
        "financial_pressure_or_obligation", "financial_pressure",
        "financial pressure or obligation",
        (2,), (6, 8, 12), 1, (11,), ("Saturn", "Mars", "Rahu", "Jupiter"), "D2",
        ("pressure on savings", "a family expense", "a debt or payment obligation"), 10,
    ),
    "relationship_commitment": EventSignature(
        "relationship_commitment", "partnership_commitment", "partnership commitment",
        (7,), (2, 5, 11), 1, (6, 8, 12), ("Venus", "Jupiter"), "D9",
        ("commitment discussion", "relationship decision", "formal agreement"), 10,
        eligibility_rule="relationship",
        unknown_eligibility_label="important partnership decision",
    ),
    "property_asset": EventSignature(
        "property_asset", "home_property", "property or home decision",
        (4,), (2, 11), 1, (6, 8, 12), ("Moon", "Mars", "Venus"), "D4",
        ("property decision", "home investment", "change in living arrangements"), 10,
    ),
    "child_development": EventSignature(
        "child_development", "children_education", "child-related development",
        (5,), (9, 11), 1, (6, 8, 12), ("Jupiter",), "D7",
        ("a child's milestone", "a responsibility involving children", "creative development"), 10,
        eligibility_rule="has_children",
        unknown_eligibility_label="children or creative-responsibility development",
    ),
    "education_milestone": EventSignature(
        "education_milestone", "children_education", "education milestone",
        (5,), (4, 9), 1, (6, 8, 12), ("Mercury", "Jupiter"), "D24",
        ("course or qualification decision", "learning milestone", "examination or study responsibility"), 20,
    ),
    "long_distance_movement": EventSignature(
        "long_distance_movement", "travel_change", "long-distance movement",
        (9, 12), (3,), 1, (6, 8), ("Jupiter", "Rahu", "Moon"), "D9",
        ("long-distance travel", "temporary relocation", "foreign or distant connection"), 10,
    ),
    "sixth_house_matter": EventSignature(
        "sixth_house_matter", "workload_health", "health, workload, debt or dispute matter",
        (6,), (1, 10), 1, (8, 12), ("Mars", "Saturn", "Sun"), "D10",
        (
            "a health or treatment matter",
            "heavier workload or service obligation",
            "a debt, repayment or dispute",
            "need to reorganize routines",
        ), 10,
    ),
    "eighth_house_shared_resources": EventSignature(
        "eighth_house_shared_resources", "shared_resources_change",
        "shared resources or consequential change",
        (8,), (2, 7, 11), 1, (6, 12), ("Saturn", "Mars", "Rahu", "Jupiter"), "D9",
        (
            "a shared-finance or joint-resource matter",
            "an obligation involving a partner",
            "a consequential change requiring adjustment",
        ), 10,
    ),
    "family_financial_duty": EventSignature(
        "family_financial_duty", "family_responsibility", "family financial responsibility",
        (2, 4), (9,), 1, (6, 8, 12), ("Moon", "Jupiter", "Saturn"), "D12",
        ("shared family expense", "support for a family member", "home-related responsibility"), 10,
    ),
    "consequential_decision": EventSignature(
        "consequential_decision", "decision_communication", "consequential decision",
        (3, 5), (9, 10), 1, (6, 8, 12), ("Mercury", "Jupiter"), "D9",
        ("important negotiation", "document or agreement", "decision with longer-term consequences"), 10,
    ),
}


def signatures_for_family(family: str) -> Sequence[EventSignature]:
    return tuple(
        signature
        for signature in EVENT_SIGNATURES.values()
        if signature.parent_family == family and signature.safety_allowed
    )
