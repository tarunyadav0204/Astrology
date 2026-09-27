from calculators.planet_result_delivery import calculate_planet_result_delivery


def _chart():
    return {
        "ascendant": 0.0,
        "planets": {
            "Sun": {"sign": 0, "house": 1, "retrograde": False},
            "Moon": {"sign": 1, "house": 2, "retrograde": False},
            "Mars": {"sign": 2, "house": 3, "retrograde": True},
            "Mercury": {"sign": 11, "house": 12, "retrograde": True, "combust": True},
            "Jupiter": {"sign": 3, "house": 4, "retrograde": False},
            "Venus": {"sign": 4, "house": 5, "retrograde": False},
            "Saturn": {"sign": 5, "house": 6, "retrograde": False},
            "Rahu": {"sign": 6, "house": 7, "retrograde": True},
            "Ketu": {"sign": 0, "house": 1, "retrograde": True},
        },
        "neecha_bhanga": {
            "Mercury": {
                "neecha_bhanga_present": True,
                "source": {"reference_label": "Phaladeepika 7.26-30"},
            }
        },
    }


def test_mercury_channels_merge_lordship_occupation_and_aspect():
    result = calculate_planet_result_delivery(_chart())
    mercury = result["planets"]["Mercury"]
    assert mercury["conditions"] == {
        "debilitated": True,
        "neecha_bhanga": True,
        "retrograde": True,
        "combust": True,
    }
    assert mercury["owned_houses"] == [3, 6]
    assert mercury["occupied_house"] == 12
    assert mercury["delivery_state"] == "debilitation_cancelled_retrograde_combust"
    assert mercury["channels"] == [
        {"house": 3, "roles": ["owned"], "aspect_numbers": []},
        {"house": 6, "roles": ["owned", "aspected"], "aspect_numbers": [7]},
        {"house": 12, "roles": ["occupied"], "aspect_numbers": []},
    ]


def test_special_mars_aspects_are_exposed_as_house_channels():
    result = calculate_planet_result_delivery(_chart())
    mars = result["planets"]["Mars"]
    # Retrogression does not create special delivery houses or make this
    # explanatory card relevant by itself. The ordinary channels remain in
    # the additive API data for clients that need them.
    assert mars["relevant"] is False
    assert mars["aspected_houses"] == [
        {"house": 6, "aspect_number": 4},
        {"house": 9, "aspect_number": 7},
        {"house": 10, "aspect_number": 8},
    ]


def test_nodes_are_not_treated_as_retrograde_delivery_planets():
    result = calculate_planet_result_delivery(_chart())
    assert "Rahu" not in result["planets"]
    assert "Ketu" not in result["planets"]


def test_retrogression_is_explicitly_not_recorded_as_support():
    result = calculate_planet_result_delivery(_chart())
    mars = result["planets"]["Mars"]
    assert {row["key"] for row in mars["supporting_factors"]} == set()
    assert {row["key"] for row in mars["limiting_factors"]} == {
        "retrograde_not_automatically_positive"
    }


def test_debilitation_remains_the_presentation_trigger_when_also_retrograde():
    result = calculate_planet_result_delivery(_chart())
    mercury = result["planets"]["Mercury"]
    assert mercury["conditions"]["debilitated"] is True
    assert mercury["conditions"]["retrograde"] is True
    assert mercury["relevant"] is True
