from classical_rules.bphs.chapter_03 import (
    PASSAGE_GROUPS,
    PLANETARY_DOCTRINE,
    RULES,
    coverage,
    compile_chapter_03_facts,
    evaluate_chapter_03,
)
from classical_rules.facts import evaluate_fact_expression
from classical_rules.registry import evaluate_pack, get_pack, list_packs
from classical_rules.engine import ClassicalRuleEngine
from classical_rules.models import ClassicalRule, SourceProfile
import pytest


def _chart():
    return {
        "ascendant": 10.0,
        "planets": {
            "Sun": {"longitude": 10.0, "sign": 0, "degree": 10.0},
            "Moon": {"longitude": 45.0, "sign": 1, "degree": 15.0},
            "Mars": {"longitude": 92.0, "sign": 3, "degree": 2.0},
            "Mercury": {"longitude": 70.0, "sign": 2, "degree": 10.0},
            "Jupiter": {"longitude": 125.0, "sign": 4, "degree": 5.0},
            "Venus": {"longitude": 181.0, "sign": 6, "degree": 1.0},
            "Saturn": {"longitude": 300.0, "sign": 10, "degree": 0.0},
            "Rahu": {"longitude": 210.0, "sign": 7, "degree": 0.0},
            "Ketu": {"longitude": 30.0, "sign": 1, "degree": 0.0},
        },
    }


def test_chapter_three_coverage_has_no_missing_or_duplicate_verses():
    result = coverage()
    assert result["catalogued_verses"] == 74
    assert result["missing_verses"] == []
    assert result["duplicate_verses"] == []
    assert result["published_rules"] == 9


def test_every_executable_passage_has_a_real_published_rule():
    rule_keys = {rule.key for rule in RULES if rule.status == "published"}
    for passage in PASSAGE_GROUPS:
        if passage.executable:
            assert passage.rule_keys
            assert set(passage.rule_keys) <= rule_keys


def test_chapter_three_uses_external_witness_without_copying_restricted_text():
    for rule in RULES:
        assert rule.source.witness_url.startswith("https://")
        assert "external_reference_only" in rule.source.witness_policy
    assert PLANETARY_DOCTRINE["tissue"]["Moon"] == "blood"


def test_rule_engine_returns_traceable_deterministic_evidence():
    result = evaluate_chapter_03(_chart())
    by_key = {row["rule_key"]: row for row in result["results"]}
    nature = by_key["BPHS.3.11.NATURAL_NATURE"]
    assert nature["source"]["reference"] == "BPHS 3.11"
    moon = next(row for row in nature["evidence"]["planets"] if row["planet"] == "Moon")
    assert moon["phase"] == "waxing"
    assert moon["nature"] == "benefic"
    dignity = by_key["BPHS.3.49-50.DIGNITY"]
    assert dignity["evidence"]["planets"]["Sun"]["dignity"] == "exalted"


def test_birth_dependent_rules_fail_openly_without_a_fallback():
    result = evaluate_chapter_03(_chart())
    by_key = {row["rule_key"]: row for row in result["results"]}
    assert by_key["BPHS.3.66-70.TIME_UPAGRAHAS"]["applicability"] == "unavailable"
    assert "Birth date" in by_key["BPHS.3.66-70.TIME_UPAGRAHAS"]["reason"]
    assert result["fallback_used"] is False


def test_birth_dependent_rules_use_the_canonical_calculators_when_inputs_exist():
    birth = {
        "date": "1990-04-23", "time": "06:15:30",
        "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata",
    }
    result = evaluate_chapter_03(_chart(), birth)
    by_key = {row["rule_key"]: row for row in result["results"]}
    time_points = by_key["BPHS.3.66-70.TIME_UPAGRAHAS"]
    assert time_points["applicability"] == "matched"
    names = {row["name"] for row in time_points["evidence"]["points"]}
    assert "Gulika" in names
    assert "Mandi" not in names
    assert time_points["evidence"]["calculation_basis"]["fallback_used"] is False
    assert by_key["BPHS.3.71-74.PRANAPADA"]["applicability"] == "matched"


def test_nodes_are_not_silently_added_to_bphs_friendship_rule():
    result = evaluate_chapter_03(_chart())
    by_key = {row["rule_key"]: row for row in result["results"]}
    friendship = by_key["BPHS.3.55.NATURAL_FRIENDSHIP"]["evidence"]
    assert friendship["nodes_excluded"] is True
    assert "Rahu" not in friendship["matrix"]
    assert friendship["matrix"]["Sun"]["Moon"] == "friend"
    assert friendship["matrix"]["Sun"]["Mercury"] == "neutral"
    assert friendship["matrix"]["Sun"]["Venus"] == "enemy"
    assert friendship["matrix"]["Moon"]["Mercury"] == "friend"
    assert friendship["matrix"]["Moon"]["Mars"] == "neutral"


def test_registry_exposes_certified_packs_and_preserves_contract():
    packs = list_packs()
    assert [(row["work_key"], row["chapter"]) for row in packs] == [("bphs", 3), ("bphs", 24), ("bphs", 34)]
    result = evaluate_pack("BPHS", 3, _chart())
    assert result["chapter"] == 3
    assert result["fallback_used"] is False

    detail = get_pack("bphs", 3)
    assert detail["coverage"]["catalogued_verses"] == 74
    assert detail["rules"][0]["source"]["reference"] == "BPHS 3.11"
    assert "evaluator" not in detail["rules"][0]
    foundation = detail["passage_groups"][0]
    assert foundation["use_key"] == "methodological_foundation"
    assert "does not produce a chart match" in foundation["usage_explanation"]
    executable = next(row for row in detail["passage_groups"] if row["executable"])
    assert executable["use_key"] == "rule_engine"


def test_programming_errors_are_not_silently_reported_as_unavailable():
    def broken(_chart, _birth):
        raise RuntimeError("calculator bug")

    rule = ClassicalRule(
        "TEST.BROKEN", "Broken", SourceProfile(
            "test", "Test", 1, "Test", 1, 1, "https://example.invalid"
        ), "calculation", "natal", "published", "test.broken", broken,
    )
    with pytest.raises(RuntimeError, match="calculator bug"):
        ClassicalRuleEngine([rule]).evaluate(_chart())


def test_later_rules_can_consume_source_carrying_chapter_three_facts():
    facts = compile_chapter_03_facts(_chart())
    sun = facts.require("planet.Sun.dignity")
    assert sun.value == "exalted"
    assert sun.source_references == ("BPHS 3.49–50",)

    expression = {
        "op": "all",
        "children": [
            {"op": "fact", "key": "planet.Sun.dignity", "comparator": "in", "value": ["exalted", "moolatrikona"]},
            {"op": "fact", "key": "planet.Moon.natural_nature", "comparator": "equals", "value": "benefic"},
        ],
    }
    result = evaluate_fact_expression(expression, facts)
    assert result.matched is True
    assert result.status == "matched"
    assert {row["source_references"][0] for row in result.used_facts} == {"BPHS 3.11", "BPHS 3.49–50"}


def test_missing_fact_is_unavailable_and_cannot_be_inverted_into_a_match():
    facts = compile_chapter_03_facts(_chart())
    missing = {"op": "fact", "key": "house.1.classification", "comparator": "equals", "value": "kendra"}
    direct = evaluate_fact_expression(missing, facts)
    inverted = evaluate_fact_expression({"op": "not", "children": [missing]}, facts)
    assert direct.matched is None
    assert direct.status == "unavailable"
    assert inverted.matched is None
    assert inverted.status == "unavailable"
