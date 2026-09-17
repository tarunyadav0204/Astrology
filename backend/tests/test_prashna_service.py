from unittest.mock import patch

from prashna.service import analyze_prashna


def _fake_chart(_birth):
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    ]
    planets = {}
    placements = {
        "Sun": (4, 10, 5), "Moon": (1, 12, 2), "Mars": (0, 14, 1),
        "Mercury": (2, 6, 3), "Jupiter": (8, 4, 9), "Venus": (6, 8, 7),
        "Saturn": (9, 14, 10), "Rahu": (10, 6, 11), "Ketu": (4, 6, 5),
    }
    for name, (sign, degree, house) in placements.items():
        planets[name] = {
            "longitude": sign * 30 + degree,
            "sign": sign,
            "sign_name": signs[sign],
            "degree": degree,
            "house": house,
            "retrograde": False,
            "speed": 1.0 if name != "Moon" else 13.0,
        }
    return {
        "ascendant": 10.0,
        "houses": [{"sign": i, "sign_name": signs[i], "longitude": i * 30} for i in range(12)],
        "planets": planets,
    }


@patch("prashna.service.ChartCalculator")
def test_analyze_prashna_uses_question_clock_not_a_natal_label(calculator_cls):
    calculator_cls.return_value.calculate_chart.side_effect = _fake_chart
    result = analyze_prashna(
        question="Will this career move work?",
        category="career",
        date="1990-04-23",
        time="06:15:00",
        latitude=13.08,
        longitude=80.28,
        timezone="UTC+5:30",
        place="Chennai",
        horary_number=17,
    )
    assert result["clock"]["source"] == "question"
    assert result["clock"]["date"] == "1990-04-23"
    assert result["clock"]["place"] == "Chennai"
    assert result["clock"]["note"]
    assert result["question"]["karya_house"] == 10
    assert result["verdict"]["answer"] in {"yes", "no", "unclear"}
    assert result["chat_evidence"]["kind"] == "prashna"
    assert result["chat_evidence"]["clock"] == "question"
    assert result["kp_overlay"]["number"] == 17
    assert "Chennai" in result["explanation"]["setup"]
    assert "Lagnesha" not in result["explanation"]["why"]
    calculator_cls.return_value.calculate_chart.assert_called_once()
    clock = calculator_cls.return_value.calculate_chart.call_args[0][0]
    assert clock.date == "1990-04-23"
    assert clock.relation == "prashna"
