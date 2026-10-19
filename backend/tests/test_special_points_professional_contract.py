from calculators.sniper_points_calculator import SniperPointsCalculator


def _calculator(ascendant: float, moon: float, rahu: float) -> SniperPointsCalculator:
    d1 = {
        "ascendant": ascendant,
        "planets": {
            "Moon": {"longitude": moon, "sign": int(moon // 30), "house": 1},
            "Rahu": {"longitude": rahu, "sign": int(rahu // 30), "house": 1},
        },
    }
    return SniperPointsCalculator(d1, {}, {})


def test_bhrigu_bindu_house_uses_whole_sign_distance(monkeypatch):
    # Ascendant is late Aries. The Moon/Rahu midpoint is early Taurus. Under
    # whole-sign houses Taurus must be House 2 even though it is less than 30
    # degrees ahead of the exact ascendant longitude.
    calculator = _calculator(29.0, 42.0, 20.0)
    monkeypatch.setattr(calculator, "_calculate_bhrigu_bindu_transits", lambda *_: {})

    result = calculator.calculate_bhrigu_bindu()

    assert result["longitude"] == 31.0
    assert result["sign"] == "Taurus"
    assert result["house"] == 2
    assert result["nakshatra"] == "Krittika"
    assert result["pada"] == 2
    assert "forward zodiacal arc" in result["derivation"]


def test_bhrigu_bindu_forward_arc_wraps_through_aries(monkeypatch):
    calculator = _calculator(300.0, 10.0, 350.0)
    monkeypatch.setattr(calculator, "_calculate_bhrigu_bindu_transits", lambda *_: {})

    result = calculator.calculate_bhrigu_bindu()

    assert result["longitude"] == 0.0
    assert result["sign"] == "Aries"
    assert result["house"] == 3
    assert result["nakshatra"] == "Ashwini"
    assert result["pada"] == 1


def test_bhrigu_bindu_matches_patels_published_example():
    # Printed pp. 107–108: Libra 12°13′ Moon, Capricorn 17°06′ Rahu.
    result = _calculator(0, 192 + 13 / 60, 287 + 6 / 60).calculate_bhrigu_bindu(include_transits=False)
    assert result["longitude"] == 59.66
    assert result["sign"] == "Taurus"
    assert result["house"] == 2
    assert result["lord"] == "Venus"
    assert result["nakshatra"] == "Mrigashira"
    assert result["pada"] == 2


def test_bhrigu_bindu_direction_is_not_shortest_arc():
    # Reversing the endpoints selects the opposite midpoint.
    result = _calculator(300, 350, 10).calculate_bhrigu_bindu(include_transits=False)
    assert result["longitude"] == 180
    assert result["sign"] == "Libra"


def test_bhrigu_bindu_preserves_client_contract_and_transit_target(monkeypatch):
    calculator = _calculator(0, 40, 135)
    calls = []
    transit_payload = {"Saturn": {"exact_transit_date": "2030-01-01"}}
    def transits(longitude, sign):
        calls.append((longitude, sign))
        return transit_payload
    monkeypatch.setattr(calculator, "_calculate_bhrigu_bindu_transits", transits)
    result = calculator.calculate_bhrigu_bindu()
    assert calls == [(267.5, 8)]
    assert result["upcoming_transits"] == transit_payload
    assert set(result) == {
        "point_name", "longitude", "sign", "degree", "house", "lord",
        "nakshatra", "pada", "degree_in_nakshatra", "derivation",
        "significance", "transit_watch", "formatted", "upcoming_transits",
    }
    assert isinstance(result["longitude"], float)
    assert isinstance(result["house"], int)
    assert isinstance(result["formatted"], str)
    assert calculator.calculate_bhrigu_bindu(include_transits=False)["upcoming_transits"]["status"] == "not_requested"
    assert len(calls) == 1


def test_bhrigu_bindu_conjunction_and_exact_opposition():
    assert _calculator(0, 45, 45).calculate_bhrigu_bindu(False)["longitude"] == 45
    assert _calculator(0, 190, 10).calculate_bhrigu_bindu(False)["longitude"] == 100
    assert _calculator(0, 10, 190).calculate_bhrigu_bindu(False)["longitude"] == 280


def test_bhrigu_bindu_compact_chat_consumer_keeps_corrected_position():
    from context_agents.agents.sniper_pts import _compress_bhrigu_bindu

    result = _calculator(0, 40, 135).calculate_bhrigu_bindu(include_transits=False)
    assert _compress_bhrigu_bindu(result) == {
        'lon': 267.5, 'd': 27.5, 'h': 9, 'ld': 'Jupiter', 's': 9,
    }
