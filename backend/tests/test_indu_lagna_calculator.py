from __future__ import annotations

import pytest

from calculators.indu_lagna_calculator import InduLagnaCalculator


def _planet(sign: int, *, longitude: float | None = None, house: int = 1) -> dict:
    return {
        "sign": sign,
        "longitude": float(sign * 30 + 1 if longitude is None else longitude),
        "degree": float(1 if longitude is None else longitude % 30),
        "house": house,
    }


def _chart() -> dict:
    # Aries ascendant and Taurus Moon:
    # 9th from Lagna = Sagittarius/Jupiter (10 Kalas)
    # 9th from Moon = Capricorn/Saturn (1 Kala)
    # 10 + 1 = 11; counting 11 signs from Taurus gives Pisces.
    return {
        "ascendant": 1.0,
        "planets": {
            "Sun": _planet(5),       # Virgo: seventh aspect to Pisces
            "Moon": _planet(1),      # Taurus
            "Mars": _planet(4),
            "Mercury": _planet(0),
            "Jupiter": _planet(7),   # Scorpio: fifth aspect to Pisces
            "Venus": _planet(11),    # Occupies Indu Lagna
            "Saturn": _planet(2),    # Gemini: tenth aspect to Pisces
            "Rahu": _planet(7),      # Scorpio: disputed fifth aspect excluded
            "Ketu": _planet(5),      # Virgo: seventh aspect retained
        },
    }


def test_indu_lagna_uses_classical_kala_count() -> None:
    calculator = InduLagnaCalculator(_chart())

    assert calculator.calculate_indu_lagna() == 12

    calculation = calculator.get_indu_lagna_analysis()["special_lagnas"]["indu_lagna"]["calculation"]
    assert calculation["ninth_from_ascendant_lord"] == "Jupiter"
    assert calculation["ninth_from_ascendant_kalas"] == 10
    assert calculation["ninth_from_moon_lord"] == "Saturn"
    assert calculation["ninth_from_moon_kalas"] == 1
    assert calculation["kala_total"] == 11
    assert calculation["count_from_moon"] == 11
    assert calculation["indu_lagna_sign_name"] == "Pisces"


def test_indu_lagna_is_explicitly_sign_only() -> None:
    row = InduLagnaCalculator(_chart()).get_indu_lagna_data()

    assert row["sign"] == 11
    assert row["house"] == 12
    assert row["precision"] == "sign_only"
    assert row["exact_degree_available"] is False
    assert row["longitude_is_plotting_anchor"] is True
    assert row["degree"] == 0.0


def test_indu_analysis_includes_lord_occupants_and_gain_houses() -> None:
    indu = InduLagnaCalculator(_chart()).get_indu_lagna_analysis()["special_lagnas"]["indu_lagna"]

    assert indu["ruler"] == "Jupiter"
    assert indu["ruler_analysis"]["house"] == 8
    assert indu["ruler_analysis"]["nakshatra"]["available"] is True
    assert indu["ruler_analysis"]["strength_analysis"]["available"] is False
    assert indu["interpretation_policy"]["requires_separate_lord_strength_evidence"] is True
    assert indu["occupying_planets"] == ["Venus"]

    second = indu["second_from_indu"]
    assert second["sign_name"] == "Aries"
    assert second["natal_house"] == 1
    assert second["ruler"] == "Mars"

    eleventh = indu["eleventh_from_indu"]
    assert eleventh["sign_name"] == "Capricorn"
    assert eleventh["natal_house"] == 10
    assert eleventh["ruler"] == "Saturn"


def test_indu_aspects_use_correct_whole_sign_offsets_and_node_policy() -> None:
    indu = InduLagnaCalculator(_chart()).get_indu_lagna_analysis()["special_lagnas"]["indu_lagna"]
    aspects = {row["planet"]: row["aspect_numbers"] for row in indu["aspect_details"]}

    assert aspects["Sun"] == [7]
    assert aspects["Jupiter"] == [5]
    assert aspects["Saturn"] == [10]
    assert aspects["Ketu"] == [7]
    assert "Rahu" not in aspects
    assert "Venus" not in aspects  # Occupation is not mislabeled as an aspect.


@pytest.mark.parametrize(
    "chart, message",
    [
        ({"planets": {"Moon": _planet(1)}}, "ascendant"),
        ({"ascendant": 1.0, "planets": {}}, "Moon"),
    ],
)
def test_indu_lagna_rejects_missing_required_chart_data(chart: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        InduLagnaCalculator(chart).calculate_indu_lagna()


def test_indu_lagna_accepts_structured_ascendant_sign() -> None:
    chart = _chart()
    chart["ascendant"] = {"sign": 0}

    assert InduLagnaCalculator(chart).calculate_indu_lagna() == 12
