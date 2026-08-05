from datetime import datetime

from app.kp.services.fructification_service import (
    analyze_window,
    _build_deterministic_manifestations,
    _tone_for_house,
    _tier_houses,
)


def test_tone_dusthana_without_fulfillment_is_challenging():
    planet_sigs = {"Venus": [6, 8], "Moon": [6]}
    assert _tone_for_house(6, ["Venus", "Moon"], planet_sigs) == "challenging"


def test_tone_with_fulfillment_and_dusthana_is_mixed():
    planet_sigs = {"Jupiter": [10, 11, 6]}
    assert _tone_for_house(10, ["Jupiter"], planet_sigs) == "mixed"


def test_tier_anchor_alone_is_primary_day_lord_alone_secondary():
    candidate = {
        2: ["Moon"],       # moon star lord alone → primary
        10: ["Sun"],       # day lord alone → secondary
        11: ["Moon", "Sun"],
    }
    primary, secondary = _tier_houses(
        candidate_houses=candidate,
        eligible={2, 10, 11},
        primary_anchors=["Moon"],
    )
    assert [r["house"] for r in primary] == [2, 11]
    assert [r["house"] for r in secondary] == [10]


def test_analyze_window_intersects_dasha_and_rps():
    planet_sigs = {
        "Saturn": [10, 11],
        "Mercury": [2, 11],
        "Venus": [2, 6],
        "Moon": [2, 11],
        "Sun": [10],
        "Mars": [6, 8],
        "Jupiter": [9],
    }
    dasha = {
        "mahadasha": {"planet": "Saturn"},
        "antardasha": {"planet": "Mercury"},
        "pratyantardasha": {"planet": "Venus"},
        "sookshma": {"planet": "Moon"},
        "prana": {"planet": "Sun"},
    }
    # Base = AD∪PD = Mercury∪Venus → {2,6,11}
    # Today eligible = base ∩ Moon = {2,11}
    # Day RPs: Day=Sun, Moon star=Moon → RP houses {2,10,11}
    # Results today primary: {2,11}
    ruling = {
        "day_lord": "Sun",
        "ascendant": {"sign_lord": "Mars", "star_lord": "Mars", "sub_lord": "Jupiter"},
        "moon": {"sign_lord": "Moon", "star_lord": "Moon", "sub_lord": "Mercury"},
    }
    today = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling,
        scope="today",
        as_of=datetime(2026, 8, 5, 10, 0, 0),
    )
    houses = [r["house"] for r in today["houses_giving_results"]]
    assert houses == [2, 11]
    assert today["dasha_gate"]["eligible_houses"] == [2, 11]
    assert today["calculation"]["formula"]
    assert len(today["calculation"]["steps"]) >= 5
    how = today["houses_giving_results"][0]["how"]
    assert how["summary"]
    assert [s["title"] for s in how["steps"]] == [
        "Dasha permission",
        "Ruling-planet trigger",
        "Strength tier",
        "Outcome tone",
    ]

    # Hour: eligible also needs Prana(Sun)={10} → today∩prana = empty → fallback to today eligible
    hour = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling,
        scope="hour",
        as_of=datetime(2026, 8, 5, 10, 0, 0),
    )
    assert hour["dasha_gate"]["prana_fallback"] is True
    hour_houses = {r["house"] for r in hour["houses_giving_results"]}
    assert 2 in hour_houses or 11 in hour_houses


def test_deterministic_manifestations_match_combinations():
    primary = [
        {"house": 2, "tone": "supportive", "activating_rps": ["Moon"]},
        {"house": 11, "tone": "supportive", "activating_rps": ["Moon", "Sun"]},
    ]
    items = _build_deterministic_manifestations(
        scope="today",
        primary_houses=primary,
        as_of=datetime(2026, 8, 5, 10, 0, 0),
        dasha={
            "mahadasha": {"planet": "Saturn"},
            "antardasha": {"planet": "Mercury"},
            "pratyantardasha": {"planet": "Venus"},
            "sookshma": {"planet": "Moon"},
            "prana": {"planet": "Sun"},
        },
    )
    keys = {item["signature_key"] for item in items}
    assert "kp:today:income_accumulation" in keys
