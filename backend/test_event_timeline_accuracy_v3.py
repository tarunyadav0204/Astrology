import asyncio
import json

from calculators.event_timeline_accuracy_v2 import (
    ACCURACY_ENGINE_VERSION,
    ACCURACY_V3_ENGINE_VERSION,
    LEGACY_ENGINE_VERSION,
    selected_engine_version,
)
from calculators.event_predictor_ai import EventPredictor
from calculators.event_timeline_accuracy_v3 import (
    _annotate_display_tiers,
    _apply_general_monthly_peak_policy,
    _confirmation_sentence,
    _detailed_manifestations,
    _safe_narration,
    _select_people_candidates,
    build_month_activation_graph,
    build_v3_prediction_model,
    derive_desh_kaal_patra,
    user_fact_fingerprint,
    validate_v3_payload,
    v3_publication_mode,
)
from calculators.event_timeline_delivery_v1 import birth_time_reliability_judgment
from prediction_engine.event_windows import (
    EVENT_DEFINITIONS,
    build_relative_event_definition,
    build_relative_health_definition,
    rotate_relative_house,
)
from calculators.event_timeline_v3_context import (
    build_minimal_v3_context,
    clear_v3_natal_caches_for_tests,
    get_cached_v3_kp_evidence,
)


def _evidence(eid, level, planet, natal_house, lordships, transit_house, aspects):
    return {
        "kind": "dasha_lord_transit",
        "evidence_id": eid,
        "dasha_level": level,
        "planet": planet,
        "natal_house": natal_house,
        "lordships": lordships,
        "transit_house": transit_house,
        "aspected_houses": aspects,
        "start_date": "2030-01-01",
        "end_date": "2030-01-31",
    }


def _january_ledger():
    evidence = [
        _evidence("saturn", "mahadasha", "Saturn", 2, [7, 8], 9, [11, 3, 6]),
        _evidence("rahu", "antardasha", "Rahu", 2, [], 8, [2]),
        _evidence("jupiter", "pratyantardasha", "Jupiter", 2, [6, 9], 12, [4, 6, 8]),
        _evidence("mercury", "sookshma", "Mercury", 3, [3, 12], 12, [6]),
    ]
    return {
        "months": {
            str(month): {"evidence": evidence if month == 1 else []}
            for month in range(1, 13)
        }
    }


def test_engine_selection_supports_v3_and_rollbacks(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_ENGINE_VERSION", raising=False)
    assert selected_engine_version() == ACCURACY_V3_ENGINE_VERSION
    monkeypatch.setenv("EVENT_TIMELINE_ENGINE_VERSION", "accuracy_v2")
    assert selected_engine_version() == ACCURACY_ENGINE_VERSION
    monkeypatch.setenv("EVENT_TIMELINE_ENGINE_VERSION", "legacy_v1")
    assert selected_engine_version() == LEGACY_ENGINE_VERSION


def test_v3_defaults_to_optimized_pipeline_with_llm_narration(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_ENGINE_VERSION", raising=False)
    monkeypatch.delenv("EVENT_TIMELINE_V3_PIPELINE", raising=False)
    monkeypatch.delenv("EVENT_TIMELINE_V3_NARRATOR", raising=False)
    model = object()
    monkeypatch.setattr(
        "ai.analysis_llm_backend.build_timeline_narration_llm_model",
        lambda: (model, "test-model", "gemini"),
    )
    predictor = EventPredictor(None, None, None, None)
    assert predictor.engine_version == ACCURACY_V3_ENGINE_VERSION
    assert predictor.v3_pipeline == "optimized"
    assert predictor.v3_narrator == "llm"
    assert predictor.model is model
    assert predictor.model_name == "test-model"


def test_v3_can_roll_back_to_deterministic_narration(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_NARRATOR", "deterministic")
    predictor = EventPredictor(None, None, None, None)
    assert predictor.v3_narrator == "deterministic"
    assert predictor.model is None
    assert predictor.model_name == "deterministic_v3"


def test_deterministic_yearly_reports_real_pipeline_progress(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_ENGINE_VERSION", raising=False)
    monkeypatch.setenv("EVENT_TIMELINE_V3_NARRATOR", "deterministic")
    predictor = EventPredictor(None, None, None, None)
    predictor._last_v3_model = build_v3_prediction_model(
        {"divisional_charts": {}}, {"months": {}}, kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    measured_checkpoints = [12, 22, 25, 35, 47, 60, 68, 72, 80, 84, 92]

    def prepare_with_measured_progress(_birth, _year, **kwargs):
        callback = kwargs.get("progress_callback")
        for percent in measured_checkpoints:
            callback(percent, f"measured_{percent}")
        return "{}"

    monkeypatch.setattr(predictor, "_prepare_yearly_data", prepare_with_measured_progress)
    progress = []
    result = asyncio.run(predictor.predict_yearly_events(
        {"date": "1990-01-01"}, 2030, progress_callback=progress.append,
    ))
    assert result["status"] == "success"
    yearly_percents = [row["progress_percent"] for row in progress]
    assert yearly_percents == [5, *measured_checkpoints, 93, 94, 96]
    assert yearly_percents == sorted(yearly_percents)
    assert all(row["generation_mode"] == "deterministic" for row in progress)
    assert progress[-1]["progress_stage"] == "finalizing_timeline"

    monthly_progress = []
    monthly = asyncio.run(predictor.predict_monthly_deep(
        {"date": "1990-01-01"}, 2030, 1, progress_callback=monthly_progress.append,
    ))
    assert monthly["status"] == "success"
    monthly_percents = [row["progress_percent"] for row in monthly_progress]
    assert monthly_percents == [5, *measured_checkpoints, 93, 94, 96]
    assert monthly_percents == sorted(monthly_percents)
    assert all(row["generation_mode"] == "deterministic" for row in monthly_progress)


def test_integrated_monthly_deep_compares_against_the_full_year(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    monkeypatch.setenv("EVENT_TIMELINE_V3_NARRATOR", "deterministic")
    predictor = EventPredictor(None, None, None, None)
    captured = {}

    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_minimal_v3_context",
        lambda *_args, **_kwargs: {"context_version": "test", "d1_chart": {}},
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_target_year_dasha_facts",
        lambda *_args, **_kwargs: {"scope": "year"},
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_target_year_transit_facts",
        lambda *_args, **_kwargs: {str(month): {} for month in range(1, 13)},
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_target_month_dasha_facts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("month-only dasha path used")),
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_month_transit_facts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("month-only transit path used")),
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_target_year_supporting_context",
        lambda *_args, **kwargs: captured.setdefault("supporting_month_ids", list(kwargs["month_ids"])) or {},
    )
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_birth_time_sensitivity",
        lambda *_args, **_kwargs: {},
    )

    def fake_ledger(*_args, **kwargs):
        captured["ledger_month_ids"] = list(kwargs["month_ids"])
        return {"months": {str(month): {} for month in kwargs["month_ids"]}}

    monkeypatch.setattr("calculators.event_predictor_ai.build_evidence_ledger", fake_ledger)
    monkeypatch.setattr(
        "calculators.event_predictor_ai.build_v3_prediction_model",
        lambda *_args, **_kwargs: {"months": {str(month): {} for month in range(1, 13)}},
    )

    marker = json.loads(predictor._prepare_v3_optimized_data(
        {"date": "1990-01-01"}, 2030, selected_month=10,
    ))
    assert marker["comparison_scope"] == "full_year"
    assert captured["supporting_month_ids"] == list(range(1, 13))
    assert captured["ledger_month_ids"] == list(range(1, 13))


def test_event_timeline_trusts_supplied_birth_time_by_default(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_TRUST_SUPPLIED_BIRTH_TIME", raising=False)
    result = birth_time_reliability_judgment(
        {"birth_time_reliability": {"verified": False, "available": False}},
        {"available": True},
        {"complete": True},
    )
    assert result["verdict"] == "stable"
    assert result["source"] == "user_provided"
    assert result["available"] is True
    assert result["assumption"] == "user_supplied_birth_time_is_authoritative"
    assert result["kp_specificity"] == "retained"
    assert result["varga_specificity"] == "retained"

    monkeypatch.setenv("EVENT_TIMELINE_TRUST_SUPPLIED_BIRTH_TIME", "false")
    rollback = birth_time_reliability_judgment(
        {"birth_time_reliability": {"verified": False, "available": False}},
        {"available": True},
        {"complete": True},
    )
    assert rollback["verdict"] == "unknown"
    assert rollback["kp_specificity"] == "downgraded"


def test_scenario_why_includes_channel_specific_evidence():
    graph = {
        "all_activated_houses": [2, 4, 11],
        "houses": {
            "2": {"dasha_channels": [{"planet": "Venus", "dasha_level": "antardasha"}]},
            "4": {"dasha_channels": [{"planet": "Saturn", "dasha_level": "mahadasha"}]},
            "11": {"transit_planets": ["Mercury"]},
        },
    }
    channel = {
        "native_anchor_houses": [4],
        "active_companion_houses": [2, 11],
        "active_karakas": ["Venus"],
        "varga_required_for_specificity": "D16",
        "selected_channel": "vehicle/conveyance acquisition",
        "specificity": "channel_distinguished",
    }
    scenarios = _detailed_manifestations("vehicle_purchase", graph, {}, channel)
    assert scenarios
    assert all("vehicle/conveyance acquisition" in row["reasoning"] for row in scenarios)
    assert all("D16 confirms the same channel" in row["reasoning"] for row in scenarios)


def test_divisional_explanation_names_only_cross_chart_confirming_carriers():
    text = _confirmation_sentence(
        {"verdict": "unavailable"},
        {
            "chart": "D30",
            "available": True,
            "confirmed": True,
            "required_divisional_houses": [1, 6, 8, 12],
            "confirmed_carriers": [
                {"planet": "Saturn", "d1_event_links": [6, 8], "houses": [1, 8, 12]},
            ],
            "non_confirming_carriers": [
                {"planet": "Venus", "d1_event_links": [8], "houses": []},
            ],
        },
    )
    assert "Saturn links D1 H6 and H8 with D30 H1, H8, and H12" in text
    assert "Venus does not repeat the required houses in both charts" in text
    assert "D30 also confirms the active dasha carriers" not in text


def test_minimal_natal_and_kp_calculations_are_reused_across_years():
    clear_v3_natal_caches_for_tests()
    calls = {"chart": 0, "sav": 0, "kp": 0}
    planets = {
        planet: {"longitude": index * 35.0, "retrograde": False, "house": index + 1}
        for index, planet in enumerate(
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")
        )
    }

    class Chart:
        def calculate_chart(self, _birth):
            calls["chart"] += 1
            return {"ascendant": 10.0, "ayanamsa": 24.0, "planets": planets}

    class Sav:
        def __init__(self, _birth, _chart):
            pass

        def calculate_sarvashtakavarga(self):
            calls["sav"] += 1
            return {"sarvashtakavarga": {str(i): 28 for i in range(12)}}

    birth = {"date": "1990-01-15", "time": "10:30", "latitude": 28.6, "longitude": 77.2, "timezone": "Asia/Kolkata"}
    first = build_minimal_v3_context(birth, chart_calculator=Chart(), ashtakavarga_calculator_cls=Sav)
    second = build_minimal_v3_context(birth, chart_calculator=Chart(), ashtakavarga_calculator_cls=Sav)
    assert first["cache_status"] == "miss"
    assert second["cache_status"] == "hit"
    assert calls["chart"] == 1 and calls["sav"] == 1

    def calculate_kp():
        calls["kp"] += 1
        return {"cusp_lords": {}}

    assert get_cached_v3_kp_evidence(birth, calculate_kp) == {"cusp_lords": {}}
    assert get_cached_v3_kp_evidence(birth, calculate_kp) == {"cusp_lords": {}}
    assert calls["kp"] == 1


def test_activation_graph_preserves_full_saturn_rahu_jupiter_network():
    graph = build_month_activation_graph(_january_ledger()["months"]["1"])
    assert {2, 3, 4, 6, 7, 8, 9, 11, 12}.issubset(set(graph["all_activated_houses"]))
    assert {"Saturn", "Jupiter"}.issubset(set(graph["houses"]["6"]["transit_planets"]))
    assert set(graph["houses"]["2"]["dasha_planets"]) == {"Saturn", "Rahu", "Jupiter"}


def test_core_dasha_direct_transit_is_background_permission_not_its_own_trigger(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    saturn_only = [
        _evidence("saturn", "mahadasha", "Saturn", 2, [7, 8], 9, [11, 3, 6]),
    ]
    graph = build_month_activation_graph({"evidence": saturn_only})
    assert 9 not in graph["dasha_open_houses"]
    assert {2, 7, 8}.issubset(set(graph["dasha_open_houses"]))
    assert 9 in graph["core_dasha_transit_occupied_houses"]
    assert 9 in graph["event_anchor_permission_houses"]

    background_only = {"months": {"1": {"evidence": saturn_only}}}
    without_trigger = build_v3_prediction_model(
        {"divisional_charts": {}}, background_only, kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    assert not any(
        row["event_key"] == "foreign_travel"
        for row in without_trigger["months"]["1"]["qualified_candidates"]
    )

    mercury_trigger = _evidence(
        "mercury", "pratyantardasha", "Mercury", 2, [3, 12], 12, [10]
    )
    with_trigger = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {"1": {"evidence": saturn_only + [mercury_trigger]}}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    travel = next(
        row for row in with_trigger["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "foreign_travel"
    )
    assert travel["anchor_natal_dasha_hits"] == []
    assert travel["anchor_dasha_transit_hits"] == [9]
    assert travel["background_permission_houses"] == [9]
    assert travel["required_direct_transit_houses"] == [9, 12]
    assert any(row["house"] == 12 and row["planet"] == "Mercury" for row in travel["direct_timing_channels"])
    assert any(row["planet"] == "Mercury" for row in travel["independent_timing_channels"])
    assert "persistent background permission" in travel["activation_reasoning"]

    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "delivery_v1")
    rollback = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {"1": {"evidence": saturn_only + [mercury_trigger]}}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    assert not any(
        row["event_key"] == "foreign_travel"
        for row in rollback["months"]["1"]["qualified_candidates"]
    )


def test_relative_reference_house_is_rotation_origin_not_activation_gate(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    # Spouse is read from H7, but no channel activates native H7 here. Saturn's
    # natal H3 lordship opens the spouse-relative long-travel anchor instead.
    saturn = _evidence("saturn", "mahadasha", "Saturn", 2, [3], 8, [10, 2, 5])
    facts = {"relationships": ["I am married to my wife"]}
    without_trigger = build_v3_prediction_model(
        {"divisional_charts": {}}, {"months": {"1": {"evidence": [saturn]}}},
        kp_evidence={}, user_facts=facts, year=2030, age=40,
    )
    assert not any(
        row.get("event_key") == "relative_spouse_foreign_travel"
        for row in without_trigger["months"]["1"]["qualified_candidates"]
    )

    mercury = _evidence("mercury", "pratyantardasha", "Mercury", 5, [9], 6, [12])
    with_trigger = build_v3_prediction_model(
        {"divisional_charts": {}}, {"months": {"1": {"evidence": [saturn, mercury]}}},
        kp_evidence={}, user_facts=facts, year=2030, age=40,
    )
    relative_travel = next(
        row for row in with_trigger["months"]["1"]["qualified_candidates"]
        if row.get("event_key") == "relative_spouse_foreign_travel"
    )
    assert relative_travel["subject_anchor_natal_dasha_hits"] == []
    assert relative_travel["subject_anchor_dasha_transit_hits"] == []
    assert 7 not in relative_travel["background_permission_houses"]


def test_persistent_permission_keeps_only_peak_corridor_primary_for_self_and_relatives(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    native_evidence = [
        _evidence("saturn", "mahadasha", "Saturn", 2, [7, 8], 9, [11, 3, 6]),
        _evidence("mercury", "pratyantardasha", "Mercury", 2, [3, 12], 12, [10]),
    ]
    native = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {str(month): {"evidence": native_evidence} for month in range(1, 13)}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    native_travel = [
        row for month in native["months"].values()
        for row in month["qualified_candidates"]
        if row["event_key"] == "foreign_travel"
    ]
    assert len(native_travel) == 12
    assert sum(bool(row.get("persistent_permission_peak")) for row in native_travel) <= 2
    assert sum(
        row["event_key"] == "foreign_travel"
        for month in native["months"].values()
        for row in month["publishable_candidates"]
    ) <= 2

    relative_evidence = [
        _evidence("saturn", "mahadasha", "Saturn", 2, [3], 7, [9, 1, 4]),
        _evidence("mercury", "pratyantardasha", "Mercury", 5, [9], 6, [12]),
    ]
    relative = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {str(month): {"evidence": relative_evidence} for month in range(1, 13)}},
        kp_evidence={}, user_facts={"relationships": ["I am married to my wife"]},
        year=2030, age=40,
    )
    relative_travel = [
        row for month in relative["months"].values()
        for row in month["qualified_candidates"]
        if row["event_key"] == "relative_spouse_foreign_travel"
    ]
    assert len(relative_travel) == 12
    assert sum(bool(row.get("persistent_permission_peak")) for row in relative_travel) <= 2


def test_exhaustive_mode_really_publishes_recurring_permission_events(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    monkeypatch.setenv("EVENT_TIMELINE_V3_PUBLICATION_MODE", "exhaustive")
    evidence = [
        _evidence("saturn", "mahadasha", "Saturn", 2, [7, 8], 9, [11, 3, 6]),
        _evidence("mercury", "pratyantardasha", "Mercury", 2, [3, 12], 12, [10]),
    ]
    model = build_v3_prediction_model(
        {"divisional_charts": {}},
        {"months": {str(month): {"evidence": evidence} for month in range(1, 13)}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    assert all(
        any(row["event_key"] == "foreign_travel" for row in month["publishable_candidates"])
        for month in model["months"].values()
    )
    assert all(
        month["published_candidate_count"] == month["qualified_candidate_count"]
        for month in model["months"].values()
    )


def test_h4_alone_or_h4_with_money_does_not_claim_purchase_without_h11(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    h4 = _evidence("saturn", "mahadasha", "Saturn", 4, [], 4, [6, 10, 1])
    h2 = _evidence("mercury", "pratyantardasha", "Mercury", 2, [2], 2, [8])
    for evidence in ([h4], [h4, h2]):
        model = build_v3_prediction_model(
            {"divisional_charts": {}}, {"months": {"1": {"evidence": evidence}}},
            kp_evidence={}, user_facts={}, year=2030, age=40,
        )
        assert not any(
            row["event_key"] == "property_purchase"
            for row in model["months"]["1"]["qualified_candidates"]
        )

    h11 = _evidence("venus", "antardasha", "Venus", 11, [11], 11, [5])
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, {"months": {"1": {"evidence": [h4, h2, h11]}}},
        kp_evidence={}, user_facts={}, year=2030, age=40,
    )
    rows = {row["event_key"]: row for row in model["months"]["1"]["qualified_candidates"]}
    assert "property_purchase" in rows
    assert "vehicle_purchase" in rows
    property_audit = rows["property_purchase"]["bhava_disambiguation"]
    vehicle_audit = rows["vehicle_purchase"]["bhava_disambiguation"]
    assert "mother" in property_audit["possible_anchor_threads"]
    assert property_audit["selected_channel"] == "land/home acquisition"
    assert property_audit["varga_required_for_specificity"] == "D4"
    assert vehicle_audit["selected_channel"] == "vehicle/conveyance acquisition"
    assert vehicle_audit["varga_required_for_specificity"] == "D16"
    assert "Bhava disambiguation" in rows["property_purchase"]["activation_reasoning"]


def test_parent_subject_identity_uses_d12_separately_from_event_varga(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    context = {
        "divisional_charts": {
            "d12_dwadasamsa": {"planets": {"Saturn": {"house": 4}}},
        }
    }
    model = build_v3_prediction_model(
        context, _january_ledger(), kp_evidence={},
        user_facts={"family": ["My mother lives with us"]}, year=2030, age=40,
    )
    mother_events = [
        row for row in model["months"]["1"]["qualified_candidates"]
        if row.get("subject_key") == "mother"
    ]
    assert mother_events
    assert all(row["subject_varga_confirmation"]["chart"] == "D12" for row in mother_events)
    assert any(row["subject_varga_confirmation"]["confirmed"] for row in mother_events)


def test_relative_house_rotation_and_spouse_health_requires_explicit_subject_fact():
    spouse = build_relative_health_definition("spouse", "Spouse", 7)
    assert rotate_relative_house(7, 6) == 12
    assert rotate_relative_house(7, 8) == 2
    assert rotate_relative_house(7, 12) == 6
    assert spouse.transition.houses == (12, 2, 6)
    assert spouse.transition.minimum_hits == 2

    without_fact = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    assert not any(
        row["event_key"] == "relative_spouse_health"
        for row in without_fact["months"]["1"]["qualified_candidates"]
    )

    with_fact = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={"relationships": ["I am married to my wife"]}, year=2030, age=40,
    )
    event = next(
        row for row in with_fact["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "relative_spouse_health"
    )
    assert event["life_domain"] == "people_health"
    assert event["subject_relative_houses"] == {
        "illness_or_treatment": 12,
        "acute_change_or_intervention": 2,
        "rest_or_hospital_setting": 6,
    }
    assert "not a diagnosis" in event["prediction"]
    assert "Your spouse" not in event["prediction"]
    assert "This prediction is about" not in event["prediction"]
    assert "More than one kind of event" not in event["prediction"]
    assert "H2, H6, and H12" in event["activation_reasoning"]

    ranked_relative_events = [
        row for row in with_fact["months"]["1"]["qualified_candidates"]
        if row.get("subject_key") == "spouse"
        and row.get("claim_scope") == "ranked_manifestation_channel"
    ]
    for row in ranked_relative_events:
        if row["alternative_event_labels"]:
            assert "Other supported readings from the same active houses:" in row["prediction"]
            assert any(label in row["prediction"] for label in row["alternative_event_labels"])

    january = with_fact["months"]["1"]
    relative_source_keys = {
        row.get("source_event_key") for row in january["qualified_candidates"]
        if row.get("subject_key") == "spouse"
    }
    assert "health" in relative_source_keys
    assert len(relative_source_keys - {"health"}) >= 2
    assert all((row.get("subject_key") or "self") == "self" for row in january["publishable_candidates"])
    assert len(january["people_candidates"]) <= 2
    assert len({row["subject_key"] for row in january["people_candidates"]}) == len(january["people_candidates"])

    checked, _warnings = validate_v3_payload({}, with_fact, selected_month=1, narration_expected=False)
    rendered_month = checked["monthly_predictions"][0]
    assert all(row["subject_key"] == "self" for row in rendered_month["events"])
    assert len(rendered_month["people_candidates"]) <= 2
    assert len(rendered_month["people_candidates"]) + len(rendered_month["people_background_candidates"]) == len([
        row for row in january["qualified_candidates"] if row.get("subject_key") == "spouse"
    ])


def test_every_applicable_event_definition_can_be_rotated_for_a_relative():
    relative = {
        key: build_relative_event_definition(definition, "father", "Father", 9)
        for key, definition in EVENT_DEFINITIONS.items()
    }
    assert set(relative) == set(EVENT_DEFINITIONS)
    for key, definition in relative.items():
        assert definition.source_event_key == key
        assert definition.subject_key == "father"
        assert definition.subject_anchor.houses == (9,)
        assert definition.anchor.houses == tuple(
            rotate_relative_house(9, house) for house in EVENT_DEFINITIONS[key].anchor.houses
        ) or key == "health"


def test_newest_user_fact_wins_without_hiding_the_conflicting_history():
    dkp = derive_desh_kaal_patra(
        {"relationships": ["I am now married", "I was single"]},
        age=40,
        target_year=2030,
    )
    assert dkp["relationship_state"] == "married"
    assert len(dkp["fact_basis"]["relationship"]) == 2
    assert any(row["key"] == "spouse" for row in dkp["eligible_relative_subjects"])


def test_structured_relative_profile_makes_subject_eligible_without_chat_facts():
    profiles = [{
        "subject_key": "mother", "display_label": "Mother", "reference_house": 4,
        "life_status": "living", "employment_state": "retired",
        "location_context": "same_city", "enabled": True,
    }]
    dkp = derive_desh_kaal_patra(
        {}, age=40, target_year=2030, relative_profiles=profiles,
    )
    assert dkp["eligible_relative_subjects"] == [{
        "key": "mother", "label": "Mother", "reference_house": 4,
        "source": "structured_family_profile",
    }]
    assert dkp["relative_contexts"]["mother"]["employment_state"] == "retired"
    assert user_fact_fingerprint({}, "en", profiles) != user_fact_fingerprint({}, "en", [])


def test_deceased_or_disabled_relative_profile_is_not_event_eligible():
    profiles = [
        {"subject_key": "mother", "display_label": "Mother", "reference_house": 4, "life_status": "deceased", "enabled": True},
        {"subject_key": "father", "display_label": "Father", "reference_house": 9, "life_status": "living", "enabled": False},
    ]
    dkp = derive_desh_kaal_patra(
        {}, age=40, target_year=2030, relative_profiles=profiles,
    )
    assert dkp["eligible_relative_subjects"] == []


def test_people_selection_has_no_cross_relative_cap():
    candidates = [
        {"candidate_id": f"relative-{subject}", "subject_key": subject, "support_grade": "A", "priority_score": 80 - index, "event_key": "health"}
        for index, subject in enumerate(("spouse", "mother", "father", "child"))
    ]
    visible, overflow, summary = _select_people_candidates(candidates)
    assert {row["subject_key"] for row in visible} == {"spouse", "mother", "father", "child"}
    assert overflow == []
    assert summary["visible_count"] == 4


def test_v3_resolves_multiple_coherent_events_and_restores_llm_omissions():
    model = build_v3_prediction_model(
        {"divisional_charts": {}},
        _january_ledger(),
        kp_evidence={},
        user_facts={},
        year=2030,
        age=40,
    )
    january = model["months"]["1"]
    keys = {row["event_key"] for row in january["qualified_candidates"]}
    assert {"health", "marriage", "foreign_travel", "income_gain"}.issubset(keys)
    assert january["candidate_count"] > 1
    assert january["published_candidate_count"] == 0
    assert january["qualified_candidate_count"] == january["candidate_count"]

    checked, warnings = validate_v3_payload(
        {}, model, selected_month=1, narration_expected=False,
    )
    assert checked["accuracy_layer"] == model["accuracy_layer"]
    assert len(checked["monthly_predictions"][0]["events"]) == january["published_candidate_count"]
    assert len(checked["monthly_predictions"][0]["background_candidates"]) == len(january["background_candidates"])
    if checked["monthly_predictions"][0]["background_candidates"]:
        background = checked["monthly_predictions"][0]["background_candidates"][0]
        assert background["display_tier"] == "weak_signal"
        assert background["support_label"] == "Weak indication"
        assert background["display_reason"] == "weak_support"
        assert background["prediction"]
        assert background["activation_reasoning"]
        assert background["possible_manifestations"]
    assert checked["macro_trends"] == []
    assert warnings == []


def test_v3_llm_packet_contains_all_visible_cards_without_astrology_internals():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={"relationships": ["I am married"]}, year=2030, age=40,
    )
    predictor = EventPredictor.__new__(EventPredictor)
    predictor._last_v3_model = model
    packet = predictor._v3_narration_payload(1)
    candidates = packet["months"]["1"]["candidates"]
    expected_ids = {
        str(candidate["candidate_id"])
        for list_name in (
            "publishable_candidates", "also_possible_candidates",
            "ongoing_background_candidates", "annual_context_candidates",
            "weak_signal_candidates", "people_candidates",
            "people_also_possible_candidates", "people_ongoing_background_candidates",
            "people_annual_context_candidates", "people_weak_signal_candidates",
        )
        for candidate in model["months"]["1"].get(list_name) or []
    }
    assert {str(row["candidate_id"]) for row in candidates} == expected_ids
    assert all("fallback_prediction" not in row for row in candidates)
    assert all("alternative_event_labels" not in row for row in candidates)
    assert all(row["allowed_facts"] for row in candidates)
    assert all(row["stage"].get("phase") for row in candidates)
    assert all(
        "Other supported readings from the same active houses:" not in fact["text"]
        for row in candidates
        for fact in row["allowed_facts"]
    )
    serialized = json.dumps(packet).lower()
    for private_field in (
        "activated_houses", "activation_reasoning", "trigger_logic", "dasha",
        "kp_confirmation", "varga_confirmation", "planet_delivery", "natal_promise",
    ):
        assert private_field not in serialized


def test_v3_yearly_llm_packet_includes_every_rendered_tier_but_batches_stay_monthly():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    predictor = EventPredictor.__new__(EventPredictor)
    predictor._last_v3_model = model
    predictor._month_label = lambda month: "January"
    packet = predictor._v3_narration_payload()
    requested_ids = {
        str(candidate["candidate_id"])
        for month in packet["months"].values()
        for candidate in month["candidates"]
    }
    expected_ids = {
        str(candidate["candidate_id"])
        for month in model["months"].values()
        for list_name in (
            "publishable_candidates", "also_possible_candidates",
            "ongoing_background_candidates", "annual_context_candidates",
            "weak_signal_candidates", "people_candidates",
            "people_also_possible_candidates", "people_ongoing_background_candidates",
            "people_annual_context_candidates", "people_weak_signal_candidates",
        )
        for candidate in month.get(list_name) or []
    }
    assert requested_ids == expected_ids
    for month_key, month_payload in packet["months"].items():
        month_packet = {**packet, "months": {month_key: month_payload}}
        assert len(predictor._create_accuracy_v3_yearly_prompt(
            "", 2030, 40, payload_override=month_packet,
        )) < 40_000


def test_v3_timeout_returns_explicit_invalid_result(monkeypatch):
    predictor = EventPredictor.__new__(EventPredictor)
    predictor._v3_narration_timeout_s = lambda: 0.01

    async def slow_call(*_args, **_kwargs):
        await asyncio.sleep(0.1)
        return {"monthly_predictions": []}

    predictor._get_ai_prediction_async = slow_call
    result = asyncio.run(predictor._get_v3_narration("test"))
    assert result["_timeline_invalid"] is True
    assert "deadline" in result["error"]


def test_v3_yearly_narration_is_split_into_parallel_month_batches(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_NARRATION_CONCURRENCY", "2")
    predictor = EventPredictor.__new__(EventPredictor)
    predictor._last_v3_model = {
        "language": "en",
        "desh_kaal_patra": {},
        "months": {
            str(month): {
                "month_id": month,
                "publishable_candidates": [{
                    "candidate_id": f"C-{month}",
                    "event_family": "Work decision",
                    "prediction": "A work decision may need attention.",
                    "possible_manifestations": [{"scenario": "A work discussion may move forward."}],
                    "manifestation_phase": "developing",
                    "outcome_dimensions": {"ease": "mixed"},
                }],
            }
            for month in (1, 6, 9)
        },
    }
    prompts = []
    active = 0
    max_active = 0

    async def fake_narration(prompt):
        nonlocal active, max_active
        prompts.append(prompt)
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        month_id = next(month for month in (1, 6, 9) if f'"month_id":{month}' in prompt)
        return {
            "monthly_predictions": [{"month_id": month_id, "narrations": []}],
            "_llm_usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
        }

    predictor._get_v3_narration = fake_narration
    result = asyncio.run(predictor._get_v3_yearly_narration_batched(2030, 40))
    assert len(prompts) == 3
    assert max_active == 2
    assert all(prompt.count('"candidate_id":"C-') == 1 for prompt in prompts)
    assert result["_narration_batches"] == {"requested": 3, "completed": 3, "failed": 0}
    assert result["_llm_usage"]["input_tokens"] == 30


def test_v3_llm_narration_applies_to_background_cards_and_rejects_unsafe_copy():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    january = model["months"]["1"]
    background = (january.get("background_candidates") or [])[0]
    narrated = {
        "monthly_predictions": [{
            "month_id": 1,
            "narrations": [{
                "candidate_id": background["candidate_id"],
                "prediction": "You may notice a practical development in this area of life.",
            }],
        }],
    }
    checked, _warnings = validate_v3_payload(narrated, model, selected_month=1)
    rendered = next(
        row for row in checked["monthly_predictions"][0]["background_candidates"]
        if row["candidate_id"] == background["candidate_id"]
    )
    assert rendered["prediction"] == "You may notice a practical development in this area of life."
    assert rendered["narration_source"] == "llm"

    narrated["monthly_predictions"][0]["narrations"][0]["prediction"] = (
        "This event will certainly happen on 2030-01-15 because Saturn guarantees it."
    )
    checked, warnings = validate_v3_payload(narrated, model, selected_month=1)
    rendered = next(
        row for row in checked["monthly_predictions"][0]["background_candidates"]
        if row["candidate_id"] == background["candidate_id"]
    )
    assert rendered["prediction"] == background["prediction"]
    assert rendered["narration_source"] == "deterministic_fallback"
    assert any("unsafe or over-specific" in warning or "technical" in warning for warning in warnings)
    assert checked["narration_status"] == "partial_fallback"


def test_v3_structured_narration_requires_valid_fact_citations():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    predictor = EventPredictor.__new__(EventPredictor)
    predictor._last_v3_model = model
    packet = predictor._v3_narration_payload(1)
    brief = packet["months"]["1"]["candidates"][0]
    candidate_id = str(brief["candidate_id"])
    valid_fact_id = brief["allowed_facts"][0]["fact_id"]
    payload = {"monthly_predictions": [{"month_id": 1, "narrations": [{
        "candidate_id": candidate_id,
        "prediction": "A practical conversation may bring this situation into clearer focus.",
        "used_fact_ids": [valid_fact_id],
    }]}]}
    checked, warnings = validate_v3_payload(
        payload,
        model,
        selected_month=1,
        expected_narration_ids=predictor._last_v3_narration_ids,
        expected_narration_fact_ids=predictor._last_v3_narration_fact_ids,
    )
    rendered = next(
        row for list_name in (
            "events", "also_possible_candidates", "ongoing_background_candidates",
            "annual_context_candidates", "weak_signal_candidates", "people_candidates",
            "people_also_possible_candidates", "people_ongoing_background_candidates",
            "people_annual_context_candidates", "people_weak_signal_candidates",
        )
        for row in checked["monthly_predictions"][0].get(list_name) or []
        if row["candidate_id"] == candidate_id
    )
    assert rendered["prediction"] == payload["monthly_predictions"][0]["narrations"][0]["prediction"]
    assert rendered["narration_source"] == "llm"
    assert not any("invalid fact citations" in warning for warning in warnings)

    payload["monthly_predictions"][0]["narrations"][0]["used_fact_ids"] = ["F999"]
    checked, warnings = validate_v3_payload(
        payload,
        model,
        selected_month=1,
        expected_narration_ids=predictor._last_v3_narration_ids,
        expected_narration_fact_ids=predictor._last_v3_narration_fact_ids,
    )
    assert any("invalid fact citations" in warning for warning in warnings)
    rendered = next(
        row for list_name in (
            "events", "also_possible_candidates", "ongoing_background_candidates",
            "annual_context_candidates", "weak_signal_candidates", "people_candidates",
            "people_also_possible_candidates", "people_ongoing_background_candidates",
            "people_annual_context_candidates", "people_weak_signal_candidates",
        )
        for row in checked["monthly_predictions"][0].get(list_name) or []
        if row["candidate_id"] == candidate_id
    )
    assert rendered["narration_source"] == "deterministic_fallback"


def test_v3_foreign_travel_has_auditable_why_and_distinct_scenarios():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )
    event = next(
        row for row in model["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "foreign_travel"
    )
    why = event["activation_reasoning"]
    assert "Saturn Mahadasha" in why
    assert "Rahu Antardasha" in why
    assert "Jupiter Pratyantardasha" in why
    assert "natal lordship" in why
    assert "transit placement" in why
    assert "H9" in why and "H12" in why
    assert "KP confirmation is unavailable" in why
    assert "D9 confirmation is unavailable" in why

    scenarios = event["possible_manifestations"]
    assert len(scenarios) == 1
    assert scenarios[0]["scenario"] != event["event_family"]
    assert "temporary stay away" in scenarios[0]["scenario"]
    assert "passed the dasha-house" not in scenarios[0]["reasoning"]
    assert "Pratyantardasha" in scenarios[0]["reasoning"]


def test_v3_explanation_can_roll_back_and_cache_fingerprint_changes(monkeypatch):
    facts = {"career": ["I am a homemaker"]}
    detailed_fingerprint = user_fact_fingerprint(facts)
    monkeypatch.setenv("EVENT_TIMELINE_V3_EXPLANATION_VERSION", "legacy_v1")
    legacy_fingerprint = user_fact_fingerprint(facts)
    assert detailed_fingerprint != legacy_fingerprint

    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts=facts, year=2030, age=40,
    )
    event = next(
        row for row in model["months"]["1"]["qualified_candidates"]
        if row["event_key"] == "foreign_travel"
    )
    assert event["explanation_version"] == "legacy_v1"
    assert event["possible_manifestations"][0]["reasoning"] == (
        "This event combination passed the dasha-house and transit gates."
    )


def test_desh_kaal_patra_never_calls_homemaker_activation_a_promotion(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_PUBLICATION_MODE", "exhaustive")
    dkp = derive_desh_kaal_patra(
        {
            "career": ["I am a homemaker and manage the household"],
            "family": ["I am married and have two children"],
        },
        age=42,
        target_year=2030,
    )
    assert dkp["employment_state"] == "homemaker"
    assert dkp["relationship_state"] == "married"
    assert dkp["parenthood_state"] == "has_children"

    # Build a direct H10 + H11 promotion signature with a transit trigger.
    evidence = [
        _evidence("sun", "mahadasha", "Sun", 10, [10], 10, [4]),
        _evidence("jupiter", "antardasha", "Jupiter", 11, [11], 11, [3, 5, 7]),
    ]
    ledger = {"months": {str(m): {"evidence": evidence if m == 1 else []} for m in range(1, 13)}}
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, ledger, kp_evidence={},
        user_facts={"career": ["I am a homemaker and manage the household"]},
        year=2030, age=42,
    )
    promotion = next(row for row in model["months"]["1"]["publishable_candidates"] if row["event_key"] == "promotion")
    assert "promotion" not in promotion["event_family"].lower()
    assert "promotion" in promotion["forbidden_terms"]

    narrated = {
        "monthly_predictions": [{
            "month_id": 1,
            "events": [{
                "candidate_id": promotion["candidate_id"],
                "prediction": "You will definitely receive a job promotion.",
                "possible_manifestations": [],
            }],
        }],
    }
    checked, warnings = validate_v3_payload(narrated, model, selected_month=1)
    event = next(row for row in checked["monthly_predictions"][0]["events"] if row["candidate_id"] == promotion["candidate_id"])
    assert "promotion" not in event["prediction"].lower()
    assert any("Desh-Kaal-Patra" in warning for warning in warnings)


def test_publication_policy_is_prioritized_by_default_and_can_roll_back(monkeypatch):
    monkeypatch.delenv("EVENT_TIMELINE_V3_PUBLICATION_MODE", raising=False)
    assert v3_publication_mode() == "prioritized"
    prioritized = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )["months"]["1"]
    assert prioritized["published_candidate_count"] <= 5
    assert prioritized["qualified_candidate_count"] >= prioritized["published_candidate_count"]

    monkeypatch.setenv("EVENT_TIMELINE_V3_PUBLICATION_MODE", "exhaustive")
    exhaustive = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )["months"]["1"]
    assert exhaustive["published_candidate_count"] == exhaustive["qualified_candidate_count"]


def test_deterministic_copy_reflects_pathway_and_manifestation_phase():
    january = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40,
    )["months"]["1"]
    travel = next(row for row in january["qualified_candidates"] if row["event_key"] == "foreign_travel")
    assert "temporary stay away" in travel["prediction"]
    assert travel["manifestation_phase"] in {"result_window", "developing", "preparatory"}
    assert travel["priority_factors"]


def test_event_card_predictions_use_plain_language_and_keep_astrology_in_why():
    model = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={"relationships": ["I am married"]}, year=2030, age=40,
    )
    rows = model["months"]["1"]["qualified_candidates"]
    banned = (
        "mahadasha", "antardasha", "pratyantardasha", "sookshma", "dasha",
        "transit", "natal", " kp ", "d9", "varga", "bhava", "karaka",
        "ashtakavarga", "kakshya", "saturn", "jupiter", "mercury", "venus",
        "mars", "rahu", "ketu",
    )
    assert rows
    for row in rows:
        prediction = f" {row['prediction'].lower()} "
        assert not any(term in prediction for term in banned)
        assert row["activation_reasoning"]

    marriage = next(row for row in rows if row["event_key"] == "marriage")
    supplied = {
        "monthly_predictions": [{
            "month_id": 1,
            "events": [{
                "candidate_id": marriage["candidate_id"],
                "prediction": "Mercury and Saturn transit this bhava, while KP and D9 confirm it.",
            }],
        }]
    }
    rendered, warnings = _safe_narration(marriage, supplied["monthly_predictions"][0]["events"][0])
    assert "saturn" not in rendered["prediction"].lower()
    assert "kp" not in rendered["prediction"].lower()
    assert any("technical user-facing narration" in warning for warning in warnings)


def test_possible_scenarios_never_expose_engine_implementation_details():
    repeated = {
        "candidate_id": "kg-private-intimacy",
        "event_family": "Private closeness, intimacy or bed-comfort development",
        "prediction": "Private closeness may develop.",
        "explanation_version": "detailed_v2",
        "possible_manifestations": [{
            "scenario": "Private closeness, intimacy or bed-comfort development",
            "reasoning": "KG pattern pattern.relationship.private_intimacy supplied the event structure.",
        }],
    }
    rendered, _warnings = _safe_narration(repeated, None)
    assert rendered["possible_manifestations"] == []

    distinct = {
        **repeated,
        "possible_manifestations": [{
            "scenario": "A private relationship may become warmer or more affectionate.",
            "reasoning": "Internal calculation details that must not reach the app.",
        }],
    }
    rendered, _warnings = _safe_narration(distinct, None)
    assert rendered["possible_manifestations"] == [{
        "scenario": "A private relationship may become warmer or more affectionate."
    }]


def test_hindi_templates_preserve_astrology_and_localize_user_facing_copy():
    english = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40, language="en",
    )
    hindi = build_v3_prediction_model(
        {"divisional_charts": {}}, _january_ledger(), kp_evidence={},
        user_facts={}, year=2030, age=40, language="hi-IN",
    )
    english_rows = {row["event_key"]: row for row in english["months"]["1"]["qualified_candidates"]}
    hindi_rows = {row["event_key"]: row for row in hindi["months"]["1"]["qualified_candidates"]}
    assert english_rows.keys() == hindi_rows.keys()
    assert hindi["language"] == "hi"
    assert user_fact_fingerprint({}, "en") != user_fact_fingerprint({}, "hi")

    travel_en = english_rows["foreign_travel"]
    travel_hi = hindi_rows["foreign_travel"]
    assert travel_en["candidate_id"] == travel_hi["candidate_id"]
    assert travel_en["anchor_hits"] == travel_hi["anchor_hits"]
    assert any("\u0900" <= char <= "\u097f" for char in travel_hi["event_family"])
    assert any("\u0900" <= char <= "\u097f" for char in travel_hi["prediction"])
    assert any("\u0900" <= char <= "\u097f" for char in travel_hi["activation_reasoning"])
    assert any("\u0900" <= char <= "\u097f" for char in travel_hi["possible_manifestations"][0]["scenario"])

    checked, _ = validate_v3_payload({}, hindi, narration_expected=False)
    assert checked["macro_trends"] == []
    weak = checked["monthly_predictions"][0]["weak_signal_candidates"]
    assert weak
    assert all(any("\u0900" <= char <= "\u097f" for char in row["support_label"]) for row in weak)


def test_display_tiers_separate_alternatives_background_and_weak_signals():
    primary = {"candidate_id": "p", "support_grade": "A", "life_domain": "home", "subject_key": "self"}
    alternative = {"candidate_id": "a", "support_grade": "B", "life_domain": "home", "subject_key": "self"}
    ongoing = {
        "candidate_id": "o", "support_grade": "A", "life_domain": "travel", "subject_key": "self",
        "background_permission_houses": [9], "persistent_permission_peak": False,
    }
    weak = {"candidate_id": "w", "support_grade": "C", "life_domain": "money", "subject_key": "self"}
    month = {
        "qualified_candidates": [dict(primary), dict(alternative), dict(ongoing), dict(weak)],
        "publishable_candidates": [dict(primary)],
        "background_candidates": [dict(alternative), dict(ongoing), dict(weak)],
        "people_candidates": [], "people_background_candidates": [], "selection_summary": {},
    }
    _annotate_display_tiers({"1": month}, "en")
    assert [row["candidate_id"] for row in month["also_possible_candidates"]] == ["a"]
    assert month["also_possible_candidates"][0]["display_reason"] == "competing_event_stronger"
    assert [row["candidate_id"] for row in month["ongoing_background_candidates"]] == ["o"]
    assert [row["candidate_id"] for row in month["weak_signal_candidates"]] == ["w"]
    assert len(month["background_candidates"]) == 3


def test_general_peak_policy_stops_one_event_from_becoming_twelve_predictions(monkeypatch):
    monkeypatch.setenv("EVENT_TIMELINE_V3_ACCURACY_LAYER", "integrated_v2")
    monkeypatch.setenv("EVENT_TIMELINE_V3_PUBLICATION_MODE", "prioritized")
    months = {}
    for month_id in range(1, 13):
        phase = "exact" if month_id in {3, 9} else "stationary_or_boundary"
        orb = 0.05 if month_id == 3 else 0.2 if month_id == 9 else 1.8
        candidate = {
            "candidate_id": f"health-{month_id}",
            "event_key": "health",
            "source_event_key": "health",
            "subject_key": "self",
            "life_domain": "health",
            "support_grade": "B",
            "priority_score": 110,
            "manifestation_phase": "result_window",
            "timing_windows": [{"start_date": f"2030-{month_id:02d}-01", "end_date": f"2030-{month_id:02d}-28"}],
            "independent_timing_channels": [{
                "planet": "Mars" if month_id < 7 else "Mercury",
                "dasha_level": "sookshma",
                "mechanism": "natal_lordship",
            }],
            "exact_transit_contacts": {"event_contacts": [{
                "transit_planet": "Mars",
                "target_type": "event_lord_or_karaka",
                "peak_phase": phase,
                "peak_orb": orb,
                "peak_date": f"2030-{month_id:02d}-15",
                "start_date": f"2030-{month_id:02d}-14",
                "end_date": f"2030-{month_id:02d}-16",
            }]},
        }
        months[str(month_id)] = {
            "qualified_candidates": [candidate],
            "publishable_candidates": [dict(candidate)],
            "background_candidates": [],
            "people_candidates": [],
            "people_background_candidates": [],
            "selection_summary": {},
            "people_selection_summary": {},
        }
    _apply_general_monthly_peak_policy(months)
    _annotate_display_tiers(months, "en")
    primary_months = [month for month, row in months.items() if row["publishable_candidates"]]
    assert 1 <= len(primary_months) <= 2
    assert "3" in primary_months
    assert sum(len(row["publishable_candidates"]) for row in months.values()) <= 2
    assert all(
        row["selection_summary"]["forced_minimum"] == 0
        for row in months.values()
    )
    assert any(
        event["display_tier"] == "ongoing_background"
        for row in months.values()
        for event in row["background_candidates"]
    )
    assert months["1"]["annual_context_candidates"]
    assert not months["1"]["ongoing_background_candidates"]
    assert months["1"]["prediction_state"] == "quiet_month"
