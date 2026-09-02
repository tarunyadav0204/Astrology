"""Blind validation harness for the deterministic birth-time rectification engine.

Prediction inputs and verified birth times intentionally live in separate files.
The runner completes every chart prediction before loading the truth vault, so
the scorer cannot tune a candidate against the answer it is meant to recover.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .engine import CandidateEvaluation, RectificationEngine, SparseAstrologyEvaluator
from .contracts import CreateRectificationEventRequest


BENCHMARK_SCHEMA_VERSION = "rectification.benchmark.v1"
BLINDED_DATASET_SCHEMA_VERSION = "rectification.blinded-cases.v1"
TRUTH_VAULT_SCHEMA_VERSION = "rectification.truth-vault.v1"
RECOVERY_THRESHOLDS_MINUTES = (5, 15, 30, 60)

LAYER_KEYS = {
    "structural": "structural_promise",
    "dasha": "dasha_delivery",
    "varga": "varga_confirmation",
    "transit": "transit_confirmation",
    "kp": "kp_confirmation",
}

ABLATION_PROFILES: Dict[str, Tuple[str, ...]] = {
    "full": tuple(LAYER_KEYS),
    "without_structural": ("dasha", "varga", "transit", "kp"),
    "without_dasha": ("structural", "varga", "transit", "kp"),
    "without_varga": ("structural", "dasha", "transit", "kp"),
    "without_transit": ("structural", "dasha", "varga", "kp"),
    "without_kp": ("structural", "dasha", "varga", "transit"),
    "parashari_only": ("structural", "dasha", "varga", "transit"),
    "kp_only": ("kp",),
}
BENCHMARK_PROFILES = (*ABLATION_PROFILES.keys(), "midpoint_baseline")

FORBIDDEN_TRUTH_KEYS = {
    "verified_time", "verified_local_time", "true_time", "truth_time",
    "recorded_time", "exact_birth_time",
}


class BlindedCaseSet(list):
    dataset_id: str
    cohort_status: str

    def __init__(
        self, rows: Iterable[Mapping[str, Any]], dataset_id: str, cohort_status: str = ""
    ):
        super().__init__(dict(row) for row in rows)
        self.dataset_id = dataset_id
        self.cohort_status = cohort_status


class TruthVault(dict):
    dataset_id: str
    cohort_status: str

    def __init__(
        self, rows: Mapping[str, Mapping[str, Any]], dataset_id: str, cohort_status: str = ""
    ):
        super().__init__((key, dict(value)) for key, value in rows.items())
        self.dataset_id = dataset_id
        self.cohort_status = cohort_status


def _time_seconds(value: str) -> int:
    parts = str(value or "").strip().split(":")
    if len(parts) not in {2, 3}:
        raise ValueError(f"Invalid local time: {value!r}")
    hour, minute = int(parts[0]), int(parts[1])
    second = int(parts[2]) if len(parts) == 3 else 0
    if not 0 <= hour <= 23 or not 0 <= minute <= 59 or not 0 <= second <= 59:
        raise ValueError(f"Invalid local time: {value!r}")
    return hour * 3600 + minute * 60 + second


def _walk_forbidden_keys(value: Any, path: str = "case") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).strip().lower() in FORBIDDEN_TRUTH_KEYS:
                raise ValueError(f"Blinded input leaks truth field {path}.{key}")
            _walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]")


def load_blinded_cases(path: Path | str) -> BlindedCaseSet:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != BLINDED_DATASET_SCHEMA_VERSION:
        raise ValueError(f"Expected {BLINDED_DATASET_SCHEMA_VERSION} blinded dataset")
    dataset_id = str(payload.get("dataset_id") or "").strip()
    if not dataset_id:
        raise ValueError("Blinded benchmark dataset requires dataset_id")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Blinded benchmark dataset must contain a non-empty cases list")
    seen = set()
    required_chart = {"date", "latitude", "longitude", "timezone"}
    for case in cases:
        _walk_forbidden_keys(case)
        case_id = str(case.get("id") or "").strip()
        if not case_id or case_id in seen:
            raise ValueError(f"Every benchmark case needs a unique non-empty id: {case_id!r}")
        seen.add(case_id)
        if case.get("split") not in {"development", "holdout"}:
            raise ValueError(f"{case_id}: split must be development or holdout")
        if case.get("window_strategy") not in {
            "pre_recorded_uncertainty", "blinded_uniform_truth_position"
        }:
            raise ValueError(
                f"{case_id}: window_strategy must be pre_recorded_uncertainty or "
                "blinded_uniform_truth_position"
            )
        chart = case.get("chart") or {}
        missing = required_chart.difference(chart)
        if missing:
            raise ValueError(f"{case_id}: chart missing fields {sorted(missing)}")
        if "time" in chart:
            raise ValueError(f"{case_id}: blinded chart must not contain a birth time")
        start = _time_seconds(case.get("window_start_local"))
        end = _time_seconds(case.get("window_end_local"))
        if end < start:
            raise ValueError(f"{case_id}: benchmark windows cannot cross midnight")
        if end - start > 120 * 60:
            raise ValueError(f"{case_id}: Phase 1 benchmark windows cannot exceed 120 minutes")
        events = case.get("events")
        if not isinstance(events, list) or len(events) < 4:
            raise ValueError(f"{case_id}: blind validation requires at least four dated events")
        normalized_events = []
        for event in events:
            try:
                normalized = CreateRectificationEventRequest(**event).model_dump(mode="json")
            except ValueError as exc:
                raise ValueError(f"{case_id}: invalid event: {exc}") from exc
            normalized["id"] = event.get("id")
            normalized_events.append(normalized)
        case["events"] = normalized_events
    return BlindedCaseSet(cases, dataset_id, str(payload.get("cohort_status") or ""))


def load_truth_vault(path: Path | str) -> TruthVault:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != TRUTH_VAULT_SCHEMA_VERSION:
        raise ValueError(f"Expected {TRUTH_VAULT_SCHEMA_VERSION} truth vault")
    dataset_id = str(payload.get("dataset_id") or "").strip()
    if not dataset_id:
        raise ValueError("Truth vault requires dataset_id")
    rows = payload.get("truth")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Truth vault must contain a non-empty truth list")
    truth: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        case_id = str(row.get("id") or "").strip()
        if not case_id or case_id in truth:
            raise ValueError(f"Every truth row needs a unique non-empty id: {case_id!r}")
        verified = str(row.get("verified_local_time") or "")
        _time_seconds(verified)
        if not str(row.get("verification_source") or "").strip():
            raise ValueError(f"{case_id}: verification_source is required")
        truth[case_id] = dict(row)
    return TruthVault(truth, dataset_id, str(payload.get("cohort_status") or ""))


class CapturingEvaluator:
    def __init__(self, delegate: Any):
        self.delegate = delegate
        self.candidates: List[CandidateEvaluation] = []

    def evaluate(self, **kwargs) -> CandidateEvaluation:
        result = self.delegate.evaluate(**kwargs)
        self.candidates.append(result)
        return result


@dataclass(frozen=True)
class BlindPrediction:
    case_id: str
    split: str
    result: Dict[str, Any]
    candidates: Tuple[CandidateEvaluation, ...]
    duration_ms: float


def _profile_score(candidate: CandidateEvaluation, layers: Sequence[str]) -> float:
    weighted_total = 0.0
    weight_total = 0.0
    for event in candidate.details.get("events") or ():
        weight = float(event.get("reliability_weight") or 0.0)
        score = sum(
            float((event.get(LAYER_KEYS[layer]) or {}).get("score") or 0.0)
            for layer in layers
        )
        maximum = sum(
            float((event.get(LAYER_KEYS[layer]) or {}).get("maximum") or 0.0)
            for layer in layers
        )
        normalized = 100.0 * score / maximum if maximum else 0.0
        weighted_total += normalized * weight
        weight_total += weight
    return weighted_total / weight_total if weight_total else 0.0


def _profile_winners(
    candidates: Sequence[CandidateEvaluation], layers: Sequence[str]
) -> Dict[str, Any]:
    scored = [(candidate, _profile_score(candidate, layers)) for candidate in candidates]
    scored.sort(key=lambda row: (-row[1], row[0].local_time))
    best_score = scored[0][1]
    tied = [row[0].local_time for row in scored if math.isclose(row[1], best_score, abs_tol=1e-9)]
    return {
        "selected_local_time": scored[0][0].local_time,
        "winning_local_times": tied,
        "relative_fit": round(best_score, 3),
        "tie_count": len(tied),
    }


def _event_boundary_signature(event: Mapping[str, Any]) -> Dict[str, Any]:
    kp_rows = (event.get("kp_confirmation") or {}).get("cusp_promise") or ()
    transit_rows = (event.get("transit_confirmation") or {}).get("contacts") or ()
    return {
        "dasha": (event.get("dasha_delivery") or {}).get("active_lords") or {},
        "kp_cusps": [
            [row.get("house"), row.get("sub_lord"), bool(row.get("supports"))]
            for row in kp_rows
        ],
        "transit_contacts": [
            [row.get("planet"), row.get("contacted_anchor_houses") or []]
            for row in transit_rows
        ],
        "layer_scores": {
            layer: round(float((event.get(key) or {}).get("score") or 0.0), 3)
            for layer, key in LAYER_KEYS.items()
        },
    }


def analyze_candidate_boundaries(candidates: Sequence[CandidateEvaluation]) -> Dict[str, Any]:
    """Describe evidence changes between adjacent candidate minutes."""
    transitions = []
    component_counts: Dict[str, int] = defaultdict(int)
    for left, right in zip(candidates, candidates[1:]):
        changed = []
        left_details, right_details = left.details, right.details
        if left_details.get("d1_ascendant_sign") != right_details.get("d1_ascendant_sign"):
            changed.append("d1_ascendant_sign")
        left_vargas = left_details.get("varga_ascendants") or {}
        right_vargas = right_details.get("varga_ascendants") or {}
        for division in sorted(set(left_vargas).union(right_vargas)):
            if (left_vargas.get(division) or {}).get("sign") != (
                right_vargas.get(division) or {}
            ).get("sign"):
                changed.append(f"{division}_ascendant_sign")
        event_changes = []
        left_events = left_details.get("events") or ()
        right_events = right_details.get("events") or ()
        for index, (left_event, right_event) in enumerate(zip(left_events, right_events)):
            before = _event_boundary_signature(left_event)
            after = _event_boundary_signature(right_event)
            fields = [field for field in before if before[field] != after[field]]
            if fields:
                event_changes.append({
                    "event_index": index,
                    "event_id": right_event.get("event_id"),
                    "event_type": right_event.get("event_type"),
                    "changed": fields,
                })
                changed.extend(fields)
        score_delta = round(float(right.score) - float(left.score), 3)
        fingerprint_changed = left.fingerprint != right.fingerprint
        if changed or fingerprint_changed or score_delta:
            unique_changed = sorted(set(changed))
            for component in unique_changed:
                component_counts[component] += 1
            transitions.append({
                "after_local_time": right.local_time,
                "from_local_time": left.local_time,
                "score_before": left.score,
                "score_after": right.score,
                "score_delta": score_delta,
                "fingerprint_changed": fingerprint_changed,
                "changed_components": unique_changed,
                "event_changes": event_changes,
            })
    plateau_lengths = []
    current = 1
    for left, right in zip(candidates, candidates[1:]):
        if left.fingerprint == right.fingerprint:
            current += 1
        else:
            plateau_lengths.append(current)
            current = 1
    if candidates:
        plateau_lengths.append(current)
    score_values = [candidate.score for candidate in candidates]
    return {
        "candidate_count": len(candidates),
        "unique_evidence_profiles": len({candidate.fingerprint for candidate in candidates}),
        "evidence_boundary_count": len(transitions),
        "component_boundary_counts": dict(sorted(component_counts.items())),
        "longest_identical_plateau_candidates": max(plateau_lengths, default=0),
        "median_identical_plateau_candidates": round(median(plateau_lengths), 3) if plateau_lengths else 0,
        "score_range": round(max(score_values) - min(score_values), 3) if score_values else 0.0,
        "transitions": transitions,
    }


def predict_blinded_cases(
    cases: Sequence[Mapping[str, Any]],
    *,
    split: Optional[str] = None,
    minute_step: int = 1,
    evaluator_factory: Optional[Callable[[], Any]] = None,
) -> List[BlindPrediction]:
    """Run predictions without accepting or loading any verified birth times."""
    selected = [case for case in cases if split is None or case.get("split") == split]
    if not selected:
        raise ValueError(f"No benchmark cases selected for split={split!r}")
    predictions: List[BlindPrediction] = []
    for case in selected:
        _walk_forbidden_keys(case)
        chart_input = dict(case["chart"])
        chart_input["time"] = str(case["window_start_local"])
        evaluator = CapturingEvaluator(
            evaluator_factory() if evaluator_factory else SparseAstrologyEvaluator()
        )
        started = perf_counter()
        result = RectificationEngine(evaluator=evaluator).run(
            chart_input=chart_input,
            events=case["events"],
            window_start_seconds=_time_seconds(case["window_start_local"]),
            window_end_seconds=_time_seconds(case["window_end_local"]),
            minute_step=minute_step,
        )
        predictions.append(BlindPrediction(
            case_id=str(case["id"]),
            split=str(case["split"]),
            result=result,
            candidates=tuple(evaluator.candidates),
            duration_ms=round((perf_counter() - started) * 1000.0, 3),
        ))
    return predictions


def _shift_iso_date(value: Any, days: int) -> str:
    resolved = datetime.fromisoformat(str(value)[:10]).date() + timedelta(days=days)
    return resolved.isoformat()


def build_date_jitter_cases(
    cases: Sequence[Mapping[str, Any]], days: int
) -> BlindedCaseSet:
    """Shift every event interval without exposing or consulting birth-time truth."""
    if not days:
        raise ValueError("Date jitter must be non-zero")
    shifted = deepcopy(list(cases))
    for case in shifted:
        for event in case.get("events") or ():
            original_start = event["date_start"]
            original_end = event.get("date_end") or original_start
            event["date_start"] = _shift_iso_date(original_start, days)
            event["date_end"] = _shift_iso_date(original_end, days)
    return BlindedCaseSet(
        shifted,
        getattr(cases, "dataset_id", ""),
        getattr(cases, "cohort_status", ""),
    )


def build_cross_chart_event_control(
    cases: Sequence[Mapping[str, Any]],
) -> BlindedCaseSet:
    """Rotate complete event histories across charts as a negative control."""
    if len(cases) < 2:
        raise ValueError("Cross-chart event control requires at least two cases")
    rotated = deepcopy(list(cases))
    source_events = [deepcopy(case.get("events") or []) for case in cases]
    for index, case in enumerate(rotated):
        case["events"] = source_events[(index + 1) % len(source_events)]
    return BlindedCaseSet(
        rotated,
        getattr(cases, "dataset_id", ""),
        getattr(cases, "cohort_status", ""),
    )


def build_same_type_date_rotation_control(
    cases: Sequence[Mapping[str, Any]],
) -> BlindedCaseSet:
    """Swap dates across charts while preserving each event type and case shape."""
    if len(cases) < 2:
        raise ValueError("Same-type date rotation requires at least two cases")
    rotated = deepcopy(list(cases))
    groups: Dict[str, List[Tuple[int, int]]] = defaultdict(list)
    for case_index, case in enumerate(cases):
        for event_index, event in enumerate(case.get("events") or ()):
            groups[str(event.get("event_type") or "")].append((case_index, event_index))
    changed = 0
    for positions in groups.values():
        if len(positions) < 2:
            continue
        # Choose a bijective cyclic permutation that maximizes cross-chart
        # assignments. Every source date is consumed exactly once; unequal
        # event counts therefore cannot duplicate one foreign date many times.
        offsets = range(1, len(positions))
        best_offset = max(offsets, key=lambda offset: (
            sum(
                positions[(index + offset) % len(positions)][0] != target_case
                for index, (target_case, _) in enumerate(positions)
            ),
            -offset,
        ))
        for position_index, (target_case, target_event) in enumerate(positions):
            source_position = positions[(position_index + best_offset) % len(positions)]
            if source_position == (target_case, target_event):
                continue
            source_case, source_event = source_position
            source = cases[source_case]["events"][source_event]
            target = rotated[target_case]["events"][target_event]
            target["date_start"] = source["date_start"]
            target["date_end"] = source.get("date_end") or source["date_start"]
            target["precision"] = source.get("precision")
            target["source_reliability"] = source.get("source_reliability")
            changed += 1
    if not changed:
        raise ValueError("No event type occurs across two different charts")
    return BlindedCaseSet(
        rotated,
        getattr(cases, "dataset_id", ""),
        getattr(cases, "cohort_status", ""),
    )


def _distance_seconds(a: str, b: str) -> int:
    return abs(_time_seconds(a) - _time_seconds(b))


def _interval_distance_seconds(value: str, start: str, end: str) -> int:
    stamp = _time_seconds(value)
    lower, upper = _time_seconds(start), _time_seconds(end)
    if lower <= stamp <= upper:
        return 0
    return min(abs(stamp - lower), abs(stamp - upper))


def _wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> List[float]:
    if total <= 0:
        return [0.0, 0.0]
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total) / denominator
    return [round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6)]


def _aggregate_profile(rows: Sequence[Mapping[str, Any]], profile: str) -> Dict[str, Any]:
    total = len(rows)
    selected_errors = [float(row["profiles"][profile]["selected_error_minutes"]) for row in rows]
    tie_errors = [float(row["profiles"][profile]["tie_aware_error_minutes"]) for row in rows]
    recovery = {}
    for threshold in RECOVERY_THRESHOLDS_MINUTES:
        selected_hits = sum(error <= threshold for error in selected_errors)
        tie_hits = sum(error <= threshold for error in tie_errors)
        recovery[str(threshold)] = {
            "selected_hits": selected_hits,
            "selected_rate": round(selected_hits / total, 6) if total else 0.0,
            "selected_wilson_95": _wilson_interval(selected_hits, total),
            "tie_aware_hits": tie_hits,
            "tie_aware_rate": round(tie_hits / total, 6) if total else 0.0,
            "tie_aware_wilson_95": _wilson_interval(tie_hits, total),
        }
    return {
        "cases": total,
        "mean_selected_error_minutes": round(sum(selected_errors) / total, 3) if total else None,
        "median_selected_error_minutes": round(median(selected_errors), 3) if selected_errors else None,
        "mean_tie_aware_error_minutes": round(sum(tie_errors) / total, 3) if total else None,
        "recovery": recovery,
    }


def _layer_preference_diagnostic(
    candidates: Sequence[CandidateEvaluation], verified: str, selected: str
) -> Dict[str, Any]:
    verified_candidate = min(
        candidates,
        key=lambda candidate: (
            _distance_seconds(candidate.local_time, verified), candidate.local_time
        ),
    )
    selected_candidate = next(
        candidate for candidate in candidates if candidate.local_time == selected
    )
    rows = []
    totals = {layer: 0.0 for layer in LAYER_KEYS}
    verified_events = verified_candidate.details.get("events") or ()
    selected_events = selected_candidate.details.get("events") or ()
    for verified_event, selected_event in zip(verified_events, selected_events):
        weight = float(selected_event.get("reliability_weight") or 0.0)
        layers = {}
        for layer, key in LAYER_KEYS.items():
            at_verified = float((verified_event.get(key) or {}).get("score") or 0.0)
            at_selected = float((selected_event.get(key) or {}).get("score") or 0.0)
            weighted_delta = (at_selected - at_verified) * weight
            totals[layer] += weighted_delta
            layers[layer] = {
                "at_verified": round(at_verified, 3),
                "at_selected": round(at_selected, 3),
                "selected_minus_verified": round(at_selected - at_verified, 3),
                "weighted_selected_minus_verified": round(weighted_delta, 3),
            }
        rows.append({
            "event_id": selected_event.get("event_id"),
            "event_type": selected_event.get("event_type"),
            "inspection_date_at_verified": verified_event.get("inspection_date"),
            "inspection_date_at_selected": selected_event.get("inspection_date"),
            "layers": layers,
        })
    return {
        "verified_time": verified,
        "nearest_evaluated_verified_time": verified_candidate.local_time,
        "selected_time": selected_candidate.local_time,
        "weighted_layer_preference_for_selected": {
            layer: round(value, 3) for layer, value in totals.items()
        },
        "events": rows,
    }


def score_predictions(
    predictions: Sequence[BlindPrediction],
    truth: Mapping[str, Mapping[str, Any]],
    *,
    dataset_hash: str,
    truth_hash: str,
    cohort_status: str = "",
) -> Dict[str, Any]:
    prediction_ids = {prediction.case_id for prediction in predictions}
    missing = sorted(prediction_ids.difference(truth))
    if missing:
        raise ValueError(f"Truth vault is missing benchmark ids: {', '.join(missing)}")
    cases: List[Dict[str, Any]] = []
    boundary_rows: Dict[str, Any] = {}
    for prediction in predictions:
        verified = str(truth[prediction.case_id]["verified_local_time"])
        profiles: Dict[str, Any] = {}
        for name, layers in ABLATION_PROFILES.items():
            winner = _profile_winners(prediction.candidates, layers)
            selected_error = _distance_seconds(winner["selected_local_time"], verified) / 60.0
            tie_error = min(
                _distance_seconds(candidate_time, verified)
                for candidate_time in winner["winning_local_times"]
            ) / 60.0
            profiles[name] = {
                **winner,
                "selected_error_minutes": round(selected_error, 3),
                "tie_aware_error_minutes": round(tie_error, 3),
            }
        candidate_times = [candidate.local_time for candidate in prediction.candidates]
        lower = _time_seconds(candidate_times[0])
        upper = _time_seconds(candidate_times[-1])
        midpoint = (lower + upper) / 2.0
        midpoint_time = min(
            candidate_times,
            key=lambda value: (abs(_time_seconds(value) - midpoint), _time_seconds(value)),
        )
        midpoint_error = _distance_seconds(midpoint_time, verified) / 60.0
        profiles["midpoint_baseline"] = {
            "selected_local_time": midpoint_time,
            "winning_local_times": [midpoint_time],
            "relative_fit": None,
            "tie_count": 1,
            "selected_error_minutes": round(midpoint_error, 3),
            "tie_aware_error_minutes": round(midpoint_error, 3),
        }
        best_window = prediction.result["best_window"]
        boundary_rows[prediction.case_id] = analyze_candidate_boundaries(prediction.candidates)
        layer_diagnostic = _layer_preference_diagnostic(
            prediction.candidates,
            verified,
            profiles["full"]["selected_local_time"],
        )
        cases.append({
            "id": prediction.case_id,
            "split": prediction.split,
            "verified_local_time": verified,
            "verification_rating": truth[prediction.case_id].get("verification_rating"),
            "duration_ms": prediction.duration_ms,
            "candidate_count": prediction.result["candidate_count"],
            "event_count": prediction.result["event_count"],
            "confidence_label": prediction.result["confidence_label"],
            "top_cluster_distance_minutes": round(
                _interval_distance_seconds(
                    verified, best_window["start_local_time"], best_window["end_local_time"]
                ) / 60.0,
                3,
            ),
            "profiles": profiles,
            "layer_preference_diagnostic": layer_diagnostic,
        })
    groups: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    groups["all"].extend(cases)
    for row in cases:
        groups[row["split"]].append(row)
    metrics = {
        group: {
            profile: _aggregate_profile(rows, profile)
            for profile in BENCHMARK_PROFILES
        }
        for group, rows in groups.items()
    }
    midpoint_comparison = {}
    for group, profiles in metrics.items():
        full = profiles["full"]
        baseline = profiles["midpoint_baseline"]
        midpoint_comparison[group] = {
            "cases": full["cases"],
            "mean_error_improvement_minutes": round(
                float(baseline["mean_selected_error_minutes"])
                - float(full["mean_selected_error_minutes"]),
                3,
            ),
            "recovery_rate_delta": {
                str(threshold): round(
                    full["recovery"][str(threshold)]["selected_rate"]
                    - baseline["recovery"][str(threshold)]["selected_rate"],
                    6,
                )
                for threshold in RECOVERY_THRESHOLDS_MINUTES
            },
            "full_beats_midpoint_mean_error": (
                float(full["mean_selected_error_minutes"])
                < float(baseline["mean_selected_error_minutes"])
            ),
        }
    cluster_metrics = {}
    for group, rows in groups.items():
        distances = [float(row["top_cluster_distance_minutes"]) for row in rows]
        cluster_metrics[group] = {
            "cases": len(rows),
            "mean_distance_minutes": round(sum(distances) / len(distances), 3) if distances else None,
            "recovery": {
                str(threshold): {
                    "hits": sum(distance <= threshold for distance in distances),
                    "rate": round(
                        sum(distance <= threshold for distance in distances) / len(distances), 6
                    ) if distances else 0.0,
                }
                for threshold in RECOVERY_THRESHOLDS_MINUTES
            },
        }
    boundary_component_totals: Dict[str, int] = defaultdict(int)
    for row in boundary_rows.values():
        for component, count in row["component_boundary_counts"].items():
            boundary_component_totals[component] += int(count)
    boundary_summary = {
        "cases": len(boundary_rows),
        "mean_unique_evidence_profiles": round(
            sum(row["unique_evidence_profiles"] for row in boundary_rows.values())
            / len(boundary_rows),
            3,
        ) if boundary_rows else None,
        "mean_score_range": round(
            sum(float(row["score_range"]) for row in boundary_rows.values()) / len(boundary_rows),
            3,
        ) if boundary_rows else None,
        "component_boundary_totals": dict(sorted(boundary_component_totals.items())),
    }
    layer_preference_totals = {layer: 0.0 for layer in LAYER_KEYS}
    for row in cases:
        preferences = row["layer_preference_diagnostic"][
            "weighted_layer_preference_for_selected"
        ]
        for layer in LAYER_KEYS:
            layer_preference_totals[layer] += float(preferences[layer])
    layer_diagnostic_summary = {
        "interpretation": (
            "Positive values mean the layer favored the selected minute over the "
            "recorded minute; this is diagnostic association, not causal attribution."
        ),
        "weighted_preference_for_selected_total": {
            layer: round(value, 3) for layer, value in layer_preference_totals.items()
        },
    }
    full = metrics["all"]["full"]
    for profile, values in metrics["all"].items():
        for threshold in RECOVERY_THRESHOLDS_MINUTES:
            key = str(threshold)
            values["recovery"][key]["delta_vs_full_selected"] = round(
                values["recovery"][key]["selected_rate"]
                - full["recovery"][key]["selected_rate"],
                6,
            )
    limitations = [
        "Retrospective recovery is not a probability for an individual chart.",
        "Development cases cannot be reported as untouched holdout evidence after rule tuning.",
        "Tie-aware recovery is reported separately so scoring plateaus do not inflate the selected winner.",
    ]
    if "unaudited" in cohort_status:
        limitations.insert(
            0,
            "Public seed event dates are not independently audited; results are diagnostic only.",
        )
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "engine_version": predictions[0].result.get("engine_version") if predictions else None,
        "registry_version": predictions[0].result.get("registry_version") if predictions else None,
        "result_kind": "retrospective_recovery_not_probability",
        "cohort_status": cohort_status or "unspecified",
        "blindness": {
            "predictions_completed_before_truth_loaded": True,
            "dataset_sha256": dataset_hash,
            "truth_vault_sha256": truth_hash,
        },
        "thresholds_minutes": list(RECOVERY_THRESHOLDS_MINUTES),
        "ablation_profiles": {key: list(value) for key, value in ABLATION_PROFILES.items()},
        "baselines": ["midpoint_baseline"],
        "metrics": metrics,
        "comparison_to_midpoint": midpoint_comparison,
        "top_cluster_metrics": cluster_metrics,
        "boundary_sensitivity": {
            "summary": boundary_summary,
            "cases": boundary_rows,
        },
        "layer_preference_diagnostics": layer_diagnostic_summary,
        "cases": cases,
        "limitations": limitations,
    }


def _compare_control_report(
    base: Mapping[str, Any], control: Mapping[str, Any]
) -> Dict[str, Any]:
    base_cases = {row["id"]: row for row in base["cases"]}
    control_cases = {row["id"]: row for row in control["cases"]}
    case_rows = []
    for case_id in sorted(base_cases):
        original = base_cases[case_id]["profiles"]["full"]
        changed = control_cases[case_id]["profiles"]["full"]
        case_rows.append({
            "id": case_id,
            "winner_displacement_minutes": round(
                _distance_seconds(
                    original["selected_local_time"], changed["selected_local_time"]
                ) / 60.0,
                3,
            ),
            "control_minus_original_error_minutes": round(
                float(changed["selected_error_minutes"])
                - float(original["selected_error_minutes"]),
                3,
            ),
            "original_minus_control_relative_fit": round(
                float(original["relative_fit"] or 0.0)
                - float(changed["relative_fit"] or 0.0),
                3,
            ),
        })
    return {
        "cases": len(case_rows),
        "original_mean_error_minutes": base["metrics"]["all"]["full"][
            "mean_selected_error_minutes"
        ],
        "control_mean_error_minutes": control["metrics"]["all"]["full"][
            "mean_selected_error_minutes"
        ],
        "control_minus_original_mean_error_minutes": round(
            float(control["metrics"]["all"]["full"]["mean_selected_error_minutes"])
            - float(base["metrics"]["all"]["full"]["mean_selected_error_minutes"]),
            3,
        ),
        "mean_winner_displacement_minutes": round(
            sum(row["winner_displacement_minutes"] for row in case_rows) / len(case_rows),
            3,
        ) if case_rows else None,
        "original_fit_exceeds_control_cases": sum(
            row["original_minus_control_relative_fit"] > 0 for row in case_rows
        ),
        "case_comparisons": case_rows,
    }


def _build_release_gate(report: Mapping[str, Any]) -> Dict[str, Any]:
    all_metrics = report["metrics"]["all"]
    holdout_cases = int((report["metrics"].get("holdout") or {}).get("full", {}).get("cases") or 0)
    full = all_metrics["full"]
    midpoint = all_metrics["midpoint_baseline"]
    controls = (report.get("robustness_controls") or {}).get("comparisons") or {}
    negative = controls.get("cross_chart_same_type_date_rotation")
    checks = {
        "minimum_total_cases_25": int(full["cases"]) >= 25,
        "minimum_untouched_holdout_cases_10": holdout_cases >= 10,
        "beats_midpoint_mean_error": (
            float(full["mean_selected_error_minutes"])
            < float(midpoint["mean_selected_error_minutes"])
        ),
        "recovery_within_15_minutes_at_least_50_percent": (
            float(full["recovery"]["15"]["selected_rate"]) >= 0.50
        ),
        "recovery_within_30_minutes_at_least_70_percent": (
            float(full["recovery"]["30"]["selected_rate"]) >= 0.70
        ),
        "type_preserving_negative_control_is_worse": bool(negative) and (
            float(negative["control_minus_original_mean_error_minutes"]) > 0
            and int(negative["original_fit_exceeds_control_cases"])
            >= math.ceil(0.75 * int(negative["cases"]))
        ),
    }
    return {
        "status": "eligible_for_limited_beta" if all(checks.values()) else "blocked",
        "use_rectified_time_enabled": False,
        "checks": checks,
        "note": (
            "Passing this gate permits only a limited research beta. Applying a rectified "
            "time remains disabled until chart revision is separately designed and validated."
        ),
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Birth-time rectification blind benchmark",
        "",
        f"Generated: {report['generated_at']}",
        f"Engine: `{report.get('engine_version')}` · Registry: `{report.get('registry_version')}`",
        "",
        "Predictions were completed before the verified-time vault was loaded.",
        "",
    ]
    for group, profiles in report["metrics"].items():
        lines.extend([f"## {group.title()} split", "", "| Profile | Cases | Mean error | ≤5m | ≤15m | ≤30m | ≤60m |", "|---|---:|---:|---:|---:|---:|---:|"])
        for profile, values in profiles.items():
            recovery = values["recovery"]
            lines.append(
                f"| {profile} | {values['cases']} | {values['mean_selected_error_minutes']} | "
                f"{recovery['5']['selected_rate']:.1%} | {recovery['15']['selected_rate']:.1%} | "
                f"{recovery['30']['selected_rate']:.1%} | {recovery['60']['selected_rate']:.1%} |"
            )
        lines.append("")
        comparison = report["comparison_to_midpoint"][group]
        lines.append(
            f"Full-engine mean-error improvement over midpoint: "
            f"{comparison['mean_error_improvement_minutes']} minutes."
        )
        lines.append("")
    lines.extend([
        "## Candidate-minute sensitivity",
        "",
        f"Mean distinct evidence profiles per case: "
        f"{report['boundary_sensitivity']['summary']['mean_unique_evidence_profiles']}. ",
        f"Mean score range: {report['boundary_sensitivity']['summary']['mean_score_range']}.",
        "",
        "A profile change identifies a calculation boundary; it does not establish that the "
        "boundary is astrologically predictive. Long identical plateaus mean the included "
        "evidence does not distinguish the minutes inside them.",
        "",
        "## Layer preference at the selected minute",
        "",
        report["layer_preference_diagnostics"]["interpretation"],
        "",
    ])
    for layer, value in report["layer_preference_diagnostics"][
        "weighted_preference_for_selected_total"
    ].items():
        lines.append(f"- {layer}: {value}")
    lines.append("")
    controls = (report.get("robustness_controls") or {}).get("comparisons") or {}
    if controls:
        lines.extend(["## Robustness controls", ""])
        for name, values in controls.items():
            lines.append(
                f"- `{name}`: mean error {values['control_mean_error_minutes']} minutes "
                f"(delta vs original {values['control_minus_original_mean_error_minutes']}); "
                f"mean winner displacement {values['mean_winner_displacement_minutes']} minutes."
            )
        lines.append("")
    gate = report.get("release_gate") or {}
    if gate:
        lines.extend([
            "## Release gate",
            "",
            f"Status: **{gate['status']}**. Applying a rectified time: "
            f"**{'enabled' if gate['use_rectified_time_enabled'] else 'disabled'}**.",
            "",
        ])
        for name, passed in gate["checks"].items():
            lines.append(f"- {'PASS' if passed else 'FAIL'} — {name}")
        lines.append("")
    lines.extend([
        "## Interpretation boundary",
        "",
        "These are retrospective recovery measurements, not individual probabilities. "
        "Do not tune rules on the holdout split and then continue calling it holdout evidence.",
        "",
    ])
    return "\n".join(lines)


def run_benchmark(
    *,
    cases_path: Path | str,
    truth_path: Path | str,
    split: Optional[str] = None,
    minute_step: int = 1,
    evaluator_factory: Optional[Callable[[], Any]] = None,
    robustness_controls: bool = False,
    jitter_days: Sequence[int] = (7, 30),
    reveal_holdout: bool = False,
    frozen_manifest_path: Path | str | None = None,
) -> Dict[str, Any]:
    cases_path, truth_path = Path(cases_path), Path(truth_path)
    cases = load_blinded_cases(cases_path)
    has_holdout = any(case.get("split") == "holdout" for case in cases)
    if has_holdout and (split == "holdout" or split is None) and not reveal_holdout:
        raise ValueError(
            "Holdout scoring is locked. Run development only, or explicitly set "
            "reveal_holdout=True after the cohort and rule profile are frozen."
        )
    if has_holdout and (split == "holdout" or split is None) and reveal_holdout:
        if frozen_manifest_path is None:
            raise ValueError(
                "Holdout scoring requires a frozen cohort manifest created before reveal."
            )
        # Local import avoids a module cycle: the freeze utility validates this
        # runner's case/truth schemas while the runner validates the freeze hash.
        from .cohort_freeze import validate_frozen_manifest
        validate_frozen_manifest(
            manifest_path=frozen_manifest_path,
            cases_path=cases_path,
            truth_path=truth_path,
        )
    predictions = predict_blinded_cases(
        cases, split=split, minute_step=minute_step, evaluator_factory=evaluator_factory
    )
    control_predictions: Dict[str, List[BlindPrediction]] = {}
    if robustness_controls:
        selected_cases = BlindedCaseSet(
            [case for case in cases if split is None or case.get("split") == split],
            cases.dataset_id,
            cases.cohort_status,
        )
        if len(selected_cases) >= 2:
            control_predictions["cross_chart_event_rotation"] = predict_blinded_cases(
                build_cross_chart_event_control(selected_cases),
                minute_step=minute_step,
                evaluator_factory=evaluator_factory,
            )
            control_predictions[
                "cross_chart_same_type_date_rotation"
            ] = predict_blinded_cases(
                build_same_type_date_rotation_control(selected_cases),
                minute_step=minute_step,
                evaluator_factory=evaluator_factory,
            )
        for days in sorted(set(int(value) for value in jitter_days if int(value) > 0)):
            for signed_days in (-days, days):
                key = f"event_date_jitter_{signed_days:+d}_days"
                control_predictions[key] = predict_blinded_cases(
                    build_date_jitter_cases(selected_cases, signed_days),
                    minute_step=minute_step,
                    evaluator_factory=evaluator_factory,
                )
    # Deliberate trust boundary: no truth file is opened until every prediction exists.
    truth = load_truth_vault(truth_path)
    if cases.dataset_id != truth.dataset_id:
        raise ValueError(
            f"Dataset id mismatch: blinded={cases.dataset_id!r}, truth={truth.dataset_id!r}"
        )
    if cases.cohort_status != truth.cohort_status:
        raise ValueError(
            f"Cohort status mismatch: blinded={cases.cohort_status!r}, "
            f"truth={truth.cohort_status!r}"
        )
    if split == "holdout" and "unaudited" in cases.cohort_status:
        raise ValueError("Unaudited public seed events cannot be reported as holdout evidence")
    report = score_predictions(
        predictions,
        truth,
        dataset_hash=hashlib.sha256(cases_path.read_bytes()).hexdigest(),
        truth_hash=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
        cohort_status=cases.cohort_status,
    )
    report["holdout_revealed"] = bool(has_holdout and (split == "holdout" or split is None))
    if control_predictions:
        report["robustness_controls"] = {
            "all_controls_predicted_before_truth_loaded": True,
            "comparisons": {},
        }
        for name, rows in control_predictions.items():
            control_report = score_predictions(
                rows,
                truth,
                dataset_hash=f"derived-control:{name}:{report['blindness']['dataset_sha256']}",
                truth_hash=report["blindness"]["truth_vault_sha256"],
                cohort_status=cases.cohort_status,
            )
            report["robustness_controls"]["comparisons"][name] = _compare_control_report(
                report, control_report
            )
    report["release_gate"] = _build_release_gate(report)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run blind birth-time rectification validation")
    parser.add_argument("--cases", required=True, help="Blinded cases JSON (must contain no true times)")
    parser.add_argument("--truth", required=True, help="Separate verified-time vault JSON")
    parser.add_argument("--split", choices=("development", "holdout"))
    parser.add_argument("--minute-step", type=int, default=1, choices=range(1, 6))
    parser.add_argument("--output", help="Write the full machine-readable JSON report here")
    parser.add_argument("--markdown", help="Write a human-readable Markdown report here")
    parser.add_argument(
        "--robustness-controls",
        action="store_true",
        help="Also run cross-chart event rotation and ±7/±30-day date jitter controls",
    )
    parser.add_argument(
        "--frozen-manifest",
        help="Private manifest binding audited cases/truth hashes before holdout reveal",
    )
    parser.add_argument(
        "--reveal-holdout",
        action="store_true",
        help="Explicitly score a preassigned holdout after cohort and rule profile are frozen",
    )
    args = parser.parse_args(argv)
    report = run_benchmark(
        cases_path=args.cases,
        truth_path=args.truth,
        split=args.split,
        minute_step=args.minute_step,
        robustness_controls=args.robustness_controls,
        reveal_holdout=args.reveal_holdout,
        frozen_manifest_path=args.frozen_manifest,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    if args.markdown:
        Path(args.markdown).write_text(render_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
