from __future__ import annotations

from prediction_engine.context import CalculationContext
from prediction_engine.contracts import (
    ActivationAssessment,
    ActivationBand,
    BirthChartInput,
    HouseActivation,
    HouseActivationState,
    OutcomeAssessment,
    Polarity,
    PredictionWindow,
)
from prediction_engine.event_windows import EventWindowEngine


def _window() -> PredictionWindow:
    return PredictionWindow(
        "2027-04-01", "2027-04-20", "Saturn", "Mercury", "Rahu", "sig",
        opened_by=({"kind": "dasha", "level": "PD", "label": "PD Rahu begins"},),
    )


def _activation(house: int, state: HouseActivationState) -> HouseActivation:
    reinforced = state in {
        HouseActivationState.DASHA_TRANSIT_ACTIVATED,
        HouseActivationState.FULLY_REINFORCED,
    }
    return HouseActivation(
        house=house,
        window=_window(),
        state=state,
        activation=ActivationAssessment(
            band=ActivationBand.STRONG if reinforced else ActivationBand.MODERATE,
            independent_confirmations=2 if reinforced else 1,
            active_dasha_levels=("MD", "AD", "PD"),
            transit_reinforced=reinforced,
            natal_position_reinforced=False,
            primary_houses_covered=(house,),
            carrier_planets=("Saturn",),
            rule_id="test",
        ),
        outcome=OutcomeAssessment(
            tone=Polarity.NEUTRAL,
            supportive_factors=0,
            challenging_factors=0,
            rule_id="test",
        ),
        house_lord="Saturn",
        natal_connections=({"level": "MD", "planet": "Saturn", "relation": "lordship"},),
        transit_connections=({
            "planet": "Saturn", "relation": "aspect", "transit_house": 4,
            "timing_trigger": reinforced,
        },),
        dasha_relationships=(),
        trigger_planets=("Saturn",) if reinforced else (),
        timing_triggers=(),
        evidence=(),
    )


def _context() -> CalculationContext:
    return CalculationContext(
        birth=BirthChartInput.from_mapping({
            "date": "1990-01-15", "time": "10:30",
            "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata",
        }),
        chart={"ascendant": 0.0, "houses": [], "planets": {}},
        natal_dignities={}, yogi_points={}, gandanta={}, badhaka_lord="Saturn",
        windows=(_window(),),
        transit_states_by_signature={
            "sig": {
                "Jupiter": {"house": 1},
                "Saturn": {"house": 2},
            },
        },
        divisional_charts={},
        natal_promises=(),
    )


def _disable_varga(monkeypatch):
    monkeypatch.setattr(
        "prediction_engine.event_windows._build_varga", lambda calculation, varga: {}
    )
    monkeypatch.setattr(
        "prediction_engine.event_windows._varga_confirmation",
        lambda chart, window, definition: {
            "passed": False, "chart": definition.varga, "matches": [],
            "explanation": f"No {definition.varga} link",
        },
    )


def test_job_change_does_not_require_a_static_natal_promise(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="job_change",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_CONNECTED),
            _activation(3, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(2, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert result["qualified_windows"] == 1
    window = result["windows"][0]
    assert window["strength"] == "strong"
    assert window["classification"] == "job_change_with_gain_support"
    assert all(step["key"] != "natal_promise" for step in window["calculation_trace"])


def test_job_change_rejects_generic_career_activation_without_transition(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="job_change",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(2, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert result["qualified_windows"] == 0
    assert result["rejected_summary"]["missing_transition"] == 1


def test_income_houses_classify_outcome_but_do_not_gate_change(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="job_change",
        calculation=_context(),
        activations=(
            _activation(6, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )

    assert result["qualified_windows"] == 1
    assert result["windows"][0]["classification"] == "exit_or_interruption"
    outcome = next(
        step for step in result["windows"][0]["calculation_trace"]
        if step["key"] == "outcome"
    )
    assert outcome["required"] is False
    assert outcome["passed"] is False


def test_health_focus_uses_health_pressure_and_recovery_groups(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="health",
        calculation=_context(),
        activations=(
            _activation(1, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(5, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert result["qualified_windows"] == 1
    window = result["windows"][0]
    assert window["classification"] == "health_attention_with_recovery_support"
    assert result["varga"] == "D30"
    assert "does not diagnose" in result["event_description"]


def test_health_focus_does_not_require_recovery_support(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="health",
        calculation=_context(),
        activations=(
            _activation(6, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )

    assert result["qualified_windows"] == 1
    assert result["windows"][0]["classification"] == "rest_or_treatment_window"
