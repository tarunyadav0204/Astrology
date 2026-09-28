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
    calculator = _calculator(29.0, 20.0, 42.0)
    monkeypatch.setattr(calculator, "_calculate_bhrigu_bindu_transits", lambda *_: {})

    result = calculator.calculate_bhrigu_bindu()

    assert result["longitude"] == 31.0
    assert result["sign"] == "Taurus"
    assert result["house"] == 2
    assert result["nakshatra"] == "Krittika"
    assert result["pada"] == 2
    assert result["derivation"] == "Shorter-arc midpoint between the natal Moon and Rahu"


def test_bhrigu_bindu_shorter_arc_wrap_is_preserved(monkeypatch):
    calculator = _calculator(300.0, 350.0, 10.0)
    monkeypatch.setattr(calculator, "_calculate_bhrigu_bindu_transits", lambda *_: {})

    result = calculator.calculate_bhrigu_bindu()

    assert result["longitude"] == 0.0
    assert result["sign"] == "Aries"
    assert result["house"] == 3
    assert result["nakshatra"] == "Ashwini"
    assert result["pada"] == 1
