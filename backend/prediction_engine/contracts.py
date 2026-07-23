from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence

from .errors import PredictionInputError


SCHEMA_VERSION = "prediction_engine.v17"


class EvidenceStatus(str, Enum):
    EVALUATED = "evaluated"
    NOT_APPLICABLE = "not_applicable"
    NOT_AVAILABLE = "not_available"
    CALCULATION_ERROR = "calculation_error"


class Polarity(str, Enum):
    SUPPORTIVE = "supportive"
    CHALLENGING = "challenging"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class Importance(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    CONFIRMATORY = "confirmatory"


class ActivationBand(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    INSUFFICIENT = "insufficient"


class HouseActivationState(str, Enum):
    """Source-aware state of a native house in one timing window.

    A transit can make a house conspicuous without proving a promised event.
    Keeping that state distinct prevents transit occupation from being silently
    promoted into a prediction.
    """

    DORMANT = "dormant"
    TRANSIT_ONLY = "transit_only"
    DASHA_CONNECTED = "dasha_connected"
    DASHA_TRANSIT_ACTIVATED = "dasha_transit_activated"
    FULLY_REINFORCED = "fully_reinforced"


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNCONFIRMED = "unconfirmed"
    INELIGIBLE = "ineligible"


class ResolutionSpecificity(str, Enum):
    NONE = "none"
    CORE = "core_event"
    CORROBORATED = "corroborated_event"


@dataclass(frozen=True)
class LifeContext:
    """Explicit real-life facts used only to rule manifestations in or out.

    Unknown values are intentional.  The prediction engine must never infer
    these fields from a chart or silently replace them with defaults.
    """

    relationship_status: str = "unknown"
    employment_status: str = "unknown"
    business_owner: Optional[bool] = None
    property_owner: Optional[bool] = None
    has_children: Optional[bool] = None
    education_status: str = "unknown"


@dataclass(frozen=True)
class BirthChartInput:
    date: str
    time: str
    latitude: float
    longitude: float
    timezone: Any
    name: str = ""
    place: str = ""
    gender: str = ""
    birth_chart_id: Optional[int] = None

    @classmethod
    def from_mapping(cls, value: Dict[str, Any]) -> "BirthChartInput":
        required = ("date", "time", "latitude", "longitude", "timezone")
        missing = [key for key in required if value.get(key) in (None, "")]
        if missing:
            raise PredictionInputError(
                f"Birth chart input is missing required fields: {', '.join(missing)}"
            )
        try:
            latitude = float(value["latitude"])
            longitude = float(value["longitude"])
        except (TypeError, ValueError) as exc:
            raise PredictionInputError("Birth latitude/longitude must be numeric") from exc
        if not -90.0 <= latitude <= 90.0 or not -180.0 <= longitude <= 180.0:
            raise PredictionInputError("Birth latitude/longitude is outside the valid range")
        return cls(
            date=str(value["date"]).split("T")[0],
            time=str(value["time"]),
            latitude=latitude,
            longitude=longitude,
            timezone=value["timezone"],
            name=str(value.get("name") or ""),
            place=str(value.get("place") or ""),
            gender=str(value.get("gender") or ""),
            birth_chart_id=(
                int(value.get("birth_chart_id") or value.get("id"))
                if value.get("birth_chart_id") is not None or value.get("id") is not None
                else None
            ),
        )

    def to_calculator_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PredictionRequest:
    birth: BirthChartInput
    as_of: date
    horizon_days: int = 90
    profile: str = "parashari_fomo_v1"
    subjects: Sequence[str] = ("self", "mother", "father", "spouse")
    domains: Optional[Sequence[str]] = None
    maximum_candidates: int = 10
    trace: bool = False
    life_context: Optional[LifeContext] = None
    exploration_mode: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.horizon_days <= 366:
            raise PredictionInputError("horizon_days must be between 1 and 366")
        if not 1 <= self.maximum_candidates <= 100:
            raise PredictionInputError("maximum_candidates must be between 1 and 100")
        if not self.subjects:
            raise PredictionInputError("At least one subject is required")


@dataclass(frozen=True)
class PredictionWindow:
    start_date: str
    end_date: str
    mahadasha: str
    antardasha: str
    pratyantardasha: str
    transit_signature: str


@dataclass(frozen=True)
class Evidence:
    provider: str
    provider_version: str
    rule_id: str
    status: EvidenceStatus
    subject: str
    domain: str
    window_start: str
    window_end: str
    planet: Optional[str]
    house: Optional[int]
    importance: Importance
    polarity: Polarity
    facts: Dict[str, Any] = field(default_factory=dict)
    independent_key: str = ""

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["importance"] = self.importance.value
        value["polarity"] = self.polarity.value
        return value


@dataclass(frozen=True)
class ActivationAssessment:
    band: ActivationBand
    independent_confirmations: int
    active_dasha_levels: Sequence[str]
    transit_reinforced: bool
    natal_position_reinforced: bool
    primary_houses_covered: Sequence[int]
    carrier_planets: Sequence[str]
    rule_id: str


@dataclass(frozen=True)
class OutcomeAssessment:
    tone: Polarity
    supportive_factors: int
    challenging_factors: int
    rule_id: str
    mixed_factors: int = 0
    supportive_reasons: Sequence[Dict[str, Any]] = field(default_factory=tuple)
    challenging_reasons: Sequence[Dict[str, Any]] = field(default_factory=tuple)
    mixed_reasons: Sequence[Dict[str, Any]] = field(default_factory=tuple)


@dataclass(frozen=True)
class DashaRelationship:
    first_level: str
    first_planet: str
    second_level: str
    second_planet: str
    relations: Sequence[str]
    natal_houses: Sequence[int]


@dataclass(frozen=True)
class HouseActivation:
    house: int
    window: PredictionWindow
    state: HouseActivationState
    activation: ActivationAssessment
    outcome: OutcomeAssessment
    house_lord: str
    natal_connections: Sequence[Dict[str, Any]]
    transit_connections: Sequence[Dict[str, Any]]
    dasha_relationships: Sequence[DashaRelationship]
    trigger_planets: Sequence[str]
    timing_triggers: Sequence[Dict[str, Any]]
    evidence: Sequence[Evidence]

    def to_dict(self, *, include_evidence: bool = True) -> Dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        value["activation"]["band"] = self.activation.band.value
        value["outcome"]["tone"] = self.outcome.tone.value
        value["evidence"] = (
            [item.to_dict() for item in self.evidence] if include_evidence else []
        )
        return value


@dataclass(frozen=True)
class DivisionalConfirmation:
    chart: str
    confirmed: bool
    carrier_planets: Sequence[str]
    houses: Sequence[int]
    relations: Sequence[str]
    rule_id: str


@dataclass(frozen=True)
class InterpretationAlternative:
    subject: str
    domain: str
    event_family: str
    signature_key: Optional[str]
    label: str
    native_houses: Sequence[int]
    relative_houses: Sequence[int]
    focus_native_houses: Sequence[int]
    focus_relative_houses: Sequence[int]
    carrier_planets: Sequence[str]
    manifestations: Sequence[str]
    tone: Polarity
    supportive_factors: int
    challenging_factors: int
    tone_interpretation: str
    outcome_rule_id: str


@dataclass(frozen=True)
class EventResolution:
    status: ResolutionStatus
    specificity: ResolutionSpecificity
    signature_key: Optional[str]
    label: str
    manifestations: Sequence[str]
    alternative_signature_keys: Sequence[str]
    interpretation_alternatives: Sequence[InterpretationAlternative]
    required_houses_covered: Sequence[int]
    supporting_houses_covered: Sequence[int]
    missing_required_houses: Sequence[int]
    carrier_planets: Sequence[str]
    dasha_levels: Sequence[str]
    transit_reinforced: bool
    karaka_confirmed: bool
    divisional_confirmations: Sequence[DivisionalConfirmation]
    eligibility_reasons: Sequence[str]
    conflict_houses_activated: Sequence[int]
    rule_id: str


@dataclass(frozen=True)
class PredictionCandidate:
    candidate_id: str
    subject: str
    domain: str
    event_family: str
    native_houses: Sequence[int]
    window: PredictionWindow
    activation: ActivationAssessment
    outcome: OutcomeAssessment
    evidence: Sequence[Evidence]
    resolution: Optional[EventResolution] = None

    def to_dict(self, *, include_evidence: bool = True) -> Dict[str, Any]:
        value = asdict(self)
        value["activation"]["band"] = self.activation.band.value
        value["outcome"]["tone"] = self.outcome.tone.value
        if self.resolution is not None:
            value["resolution"]["status"] = self.resolution.status.value
            value["resolution"]["specificity"] = self.resolution.specificity.value
            for alternative in value["resolution"]["interpretation_alternatives"]:
                alternative["tone"] = alternative["tone"].value
        value["evidence"] = (
            [item.to_dict() for item in self.evidence] if include_evidence else []
        )
        return value


@dataclass(frozen=True)
class ManifestationHouseRole:
    native_house: int
    relative_house: int
    role: str
    activation_state: HouseActivationState
    activation_band: ActivationBand
    outcome_tone: Polarity
    direct_carriers: Sequence[str]
    dasha_connections: Sequence[str]
    transit_connections: Sequence[str]

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["activation_state"] = self.activation_state.value
        value["activation_band"] = self.activation_band.value
        value["outcome_tone"] = self.outcome_tone.value
        return value


@dataclass(frozen=True)
class ChartManifestation:
    manifestation_id: str
    signature_key: str
    subject: str
    domain: str
    label: str
    window: PredictionWindow
    house_roles: Sequence[ManifestationHouseRole]
    subject_confirmation: Dict[str, Any]
    carrier_planets: Sequence[str]
    carrier_coherence: str
    carrier_relationships: Sequence[Dict[str, Any]]
    activation_band: ActivationBand
    outcome_tone: Polarity
    synthesis_strength: str
    summary: str
    possibilities: Sequence[str]
    helpful_reasons: Sequence[Dict[str, Any]]
    pressure_reasons: Sequence[Dict[str, Any]]
    mixed_reasons: Sequence[Dict[str, Any]]
    rationale: Sequence[str]
    rule_id: str

    def to_dict(self) -> Dict[str, Any]:
        value = asdict(self)
        value["activation_band"] = self.activation_band.value
        value["outcome_tone"] = self.outcome_tone.value
        value["house_roles"] = [row.to_dict() for row in self.house_roles]
        return value


@dataclass(frozen=True)
class PredictionResult:
    engine_version: str
    schema_version: str
    profile: str
    profile_version: str
    as_of: str
    horizon_end: str
    evidence_signature: str
    candidates: Sequence[PredictionCandidate]
    house_activations: Sequence[HouseActivation] = ()
    chart_manifestations: Sequence[ChartManifestation] = ()
    natal_promises: Sequence[Dict[str, Any]] = ()
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self, *, include_evidence: bool = True) -> Dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "schema_version": self.schema_version,
            "profile": self.profile,
            "profile_version": self.profile_version,
            "as_of": self.as_of,
            "horizon_end": self.horizon_end,
            "evidence_signature": self.evidence_signature,
            "candidates": [
                candidate.to_dict(include_evidence=include_evidence)
                for candidate in self.candidates
            ],
            "house_activations": [
                activation.to_dict(include_evidence=include_evidence)
                for activation in self.house_activations
            ],
            "chart_manifestations": [
                manifestation.to_dict()
                for manifestation in self.chart_manifestations
            ],
            "natal_promises": list(self.natal_promises),
            "diagnostics": self.diagnostics,
        }
