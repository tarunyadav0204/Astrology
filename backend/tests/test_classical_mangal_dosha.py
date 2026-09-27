from calculators.classical_mangal_dosha import (
    calculate_classical_mangal_dosha,
    calculate_mangal_pair_balance,
)
from calculators.yoga_calculator import YogaCalculator
from marriage_matching.manglik import ManglikAnalyzer
from marriage_matching.premium_report import build_static_compatibility_report


def chart(mars_sign, *, ascendant_sign=0, moon_sign=0, venus_sign=None, extra_planets=None):
    planets = {
        "Mars": {"sign": mars_sign, "longitude": mars_sign * 30.0 + 5.0},
        "Moon": {"sign": moon_sign, "longitude": moon_sign * 30.0 + 10.0},
    }
    if venus_sign is not None:
        planets["Venus"] = {"sign": venus_sign, "longitude": venus_sign * 30.0 + 15.0}
    planets.update(extra_planets or {})
    return {
        "ascendant": ascendant_sign * 30.0,
        "planets": planets,
    }


def test_primary_lagna_reading_uses_only_five_named_houses():
    for house in (1, 4, 7, 8, 12):
        result = calculate_classical_mangal_dosha(chart(house - 1))
        assert result["present"] is True, house
        assert result["mars_house"] == house
    for house in (2, 3, 5, 6, 9, 10, 11):
        assert calculate_classical_mangal_dosha(chart(house - 1))["present"] is False, house


def test_dhane_textual_reading_is_reported_without_being_merged():
    result = calculate_classical_mangal_dosha(chart(1))  # House 2 from Aries Lagna
    assert result["present"] is False
    assert result["textual_variants"][0]["matched"] is True
    assert result["textual_variants"][0]["material_difference"] is True
    assert result["status"] == "not_formed"


def test_dhane_reading_is_not_presented_as_a_distinct_result_for_shared_houses():
    result = calculate_classical_mangal_dosha(chart(7))  # House 8 in both readings
    variant = next(row for row in result["evidence"] if row["rule_id"] == "MS-DHANE-VARIANT")
    assert variant["matched"] is True
    assert variant["material_difference"] is False
    assert "same placement result" in variant["fact"]


def test_moon_and_venus_are_supplementary_and_do_not_change_verdict():
    # Mars H3 from Lagna, H4 from Moon, H7 from Venus.
    result = calculate_classical_mangal_dosha(chart(2, moon_sign=11, venus_sign=8))
    assert result["present"] is False
    assert result["from_moon"] is True
    assert result["from_venus"] is True
    assert result["references"]["navamsa_d9"]["used"] is False


def test_source_backed_benefic_condition_is_applied_without_severity_band():
    result = calculate_classical_mangal_dosha(chart(6))
    assert result["present"] is True
    assert result["severity"] == "Present"
    assert result["individual_exceptions"]["applied"] is False
    assert result["cancellation"]["has_cancellation"] is False

    protected = calculate_classical_mangal_dosha(chart(
        6,
        extra_planets={"Jupiter": {"sign": 2, "longitude": 65.0}},
    ))
    assert protected["placement_present"] is True
    assert protected["present"] is False
    assert protected["status"] == "protected"
    assert protected["individual_exceptions"]["matched_rules"] == [
        {"planet": "Jupiter", "relation": "aspect", "matched": True}
    ]


def test_waxing_moon_and_unafflicted_mercury_are_contextual_benefics():
    waxing_moon = calculate_classical_mangal_dosha(chart(
        6,
        moon_sign=0,
        extra_planets={"Sun": {"sign": 11, "longitude": 350.0}},
    ))
    assert any(row["planet"] == "Moon" for row in waxing_moon["benefic_condition"]["relations_to_mars"])

    mercury_with_mars = calculate_classical_mangal_dosha(chart(
        6,
        extra_planets={"Mercury": {"sign": 6, "longitude": 190.0}},
    ))
    assert mercury_with_mars["present"] is True
    assert mercury_with_mars["benefic_condition"]["nature_context"]["mercury_joined_malefics"] == ["Mars"]


def test_missing_required_data_is_explicitly_unavailable():
    result = calculate_classical_mangal_dosha({"planets": {}})
    assert result["available"] is False
    assert result["status"] == "unavailable"


def test_pair_balance_is_separate_from_natal_formation():
    formed = calculate_classical_mangal_dosha(chart(6))
    clear = calculate_classical_mangal_dosha(chart(2))
    both = calculate_mangal_pair_balance(formed, formed)
    one = calculate_mangal_pair_balance(formed, clear)
    assert both["balanced"] is True
    assert both["score_is_classical"] is False
    assert formed["present"] is True
    assert one["status"] == "one_sided"
    assert one["pair_cancellation"] is False


def test_yoga_api_facade_and_matching_client_share_the_canonical_contract():
    source_chart = chart(6)
    yoga_calculator = YogaCalculator.__new__(YogaCalculator)
    yoga_calculator.chart_data = source_chart
    yoga_result = yoga_calculator._check_mangal_dosha()
    matching_result = ManglikAnalyzer().analyze(source_chart, d9_chart={})
    assert yoga_result["method"] == "bphs_80_47_lagna_reading"
    assert matching_result["method"] == yoga_result["method"]
    assert matching_result["references"]["navamsa_d9"]["used"] is False


def test_matching_report_does_not_present_legacy_mangal_points():
    formed = calculate_classical_mangal_dosha(chart(6))
    pair = calculate_mangal_pair_balance(formed, formed)
    pair["classical_status"] = pair["status"]
    pair["status"] = "Compatible"
    report = build_static_compatibility_report(
        {
            "manglik": {"compatibility": pair},
            "profiles": {"boy": {}, "girl": {}},
            "ashtakoota": {},
            "relationship_indicators": {"cross_chart": {}},
            "timing_overlay": {},
            "recommendation": {},
            "evidence_summary": {},
        },
        {"name": "Person 1"},
        {"name": "Person 2"},
    )
    section = next(row for row in report["sections"] if row["key"] == "manglik_and_dosha_handling")
    assert not any("Pair score" in fact for fact in section["facts"])
    assert any("categorical" in fact for fact in section["facts"])
