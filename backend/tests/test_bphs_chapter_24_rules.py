import pytest

from classical_rules.bphs.chapter_24 import RULES, coverage, evaluate_chapter_24
from classical_rules.models import RuleInputUnavailable
from classical_rules.registry import evaluate_pack, get_pack


def _chart():
    return {
        "ascendant": 10.0,
        "planets": {
            "Sun": {"longitude": 125.0, "sign": 4, "degree": 5.0},
            "Moon": {"longitude": 45.0, "sign": 1, "degree": 15.0},
            "Mars": {"longitude": 92.0, "sign": 3, "degree": 2.0},
            "Mercury": {"longitude": 70.0, "sign": 2, "degree": 10.0},
            "Jupiter": {"longitude": 95.0, "sign": 3, "degree": 5.0},
            "Venus": {"longitude": 181.0, "sign": 6, "degree": 1.0},
            "Saturn": {"longitude": 300.0, "sign": 10, "degree": 0.0},
            "Rahu": {"longitude": 210.0, "sign": 7, "degree": 0.0},
            "Ketu": {"longitude": 30.0, "sign": 1, "degree": 0.0},
        },
    }


def test_all_144_placement_rules_and_strength_control_are_catalogued():
    result = coverage()
    assert len(RULES) == 144
    assert result == {
        "total_verses": 145,
        "catalogued_verses": 145,
        "placement_rules": 144,
        "interpretive_controls": 1,
        "missing_verses": [],
        "duplicate_verses": [],
    }


def test_chart_returns_exactly_one_classical_placement_for_each_house_lord():
    result = evaluate_chapter_24(_chart())
    assert len(result["matches"]) == 12
    assert {row["source_house"] for row in result["matches"]} == set(range(1, 13))
    first = result["matches"][0]
    assert first["lord"] == "Mars"
    assert first["occupied_house"] == 4
    assert first["source"]["reference"] == "BPHS 24.4"
    assert first["outcomes"]
    assert result["interpretive_control"]["reference"] == "BPHS 24.145"
    assert result["fallback_used"] is False


def test_lord_condition_is_chart_specific_and_exposed_without_a_score():
    result = evaluate_chapter_24(_chart())
    fifth = next(row for row in result["matches"] if row["source_house"] == 5)
    assert fifth["lord"] == "Sun"
    assert fifth["lord_condition"]["dignity"] == "moolatrikona"
    assert fifth["lord_condition"]["classification"] in {"supported", "mixed"}
    assert "score" not in fifth["lord_condition"]


def test_missing_chart_input_is_explicit_and_never_falls_back():
    with pytest.raises(RuleInputUnavailable, match="ascendant"):
        evaluate_chapter_24({"planets": {}})


def test_registry_exposes_and_evaluates_chapter_24():
    detail = get_pack("bphs", 24)
    assert detail["coverage"]["placement_rules"] == 144
    assert detail["rules"][0]["source"]["reference"] == "BPHS 24.1"
    result = evaluate_pack("bphs", 24, _chart())
    assert len(result["matches"]) == 12
