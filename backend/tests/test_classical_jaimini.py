import pytest

from calculators.classical_jaimini import (
    ClassicalJaiminiCalculator,
    ClassicalJaiminiInputError,
)


def _planet(longitude, house=None):
    row = {
        "longitude": float(longitude),
        "sign": int(float(longitude) // 30) % 12,
    }
    if house is not None:
        row["house"] = house
    return row


def _charts():
    d1 = {
        "ascendant": 5.0,
        "planets": {
            "Sun": _planet(25.0, 1),
            "Moon": _planet(54.0, 2),
            "Mars": _planet(83.0, 3),
            "Mercury": _planet(112.0, 4),
            "Jupiter": _planet(141.0, 5),
            "Venus": _planet(140.0, 5),
            "Saturn": _planet(199.0, 7),
            "Rahu": _planet(222.0, 8),
            "Ketu": _planet(42.0, 2),
        },
    }
    d9 = {
        "ascendant": 90.0,
        "planets": {
            "Sun": _planet(240.0),
            "Moon": _planet(270.0),
            "Mars": _planet(300.0),
            "Mercury": _planet(330.0),
            "Jupiter": _planet(0.0),
            "Venus": _planet(30.0),
            "Saturn": _planet(60.0),
            "Rahu": _planet(90.0),
            "Ketu": _planet(270.0),
        },
    }
    return d1, d9


def test_seven_and_eight_karaka_schemes_stay_separate_and_reverse_rahu():
    d1, d9 = _charts()
    result = ClassicalJaiminiCalculator(d1, d9).calculate()

    seven = result["karaka_schemes"]["seven"]
    eight = result["karaka_schemes"]["eight"]

    assert [row["planet"] for row in seven["rows"]] == [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
    ]
    # Rahu is at 12 degrees in its sign, therefore its reverse measure is 18.
    rahu = next(row for row in eight["rows"] if row["planet"] == "Rahu")
    assert rahu["ranking_degree"] == 18.0
    assert rahu["measured_in_reverse"] is True
    assert len(seven["rows"]) == 7
    assert len(eight["rows"]) == 8
    assert "PiK" not in {row["karaka_code"] for row in seven["rows"]}
    assert "PiK" in {row["karaka_code"] for row in eight["rows"]}


def test_rahu_at_zero_degrees_has_thirty_degree_reverse_measure():
    d1, d9 = _charts()
    d1["planets"]["Rahu"] = _planet(210.0)
    eight = ClassicalJaiminiCalculator(d1, d9).calculate()["karaka_schemes"]["eight"]
    rahu = next(row for row in eight["rows"] if row["planet"] == "Rahu")

    assert rahu["ranking_degree"] == 30.0
    assert rahu["ranking_degree_text"] == "30° 00′ 00″"
    assert eight["rows"][0]["planet"] == "Rahu"


def test_svamsha_and_karakamsha_use_atmakaraka_navamsa_sign():
    d1, d9 = _charts()
    result = ClassicalJaiminiCalculator(d1, d9).calculate()
    reference = result["svamsha_karakamsha"]["seven"]

    assert reference["atmakaraka"] == "Sun"
    assert reference["sign_name"] == "Sagittarius"
    assert reference["d9_reference_houses"][0]["occupants"] == ["Sun"]
    assert reference["terminology"]["svamsha"].startswith("The Atmakaraka")


def test_all_arudha_padas_include_classical_exception_derivation():
    d1, d9 = _charts()
    result = ClassicalJaiminiCalculator(d1, d9).calculate()
    padas = result["arudha_padas"]

    assert len(padas) == 12
    assert result["principal_padas"]["arudha_lagna"] == padas[0]
    assert result["principal_padas"]["darapada"] == padas[6]
    assert result["principal_padas"]["upapada"] == padas[11]

    # Aries lord Mars is in Gemini, so ordinary double-count gives Leo.
    assert padas[0]["lord"] == "Mars"
    assert padas[0]["sign_name"] == "Leo"
    assert padas[0]["exception_applied"] is False

    # Taurus source (A2) has Venus in Virgo, fourth from Taurus: take fourth.
    assert padas[1]["lord"] == "Venus"
    assert padas[1]["exception"] == "lord_in_4_or_10_take_4"
    assert padas[1]["sign_name"] == "Leo"


@pytest.mark.parametrize(
    ("mars_longitude", "exception", "result"),
    [
        (5.0, "lord_in_1_or_7_take_10", "Capricorn"),
        (185.0, "lord_in_1_or_7_take_10", "Capricorn"),
        (95.0, "lord_in_4_or_10_take_4", "Cancer"),
        (275.0, "lord_in_4_or_10_take_4", "Cancer"),
    ],
)
def test_arudha_exception_covers_lord_in_1_4_7_and_10(mars_longitude, exception, result):
    d1, d9 = _charts()
    d1["planets"]["Mars"] = _planet(mars_longitude)
    pada = ClassicalJaiminiCalculator(d1, d9).calculate()["arudha_padas"][0]

    assert pada["exception"] == exception
    assert pada["sign_name"] == result


@pytest.mark.parametrize(
    ("source", "targets"),
    [
        ("Aries", {"Leo", "Scorpio", "Aquarius"}),
        ("Taurus", {"Cancer", "Libra", "Capricorn"}),
        ("Gemini", {"Virgo", "Sagittarius", "Pisces"}),
    ],
)
def test_rashi_drishti_rules(source, targets):
    d1, d9 = _charts()
    rows = ClassicalJaiminiCalculator(d1, d9).calculate()["rashi_drishti"]
    row = next(value for value in rows if value["sign_name"] == source)
    assert {value["sign_name"] for value in row["aspected_signs"]} == targets


def test_upagrahas_are_not_silently_mixed_into_jaimini_graha_rows():
    d1, d9 = _charts()
    d1["planets"]["Mandi"] = _planet(5.0)
    d9["planets"]["Gulika"] = _planet(240.0)
    result = ClassicalJaiminiCalculator(d1, d9).calculate()

    aries = next(row for row in result["rashi_drishti"] if row["sign_name"] == "Aries")
    assert "Mandi" not in aries["occupants"]
    assert all(
        "Gulika" not in row["occupants"]
        for row in result["svamsha_karakamsha"]["seven"]["d9_reference_houses"]
    )


def test_missing_d9_is_reported_instead_of_silently_estimated():
    d1, _ = _charts()
    with pytest.raises(ClassicalJaiminiInputError, match="D9 planets"):
        ClassicalJaiminiCalculator(d1, {}).calculate()
