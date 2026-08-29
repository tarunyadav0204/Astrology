from __future__ import annotations

"""Auditable, event-specific timing windows built on the house ledger.

The resolver is deliberately generic.  A life area contributes a declarative
definition; the shared evaluator applies gates, confirmations, scoring, and a
calculation trace without embedding event names in the algorithm.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from calculators.divisional_chart_calculator import DivisionalChartCalculator

from .context import CalculationContext
from .contracts import HouseActivation, HouseActivationState, PredictionWindow
from .errors import PredictionCalculationError, PredictionConfigurationError
from .primitives import aspected_houses, ruled_houses


EVENT_WINDOW_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True)
class SignalGroup:
    key: str
    label: str
    houses: Tuple[int, ...]
    weight: int
    required: bool = False
    require_all: bool = False
    description: str = ""


@dataclass(frozen=True)
class ClassificationRule:
    key: str
    label: str
    transition_any: Tuple[int, ...] = ()
    transition_all: Tuple[int, ...] = ()
    outcome: str = "any"  # any | present | absent


@dataclass(frozen=True)
class EventDefinition:
    key: str
    label: str
    description: str
    varga: str
    varga_houses: Tuple[int, ...]
    varga_description: str
    anchor: SignalGroup
    transition: SignalGroup
    outcome: SignalGroup
    classifications: Tuple[ClassificationRule, ...]
    version: str
    independent_confirmation_required: bool = True
    score_activation_quality: bool = False


JOB_CHANGE = EventDefinition(
    key="job_change",
    label="Job change",
    description=(
        "Professional movement requiring a dynamically active career anchor "
        "and a separate transition signal. Natal career-change wiring is "
        "context only and never vetoes a window."
    ),
    varga="D10",
    varga_houses=(6, 10),
    varga_description=(
        "D10 is the career-specific divisional chart. An active dasha lord connected to D10 H6 "
        "strengthens employment/service relevance; connection to D10 H10 strengthens profession, "
        "responsibility and status relevance. D10 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="career_anchor", label="Career anchor", houses=(6, 10), weight=25,
        required=True,
        description=(
            "At least one career house must be opened by the current MD/AD/PD: H6 describes employment, "
            "service, duties and the working environment; H10 describes profession, role, authority and status."
        ),
    ),
    transition=SignalGroup(
        key="transition", label="Transition signal", houses=(3, 8, 12), weight=20,
        required=True,
        description=(
            "A job-change reading needs movement as well as career activity: H3 can show initiative, "
            "applications or transfer; H8 can show restructuring or a break in continuity; H12 can "
            "show release from the present arrangement."
        ),
    ),
    outcome=SignalGroup(
        key="outcome", label="Outcome support", houses=(2, 11), weight=10,
        description=(
            "H2 describes salary and financial continuity; H11 describes gain, fulfilment and the benefit "
            "received. They classify the likely outcome but are not required for a job change to occur."
        ),
    ),
    classifications=(
        ClassificationRule(
            "job_change_with_gain_support", "Job change with gain support", outcome="present"
        ),
        ClassificationRule(
            "transfer_or_relocation", "Transfer or relocation pattern",
            transition_all=(3, 12), outcome="absent",
        ),
        ClassificationRule(
            "exit_or_interruption", "Exit or interruption pattern",
            transition_any=(8, 12), outcome="absent",
        ),
        ClassificationRule("professional_transition", "Professional transition"),
    ),
    version="job_change.v1",
)


HEALTH = EventDefinition(
    key="health",
    label="Health",
    description=(
        "Significant periods of health attention, treatment, rest or recovery support. "
        "This is an astrological timing aid and does not diagnose a condition or replace medical care."
    ),
    varga="D30",
    varga_houses=(1, 6, 8, 12),
    varga_description=(
        "D30 is used here only as a confirming chart for vulnerability, difficulty and the handling "
        "of health pressure. A dasha-lord connection to D30 H1/H6/H8/H12 strengthens relevance, "
        "but D30 never diagnoses a disease and never vetoes a health window."
    ),
    anchor=SignalGroup(
        key="health_anchor", label="Health anchor", houses=(1, 6), weight=25,
        required=True,
        description=(
            "H1 describes the body, vitality and overall physical state; H6 describes illness, "
            "treatment, health routines and the effort required to overcome a problem. At least one "
            "must be opened by the active MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="health_pressure", label="Health pressure or intervention", houses=(8, 12), weight=20,
        required=True,
        description=(
            "H8 can show an acute change, chronic concern, investigation or deeper intervention; "
            "H12 can show rest, withdrawal, hospitalization, isolation or sustained recovery time."
        ),
    ),
    outcome=SignalGroup(
        key="recovery_support", label="Recovery support", houses=(5, 11), weight=10,
        description=(
            "H5 is the twelfth from H6 and can show release from illness; H11 can show improvement, "
            "support and fulfilment of treatment. These houses describe recovery support, not a guarantee."
        ),
    ),
    classifications=(
        ClassificationRule(
            "health_attention_with_recovery_support",
            "Health attention with recovery support",
            outcome="present",
        ),
        ClassificationRule(
            "rest_or_treatment_window", "Rest or treatment window",
            transition_any=(12,), outcome="absent",
        ),
        ClassificationRule(
            "intensive_health_attention", "Intensive health-attention window",
            transition_any=(8,), outcome="absent",
        ),
        ClassificationRule("health_attention", "Health-attention window"),
    ),
    version="health.v1",
)


PROPERTY_PURCHASE = EventDefinition(
    key="property_purchase",
    label="Property purchase",
    description=(
        "A home or property acquisition window: the fourth house must be dasha-opened, "
        "together with a payment or financing signal. Natal property yogas are context only "
        "and never veto a window."
    ),
    varga="D4",
    varga_houses=(4,),
    varga_description=(
        "D4 is the property and residence chart. An active dasha lord connected to D4 H4 "
        "strengthens home, land and fixed-asset relevance. D4 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="property_anchor", label="Property anchor", houses=(4,), weight=25,
        required=True,
        description=(
            "H4 describes home, residence, land, vehicles as conveyances and inner stability. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="purchase_outlay", label="Payment or financing", houses=(2, 8), weight=20,
        required=True,
        description=(
            "A purchase needs an outlay as well as a property house: H2 can show using savings "
            "or family resources; H8 can show a loan, mortgage, inheritance or joint purchase."
        ),
    ),
    outcome=SignalGroup(
        key="property_fulfilment", label="Property fulfilment", houses=(11,), weight=10,
        description=(
            "H11 describes gaining the asset, fulfilment of the property objective and the benefit "
            "received. It classifies a completed-looking purchase but is not required for the window."
        ),
    ),
    classifications=(
        ClassificationRule(
            "property_purchase_with_gain", "Property purchase with gain support", outcome="present"
        ),
        ClassificationRule(
            "loan_or_shared_purchase", "Loan, mortgage or shared-purchase pattern",
            transition_any=(8,), outcome="absent",
        ),
        ClassificationRule(
            "purchase_from_savings", "Purchase from savings or family resources",
            transition_any=(2,), outcome="absent",
        ),
        ClassificationRule("property_purchase", "Property purchase window"),
    ),
    version="property_purchase.v1",
)


RELOCATION = EventDefinition(
    key="relocation",
    label="Relocation",
    description=(
        "A change of residence or time away from the present home. The fourth house must be "
        "dasha-opened together with a movement or leaving signal. This is a housing-timing aid, "
        "not a guaranteed move date."
    ),
    varga="D4",
    varga_houses=(4, 12),
    varga_description=(
        "D4 H4 strengthens residence and property relevance; D4 H12 strengthens leaving, "
        "distance or a stay away from the present home. D4 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="home_anchor", label="Home anchor", houses=(4,), weight=25,
        required=True,
        description=(
            "H4 describes the current home, residence and living foundation. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="home_shift", label="Move or leaving signal", houses=(3, 12), weight=20,
        required=True,
        description=(
            "A relocation reading needs movement as well as a home house: H3 can show shifting, "
            "papers, short-distance change or the effort of moving; H12 can show leaving the "
            "present arrangement, expense of the move or a stay away from home."
        ),
    ),
    outcome=SignalGroup(
        key="settlement_support", label="Settlement or distance support", houses=(9, 11), weight=10,
        description=(
            "H9 can show a longer-distance or fortune-linked shift; H11 can show securing a new "
            "place or fulfilment of the move. They classify the flavour of relocation and are not required."
        ),
    ),
    classifications=(
        ClassificationRule(
            "relocation_with_settlement", "Relocation with settlement or distance support",
            outcome="present",
        ),
        ClassificationRule(
            "away_from_home", "Leaving or stay-away pattern",
            transition_any=(12,), outcome="absent",
        ),
        ClassificationRule(
            "local_home_shift", "Local home-shift pattern",
            transition_any=(3,), outcome="absent",
        ),
        ClassificationRule("relocation", "Relocation window"),
    ),
    version="relocation.v1",
)


PROPERTY_GAIN = EventDefinition(
    key="property_gain",
    label="Property gain",
    description=(
        "Periods where a home or property objective can reach fulfilment: the fourth house and "
        "an eleventh-house gain signal must both be dasha-opened. This does not guarantee a sale, "
        "allotment or possession date."
    ),
    varga="D4",
    varga_houses=(4, 11),
    varga_description=(
        "D4 H4 strengthens property and residence; D4 H11 strengthens fulfilment and gain of the "
        "fixed-asset objective. D4 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="property_anchor", label="Property anchor", houses=(4,), weight=25,
        required=True,
        description=(
            "H4 describes home, residence, land and fixed assets. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="property_gain_signal", label="Property gain signal", houses=(11,), weight=20,
        required=True,
        description=(
            "H11 describes gaining the asset, progress toward a property objective and the benefit "
            "received. For this search it must be opened in the same dasha window as H4."
        ),
    ),
    outcome=SignalGroup(
        key="resource_support", label="Resource support", houses=(2,), weight=10,
        description=(
            "H2 can show savings, family resources or liquidity supporting the gain. "
            "It classifies how the fulfilment is resourced and is not required."
        ),
    ),
    classifications=(
        ClassificationRule(
            "property_gain_with_resources", "Property gain with resource support", outcome="present"
        ),
        ClassificationRule("property_gain", "Property-gain window"),
    ),
    version="property_gain.v1",
)


PROMOTION = EventDefinition(
    key="promotion",
    label="Promotion / status",
    description=(
        "A rise in professional status, responsibility or recognition while remaining in career. "
        "This is not a job-change search: exit, resignation or role-break houses are not required "
        "and natal career yogas never veto a window."
    ),
    varga="D10",
    varga_houses=(10, 11),
    varga_description=(
        "D10 is the career-specific divisional chart. An active dasha lord connected to D10 H10 "
        "strengthens profession, authority and status; connection to D10 H11 strengthens recognition "
        "and the fruit of that status. D10 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="status_anchor", label="Career status anchor", houses=(10,), weight=25,
        required=True,
        description=(
            "H10 describes profession, public role, authority and career status. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="status_rise", label="Status or recognition signal", houses=(5, 11), weight=20,
        required=True,
        description=(
            "A promotion reading needs a rise as well as a career house: H11 can show gain, "
            "recognition, fulfilment and the fruit of status; H5 can show authority, honour, "
            "award or a visible step-up without leaving the role."
        ),
    ),
    outcome=SignalGroup(
        key="pay_support", label="Salary or resource support", houses=(2,), weight=10,
        description=(
            "H2 describes salary, accumulated resources and financial continuity with the rise. "
            "It classifies a pay-linked promotion and is not required for a status window."
        ),
    ),
    classifications=(
        ClassificationRule(
            "promotion_with_salary_support", "Promotion with salary support", outcome="present"
        ),
        ClassificationRule(
            "recognition_or_authority", "Recognition or authority pattern",
            transition_any=(5,), outcome="absent",
        ),
        ClassificationRule("career_status_rise", "Career status-rise window"),
    ),
    version="promotion.v1",
)


MARRIAGE = EventDefinition(
    key="marriage",
    label="Marriage / partnership",
    description=(
        "A partnership-commitment window: the seventh house must be dasha-opened together with "
        "a joining, romance or fulfilment signal. This is relationship timing, not a guaranteed "
        "wedding date, and natal marriage yogas never veto a window."
    ),
    varga="D9",
    varga_houses=(7,),
    varga_description=(
        "D9 is the marriage and dharma chart. An active dasha lord connected to D9 H7 "
        "strengthens spouse and partnership relevance. D9 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="partnership_anchor", label="Partnership anchor", houses=(7,), weight=25,
        required=True,
        description=(
            "H7 describes spouse, one-to-one partnership, agreements and the counterpart. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="joining_signal", label="Joining, romance or fulfilment", houses=(2, 5, 11), weight=20,
        required=True,
        description=(
            "A marriage reading needs a joining signal as well as H7: H2 can show family "
            "coming together or shared resources; H5 can show romance, meeting or affection; "
            "H11 can show gaining a partner and fulfilment of the relationship objective."
        ),
    ),
    outcome=SignalGroup(
        key="ceremony_support", label="Dharma or ceremony support", houses=(9,), weight=10,
        description=(
            "H9 can show a dharmic, ceremonial or fortune-linked flavour to the partnership. "
            "It classifies support for formalisation and is not required for the window."
        ),
    ),
    classifications=(
        ClassificationRule(
            "partnership_with_fulfilment", "Partnership with fulfilment support",
            transition_any=(11,),
        ),
        ClassificationRule(
            "romance_or_meeting", "Romance or meeting pattern",
            transition_any=(5,),
        ),
        ClassificationRule(
            "family_joining", "Family-joining pattern",
            transition_any=(2,),
        ),
        ClassificationRule("partnership_commitment", "Partnership-commitment window"),
    ),
    version="marriage.v1",
)


FOREIGN_TRAVEL = EventDefinition(
    key="foreign_travel",
    label="Foreign travel / stay",
    description=(
        "Long-distance travel or a stay away from the native land. The ninth house must be "
        "dasha-opened together with a movement or foreign-stay signal. This is not a home-move "
        "search: relocation still requires the fourth house."
    ),
    varga="D9",
    varga_houses=(9, 12),
    varga_description=(
        "D9 H9 strengthens long journeys, fortune and dharma-linked travel; D9 H12 strengthens "
        "foreign stay, distance or residence abroad. D9 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="journey_anchor", label="Long-journey anchor", houses=(9,), weight=25,
        required=True,
        description=(
            "H9 describes long journeys, fortune, teachers and the far horizon. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="travel_or_stay", label="Travel or foreign-stay signal", houses=(3, 12), weight=20,
        required=True,
        description=(
            "A travel reading needs movement as well as H9: H3 can show papers, planning or "
            "the short-distance start of a journey; H12 can show foreign stay, expense of travel "
            "or residence away from the native land."
        ),
    ),
    outcome=SignalGroup(
        key="travel_opportunity", label="Opportunity support", houses=(11,), weight=10,
        description=(
            "H11 can show gain, opportunity or fulfilment through the journey. "
            "It classifies a fruit-bearing trip and is not required."
        ),
    ),
    classifications=(
        ClassificationRule(
            "travel_with_opportunity", "Travel with opportunity support", outcome="present"
        ),
        ClassificationRule(
            "foreign_stay", "Foreign-stay pattern",
            transition_any=(12,), outcome="absent",
        ),
        ClassificationRule(
            "journey_or_travel_plans", "Journey or travel-plans pattern",
            transition_any=(3,), outcome="absent",
        ),
        ClassificationRule("long_distance_movement", "Long-distance movement window"),
    ),
    version="foreign_travel.v1",
)


CHILDREN = EventDefinition(
    key="children",
    label="Children",
    description=(
        "Child-related development, responsibility or fulfilment around the fifth house. "
        "This is an astrological timing aid and does not predict a birth, diagnose fertility "
        "or determine the sex of a child."
    ),
    varga="D7",
    varga_houses=(5,),
    varga_description=(
        "D7 is used here only as a confirming chart for children and creative progeny. "
        "A dasha-lord connection to D7 H5 strengthens relevance, but D7 never predicts a birth "
        "and never vetoes the window."
    ),
    anchor=SignalGroup(
        key="children_anchor", label="Children anchor", houses=(5,), weight=25,
        required=True,
        description=(
            "H5 describes children, creative progeny and the intelligence applied to them. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="child_development", label="Expansion or fulfilment", houses=(9, 11), weight=20,
        required=True,
        description=(
            "A children reading needs growth as well as H5: H9 can show dharma, expansion or "
            "a blessing-linked development; H11 can show fulfilment of a child-related objective."
        ),
    ),
    outcome=SignalGroup(
        key="family_support", label="Family-resource support", houses=(2,), weight=10,
        description=(
            "H2 can show family resources or the household supporting the development. "
            "It classifies support and is not required."
        ),
    ),
    classifications=(
        ClassificationRule(
            "child_development_with_fulfilment", "Child-related development with fulfilment",
            transition_any=(11,),
        ),
        ClassificationRule(
            "child_dharma_or_expansion", "Dharma or expansion pattern",
            transition_any=(9,),
        ),
        ClassificationRule("child_development", "Child-related development window"),
    ),
    version="children.v1",
)


EDUCATION = EventDefinition(
    key="education",
    label="Education / exams",
    description=(
        "Study, qualification or examination windows around the fifth house. "
        "Natal education yogas never veto a window, and this does not guarantee a result."
    ),
    varga="D24",
    varga_houses=(5, 9),
    varga_description=(
        "D24 is the learning chart. An active dasha lord connected to D24 H5 strengthens "
        "study and intelligence; connection to D24 H9 strengthens higher learning. "
        "D24 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="learning_anchor", label="Learning anchor", houses=(5,), weight=25,
        required=True,
        description=(
            "H5 describes intelligence, study, examinations and the application of learning. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="study_path", label="Study path", houses=(4, 9), weight=20,
        required=True,
        description=(
            "An education reading needs a path as well as H5: H4 can show foundational learning, "
            "schooling or the educational base; H9 can show higher studies, teachers or long-form "
            "qualification."
        ),
    ),
    outcome=SignalGroup(
        key="exam_result", label="Result support", houses=(11,), weight=10,
        description=(
            "H11 can show fulfilment of a course, examination success or the fruit of study. "
            "It classifies a result-looking window and is not a guarantee."
        ),
    ),
    classifications=(
        ClassificationRule(
            "education_with_result", "Education with result support", outcome="present"
        ),
        ClassificationRule(
            "higher_learning", "Higher-learning pattern",
            transition_any=(9,), outcome="absent",
        ),
        ClassificationRule(
            "foundational_study", "Foundational-study pattern",
            transition_any=(4,), outcome="absent",
        ),
        ClassificationRule("education_milestone", "Education-milestone window"),
    ),
    version="education.v1",
)


INCOME_GAIN = EventDefinition(
    key="income_gain",
    label="Income / gains",
    description=(
        "Income and accumulated-resource windows: the second and eleventh houses must both "
        "be dasha-opened in the same period. This is not a job-change or promotion search."
    ),
    varga="D2",
    varga_houses=(2, 11),
    varga_description=(
        "D2 is the resource chart. An active dasha lord connected to D2 H2 strengthens savings "
        "and accumulated wealth; connection to D2 H11 strengthens gains and inflow. "
        "D2 confirms but never vetoes the event."
    ),
    anchor=SignalGroup(
        key="savings_anchor", label="Savings anchor", houses=(2,), weight=25,
        required=True,
        description=(
            "H2 describes accumulated resources, savings, family money and the store of wealth. "
            "It must be opened by the current MD/AD/PD."
        ),
    ),
    transition=SignalGroup(
        key="gains_signal", label="Gains signal", houses=(11,), weight=20,
        required=True,
        description=(
            "H11 describes income, gains, fulfilment of financial objectives and inflow. "
            "For this search it must be opened in the same dasha window as H2."
        ),
    ),
    outcome=SignalGroup(
        key="fortune_or_speculation", label="Fortune or speculation support", houses=(5, 9), weight=10,
        description=(
            "H5 can show speculative or intelligent-risk income; H9 can show fortune-linked or "
            "guidance-linked gain. They classify the flavour of inflow and are not required."
        ),
    ),
    classifications=(
        ClassificationRule(
            "income_with_fortune_or_speculation",
            "Income with fortune or speculation support",
            outcome="present",
        ),
        ClassificationRule("income_and_gains", "Income and gains window"),
    ),
    version="income_gain.v1",
)


EVENT_DEFINITIONS: Mapping[str, EventDefinition] = {
    JOB_CHANGE.key: JOB_CHANGE,
    PROMOTION.key: PROMOTION,
    HEALTH.key: HEALTH,
    PROPERTY_PURCHASE.key: PROPERTY_PURCHASE,
    RELOCATION.key: RELOCATION,
    PROPERTY_GAIN.key: PROPERTY_GAIN,
    MARRIAGE.key: MARRIAGE,
    FOREIGN_TRAVEL.key: FOREIGN_TRAVEL,
    CHILDREN.key: CHILDREN,
    EDUCATION.key: EDUCATION,
    INCOME_GAIN.key: INCOME_GAIN,
}

CUSTOM_EVENT_KEY = "custom"


def normalise_focus_houses(houses: Sequence[Any] | None) -> Tuple[int, ...]:
    if not houses:
        raise PredictionConfigurationError("Custom focus requires at least one house")
    unique: List[int] = []
    seen = set()
    for value in houses:
        house = int(value)
        if house < 1 or house > 12:
            raise PredictionConfigurationError("Custom houses must be between 1 and 12")
        if house not in seen:
            seen.add(house)
            unique.append(house)
    return tuple(sorted(unique))


def build_custom_definition(houses: Sequence[Any] | None) -> EventDefinition:
    selected = normalise_focus_houses(houses)
    labels = "/".join(f"H{house}" for house in selected)
    return EventDefinition(
        key=CUSTOM_EVENT_KEY,
        label="Custom",
        description=(
            "Find periods where every selected house is opened by the current MD, AD or PD. "
            "Transit hits, dasha boundaries, Jupiter–Saturn contact and exact returns are optional "
            "and only change the strength of a window."
        ),
        varga="",
        varga_houses=(),
        varga_description="",
        anchor=SignalGroup(
            key="selected_houses",
            label="Selected houses",
            houses=selected,
            weight=55,
            required=True,
            require_all=True,
            description=(
                f"Every selected house ({labels}) must be opened by the active MD/AD/PD through "
                "lordship, occupation or aspect. Transit-only contact is not enough."
            ),
        ),
        transition=SignalGroup(
            key="unused_transition",
            label="Transition",
            houses=(),
            weight=0,
            required=False,
        ),
        outcome=SignalGroup(
            key="unused_outcome",
            label="Outcome",
            houses=(),
            weight=0,
            required=False,
        ),
        classifications=(
            ClassificationRule("selected_houses_dasha", "Selected houses in dasha"),
        ),
        version=f"custom.v1.h{'-'.join(str(house) for house in selected)}",
        independent_confirmation_required=False,
        score_activation_quality=True,
    )


STATE_RANK = {
    HouseActivationState.DORMANT: 0,
    HouseActivationState.TRANSIT_ONLY: 0,
    HouseActivationState.DASHA_CONNECTED: 1,
    HouseActivationState.DASHA_TRANSIT_ACTIVATED: 2,
    HouseActivationState.FULLY_REINFORCED: 3,
}


def _relation_rows(chart: Dict[str, Any], planet: str, houses: Iterable[int]) -> List[Dict[str, Any]]:
    occupied = int(chart["planets"][planet]["house"])
    ruled = set(ruled_houses(chart, planet))
    aspected = set(aspected_houses(planet, occupied))
    rows: List[Dict[str, Any]] = []
    for house in houses:
        relations: List[str] = []
        if house in ruled:
            relations.append("lordship")
        if house == occupied:
            relations.append("occupation")
        if house in aspected:
            relations.append("aspect")
        if relations:
            rows.append({"planet": planet, "house": house, "relations": relations})
    return rows


def _build_varga(calculation: CalculationContext, varga: str) -> Dict[str, Any]:
    try:
        division = int(str(varga).upper().removeprefix("D"))
        chart = DivisionalChartCalculator(calculation.chart).calculate_divisional_chart(division)[
            "divisional_chart"
        ]
        if not isinstance(chart, dict) or not isinstance(chart.get("planets"), dict):
            raise ValueError(f"{varga} contains no planets")
        return chart
    except Exception as exc:
        raise PredictionCalculationError(f"Required {varga} event confirmation failed") from exc


def _varga_confirmation(
    chart: Dict[str, Any], window: PredictionWindow, definition: EventDefinition
) -> Dict[str, Any]:
    matches = [
        relation
        for planet in dict.fromkeys((
            window.mahadasha, window.antardasha, window.pratyantardasha,
        ))
        for relation in _relation_rows(chart, planet, definition.varga_houses)
    ]
    return {
        "passed": bool(matches),
        "chart": definition.varga,
        "matches": matches,
        "explanation": (
            f"An active dasha lord carries {definition.varga} "
            f"{('/'.join(f'H{house}' for house in definition.varga_houses))} by lordship, occupation, or aspect."
            if matches else
            f"No active dasha lord carries the selected {definition.varga} houses in this period."
        ),
    }


def _double_transit(calculation: CalculationContext, window: PredictionWindow, houses: Sequence[int]) -> Dict[str, Any]:
    states = calculation.transit_states_by_signature[window.transit_signature]
    matches: List[int] = []
    planet_rows: Dict[str, Dict[str, Any]] = {}
    for planet in ("Jupiter", "Saturn"):
        transit_house = int(states[planet]["house"])
        contacts = {transit_house, *aspected_houses(planet, transit_house)}
        planet_rows[planet] = {
            "transit_house": transit_house,
            "contacted_focus_houses": sorted(set(houses).intersection(contacts)),
        }
    for house in houses:
        if all(house in planet_rows[p]["contacted_focus_houses"] for p in ("Jupiter", "Saturn")):
            matches.append(house)
    return {
        "passed": bool(matches),
        "houses": matches,
        "planets": planet_rows,
        "explanation": (
            f"Jupiter and Saturn both contact {'/'.join(f'H{h}' for h in matches)}."
            if matches else "Jupiter and Saturn do not jointly contact the same focus house."
        ),
    }


def _rows_for_window(
    activations: Sequence[HouseActivation], window: PredictionWindow
) -> Dict[int, HouseActivation]:
    covering = [
        row for row in activations
        if row.window.start_date <= window.start_date
        and row.window.end_date >= window.end_date
    ]
    best: Dict[int, HouseActivation] = {}
    for row in covering:
        previous = best.get(row.house)
        if previous is None or STATE_RANK[row.state] > STATE_RANK[previous.state]:
            best[row.house] = row
    return best


def _group_trace(group: SignalGroup, rows: Mapping[int, HouseActivation]) -> Dict[str, Any]:
    matched = [
        rows[house] for house in group.houses
        if house in rows and STATE_RANK[rows[house].state] >= 1
    ]
    if not group.houses:
        passed = not group.required
    elif group.require_all:
        passed = len(matched) == len(group.houses)
    else:
        passed = bool(matched)
    return {
        "key": group.key,
        "label": group.label,
        "required": group.required,
        "passed": passed,
        "score": group.weight if passed else 0,
        "maximum_score": group.weight,
        "description": group.description,
        "evidence": [
            {
                "house": row.house,
                "state": row.state.value,
                "carriers": list(row.activation.carrier_planets),
                "dasha_levels": list(row.activation.active_dasha_levels),
                "natal_connections": list(row.natal_connections),
                "transit_connections": list(row.transit_connections),
            }
            for row in matched
        ],
    }


def _custom_classification(independent_passed: bool, transit_reinforced: bool) -> Tuple[str, str]:
    if independent_passed and transit_reinforced:
        return "selected_houses_reinforced", "Selected houses with dasha and transit"
    if independent_passed:
        return "selected_houses_confirmed", "Selected houses with timing confirmation"
    return "selected_houses_dasha", "Selected houses in dasha"


def _confirmations(rows: Iterable[HouseActivation]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        for item in row.transit_confirmations:
            key = (
                item.get("kind"), item.get("planet"), item.get("target_planet"),
                item.get("exact_at"), item.get("label"),
            )
            if key not in seen:
                seen.add(key)
                output.append(dict(item))
    return output


def _classification(
    definition: EventDefinition,
    transition: Dict[str, Any],
    outcome: Dict[str, Any],
) -> Tuple[str, str]:
    transition_houses = {row["house"] for row in transition["evidence"]}
    outcome_houses = {row["house"] for row in outcome["evidence"]}
    for rule in definition.classifications:
        if rule.outcome == "present" and not outcome_houses:
            continue
        if rule.outcome == "absent" and outcome_houses:
            continue
        if rule.transition_any and not transition_houses.intersection(rule.transition_any):
            continue
        if rule.transition_all and not set(rule.transition_all).issubset(transition_houses):
            continue
        return rule.key, rule.label
    raise PredictionConfigurationError(
        f"Event definition {definition.key} has no matching fallback classification"
    )


def _next_day(value: str) -> str:
    return (date.fromisoformat(value) + timedelta(days=1)).isoformat()


def _merge_key(row: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        tuple(row["dasha"].values()),
        row["strength"],
        row["classification"],
        tuple(row["activated_houses"]),
        row["score"],
    )


def _merge_adjacent_windows(rows: Sequence[Dict[str, Any]], event_key: str) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    for source in rows:
        row = dict(source)
        row["timing_slices"] = [{
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "score": row["score"],
            "opened_by": row["opened_by"],
            "closed_by": row["closed_by"],
        }]
        if (
            merged
            and _next_day(merged[-1]["end_date"]) == row["start_date"]
            and _merge_key(merged[-1]) == _merge_key(row)
        ):
            merged[-1]["end_date"] = row["end_date"]
            merged[-1]["closed_by"] = row["closed_by"]
            merged[-1]["timing_slices"].extend(row["timing_slices"])
            # Prefer a more exact timing reason from a later merged slice.
            if row["peak_rank"] > merged[-1]["peak_rank"]:
                merged[-1]["peak_date"] = row["peak_date"]
                merged[-1]["inspection_date"] = row["inspection_date"]
                merged[-1]["peak_reason"] = row["peak_reason"]
                merged[-1]["peak_rank"] = row["peak_rank"]
                merged[-1]["calculation_trace"] = row["calculation_trace"]
            continue
        merged.append(row)
    for row in merged:
        row["window_id"] = hashlib.sha256(
            f"{event_key}|{row['start_date']}|{row['end_date']}|{_merge_key(row)}".encode()
        ).hexdigest()[:20]
    return merged


class EventWindowEngine:
    version = EVENT_WINDOW_ENGINE_VERSION

    def resolve(
        self,
        *,
        event_key: str,
        calculation: CalculationContext,
        activations: Sequence[HouseActivation],
        include_developing: bool = False,
        focus_houses: Optional[Sequence[Any]] = None,
    ) -> Dict[str, Any]:
        if event_key == CUSTOM_EVENT_KEY:
            definition = build_custom_definition(focus_houses)
        else:
            definition = EVENT_DEFINITIONS.get(event_key)
            if definition is None:
                raise PredictionConfigurationError(f"Unsupported event focus: {event_key}")

        varga_chart = _build_varga(calculation, definition.varga) if definition.varga else {}
        varga_by_dasha: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
        output: List[Dict[str, Any]] = []
        rejected = {"missing_anchor": 0, "missing_transition": 0, "missing_confirmation": 0}
        for window in calculation.windows:
            rows = _rows_for_window(activations, window)
            anchor = _group_trace(definition.anchor, rows)
            transition = _group_trace(definition.transition, rows)
            outcome = _group_trace(definition.outcome, rows)
            if not anchor["passed"]:
                rejected["missing_anchor"] += 1
                continue
            if definition.transition.required and not transition["passed"]:
                rejected["missing_transition"] += 1
                continue

            relevant_houses = set(definition.anchor.houses + definition.transition.houses)
            relevant_rows = [rows[house] for house in relevant_houses if house in rows]
            confirmations = _confirmations(relevant_rows)
            dasha_key = (window.mahadasha, window.antardasha, window.pratyantardasha)
            if definition.varga:
                if dasha_key not in varga_by_dasha:
                    varga_by_dasha[dasha_key] = _varga_confirmation(
                        varga_chart, window, definition
                    )
                varga_confirmation = varga_by_dasha[dasha_key]
            else:
                varga_confirmation = {
                    "passed": False, "chart": "", "matches": [], "explanation": "",
                }
            double = _double_transit(calculation, window, definition.anchor.houses)
            transit_reinforced = any(STATE_RANK[row.state] >= 2 for row in relevant_rows)
            dasha_boundary = [row for row in window.opened_by if row.get("kind") == "dasha"]
            independent_passed = bool(
                transit_reinforced or confirmations or double["passed"] or dasha_boundary
            )
            if not independent_passed:
                rejected["missing_confirmation"] += 1

            confirmation_trace = {
                "key": "independent_confirmation",
                "label": "Independent timing confirmation",
                "required": definition.independent_confirmation_required,
                "passed": independent_passed,
                "score": 15 if independent_passed else 0,
                "maximum_score": 15,
                "description": (
                    "Dasha describes what is available, but it is too broad to time an event alone. "
                    "This gate therefore asks for a separate clock: a direct dasha-lord transit, "
                    "Jupiter–Saturn contact, an MD/AD/PD boundary, or an exact/repeated natal contact."
                    if definition.independent_confirmation_required else
                    "Optional. A separate clock — dasha-lord transit, Jupiter–Saturn contact, "
                    "an MD/AD/PD boundary, or an exact/repeated natal contact — raises strength "
                    "but is not required to qualify the window."
                ),
                "evidence": {
                    "transit_reinforced": transit_reinforced,
                    "dasha_boundaries": dasha_boundary,
                    "exact_and_repetition_confirmations": confirmations,
                    "double_transit": double,
                },
            }
            dasha_trace = {
                "key": "dasha_permission",
                "label": "Dasha relevance",
                "required": True,
                "passed": True,
                "score": 20,
                "maximum_score": 20,
                "description": (
                    "A house is dasha-relevant when an active MD, AD or PD lord owns it, occupies it "
                    "or aspects it in the natal chart. MD gives the broad chapter, AD channels it, "
                    "and PD helps identify the shorter delivery period."
                ),
                "evidence": {
                    "MD": window.mahadasha,
                    "AD": window.antardasha,
                    "PD": window.pratyantardasha,
                },
            }
            varga_trace = {
                "key": "divisional_confirmation",
                "label": f"{definition.varga} confirmation",
                "required": False,
                "passed": varga_confirmation["passed"],
                "score": 10 if varga_confirmation["passed"] else 0,
                "maximum_score": 10,
                "description": definition.varga_description,
                "evidence": varga_confirmation,
            }
            quality_trace = {
                "key": "activation_quality",
                "label": "Transit reinforcement",
                "required": False,
                "passed": transit_reinforced,
                "score": 10 if transit_reinforced else 0,
                "maximum_score": 10,
                "description": (
                    "Optional. A selected house is stronger when the dasha lord that opens it "
                    "also occupies or aspects it in transit, or is fully reinforced by self-contact or the Sun."
                ),
                "evidence": {
                    "transit_reinforced": transit_reinforced,
                    "houses": [
                        {"house": row.house, "state": row.state.value}
                        for row in relevant_rows if STATE_RANK[row.state] >= 2
                    ],
                },
            }
            trace = [anchor]
            if definition.transition.houses:
                trace.append(transition)
            trace.extend([dasha_trace, confirmation_trace])
            if definition.outcome.houses:
                trace.append(outcome)
            if definition.varga:
                trace.append(varga_trace)
            if definition.score_activation_quality:
                trace.append(quality_trace)
            score = sum(int(row["score"]) for row in trace)
            required_passed = anchor["passed"]
            if definition.transition.required:
                required_passed = required_passed and transition["passed"]
            if definition.independent_confirmation_required:
                required_passed = required_passed and independent_passed
            strength = (
                "exceptional" if required_passed and score >= 95 else
                "strong" if required_passed and score >= 80 else
                "developing"
            )
            if strength == "developing" and not include_developing:
                continue
            if definition.key == CUSTOM_EVENT_KEY:
                classification_key, classification_label = _custom_classification(
                    independent_passed, transit_reinforced
                )
            else:
                classification_key, classification_label = _classification(
                    definition, transition, outcome
                )
            exact_peak = next(
                (
                    (str(row.get("exact_at"))[:10], str(row.get("label") or "Exact transit confirmation"))
                    for row in confirmations if row.get("exact_at")
                ),
                None,
            )
            opening_dasha = next(
                (str(row.get("label")) for row in dasha_boundary if row.get("label")),
                None,
            )
            if exact_peak:
                peak, peak_reason, peak_rank = exact_peak[0], exact_peak[1], 2
            elif opening_dasha:
                peak, peak_reason, peak_rank = window.start_date, opening_dasha, 1
            else:
                peak, peak_reason, peak_rank = None, (
                    "No exact peak was isolated in this slice; inspect from the window opening."
                ), 0
            identity = hashlib.sha256(
                f"{event_key}|{window.start_date}|{window.end_date}|{window.transit_signature}".encode()
            ).hexdigest()[:20]
            output.append({
                "window_id": identity,
                "start_date": window.start_date,
                "end_date": window.end_date,
                "peak_date": peak,
                "inspection_date": peak or window.start_date,
                "peak_reason": peak_reason,
                "peak_rank": peak_rank,
                "dasha": {
                    "mahadasha": window.mahadasha,
                    "antardasha": window.antardasha,
                    "pratyantardasha": window.pratyantardasha,
                },
                "strength": strength,
                "score": score,
                "maximum_score": 100,
                "classification": classification_key,
                "classification_label": classification_label,
                "summary": (
                    f"{classification_label}: {definition.anchor.label.lower()} and "
                    f"{definition.transition.label.lower()} converge in the same dasha window."
                ),
                "qualification_summary": (
                    f"{definition.anchor.label} is shown through "
                    f"{', '.join('H{}'.format(row['house']) for row in anchor['evidence'])}; "
                    f"{definition.transition.label.lower()} is shown through "
                    f"{', '.join('H{}'.format(row['house']) for row in transition['evidence'])}. "
                    + (
                        f"H{', H'.join(str(row['house']) for row in outcome['evidence'])} adds "
                        f"{definition.outcome.label.lower()}. "
                        if outcome["evidence"] else
                        f"{definition.outcome.label} was not required to qualify this window. "
                    )
                    + (
                        f"{definition.varga} adds divisional confirmation."
                        if varga_confirmation["passed"] else
                        f"{definition.varga} does not add a direct confirmation."
                    )
                ),
                "activated_houses": sorted({
                    evidence["house"]
                    for item in (anchor, transition, outcome)
                    for evidence in item["evidence"]
                }),
                "opened_by": [dict(item) for item in window.opened_by],
                "closed_by": [dict(item) for item in window.closed_by],
                "calculation_trace": trace,
            })

        output = _merge_adjacent_windows(output, event_key)
        signature = hashlib.sha256(json.dumps({
            "engine": self.version,
            "definition": definition.version,
            "event": event_key,
            "focus_houses": list(definition.anchor.houses) if event_key == CUSTOM_EVENT_KEY else [],
            "year": calculation.windows[0].start_date[:4] if calculation.windows else "",
            "windows": [(row["window_id"], row["score"]) for row in output],
        }, sort_keys=True).encode()).hexdigest()
        return {
            "engine_version": self.version,
            "definition_version": definition.version,
            "event_key": definition.key,
            "event_label": definition.label,
            "event_description": definition.description,
            "varga": definition.varga or None,
            "focus_houses": list(definition.anchor.houses) if event_key == CUSTOM_EVENT_KEY else [],
            "include_developing": include_developing,
            "evaluated_windows": len(calculation.windows),
            "qualified_windows": len(output),
            "rejected_summary": rejected,
            "evidence_signature": signature,
            "windows": output,
        }
