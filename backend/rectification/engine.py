from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from app.kp.services.chart_service import KPChartService
from calculators.badhaka_calculator import BadhakaCalculator
from calculators.chart_calculator import ChartCalculator, _SWISSEPH_CHART_LOCK
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from prediction_engine.primitives import aspected_houses, ruled_houses
from shared.dasha_calculator import DashaCalculator

from .registry import (
    EVENT_DEFINITIONS,
    RECTIFICATION_REGISTRY_VERSION,
    RectificationEventDefinition,
    get_event_definition,
)


RECTIFICATION_ENGINE_VERSION = "rectification.engine.v2"
RECTIFICATION_RESULT_SCHEMA_VERSION = "rectification.result.v1"

LEVEL_WEIGHTS = {"mahadasha": 0.45, "antardasha": 0.70, "pratyantardasha": 1.0}
LEVEL_WEIGHT_TOTAL = sum(LEVEL_WEIGHTS.values())
PRECISION_WEIGHTS = {"exact_day": 1.0, "month": 0.80, "year": 0.55, "range": 0.70}
RELIABILITY_WEIGHTS = {
    "documented": 1.0,
    "confident_memory": 0.85,
    "approximate_memory": 0.60,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _house_lord(chart: Mapping[str, Any], house: int) -> str:
    ascendant_sign = int(float(chart["ascendant"]) / 30.0) % 12
    return BadhakaCalculator.SIGN_LORDS[(ascendant_sign + int(house) - 1) % 12]


def _relation_rows(chart: Mapping[str, Any], planet: str, houses: Iterable[int]) -> List[Dict[str, Any]]:
    planets = chart.get("planets") or {}
    placement = planets.get(planet)
    if not isinstance(placement, Mapping) or placement.get("house") is None:
        return []
    occupied = int(placement["house"])
    ruled = set(ruled_houses(dict(chart), planet))
    aspected = set(aspected_houses(planet, occupied))
    rows: List[Dict[str, Any]] = []
    for raw_house in houses:
        house = int(raw_house)
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


def _inspection_dates(event: Mapping[str, Any]) -> Tuple[date, ...]:
    start = date.fromisoformat(str(event["date_start"])[:10])
    end = date.fromisoformat(str(event.get("date_end") or event["date_start"])[:10])
    if start == end:
        return (start,)
    middle = start + timedelta(days=(end - start).days // 2)
    return tuple(dict.fromkeys((start, middle, end)))


def _event_weight(event: Mapping[str, Any]) -> float:
    precision = PRECISION_WEIGHTS.get(str(event.get("precision") or "range"), 0.60)
    reliability = RELIABILITY_WEIGHTS.get(
        str(event.get("source_reliability") or "approximate_memory"), 0.60
    )
    return round(precision * reliability, 4)


def _active_dashas(birth: Mapping[str, Any], inspection_date: date) -> Dict[str, str]:
    resolved = DashaCalculator().calculate_current_dashas(
        dict(birth), datetime.combine(inspection_date, time(hour=12)), strict=True
    )
    output: Dict[str, str] = {}
    for level in LEVEL_WEIGHTS:
        row = resolved.get(level) or {}
        planet = str(row.get("planet") or "")
        if not planet:
            raise RuntimeError(f"Rectification dasha calculation returned no {level}")
        output[level] = planet
    return output


def _group_strength(
    chart: Mapping[str, Any], dashas: Mapping[str, str], houses: Sequence[int]
) -> Tuple[float, List[Dict[str, Any]]]:
    if not houses:
        return 0.0, []
    evidence: List[Dict[str, Any]] = []
    matched_weight = 0.0
    for level, planet in dashas.items():
        rows = _relation_rows(chart, planet, houses)
        if not rows:
            continue
        level_weight = LEVEL_WEIGHTS[level]
        matched_weight += level_weight
        evidence.extend({"level": level, **row} for row in rows)
    return matched_weight / LEVEL_WEIGHT_TOTAL, evidence


def _transit_contact(
    chart: Mapping[str, Any], planet: str, longitude: float, houses: Sequence[int]
) -> List[int]:
    ascendant = float(chart["ascendant"])
    transit_house = RealTransitCalculator().calculate_house_from_longitude(longitude, ascendant)
    contacted = {transit_house, *aspected_houses(planet, transit_house)}
    return sorted(contacted.intersection(int(house) for house in houses))


@dataclass(frozen=True)
class CandidateEvaluation:
    local_time: str
    score: float
    weighted_score: float
    event_weight_total: float
    fingerprint: str
    details: Dict[str, Any]


class SparseAstrologyEvaluator:
    """Calculate only the supplied life-event dates for one birth-time candidate."""

    def __init__(self, transit_cache: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None):
        self.transit_cache = transit_cache if transit_cache is not None else {}

    def _transits_for(self, day: date, planets: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        key = day.isoformat()
        cache = self.transit_cache.setdefault(key, {})
        calculator = RealTransitCalculator()
        for planet in sorted(set(planets)):
            if planet not in cache:
                cache[planet] = calculator.get_planet_state(datetime.combine(day, time(hour=12)), planet)
        return cache

    def _structural_score(
        self, chart: Mapping[str, Any], definition: RectificationEventDefinition
    ) -> Tuple[float, Dict[str, Any]]:
        supporting = (*definition.transition_houses, *definition.outcome_houses)
        lord_links: List[Dict[str, Any]] = []
        for house in definition.anchor_houses:
            lord = _house_lord(chart, house)
            lord_links.extend(
                {"anchor_house": house, "anchor_lord": lord, **row}
                for row in _relation_rows(chart, lord, supporting)
            )
        karaka_links = [
            row
            for planet in definition.karakas
            for row in _relation_rows(chart, planet, definition.anchor_houses)
        ]
        score = (6.0 if lord_links else 0.0) + (4.0 if karaka_links else 0.0)
        return score, {
            "score": score,
            "maximum": 10.0,
            "anchor_lord_links": lord_links,
            "karaka_links": karaka_links,
        }

    def _dasha_score(
        self,
        chart: Mapping[str, Any],
        dashas: Mapping[str, str],
        definition: RectificationEventDefinition,
    ) -> Tuple[float, Dict[str, Any]]:
        anchor_strength, anchor = _group_strength(chart, dashas, definition.anchor_houses)
        transition_strength, transition = _group_strength(chart, dashas, definition.transition_houses)
        outcome_strength, outcome = _group_strength(chart, dashas, definition.outcome_houses)
        score = 20.0 * anchor_strength + 10.0 * transition_strength + 10.0 * outcome_strength
        contradictions = []
        if anchor_strength == 0:
            contradictions.append("No MD/AD/PD lord connects to the event anchor houses")
        if definition.transition_required and transition_strength == 0:
            contradictions.append("The event requires a transition signal, but none is dasha-connected")
        return score, {
            "score": round(score, 3),
            "maximum": 40.0,
            "active_lords": dict(dashas),
            "anchor": anchor,
            "transition": transition,
            "outcome": outcome,
            "contradictions": contradictions,
        }

    def _varga_score(
        self,
        varga_chart: Mapping[str, Any],
        dashas: Mapping[str, str],
        definition: RectificationEventDefinition,
    ) -> Tuple[float, Dict[str, Any]]:
        strength, evidence = _group_strength(varga_chart, dashas, definition.varga_houses)
        score = 20.0 * strength
        return score, {
            "score": round(score, 3),
            "maximum": 20.0,
            "chart": f"D{definition.varga}",
            "houses": list(definition.varga_houses),
            "connections": evidence,
        }

    def _transit_score(
        self,
        chart: Mapping[str, Any],
        day: date,
        definition: RectificationEventDefinition,
    ) -> Tuple[float, Dict[str, Any]]:
        planets = {"Jupiter", "Saturn", *definition.karakas}
        states = self._transits_for(day, planets)
        rows: List[Dict[str, Any]] = []
        for planet in sorted(planets):
            contacts = _transit_contact(
                chart, planet, float(states[planet]["longitude"]), definition.anchor_houses
            )
            if contacts:
                rows.append({"planet": planet, "contacted_anchor_houses": contacts})
        slow_hits = {row["planet"] for row in rows}.intersection({"Jupiter", "Saturn"})
        karaka_hit = any(row["planet"] in definition.karakas for row in rows)
        score = (5.0 * len(slow_hits)) + (5.0 if karaka_hit else 0.0)
        return min(score, 15.0), {
            "score": min(score, 15.0),
            "maximum": 15.0,
            "inspection_date": day.isoformat(),
            "contacts": rows,
            "double_transit": slow_hits == {"Jupiter", "Saturn"},
        }

    def _kp_score(
        self,
        kp_chart: Mapping[str, Any],
        dashas: Mapping[str, str],
        definition: RectificationEventDefinition,
    ) -> Tuple[float, Dict[str, Any]]:
        relevant = set(definition.relevant_houses)
        planet_sigs = kp_chart.get("planet_significators") or {}
        cusp_lords = kp_chart.get("cusp_lords") or {}
        cusp_rows: List[Dict[str, Any]] = []
        for house in definition.anchor_houses:
            lords = cusp_lords.get(house) or cusp_lords.get(str(house)) or {}
            sub_lord = str(lords.get("sub_lord") or "")
            signified = set(int(value) for value in (planet_sigs.get(sub_lord) or ()))
            matches = sorted(signified.intersection(relevant))
            cusp_rows.append({
                "house": house,
                "sub_lord": sub_lord,
                "signified_houses": sorted(signified),
                "matched_event_houses": matches,
                "supports": bool(matches),
            })
        dasha_rows: List[Dict[str, Any]] = []
        matched_level_weight = 0.0
        for level, planet in dashas.items():
            signified = set(int(value) for value in (planet_sigs.get(planet) or ()))
            matches = sorted(signified.intersection(relevant))
            if matches:
                matched_level_weight += LEVEL_WEIGHTS[level]
                dasha_rows.append({
                    "level": level,
                    "planet": planet,
                    "signified_houses": sorted(signified),
                    "matched_event_houses": matches,
                })
        promise_ratio = (
            sum(1 for row in cusp_rows if row["supports"]) / len(cusp_rows)
            if cusp_rows else 0.0
        )
        promise_score = 8.0 * promise_ratio
        dasha_coverage = matched_level_weight / LEVEL_WEIGHT_TOTAL
        dasha_score = 7.0 * dasha_coverage
        score = promise_score + dasha_score
        return score, {
            "score": round(score, 3),
            "maximum": 15.0,
            "cusp_promise": cusp_rows,
            "dasha_significators": dasha_rows,
            "cusp_promise_score": round(promise_score, 3),
            "dasha_significator_score": round(dasha_score, 3),
            "dasha_level_coverage": round(dasha_coverage, 4),
            "stream_veto": bool(cusp_rows) and promise_ratio == 0.0,
        }

    @staticmethod
    def _aggregate_inspection_rows(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
        """Avoid candidate-specific cherry-picking inside imprecise event ranges."""
        if len(rows) == 1:
            return {**deepcopy(dict(rows[0])), "inspection_aggregation": "exact_date"}
        representative = deepcopy(dict(rows[len(rows) // 2]))
        samples = []
        for row in rows:
            samples.append({
                "inspection_date": row["inspection_date"],
                "score": row["score"],
                "active_lords": (row["dasha_delivery"] or {}).get("active_lords") or {},
            })
        for key in (
            "structural_promise", "dasha_delivery", "varga_confirmation",
            "transit_confirmation", "kp_confirmation",
        ):
            scores = [float((row.get(key) or {}).get("score") or 0.0) for row in rows]
            representative[key]["score"] = round(sum(scores) / len(scores), 3)
            representative[key]["sample_scores"] = [
                {"inspection_date": row["inspection_date"], "score": round(score, 3)}
                for row, score in zip(rows, scores)
            ]
        representative["score"] = round(sum(
            float(representative[key]["score"])
            for key in (
                "structural_promise", "dasha_delivery", "varga_confirmation",
                "transit_confirmation", "kp_confirmation",
            )
        ), 3)
        representative["inspection_aggregation"] = "mean_across_uncertainty_range"
        representative["inspection_samples"] = samples
        return representative

    def evaluate(
        self,
        *,
        chart_input: Mapping[str, Any],
        candidate_time: str,
        events: Sequence[Mapping[str, Any]],
    ) -> CandidateEvaluation:
        birth = dict(chart_input)
        birth["time"] = candidate_time
        namespace = SimpleNamespace(**birth)
        with _SWISSEPH_CHART_LOCK:
            chart = ChartCalculator({}).calculate_chart(namespace)
            kp_chart = KPChartService.calculate_kp_chart(
                birth["date"], candidate_time, float(birth["latitude"]),
                float(birth["longitude"]), birth.get("timezone"),
            )

            vargas: Dict[int, Dict[str, Any]] = {}
            event_results: List[Dict[str, Any]] = []
            weighted_total = 0.0
            event_weight_total = 0.0
            fingerprint_rows: List[Any] = []
            event_type_counts: Dict[str, int] = {}
            for event in events:
                key = str(event["event_type"])
                event_type_counts[key] = event_type_counts.get(key, 0) + 1

            for event in events:
                definition = get_event_definition(str(event["event_type"]))
                occurrence_count = event_type_counts[definition.key]
                if definition.varga not in vargas:
                    vargas[definition.varga] = DivisionalChartCalculator(chart).calculate_divisional_chart(
                        definition.varga
                    )["divisional_chart"]
                inspection_rows: List[Dict[str, Any]] = []
                for inspection_date in _inspection_dates(event):
                    dashas = _active_dashas(birth, inspection_date)
                    structural_score, structural = self._structural_score(chart, definition)
                    raw_structural_score = structural_score
                    structural_score = structural_score / occurrence_count
                    structural.update({
                        "raw_score_before_occurrence_normalization": round(raw_structural_score, 3),
                        "occurrence_count": occurrence_count,
                        "score": round(structural_score, 3),
                    })
                    dasha_score, dasha = self._dasha_score(chart, dashas, definition)
                    varga_score, varga = self._varga_score(
                        vargas[definition.varga], dashas, definition
                    )
                    transit_score, transit = self._transit_score(chart, inspection_date, definition)
                    kp_score, kp = self._kp_score(kp_chart, dashas, definition)
                    raw_promise_score = float(kp["cusp_promise_score"])
                    normalized_promise_score = raw_promise_score / occurrence_count
                    kp_score = normalized_promise_score + float(kp["dasha_significator_score"])
                    kp.update({
                        "raw_cusp_promise_score": round(raw_promise_score, 3),
                        "occurrence_count": occurrence_count,
                        "cusp_promise_score": round(normalized_promise_score, 3),
                        "score": round(kp_score, 3),
                    })
                    score = structural_score + dasha_score + varga_score + transit_score + kp_score
                    row = {
                        "inspection_date": inspection_date.isoformat(),
                        "score": round(score, 3),
                        "structural_promise": structural,
                        "dasha_delivery": dasha,
                        "varga_confirmation": varga,
                        "transit_confirmation": transit,
                        "kp_confirmation": kp,
                    }
                    inspection_rows.append(row)
                best = self._aggregate_inspection_rows(inspection_rows)
                weight = _event_weight(event)
                weighted_total += float(best["score"]) * weight
                event_weight_total += weight
                fit = (
                    "strong" if best["score"] >= 70 else
                    "moderate" if best["score"] >= 50 else
                    "weak"
                )
                result = {
                    "event_id": event.get("id"),
                    "event_type": definition.key,
                    "event_label": definition.label,
                    "date_start": str(event["date_start"])[:10],
                    "date_end": str(event.get("date_end") or event["date_start"])[:10],
                    "precision": event.get("precision"),
                    "source_reliability": event.get("source_reliability"),
                    "reliability_weight": weight,
                    "fit": fit,
                    **best,
                }
                event_results.append(result)
                fingerprint_rows.append({
                    "event": definition.key,
                    "fit": fit,
                    "inspection_date": best["inspection_date"],
                    "dashas": best["dasha_delivery"]["active_lords"],
                    "kp_cusps": [
                        (row["house"], row["sub_lord"], row["supports"])
                        for row in best["kp_confirmation"]["cusp_promise"]
                    ],
                    "varga_asc": int(float(vargas[definition.varga]["ascendant"]) / 30.0),
                    "layer_scores": {
                        key: (best[layer] or {}).get("score")
                        for key, layer in {
                            "structural": "structural_promise",
                            "dasha": "dasha_delivery",
                            "varga": "varga_confirmation",
                            "transit": "transit_confirmation",
                            "kp": "kp_confirmation",
                        }.items()
                    },
                    "transit_contacts": [
                        (row["planet"], tuple(row["contacted_anchor_houses"]))
                        for row in best["transit_confirmation"]["contacts"]
                    ],
                })

        score = weighted_total / event_weight_total if event_weight_total else 0.0
        fingerprint_payload = {
            "d1_asc": int(float(chart["ascendant"]) / 30.0),
            "events": fingerprint_rows,
        }
        fingerprint = hashlib.sha256(_canonical_json(fingerprint_payload).encode("utf-8")).hexdigest()[:20]
        return CandidateEvaluation(
            local_time=candidate_time,
            score=round(score, 3),
            weighted_score=round(weighted_total, 3),
            event_weight_total=round(event_weight_total, 4),
            fingerprint=fingerprint,
            details={
                "candidate_local_time": candidate_time,
                "relative_fit": round(score, 3),
                "d1_ascendant": float(chart["ascendant"]),
                "d1_ascendant_sign": int(float(chart["ascendant"]) / 30.0),
                "varga_ascendants": {
                    f"D{division}": {
                        "longitude": float(varga["ascendant"]),
                        "sign": int(float(varga["ascendant"]) / 30.0),
                    }
                    for division, varga in sorted(vargas.items())
                },
                "events": event_results,
            },
        )


class RectificationEngine:
    version = RECTIFICATION_ENGINE_VERSION

    def __init__(self, evaluator: Optional[Any] = None):
        self.evaluator = evaluator or SparseAstrologyEvaluator()

    @staticmethod
    def candidate_times(start_seconds: int, end_seconds: int, minute_step: int = 1) -> Tuple[str, ...]:
        if not 0 <= int(start_seconds) <= int(end_seconds) < 86400:
            raise ValueError("Rectification window must be within one local civil day")
        if not 1 <= int(minute_step) <= 5:
            raise ValueError("minute_step must be between 1 and 5")
        step = int(minute_step) * 60
        seconds = list(range(int(start_seconds), int(end_seconds) + 1, step))
        if seconds[-1] != int(end_seconds):
            seconds.append(int(end_seconds))
        return tuple(
            f"{value // 3600:02d}:{(value % 3600) // 60:02d}:{value % 60:02d}"
            for value in seconds
        )

    @staticmethod
    def _cluster(candidates: Sequence[CandidateEvaluation]) -> List[Dict[str, Any]]:
        clusters: List[Dict[str, Any]] = []
        for candidate in candidates:
            if clusters and clusters[-1]["fingerprint"] == candidate.fingerprint:
                cluster = clusters[-1]
                cluster["end_local_time"] = candidate.local_time
                cluster["candidate_count"] += 1
                if candidate.score > cluster["best_candidate"]["relative_fit"]:
                    cluster["best_candidate"] = candidate.details
                cluster["minimum_fit"] = min(cluster["minimum_fit"], candidate.score)
                cluster["maximum_fit"] = max(cluster["maximum_fit"], candidate.score)
                continue
            clusters.append({
                "fingerprint": candidate.fingerprint,
                "start_local_time": candidate.local_time,
                "end_local_time": candidate.local_time,
                "candidate_count": 1,
                "minimum_fit": candidate.score,
                "maximum_fit": candidate.score,
                "best_candidate": candidate.details,
            })
        clusters.sort(
            key=lambda row: (
                -float(row["best_candidate"]["relative_fit"]),
                row["start_local_time"],
            )
        )
        for rank, cluster in enumerate(clusters, start=1):
            cluster["rank"] = rank
            cluster["relative_fit"] = cluster["best_candidate"]["relative_fit"]
        return clusters

    @staticmethod
    def _stability(candidates: Sequence[CandidateEvaluation], winner: Mapping[str, Any]) -> Dict[str, Any]:
        events = list((winner.get("best_candidate") or {}).get("events") or [])
        if len(events) < 2:
            return {"leave_one_event_out": None, "label": "insufficient_events"}
        winning_fingerprint = str(winner.get("fingerprint") or "")
        retained = 0
        for omitted in range(len(events)):
            ranked: List[Tuple[float, str]] = []
            for candidate in candidates:
                candidate_events = candidate.details.get("events") or []
                weighted = 0.0
                weights = 0.0
                for index, event in enumerate(candidate_events):
                    if index == omitted:
                        continue
                    weight = float(event.get("reliability_weight") or 0.0)
                    weighted += float(event.get("score") or 0.0) * weight
                    weights += weight
                ranked.append((weighted / weights if weights else 0.0, candidate.fingerprint))
            ranked.sort(key=lambda row: (-row[0], row[1]))
            if ranked and ranked[0][1] == winning_fingerprint:
                retained += 1
        ratio = retained / len(events)
        return {
            "leave_one_event_out": round(ratio, 3),
            "label": "stable" if ratio >= 0.75 else "sensitive",
        }

    def run(
        self,
        *,
        chart_input: Mapping[str, Any],
        events: Sequence[Mapping[str, Any]],
        window_start_seconds: int,
        window_end_seconds: int,
        minute_step: int = 1,
        progress: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        if len(events) < 2:
            raise ValueError("At least two dated life events are required")
        unsupported = sorted({
            str(event.get("event_type") or "")
            for event in events
            if str(event.get("event_type") or "") not in EVENT_DEFINITIONS
        })
        if unsupported:
            raise ValueError(f"Unsupported rectification event types: {', '.join(unsupported)}")
        times = self.candidate_times(window_start_seconds, window_end_seconds, minute_step)
        candidates: List[CandidateEvaluation] = []
        for index, candidate_time in enumerate(times, start=1):
            candidates.append(self.evaluator.evaluate(
                chart_input=chart_input,
                candidate_time=candidate_time,
                events=events,
            ))
            if progress:
                progress(index, len(times))
        chronological = sorted(candidates, key=lambda item: item.local_time)
        clusters = self._cluster(chronological)
        winner = clusters[0]
        stability = self._stability(candidates, winner)
        separation = (
            float(clusters[0]["relative_fit"]) - float(clusters[1]["relative_fit"])
            if len(clusters) > 1 else float(clusters[0]["relative_fit"])
        )
        if len(events) < 4:
            confidence_label = "insufficient_evidence"
        elif separation >= 8 and stability.get("label") == "stable":
            confidence_label = "clear_relative_leader"
        elif separation >= 3:
            confidence_label = "moderate_relative_leader"
        else:
            confidence_label = "multiple_plausible_windows"
        landscape = [
            {"local_time": item.local_time, "relative_fit": item.score, "fingerprint": item.fingerprint}
            for item in chronological
        ]
        return {
            "schema_version": RECTIFICATION_RESULT_SCHEMA_VERSION,
            "engine_version": self.version,
            "registry_version": RECTIFICATION_REGISTRY_VERSION,
            "result_kind": "relative_fit_not_probability",
            "candidate_count": len(candidates),
            "event_count": len(events),
            "confidence_label": confidence_label,
            "score_separation": round(separation, 3),
            "stability": stability,
            "best_window": {
                "start_local_time": winner["start_local_time"],
                "end_local_time": winner["end_local_time"],
                "best_local_time": winner["best_candidate"]["candidate_local_time"],
                "relative_fit": winner["relative_fit"],
            },
            "clusters": clusters[:10],
            "score_landscape": landscape,
            "disclaimer": (
                "This ranks astrological fit against the life events supplied. "
                "It does not independently prove an exact birth minute."
            ),
        }
