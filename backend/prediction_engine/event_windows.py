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
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

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


EVENT_DEFINITIONS: Mapping[str, EventDefinition] = {
    JOB_CHANGE.key: JOB_CHANGE,
    HEALTH.key: HEALTH,
}


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
    return {
        "key": group.key,
        "label": group.label,
        "required": group.required,
        "passed": bool(matched),
        "score": group.weight if matched else 0,
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
    ) -> Dict[str, Any]:
        definition = EVENT_DEFINITIONS.get(event_key)
        if definition is None:
            raise PredictionConfigurationError(f"Unsupported event focus: {event_key}")

        varga_chart = _build_varga(calculation, definition.varga)
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
            if not transition["passed"]:
                rejected["missing_transition"] += 1
                continue

            relevant_houses = set(definition.anchor.houses + definition.transition.houses)
            relevant_rows = [rows[house] for house in relevant_houses if house in rows]
            confirmations = _confirmations(relevant_rows)
            dasha_key = (window.mahadasha, window.antardasha, window.pratyantardasha)
            if dasha_key not in varga_by_dasha:
                varga_by_dasha[dasha_key] = _varga_confirmation(
                    varga_chart, window, definition
                )
            varga_confirmation = varga_by_dasha[dasha_key]
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
                "required": True,
                "passed": independent_passed,
                "score": 15 if independent_passed else 0,
                "maximum_score": 15,
                "description": (
                    "Dasha describes what is available, but it is too broad to time an event alone. "
                    "This gate therefore asks for a separate clock: a direct dasha-lord transit, "
                    "Jupiter–Saturn contact, an MD/AD/PD boundary, or an exact/repeated natal contact."
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
            trace = [anchor, transition, dasha_trace, confirmation_trace, outcome, varga_trace]
            score = sum(int(row["score"]) for row in trace)
            required_passed = anchor["passed"] and transition["passed"] and independent_passed
            strength = (
                "exceptional" if required_passed and score >= 95 else
                "strong" if required_passed and score >= 80 else
                "developing"
            )
            if strength == "developing" and not include_developing:
                continue
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
            "year": calculation.windows[0].start_date[:4] if calculation.windows else "",
            "windows": [(row["window_id"], row["score"]) for row in output],
        }, sort_keys=True).encode()).hexdigest()
        return {
            "engine_version": self.version,
            "definition_version": definition.version,
            "event_key": definition.key,
            "event_label": definition.label,
            "event_description": definition.description,
            "varga": definition.varga,
            "include_developing": include_developing,
            "evaluated_windows": len(calculation.windows),
            "qualified_windows": len(output),
            "rejected_summary": rejected,
            "evidence_signature": signature,
            "windows": output,
        }
