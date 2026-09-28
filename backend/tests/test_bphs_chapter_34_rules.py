from __future__ import annotations

import pytest

from calculators.classical_functional_nature import PLANETS, functional_nature_table
from classical_rules.bphs.chapter_34 import (
    ASCENDANT_RULES,
    PASSAGE_GROUPS,
    RULES,
    compile_chapter_34_facts,
    coverage,
    evaluate_chapter_34,
)
from classical_rules.models import RuleInputUnavailable
from classical_rules.reading import build_classical_reading
from classical_rules.registry import evaluate_pack, get_pack
from tests.test_bphs_chapter_24_rules import _chart


def _aquarius_chart():
    chart = _chart()
    chart["ascendant"] = 310.0
    return chart


EXPECTED_CATALOGUE = {
    0: {"benefic": {"Sun", "Mars", "Jupiter"}, "malefic": {"Mercury", "Venus", "Saturn"}, "neutral": {"Moon"}},
    1: {"benefic": {"Sun", "Saturn"}, "malefic": {"Moon", "Mercury", "Jupiter", "Venus"}, "neutral": {"Mars"}},
    2: {"benefic": {"Venus"}, "malefic": {"Sun", "Mars", "Jupiter"}, "neutral": {"Moon", "Mercury", "Saturn"}},
    3: {"benefic": {"Moon", "Mars", "Jupiter"}, "malefic": {"Mercury", "Venus"}, "neutral": {"Sun", "Saturn"}},
    4: {"benefic": {"Sun", "Mars", "Jupiter"}, "malefic": {"Mercury", "Venus", "Saturn"}, "neutral": {"Moon"}},
    5: {"benefic": {"Mercury", "Venus"}, "malefic": {"Moon", "Mars", "Jupiter"}, "neutral": {"Sun", "Saturn"}},
    6: {"benefic": {"Mercury", "Saturn"}, "malefic": {"Sun", "Mars", "Jupiter"}, "neutral": {"Moon", "Venus"}},
    7: {"benefic": {"Sun", "Moon", "Jupiter"}, "malefic": {"Mercury", "Venus", "Saturn"}, "neutral": {"Mars"}},
    8: {"benefic": {"Sun", "Mars"}, "malefic": {"Venus"}, "neutral": {"Moon", "Mercury", "Jupiter", "Saturn"}},
    9: {"benefic": {"Mercury", "Venus"}, "malefic": {"Moon", "Mars", "Jupiter"}, "neutral": {"Sun", "Saturn"}},
    10: {"benefic": {"Venus", "Saturn"}, "malefic": {"Moon", "Mars", "Jupiter"}, "neutral": {"Sun", "Mercury"}},
    11: {"benefic": {"Moon", "Mars"}, "malefic": {"Sun", "Mercury", "Venus", "Saturn"}, "neutral": {"Jupiter"}},
}


def test_all_46_verses_are_owned_once_and_all_12_lagna_catalogues_are_published():
    result = coverage()
    assert result["total_verses"] == 46
    assert result["catalogued_verses"] == 46
    assert result["executable_verses"] == 42
    assert result["missing_verses"] == []
    assert result["duplicate_verses"] == []
    assert result["published_rules"] == 16
    assert len(ASCENDANT_RULES) == 12
    assert len(RULES) == 16
    assert {verse for group in PASSAGE_GROUPS for verse in group.verses()} == set(range(1, 47))


@pytest.mark.parametrize("ascendant", range(12))
def test_pinned_ascendant_catalogue_assigns_every_visible_planet_exactly_once(ascendant):
    table = functional_nature_table(ascendant)
    expected = EXPECTED_CATALOGUE[ascendant]
    actual = {
        nature: {planet for planet in PLANETS if table[planet]["stated_nature"] == nature}
        for nature in ("benefic", "malefic", "neutral")
    }
    assert actual == expected
    assert set.union(*actual.values()) == set(PLANETS)


def test_single_planet_yogakaraka_is_not_confused_with_lagna_ownership_or_relationship_yoga():
    expected = {
        0: set(), 1: {"Saturn"}, 2: set(), 3: {"Mars"},
        4: {"Mars"}, 5: set(), 6: {"Saturn"}, 7: set(),
        8: set(), 9: {"Venus"}, 10: {"Venus"}, 11: set(),
    }
    for ascendant, planets in expected.items():
        table = functional_nature_table(ascendant)
        assert {planet for planet, row in table.items() if row["is_yogakaraka"]} == planets

    # Aries Mars owns Lagna and House 8; this does not satisfy verse 13.
    assert functional_nature_table(0)["Mars"]["is_yogakaraka"] is False
    # Virgo Mercury/Venus yoga is a stated relationship condition, not two
    # inherent single-planet Yoga Karakas.
    virgo = functional_nature_table(5)
    assert virgo["Mercury"]["stated_yoga_note"]
    assert virgo["Venus"]["stated_yoga_note"]
    assert virgo["Mercury"]["is_yogakaraka"] is False
    assert virgo["Venus"]["is_yogakaraka"] is False


def test_maraka_house_geometry_and_textual_maraka_statement_remain_separate():
    aries = functional_nature_table(0)
    assert aries["Mars"]["is_maraka_lord"] is False
    assert aries["Mars"]["stated_maraka_note"] is None
    assert aries["Venus"]["is_maraka_lord"] is True
    assert "Independent Maraka" in aries["Venus"]["stated_maraka_note"]

    taurus = functional_nature_table(1)
    assert taurus["Mars"]["is_maraka_lord"] is True
    assert "stated passage" in taurus["Mars"]["stated_maraka_note"]
    # Jupiter owns House 8/11 for Taurus but is not manufactured into a
    # Lagna-specific Maraka statement by the generic house flag.
    assert taurus["Jupiter"]["stated_maraka_note"] is None


def test_chapter_evaluation_is_additive_source_grounded_and_has_no_fallback():
    result = evaluate_chapter_34(_aquarius_chart())
    assert result["ascendant_sign_name"] == "Aquarius"
    assert result["yogakaraka_rule"]["yogakarakas"] == ["Venus"]
    assert result["ascendant_catalogue"]["source"]["reference"] == "BPHS 34.41–42"
    assert result["fallback_used"] is False
    assert len(result["insights"]) == 1
    insight = result["insights"][0]
    assert insight["subject"]["key"] == "functional_planetary_roles"
    assert any("single-planet Yoga Karaka" in row for row in insight["supports"])
    assert any("Maraka" in row for row in insight["pressures"])
    assert {source["reference"] for source in insight["sources"]} == {
        "BPHS 34.2–10", "BPHS 34.11–12", "BPHS 34.13–15",
        "BPHS 34.16–17", "BPHS 34.41–42",
    }


def test_fact_set_carries_exact_rule_and_reference_for_later_chapters():
    facts = compile_chapter_34_facts(_aquarius_chart())
    venus_yogakaraka = facts.require("planet.Venus.is_yogakaraka")
    assert venus_yogakaraka.value is True
    assert venus_yogakaraka.source_rules == ("BPHS.34.13-15.SINGLE_PLANET_YOGAKARAKA",)
    assert venus_yogakaraka.source_references == ("BPHS 34.13–15",)

    mercury_role = facts.require("planet.Mercury.functional_nature")
    assert mercury_role.value == "neutral"
    assert mercury_role.source_references == ("BPHS 34.41–42",)
    assert facts.get("planet.Mercury.stated_maraka_role") is None


def test_corpus_reading_adds_a_separate_house_one_topic_without_altering_chapter_24():
    result = build_classical_reading(_chart())
    assert result["area_count"] == 12
    assert result["insight_count"] == 13
    house_one = result["areas"][0]
    assert house_one["key"] == "house_1"
    assert [subject["key"] for subject in house_one["subjects"]] == [
        "functional_planetary_roles", "house_lord_placement",
    ]
    assert len(house_one["insights"]) == 2
    assert next(row for row in house_one["insights"] if row["subject"]["key"] == "house_lord_placement")["sources"][0]["reference"] == "BPHS 24.4"


def test_registry_exposes_chapter_and_missing_ascendant_fails_loudly():
    detail = get_pack("bphs", 34)
    assert detail["coverage"]["catalogued_verses"] == 46
    assert detail["rules"][0]["source"]["reference"] == "BPHS 34.2–10"
    assert evaluate_pack("bphs", 34, _aquarius_chart())["ascendant_sign_name"] == "Aquarius"
    with pytest.raises(RuleInputUnavailable, match="ascendant"):
        evaluate_chapter_34({"planets": {}})


def test_chart_ascendant_is_always_read_as_longitude_not_as_a_sign_index():
    chart = _chart()
    chart["ascendant"] = 10.0
    assert evaluate_chapter_34(chart)["ascendant_sign_name"] == "Aries"


def test_relationship_yoga_uses_only_relations_named_in_verses_11_and_12():
    chart = _chart()  # Aries Lagna
    # Moon rules H4 and Sun rules H5. Put them together in Taurus.
    chart["planets"]["Sun"] = {"longitude": 45.0, "sign": 1, "degree": 15.0}
    result = evaluate_chapter_34(chart)["relationship_yoga_rule"]
    match = next(row for row in result["matches"] if set(row["planets"]) == {"Moon", "Sun"})
    assert match["relationships"] == ["conjunction in one sign"]
    assert match["adverse_ownership_block"] is False
    assert match["forms_yoga"] is True


def test_node_yogakaraka_requires_kendra_or_trikona_and_contact_from_other_lord_type():
    chart = _chart()  # Aries Lagna
    # Rahu in H4 receives the full seventh aspect of Sun, lord of H5.
    chart["planets"]["Rahu"] = {"longitude": 95.0, "sign": 3, "degree": 5.0}
    chart["planets"]["Sun"] = {"longitude": 275.0, "sign": 9, "degree": 5.0}
    result = evaluate_chapter_34(chart)["node_delivery_rule"]
    rahu = next(row for row in result["nodes"] if row["node"] == "Rahu")
    assert rahu["house"] == 4
    assert rahu["is_conditioned_yogakaraka"] is True
    assert {row["planet"]: row["contact"] for row in rahu["yogakaraka_contacts"]} == {
        "Sun": "full aspect",
        "Jupiter": "joined",
    }


def test_missing_nodes_are_reported_as_unavailable_without_a_fallback_or_fabricated_role():
    chart = _chart()
    chart["planets"].pop("Rahu")
    chart["planets"].pop("Ketu")
    result = evaluate_chapter_34(chart)
    assert result["node_delivery_rule"]["applicability"] == "unavailable"
    assert "Rahu" in result["node_delivery_rule"]["reason"]
    assert result["node_delivery_rule"]["fallback_used"] is False
    assert result["fallback_used"] is False
