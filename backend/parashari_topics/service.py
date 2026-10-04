"""Reusable Topic Lens orchestration over existing canonical engines."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any, Dict, Iterable, Mapping, Protocol

from health_v2.natal_engine import NatalHealthBlueprintEngine
from health_v2.timing_engine import HealthTimingHeatmapEngine
from reports.context.base_context_builder import calculate_chart_for_birth, calculate_divisional_chart

from .registry import TopicDefinition, get_topic


SERVICE_VERSION = "parashari.topic-judgment/1.0.0"


def _list(value: Any) -> list:
    return list(value) if isinstance(value, (list, tuple)) else []


def _has_longitudes(chart: Mapping[str, Any]) -> bool:
    planets = chart.get("planets") or {}
    required = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
    return all(
        isinstance(planets.get(planet), dict)
        and planets[planet].get("longitude") is not None
        for planet in required
    )


def _unique_strings(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output


def _chart_signature(birth_data: Mapping[str, Any], profile: Mapping[str, Any] | None) -> str:
    fields = {
        key: birth_data.get(key)
        for key in ("id", "chart_id", "birth_chart_id", "date", "time", "latitude", "longitude", "timezone", "gender")
    }
    fields["calculation_profile"] = dict(profile or {})
    return hashlib.sha256(json.dumps(fields, sort_keys=True, default=str).encode()).hexdigest()


def _health_status(vulnerabilities: list[dict]) -> str:
    grades = {str(row.get("evidence_grade") or row.get("support_grade") or "").lower() for row in vulnerabilities}
    if "strong" in grades:
        return "established_with_strong_repetition"
    if "moderate" in grades:
        return "established_with_moderate_repetition"
    if vulnerabilities:
        return "directional_only"
    return "no_distinct_pattern"


def _health_headline(vulnerabilities: list[dict]) -> str:
    labels = _unique_strings((row.get("label") or row.get("title")) for row in vulnerabilities[:3])
    if not labels:
        return "No distinct natal health susceptibility was established"
    if len(labels) == 1:
        return labels[0]
    return f"The clearest natal patterns concern {', '.join(labels[:-1])} and {labels[-1]}"


def _health_contributor(row: Mapping[str, Any]) -> dict:
    return {
        "evidence_id": row.get("stable_id"),
        "title": row.get("label"),
        "description": row.get("description"),
        "claim_type": row.get("claim_type"),
        "evidence_grade": row.get("evidence_grade") or row.get("support_grade"),
        "planets": _list(row.get("source_planets")),
        "houses": _list(row.get("timing_houses")),
        "body_zones": _list(row.get("body_zones")),
        "confluence_count": int(row.get("confluence_count") or 0),
        "standing_weight": int(row.get("standing_weight") or 0),
        "primary_medical_factors": _list(row.get("primary_medical_factors")),
        "supporting_rules": _list(row.get("supporting_rules")),
        "protective_rules": _list(row.get("protective_rules")),
        "pressure_rules": _list(row.get("contradicting_rules")),
        "capacity_modifiers": _list(row.get("capacity_modifiers")),
        "d30_confirmation": dict(row.get("d30_confirmation") or {}),
        "eligible_for_timing": bool(row.get("eligible_for_timing")),
    }


def _health_overview_contributors(contributors: list[dict], limit: int = 4) -> list[dict]:
    """Keep body-area evidence visible beside authored condition patterns.

    Anatomical standing weights and authored condition grades are different
    evidence systems and should not compete in one flat sort. Reserve space
    for both and rank each group only by its own evidence fields.
    """
    if limit <= 0:
        return []
    grade = {"strong": 3, "moderate": 2, "directional": 1}
    anatomy = [row for row in contributors if row.get("claim_type") == "anatomical_vulnerability"]
    patterns = [row for row in contributors if row.get("claim_type") != "anatomical_vulnerability"]
    anatomy.sort(
        key=lambda row: (
            -grade.get(str(row.get("evidence_grade") or "").lower(), 0),
            -int(row.get("standing_weight") or 0),
            -int(row.get("confluence_count") or 0),
            -len(row.get("primary_medical_factors") or []),
            str(row.get("evidence_id") or ""),
        )
    )
    patterns.sort(
        key=lambda row: (
            -grade.get(str(row.get("evidence_grade") or "").lower(), 0),
            -len(row.get("supporting_rules") or []),
            str(row.get("evidence_id") or ""),
        )
    )
    anatomy_slots = min(len(anatomy), max(1, limit // 2)) if anatomy else 0
    pattern_slots = min(len(patterns), limit - anatomy_slots)
    if pattern_slots < limit - anatomy_slots:
        anatomy_slots = min(len(anatomy), limit - pattern_slots)
    return [*anatomy[:anatomy_slots], *patterns[:pattern_slots]]


def _health_overview_groups(contributors: list[dict], limit_each: int = 2) -> tuple[list[dict], list[dict]]:
    selected = _health_overview_contributors(contributors, limit_each * 2)
    anatomy = [row for row in selected if row.get("claim_type") == "anatomical_vulnerability"]
    patterns = [row for row in selected if row.get("claim_type") != "anatomical_vulnerability"]
    return anatomy, patterns


class TopicProvider(Protocol):
    """Adapter contract implemented once by each canonical topic engine."""

    def generate(
        self,
        *,
        topic: TopicDefinition,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any] | None,
        as_of: date,
        calculation_profile: Dict[str, str] | None,
    ) -> Dict[str, Any]: ...

    def timing(
        self,
        *,
        topic: TopicDefinition,
        birth_data: Dict[str, Any],
        start_date: date,
        days: int,
        chart_data: Dict[str, Any] | None,
        calculation_profile: Dict[str, str] | None,
    ) -> Dict[str, Any]: ...


class HealthTopicProvider:
    """Translate the existing Health V2 contracts into the shared topic contract."""

    def generate(
        self,
        *,
        topic: TopicDefinition,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any] | None = None,
        as_of: date | None = None,
        calculation_profile: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        return self._generate_health(
            topic=topic,
            birth_data=birth_data,
            chart_data=chart_data,
            as_of=as_of or date.today(),
            calculation_profile=calculation_profile,
        )

    def timing(
        self,
        *,
        topic: TopicDefinition,
        birth_data: Dict[str, Any],
        start_date: date,
        days: int,
        chart_data: Dict[str, Any] | None = None,
        calculation_profile: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        if days < 1 or days > 366:
            raise ValueError("days must be between 1 and 366")
        chart, blueprint = self._health_blueprint(birth_data, chart_data, calculation_profile)
        raw = HealthTimingHeatmapEngine(chart, blueprint, birth_data).calculate(start_date, days)
        return {
            "schema_version": "parashari.topic-timing.v1",
            "service_version": SERVICE_VERSION,
            "topic_id": topic.key,
            "topic_version": topic.version,
            "chart_signature": _chart_signature(birth_data, calculation_profile),
            "start_date": start_date.isoformat(),
            "days": days,
            "provider": {
                "key": "health_v2_timing",
                "schema_version": raw.get("schema_version"),
                "engine_version": raw.get("engine_version"),
                "methodology_version": raw.get("methodology_version"),
            },
            "result": raw,
        }

    def _health_blueprint(
        self,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any] | None,
        calculation_profile: Dict[str, str] | None,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        node_type = str((calculation_profile or {}).get("node_type") or "mean")
        chart = chart_data or calculate_chart_for_birth(birth_data, node_type=node_type)
        if not _has_longitudes(chart):
            raise ValueError("Complete planetary longitudes are required for the Health topic")
        divisions = {
            f"D{division}": calculate_divisional_chart(chart, division)["divisional_chart"]
            for division in (3, 9, 12, 30)
        }
        blueprint = NatalHealthBlueprintEngine(
            chart,
            divisions,
            gender=birth_data.get("gender"),
        ).calculate()
        return chart, blueprint

    def _generate_health(
        self,
        *,
        topic: TopicDefinition,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any] | None,
        as_of: date,
        calculation_profile: Dict[str, str] | None,
    ) -> Dict[str, Any]:
        _chart, blueprint = self._health_blueprint(birth_data, chart_data, calculation_profile)
        vulnerabilities = [dict(row) for row in _list(blueprint.get("vulnerabilities")) if isinstance(row, dict)]
        contributors = [_health_contributor(row) for row in vulnerabilities]
        overview_contributors = _health_overview_contributors(contributors)
        overview_body_areas, overview_named_patterns = _health_overview_groups(contributors)
        protective = _unique_strings(blueprint.get("protective_factors") or [])
        pressure = _unique_strings(blueprint.get("constitutional_pressure_factors") or [])
        source_references = _unique_strings(
            value.removeprefix("Source: ").strip()
            for row in vulnerabilities
            for value in _list(row.get("supporting_rules"))
            if str(value).startswith("Source:")
        )
        counter_evidence = [
            {
                "evidence_id": item["evidence_id"],
                "title": item["title"],
                "factors": item["pressure_rules"],
            }
            for item in contributors
            if item["pressure_rules"]
        ]
        return {
            "schema_version": "parashari.topic-judgment.v1",
            "service_version": SERVICE_VERSION,
            "topic_id": topic.key,
            "topic_version": topic.version,
            "registry_version": topic.public_dict()["registry_version"],
            "chart_signature": _chart_signature(birth_data, calculation_profile),
            "as_of": as_of.isoformat(),
            "topic": topic.public_dict(),
            "natal_promise": {
                "status": _health_status(vulnerabilities),
                "headline": _health_headline(overview_contributors),
                "summary": (
                    "These are natal susceptibility patterns already present in the chart. "
                    "Dasha and transit timing may activate an eligible pattern but cannot create one."
                ),
                "scope": blueprint.get("scope"),
                "finding_count": len(vulnerabilities),
                "timing_eligible_count": len(blueprint.get("eligible_vulnerability_ids") or []),
            },
            "primary_contributors": overview_contributors,
            "overview_body_areas": overview_body_areas,
            "overview_named_patterns": overview_named_patterns,
            "supporting_factors": protective,
            "obstructing_factors": pressure,
            "protective_factors": protective,
            "possible_manifestations": contributors,
            "alternative_manifestations": [],
            "counter_evidence": counter_evidence,
            "active_period": {
                "status": "not_loaded",
                "provider": "health_v2_timing",
                "message": "Open Timing to calculate the selected period.",
            },
            "timing_windows": {
                "status": "not_loaded",
                "provider": "health_v2_timing",
                "endpoint": "/api/parashari/topic-timing",
            },
            "available_timing_questions": [
                {
                    "key": row.key,
                    "label": row.label,
                    "description": row.description,
                    "provider": row.provider,
                    "event_key": row.event_key or None,
                }
                for row in topic.timing_questions
            ],
            "rule_trace": [
                {
                    "evidence_id": item["evidence_id"],
                    "title": item["title"],
                    "supporting_rules": item["supporting_rules"],
                    "protective_rules": item["protective_rules"],
                    "pressure_rules": item["pressure_rules"],
                    "capacity_modifiers": item["capacity_modifiers"],
                }
                for item in contributors
            ],
            "source_references": source_references,
            "provider": {
                "key": topic.provider,
                "schema_version": blueprint.get("schema_version"),
                "engine_version": blueprint.get("engine_version"),
                "methodology_version": blueprint.get("methodology_version"),
                "claim_policy": blueprint.get("claim_policy") or {},
            },
            "raw_sections": {
                "vitality_foundation": blueprint.get("vitality_foundation") or {},
                "constitutional_protection": blueprint.get("constitutional_protection") or {},
                "female_health": blueprint.get("female_health"),
                "sixth_house_chain": blueprint.get("sixth_house_chain") or {},
                "limitations": blueprint.get("limitations") or [],
            },
        }


class TopicJudgmentService:
    """Route topic requests to canonical engines through small provider adapters."""

    def __init__(self, providers: Mapping[str, TopicProvider] | None = None):
        self.providers: Mapping[str, TopicProvider] = providers or {
            "health_v2": HealthTopicProvider(),
        }

    def _provider(self, topic: TopicDefinition) -> TopicProvider:
        provider = self.providers.get(topic.provider)
        if provider is None:
            raise ValueError(f"No provider is registered for Parashari topic: {topic.key}")
        return provider

    def generate(
        self,
        *,
        topic_key: str,
        birth_data: Dict[str, Any],
        chart_data: Dict[str, Any] | None = None,
        as_of: date | None = None,
        calculation_profile: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        topic = get_topic(topic_key)
        return self._provider(topic).generate(
            topic=topic,
            birth_data=birth_data,
            chart_data=chart_data,
            as_of=as_of or date.today(),
            calculation_profile=calculation_profile,
        )

    def timing(
        self,
        *,
        topic_key: str,
        birth_data: Dict[str, Any],
        start_date: date,
        days: int,
        chart_data: Dict[str, Any] | None = None,
        calculation_profile: Dict[str, str] | None = None,
    ) -> Dict[str, Any]:
        topic = get_topic(topic_key)
        return self._provider(topic).timing(
            topic=topic,
            birth_data=birth_data,
            start_date=start_date,
            days=days,
            chart_data=chart_data,
            calculation_profile=calculation_profile,
        )
