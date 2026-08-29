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
from prediction_engine.errors import PredictionConfigurationError
from prediction_engine.event_windows import EventWindowEngine


def _window(*, opened_by=({"kind": "dasha", "level": "PD", "label": "PD Rahu begins"},)) -> PredictionWindow:
    return PredictionWindow(
        "2027-04-01", "2027-04-20", "Saturn", "Mercury", "Rahu", "sig",
        opened_by=opened_by,
    )


def _activation(
    house: int,
    state: HouseActivationState,
    window: PredictionWindow | None = None,
) -> HouseActivation:
    timing = window or _window()
    reinforced = state in {
        HouseActivationState.DASHA_TRANSIT_ACTIVATED,
        HouseActivationState.FULLY_REINFORCED,
    }
    return HouseActivation(
        house=house,
        window=timing,
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


def _context(window: PredictionWindow | None = None) -> CalculationContext:
    timing = window or _window()
    return CalculationContext(
        birth=BirthChartInput.from_mapping({
            "date": "1990-01-15", "time": "10:30",
            "latitude": 28.6139, "longitude": 77.2090, "timezone": "Asia/Kolkata",
        }),
        chart={"ascendant": 0.0, "houses": [], "planets": {}},
        natal_dignities={}, yogi_points={}, gandanta={}, badhaka_lord="Saturn",
        windows=(timing,),
        transit_states_by_signature={
            timing.transit_signature: {
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


def test_property_purchase_requires_payment_or_financing(monkeypatch):
    _disable_varga(monkeypatch)
    rejected = EventWindowEngine().resolve(
        event_key="property_purchase",
        calculation=_context(),
        activations=(_activation(4, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )
    qualified = EventWindowEngine().resolve(
        event_key="property_purchase",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(8, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    with_gain = EventWindowEngine().resolve(
        event_key="property_purchase",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(2, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(11, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert rejected["qualified_windows"] == 0
    assert rejected["rejected_summary"]["missing_transition"] == 1
    assert qualified["windows"][0]["classification"] == "loan_or_shared_purchase"
    assert qualified["varga"] == "D4"
    assert with_gain["windows"][0]["classification"] == "property_purchase_with_gain"


def test_relocation_requires_a_move_or_leaving_signal(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="relocation",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    settled = EventWindowEngine().resolve(
        event_key="relocation",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(3, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(11, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert result["qualified_windows"] == 1
    assert result["windows"][0]["classification"] == "away_from_home"
    assert settled["windows"][0]["classification"] == "relocation_with_settlement"


def test_property_gain_requires_fourth_and_eleventh(monkeypatch):
    _disable_varga(monkeypatch)
    rejected = EventWindowEngine().resolve(
        event_key="property_gain",
        calculation=_context(),
        activations=(_activation(4, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )
    result = EventWindowEngine().resolve(
        event_key="property_gain",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(2, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert rejected["qualified_windows"] == 0
    assert rejected["rejected_summary"]["missing_transition"] == 1
    assert result["qualified_windows"] == 1
    assert result["windows"][0]["classification"] == "property_gain_with_resources"
    assert result["varga"] == "D4"


def test_promotion_requires_status_or_recognition_not_a_job_exit(monkeypatch):
    _disable_varga(monkeypatch)
    career_only = EventWindowEngine().resolve(
        event_key="promotion",
        calculation=_context(),
        activations=(_activation(10, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )
    job_exit_shape = EventWindowEngine().resolve(
        event_key="promotion",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    status = EventWindowEngine().resolve(
        event_key="promotion",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    with_pay = EventWindowEngine().resolve(
        event_key="promotion",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(2, HouseActivationState.DASHA_CONNECTED),
        ),
    )
    recognition = EventWindowEngine().resolve(
        event_key="promotion",
        calculation=_context(),
        activations=(
            _activation(10, HouseActivationState.DASHA_CONNECTED),
            _activation(5, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )

    assert career_only["qualified_windows"] == 0
    assert career_only["rejected_summary"]["missing_transition"] == 1
    assert job_exit_shape["qualified_windows"] == 0
    assert status["windows"][0]["classification"] == "career_status_rise"
    assert status["varga"] == "D10"
    assert with_pay["windows"][0]["classification"] == "promotion_with_salary_support"
    assert recognition["windows"][0]["classification"] == "recognition_or_authority"


def test_marriage_requires_seventh_plus_a_joining_signal(monkeypatch):
    _disable_varga(monkeypatch)
    rejected = EventWindowEngine().resolve(
        event_key="marriage",
        calculation=_context(),
        activations=(_activation(7, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )
    result = EventWindowEngine().resolve(
        event_key="marriage",
        calculation=_context(),
        activations=(
            _activation(7, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    romance = EventWindowEngine().resolve(
        event_key="marriage",
        calculation=_context(),
        activations=(
            _activation(7, HouseActivationState.DASHA_CONNECTED),
            _activation(5, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )

    assert rejected["qualified_windows"] == 0
    assert rejected["rejected_summary"]["missing_transition"] == 1
    assert result["windows"][0]["classification"] == "partnership_with_fulfilment"
    assert result["varga"] == "D9"
    assert "not a guaranteed" in result["event_description"]
    assert romance["windows"][0]["classification"] == "romance_or_meeting"


def test_foreign_travel_is_not_a_home_relocation(monkeypatch):
    _disable_varga(monkeypatch)
    home_only = EventWindowEngine().resolve(
        event_key="foreign_travel",
        calculation=_context(),
        activations=(
            _activation(4, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    result = EventWindowEngine().resolve(
        event_key="foreign_travel",
        calculation=_context(),
        activations=(
            _activation(9, HouseActivationState.DASHA_CONNECTED),
            _activation(12, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )

    assert home_only["qualified_windows"] == 0
    assert result["qualified_windows"] == 1
    assert result["windows"][0]["classification"] == "foreign_stay"
    assert result["varga"] == "D9"


def test_children_and_education_share_the_fifth_but_need_different_paths(monkeypatch):
    _disable_varga(monkeypatch)
    children = EventWindowEngine().resolve(
        event_key="children",
        calculation=_context(),
        activations=(
            _activation(5, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    education = EventWindowEngine().resolve(
        event_key="education",
        calculation=_context(),
        activations=(
            _activation(5, HouseActivationState.DASHA_CONNECTED),
            _activation(9, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
        ),
    )
    fifth_only = EventWindowEngine().resolve(
        event_key="children",
        calculation=_context(),
        activations=(_activation(5, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )

    assert children["windows"][0]["classification"] == "child_development_with_fulfilment"
    assert children["varga"] == "D7"
    assert "does not predict a birth" in children["event_description"]
    assert education["windows"][0]["classification"] == "higher_learning"
    assert education["varga"] == "D24"
    assert fifth_only["qualified_windows"] == 0


def test_income_gain_requires_second_and_eleventh(monkeypatch):
    _disable_varga(monkeypatch)
    rejected = EventWindowEngine().resolve(
        event_key="income_gain",
        calculation=_context(),
        activations=(_activation(2, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
    )
    result = EventWindowEngine().resolve(
        event_key="income_gain",
        calculation=_context(),
        activations=(
            _activation(2, HouseActivationState.DASHA_CONNECTED),
            _activation(11, HouseActivationState.DASHA_TRANSIT_ACTIVATED),
            _activation(9, HouseActivationState.DASHA_CONNECTED),
        ),
    )

    assert rejected["qualified_windows"] == 0
    assert rejected["rejected_summary"]["missing_transition"] == 1
    assert result["windows"][0]["classification"] == "income_with_fortune_or_speculation"
    assert result["varga"] == "D2"


def test_custom_requires_every_selected_house_to_be_dasha_open(monkeypatch):
    _disable_varga(monkeypatch)
    result = EventWindowEngine().resolve(
        event_key="custom",
        calculation=_context(),
        activations=(_activation(10, HouseActivationState.DASHA_CONNECTED),),
        include_developing=True,
        focus_houses=(6, 10),
    )

    assert result["qualified_windows"] == 0
    assert result["rejected_summary"]["missing_anchor"] == 1


def test_custom_qualifies_on_dasha_alone_and_treats_confirmation_as_strength(monkeypatch):
    _disable_varga(monkeypatch)
    quiet = _window(opened_by=())
    dasha_only = EventWindowEngine().resolve(
        event_key="custom",
        calculation=_context(quiet),
        activations=(_activation(10, HouseActivationState.DASHA_CONNECTED, quiet),),
        include_developing=True,
        focus_houses=(10,),
    )
    hidden = EventWindowEngine().resolve(
        event_key="custom",
        calculation=_context(quiet),
        activations=(_activation(10, HouseActivationState.DASHA_CONNECTED, quiet),),
        include_developing=False,
        focus_houses=(10,),
    )
    confirmed = EventWindowEngine().resolve(
        event_key="custom",
        calculation=_context(),
        activations=(_activation(10, HouseActivationState.DASHA_CONNECTED),),
        focus_houses=(10,),
    )
    reinforced = EventWindowEngine().resolve(
        event_key="custom",
        calculation=_context(),
        activations=(_activation(10, HouseActivationState.DASHA_TRANSIT_ACTIVATED),),
        focus_houses=(10,),
    )

    assert dasha_only["qualified_windows"] == 1
    assert dasha_only["windows"][0]["strength"] == "developing"
    assert dasha_only["windows"][0]["score"] == 75
    assert dasha_only["windows"][0]["classification"] == "selected_houses_dasha"
    assert hidden["qualified_windows"] == 0
    assert confirmed["windows"][0]["strength"] == "strong"
    assert confirmed["windows"][0]["score"] == 90
    assert confirmed["windows"][0]["classification"] == "selected_houses_confirmed"
    assert reinforced["windows"][0]["strength"] == "exceptional"
    assert reinforced["windows"][0]["score"] == 100
    assert reinforced["windows"][0]["classification"] == "selected_houses_reinforced"
    independent = next(
        step for step in dasha_only["windows"][0]["calculation_trace"]
        if step["key"] == "independent_confirmation"
    )
    assert independent["required"] is False
    assert independent["passed"] is False


def test_custom_without_houses_is_rejected():
    try:
        EventWindowEngine().resolve(
            event_key="custom",
            calculation=_context(),
            activations=(_activation(10, HouseActivationState.DASHA_CONNECTED),),
        )
    except PredictionConfigurationError as exc:
        assert "at least one house" in str(exc)
    else:
        raise AssertionError("custom focus must require houses")

