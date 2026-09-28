from __future__ import annotations

from calculators.classical_natural_nature import calculate_natural_nature, moon_natural_nature
from calculators.planet_analyzer import PlanetAnalyzer
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from chat.instant_chat_pipeline import _enrich_calculated_chart_for_prediction


def _chart(moon_longitude: float) -> dict:
    planets = {
        "Sun": {"longitude": 10.0, "sign": 0, "degree": 10.0, "house": 1},
        "Moon": {"longitude": moon_longitude, "sign": int(moon_longitude / 30), "degree": moon_longitude % 30, "house": 2},
        "Mars": {"longitude": 70.0, "sign": 2, "degree": 10.0, "house": 3},
        "Mercury": {"longitude": 100.0, "sign": 3, "degree": 10.0, "house": 4},
        "Jupiter": {"longitude": 130.0, "sign": 4, "degree": 10.0, "house": 5},
        "Venus": {"longitude": 160.0, "sign": 5, "degree": 10.0, "house": 6},
        "Saturn": {"longitude": 190.0, "sign": 6, "degree": 10.0, "house": 7},
        "Rahu": {"longitude": 220.0, "sign": 7, "degree": 10.0, "house": 8},
        "Ketu": {"longitude": 40.0, "sign": 1, "degree": 10.0, "house": 2},
    }
    return {"ascendant": 5.0, "ascendant_sign": 0, "planets": planets}


def test_moon_is_benefic_while_waxing_and_malefic_while_waning():
    waxing = moon_natural_nature(_chart(100.0))
    waning = moon_natural_nature(_chart(250.0))
    assert waxing == {
        "nature": "benefic", "phase": "waxing", "paksha": "shukla",
        "elongation": 90.0,
        "reason": "Waxing Moon (Shukla Paksha) is treated as a natural benefic.",
    }
    assert waning["nature"] == "malefic"
    assert waning["phase"] == "waning_or_dark"
    assert waning["paksha"] == "krishna"
    assert waning["elongation"] == 240.0


def test_new_moon_boundary_is_not_mislabeled_as_waxing_benefic():
    dark = moon_natural_nature(_chart(10.0))
    assert dark["nature"] == "malefic"
    assert dark["phase"] == "waning_or_dark"


def test_dignity_and_chat_clients_receive_the_same_phase_based_moon_nature():
    chart = _chart(250.0)
    dignity = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
    assert dignity["Moon"]["natural_nature"] == "malefic"
    assert dignity["Moon"]["natural_nature_details"]["phase"] == "waning_or_dark"

    enriched = _enrich_calculated_chart_for_prediction("D1", chart)
    assert enriched["planets"]["Moon"]["natural_nature"] == "malefic"
    assert enriched["planets"]["Moon"]["natural_nature_details"]["paksha"] == "krishna"


def test_functional_role_remains_separate_from_moon_phase():
    chart = _chart(250.0)  # Aries Lagna: Moon is functionally neutral in BPHS table.
    moon = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()["Moon"]
    assert moon["natural_nature"] == "malefic"
    assert moon["functional_nature"] == "neutral"


def test_planet_analyzer_uses_phase_when_judging_a_moon_aspect():
    chart = _chart(250.0)
    analyzer = PlanetAnalyzer(chart, compute_shadbala=False)
    effect = analyzer._get_aspect_effect("Moon", "Mars")
    assert effect["score"] < 0
    assert any("Natural malefic (Moon)" in line for line in effect["calculation_details"])
    assert any("Moon phase: waning_or_dark" in line for line in effect["calculation_details"])


def test_mercury_association_uses_the_actual_moon_phase():
    chart = _chart(250.0)
    chart["planets"]["Mercury"].update({"sign": 8, "longitude": 250.0, "degree": 10.0})
    chart["planets"]["Ketu"].update({"sign": 8, "longitude": 251.0, "degree": 11.0})
    nature = calculate_natural_nature(chart, "Mercury")
    assert nature["nature"] == "malefic"
    assert nature["malefic_associates"] == ["Ketu", "Moon"]
