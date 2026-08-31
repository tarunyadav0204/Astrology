import json
from datetime import datetime
from pathlib import Path

from longevity.validation import (
    ValidationConfig,
    _group_metrics,
    _shift_birth_time,
    evaluate_case,
    load_cases,
)


def test_seed_dataset_is_sourced_and_quality_rated():
    cases = load_cases()
    assert len(cases) == 5
    assert all(case["birth_rating"] in {"AA", "A"} for case in cases)
    assert all(case["source_url"].startswith("https://www.astro.com/") for case in cases)
    assert len({case["cause_group"] for case in cases}) > 1


def test_classical_registry_source_references_are_resolvable_and_disclosed():
    registry_path = Path(__file__).parents[1] / "longevity" / "classical_rule_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    bibliography_ids = {entry["id"] for entry in registry["bibliography"]}
    assert bibliography_ids
    assert all(entry["url"].startswith("https://") for entry in registry["bibliography"])

    for rule in registry["rules"]:
        if rule["status"] in {"source_locked", "translation_profile"}:
            assert rule.get("source_ids"), rule["id"]
            assert set(rule["source_ids"]) <= bibliography_ids


def test_group_metrics_normalize_event_capture_by_control_person_time():
    rows = [
        {"event_hit": True, "control_days": 100, "positive_control_days": 20, "compartment_contains_event_age": True, "birth_time_stable": True},
        {"event_hit": False, "control_days": 100, "positive_control_days": 20, "compartment_contains_event_age": False, "birth_time_stable": False},
    ]
    metrics = _group_metrics(rows, threshold=2)
    assert metrics["event_capture_rate"] == 0.5
    assert metrics["control_positive_rate"] == 0.2
    assert metrics["event_lift_over_control_person_time"] == 2.5


def test_birth_time_shift_crosses_midnight_without_losing_date():
    birth = {"date": "2000-01-02", "time": "00:05:00"}
    shifted = _shift_birth_time(birth, -15)
    assert shifted["date"] == "2000-01-01"
    assert shifted["time"] == "23:50:00"


def test_single_case_validation_emits_event_and_person_time_metrics():
    case = load_cases()[1]  # Elvis: AA-rated record.
    result = evaluate_case(
        case,
        ValidationConfig(
            observation_years=1,
            event_exclusion_days=30,
            convergence_threshold=2,
            birth_time_offsets_minutes=(0,),
        ),
    )
    assert result["event_date"] == "1977-08-16"
    assert result["control_days"] > 300
    assert 0 <= result["control_positive_rate"] <= 1
    assert result["event_confirmed_systems"] == sum(result["event_components"].values())
