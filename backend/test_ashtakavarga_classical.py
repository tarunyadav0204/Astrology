from types import SimpleNamespace

from calculators.ashtakavarga import AshtakavargaCalculator
from calculators.chart_calculator import ChartCalculator


def _dummy_birth():
    return SimpleNamespace(
        name="Test",
        date="2000-01-01",
        time="00:00",
        latitude=0.0,
        longitude=0.0,
        place="",
        timezone=0.0,
    )


def _dummy_chart():
    return {
        "ascendant": 0.0,
        "planets": {
            planet: {"sign": 0, "longitude": 0.0}
            for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        },
    }


def _parasharas_light_sample_chart():
    """Exact sidereal positions printed in Parashara's Light Sample Report 5.

    Source: Parashara's Light 7.0.3, Sample Report 5, pp. 2 and 14–18.
    Birth: 2000-11-11 09:01:20, Delhi; Lahiri ayanamsha.
    """
    positions = {
        "Sun": (6, 205 + 11 / 60),
        "Moon": (0, 15 + 32 / 60),
        "Mars": (5, 160 + 28 / 60),
        "Mercury": (6, 186 + 53 / 60),
        "Jupiter": (1, 44 + 31 / 60),
        "Venus": (8, 243 + 47 / 60),
        "Saturn": (1, 34 + 18 / 60),
    }
    return {
        "ascendant": 210 + 24 + 25 / 60,
        "planets": {
            planet: {"sign": sign, "longitude": longitude}
            for planet, (sign, longitude) in positions.items()
        },
    }


def _parasharas_light_sample_chart_two():
    """Second independently published Parashara's Light sample report.

    Source: Himalaya Vedic World AVKP1 sample, pp. 1–2 and 14–17.
    Birth: 1980-03-20 12:08:13, Delhi; Lahiri ayanamsha.
    """
    positions = {
        "Sun": (11, 336 + 14 / 60),
        "Moon": (0, 25 + 2 / 60),
        "Mars": (4, 124 + 9 / 60),
        "Mercury": (10, 313 + 51 / 60),
        "Jupiter": (4, 128 + 42 / 60),
        "Venus": (0, 21 + 19 / 60),
        "Saturn": (4, 149 + 34 / 60),
    }
    return {
        "ascendant": 60 + 14 + 2 / 60,
        "planets": {
            planet: {"sign": sign, "longitude": longitude}
            for planet, (sign, longitude) in positions.items()
        },
    }


def test_classical_bhinnashtakavarga_fixed_totals():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())

    expected_totals = {
        "Sun": 48,
        "Moon": 49,
        "Mars": 39,
        "Mercury": 54,
        "Jupiter": 56,
        "Venus": 52,
        "Saturn": 39,
    }

    actual_totals = {
        planet: sum(len(houses) for houses in rules.values())
        for planet, rules in calc.contribution_rules.items()
    }

    assert actual_totals == expected_totals
    assert sum(actual_totals.values()) == 337


def test_reference_chart_moon_bhinnashtakavarga_matches_classical_table():
    birth = SimpleNamespace(
        name="Reference Chart",
        date="1980-04-02",
        time="14:55",
        latitude=29.1492,
        longitude=75.7217,
        place="Hisar, Haryana, India",
        timezone=5.5,
    )

    chart = ChartCalculator({}).calculate_chart(birth, "mean")
    calc = AshtakavargaCalculator(birth, chart)
    moon_bindus = calc.calculate_individual_ashtakavarga("Moon")["bindus"]

    expected = {
        0: 4,
        1: 5,
        2: 4,
        3: 3,
        4: 5,
        5: 5,
        6: 4,
        7: 3,
        8: 6,
        9: 4,
        10: 3,
        11: 3,
    }

    assert moon_bindus == expected


def test_classical_lagna_bhinnashtakavarga_total_is_49():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())
    assert sum(len(houses) for houses in calc.lagna_contribution_rules.values()) == 49


def test_reference_chart_lagna_bhinnashtakavarga_matches_classical_table():
    birth = SimpleNamespace(
        name="Reference Chart",
        date="1980-04-02",
        time="14:55",
        latitude=29.1492,
        longitude=75.7217,
        place="Hisar, Haryana, India",
        timezone=5.5,
    )

    chart = ChartCalculator({}).calculate_chart(birth, "mean")
    calc = AshtakavargaCalculator(birth, chart)
    lagna_bindus = calc.calculate_lagna_ashtakavarga()["bindus"]

    expected = {
        0: 2,
        1: 7,
        2: 5,
        3: 3,
        4: 6,
        5: 5,
        6: 2,
        7: 3,
        8: 6,
        9: 5,
        10: 3,
        11: 2,
    }

    assert lagna_bindus == expected


def test_prastara_reconstructs_every_bav_sign_total():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())
    for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        prastara = calc.calculate_prastara_ashtakavarga(planet)
        bav = calc.calculate_individual_ashtakavarga(planet)["bindus"]
        assert prastara["sign_totals"] == {str(sign): bav[sign] for sign in range(12)}


def test_kakshya_boundaries_are_exact_half_open_intervals():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())
    expected = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Ascendant"]
    starts = [0, 3.75, 7.5, 11.25, 15, 18.75, 22.5, 26.25]
    for index, start in enumerate(starts):
        at_start = calc.calculate_kakshya_activation("Saturn", 30 + start)
        assert at_start["kakshya_number"] == index + 1
        assert at_start["kakshya_ruler"] == expected[index]
    assert calc.calculate_kakshya_activation("Saturn", 33.749999)["kakshya_ruler"] == "Saturn"
    assert calc.calculate_kakshya_activation("Saturn", 60.0)["sign_id"] == 2
    assert calc.calculate_kakshya_activation("Saturn", 60.0)["kakshya_ruler"] == "Saturn"


def test_trikona_and_ekadhipatya_reduction_rules():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())
    raw = [7, 0, 0, 0, 4, 0, 0, 0, 4, 0, 0, 0]
    reduced, trace = calc.apply_trikona_shodhana(raw)
    assert [reduced[index] for index in (0, 4, 8)] == [3, 0, 0]
    assert trace[0]["minimum"] == 4

    chart = _dummy_chart()
    chart["planets"]["Sun"]["sign"] = 1  # Taurus occupied; Libra empty.
    calc = AshtakavargaCalculator(_dummy_birth(), chart)
    values = [0, 4, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0]
    lower_empty, trace = calc.apply_ekadhipatya_shodhana(values)
    assert lower_empty[1] == 4 and lower_empty[6] == 0
    assert next(row for row in trace if row["lord"] == "Venus")["action"] == "empty_reduced_to_zero"

    values[6] = 6
    higher_empty, _ = calc.apply_ekadhipatya_shodhana(values)
    assert higher_empty[1] == 4 and higher_empty[6] == 4


def test_shodhya_pinda_matches_pvr_narasimha_rao_example_43():
    chart = _dummy_chart()
    for planet in ("Sun", "Mars", "Mercury"):
        chart["planets"][planet]["sign"] = 2  # Gemini
    chart["planets"]["Venus"]["sign"] = 0  # Aries
    for planet in ("Moon", "Jupiter", "Saturn"):
        chart["planets"][planet]["sign"] = 3  # a zero-rekha sign in this fixture
    calc = AshtakavargaCalculator(_dummy_birth(), chart)
    fixture = [3, 1, 3, 0, 0, 0, 0, 0, 0, 0, 2, 0]
    calc.calculate_individual_ashtakavarga = lambda _planet: {
        "planet": "Mercury", "bindus": {i: fixture[i] for i in range(12)}, "total": sum(fixture)
    }
    result = calc.calculate_shodhya_pinda("Mercury")
    assert result["after_ekadhipatya"] == {str(i): fixture[i] for i in range(12)}
    assert result["rashi_pinda"] == 77
    assert result["graha_pinda"] == 75
    assert result["shodhya_pinda"] == 152


def test_parasharas_light_sample_matches_all_seven_raw_bavs_and_kakshyas():
    chart = _parasharas_light_sample_chart()
    calc = AshtakavargaCalculator(_dummy_birth(), chart)
    expected_bavs = {
        "Sun": [3, 4, 6, 3, 4, 5, 4, 3, 3, 5, 4, 4],
        "Moon": [6, 4, 3, 4, 5, 4, 5, 2, 3, 4, 5, 4],
        "Mars": [3, 2, 2, 3, 4, 3, 3, 3, 4, 2, 5, 5],
        "Mercury": [4, 3, 5, 4, 5, 5, 4, 3, 6, 3, 6, 6],
        "Jupiter": [5, 5, 4, 6, 6, 4, 6, 4, 5, 3, 4, 4],
        "Venus": [2, 3, 3, 5, 6, 5, 1, 3, 6, 5, 7, 6],
        "Saturn": [3, 3, 3, 4, 4, 5, 4, 4, 0, 3, 3, 3],
    }
    expected_kakshyas = {
        "Sun": (7, "Moon", 0),
        "Moon": (5, "Venus", 1),
        "Mars": (3, "Mars", 1),
        "Mercury": (2, "Jupiter", 1),
        "Jupiter": (4, "Sun", 1),
        "Venus": (2, "Jupiter", 1),
        "Saturn": (2, "Jupiter", 0),
    }

    for planet, expected in expected_bavs.items():
        bav = calc.calculate_individual_ashtakavarga(planet)
        assert [bav["bindus"][sign] for sign in range(12)] == expected
        kakshya = calc.calculate_kakshya_activation(planet, chart["planets"][planet]["longitude"])
        assert (kakshya["kakshya_number"], kakshya["kakshya_ruler"], kakshya["bindu"]) == expected_kakshyas[planet]
    sav = calc.calculate_sarvashtakavarga()
    assert [sav["sarvashtakavarga"][str(sign)] for sign in range(12)] == [
        26, 24, 26, 29, 34, 31, 27, 22, 27, 25, 34, 32,
    ]
    assert sav["total_bindus"] == 337


def test_parasharas_light_profile_matches_all_21_pinda_totals():
    calc = AshtakavargaCalculator(
        _dummy_birth(),
        _parasharas_light_sample_chart(),
        reduction_profile="parasharas_light_7",
    )
    expected = {
        "Sun": (41, 8, 49),
        "Moon": (109, 35, 144),
        "Mars": (77, 25, 102),
        "Mercury": (78, 30, 108),
        "Jupiter": (58, 58, 116),
        "Venus": (128, 44, 172),
        "Saturn": (92, 41, 133),
    }
    for planet, totals in expected.items():
        result = calc.calculate_shodhya_pinda(planet)
        assert (result["rashi_pinda"], result["graha_pinda"], result["shodhya_pinda"]) == totals
        assert result["reduction_profile"] == "parasharas_light_7"


def test_second_parasharas_light_chart_matches_all_bavs_and_21_pinda_totals():
    chart = _parasharas_light_sample_chart_two()
    calc = AshtakavargaCalculator(_dummy_birth(), chart, reduction_profile="parasharas_light_7")
    expected_bavs = {
        "Sun": [6, 3, 6, 1, 3, 6, 3, 5, 3, 4, 3, 5],
        "Moon": [4, 4, 6, 2, 5, 4, 5, 3, 5, 5, 4, 2],
        "Mars": [3, 4, 6, 3, 4, 3, 0, 4, 2, 2, 4, 4],
        "Mercury": [5, 4, 6, 6, 4, 4, 1, 7, 2, 5, 6, 4],
        "Jupiter": [2, 6, 5, 3, 4, 5, 6, 5, 6, 3, 6, 5],
        "Venus": [7, 4, 7, 5, 3, 1, 5, 3, 6, 4, 4, 3],
        "Saturn": [2, 1, 6, 3, 1, 5, 4, 2, 5, 5, 2, 3],
    }
    expected_pindas = {
        "Sun": (106, 56, 162),
        "Moon": (55, 23, 78),
        "Mars": (151, 83, 234),
        "Mercury": (144, 107, 251),
        "Jupiter": (118, 61, 179),
        "Venus": (119, 48, 167),
        "Saturn": (116, 17, 133),
    }
    for planet in expected_bavs:
        bav = calc.calculate_individual_ashtakavarga(planet)
        assert [bav["bindus"][sign] for sign in range(12)] == expected_bavs[planet]
        result = calc.calculate_shodhya_pinda(planet)
        assert (result["rashi_pinda"], result["graha_pinda"], result["shodhya_pinda"]) == expected_pindas[planet]
    sav = calc.calculate_sarvashtakavarga()
    assert [sav["sarvashtakavarga"][str(sign)] for sign in range(12)] == [
        29, 26, 42, 23, 24, 28, 24, 29, 29, 28, 29, 26,
    ]
    assert sav["total_bindus"] == 337


def test_default_pvr_profile_is_declared_and_not_silently_blended():
    calc = AshtakavargaCalculator(_dummy_birth(), _parasharas_light_sample_chart())
    advanced = calc.calculate_advanced_ashtakavarga()
    assert advanced["convention"]["reduction_profile"] == "pvr_narasimha_rao"
    assert advanced["convention"]["mixed_higher_empty_rule"] == "replace_with_occupied_value"
    assert advanced["convention"]["count_ascendant_as_occupant"] is False
    # These two values are the known points of divergence from Parashara's Light.
    assert calc.calculate_shodhya_pinda("Mercury")["shodhya_pinda"] == 120
    assert calc.calculate_shodhya_pinda("Saturn")["shodhya_pinda"] == 125


def test_shodhya_timing_maps_zero_remainder_to_last_nakshatra_and_sign():
    calc = AshtakavargaCalculator(_dummy_birth(), _dummy_chart())
    calc.calculate_shodhya_pinda = lambda _planet: {
        "raw_bav": {str(i): 0 for i in range(12)}, "shodhya_pinda": 203
    }
    timing = calc.calculate_shodhya_timing("Saturn", 8)
    assert timing["nakshatra_number"] == 27
    assert timing["nakshatra"] == "Revati"
    assert timing["rashi_number"] == 12
    assert timing["rashi"] == "Pisces"
