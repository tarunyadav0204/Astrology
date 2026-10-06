from copy import deepcopy

import pytest

from classical_rules.deva_keralam.chart_facts import (
    ChartFactInputError,
    compile_deva_keralam_chart_facts,
)
from classical_rules.deva_keralam.draft_compiler import (
    UnknownDraftFactKey,
    compile_draft_expression,
)
from classical_rules.deva_keralam.ontology import is_canonical_fact_key
from classical_rules.deva_keralam.reviewed_aliases import UnknownReviewedValue


def _chart():
    return {
        "ascendant": 1.05,
        "planets": {
            "Sun": {"longitude": 10.0},
            "Moon": {"longitude": 95.0},
            "Mars": {"longitude": 5.0},
            "Mercury": {"longitude": 20.0},
            "Jupiter": {"longitude": 65.0},
            "Venus": {"longitude": 35.0},
            "Saturn": {"longitude": 185.0},
            "Rahu": {"longitude": 250.0},
            "Ketu": {"longitude": 70.0},
        },
    }


def test_adapter_emits_only_canonical_positive_and_negative_natal_facts():
    source = _chart()
    original = deepcopy(source)
    facts = compile_deva_keralam_chart_facts(
        source, ascendant_longitude_uncertainty_arcseconds=1,
    )
    payload = facts.as_dict()["facts"]

    assert source == original
    assert all(is_canonical_fact_key(key) for key in payload)
    assert payload["deva_keralam.ascendant.rashi.name"]["value"] == "Aries"
    assert payload["deva_keralam.house.4.rashi.name"]["value"] == "Cancer"
    assert payload["deva_keralam.house.4.lord"]["value"] == "Moon"
    assert payload["deva_keralam.house.4.lord_house"]["value"] == 4
    assert payload["deva_keralam.planet.Mars.lordships"]["value"] == [1, 8]
    assert payload["deva_keralam.planet.Sun.navamsa.name"]["value"] == "Cancer"
    assert payload["deva_keralam.planet.Sun.dignity"]["value"] == "exalted"
    assert payload["deva_keralam.relationship.conjunction.Sun.Mercury.present"]["value"] is True
    assert payload["deva_keralam.relationship.conjunction.Sun.Moon.present"]["value"] is False
    assert payload["deva_keralam.relationship.aspect.Mars.Moon.present"]["value"] is True
    assert payload["deva_keralam.relationship.aspect.Mars.Moon.numbers"]["value"] == [4]
    assert payload["deva_keralam.relationship.aspect.Mars.Venus.present"]["value"] is False
    assert payload["deva_keralam.planet.Rahu.aspected_houses"]["value"] == [3]
    assert payload["deva_keralam.precision.ascendant.reliable"]["value"] is True


def test_typed_dasha_transit_and_age_facts_are_deterministic():
    facts = compile_deva_keralam_chart_facts(
        _chart(),
        ascendant_longitude_uncertainty_arcseconds=1,
        timing_context={
            "birth_date": "2000-10-10",
            "as_of": "2026-10-05",
            "dasha": {
                "MD": {"lord": "Saturn", "ordinal": 1, "start": "2020-01-01", "end": "2039-01-01", "active": True},
                "AD": {"lord": "Venus", "ordinal": 2},
            },
            "transits": {"Mars": {"longitude": 95.0}},
        },
    ).as_dict()["facts"]

    assert facts["deva_keralam.timing.dasha.mahadasha.lord"]["value"] == "Saturn"
    assert facts["deva_keralam.timing.dasha.mahadasha.ordinal"]["value"] == 1
    assert facts["deva_keralam.timing.dasha.antardasha.lord"]["value"] == "Venus"
    assert facts["deva_keralam.timing.transit.Mars.house"]["value"] == 4
    assert facts["deva_keralam.timing.transit.Mars.conjunct_natal_planets"]["value"] == ["Moon"]
    assert facts["deva_keralam.timing.native.completed_age_years"]["value"] == 25


def test_reviewed_abala_prabha_aliases_compile_to_table_1_prabhaa_only():
    for supplied in ("Abala", "Prabha", "Prabhaa"):
        compiled = compile_draft_expression({
            "op": "fact",
            "key": "ascendant.nadiamsa.name",
            "comparator": "equals",
            "value": supplied,
        })
        assert compiled["key"] == "deva_keralam.ascendant.nadiamsa.name"
        assert compiled["value"] == "Prabhaa"
        if supplied != "Prabhaa":
            assert compiled["reviewed_value_alias"]["canonical_ordinal"] == 16
            assert "C. G. Rajan" in compiled["reviewed_value_alias"]["source_reference"]
        else:
            assert "reviewed_value_alias" not in compiled


def test_unknown_draft_keys_and_unreviewed_name_values_fail_closed():
    with pytest.raises(UnknownDraftFactKey):
        compile_draft_expression({"op": "fact", "key": "planet.Mars.maybe_aspects", "value": True})
    with pytest.raises(UnknownReviewedValue):
        compile_draft_expression({
            "op": "fact", "key": "ascendant.nadiamsa.name", "value": "Probable Prabha",
        })


def test_contradictory_supplied_chart_fields_fail_closed():
    chart = _chart()
    chart["planets"]["Sun"]["sign"] = 3
    with pytest.raises(ChartFactInputError, match="contradicts"):
        compile_deva_keralam_chart_facts(chart)


def test_structural_bindings_expose_modality_parity_occupants_and_vargottama():
    facts = compile_deva_keralam_chart_facts(
        _chart(), ascendant_longitude_uncertainty_arcseconds=1,
    ).as_dict()["facts"]

    assert facts["deva_keralam.ascendant.degree_in_sign"]["value"] == pytest.approx(1.05)
    assert facts["deva_keralam.ascendant.rashi.modality"]["value"] == "movable"
    assert facts["deva_keralam.ascendant.navamsa.parity"]["value"] in {"odd", "even"}
    assert facts["deva_keralam.house.1.occupants"]["value"] == ["Sun", "Mars", "Mercury"]
    assert facts["deva_keralam.house.2.rashi.modality"]["value"] == "fixed"
    assert facts["deva_keralam.planet.Sun.degree_in_sign"]["value"] == pytest.approx(10.0)
    assert facts["deva_keralam.planet.Sun.rashi.modality"]["value"] == "movable"
    assert facts["deva_keralam.planet.Sun.navamsa.modality"]["value"] == "movable"
    assert facts["deva_keralam.planet.Sun.navamsa.parity"]["value"] == "even"
    assert facts["deva_keralam.planet.Sun.vargottama"]["value"] is False


def test_all_house_lords_share_one_identity_placement_and_varga_grammar():
    facts = compile_deva_keralam_chart_facts(
        _chart(), ascendant_longitude_uncertainty_arcseconds=1,
    ).as_dict()["facts"]

    for house in range(1, 13):
        prefix = f"deva_keralam.house.{house}.lord"
        lord = facts[f"{prefix}.name"]["value"]
        assert lord == facts[f"deva_keralam.house.{house}.lord"]["value"]
        assert facts[f"{prefix}.house"]["value"] == facts[f"deva_keralam.planet.{lord}.house"]["value"]
        assert facts[f"{prefix}.rashi.name"]["value"] == facts[f"deva_keralam.planet.{lord}.rashi.name"]["value"]
        assert facts[f"{prefix}.navamsa.name"]["value"] == facts[f"deva_keralam.planet.{lord}.navamsa.name"]["value"]
        assert facts[f"{prefix}.nadiamsa.name"]["value"] == facts[f"deva_keralam.planet.{lord}.nadiamsa.name"]["value"]
        assert facts[f"{prefix}.vargottama"]["value"] == facts[f"deva_keralam.planet.{lord}.vargottama"]["value"]


def test_house_lord_identity_survives_partial_chart_but_placement_fails_closed():
    facts = compile_deva_keralam_chart_facts({"ascendant": 1.0, "planets": {}}).as_dict()["facts"]
    assert facts["deva_keralam.house.1.lord.name"]["value"] == "Mars"
    assert facts["deva_keralam.house.12.lord.name"]["value"] == "Jupiter"
    assert "deva_keralam.house.1.lord.house" not in facts
    assert "deva_keralam.house.12.lord.navamsa.name" not in facts


def test_sign_boundary_reassigns_house_lord_geometry_without_rounding():
    before = compile_deva_keralam_chart_facts({
        "ascendant": 29.999999,
        "planets": {"Venus": {"longitude": 29.999999}},
    }).as_dict()["facts"]
    boundary = compile_deva_keralam_chart_facts({
        "ascendant": 30.0,
        "planets": {"Venus": {"longitude": 30.0}},
    }).as_dict()["facts"]

    assert before["deva_keralam.ascendant.rashi.name"]["value"] == "Aries"
    assert boundary["deva_keralam.ascendant.rashi.name"]["value"] == "Taurus"
    assert before["deva_keralam.planet.Venus.rashi.name"]["value"] == "Aries"
    assert boundary["deva_keralam.planet.Venus.rashi.name"]["value"] == "Taurus"
    assert boundary["deva_keralam.planet.Venus.degree_in_sign"]["value"] == 0.0
    assert boundary["deva_keralam.house.1.lord.name"]["value"] == "Venus"
    assert boundary["deva_keralam.house.1.lord.house"]["value"] == 1
    assert boundary["deva_keralam.house.1.lord.nadiamsa.birth_time_precision_warning"]["value"] is True


def test_relationship_facts_preserve_aspect_direction_and_relative_house_order():
    facts = compile_deva_keralam_chart_facts(
        _chart(), ascendant_longitude_uncertainty_arcseconds=1,
    ).as_dict()["facts"]

    assert facts["deva_keralam.relationship.aspect.Mars.Moon.present"]["value"] is True
    assert facts["deva_keralam.relationship.aspect.Mars.Moon.numbers"]["value"] == [4]
    assert facts["deva_keralam.relationship.aspect.Moon.Mars.present"]["value"] is False
    assert facts["deva_keralam.relationship.aspect.Moon.Mars.numbers"]["value"] == []
    assert facts["deva_keralam.relationship.relative_house.Moon.Mars"]["value"] == 4
    assert facts["deva_keralam.relationship.relative_house.Mars.Moon"]["value"] == 10
    assert facts["deva_keralam.planet.Mars.aspects_planets"]["value"] == ["Moon", "Saturn"]
    assert "Mars" in facts["deva_keralam.planet.Moon.aspected_by_planets"]["value"]


def test_conjunction_pair_key_is_canonical_but_planet_lists_are_symmetric():
    facts = compile_deva_keralam_chart_facts(_chart()).as_dict()["facts"]

    assert facts["deva_keralam.relationship.conjunction.Sun.Mercury.present"]["value"] is True
    assert "deva_keralam.relationship.conjunction.Mercury.Sun.present" not in facts
    assert "Mercury" in facts["deva_keralam.planet.Sun.conjunct_planets"]["value"]
    assert "Sun" in facts["deva_keralam.planet.Mercury.conjunct_planets"]["value"]


def test_house_lord_relationships_are_explicit_and_directional():
    facts = compile_deva_keralam_chart_facts(_chart()).as_dict()["facts"]

    # Aries Lagna: Mars rules H1 and casts its fourth aspect to the Moon.
    assert facts["deva_keralam.house.1.lord.relationship.aspect_to.Moon.present"]["value"] is True
    assert facts["deva_keralam.house.1.lord.relationship.aspect_to.Moon.numbers"]["value"] == [4]
    assert facts["deva_keralam.house.1.lord.relationship.aspected_by.Moon.present"]["value"] is False
    assert facts["deva_keralam.house.4.lord.relationship.aspected_by.Mars.present"]["value"] is True
    assert facts["deva_keralam.house.1.lord.relationship.conjunction.Mercury.present"]["value"] is True
    assert facts["deva_keralam.house.1.lord.relative_to.Moon.house"]["value"] == 10


def test_dispositor_projection_exposes_identity_placement_and_separate_relations():
    facts = compile_deva_keralam_chart_facts(_chart()).as_dict()["facts"]

    # Mercury is in Aries, so its Rashi dispositor is Mars.
    assert facts["deva_keralam.planet.Mercury.dispositor.name"]["value"] == "Mars"
    assert facts["deva_keralam.planet.Mercury.dispositor.house"]["value"] == 1
    assert facts["deva_keralam.planet.Mercury.dispositor.rashi.name"]["value"] == "Aries"
    assert facts["deva_keralam.planet.Mercury.dispositor.navamsa.name"]["value"] == "Taurus"
    assert facts["deva_keralam.planet.Mercury.dispositor.nadiamsa.name"]["value"] == facts["deva_keralam.planet.Mars.nadiamsa.name"]["value"]
    assert facts["deva_keralam.planet.Mercury.dispositor.relationship.conjunction.Sun.present"]["value"] is True
    assert facts["deva_keralam.planet.Mercury.dispositor.relationship.aspect_to.Moon.present"]["value"] is True
    assert facts["deva_keralam.planet.Mercury.dispositor.relationship.aspected_by.Moon.present"]["value"] is False


def test_nodes_keep_only_seventh_aspect_in_all_relationship_projections():
    facts = compile_deva_keralam_chart_facts(_chart()).as_dict()["facts"]

    assert facts["deva_keralam.planet.Rahu.aspected_houses"]["value"] == [3]
    assert facts["deva_keralam.relationship.aspect.Rahu.house.3.numbers"]["value"] == [7]
    assert facts["deva_keralam.relationship.aspect.Rahu.house.1.present"]["value"] is False
    assert facts["deva_keralam.relationship.aspect.Rahu.Ketu.present"]["value"] is True
    assert facts["deva_keralam.relationship.aspect.Rahu.Ketu.numbers"]["value"] == [7]


def test_partial_chart_omits_unavailable_house_lord_and_dispositor_relations():
    facts = compile_deva_keralam_chart_facts({
        "ascendant": 1.0,
        "planets": {"Sun": {"longitude": 10.0}},
    }).as_dict()["facts"]

    assert facts["deva_keralam.house.1.lord.name"]["value"] == "Mars"
    assert "deva_keralam.house.1.lord.relationship.aspect_to.Sun.present" not in facts
    assert facts["deva_keralam.planet.Sun.dispositor.name"]["value"] == "Mars"
    assert "deva_keralam.planet.Sun.dispositor.house" not in facts
    assert "deva_keralam.planet.Sun.dispositor.relationship.conjunction.Sun.present" not in facts
