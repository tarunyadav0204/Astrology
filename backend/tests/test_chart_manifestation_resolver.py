from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from prediction_engine.chart_manifestations import ChartManifestationResolver
from prediction_engine.contracts import (
    ActivationAssessment,
    ActivationBand,
    BirthChartInput,
    DashaRelationship,
    HouseActivation,
    HouseActivationState,
    OutcomeAssessment,
    Polarity,
    PredictionRequest,
    PredictionWindow,
)


def _request(*, subjects=("self",), domains=None):
    return PredictionRequest(
        birth=BirthChartInput.from_mapping({
            "date": "1990-01-01",
            "time": "12:00",
            "latitude": 28.6,
            "longitude": 77.2,
            "timezone": "Asia/Kolkata",
        }),
        as_of=date(2026, 7, 23),
        horizon_days=30,
        subjects=subjects,
        domains=domains,
        maximum_candidates=10,
    )


def _activation(
    house,
    carrier,
    *,
    tone=Polarity.SUPPORTIVE,
    relationship=(),
    start="2026-07-20",
    end="2026-08-10",
):
    window = PredictionWindow(
        start_date=start,
        end_date=end,
        mahadasha="Saturn",
        antardasha="Rahu",
        pratyantardasha="Saturn",
        transit_signature=f"transit-{house}",
    )
    return HouseActivation(
        house=house,
        window=window,
        state=HouseActivationState.FULLY_REINFORCED,
        activation=ActivationAssessment(
            band=ActivationBand.STRONG,
            independent_confirmations=4,
            active_dasha_levels=("MD", "AD", "PD"),
            transit_reinforced=True,
            natal_position_reinforced=True,
            primary_houses_covered=(house,),
            carrier_planets=(carrier,),
            rule_id="test",
        ),
        outcome=OutcomeAssessment(
            tone=tone,
            supportive_factors=1 if tone == Polarity.SUPPORTIVE else 0,
            challenging_factors=1 if tone == Polarity.CHALLENGING else 0,
            mixed_factors=1 if tone == Polarity.MIXED else 0,
            rule_id="test",
        ),
        house_lord="Sun",
        natal_connections=({"level": "MD", "planet": carrier, "relation": "occupation"},),
        transit_connections=(),
        dasha_relationships=relationship,
        trigger_planets=(carrier,),
        timing_triggers=(),
        evidence=(),
    )


def test_resolver_accepts_shared_direct_carrier_and_is_deterministic():
    rows = (_activation(2, "Saturn"), _activation(11, "Saturn"))
    resolver = ChartManifestationResolver()
    first = resolver.resolve(_request(domains=("wealth",)), rows)
    second = resolver.resolve(_request(domains=("wealth",)), rows)

    assert len(first) == 1
    assert first[0].signature_key == "income_accumulation"
    assert first[0].carrier_coherence == "shared_direct_carrier"
    assert first[0].manifestation_id == second[0].manifestation_id
    assert first[0].house_roles[0].dasha_connections == (
        "Saturn connects through natal occupation (MD)",
    )
    assert "House 2 is supportive" in first[0].rationale[-1]


def test_resolver_rejects_unrelated_carrier_union():
    rows = (_activation(2, "Saturn"), _activation(11, "Rahu"))
    assert ChartManifestationResolver().resolve(_request(), rows) == ()


def test_resolver_accepts_declared_sambandha_between_direct_carriers():
    relationship = (
        DashaRelationship(
            first_level="MD",
            first_planet="Saturn",
            second_level="AD",
            second_planet="Rahu",
            relations=("conjunction",),
            natal_houses=(2,),
        ),
    )
    rows = (
        _activation(2, "Saturn", relationship=relationship),
        _activation(11, "Rahu", relationship=relationship),
    )
    result = ChartManifestationResolver().resolve(_request(), rows)

    assert result[0].carrier_coherence == "connected_dasha_carriers"
    assert result[0].carrier_planets == ("Rahu", "Saturn")
    assert result[0].carrier_relationships


def test_focus_house_pressure_cannot_be_averaged_into_supportive_tone():
    # In financial obligation, H6 is the event-defining house.
    rows = (
        _activation(2, "Saturn", tone=Polarity.SUPPORTIVE),
        _activation(6, "Saturn", tone=Polarity.CHALLENGING),
    )
    result = ChartManifestationResolver().resolve(_request(), rows)
    obligation = next(
        item for item in result if item.signature_key == "financial_obligation"
    )
    assert obligation.outcome_tone == Polarity.CHALLENGING


def test_subject_rotation_uses_relative_houses_without_relabelling_native_house():
    # Native H8 is spouse's H2; native H5 is spouse's H11.
    # Native H7 independently identifies the spouse frame in the same chain.
    rows = (
        _activation(8, "Saturn"),
        _activation(5, "Saturn"),
        _activation(7, "Saturn"),
    )
    result = ChartManifestationResolver().resolve(
        _request(subjects=("spouse",)), rows
    )
    income = next(item for item in result if item.signature_key == "income_accumulation")

    assert [role.native_house for role in income.house_roles] == [8, 5]
    assert [role.relative_house for role in income.house_roles] == [2, 11]
    assert income.subject_confirmation["method"] == "anchor_house"


def test_relative_frame_is_rejected_without_anchor_or_karaka_lock():
    rows = (_activation(8, "Saturn"), _activation(5, "Saturn"))
    result = ChartManifestationResolver().resolve(
        _request(subjects=("spouse",)), rows
    )
    assert result == ()


def test_symmetric_self_and_relative_readings_do_not_duplicate_one_event():
    rows = (
        _activation(2, "Saturn"),
        _activation(8, "Saturn"),
        _activation(7, "Saturn"),
    )
    result = ChartManifestationResolver().resolve(
        _request(subjects=("self", "spouse")), rows
    )
    overlapping = [
        item for item in result
        if {role.native_house for role in item.house_roles}.issubset({2, 7, 8})
    ]
    assert len(overlapping) == 1
    assert overlapping[0].subject == "self"
    assert overlapping[0].rule_id == "semantic_event_signature_graph_cluster"


def test_h8_and_h11_form_a_grounded_shared_resource_result_cluster():
    rows = (_activation(8, "Saturn"), _activation(11, "Saturn"))

    result = ChartManifestationResolver().resolve(_request(), rows)

    cluster = next(
        item for item in result
        if item.rule_id == "semantic_event_signature_graph_cluster"
    )
    assert [role.native_house for role in cluster.house_roles] == [8, 11]
    assert {
        theme["key"] for theme in cluster.constituent_themes
    } == {"eighth_house_shared_resources"}
    assert cluster.constituent_themes[0]["required_varga"] == "D9"


def test_overlapping_signatures_synthesize_all_coherent_active_houses():
    rows = tuple(
        _activation(house, "Saturn")
        for house in (2, 4, 7, 8, 11)
    )

    result = ChartManifestationResolver().resolve(_request(), rows)

    cluster = next(
        item for item in result
        if item.rule_id == "semantic_event_signature_graph_cluster"
        and {role.native_house for role in item.house_roles} == {2, 4, 7, 8, 11}
    )
    theme_keys = {theme["key"] for theme in cluster.constituent_themes}
    assert {
        "property_asset",
        "relationship_commitment",
        "eighth_house_shared_resources",
        "financial_pressure_or_obligation",
    }.issubset(theme_keys)
    assert cluster.domain == "combined"
    assert len(cluster.house_roles) == 5


def test_active_houses_are_not_merged_without_a_registered_semantic_edge():
    rows = (_activation(1, "Saturn"), _activation(2, "Saturn"))

    result = ChartManifestationResolver().resolve(_request(), rows)

    assert not any(
        item.rule_id == "semantic_event_signature_graph_cluster"
        for item in result
    )
