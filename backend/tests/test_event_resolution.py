from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from prediction_engine.context import CalculationContext
from prediction_engine.contracts import (
    ActivationAssessment,
    ActivationBand,
    BirthChartInput,
    Evidence,
    EvidenceStatus,
    Importance,
    OutcomeAssessment,
    Polarity,
    PredictionCandidate,
    PredictionRequest,
    PredictionWindow,
    ResolutionSpecificity,
    ResolutionStatus,
    HouseActivationState,
)
from prediction_engine.event_resolution import EventResolutionEngine
from prediction_engine.house_significations import build_house_interpretations
from prediction_engine.service import PredictionService


def _evidence(provider, planet, house, level="AD", relation="occupation"):
    return Evidence(
        provider=provider,
        provider_version="1.0.0",
        rule_id=f"test_{provider}",
        status=EvidenceStatus.EVALUATED,
        subject="self",
        domain="career",
        window_start="2026-07-21",
        window_end="2026-07-31",
        planet=planet,
        house=house,
        importance=Importance.PRIMARY,
        polarity=Polarity.NEUTRAL,
        facts={"dasha_level": level, "relation": relation},
        independent_key=f"{provider}:{planet}:{house}:{level}:{relation}",
    )


def _chart(planet="Mercury", house=10):
    planets = {
        name: {"house": 1, "sign": 0, "longitude": 0.0}
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
    }
    planets[planet] = {"house": house, "sign": house - 1, "longitude": (house - 1) * 30.0}
    return {
        "ascendant": 0.0,
        "houses": [{"house_number": number, "sign": number - 1} for number in range(1, 13)],
        "planets": planets,
    }


def _context(vargas=None):
    birth = BirthChartInput.from_mapping({
        "date": "1990-01-15", "time": "10:30", "latitude": 28.6,
        "longitude": 77.2, "timezone": "Asia/Kolkata",
    })
    return CalculationContext(
        birth=birth,
        chart=_chart(),
        natal_dignities={},
        yogi_points={},
        gandanta={},
        badhaka_lord="Saturn",
        windows=(),
        transit_states_by_signature={},
        divisional_charts=vargas if vargas is not None else {"D10": _chart()},
    )


def _candidate(evidence):
    return PredictionCandidate(
        candidate_id="test",
        subject="self",
        domain="career",
        event_family="career_authority",
        native_houses=(10, 2, 6, 7, 11),
        window=PredictionWindow(
            "2026-07-21", "2026-07-31", "Mercury", "Mercury", "Mercury", "test"
        ),
        activation=ActivationAssessment(
            ActivationBand.MODERATE, 3, ("MD", "AD"), True, False, (10,),
            ("Mercury",), "test",
        ),
        outcome=OutcomeAssessment(Polarity.NEUTRAL, 0, 0, "test"),
        evidence=tuple(evidence),
    )


def _complete_d1(planet="Mercury"):
    return [
        _evidence("dasha_house_activation", planet, 10, "MD"),
        _evidence("dasha_house_activation", planet, 10, "AD"),
        _evidence("dasha_house_activation", planet, 2, "AD"),
    ]


def test_divisional_chart_cannot_create_an_event_without_d1_promise():
    candidate = _candidate([_evidence("transit_house", "Mercury", 10)])
    resolution = EventResolutionEngine().resolve(candidate, _context(), None)
    assert resolution.status == ResolutionStatus.UNCONFIRMED
    assert resolution.missing_required_houses == (10,)


def test_d1_and_transit_must_use_the_same_active_carrier():
    evidence = _complete_d1("Mercury")
    evidence.append(_evidence("transit_house", "Saturn", 10))
    resolution = EventResolutionEngine().resolve(candidate=_candidate(evidence), calculation=_context(), life_context=None)
    assert resolution.status == ResolutionStatus.UNCONFIRMED
    assert not resolution.transit_reinforced


def test_missing_relevant_varga_cannot_be_treated_as_confirmation():
    evidence = _complete_d1("Mercury")
    evidence.append(_evidence("transit_house", "Mercury", 10))
    resolution = EventResolutionEngine().resolve(_candidate(evidence), _context(vargas={}), None)
    assert resolution.status in {ResolutionStatus.RESOLVED, ResolutionStatus.AMBIGUOUS}
    assert resolution.specificity == ResolutionSpecificity.CORE
    assert not resolution.divisional_confirmations[0].confirmed


def test_equal_complete_signatures_remain_ambiguous_instead_of_arbitrary():
    evidence = _complete_d1("Mercury")
    evidence.append(_evidence("transit_house", "Mercury", 10))
    resolution = EventResolutionEngine().resolve(_candidate(evidence), _context(), None)
    assert resolution.status == ResolutionStatus.AMBIGUOUS
    assert resolution.specificity == ResolutionSpecificity.CORROBORATED
    assert resolution.signature_key is None
    assert resolution.label == "career authority"
    assert resolution.alternative_signature_keys == (
        "promotion_authority",
        "business_expansion",
    )


def test_same_native_house_across_subject_frames_is_returned_as_alternatives():
    birth = BirthChartInput.from_mapping({
        "birth_chart_id": 10281,
        "name": "Derived House Regression",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.2396596,
        "longitude": 75.8174505,
        "timezone": "Asia/Kolkata",
    })
    result = PredictionService().generate(PredictionRequest(
        birth=birth,
        as_of=date(2026, 7, 21),
        horizon_days=90,
        trace=True,
    ))
    current = {
        row.house: row
        for row in result.house_activations
        if row.window.start_date == "2026-07-21"
    }
    assert current[2].state == HouseActivationState.FULLY_REINFORCED
    assert current[8].state == HouseActivationState.FULLY_REINFORCED
    assert current[6].state == HouseActivationState.TRANSIT_ONLY
    assert current[6].activation.band == ActivationBand.INSUFFICIENT
    assert current[6].activation.active_dasha_levels == ()
    assert current[6].activation.carrier_planets == ()
    assert not current[6].activation.natal_position_reinforced
    house_two = current[2]
    mars = next(reason for reason in house_two.outcome.mixed_reasons if reason["planet"] == "Mars")
    mars_functional = next(
        component for component in mars["components"]
        if component["rule_id"] == "occupant_functional_lordship"
    )
    assert mars_functional["facts"]["yogakaraka"] is True
    assert mars_functional["facts"]["ruled_houses"] == (5, 10)
    jupiter = next(reason for reason in house_two.outcome.mixed_reasons if reason["planet"] == "Jupiter")
    jupiter_functional = next(
        component for component in jupiter["components"]
        if component["rule_id"] == "occupant_functional_lordship"
    )
    assert jupiter_functional["polarity"] == "mixed"
    assert jupiter_functional["facts"]["supportive_houses"] == (9,)
    assert jupiter_functional["facts"]["challenging_houses"] == (6,)
    mars_rules = {component["rule_id"] for component in mars["components"]}
    assert {"planet_gandanta", "combined_special_status"}.issubset(mars_rules)
    assert "fivefold_friendship_with_nakshatra_lord" not in mars_rules
    special = next(component for component in mars["components"] if component["rule_id"] == "combined_special_status")
    special_rules = {status["rule_id"] for status in special["facts"]["statuses"]}
    assert {"avayogi_lord", "dagdha_rashi_lord", "tithi_shunya_lord"}.issubset(special_rules)
    gandanta_reason = next(
        component for component in mars["components"]
        if component["rule_id"] == "planet_gandanta"
    )
    assert gandanta_reason["facts"]["gandanta_name"] == "Ashlesha-Magha Gandanta"
    assert gandanta_reason["facts"]["distance_from_junction"] == 2.39
    assert gandanta_reason["facts"]["intensity"] == "Medium"
    assert house_two.outcome.supportive_factors == 0
    assert house_two.outcome.mixed_factors == 3
    assert house_two.outcome.challenging_factors == 3
    mercury = next(reason for reason in house_two.outcome.mixed_reasons if reason["planet"] == "Mercury")
    mercury_natural = next(
        component for component in mercury["components"]
        if component["rule_id"] == "aspector_natural_influence"
    )
    assert mercury_natural["facts"]["malefic_associations"] == ("Ketu",)
    mercury_rules = {component["rule_id"] for component in mercury["components"]}
    assert "fivefold_friendship_with_house_lord" not in mercury_rules
    mercury_host = next(
        component for component in mercury["components"]
        if component["rule_id"] == "placement_dispositor_relationship"
    )
    assert mercury_host["polarity"] == "challenging"
    assert mercury_host["facts"]["placement_sign_name"] == "Aquarius"
    assert mercury_host["facts"]["dispositor"] == "Saturn"
    assert mercury_host["facts"]["natural_relation"] == "neutral"
    assert mercury_host["facts"]["compound_relation"] == "enemy"
    mercury_functional = next(
        component for component in mercury["components"]
        if component["rule_id"] == "aspector_functional_lordship"
    )
    assert mercury_functional["facts"]["challenging_houses"] == (3, 12)
    assert mercury_functional["facts"]["reversal_houses"] == (12,)
    assert mercury_functional["facts"]["effective_challenging_houses"] == (3,)
    assert mercury_functional["facts"]["directional_weight_multiplier"] == 0.5
    mercury_reversal = next(
        component for component in mercury["components"]
        if component["rule_id"] == "dusthana_reversal_mitigation"
    )
    assert mercury_reversal["polarity"] == "supportive"
    assert mercury_reversal["facts"]["classification"] == "afflicted"
    assert mercury_reversal["facts"]["yoga_types"] == ("Vimala-type",)
    assert mercury_reversal["facts"]["reversed_lordships"] == (12,)
    assert mercury_reversal["facts"]["placement_house"] == 8
    assert set(mercury_reversal["facts"]["afflictions"]) == {
        "node_conjunction", "hostile_dispositor_relationship",
    }
    assert mercury_reversal["facts"]["other_lordships"] == (3,)
    assert mercury_reversal["facts"]["mitigation_weight"] == 0.25
    for node in ("Rahu", "Ketu"):
        node_reason = next(
            reason for reason in house_two.outcome.challenging_reasons
            if reason["planet"] == node
        )
        node_rules = {component["rule_id"] for component in node_reason["components"]}
        assert "fivefold_friendship_with_house_lord" not in node_rules
        assert "fivefold_friendship_with_nakshatra_lord" not in node_rules
        assert "node_dispositor_and_associations" not in node_rules
        assert "node_conditioned_influence" in node_rules
    ketu_reason = next(
        reason for reason in house_two.outcome.challenging_reasons
        if reason["planet"] == "Ketu"
    )
    ketu_condition = next(
        component for component in ketu_reason["components"]
        if component["rule_id"] == "node_conditioned_influence"
    )
    assert ketu_condition["facts"]["resolved_polarity"] == "challenging"
    assert [row["planet"] for row in ketu_condition["facts"]["influencers"]] == [
        "Saturn", "Mercury",
    ]
    rahu_reason = next(
        reason for reason in house_two.outcome.challenging_reasons
        if reason["planet"] == "Rahu"
    )
    rahu_condition = next(
        component for component in rahu_reason["components"]
        if component["rule_id"] == "node_conditioned_influence"
    )
    assert rahu_condition["facts"]["resolved_polarity"] == "challenging"
    assert rahu_condition["facts"]["supportive_score"] > 0
    assert rahu_condition["facts"]["challenging_score"] > rahu_condition["facts"]["supportive_score"]
    assert {
        row["planet"]: row["polarity"]
        for row in rahu_condition["facts"]["influencers"]
    } == {
        "Sun": "challenging",
        "Jupiter": "supportive",
        "Mars": "mixed",
        "Saturn": "challenging",
    }
    assert current[6].activation.rule_id == "transit_activation_without_current_dasha_natal_connection"
    assert set(current[8].activation.carrier_planets) == {"Rahu", "Saturn"}
    assert current[9].state == HouseActivationState.TRANSIT_ONLY
    assert current[9].activation.band == ActivationBand.INSUFFICIENT
    assert current[1].state == HouseActivationState.TRANSIT_ONLY
    assert "Sun" not in current[1].activation.carrier_planets
    assert "Moon" not in current[8].trigger_planets
    assert any(
        trigger["kind"] == "moon_peak"
        and not trigger["creates_event"]
        for trigger in current[8].timing_triggers
    )
    assert not any(
        trigger["kind"] == "sun_reinforcement"
        for trigger in current[8].timing_triggers
    )
    assert len(result.natal_promises) == 12
    eighth_promise = next(row for row in result.natal_promises if row["house"] == 8)
    assert eighth_promise["lord"] == "Saturn"
    assert set(eighth_promise["occupants"]) == {"Ketu", "Mercury"}
    assert "Saturn" in eighth_promise["karakas"]
    assert all(
        planet in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        for planet in (*eighth_promise["occupants"], *eighth_promise["aspecting_planets"])
    )
    clusters = [
        candidate.resolution
        for candidate in result.candidates
        if candidate.resolution
        and candidate.native_houses == (2,)
    ]
    assert clusters
    alternatives = {
        (row.subject, row.signature_key)
        for row in clusters[0].interpretation_alternatives
    }
    assert alternatives == {
        ("self", "house_2"),
        ("mother", "house_11"),
        ("spouse", "house_8"),
    }
    mother = next(
        row for row in clusters[0].interpretation_alternatives
        if row.subject == "mother"
    )
    assert mother.relative_houses == (11,)
    assert "gains" in mother.label
    assert any("objective" in text for text in mother.manifestations)
    assert mother.tone == clusters[0].interpretation_alternatives[0].tone
    assert "improvement in income" not in " ".join(mother.manifestations)


def test_future_sun_contact_surfaces_father_only_in_its_timing_window():
    birth = BirthChartInput.from_mapping({
        "birth_chart_id": 10281,
        "name": "Derived House Timing Regression",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.2396596,
        "longitude": 75.8174505,
        "timezone": "Asia/Kolkata",
    })
    result = PredictionService().generate(PredictionRequest(
        birth=birth,
        as_of=date(2026, 7, 22),
        horizon_days=120,
        maximum_candidates=100,
        trace=True,
        exploration_mode=True,
    ))
    current_h2 = next(
        row for row in result.house_activations
        if row.house == 2 and row.window.start_date <= "2026-07-22" <= row.window.end_date
    )
    sun_h2 = next(
        row for row in result.house_activations
        if row.house == 2 and row.window.start_date == "2026-08-17"
    )
    assert sun_h2.window.end_date == "2026-09-16"
    assert not any(
        evidence.planet == "Sun" and evidence.provider == "transit_natal_ledger"
        for evidence in current_h2.evidence
    )
    assert any(
        evidence.planet == "Sun"
        and evidence.provider == "transit_natal_ledger"
        and evidence.facts.get("natal_planet") == "Saturn"
        for evidence in sun_h2.evidence
    )
    current_subjects = {
        alternative.subject
        for candidate in result.candidates
        if candidate.native_houses == (2,)
        and candidate.window.start_date == current_h2.window.start_date
        for alternative in candidate.resolution.interpretation_alternatives
    }
    sun_subjects = {
        alternative.subject
        for candidate in result.candidates
        if candidate.native_houses == (2,)
        and candidate.window.start_date == sun_h2.window.start_date
        for alternative in candidate.resolution.interpretation_alternatives
    }
    assert "father" not in current_subjects
    assert "father" in sun_subjects


def test_house_combination_appears_only_when_every_required_house_is_active():
    outcome = OutcomeAssessment(Polarity.MIXED, 2, 3, "test_mixed")
    single = build_house_interpretations((2,), ("self",), ("Rahu",), outcome)[0]
    combined = build_house_interpretations(
        (2, 11), ("self",), ("Rahu",), outcome
    )[0]
    assert "income_accumulation" not in single.signature_key
    assert "income_accumulation" in combined.signature_key
    assert "income and resource accumulation" in combined.label


def test_second_house_includes_savings_and_anatomical_significations():
    outcome = OutcomeAssessment(Polarity.NEUTRAL, 0, 0, "test_neutral")
    alternative = build_house_interpretations(
        (2,), ("self",), ("Saturn",), outcome
    )[0]
    assert "savings" in alternative.label
    assert "income" not in alternative.label
    assert any("face, mouth, teeth" in item for item in alternative.manifestations)


def test_spouse_shared_finances_is_focused_on_native_second_house():
    outcome = OutcomeAssessment(Polarity.CHALLENGING, 0, 4, "test_challenging")
    alternatives = build_house_interpretations(
        (2, 8), ("self", "spouse"), ("Rahu", "Saturn"), outcome
    )
    native = next(row for row in alternatives if row.subject == "self")
    spouse = next(row for row in alternatives if row.subject == "spouse")

    assert native.signature_key == "shared_finances"
    assert native.focus_relative_houses == (8,)
    assert native.focus_native_houses == (8,)
    assert spouse.signature_key == "shared_finances"
    assert spouse.focus_relative_houses == (8,)
    assert spouse.focus_native_houses == (2,)


def test_challenging_tone_is_preserved_when_native_house_is_rotated():
    outcome = OutcomeAssessment(
        Polarity.CHALLENGING, 0, 4, "challenging_carrier_conditions"
    )
    alternatives = build_house_interpretations(
        (2,), ("self", "mother", "father", "spouse"), ("Rahu",), outcome
    )
    assert {row.tone for row in alternatives} == {Polarity.CHALLENGING}
    mother = next(row for row in alternatives if row.subject == "mother")
    assert mother.relative_houses == (11,)
    assert "obstruction or strain" in mother.tone_interpretation
    assert mother.supportive_factors == 0
    assert mother.challenging_factors == 4
