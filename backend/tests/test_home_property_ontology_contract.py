from __future__ import annotations

from datetime import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from ai.intent_router import apply_home_routing_guards  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _attach_missing_home_fact_markers,
    _align_home_visible_astrology_contract,
    _build_forward_event_dasha_scan,
    _build_instant_context,
    _build_instant_composer_prompt_v3,
    _fit_composer_brief,
    _instant_relational_voice_contract,
    _looks_like_open_ended_life_event_when,
    _mode_selection_from_intent,
    _requested_charts_from_intent,
    _resolve_home_fact_contract,
    _strip_home_fact_markers,
    _validate_home_fact_markers,
)
from instant_chat_v2.graph_live import (  # noqa: E402
    _live_contract,
    apply_live_graph_policy,
    enforce_live_graph_answer,
)
from instant_chat_v2.home import BOUNDARY_HOME_SUBTYPES, HOME_PROFILES, TIMING_HOME_SUBTYPES  # noqa: E402
from instant_chat_v2.home_graph_policy import HomeGraphPolicyStore  # noqa: E402
from instant_chat_v2.home_graph_runtime import (  # noqa: E402
    compare_home_graph_policy,
    home_graph_runtime_key,
)
from instant_chat_v2.home_calculation import _home_timing_decision, _vehicle_color_synthesis, build_home_foundation  # noqa: E402
from instant_chat_v2.home_remedies import build_classical_property_remedy_blueprint  # noqa: E402
from instant_chat_v2.planner import build_query_plan  # noqa: E402
from instant_chat_v2.orchestrator import build_instant_v2_packet  # noqa: E402
from instant_chat_v2.translated_astrology import build_translated_astrology_contract  # noqa: E402


def test_typed_home_timing_route_cannot_fall_back_to_comparison_mode() -> None:
    selection = _mode_selection_from_intent({
        "category": "property",
        "home_subtype": "property_purchase_timing",
        "answer_mode": "comparison_choice",
        "route_action": "answer",
    })
    assert selection is not None
    assert selection["raw_answer_mode"] == "comparison_choice"
    assert selection["answer_mode"] == "event_prediction"


def _context(key: str, *, timing: bool = False) -> dict:
    policy = HomeGraphPolicyStore().resolve(key)
    assert policy is not None
    boundary = key in BOUNDARY_HOME_SUBTYPES
    availability = {
        "d1": not boundary,
        "d4": not boundary,
        "d16": not boundary and "home:D16" in policy.required_factors,
        "dignity_strength": not boundary,
        "kp_fructification": timing,
        "remedy_blueprint": key == "property_remedy",
        "scope_boundary": boundary,
    }
    context = {
        "intent_summary": {"category": "property", "home_subtype": key},
        "normalized_evidence": {"home_foundation": {
            "home_subtype": key,
            "houses_available": [int(x.split("H", 1)[1]) for x in policy.required_factors if x.startswith("home:H")],
            "availability": availability,
            "timing_synthesis": {
                "dasha_activation_established": timing,
                "transit_confirmation_established": timing,
                "dasha_evaluation_complete": timing,
                "transit_evaluation_complete": timing,
                "kp_fructification": {"complete": timing},
                "timing_windows": [{"transit_confirmed": True}] if timing else [],
            },
        }},
    }
    if timing:
        context["current_dashas"] = {"levels": {"MD": {"planet": "Jupiter"}}}
        context["current_transits"] = {"planets": {"Jupiter": {"house": 4}}}
    return context


def test_home_ontology_compiles_and_covers_every_runtime_route() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_home_property_ontology.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "30 competency questions" in result.stdout
    assert set(HomeGraphPolicyStore().runtime_keys()) == set(HOME_PROFILES)


def test_static_routes_exclude_timing_and_timed_routes_require_triangular_evidence() -> None:
    store = HomeGraphPolicyStore()
    for key in set(HOME_PROFILES) - set(TIMING_HOME_SUBTYPES) - set(BOUNDARY_HOME_SUBTYPES):
        policy = store.resolve(key)
        assert policy is not None
        assert "home:DashaActivation" in policy.default_exclusions, key
    for key in TIMING_HOME_SUBTYPES:
        policy = store.resolve(key)
        assert policy is not None
        required = set(policy.required_factors)
        assert {"home:KPFructification", "home:DashaActivation", "home:TransitConfirmation"}.issubset(required)
        mode = "event_prediction"
        result = compare_home_graph_policy(
            category="property", query_plan={"home_subtype": key, "answer_mode": mode},
            observed_answer_mode=mode, context=_context(key, timing=True),
        )
        assert result and result["match"], (key, result)


def test_routing_preserves_semantics_and_only_requests_d1_d4() -> None:
    intent = {"category": "property", "home_subtype": "property_potential"}
    apply_home_routing_guards(intent)
    assert intent["category"] == "property"
    assert intent["divisional_charts"] == ["D1", "D4"]
    assert _requested_charts_from_intent(intent, answer_mode="potential_capacity") == ["D1", "D4"]
    vehicle = {"category": "vehicle", "home_subtype": "vehicle_potential"}
    apply_home_routing_guards(vehicle)
    assert vehicle["category"] == "vehicles"
    stale_vehicle = {
        "category": "vehicles", "home_subtype": "vehicle_potential",
        "answer_mode": "potential_capacity", "needs_transits": True,
    }
    apply_home_routing_guards(stale_vehicle)
    assert stale_vehicle["home_subtype"] == "vehicle_potential"
    assert stale_vehicle["answer_mode"] == "potential_capacity"
    timed_vehicle = {"category": "vehicle", "home_subtype": "vehicle_potential", "needs_transits": True}
    apply_home_routing_guards(timed_vehicle)
    assert timed_vehicle["home_subtype"] == "vehicle_timing"
    assert timed_vehicle["answer_mode"] == "event_prediction"
    assert timed_vehicle["divisional_charts"] == ["D1", "D4", "D16"]
    assert _requested_charts_from_intent(timed_vehicle, answer_mode="event_prediction") == ["D1", "D4", "D16"]
    color_vehicle = {
        "category": "vehicles", "home_subtype": "vehicle_selection",
        "answer_mode": "event_prediction", "needs_transits": True,
        "period_window": {"kind": "current", "start": "2026-09-04", "end": "2026-09-04"},
        "required_evidence": ["future_dasha_event_windows", "transit_event_windows"],
    }
    apply_home_routing_guards(color_vehicle)
    assert color_vehicle["answer_mode"] == "comparison_choice"
    assert color_vehicle["needs_transits"] is False
    assert "period_window" not in color_vehicle
    assert color_vehicle["required_evidence"] == []
    assert color_vehicle["divisional_charts"] == ["D1", "D4", "D16"]
    timed_move = {"category": "property", "home_subtype": "relocation_home", "answer_mode": "timing_window"}
    apply_home_routing_guards(timed_move)
    assert timed_move["home_subtype"] == "relocation_timing"
    static_move = {"category": "property", "home_subtype": "relocation_home", "answer_mode": "potential_capacity"}
    apply_home_routing_guards(static_move)
    assert static_move["home_subtype"] == "relocation_home"
    assert static_move["answer_mode"] == "comparison_choice"
    boundary = {"category": "property", "home_subtype": "property_dispute_handoff"}
    apply_home_routing_guards(boundary)
    assert boundary["route_action"] == "handoff"
    assert boundary["divisional_charts"] == []
    joint = {"category": "property", "home_subtype": "joint_property", "answer_mode": "topic_reading"}
    apply_home_routing_guards(joint)
    assert joint["answer_mode"] == "comparison_choice"
    capacity = {"category": "property", "home_subtype": "property_potential", "answer_mode": "topic_reading"}
    apply_home_routing_guards(capacity)
    assert capacity["answer_mode"] == "potential_capacity"


def test_explicit_multilingual_remedy_signal_overrides_obstacle_diagnosis() -> None:
    intent = {
        "category": "property",
        "home_subtype": "property_obstacles",
        "answer_mode": "problem_diagnosis",
        "explicit_remedy_request": True,
    }
    apply_home_routing_guards(intent)
    assert intent["home_subtype"] == "property_remedy"
    assert intent["answer_mode"] == "remedy_action"
    assert intent["divisional_charts"] == ["D1", "D4"]


def test_property_remedy_is_classical_and_selected_from_d1_d4_not_timing() -> None:
    d1 = [
        {
            "chart": "D1", "house": 4, "available": True,
            "lord": "Venus", "lord_house": 11, "lord_dignity": "own_sign",
            "occupants": ["Moon"],
            "house_aspects": [{"planet": "Saturn", "tone": "functional_malefic"}],
        },
        {
            "chart": "D1", "house": 8, "available": True,
            "lord": "Saturn", "lord_house": 2, "lord_dignity": "enemy_sign",
            "occupants": ["Ketu"], "house_aspects": [],
        },
    ]
    d4 = [{
        "chart": "D4", "house": 4, "available": True,
        "lord": "Moon", "lord_house": 10, "lord_dignity": "friendly_sign",
        "occupants": [],
        "house_aspects": [
            {"planet": "Moon", "tone": "functional_benefic"},
            {"planet": "Jupiter", "tone": "functional_benefic"},
            {"planet": "Saturn", "tone": "functional_malefic"},
        ],
    }]
    blueprint = build_classical_property_remedy_blueprint(
        d1_conditions=d1,
        d4_conditions=d4,
        natal_factors_by_house={},
    )
    top = blueprint["top_recommendation"]
    assert blueprint["selection_mode"] == "single_top"
    assert blueprint["scope"].endswith("D1 and D4")
    assert top["planet"] == "Saturn"
    assert top["classification"] == "classical_graha_shanti"
    assert "sesame-oil lamp" in top["action"]
    assert "108 times" in top["action"]
    assert "Saturn directly aspects House 4" in top["astrological_reason"]
    rendered = str(blueprint["ranked_remedies"]).lower()
    assert "current dasha" not in str(top).lower()
    assert not any(term in rendered for term in ("journaling", "budgeting plan", "communication exercise"))
    assert "gemstone" in blueprint["caution"].lower()


def test_property_remedy_fails_closed_without_a_calculated_obstruction() -> None:
    clean_h4 = [{
        "chart": "D1", "house": 4, "available": True,
        "lord": "Venus", "lord_house": 11, "lord_dignity": "own_sign",
        "occupants": ["Moon"],
        "house_aspects": [{"planet": "Jupiter", "tone": "functional_benefic"}],
    }]
    blueprint = build_classical_property_remedy_blueprint(
        d1_conditions=clean_h4,
        d4_conditions=clean_h4,
        natal_factors_by_house={},
    )
    assert blueprint["evidence_complete"] is False
    assert blueprint["top_recommendation"] == {}

    incomplete = build_classical_property_remedy_blueprint(
        d1_conditions=[{
            "chart": "D1", "house": 4, "available": True,
            "lord": "Venus", "lord_house": 11, "lord_dignity": "own_sign",
            "occupants": [],
            "house_aspects": [{"planet": "Saturn", "tone": "functional_malefic"}],
        }],
        d4_conditions=[],
        natal_factors_by_house={},
    )
    assert incomplete["required_layers"]["d1_fourth_house"] is True
    assert incomplete["required_layers"]["d4_fourth_house"] is False
    assert incomplete["evidence_complete"] is False
    assert incomplete["top_recommendation"] == {}


def test_property_graph_exposes_classical_remedy_contract_without_modern_substitutes() -> None:
    context = _context("property_remedy")
    top = {
        "planet": "Saturn",
        "classification": "classical_graha_shanti",
        "action": "Light a sesame-oil lamp for Shani and recite the supplied mantra 108 times.",
        "frequency": "Every Saturday for 11 consecutive Saturdays.",
        "dana": "Offer black sesame according to your means.",
        "astrological_reason": "D1 Saturn directly aspects House 4.",
    }
    context["normalized_evidence"]["remedy_blueprint"] = {
        "schema_version": "classical-property-remedy/v1",
        "selection_mode": "single_top",
        "top_recommendation": top,
        "ranked_remedies": [top],
    }
    packet = {
        "query_plan": {"category": "property", "home_subtype": "property_remedy", "answer_mode": "remedy_action"},
        "answer_spec": {}, "verdict": {}, "verification": {}, "user_derivation": {},
    }
    result = apply_live_graph_policy(
        packet,
        intent={"category": "property", "home_subtype": "property_remedy"},
        context=context,
    )
    rules = result["answer_spec"]["property_remedy_rules"]
    assert rules["required_count"] == 1
    assert rules["top_recommendation"]["planet"] == "Saturn"
    assert any("budgeting" in line for line in rules["forbidden_moves"])
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert "classical property remedy" in policy["instruction"]


def test_home_foundation_replaces_generic_remedy_with_property_calculation() -> None:
    lords = ("Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury")
    planets = {
        "Moon": {"house": 4, "dignity": "friendly_sign", "aspects_to_houses": [10]},
        "Sun": {"house": 9, "dignity": "friendly_sign", "aspects_to_houses": [3]},
        "Mercury": {"house": 8, "dignity": "friendly_sign", "aspects_to_houses": [2]},
        "Venus": {"house": 11, "dignity": "own_sign", "aspects_to_houses": [5]},
        "Mars": {"house": 2, "dignity": "enemy_sign", "aspects_to_houses": [5, 8, 9]},
        "Jupiter": {"house": 2, "dignity": "friendly_sign", "aspects_to_houses": [6, 8, 10]},
        "Saturn": {"house": 2, "dignity": "enemy_sign", "functional_nature": "functional_malefic", "aspects_to_houses": [4, 8, 11]},
        "Rahu": {"house": 2, "aspects_to_houses": [8]},
        "Ketu": {"house": 8, "aspects_to_houses": [2]},
    }
    chart = {
        "houses": [
            {"house": house, "lord": lords[house - 1], "occupants": [name for name, row in planets.items() if row["house"] == house]}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    foundation = build_home_foundation(
        chart_data={"charts": {"D1": chart, "D4": chart}},
        normalized_evidence={"remedy_blueprint": {"top_recommendation": {"action": "generic modern advice"}}},
        category="property",
        answer_mode="remedy_action",
        home_subtype="property_remedy",
    )
    blueprint = foundation["remedy_blueprint"]
    assert blueprint["schema_version"] == "classical-property-remedy/v1"
    assert blueprint["top_recommendation"]["planet"] == "Saturn"
    assert blueprint["top_recommendation"]["action"] != "generic modern advice"
    assert foundation["route_synthesis"]["top_recommendation"] == blueprint["top_recommendation"]
    assert foundation["availability"]["remedy_blueprint"] is True


def test_single_property_remedy_makes_only_its_calculated_graha_visible() -> None:
    contract = build_translated_astrology_contract(
        {
            "query_plan": {"category": "property", "home_subtype": "property_remedy", "answer_mode": "remedy_action"},
            "verdict": {"direction": "calculated_remedy"},
            "evidence": {
                "remedy_blueprint": {
                    "selection_mode": "single_top",
                    "top_recommendation": {
                        "planet": "Saturn",
                        "astrological_reason": "D1 Saturn directly aspects House 4.",
                    },
                    "candidate_planets": ["Saturn", "Mercury", "Mars"],
                },
                "primary_drivers": ["Mercury", "Mars"],
            },
            "answer_contract": {"knowledge_graph_policy": {"domain": "home_property"}},
        },
        question="Which calculated remedy is relevant?",
        language="english",
        response_style="technical",
    )
    assert contract["allowed_planets"] == ["Saturn"]
    assert contract["reason_anchors"][0]["source_fact"] == "D1 Saturn directly aspects House 4."


def test_property_remedy_skips_general_home_fact_marker_gate() -> None:
    marker_contract = {
        "validation_markers": ["[[HOME_D1_H4:LORD=Venus]]"],
    }
    context = {
        "intent_summary": {"category": "property", "home_subtype": "property_remedy"},
        "normalized_evidence": {"home_foundation": {"immutable_fact_contract": marker_contract}},
    }
    assert _resolve_home_fact_contract(context, None, None) == {}


def test_reference_chart_property_remedy_survives_graph_validation() -> None:
    birth = {
        "name": "Tarun", "date": "1980-04-02", "time": "14:55:00",
        "latitude": 29.2396596, "longitude": 75.8174505,
        "timezone": "UTC+5:30", "place": "Hisar, Haryana, India",
    }
    intent = {
        "category": "property", "home_subtype": "property_remedy",
        "answer_mode": "remedy_action", "explicit_remedy_request": True,
        "query_context": {"as_of": "2026-09-04T10:00:00+05:30"},
    }
    apply_home_routing_guards(intent)
    context = _build_instant_context(
        birth,
        "Which calculated remedy is relevant for repeated delays in buying a home?",
        intent,
        [],
        answer_mode_override="remedy_action",
        target_subject_override={"key": "self", "label": "self", "base_house": 1},
    )
    foundation = context["normalized_evidence"]["home_foundation"]
    blueprint = context["normalized_evidence"]["remedy_blueprint"]
    assert context["intent_summary"]["home_subtype"] == "property_remedy"
    assert foundation["availability"]["d1"] is True
    assert foundation["availability"]["d4"] is True
    assert foundation["availability"]["remedy_blueprint"] is True
    assert blueprint["schema_version"] == "classical-property-remedy/v1"

    packet = build_instant_v2_packet(
        question="Which calculated remedy is relevant for repeated delays in buying a home?",
        intent=intent,
        answer_mode="remedy_action",
        target_subject={"key": "self", "label": "self", "base_house": 1},
        language="english",
        instant_context=context,
    )
    result = apply_live_graph_policy(packet, intent=intent, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["evidence_status"] == "complete"
    assert policy["missing_required_factors"] == []
    assert policy["fallback_to_deeper_mode"] is False
    assert "home_timing_rules" not in result["answer_spec"]
    assert result["verdict"].get("missing_required_capabilities") in (None, [])


def test_planner_and_runtime_do_not_collapse_property_questions_to_wealth() -> None:
    plan = build_query_plan(
        question="Should I buy or rent?", language="english", answer_mode="comparison_choice",
        target_subject={"key": "self", "label": "self"},
        intent={"category": "property", "home_subtype": "property_comparison"},
    )
    assert plan["category"] == "property"
    assert plan["home_subtype"] == "property_comparison"
    assert home_graph_runtime_key("property", plan) == "property_comparison"


def test_inheritance_boundary_transfers_to_wealth_graph_not_partnership() -> None:
    intent = {
        "category": "property",
        "home_subtype": "inheritance_handoff",
        "answer_mode": "dedicated_partnership_flow",
        "route_action": "handoff",
        "divisional_charts": ["D1", "D4"],
    }
    apply_home_routing_guards(intent)
    assert intent["category"] == "inheritance"
    assert intent["home_subtype"] is None
    assert intent["answer_mode"] == "potential_capacity"
    assert intent["route_action"] == "answer"
    assert intent["divisional_charts"] == ["D1", "D2", "D8"]


def test_boundary_routes_never_emit_property_outcome_claims() -> None:
    for key, phrase in {
        "property_dispute_handoff": "Legal, Competition and Conflict",
        "muhurat_handoff": "Muhurat flow",
        "foreign_handoff": "Foreign Life",
        "inheritance_handoff": "Wealth and Inheritance",
    }.items():
        result = enforce_live_graph_answer(
            "A speculative answer", {"answer_spec": {"knowledge_graph_policy": {"runtime_key": key}}},
        )
        assert phrase in result


def test_incomplete_live_route_uses_the_shared_language_aware_deeper_mode_contract() -> None:
    policy = _live_contract("home_property", {
        "match": False, "runtime_key": "home_overview", "mode_match": True,
        "required_factors": ["home:D4"], "missing_required_factors": ["home:D4"],
    }, {})
    assert policy["fallback_to_deeper_mode"] is True
    assert "same language and script" in policy["instruction"]
    assert "Standard or Premium" in policy["instruction"]
    packet = {"answer_spec": {"knowledge_graph_policy": policy}}
    english = enforce_live_graph_answer("invented date", packet, language="english")
    hindi = enforce_live_graph_answer("मनगढ़ंत तारीख", packet, language="hindi")
    assert "Standard or Premium mode" in english
    assert "missing" not in english.lower()
    assert "Standard या Premium mode" in hindi
    assert "ग्राफ" not in hindi


def test_static_relocation_with_complete_d1_d4_evidence_stays_answerable_in_live_mode() -> None:
    intent = {
        "category": "property",
        "home_subtype": "relocation_home",
        "answer_mode": "potential_capacity",
        "route_action": "answer",
    }
    apply_home_routing_guards(intent)
    context = _context("relocation_home")
    packet = {
        "query_plan": dict(intent),
        "answer_spec": {},
        "verdict": {},
        "verification": {},
        "user_derivation": {},
    }

    result = apply_live_graph_policy(packet, intent=intent, context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]

    assert intent["answer_mode"] == "comparison_choice"
    assert policy["runtime_key"] == "relocation_home"
    assert policy["mode_match"] is True
    assert policy["missing_required_factors"] == []
    assert policy["evidence_status"] == "complete"
    assert policy["fallback_to_deeper_mode"] is False
    assert "Standard or Premium" not in enforce_live_graph_answer(
        "Your chart supports a domestic move with conditions.", result, language="english",
    )


def test_living_arrangement_exposes_multi_layer_evidence_and_never_collapses_to_h4_occupant() -> None:
    def chart(lords: dict[int, str]) -> dict:
        planets = {
            "Moon": {"house": 4, "sign": 6, "dignity": "neutral_sign", "aspects_to_houses": [10]},
            "Venus": {"house": 11, "sign": 1, "dignity": "own_sign", "aspects_to_houses": [5]},
            "Mars": {"house": 2, "sign": 4, "dignity": "enemy_sign", "aspects_to_houses": [4, 8, 9]},
            "Saturn": {"house": 2, "sign": 4, "dignity": "enemy_sign", "functional_nature": "functional_malefic", "aspects_to_houses": [4, 8, 11]},
            "Mercury": {"house": 8, "sign": 10, "dignity": "neutral_sign", "aspects_to_houses": [2]},
        }
        return {
            "houses": [{"house": house, "lord": lord, "occupants": []} for house, lord in lords.items()],
            "planets": planets,
        }

    d1 = chart({2: "Sun", 3: "Mercury", 4: "Venus", 11: "Venus", 12: "Mercury"})
    d1["planets"]["Sun"] = {"house": 9, "sign": 11, "dignity": "friendly_sign", "aspects_to_houses": [3]}
    d4 = chart({2: "Venus", 3: "Mercury", 4: "Moon", 11: "Saturn", 12: "Jupiter"})
    d4["planets"]["Jupiter"] = {"house": 1, "sign": 8, "dignity": "own_sign", "aspects_to_houses": [4, 5, 7]}
    natal = {"houses": [{
        "house": house,
        "lord": lord,
        "occupants": ["Moon"] if house == 4 else [],
        "aspecting_planets": ["Saturn"] if house == 4 else [],
        "tone": "mixed",
        "factors": [{
            "source": "lord_dignity",
            "planet": lord,
            "polarity": "supportive",
            "weight": 1.25,
            "facts": {"dignity": "own_sign"},
        }],
    } for house, lord in {2: "Sun", 3: "Mercury", 4: "Venus", 11: "Venus", 12: "Mercury"}.items()]}
    result = build_home_foundation(
        chart_data={"charts": {"D1": d1, "D4": d4}},
        normalized_evidence={},
        category="property",
        answer_mode="comparison_choice",
        home_subtype="living_arrangement",
        natal_topic_factors=natal,
    )
    assert result["availability"]["d4"] is True
    assert len(result["focus_house_evidence"]) == 5
    assert result["fourth_house_evidence"]["d1_lord_condition"]["lord"] == "Venus"
    assert result["fourth_house_evidence"]["d4_lord_condition"]["lord"] == "Moon"
    assert result["fourth_house_evidence"]["material_natal_factors"][0]["facts"]["dignity"] == "own_sign"
    synthesis = result["living_arrangement_synthesis"]
    assert synthesis["evidence_complete"] is True
    assert {row["house"] for row in synthesis["family_living"]["evidence_ledger"]} == {2, 4, 11}
    assert {row["house"] for row in synthesis["independent_living"]["evidence_ledger"]} == {3, 4, 12}


def test_every_non_boundary_route_has_a_dedicated_calculated_synthesis() -> None:
    planets = {
        name: {
            "house": (index % 12) + 1,
            "sign": index % 12,
            "dignity": "own_sign" if name in {"Moon", "Venus"} else "friendly_sign",
            "functional_nature": "functional_benefic",
            "aspects_to_houses": [4, 11],
        }
        for index, name in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"))
    }
    lords = ("Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury")
    chart = {
        "houses": [{"house": house, "lord": lords[house - 1], "occupants": []} for house in range(1, 13)],
        "planets": planets,
    }
    natal = {"houses": [{
        "house": house, "lord": lords[house - 1], "tone": "supportive",
        "factors": [{"source": "lord_dignity", "planet": lords[house - 1], "polarity": "supportive", "weight": 1.0, "facts": {"dignity": "friendly_sign"}}],
    } for house in range(1, 13)]}
    scan_row = {
        "start": "2027-01-01", "end": "2027-06-30", "relevance_score": 80,
        "activated_focus_houses": list(range(1, 13)), "transit_trigger_score": 6,
        "peak_activation_windows": [{"start": "2027-03-01", "end": "2027-03-10", "activated_focus_houses": list(range(1, 13)), "trigger_score": 6}],
    }
    normalized = {
        "forward_event_dasha_scan": {"periods": [scan_row]},
        "historical_event_dasha_scan": {"periods": [scan_row]},
        "remedy_blueprint": {"top_recommendation": {"action": "calculated action"}},
    }
    kp = {
        "cusp_lords": {house: {"sub_lord": "Venus"} for house in range(1, 13)},
        "planet_significators": {"Venus": list(range(1, 13))},
    }
    for key in set(HOME_PROFILES) - set(BOUNDARY_HOME_SUBTYPES):
        result = build_home_foundation(
            chart_data={"charts": {"D1": chart, "D4": chart}}, normalized_evidence=normalized,
            category="property", answer_mode="event_prediction" if key in TIMING_HOME_SUBTYPES else "topic_reading",
            home_subtype=key, kp_evidence=kp, natal_topic_factors=natal,
        )
        assert result["route_synthesis"], key
        assert result["availability"]["d1"] is True, key
        assert result["availability"]["d4"] is True, key
        if key in TIMING_HOME_SUBTYPES:
            assert result["timing_synthesis"]["timing_window_count"] >= 1, key
            assert result["timing_synthesis"]["dasha_activation_established"] is True, key
            assert result["timing_synthesis"]["transit_confirmation_established"] is True, key


def test_home_fact_contract_keeps_lord_occupant_and_aspector_roles_distinct() -> None:
    lords = ("Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury")
    d1_planets = {
        "Moon": {"house": 4, "sign": 6, "dignity": "friendly_sign", "aspects_to_houses": [10]},
        "Venus": {"house": 11, "sign": 1, "dignity": "own_sign", "aspects_to_houses": [5]},
        "Saturn": {"house": 2, "sign": 4, "dignity": "enemy_sign", "aspects_to_houses": [4, 8, 11]},
        "Mars": {"house": 2, "sign": 4, "dignity": "enemy_sign", "aspects_to_houses": [5, 8, 9]},
        "Sun": {"house": 9, "sign": 11, "dignity": "friendly_sign", "aspects_to_houses": [3]},
        "Mercury": {"house": 8, "sign": 10, "dignity": "friendly_sign", "aspects_to_houses": [2]},
        "Jupiter": {"house": 2, "sign": 4, "dignity": "friendly_sign", "aspects_to_houses": [6, 8, 10]},
        "Rahu": {"house": 2, "sign": 4, "aspects_to_houses": [8]},
        "Ketu": {"house": 8, "sign": 10, "aspects_to_houses": [2]},
    }
    d4_planets = {
        **d1_planets,
        "Moon": {"house": 10, "sign": 9, "dignity": "friendly_sign", "aspects_to_houses": [4]},
    }
    d4_lords = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
    chart = lambda planets, chart_lords: {
        "houses": [
            {"house": house, "lord": chart_lords[house - 1], "occupants": [name for name, row in planets.items() if row.get("house") == house]}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    result = build_home_foundation(
        chart_data={"charts": {"D1": chart(d1_planets, lords), "D4": chart(d4_planets, d4_lords)}},
        normalized_evidence={},
        category="property",
        answer_mode="topic_reading",
        home_subtype="home_life",
    )
    facts = result["immutable_fact_contract"]
    assert facts["d1_ascendant_lord"] == "Moon"
    assert facts["d1_fourth_house"]["lord"] == "Venus"
    assert facts["d1_fourth_house"]["lord_house"] == 11
    assert facts["d1_fourth_house"]["occupants"] == ["Moon"]
    assert facts["d1_fourth_house"]["house_aspectors"] == ["Saturn"]
    assert facts["d4_fourth_house"]["lord"] == "Moon"
    assert facts["d4_fourth_house"]["lord_house"] == 10

    compact = _fit_composer_brief({
        "evidence": {"home_foundation": result},
        "query_plan": {"category": "property", "home_subtype": "home_life"},
        "verdict": {"direction": "supported_with_conditions"},
        "answer_contract": {},
    }, target_chars=100)
    compact_facts = compact["evidence"]["home_foundation"]["immutable_fact_contract"]
    assert compact_facts["d1_fourth_house"]["lord"] == "Venus"
    assert compact_facts["d1_fourth_house"]["occupants"] == ["Moon"]
    assert compact_facts["d1_fourth_house"]["house_aspectors"] == ["Saturn"]
    assert compact_facts["d4_fourth_house"]["lord"] == "Moon"
    assert compact_facts["validation_markers"] == facts["validation_markers"]

    wrong_answer = "The Moon is the fourth lord, strengthened by Venus and Mars."
    assert len(_validate_home_fact_markers(wrong_answer, facts)) == 2
    marked_answer = "Correct D1 fact. " + " Correct D4 fact. ".join(facts["validation_markers"])
    assert _validate_home_fact_markers(marked_answer, facts) == []
    leaked_heading = marked_answer + "\n\nRoute synthesis: timing works."
    assert "internal implementation heading" in _validate_home_fact_markers(leaked_heading, facts)[0]
    assert "[[HOME_" not in _strip_home_fact_markers(marked_answer)

    prompt = _build_instant_composer_prompt_v3(
        "What does my chart show about my home life?",
        {
            "context_profile": "instant_composer_v3",
            "query_plan": {"category": "property", "home_subtype": "home_overview", "answer_mode": "topic_reading"},
            "verdict": {"direction": "synthesize_from_calculated_home_foundation"},
            "evidence": {"home_foundation": result},
            "answer_contract": {
                "knowledge_graph_policy": {"live": True, "domain": "home_property"},
                "visible_astrology": {"required": False, "technical_detail_allowed": False},
                "home_answer_rules": {},
            },
        },
        "english",
    )
    assert "`occupants` only occupy House 4" in prompt
    assert "`house_aspectors` is the complete allowed list" in prompt
    assert facts["validation_markers"][0] in prompt


def test_timing_graph_rejects_generic_dasha_and_transit_presence_without_route_window() -> None:
    key = "property_purchase_timing"
    context = _context(key, timing=True)
    context["normalized_evidence"]["home_foundation"]["timing_synthesis"] = {
        "dasha_activation_established": False,
        "transit_confirmation_established": False,
        "dasha_evaluation_complete": False,
        "transit_evaluation_complete": False,
        "kp_fructification": {"complete": True},
        "timing_windows": [],
    }
    result = compare_home_graph_policy(
        category="property", query_plan={"home_subtype": key, "answer_mode": "event_prediction"},
        observed_answer_mode="event_prediction", context=context,
    )
    assert result and result["match"] is False
    assert "home:DashaActivation" in result["missing_required_factors"]
    assert "home:TransitConfirmation" in result["missing_required_factors"]


def test_completed_timing_scan_with_no_qualifying_window_is_not_missing_evidence() -> None:
    lords = ("Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury")
    planets = {
        name: {
            "house": (index % 12) + 1,
            "sign": index % 12,
            "dignity": "friendly_sign",
            "functional_nature": "functional_benefic",
            "aspects_to_houses": [],
        }
        for index, name in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"))
    }
    chart = {
        "houses": [
            {"house": house, "lord": lords[house - 1], "occupants": [name for name, row in planets.items() if row["house"] == house]}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    normalized = {
        "forward_event_dasha_scan": {
            "horizon_start": "2026-09-03",
            "horizon_end": "2029-09-03",
            "dasha_evaluation_complete": True,
            "transit_evaluation_complete": True,
            "evaluated_dasha_period_count": 9,
            "qualifying_period_count": 0,
            "periods": [],
        }
    }
    kp = {
        "cusp_lords": {4: {"sub_lord": "Venus"}, 11: {"sub_lord": "Venus"}},
        "planet_significators": {"Venus": [2, 4, 9, 11]},
    }
    foundation = build_home_foundation(
        chart_data={"charts": {"D1": chart, "D4": chart}},
        normalized_evidence=normalized,
        category="property",
        answer_mode="event_prediction",
        home_subtype="property_purchase_timing",
        kp_evidence=kp,
    )
    timing = foundation["timing_synthesis"]
    assert timing["verdict"] == "no_triangulated_window_in_horizon"
    assert timing["dasha_evaluation_complete"] is True
    assert timing["transit_evaluation_complete"] is True
    assert foundation["availability"]["dasha_activation"] is True
    assert foundation["availability"]["transit_confirmation"] is True

    comparison = compare_home_graph_policy(
        category="property",
        query_plan={"home_subtype": "property_purchase_timing", "answer_mode": "event_prediction"},
        observed_answer_mode="event_prediction",
        context={"normalized_evidence": {"home_foundation": foundation}},
    )
    assert comparison and comparison["match"] is True


def test_property_timing_promotes_kp_dasha_and_transit_into_answer_contract() -> None:
    context = _context("property_purchase_timing", timing=True)
    timing = context["normalized_evidence"]["home_foundation"]["timing_synthesis"]
    timing.update({
        "requested_window_assessment": {
            "kind": "current",
            "start": "2026-09-03",
            "end": "2026-09-03",
            "supportive_now": True,
            "verdict": "supportive_requested_period",
        },
        "kp_fructification": {
            "complete": True,
            "verdict": "supported",
            "cusp_judgments": [{"cusp": 4, "sub_lord": "Venus", "success_house_links": [4, 11]}],
        },
        "timing_windows": [{
            "start": "2026-08-01",
            "end": "2026-11-01",
            "mahadasha": "Saturn",
            "antardasha": "Rahu",
            "pratyantardasha": "Saturn",
            "activated_focus_houses": [4, 11],
            "dasha_activation": {"activated_houses": [4, 11]},
            "transit_confirmation": [{
                "start": "2026-09-01", "end": "2026-09-08", "planet": "Saturn",
                "activated_focus_houses": [4, 11],
            }],
            "transit_confirmed": True,
        }],
    })
    timing["now_vs_wait_synthesis"] = {
        "decision": "buying_in_requested_period_is_supported",
        "required_visible_conclusion": "The requested period is astrologically supportive for a purchase.",
    }
    timing["next_window"] = timing["timing_windows"][0]
    timing["strongest_window"] = timing["timing_windows"][0]
    packet = {
        "query_plan": {
            "category": "property",
            "home_subtype": "property_purchase_timing",
            "answer_mode": "event_prediction",
        },
        "answer_spec": {},
        "verdict": {},
        "verification": {},
        "user_derivation": {},
    }
    result = apply_live_graph_policy(
        packet,
        intent={"category": "property", "home_subtype": "property_purchase_timing"},
        context=context,
    )
    rules = result["answer_spec"]["home_timing_rules"]
    assert rules["requested_window_assessment"]["supportive_now"] is True
    assert rules["now_vs_wait_synthesis"]["decision"] == "buying_in_requested_period_is_supported"
    assert rules["kp_fructification"]["cusp_judgments"][0]["sub_lord"] == "Venus"
    assert rules["allowed_timing_windows"][0]["dasha_activation"]["activated_houses"] == [4, 11]
    assert rules["allowed_timing_windows"][0]["transit_confirmation"][0]["planet"] == "Saturn"
    assert rules["human_bridge_rules"]["required"] is True
    assert any(
        "timing mismatch versus permanent denial" in item
        for item in rules["human_bridge_rules"]["allowed_distinctions"]
    )
    assert any("emotionally relevant question" in item for item in rules["required_answer_order"])
    assert result["answer_spec"]["event_rules"]["allowed_timing_windows"]
    assert result["verdict"]["direction"] == "supportive_requested_period"

    prompt = _build_instant_composer_prompt_v3(
        "Is this a good period to buy a house?",
        {
            "context_profile": "instant_composer_v3",
            "query_plan": packet["query_plan"],
            "verdict": result["verdict"],
            "evidence": context["normalized_evidence"],
            "answer_contract": result["answer_spec"],
        },
        "english",
    )
    assert "LIVE TIMING EVIDENCE CHECK" in prompt
    assert 'Forbidden visible labels include "Route synthesis"' in prompt
    assert "A present-period yes is allowed only" in prompt
    assert "now-versus-wait" in prompt
    assert 'Do not call it the "career sphere"' in prompt


def test_shared_instant_voice_requires_grounded_human_bridge_not_engagement_bait() -> None:
    contract = _instant_relational_voice_contract()
    assert "HUMAN BRIDGE" in contract
    assert "timing mismatch rather than personal failure or permanent denial" in contract
    assert "what is creating the urgency" in contract
    assert "never force reassurance" in contract
    assert "Never encourage dependency" in contract


def test_every_home_timing_route_uses_its_own_event_language() -> None:
    expected = {
        "property_purchase_timing": ("buying_in_requested_period_is_supported", "buying property", "purchase window"),
        "property_sale_timing": ("selling_in_requested_period_is_supported", "selling the property", "sale window"),
        "possession_documentation_timing": ("possession_documentation_in_requested_period_is_supported", "possession or property documentation", "completion window"),
        "construction_timing": ("construction_in_requested_period_is_supported", "construction or renovation", "execution window"),
        "relocation_timing": ("relocation_in_requested_period_is_supported", "domestic move", "moving window"),
        "vehicle_timing": ("vehicle_purchase_in_requested_period_is_supported", "purchasing a vehicle", "vehicle window"),
    }
    for subtype, (decision, supported_phrase, wait_phrase) in expected.items():
        supported = _home_timing_decision(
            subtype,
            requested_period_supportive=True,
            next_window={"start": "2026-09-19", "end": "2027-02-12"},
        )
        waiting = _home_timing_decision(
            subtype,
            requested_period_supportive=False,
            next_window={"start": "2026-09-19", "end": "2027-02-12"},
        )
        assert supported["decision"] == decision
        assert supported_phrase in supported["required_visible_conclusion"]
        assert wait_phrase in waiting["required_visible_conclusion"]

    sale = _home_timing_decision(
        "property_sale_timing",
        requested_period_supportive=False,
        next_window={"start": "2026-09-19", "end": "2027-02-12"},
    )
    assert "ownership" not in sale["required_visible_conclusion"].lower()
    assert "buy" not in sale["required_visible_conclusion"].lower()


def test_open_ended_vehicle_when_question_leads_with_next_window_not_requested_period() -> None:
    assert _looks_like_open_ended_life_event_when(
        "When will I buy a vehicle?", {"mode": "LIFESPAN_EVENT_TIMING"},
    ) is True
    result = _home_timing_decision(
        "vehicle_timing",
        requested_period_supportive=True,
        next_window={"start": "2026-09-04", "end": "2026-09-18"},
        next_event_request=True,
    )
    assert result["question_scope"] == "next_event_window"
    assert result["decision"] == "next_supported_window_identified"
    assert result["required_visible_conclusion"] == (
        "The next fully supported vehicle purchase window is from 2026-09-04 to 2026-09-18."
    )
    assert "requested period" not in result["required_visible_conclusion"].lower()

    qualified = _home_timing_decision(
        "vehicle_timing",
        requested_period_supportive=True,
        next_window={"start": "2026-09-04", "end": "2026-09-18"},
        next_event_request=True,
        fructification_status="qualified",
    )
    assert qualified["decision"] == "conditional_window_only"
    assert qualified["next_supported_window_available"] is False
    assert "No fully supported vehicle purchase window" in qualified["required_visible_conclusion"]
    assert "conditional" in qualified["required_visible_conclusion"]


def test_vehicle_colour_selection_is_static_and_uses_ranked_d1_d16_carriers() -> None:
    d1 = {"planets": {"Venus": {"dignity": "own_sign"}, "Moon": {"dignity": "friendly_sign"}}}
    d16 = {"planets": {"Venus": {"dignity": "own_sign"}, "Moon": {"dignity": "friendly_sign"}}}
    d1_h4 = {
        "available": True, "lord": "Moon", "occupants": ["Venus"],
        "house_aspects": [],
    }
    d16_h4 = {
        "available": True, "lord": "Venus", "occupants": [],
        "house_aspects": [],
    }
    synthesis = _vehicle_color_synthesis(d1, d16, d1_h4, d16_h4)
    assert synthesis["verdict"] == "ranked_palette"
    assert synthesis["recommended_colors"][0]["color"] in {"white", "silver"}
    assert "timing" not in synthesis["required_visible_conclusion"].lower()

    context = _context("vehicle_selection")
    packet = {
        "query_plan": {"category": "vehicles", "home_subtype": "vehicle_selection", "answer_mode": "comparison_choice"},
        "answer_spec": {}, "verdict": {}, "verification": {}, "user_derivation": {},
    }
    result = apply_live_graph_policy(packet, intent=packet["query_plan"], context=context)
    policy = result["answer_spec"]["knowledge_graph_policy"]
    assert policy["runtime_key"] == "vehicle_selection"
    assert policy["fallback_to_deeper_mode"] is False
    assert "home_timing_rules" not in result["answer_spec"]


def test_retrospective_property_timing_is_not_presented_as_now_versus_wait() -> None:
    result = _home_timing_decision(
        "retrospective_property_timing",
        requested_period_supportive=False,
        next_window={"start": "2004-01-01", "end": "2005-06-01"},
    )
    assert result["decision"] == "probable_historical_periods_identified"
    assert "verify" in result["required_visible_conclusion"]
    assert "wait" not in result["required_visible_conclusion"].lower()


def test_property_capacity_and_joint_purchase_expose_direct_user_decisions() -> None:
    lords = ("Moon", "Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter", "Mars", "Venus", "Mercury")
    planets = {
        "Sun": {"house": 9, "sign": 11, "dignity": "friend_sign", "aspects_to_houses": [3]},
        "Moon": {"house": 4, "sign": 6, "dignity": "neutral_sign", "aspects_to_houses": [10]},
        "Mars": {"house": 2, "sign": 4, "dignity": "neutral_sign", "aspects_to_houses": [5, 8, 9]},
        "Mercury": {"house": 8, "sign": 10, "dignity": "neutral_sign", "aspects_to_houses": [2]},
        "Jupiter": {"house": 2, "sign": 4, "dignity": "friend_sign", "aspects_to_houses": [6, 8, 10]},
        "Venus": {"house": 11, "sign": 1, "dignity": "own_sign", "aspects_to_houses": [5]},
        "Saturn": {"house": 2, "sign": 4, "dignity": "enemy_sign", "aspects_to_houses": [4, 8, 11]},
        "Rahu": {"house": 2, "sign": 4, "dignity": "neutral_sign", "aspects_to_houses": [8]},
        "Ketu": {"house": 8, "sign": 10, "dignity": "neutral_sign", "aspects_to_houses": [2]},
    }
    chart = {
        "houses": [
            {"house": house, "lord": lords[house - 1], "occupants": [name for name, row in planets.items() if row["house"] == house]}
            for house in range(1, 13)
        ],
        "planets": planets,
    }
    chart_data = {"charts": {"D1": chart, "D4": chart}}
    capacity = build_home_foundation(
        chart_data=chart_data, normalized_evidence={}, category="property",
        answer_mode="potential_capacity", home_subtype="property_potential",
    )
    assert capacity["ownership_capacity_synthesis"]["evidence_complete"] is True
    assert "capacity" in capacity["ownership_capacity_synthesis"]["timing_boundary"]

    joint = build_home_foundation(
        chart_data=chart_data, normalized_evidence={}, category="property",
        answer_mode="comparison_choice", home_subtype="joint_property",
    )
    assessment = joint["comparison_synthesis"]["asked_option_assessment"]
    assert assessment["option"] == "joint_ownership"
    assert assessment["evidence_complete"] is True
    assert assessment["required_visible_conclusion"]
    assert "native's co-ownership pattern" in assessment["scope_boundary"]


def test_home_fact_markers_are_attached_before_metadata_and_never_shown() -> None:
    contract = {
        "validation_markers": [
            "[[HOME_D1_H4:LORD=Venus;LORD_HOUSE=11;OCCUPANTS=Moon;ASPECTORS=Saturn]]",
            "[[HOME_D4_H4:LORD=Moon;LORD_HOUSE=10;OCCUPANTS=none;ASPECTORS=Saturn]]",
        ]
    }
    answer = (
        "The calculated property foundation is supportive.\n"
        'NEXT_ACTION_META: {"type":"none","follow_up_questions":[]}'
    )
    bound = _attach_missing_home_fact_markers(answer, contract)
    assert bound.index("[[HOME_D1_H4:") < bound.index("NEXT_ACTION_META:")
    assert _validate_home_fact_markers(bound, contract) == []
    assert "[[HOME_" not in _strip_home_fact_markers(bound)
    assert _strip_home_fact_markers("This is s…upportive.") == "This is supportive."


def test_home_visible_planet_contract_accepts_every_immutable_role_and_timing_carrier() -> None:
    aligned = _align_home_visible_astrology_contract(
        {"allowed_planets": ["Jupiter"], "maximum_planet_reasons": 2, "technical_detail_allowed": False},
        {
            "d1_fourth_house": {"lord": "Mercury", "occupants": ["Jupiter"], "house_aspectors": ["Sun", "Mars"]},
            "d4_fourth_house": {"lord": "Jupiter", "occupants": [], "house_aspectors": ["Saturn"]},
            "timing_answer_evidence_contract": {
                "kp_fructification": {"cusp_judgments": [{"sub_lord": "Venus"}]},
                "dasha_activation": {"mahadasha": "Saturn", "antardasha": "Venus", "pratyantardasha": "Venus"},
                "transit_confirmation": [{"planet": "Venus"}],
            },
        },
    )
    assert aligned["allowed_planets"] == ["Jupiter", "Mercury", "Sun", "Mars", "Saturn", "Venus"]
    assert aligned["maximum_planet_reasons"] == 6


def test_dasha_scanner_records_every_relevant_planetary_aspect() -> None:
    scan = _build_forward_event_dasha_scan(
        birth_data={},
        now_local=datetime(2026, 9, 3),
        house_lordships={"Saturn": [7, 8], "Rahu": []},
        focus_houses=[2, 4, 9, 11],
        category="property",
        chart_data={"planets": {"Saturn": {"house": 2}, "Rahu": {"house": 2}}},
        current_dashas={
            "mahadasha": {"planet": "Saturn"},
            "antardasha": {"planet": "Rahu"},
            "pratyantardasha": {"planet": "Saturn"},
        },
        raw_periods=[{
            "start_date": "2026-08-01",
            "end_date": "2026-11-01",
            "mahadasha": "Saturn",
            "antardasha": "Rahu",
            "pratyantardasha": "Saturn",
        }],
    )
    # Saturn in H2 has its 3rd and 10th aspects on H4 and H11. The scanner
    # must retain both; stopping after H4 breaks property triangulation.
    assert scan["periods"][0]["activated_focus_houses"] == [2, 4, 11]


def test_technical_visible_astrology_uses_controlling_home_and_timing_planets() -> None:
    context = {
        "query_plan": {"category": "property", "answer_mode": "timing_window"},
        "verdict": {"direction": "supportive_requested_period"},
        "answer_contract": {"knowledge_graph_policy": {"domain": "home_property"}},
        "evidence": {"home_foundation": {
            "immutable_fact_contract": {
                "d1_fourth_house": {"lord": "Venus", "house_aspectors": ["Saturn"]},
                "d4_fourth_house": {"lord": "Moon", "house_aspectors": ["Jupiter", "Saturn"]},
            },
            "timing_synthesis": {"answer_evidence_contract": {
                "dasha_activation": {"mahadasha": "Saturn", "antardasha": "Rahu"},
                "transit_confirmation": [{"planet": "Jupiter", "activated_focus_houses": [4, 11]}],
            }},
            "route_synthesis": {"evidence_ledger": [{"lord": "Sun", "tone": "challenging"}]},
        }},
    }
    contract = build_translated_astrology_contract(
        context,
        question="Is this a good period to buy a house?",
        language="english",
        response_style="technical",
    )
    assert {"Venus", "Saturn", "Rahu", "Jupiter"}.issubset(set(contract["allowed_planets"]))
    assert contract["maximum_planet_reasons"] > 2
