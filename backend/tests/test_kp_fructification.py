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
        2: ["Moon"],
        10: ["Sun"],
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
    how = today["houses_giving_results"][0]["how"]
    assert how["summary"]


def test_today_absorbs_hour_houses_day_rps_missed():
    """Asc star can confirm hour houses that Day Lord + Moon star alone miss."""
    from app.kp.services.fructification_service import _merge_hour_primaries_into_today

    planet_sigs = {
        "Saturn": [1, 7],
        "Mercury": [1, 7],
        "Venus": [1],
        "Moon": [10],  # day moon-star does not hit 1/7
        "Sun": [10],   # day lord does not hit 1/7
        "Mars": [1, 7],  # asc star hits 1/7
        "Jupiter": [7],
    }
    dasha = {
        "mahadasha": {"planet": "Saturn"},
        "antardasha": {"planet": "Mercury"},
        "pratyantardasha": {"planet": "Venus"},
        "sookshma": {"planet": "Saturn"},
        "prana": {"planet": "Mercury"},
    }
    ruling = {
        "day_lord": "Sun",
        "ascendant": {"sign_lord": "Mars", "star_lord": "Mars", "sub_lord": "Jupiter"},
        "moon": {"sign_lord": "Moon", "star_lord": "Moon", "sub_lord": "Jupiter"},
    }
    as_of = datetime(2026, 8, 5, 10, 0, 0)
    today = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling,
        scope="today",
        as_of=as_of,
    )
    hour = analyze_window(
        planet_sigs=planet_sigs,
        dasha=dasha,
        ruling_planets=ruling,
        scope="hour",
        as_of=as_of,
    )
    assert [r["house"] for r in today["houses_giving_results"]] == []
    assert [r["house"] for r in hour["houses_giving_results"]] == [1, 7]

    merged = _merge_hour_primaries_into_today(today, hour, as_of=as_of, dasha=dasha)
    assert [r["house"] for r in merged["houses_giving_results"]] == [1, 7]
    assert merged["hour_houses_absorbed"] == [1, 7]
    assert all(r.get("included_from_hour") for r in merged["houses_giving_results"])
    assert len(merged["manifestations_deterministic"]) == 4


def test_manifestations_cover_all_subjects_for_cache_sharing():
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
    subjects = [item["subject"] for item in items]
    assert subjects == ["self", "spouse", "mother", "father"]
    self_item = items[0]
    assert self_item["signature_key"] == "kp:today:self:combined-2-11"
    assert {r["native_house"] for r in self_item["house_roles"]} == {2, 11}
    # Mother anchor=4: native 2→rel 11, native 11→rel 8
    mother = next(i for i in items if i["subject"] == "mother")
    assert {r["relative_house"] for r in mother["house_roles"]} == {8, 11}
    # Spouse anchor=7: native 2→rel 8, native 11→rel 5
    spouse = next(i for i in items if i["subject"] == "spouse")
    assert {r["relative_house"] for r in spouse["house_roles"]} == {5, 8}


def test_combined_theme_tones_for_mixed_houses():
    primary = [
        {"house": 1, "tone": "supportive", "activating_rps": ["Moon"]},
        {"house": 7, "tone": "challenging", "activating_rps": ["Venus"]},
    ]
    items = _build_deterministic_manifestations(
        scope="hour",
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
    assert len(items) == 4
    assert items[0]["outcome_tone"] == "mixed"
