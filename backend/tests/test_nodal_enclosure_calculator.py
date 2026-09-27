from backend.calculators.nodal_enclosure_calculator import calculate_nodal_enclosure
from backend.calculators.yoga_calculator import YogaCalculator


VISIBLE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def chart(longitudes, *, rahu=10.0, ketu=190.0):
    planets = {
        name: {"longitude": longitude, "sign": int(longitude // 30), "house": int(longitude // 30) + 1}
        for name, longitude in zip(VISIBLE, longitudes)
    }
    planets["Rahu"] = {"longitude": rahu, "sign": int(rahu // 30), "house": int(rahu // 30) + 1}
    planets["Ketu"] = {"longitude": ketu, "sign": int(ketu // 30), "house": int(ketu // 30) + 1}
    return {
        "ascendant": 0.0,
        "planets": planets,
        "houses": [{"house": number, "sign": number - 1} for number in range(1, 13)],
    }


def test_strict_enclosure_uses_longitudes_and_returns_direction_and_planets():
    result = calculate_nodal_enclosure(chart([20, 45, 70, 95, 120, 145, 180]))

    assert result["present"] is True
    assert result["status"] == "complete"
    assert result["strict_complete"] is True
    assert result["direction"] == "Rahu_to_Ketu"
    assert result["contained_planets"] == list(VISIBLE)
    assert result["outside_planets"] == []
    assert result["source"]["classical_source_verified"] is False
    assert result["classification"] == "modern_astronomical_convention"


def test_same_houses_do_not_create_false_positive_when_longitudes_cross_axis():
    # The Sun and Moon can share the nodes' signs while lying on opposite sides
    # of the exact nodal degrees. A sign/house-only calculation cannot see this.
    result = calculate_nodal_enclosure(chart([5, 195, 40, 70, 100, 130, 160]))

    assert result["present"] is False
    assert result["status"] == "not_formed"
    assert result["outside_planets"]


def test_planet_exactly_on_node_is_reported_as_boundary_not_strict():
    result = calculate_nodal_enclosure(chart([10, 45, 70, 95, 120, 145, 180]))

    assert result["present"] is True
    assert result["complete"] is True
    assert result["strict_complete"] is False
    assert result["status"] == "boundary"
    assert result["boundary_planets"] == [{"planet": "Sun", "node": "Rahu", "orb_degrees": 0.0}]


def test_wraparound_ketu_to_rahu_arc_is_supported():
    result = calculate_nodal_enclosure(chart([200, 220, 245, 270, 300, 330, 5]))

    assert result["present"] is True
    assert result["direction"] == "Ketu_to_Rahu"
    assert result["contained_planets"] == list(VISIBLE)


def test_missing_visible_planet_makes_result_unavailable_instead_of_skipping_it():
    value = chart([20, 45, 70, 95, 120, 145, 180])
    del value["planets"]["Saturn"]
    result = calculate_nodal_enclosure(value)

    assert result["present"] is False
    assert result["status"] == "unavailable"
    assert result["missing_planets"] == ["Saturn"]


def test_partial_configuration_is_described_but_not_claimed_as_a_dosha():
    result = calculate_nodal_enclosure(chart([20, 45, 70, 95, 120, 145, 220]))

    assert result["present"] is False
    assert result["selected_arc"]["contained_count"] == 6
    assert result["partial_configuration"]["claimed"] is False
    assert result["named_variant"]["claimed"] is False


def test_yoga_calculator_preserves_major_dosha_contract():
    result = YogaCalculator(None, chart([20, 45, 70, 95, 120, 145, 180])).calculate_major_doshas()

    assert set(result) == {"mangal_dosha", "kaal_sarp_dosha", "pitra_dosha", "matru_dosha"}
    assert result["kaal_sarp_dosha"]["present"] is True
    assert result["kaal_sarp_dosha"]["type"] == "Nodal enclosure"
