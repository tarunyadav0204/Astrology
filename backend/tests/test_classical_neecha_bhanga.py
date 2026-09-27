from calculators.classical_neecha_bhanga import (
    SOURCE,
    calculate_classical_neecha_bhanga,
)
from calculators.neecha_bhanga_calculator import NeechaBhangaCalculator
from calculators.yoga_calculator import YogaCalculator


VISIBLE = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _chart(overrides=None, *, ascendant_sign=0):
    signs = {
        "Sun": 4,
        "Moon": 1,
        "Mars": 0,
        "Mercury": 2,
        "Jupiter": 8,
        "Venus": 6,
        "Saturn": 10,
        "Rahu": 5,
        "Ketu": 11,
    }
    signs.update(overrides or {})
    planets = {}
    for index, (planet, sign) in enumerate(signs.items()):
        planets[planet] = {
            "sign": sign,
            "house": ((sign - ascendant_sign) % 12) + 1,
            "longitude": sign * 30.0 + 5.0 + index / 10.0,
        }
    return {
        "ascendant": ascendant_sign * 30.0 + 10.0,
        "houses": [
            {"house_number": house, "sign": (ascendant_sign + house - 1) % 12}
            for house in range(1, 13)
        ],
        "planets": planets,
    }


def _rule_ids(result, planet):
    return set(result[planet]["matched_rule_ids"])


def test_no_debilitated_planet_produces_no_result():
    assert calculate_classical_neecha_bhanga(_chart()) == {}


def test_phaladeepika_7_26_and_7_29_debilitation_lord_in_kendra():
    chart = _chart({"Mercury": 11, "Jupiter": 3})
    rules = _rule_ids(calculate_classical_neecha_bhanga(chart), "Mercury")
    assert "PD_7_26_29_DEBILITATION_LORD_KENDRA_FROM_LAGNA" in rules


def test_phaladeepika_7_26_planet_exalted_in_debilitation_sign_in_kendra():
    chart = _chart({"Sun": 6, "Saturn": 9})
    result = calculate_classical_neecha_bhanga(chart)
    assert result["Sun"]["planet_exalted_in_debilitation_sign"] == "Saturn"
    assert "PD_7_26_EXALTED_IN_DEBILITATION_SIGN_KENDRA_FROM_LAGNA" in _rule_ids(result, "Sun")


def test_phaladeepika_7_27_two_lords_in_mutual_kendras():
    chart = _chart({"Mars": 3, "Moon": 1, "Saturn": 4})
    rules = _rule_ids(calculate_classical_neecha_bhanga(chart), "Mars")
    assert "PD_7_27_LORDS_IN_MUTUAL_KENDRAS" in rules


def test_phaladeepika_7_28_dispositor_aspects_debilitated_planet():
    chart = _chart({"Saturn": 0, "Mars": 6})
    rules = _rule_ids(calculate_classical_neecha_bhanga(chart), "Saturn")
    assert "PD_7_28_DEBILITATED_PLANET_ASPECTED_BY_SIGN_LORD" in rules


def test_phaladeepika_7_30_debilitated_planet_itself_in_kendra():
    chart = _chart({"Jupiter": 9})
    rules = _rule_ids(calculate_classical_neecha_bhanga(chart), "Jupiter")
    assert "PD_7_30_DEBILITATED_PLANET_KENDRA_FROM_LAGNA" in rules


def test_conjunction_with_dispositor_is_not_invented_as_verse_7_28_aspect():
    # Pisces ascendant: Saturn and its dispositor Mars conjoin in Aries/H2.
    # The other classical limbs are deliberately placed outside Kendras.
    chart = _chart(
        {"Saturn": 0, "Mars": 0, "Moon": 11, "Sun": 0, "Venus": 1},
        ascendant_sign=11,
    )
    saturn = calculate_classical_neecha_bhanga(chart)["Saturn"]
    assert saturn["neecha_bhanga_present"] is False
    assert "PD_7_28_DEBILITATED_PLANET_ASPECTED_BY_SIGN_LORD" not in saturn["matched_rule_ids"]


def test_legacy_summary_contract_and_yoga_contract_are_preserved():
    chart = _chart({"Mercury": 11, "Jupiter": 3})
    summary = NeechaBhangaCalculator(chart, {"d9_navamsa": {}}).get_neecha_bhanga_summary()
    assert summary["neecha_bhanga_planets"] == summary["planets_with_neecha_bhanga"]
    assert summary["total_neecha_bhanga_planets"] == 1
    assert summary["source"]["reference_label"] == "Phaladeepika 7.26-30"

    yogas = YogaCalculator(None, chart).calculate_neecha_bhanga_yogas()
    mercury = next(row for row in yogas if row["planet"] == "Mercury")
    assert mercury["name"] == "Neecha Bhanga Raja Yoga"
    assert mercury["strength"] == "Established"
    assert mercury["classical_conditions"]
    assert "power, status, fame and wealth" in mercury["classical_result"]
    assert mercury["source"] == SOURCE
    assert mercury["result_delivery"]["conditions"]["neecha_bhanga"] is True
    assert mercury["result_delivery"]["channels"]


def test_every_visible_planet_uses_the_canonical_debilitation_sign():
    expected = {
        "Sun": 6,
        "Moon": 7,
        "Mars": 3,
        "Mercury": 11,
        "Jupiter": 9,
        "Venus": 5,
        "Saturn": 0,
    }
    for planet in VISIBLE:
        chart = _chart({planet: expected[planet]})
        assert calculate_classical_neecha_bhanga(chart)[planet]["debilitation_sign_index"] == expected[planet]


def test_chart_response_contract_marks_only_the_matching_planet():
    # Cached chart payloads pass through this same additive upgrader, so an old
    # response and a newly calculated response expose identical display fields.
    from charts.routes import _attach_classical_neecha_bhanga

    chart = _chart({"Mercury": 11, "Jupiter": 3})
    _attach_classical_neecha_bhanga(chart)

    assert chart["planets"]["Mercury"]["neecha_bhanga"] is True
    assert chart["planets"]["Jupiter"]["neecha_bhanga"] is False
    assert chart["neecha_bhanga"]["Mercury"]["source"] == SOURCE
    assert chart["planet_result_delivery"]["planets"]["Mercury"]["conditions"]["neecha_bhanga"] is True
