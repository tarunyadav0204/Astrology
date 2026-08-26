from __future__ import annotations

from daily_prediction_spine import _build_trigger_evidence
from instant_aspect_policy import instant_activation_aspects


def test_nodal_instant_policy_keeps_only_conjunction_and_seventh_aspect() -> None:
    assert instant_activation_aspects("Rahu") == (1, 7)
    assert instant_activation_aspects("Ketu") == (1, 7)
    assert instant_activation_aspects("Rahu", include_conjunction=False) == (7,)
    assert instant_activation_aspects("Ketu", include_conjunction=False) == (7,)


def test_daily_nodal_trigger_does_not_emit_fifth_or_ninth_aspect() -> None:
    natal = {"planet": "Rahu", "house": 2, "sign": "Taurus", "longitude": 40.0}
    transit = {
        "planet": "Rahu",
        "available": True,
        "house": 2,
        "sign": "Taurus",
        "longitude": 40.0,
        "nakshatra": "Rohini",
    }
    natal_rows = {
        "Rahu": natal,
        "FifthTarget": {"planet": "FifthTarget", "house": 6},
        "SeventhTarget": {"planet": "SeventhTarget", "house": 8},
        "NinthTarget": {"planet": "NinthTarget", "house": 10},
    }

    trigger = _build_trigger_evidence("Rahu", natal, transit, natal_rows)
    aspects = {
        row["aspect_number"]: row["target_house"]
        for row in trigger["aspects_to_natal_planets"]
    }

    assert aspects.get(7) == 8
    assert 5 not in aspects
    assert 9 not in aspects
