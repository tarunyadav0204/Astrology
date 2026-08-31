from datetime import datetime

from longevity.calculator import LongevityCalculator
from reports.context.base_context_builder import calculate_chart_for_birth


ABC_BIRTH = {
    "name": "ABC",
    "date": "1980-04-02",
    "time": "14:55",
    "latitude": 29.2396596,
    "longitude": 75.8174505,
    "timezone": "UTC+5:30",
    "place": "Hisar, Haryana, India",
    "gender": "Male",
}


def test_abc_does_not_report_an_alpayu_band_already_exceeded():
    chart = calculate_chart_for_birth(ABC_BIRTH)
    result = LongevityCalculator(ABC_BIRTH, chart).calculate(as_of=datetime(2026, 8, 30))

    compartment = result["verdict"]["compartment"]
    modification = compartment["classical_modifications"]
    saturn_rule = next(rule for rule in modification["rules"] if "saturn_hrasa" in rule["id"])
    ashtakavarga = next(pillar for pillar in result["pillars"] if pillar["id"] == "ashtakavarga")
    safeguards = result["safeguards"]

    assert compartment["pair_majority"] == "Madhyayu"
    assert compartment["label"] == "Madhyayu"
    assert compartment["range"] == "36–72"
    assert compartment["confidence"] == "Moderate"
    assert compartment["age_validation"] == {
        "applicable": True,
        "reconciled": True,
        "calculated_compartment": "Alpayu",
        "final_compartment": "Madhyayu",
        "completed_age": 46,
        "running_age": 47,
        "reason": "The Alpayu adjustment is contradicted by attained age 46; the unreduced Madhyayu majority is retained",
    }
    assert modification["calculated_final_compartment"] == "Alpayu"
    assert modification["final_compartment"] == "Madhyayu"
    assert saturn_rule["applied"] is True
    assert saturn_rule["used_in_final_verdict"] is False
    assert saturn_rule["validation_status"] == "contradicted_by_attained_age"
    assert saturn_rule["exception"] is None
    assert saturn_rule["calculated_effect"] == "Madhyayu → Alpayu"
    assert saturn_rule["final_verdict_effect"] == "Excluded; final compartment remains Madhyayu"
    assert ashtakavarga["title"] == "Ashtakavarga · 8th-house support (SAV)"
    assert ashtakavarga["verdict"] == "Below-average support"
    assert ashtakavarga["metrics"] == {
        "eighth_house_sav_bindus": 21,
        "standard_per_sign_reference": 28,
        "difference_from_reference": -7,
        "effect_on_lifespan_compartment": "None — supporting evidence only",
    }
    assert "not a lifespan in years" in ashtakavarga["detail"]
    assert safeguards["title"] == "BPHS early-life cancellation audit"
    assert safeguards["summary"] == "0 of 4 listed combinations fully satisfied; 3 partially satisfied"
    assert "not a current health-risk score" in safeguards["interpretation"]
    assert [rule["status"] for rule in safeguards["rules"]] == [
        "not_satisfied",
        "partially_satisfied",
        "partially_satisfied",
        "partially_satisfied",
    ]
    assert safeguards["rules"][1]["condition_checks"][0]["passed"] is False
    assert safeguards["rules"][1]["condition_checks"][1]["passed"] is True
    assert safeguards["rules"][2]["condition_checks"][0]["passed"] is True
    assert safeguards["rules"][2]["condition_checks"][1]["passed"] is False


def test_abc_keeps_the_classical_reduction_before_the_alpayu_ceiling():
    chart = calculate_chart_for_birth(ABC_BIRTH)
    result = LongevityCalculator(ABC_BIRTH, chart).calculate(as_of=datetime(2010, 8, 30))

    compartment = result["verdict"]["compartment"]
    assert compartment["label"] == "Alpayu"
    assert compartment["age_validation"]["reconciled"] is False
    assert compartment["age_validation"]["completed_age"] == 30


def test_parent_view_never_presents_a_direct_lifespan_compartment_or_child_age_khanda():
    chart = calculate_chart_for_birth(ABC_BIRTH)
    result = LongevityCalculator(ABC_BIRTH, chart, subject="mother").calculate(as_of=datetime(2026, 8, 30))

    compartment = result["verdict"]["compartment"]
    jaimini = next(pillar for pillar in result["pillars"] if pillar["id"] == "jaimini")

    assert compartment["label"] in {
        "Lower derived vitality support",
        "Moderate derived vitality support",
        "Higher derived vitality support",
    }
    assert compartment["classical_category"] in {"Alpayu", "Madhyayu", "Purnayu"}
    assert compartment["range"] is None
    assert compartment["is_direct_lifespan_estimate"] is False
    assert "does not calculate the parent's age or lifespan" in compartment["interpretation"]
    assert jaimini["verdict"] == compartment["label"]
    assert "not the parent's lifespan compartment" in jaimini["detail"]
    assert all(window["level"] != "critical" for window in result["crisis_windows"])
    assert all(window["khanda_boundary"]["status"] == "not_applicable" for window in result["crisis_windows"])
    assert all(window["khanda_boundary"]["age_at_start"] is None for window in result["crisis_windows"])
    assert all(window["khanda_boundary"]["age_at_end"] is None for window in result["crisis_windows"])
