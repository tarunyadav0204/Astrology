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
