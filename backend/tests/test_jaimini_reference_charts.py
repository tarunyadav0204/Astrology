import pytest

from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.jaimini_chart_calculator import JaiminiChartCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator


def _chart():
    longitudes = {
        "Sun": 25.0,
        "Moon": 54.0,
        "Mars": 83.0,
        "Mercury": 112.0,
        "Jupiter": 141.0,
        "Venus": 140.0,
        "Saturn": 199.0,
        "Rahu": 222.0,
        "Ketu": 42.0,
        "Mandi": 5.0,
        "Gulika": 6.0,
    }
    return {
        "ascendant": 5.0,
        "ayanamsa": 24.0,
        "planets": {
            name: {
                "longitude": longitude,
                "sign": int(longitude // 30) % 12,
                "degree": longitude % 30,
                "house": int(longitude // 30) + 1,
                "retrograde": False,
            }
            for name, longitude in longitudes.items()
        },
    }


def test_karakamsha_and_swamsha_share_ak_d9_sign_but_use_different_frames():
    chart = _chart()
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)["divisional_chart"]
    expected_sign = d9["planets"]["Sun"]["sign"]
    calculator = JaiminiChartCalculator(chart, "Sun")

    karakamsha = calculator.calculate_karkamsa_chart()
    swamsha = calculator.calculate_swamsa_chart()

    assert karakamsha["karkamsa_sign"] == expected_sign
    assert swamsha["swamsa_sign"] == expected_sign
    assert karakamsha["calculation_basis"]["planetary_frame"] == "D1"
    assert swamsha["calculation_basis"]["planetary_frame"] == "D9"
    assert karakamsha["karkamsa_chart"]["planets"]["Sun"]["sign"] == chart["planets"]["Sun"]["sign"]
    assert swamsha["swamsa_chart"]["planets"]["Sun"]["sign"] == d9["planets"]["Sun"]["sign"]


def test_reference_charts_exclude_unrequested_upagrahas():
    calculator = JaiminiChartCalculator(_chart(), "Sun")

    karakamsha_planets = calculator.calculate_karkamsa_chart()["karkamsa_chart"]["planets"]
    swamsha_planets = calculator.calculate_swamsa_chart()["swamsa_chart"]["planets"]

    assert "Mandi" not in karakamsha_planets
    assert "Gulika" not in karakamsha_planets
    assert "Mandi" not in swamsha_planets
    assert "Gulika" not in swamsha_planets


def test_received_atmakaraka_is_validated_instead_of_silently_used():
    with pytest.raises(ValueError, match="Atmakaraka mismatch"):
        JaiminiChartCalculator(_chart(), "Moon").calculate_karkamsa_chart()


def test_eight_karaka_scheme_can_be_requested_explicitly():
    result = JaiminiChartCalculator(_chart(), "Sun", karaka_scheme="eight").calculate_swamsa_chart()
    assert result["karaka_scheme"] == "eight"
    assert result["atmakaraka"] == "Sun"


def test_legacy_interpretation_fields_are_factual_method_descriptions():
    calculator = JaiminiChartCalculator(_chart(), "Sun")
    assert calculator.get_karkamsa_interpretation(8).startswith("Karakamsha reference: D1 grahas")
    assert calculator.get_swamsa_interpretation(8).startswith("Swamsha reference: D9 grahas")


def test_legacy_swamsa_point_matches_the_dedicated_chart_reference_sign():
    chart = _chart()
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)["divisional_chart"]
    points = JaiminiPointCalculator(chart, d9, "Sun").calculate_jaimini_points()
    chart_result = JaiminiChartCalculator(chart, "Sun").calculate_swamsa_chart()

    assert points["swamsa_lagna"]["sign_id"] == chart_result["swamsa_sign"]
    assert points["swamsa_lagna"]["sign_id"] != int(d9["ascendant"] // 30)


def test_legacy_contract_does_not_fabricate_time_lagnas_without_birth_data():
    chart = _chart()
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)["divisional_chart"]
    points = JaiminiPointCalculator(chart, d9, "Sun").calculate_jaimini_points()

    assert points["hora_lagna"]["available"] is False
    assert points["ghatika_lagna"]["available"] is False
    assert points["hora_lagna"]["fallback_used"] is False
    assert "sign_id" not in points["hora_lagna"]
