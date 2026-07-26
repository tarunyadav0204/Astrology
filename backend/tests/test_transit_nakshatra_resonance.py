from __future__ import annotations

from prediction_engine.context import CalculationContext, EvaluationContext
from prediction_engine.contracts import (
    ActivationBand,
    BirthChartInput,
    Evidence,
    EvidenceStatus,
    Importance,
    Polarity,
    PredictionWindow,
)
from prediction_engine.engine import _activation_assessment
from prediction_engine.nakshatra_transit import nakshatra_transit_relation
from prediction_engine.profiles import get_profile
from prediction_engine.providers.transit_nakshatra import (
    TransitNakshatraResonanceProvider,
)
from prediction_engine.taxonomy import EVENT_FAMILIES


def _chart(saturn_longitude: float = 30.0):
    planets = {
        planet: {
            "house": 1,
            "sign": 0,
            "longitude": 1.0,
            "retrograde": False,
        }
        for planet in (
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        )
    }
    planets["Saturn"] = {
        "house": 2,
        "sign": int(saturn_longitude / 30.0),
        "longitude": saturn_longitude,
        "retrograde": False,
    }
    return {
        "ascendant": 0.0,
        "houses": [
            {"house_number": house, "sign": house - 1}
            for house in range(1, 13)
        ],
        "planets": planets,
    }


def _evaluation_context(transit_longitude: float) -> EvaluationContext:
    window = PredictionWindow(
        "2026-07-01", "2026-07-15", "Saturn", "Saturn", "Saturn", "sig"
    )
    calculation = CalculationContext(
        birth=BirthChartInput.from_mapping({
            "date": "1980-04-02",
            "time": "14:55",
            "latitude": 29.1492,
            "longitude": 75.7217,
            "timezone": "Asia/Kolkata",
        }),
        chart=_chart(),
        natal_dignities={
            "Sun": {"dignity": "own_sign", "combustion_status": "normal"}
        },
        yogi_points={},
        gandanta={},
        badhaka_lord="Saturn",
        windows=(window,),
        transit_states_by_signature={
            "sig": {
                "Saturn": {
                    "longitude": transit_longitude,
                    "sign": int(transit_longitude / 30.0),
                    "house": int(transit_longitude / 30.0) + 1,
                }
            }
        },
        divisional_charts={},
    )
    family = EVENT_FAMILIES["career_authority"]
    return EvaluationContext(
        calculation=calculation,
        window=window,
        subject="self",
        event_family=family,
        primary_houses=family.primary_relative_houses,
        supporting_houses=family.supporting_relative_houses,
        conflicting_houses=family.conflicting_relative_houses,
    )


def _activation_evidence(
    provider: str,
    rule_id: str,
    *,
    level: str = "AD",
    relation: str = "lordship",
) -> Evidence:
    return Evidence(
        provider=provider,
        provider_version="1.0.0",
        rule_id=rule_id,
        status=EvidenceStatus.EVALUATED,
        subject="self",
        domain="career",
        window_start="2026-07-01",
        window_end="2026-07-15",
        planet="Saturn",
        house=10,
        importance=Importance.PRIMARY,
        polarity=Polarity.NEUTRAL,
        facts={"dasha_level": level, "relation": relation},
        independent_key=f"{provider}:{rule_id}:{level}",
    )


def test_different_nakshatras_with_same_lord_are_secondary_resonance():
    # Natal Saturn in Krittika and transit Saturn in Uttara Phalguni:
    # different nakshatras, both ruled by the Sun.
    relation = nakshatra_transit_relation(30.0, 150.0)

    assert relation is not None
    assert relation["relation"] == "nakshatra_dispositor_resonance"
    assert relation["strength"] == "secondary_confirmation"
    assert relation["natal_nakshatra"]["name"] == "Krittika"
    assert relation["transit_nakshatra"]["name"] == "Uttara Phalguni"
    assert relation["common_nakshatra_lord"] == "Sun"


def test_provider_records_lord_relevance_and_condition_without_direct_contact():
    rows = TransitNakshatraResonanceProvider().evaluate(
        _evaluation_context(150.0)
    )
    row = next(item for item in rows if item.house == 10)

    assert row.rule_id == "dasha_planet_nakshatra_dispositor_resonance"
    assert row.facts["qualifies_as_direct_natal_contact"] is False
    assert row.facts["qualifies_as_strong_natal_return_confirmation"] is False
    assert row.facts["creates_house_promise"] is False
    assert row.facts["common_nakshatra_lord"] == "Sun"
    assert row.facts["nakshatra_lord_natal_condition"]["dignity"] == "own_sign"
    assert row.facts["nakshatra_lord_expression"] == "clear"


def test_exact_natal_nakshatra_return_is_classified_separately():
    rows = TransitNakshatraResonanceProvider().evaluate(
        _evaluation_context(31.0)
    )

    assert rows
    assert {
        row.rule_id for row in rows
    } == {"dasha_planet_exact_natal_nakshatra_return"}
    assert all(row.facts["qualifies_as_direct_natal_contact"] is False for row in rows)
    assert all(
        row.facts["qualifies_as_strong_natal_return_confirmation"] is True
        for row in rows
    )


def test_unrelated_nakshatra_lord_produces_no_resonance():
    assert nakshatra_transit_relation(30.0, 100.0) is None
    assert TransitNakshatraResonanceProvider().evaluate(
        _evaluation_context(100.0)
    ) == []


def test_same_lord_resonance_cannot_make_activation_strong():
    evidence = [
        _activation_evidence(
            "dasha_house_activation", "dasha_planet_lordship_house", level="MD"
        ),
        _activation_evidence(
            "dasha_house_activation", "dasha_planet_lordship_house", level="AD"
        ),
        _activation_evidence(
            "transit_house", "dasha_planet_transits_event_house", relation="occupation"
        ),
        _activation_evidence(
            "transit_nakshatra_resonance",
            "dasha_planet_nakshatra_dispositor_resonance",
        ),
    ]

    assessment = _activation_assessment(
        evidence,
        get_profile("parashari_fomo_v1"),
        EVENT_FAMILIES["career_authority"],
    )

    assert assessment.band != ActivationBand.STRONG
    assert assessment.natal_position_reinforced is False


def test_exact_nakshatra_return_can_reinforce_an_already_delivered_transit():
    evidence = [
        _activation_evidence(
            "dasha_house_activation", "dasha_planet_lordship_house", level="MD"
        ),
        _activation_evidence(
            "dasha_house_activation", "dasha_planet_lordship_house", level="AD"
        ),
        _activation_evidence(
            "transit_house", "dasha_planet_transits_event_house", relation="occupation"
        ),
        _activation_evidence(
            "transit_nakshatra_resonance",
            "dasha_planet_exact_natal_nakshatra_return",
        ),
    ]

    assessment = _activation_assessment(
        evidence,
        get_profile("parashari_fomo_v1"),
        EVENT_FAMILIES["career_authority"],
    )

    assert assessment.band == ActivationBand.STRONG
    assert assessment.natal_position_reinforced is True
