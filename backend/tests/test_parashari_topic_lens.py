from __future__ import annotations

from datetime import date

from parashari_topics.registry import get_topic, public_topics
from parashari_topics.service import HealthTopicProvider, TopicJudgmentService


def _blueprint():
    return {
        "schema_version": "health.natal_blueprint.v2",
        "engine_version": "health-test",
        "methodology_version": "health-method-test",
        "scope": "natal_vulnerability_only",
        "claim_policy": {"timing_cannot_create_vulnerability": True},
        "eligible_vulnerability_ids": ["health.condition.digestive"],
        "protective_factors": ["Jupiter protects the Lagna"],
        "constitutional_pressure_factors": ["Saturn pressures the sixth-house chain"],
        "vitality_foundation": {"ascendant_sign": "Cancer", "ascendant_lord": "Moon"},
        "constitutional_protection": {"overall_resilience": {"status": "mixed"}},
        "female_health": None,
        "sixth_house_chain": {"sixth_house_sign": "Sagittarius"},
        "limitations": ["Not a medical diagnosis"],
        "vulnerabilities": [{
            "stable_id": "health.condition.digestive",
            "label": "Digestive and intestinal sensitivity",
            "description": "The authored chart pattern repeats the digestive field.",
            "claim_type": "named_classical_susceptibility",
            "evidence_grade": "strong",
            "source_planets": ["Moon", "Mercury"],
            "timing_houses": [6, 8],
            "body_zones": ["stomach", "intestines"],
            "supporting_rules": ["Source: Test reference", "Moon connects to the pattern"],
            "protective_rules": ["Jupiter supports recovery"],
            "contradicting_rules": ["Saturn adds pressure"],
            "capacity_modifiers": ["Mercury has ordinary dignity"],
            "eligible_for_timing": True,
        }],
    }


def test_health_is_first_active_topic_and_catalog_is_generic():
    health = get_topic("health")
    catalog = public_topics()

    assert health.provider == "health_v2"
    assert health.primary_charts == ("D1", "D30")
    assert catalog["schema_version"] == "parashari.topic-catalog.v1"
    assert [row["key"] for row in catalog["topics"]] == ["health"]
    assert catalog["topics"][0]["sections"] == ("overview", "promise", "timing", "why")


def test_health_topic_reuses_blueprint_and_keeps_timing_lazy(monkeypatch):
    provider = HealthTopicProvider()
    monkeypatch.setattr(
        provider,
        "_health_blueprint",
        lambda birth_data, chart_data, calculation_profile: ({"planets": {}}, _blueprint()),
    )
    service = TopicJudgmentService(providers={"health_v2": provider})

    result = service.generate(
        topic_key="health",
        birth_data={
            "birth_chart_id": 42,
            "date": "1990-01-01",
            "time": "10:00",
            "latitude": 28.6,
            "longitude": 77.2,
            "timezone": "Asia/Kolkata",
        },
        as_of=date(2026, 10, 3),
        calculation_profile={"ayanamsha": "lahiri", "node_type": "mean"},
    )

    assert result["schema_version"] == "parashari.topic-judgment.v1"
    assert result["topic_id"] == "health"
    assert result["natal_promise"]["status"] == "established_with_strong_repetition"
    assert result["natal_promise"]["timing_eligible_count"] == 1
    assert result["primary_contributors"][0]["evidence_id"] == "health.condition.digestive"
    assert result["active_period"]["status"] == "not_loaded"
    assert result["timing_windows"]["status"] == "not_loaded"
    assert {row["provider"] for row in result["available_timing_questions"]} == {
        "health_v2_timing", "event_windows",
    }
    assert result["source_references"] == ["Test reference"]
    assert result["provider"]["claim_policy"]["timing_cannot_create_vulnerability"] is True


def test_health_overview_ranks_anatomy_by_confluence_without_forcing_house_six_sign(monkeypatch):
    blueprint = _blueprint()
    blueprint["vulnerabilities"] = [
        *[
            {
                "stable_id": f"health.condition.named_{index}",
                "label": f"Named condition {index}",
                "claim_type": "named_classical_susceptibility",
                "evidence_grade": "strong" if index == 0 else "moderate",
                "eligible_for_timing": True,
            }
            for index in range(5)
        ],
        {
            "stable_id": "health.anatomy.knees",
            "label": "Knees anatomical vulnerability",
            "claim_type": "anatomical_vulnerability",
            "evidence_grade": "moderate",
            "body_zones": ["knees"],
            "standing_weight": 21,
            "confluence_count": 1,
            "primary_medical_factors": ["sixth_house_sign"],
            "eligible_for_timing": True,
        },
        {
            "stable_id": "health.anatomy.intestines",
            "label": "Intestinal anatomical vulnerability",
            "claim_type": "anatomical_vulnerability",
            "evidence_grade": "moderate",
            "body_zones": ["intestines"],
            "standing_weight": 35,
            "confluence_count": 3,
            "primary_medical_factors": ["sixth_lord_sign", "sixth_lord_nakshatra"],
            "eligible_for_timing": True,
        },
    ]
    provider = HealthTopicProvider()
    monkeypatch.setattr(
        provider,
        "_health_blueprint",
        lambda birth_data, chart_data, calculation_profile: ({"planets": {}}, blueprint),
    )

    result = TopicJudgmentService(providers={"health_v2": provider}).generate(
        topic_key="health",
        birth_data={"birth_chart_id": 42},
        as_of=date(2026, 10, 3),
    )

    assert len(result["primary_contributors"]) == 4
    assert result["primary_contributors"][0]["evidence_id"] == "health.anatomy.intestines"
    assert result["primary_contributors"][1]["evidence_id"] == "health.anatomy.knees"
    assert result["primary_contributors"][2]["evidence_id"] == "health.condition.named_0"
    assert [row["evidence_id"] for row in result["overview_body_areas"]] == [
        "health.anatomy.intestines", "health.anatomy.knees",
    ]
    assert result["overview_named_patterns"][0]["evidence_id"] == "health.condition.named_0"
    assert "Intestinal anatomical vulnerability" in result["natal_promise"]["headline"]
    assert len(result["possible_manifestations"]) == 7
    assert result["possible_manifestations"][0]["evidence_id"] == "health.condition.named_0"
