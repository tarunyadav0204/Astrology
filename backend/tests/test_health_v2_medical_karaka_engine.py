from __future__ import annotations

import pytest

from health_v2.medical_karaka_engine import (
    MEDICAL_SYSTEM_RULES,
    MedicalKarakaEngine,
)


def _base_chart():
    return {
        "houses": [{"house": house, "sign": house - 1} for house in range(1, 13)],
        "planets": {
            "Sun": {"house": 1, "sign": 0},
            "Moon": {"house": 2, "sign": 1},
            "Mars": {"house": 3, "sign": 2},
            "Mercury": {"house": 4, "sign": 3},
            "Jupiter": {"house": 5, "sign": 4},
            "Venus": {"house": 7, "sign": 6},
            "Saturn": {"house": 10, "sign": 9},
            "Rahu": {"house": 11, "sign": 10},
            "Ketu": {"house": 5, "sign": 4},
        },
    }


def _raw(*, chain_zone: str | None = None):
    return {
        "house_map": [
            {"house": house, "residents": [], "aspecting_planets": []}
            for house in range(1, 13)
        ],
        "sixth_house_chain": {
            "sixth_house_sign_zones": [chain_zone] if chain_zone else [],
            "sixth_lord_sign_zones": [],
            "sixth_lord_house_zones": [],
            "sixth_lord_nakshatra_zones": [],
        },
    }


@pytest.mark.parametrize("rule", MEDICAL_SYSTEM_RULES, ids=lambda rule: rule.key)
def test_every_authored_system_requires_and_accepts_three_factor_confluence(rule):
    chart = _base_chart()
    primary = rule.primary_karakas[0]
    chart["planets"][primary] = {"house": 6, "sign": 5}
    chart["planets"][rule.supporting_karakas[0]] = {"house": 8, "sign": 7}
    result = MedicalKarakaEngine(chart, _raw(chain_zone=rule.zone_terms[0])).calculate()
    pattern = next(row for row in result if row["key"] == rule.key)

    assert {"primary_karaka", "anatomical_field", "illness_axis"} <= set(pattern["factor_classes"])
    assert len(pattern["evidence"]) >= 3
    assert pattern["source_references"]
    summary = pattern["summary"].lower()
    assert any(phrase in summary for phrase in ("does not", "without", "not a "))


@pytest.mark.parametrize("rule", MEDICAL_SYSTEM_RULES, ids=lambda rule: rule.key)
def test_pressured_karaka_alone_never_creates_a_system_finding(rule):
    chart = _base_chart()
    chart["planets"][rule.primary_karakas[0]] = {"house": 6, "sign": 5}
    keys = {row["key"] for row in MedicalKarakaEngine(chart, _raw()).calculate()}
    assert rule.key not in keys


def test_nodes_are_modifiers_and_never_primary_medical_karakas():
    assert all(
        "Rahu" not in rule.primary_karakas and "Ketu" not in rule.primary_karakas
        for rule in MEDICAL_SYSTEM_RULES
    )


def test_registry_covers_every_classical_planet_as_significator_or_pressure_modifier():
    authored = {
        planet
        for rule in MEDICAL_SYSTEM_RULES
        for planet in rule.primary_karakas + rule.supporting_karakas
    }
    # Rahu and Ketu are intentionally handled by pressure evaluation rather
    # than as organ significators capable of creating a finding.
    assert {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"} <= authored


def test_female_chart_gets_a_distinct_menstrual_cycle_assessment():
    chart = _base_chart()
    chart["planets"]["Moon"] = {"house": 2, "sign": 1}
    chart["planets"]["Mars"] = {"house": 2, "sign": 1}
    chart["planets"]["Venus"] = {"house": 6, "sign": 5}
    raw = _raw()
    raw["house_map"][1]["residents"] = ["Moon", "Mars"]
    raw["house_map"][1]["aspecting_planets"] = ["Saturn"]
    raw["house_map"][5]["residents"] = ["Venus"]
    raw["house_map"][7]["aspecting_planets"] = ["Saturn"]

    assessment = MedicalKarakaEngine(chart, raw, gender="Female").menstrual_cycle_assessment()

    assert assessment is not None
    assert assessment["analyzed"] is True
    assert assessment["status"] == "heightened_attention"
    assert assessment["factor_groups"]["moon_cycle"] is True
    assert assessment["factor_groups"]["mars_blood_flow"] is True
    assert assessment["factor_groups"]["venus_reproductive"] is True
    assert assessment["factor_groups"]["reproductive_anatomy"] is True


def test_menstrual_cycle_assessment_is_not_invented_for_a_non_female_chart():
    assert MedicalKarakaEngine(_base_chart(), _raw(), gender="Male").menstrual_cycle_assessment() is None


def test_moon_saturn_and_venus_mars_in_eighth_is_not_mislabeled_no_pattern():
    chart = _base_chart()
    chart["planets"]["Moon"] = {"house": 2, "sign": 1}
    chart["planets"]["Saturn"] = {"house": 2, "sign": 1}
    chart["planets"]["Mars"] = {"house": 8, "sign": 7}
    chart["planets"]["Venus"] = {"house": 8, "sign": 7}
    # Reproduce a shared health map without resident rows. The dedicated
    # assessment must still recognize actual H8 occupation from the chart.
    assessment = MedicalKarakaEngine(chart, _raw(), gender="Female").menstrual_cycle_assessment()

    assert assessment is not None
    assert assessment["status"] == "heightened_attention"
    assert assessment["factor_groups"] == {
        "moon_cycle": True,
        "mars_blood_flow": True,
        "venus_reproductive": True,
        "reproductive_anatomy": True,
        "illness_axis": True,
    }
    assert "reproductive_anatomy" in assessment["active_factor_groups"]
    assert any("Venus occupies House 8" in line for line in assessment["evidence"])
