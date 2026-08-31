"""Regression fixtures from a published Parashara's Light 7.0.3 report."""

import asyncio
from types import SimpleNamespace

from starlette.requests import Request

from calculators.divisional_chart_calculator import DivisionalChartCalculator
from charts import routes as chart_routes


def _source_chart():
    def dms(sign_offset, degrees, minutes, seconds):
        return sign_offset + degrees + minutes / 60 + seconds / 3600

    return {
        "ascendant": dms(0, 14, 21, 33),
        "planets": {
            "Sun": {"longitude": dms(0, 8, 53, 24)},
            "Moon": {"longitude": dms(330, 8, 34, 55)},
            "Mars": {"longitude": dms(300, 7, 51, 8)},
            "Mercury": {"longitude": dms(0, 23, 47, 54)},
            "Jupiter": {"longitude": dms(60, 11, 55, 46)},
            "Venus": {"longitude": dms(300, 23, 57, 32)},
            "Saturn": {"longitude": dms(270, 1, 29, 51)},
            "Rahu": {"longitude": dms(270, 19, 17, 53)},
            "Ketu": {"longitude": dms(90, 19, 17, 53)},
        },
    }


# Values are one-based signs transcribed from pages 7-8 of the published
# Parashara's Light sample. They intentionally cover every supported varga
# from D12 upward, rather than deriving expectations with application code.
EXPECTED_SIGNS = {
    12: (6, [4, 3, 2, 10, 7, 8, 10, 5, 11]),
    16: (8, [5, 1, 9, 1, 3, 5, 1, 11, 11]),
    20: (10, [6, 10, 2, 4, 12, 12, 1, 1, 1]),
    24: (4, [12, 10, 11, 12, 2, 12, 5, 7, 7]),
    27: (1, [9, 5, 2, 10, 5, 4, 5, 9, 3]),
    30: (9, [11, 6, 11, 3, 9, 3, 2, 12, 12]),
    40: (8, [12, 6, 11, 8, 4, 8, 8, 8, 8]),
    45: (10, [2, 9, 4, 12, 2, 4, 3, 5, 5]),
    60: (5, [6, 5, 2, 12, 2, 10, 12, 12, 6]),
}

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]


def test_d12_and_higher_match_parasharas_light_signs_and_whole_sign_houses():
    calculator = DivisionalChartCalculator(_source_chart())

    for division, (expected_ascendant, expected_planets) in EXPECTED_SIGNS.items():
        chart = calculator.calculate_divisional_chart(division)["divisional_chart"]
        actual_ascendant = int(chart["ascendant"] // 30) + 1
        assert actual_ascendant == expected_ascendant, f"D{division} Ascendant"

        for planet, expected_sign in zip(PLANETS, expected_planets):
            placement = chart["planets"][planet]
            assert placement["sign"] + 1 == expected_sign, f"D{division} {planet} sign"
            expected_house = ((expected_sign - expected_ascendant) % 12) + 1
            assert placement["house"] == expected_house, f"D{division} {planet} house"


def test_divisional_route_infers_timezone_and_honors_true_node_profile(monkeypatch):
    monkeypatch.setattr(chart_routes, "_birth_hash_from_dict", lambda _birth: None)
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/calculate-divisional-chart",
            "headers": [],
            "client": ("127.0.0.1", 1234),
        }
    )
    payload = {
        "birth_data": {
            "name": "Parashara's Light sample",
            "date": "1990-04-23",
            "time": "06:15",
            "latitude": 13 + 5 / 60,
            "longitude": 80 + 17 / 60,
            # Deliberately omitted: the route must infer Asia/Kolkata, not UTC.
        },
        "division": 60,
        "calculation_profile": {"ayanamsha": "lahiri", "node_type": "true"},
    }

    response = asyncio.run(
        chart_routes.calculate_divisional_chart(
            payload,
            request,
            current_user=SimpleNamespace(userid=1),
        )
    )

    chart = response["divisional_chart"]
    assert int(chart["ascendant"] // 30) + 1 == 5
    assert chart["planets"]["Rahu"]["sign"] + 1 == 12
    assert chart["planets"]["Ketu"]["sign"] + 1 == 6
