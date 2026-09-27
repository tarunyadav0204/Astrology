from __future__ import annotations

from calculators.classical_functional_nature import (
    PLANETS,
    calculate_functional_nature,
    compatibility_lists,
    derive_lordship_nature,
    functional_nature_table,
)
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator


def _chart(ascendant_sign: int) -> dict:
    return {
        "ascendant": ascendant_sign * 30 + 10.0,
        "planets": {
            "Sun": {"sign": 0, "degree": 10.0, "longitude": 10.0},
            "Moon": {"sign": 1, "degree": 10.0, "longitude": 40.0},
            "Mars": {"sign": 2, "degree": 10.0, "longitude": 70.0},
            "Mercury": {"sign": 3, "degree": 10.0, "longitude": 100.0},
            "Jupiter": {"sign": 4, "degree": 10.0, "longitude": 130.0},
            "Venus": {"sign": 5, "degree": 10.0, "longitude": 160.0},
            "Saturn": {"sign": 6, "degree": 10.0, "longitude": 190.0},
        },
    }


def test_every_lagna_assigns_each_visible_planet_once_without_contract_gaps():
    benefics, malefics, neutrals = compatibility_lists()
    for ascendant in range(12):
        groups = [set(benefics[ascendant]), set(malefics[ascendant]), set(neutrals[ascendant])]
        assert set.union(*groups) == set(PLANETS)
        assert not (groups[0] & groups[1])
        assert not (groups[0] & groups[2])
        assert not (groups[1] & groups[2])


def test_bphs_lagna_catalogue_retains_qualified_and_unclassified_cases():
    taurus = functional_nature_table(1)
    assert taurus["Saturn"]["functional_nature"] == "benefic"
    assert taurus["Mercury"]["functional_nature"] == "malefic"
    assert taurus["Mercury"]["stated_qualification"] == "Somewhat inauspicious."
    assert taurus["Mars"]["functional_nature"] == "neutral"

    gemini = functional_nature_table(2)
    assert [planet for planet in PLANETS if gemini[planet]["functional_nature"] == "benefic"] == ["Venus"]
    assert gemini["Saturn"]["functional_nature"] == "neutral"
    assert gemini["Saturn"]["derived_nature"] == "benefic"
    assert gemini["Saturn"]["textual_departure"] is True


def test_yogakaraka_excludes_lagna_ownership_alone_and_keeps_maraka_separate():
    assert calculate_functional_nature(3, "Mars")["is_yogakaraka"] is True  # Cancer: H5/H10
    assert calculate_functional_nature(4, "Mars")["is_yogakaraka"] is True  # Leo: H4/H9
    assert calculate_functional_nature(6, "Saturn")["is_yogakaraka"] is True  # Libra: H4/H5
    assert calculate_functional_nature(9, "Venus")["is_yogakaraka"] is True  # Capricorn: H5/H10
    assert calculate_functional_nature(10, "Venus")["is_yogakaraka"] is True  # Aquarius: H4/H9
    assert calculate_functional_nature(0, "Mars")["is_yogakaraka"] is False  # Aries: H1/H8

    aries_venus = calculate_functional_nature(0, "Venus")
    assert aries_venus["functional_nature"] == "malefic"
    assert aries_venus["is_maraka_lord"] is True
    assert aries_venus["maraka_houses"] == [2, 7]


def test_general_lordship_rules_preserve_conditions_and_eighth_lord_exception():
    assert derive_lordship_nature([2, 12], "Venus")["nature"] == "conditional"
    assert derive_lordship_nature([8, 9], "Saturn")["nature"] == "benefic"
    assert derive_lordship_nature([3, 8], "Mars")["nature"] == "malefic"
    assert derive_lordship_nature([8], "Sun")["nature"] == "neutral"


def test_existing_dignity_contract_is_preserved_with_additive_classical_evidence():
    dignity = PlanetaryDignitiesCalculator(_chart(1)).calculate_planetary_dignities()
    assert dignity["Venus"]["functional_nature"] == "malefic"
    details = dignity["Venus"]["functional_nature_details"]
    assert details["ascendant_sign_name"] == "Taurus"
    assert details["stated_verses"] == "BPHS 34.23-24"
    assert details["source"]["chapter"] == 34


def test_nodes_keep_the_old_neutral_value_without_receiving_a_planetary_role():
    rahu = calculate_functional_nature(3, "Rahu")
    assert rahu["functional_nature"] == "neutral"
    assert rahu["applicable"] is False
    assert rahu["ruled_houses"] == []
