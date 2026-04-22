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
