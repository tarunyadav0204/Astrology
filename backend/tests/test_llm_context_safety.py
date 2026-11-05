from chat.llm_context_safety import strip_outer_planets_from_llm_context


def test_outer_planets_are_removed_from_keyed_and_record_payloads():
    payload = {
        "d1_chart": {
            "planets": {
                "Sun": {"house": 4},
                "Uranus": {"house": 7},
                "Neptune": {"house": 8},
                "Pluto": {"house": 9},
            },
            "aspects": [
                {"planet": "Mars", "target_planet": "Sun"},
                {"planet": "Uranus", "target_planet": "Moon"},
            ],
        },
        "transits": [{"planet_name": "Neptune"}, {"planet_name": "Saturn"}],
        "ordinary_text": "This is retained without modifying prose.",
    }

    cleaned = strip_outer_planets_from_llm_context(payload)

    assert set(cleaned["d1_chart"]["planets"]) == {"Sun"}
    assert cleaned["d1_chart"]["aspects"] == [{"planet": "Mars", "target_planet": "Sun"}]
    assert cleaned["transits"] == [{"planet_name": "Saturn"}]


def test_outer_planet_record_is_removed_even_when_nested_in_a_tuple():
    cleaned = strip_outer_planets_from_llm_context((
        {"planet": "Pluto", "house": 3},
        {"planet": "Jupiter", "house": 4},
    ))

    assert cleaned == ({"planet": "Jupiter", "house": 4},)
