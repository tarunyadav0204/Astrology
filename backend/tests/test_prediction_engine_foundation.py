from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from calculators.real_transit_calculator import RealTransitCalculator
from prediction_engine.contracts import BirthChartInput, PredictionRequest
from prediction_engine.errors import PredictionConfigurationError, PredictionInputError
from prediction_engine.providers.base import EvidenceProvider
from prediction_engine.registry import EvidenceProviderRegistry
from prediction_engine.service import PredictionService
from prediction_engine.subjects import native_houses_for_subject, rotate_relative_house
from shared.dasha_calculator import DashaCalculator


class _Provider(EvidenceProvider):
    provider_id = "test"
    version = "1.0.0"

    def evaluate(self, context):
        return []


class _DependentProvider(_Provider):
    provider_id = "dependent"
    required_providers = ("test",)
    supported_profiles = ("allowed",)


def _birth() -> BirthChartInput:
    return BirthChartInput.from_mapping(
        {
            "birth_chart_id": 1,
            "name": "Foundation Test",
            "date": "1990-01-15",
            "time": "10:30",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        }
    )


def test_birth_input_requires_real_location_and_timezone():
    with pytest.raises(PredictionInputError):
        BirthChartInput.from_mapping(
            {"date": "1990-01-15", "time": "10:30", "latitude": 28.6}
        )


def test_request_rejects_invalid_horizon():
    with pytest.raises(PredictionInputError):
        PredictionRequest(birth=_birth(), as_of=date(2026, 7, 21), horizon_days=0)


def test_relative_house_rotation_is_whole_sign_and_wraps():
    assert rotate_relative_house(7, 10) == 4  # spouse's career
    assert rotate_relative_house(9, 4) == 12  # father's home
    assert native_houses_for_subject("mother", (1, 10)) == [4, 1]


def test_prediction_engine_nodes_use_only_the_seventh_aspect():
    from prediction_engine.primitives import aspected_houses

    assert aspected_houses("Rahu", 2) == (8,)
    assert aspected_houses("Ketu", 8) == (2,)
    assert aspected_houses("Jupiter", 2) == (6, 8, 10)


def test_registry_rejects_duplicate_provider_ids():
    registry = EvidenceProviderRegistry((_Provider(),))
    with pytest.raises(PredictionConfigurationError):
        registry.register(_Provider())


def test_registry_enforces_dependencies_profiles_and_versions():
    registry = EvidenceProviderRegistry((_Provider(), _DependentProvider()))
    with pytest.raises(PredictionConfigurationError, match="missing providers"):
        registry.resolve(("dependent",), profile_key="allowed")
    with pytest.raises(PredictionConfigurationError, match="does not support"):
        registry.resolve(("test", "dependent"), profile_key="blocked")
    with pytest.raises(PredictionConfigurationError, match="version mismatch"):
        registry.resolve(
            ("test",),
            profile_key="allowed",
            expected_versions={"test": "9.9.9"},
        )


def test_strict_transit_api_rejects_unsupported_planet():
    with pytest.raises(ValueError):
        RealTransitCalculator().get_planet_state(datetime(2026, 7, 21), "Pluto")


def test_strict_dasha_does_not_return_fabricated_default_chain():
    invalid = {
        "date": "not-a-date",
        "time": "not-a-time",
        "latitude": 0,
        "longitude": 0,
        "timezone": "UTC",
    }
    with pytest.raises(RuntimeError, match="Vimshottari dasha calculation failed"):
        DashaCalculator().calculate_current_dashas(invalid, strict=True)


def test_real_service_generates_traceable_deterministic_result():
    request = PredictionRequest(
        birth=_birth(),
        as_of=date(2026, 7, 21),
        horizon_days=14,
        subjects=("self",),
        domains=("career", "wealth"),
        maximum_candidates=5,
        trace=True,
    )
    service = PredictionService()
    first = service.generate(request)
    second = service.generate(request)

    assert first.schema_version == "prediction_engine.v17"
    assert first.profile == "parashari_fomo_v1"
    assert first.evidence_signature == second.evidence_signature
    assert [row.manifestation_id for row in first.chart_manifestations] == [
        row.manifestation_id for row in second.chart_manifestations
    ]
    assert [c.candidate_id for c in first.candidates] == [
        c.candidate_id for c in second.candidates
    ]
    assert first.diagnostics["windows"] >= 1
    assert first.house_activations
    assert all({row.house for row in first.house_activations} == set(range(1, 13)) for _ in (0,))
    assert all(candidate.resolution is not None for candidate in first.candidates)
    assert all(
        candidate.resolution.rule_id
        == "house_first_activation_with_bounded_manifestations"
        for candidate in first.candidates
    )
    import json
    json.dumps(first.to_dict())
