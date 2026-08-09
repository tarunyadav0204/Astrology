from __future__ import annotations

from prediction_engine.context import CalculationContext
from prediction_engine.contracts import BirthChartInput, PredictionWindow
from prediction_engine.house_activation import (
    HouseActivationEngine,
    _repeated_natal_relationships,
)


PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


def _chart():
    planets = {
        planet: {
            "house": index + 1,
            "sign": index,
            "longitude": (index * 30.0) + 5.0,
            "retrograde": False,
        }
        for index, planet in enumerate(PLANETS)
    }
    # Jupiter in H1 has an exact natal 5th-house aspect to Saturn in H5.
    planets["Jupiter"] = {"house": 1, "sign": 0, "longitude": 5.0, "retrograde": False}
    planets["Saturn"] = {"house": 5, "sign": 4, "longitude": 125.0, "retrograde": False}
    return {
        "ascendant": 0.0,
        "houses": [{"house_number": house, "sign": house - 1} for house in range(1, 13)],
        "planets": planets,
    }


def test_repeated_relationship_requires_same_planet_pair_and_aspect_geometry():
    rows = _repeated_natal_relationships(
        _chart(),
        {"Jupiter": {"house": 1}},
        {"Jupiter"},
        {"Jupiter": {"MD", "AD", "PD"}},
    )
    saturn = next(row for row in rows if row["target_planet"] == "Saturn")
    assert saturn["relation"] == "aspect"
    assert saturn["aspect_number"] == 5

    moved = _repeated_natal_relationships(
        _chart(),
        {"Jupiter": {"house": 9}},
        {"Jupiter"},
        {"Jupiter": {"MD"}},
    )
    assert not any(row["target_planet"] == "Saturn" for row in moved)


def test_house_ledger_serializes_clear_confirmations_even_without_trace():
    chart = _chart()
    window = PredictionWindow(
        "2026-08-01", "2026-08-10", "Jupiter", "Jupiter", "Jupiter", "sig"
    )
    states = {
        planet: {
            "house": int(chart["planets"][planet]["house"]),
            "longitude": float(chart["planets"][planet]["longitude"]),
            "sign": int(chart["planets"][planet]["sign"]),
            "retrograde": False,
        }
        for planet in PLANETS
    }
    calculation = CalculationContext(
        birth=BirthChartInput.from_mapping({
            "date": "1980-04-02", "time": "14:55",
            "latitude": 29.1492, "longitude": 75.7217,
            "timezone": "Asia/Kolkata",
        }),
        chart=chart,
        natal_dignities={}, yogi_points={}, gandanta={}, badhaka_lord="Saturn",
        windows=(window,), transit_states_by_signature={"sig": states},
        divisional_charts={},
        transit_return_passes={
            "Jupiter": ({
                "planet": "Jupiter", "natal_longitude": 5.0,
                "exact_longitude": 5.0, "exact_distance_degrees": 0.0,
                "orb_degrees": 1.0,
                "start_at": "2026-08-03T00:00:00+00:00",
                "exact_at": "2026-08-04T00:00:00+00:00",
                "end_at": "2026-08-05T00:00:00+00:00",
                "motion": "direct", "retrograde": False,
                "pass_number": 1, "pass_label": "Direct pass 1",
                "pass_sequence": "Direct",
            },),
        },
    )

    row = next(
        item for item in HouseActivationEngine().evaluate_window(calculation, window)
        if item.house == 1
    ).to_dict(include_evidence=False)
    kinds = {item["kind"] for item in row["transit_confirmations"]}
    labels = [item["label"] for item in row["transit_confirmations"]]

    assert row["evidence"] == []
    assert "natal_sign_return" in kinds
    assert "exact_degree_return" in kinds
    assert "exact_nakshatra_return" in kinds
    assert "repeated_natal_relationship" in kinds
    assert any("returned to natal sign" in label for label in labels)
    assert any("exact natal longitude return" in label for label in labels)
    assert any("exact nakshatra return" in label for label in labels)
