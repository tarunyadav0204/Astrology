from calculators.planetary_dignities_calculator import (
    NAKSHATRAS,
    PlanetaryDignitiesCalculator,
)
from marriage_matching.constants import NAKSHATRA_NADI


def _chart():
    planets = {
        "Sun": (10.0, 0), "Moon": (47.0, 1), "Mars": (82.0, 2),
        "Mercury": (125.0, 4), "Jupiter": (159.0, 5), "Venus": (194.0, 6),
        "Saturn": (228.0, 7), "Rahu": (271.0, 9), "Ketu": (91.0, 3),
    }
    return {
        "ascendant": 5.0,
        "planets": {
            name: {
                "longitude": longitude,
                "sign": sign,
                "degree": longitude % 30,
                "house": ((sign - 0) % 12) + 1,
                "retrograde": name in {"Saturn", "Rahu", "Ketu"},
            }
            for name, (longitude, sign) in planets.items()
        },
    }


def test_nakshatra_placement_contract_covers_lagna_and_nine_grahas():
    chart = _chart()
    positions = PlanetaryDignitiesCalculator(chart).calculate_position_tables(
        birth_data={
            "date": "1990-01-01", "time": "12:00:00", "latitude": 28.6139,
            "longitude": 77.2090, "timezone": "Asia/Kolkata",
        }
    )
    rows = positions["nakshatra_placements"]
    assert [row["name"] for row in rows] == [
        "Lagna", "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ]
    for row in rows:
        assert 0 <= row["degree_in_nakshatra"] < 360 / 27
        assert row["pada_details"]["number"] in {1, 2, 3, 4}
        assert row["pada_details"]["navamsa_sign_name"]
        assert row["nakshatra_metadata"]["deity"]
        assert row["nakshatra_metadata"]["symbol"]
        assert row["nakshatra_metadata"]["shakti"]
        assert row["nakshatra_metadata"]["nature_class"] in {
            "kshipra", "ugra", "mishra", "dhruva", "mridu", "tikshna", "chara"
        }
        assert row["nakshatra_lord_state"]["planet"] == row["nakshatra_lord"]
        assert row["boundary_proximity"]["next_nakshatra"] in NAKSHATRAS


def test_ashtakoota_nadi_uses_the_alternating_traditional_sequence():
    assert [NAKSHATRA_NADI[index] for index in range(1, 10)] == [
        "Adya", "Madhya", "Antya",
        "Antya", "Madhya", "Adya",
        "Adya", "Madhya", "Antya",
    ]
    assert NAKSHATRA_NADI[27] == "Antya"
