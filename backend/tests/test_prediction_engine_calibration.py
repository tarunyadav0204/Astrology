from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from prediction_engine import PredictionRequest, PredictionService
from prediction_engine.contracts import (
    ActivationAssessment,
    ActivationBand,
    BirthChartInput,
    Evidence,
    EvidenceStatus,
    Importance,
    Polarity,
    ResolutionSpecificity,
    ResolutionStatus,
)
from prediction_engine.event_resolution import _eligibility
from prediction_engine.event_signatures import EVENT_SIGNATURES
from prediction_engine.contracts import LifeContext
from prediction_engine.engine import _activation_assessment, _outcome_assessment
from prediction_engine.profiles import get_profile
from prediction_engine.taxonomy import EVENT_FAMILIES
from prediction_engine.natal_promise import build_natal_promises
from calculators.planetary_dignities_calculator import PlanetaryDignitiesCalculator
from calculators.gandanta_calculator import GandantaCalculator


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "parashari_prediction_calibration.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text())


def test_gandanta_distance_uses_exact_sign_junction():
    result = GandantaCalculator({})._check_planet_gandanta("Mars", 122.38988431973502)
    assert result["distance_from_junction"] == 2.39
    assert result["intensity"] == "Medium"


@pytest.fixture(scope="module")
def calibration_results():
    service = PredictionService()
    as_of = date.fromisoformat(FIXTURE["as_of"])
    output = []
    for case in FIXTURE["cases"]:
        request = PredictionRequest(
            birth=BirthChartInput.from_mapping(case["birth"]),
            as_of=as_of,
            horizon_days=FIXTURE["horizon_days"],
            trace=True,
        )
        output.append((case, request, service.generate(request)))
    return output


def test_calibration_cases_produce_small_defensible_sets(calibration_results):
    for case, _request, result in calibration_results:
        limits = case["expected_candidate_count"]
        assert limits["min"] <= len(result.candidates) <= limits["max"], case["key"]
        assert result.diagnostics["merged_house_activation_rows"] >= 12, case["key"]


def test_final_candidates_are_diverse(calibration_results):
    for case, _request, result in calibration_results:
        families = [candidate.event_family for candidate in result.candidates]
        assert len(families) == len(set(families)), case["key"]
        houses = [candidate.native_houses for candidate in result.candidates]
        assert len(houses) == len(set(houses)), case["key"]


def test_every_candidate_has_real_natal_promise_and_carrier_transit(calibration_results):
    for case, _request, result in calibration_results:
        for candidate in result.candidates:
            assert candidate.resolution is not None
            assert candidate.resolution.status in {
                ResolutionStatus.RESOLVED,
                ResolutionStatus.AMBIGUOUS,
            }
            assert not candidate.resolution.missing_required_houses
            assert candidate.resolution.carrier_planets
            assert candidate.resolution.transit_reinforced
            assert {"AD", "PD"}.intersection(candidate.activation.active_dasha_levels)
            assert candidate.activation.primary_houses_covered == candidate.native_houses
            assert candidate.activation.carrier_planets
            assert candidate.activation.transit_reinforced
            carrier_set = set(candidate.activation.carrier_planets)
            event_transit = {
                row.planet
                for row in candidate.evidence
                if row.provider == "transit_house_ledger"
                and row.facts.get("timing_trigger")
            }
            assert event_transit, case["key"]
            if candidate.activation.band.value == "strong":
                natal_targets = {
                    row.facts.get("natal_planet")
                    for row in candidate.evidence
                    if row.provider == "transit_natal_ledger"
                }
                assert carrier_set.intersection(natal_targets)


def test_calibration_results_are_repeatable(calibration_results):
    service = PredictionService()
    for case, request, first in calibration_results:
        second = service.generate(request)
        assert first.evidence_signature == second.evidence_signature, case["key"]
        assert [c.candidate_id for c in first.candidates] == [
            c.candidate_id for c in second.candidates
        ]


def test_parashari_engine_never_labels_combustion_as_cazimi(calibration_results):
    for _case, _request, result in calibration_results:
        for candidate in result.candidates:
            for row in candidate.evidence:
                if row.rule_id in {"natal_combustion", "transit_combustion"}:
                    assert row.facts.get("combustion") != "cazimi"


def _evidence(
    *,
    provider: str,
    rule_id: str,
    planet: str,
    polarity: Polarity = Polarity.NEUTRAL,
    relation: str | None = None,
    level: str = "AD",
    house: int = 10,
) -> Evidence:
    facts = {"dasha_level": level}
    if relation:
        facts["relation"] = relation
    return Evidence(
        provider=provider,
        provider_version="1.0.0",
        rule_id=rule_id,
        status=EvidenceStatus.EVALUATED,
        subject="self",
        domain="career",
        window_start="2026-07-21",
        window_end="2026-08-01",
        planet=planet,
        house=house,
        importance=Importance.PRIMARY,
        polarity=polarity,
        facts=facts,
        independent_key=f"{provider}:{rule_id}:{planet}:{level}:{house}",
    )


def test_natal_aspect_is_a_real_dasha_house_connection():
    evidence = [
        _evidence(
            provider="dasha_house_activation",
            rule_id="dasha_natal_aspect_md",
            planet="Saturn",
            relation="natal_aspect",
            level="MD",
        ),
        _evidence(
            provider="dasha_house_activation",
            rule_id="dasha_natal_aspect",
            planet="Saturn",
            relation="natal_aspect",
        ),
        _evidence(
            provider="transit_house",
            rule_id="dasha_planet_transits_event_house",
            planet="Saturn",
        ),
        _evidence(
            provider="transit_natal_relation",
            rule_id="dasha_planet_transit_aspect_natal_self",
            planet="Saturn",
        ),
    ]
    assessment = _activation_assessment(
        evidence,
        get_profile("parashari_fomo_v1"),
        EVENT_FAMILIES["career_authority"],
    )
    assert assessment.band in {ActivationBand.MODERATE, ActivationBand.STRONG}


def test_non_carrier_planet_does_not_change_event_tone():
    activation = ActivationAssessment(
        band=ActivationBand.MODERATE,
        independent_confirmations=3,
        active_dasha_levels=("AD", "PD"),
        transit_reinforced=True,
        natal_position_reinforced=False,
        primary_houses_covered=(10,),
        carrier_planets=("Jupiter",),
        rule_id="test",
    )
    evidence = [
        _evidence(
            provider="functional_nature",
            rule_id="functional_nature",
            planet="Jupiter",
            polarity=Polarity.SUPPORTIVE,
        ),
        _evidence(
            provider="badhaka",
            rule_id="badhaka_lord_active",
            planet="Saturn",
            polarity=Polarity.CHALLENGING,
        ),
    ]
    outcome = _outcome_assessment(evidence, activation)
    assert outcome.tone == Polarity.SUPPORTIVE
    assert len(outcome.supportive_reasons) == outcome.supportive_factors == 1
    assert outcome.supportive_reasons[0]["planet"] == "Jupiter"
    assert outcome.challenging_reasons == ()
    assert outcome.mixed_reasons == ()


def test_house_outcome_exposes_every_counted_reason(calibration_results):
    for _fixture, _request, result in calibration_results:
        for house in result.house_activations:
            assert len(house.outcome.supportive_reasons) == house.outcome.supportive_factors
            assert len(house.outcome.challenging_reasons) == house.outcome.challenging_factors
            assert len(house.outcome.mixed_reasons) == house.outcome.mixed_factors
            for reason in (*house.outcome.supportive_reasons, *house.outcome.mixed_reasons, *house.outcome.challenging_reasons):
                assert reason["independent_key"]
                assert reason["rule_id"]
                assert reason["importance"] in {"primary", "secondary", "confirmatory"}


def test_explicit_life_context_can_reject_ineligible_manifestation():
    eligible, _label, reasons = _eligibility(
        EVENT_SIGNATURES["child_development"],
        LifeContext(has_children=False),
    )
    assert not eligible
    assert reasons == ("has_children_false",)


def test_unknown_life_context_is_not_invented_and_uses_broad_label():
    eligible, label, reasons = _eligibility(
        EVENT_SIGNATURES["business_expansion"], None
    )
    assert eligible
    assert label == "professional expansion decision"
    assert reasons == ("life_context_unknown",)


def test_d1_promise_records_neecha_bhanga_without_turning_it_into_unqualified_gain():
    planets = {
        "Sun": {"house": 1, "sign": 0, "longitude": 10.0, "degree": 10.0},
        "Moon": {"house": 4, "sign": 3, "longitude": 100.0, "degree": 10.0},
        "Mars": {"house": 1, "sign": 0, "longitude": 15.0, "degree": 15.0},
        "Mercury": {"house": 12, "sign": 11, "longitude": 350.0, "degree": 20.0},
        "Jupiter": {"house": 1, "sign": 0, "longitude": 20.0, "degree": 20.0},
        "Venus": {"house": 2, "sign": 1, "longitude": 40.0, "degree": 10.0},
        "Saturn": {"house": 11, "sign": 10, "longitude": 310.0, "degree": 10.0},
        "Rahu": {"house": 3, "sign": 2, "longitude": 70.0, "degree": 10.0},
        "Ketu": {"house": 9, "sign": 8, "longitude": 250.0, "degree": 10.0},
    }
    chart = {
        "ascendant": 0.0,
        "houses": [
            {"house_number": house, "sign": house - 1}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    dignities = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
    promises, yogas = build_natal_promises(chart, dignities)
    cancellation = next(
        yoga for yoga in yogas if yoga["key"] == "neecha_bhanga:Mercury"
    )
    assert "debilitation_sign_lord_in_kendra_from_lagna" in cancellation["rule"]
    mercury_lord_houses = [
        promise for promise in promises if promise["lord"] == "Mercury"
    ]
    assert mercury_lord_houses
    assert all(
        any(
            row["source"] == "house_lord_condition"
            and row["planet"] == "Mercury"
            and row["polarity"] == "neutral"
            and row["facts"]["neecha_bhanga"]
            for row in promise["factors"]
        )
        for promise in mercury_lord_houses
    )


def test_clean_dusthana_lord_in_dusthana_gets_bounded_strong_reversal():
    planets = {
        "Sun": {"house": 12, "sign": 4, "sign_name": "Leo", "longitude": 130.0, "degree": 10.0},
        "Moon": {"house": 1, "sign": 5, "sign_name": "Virgo", "longitude": 160.0, "degree": 10.0},
        "Mars": {"house": 2, "sign": 6, "sign_name": "Libra", "longitude": 190.0, "degree": 10.0},
        "Mercury": {"house": 3, "sign": 7, "sign_name": "Scorpio", "longitude": 220.0, "degree": 10.0},
        "Jupiter": {"house": 4, "sign": 8, "sign_name": "Sagittarius", "longitude": 250.0, "degree": 10.0},
        "Venus": {"house": 5, "sign": 9, "sign_name": "Capricorn", "longitude": 280.0, "degree": 10.0},
        "Saturn": {"house": 6, "sign": 10, "sign_name": "Aquarius", "longitude": 310.0, "degree": 10.0},
        "Rahu": {"house": 7, "sign": 11, "sign_name": "Pisces", "longitude": 340.0, "degree": 10.0},
        "Ketu": {"house": 1, "sign": 5, "sign_name": "Virgo", "longitude": 160.0, "degree": 10.0},
    }
    chart = {
        "ascendant": 150.0,
        "houses": [
            {"house_number": house, "sign": (5 + house - 1) % 12}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    dignities = PlanetaryDignitiesCalculator(chart).calculate_planetary_dignities()
    promises, _yogas = build_natal_promises(chart, dignities)
    twelfth = next(promise for promise in promises if promise["house"] == 12)
    reversal = next(
        factor for factor in twelfth["factors"]
        if factor["source"] == "dusthana_reversal_mitigation"
        and factor["planet"] == "Sun"
    )
    assert reversal["polarity"] == "supportive"
    assert reversal["weight"] == 0.75
    assert reversal["facts"]["classification"] == "strong"
    assert reversal["facts"]["yoga_types"] == ("Vimala-type",)
    assert reversal["facts"]["reversed_lordships"] == (12,)
    assert reversal["facts"]["afflictions"] == ()
    assert reversal["facts"]["other_lordships"] == ()
