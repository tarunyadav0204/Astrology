from ai.intent_router import apply_career_routing_guards
from instant_chat_v2.answer_spec import build_answer_spec
from instant_chat_v2.career import (
    CAREER_PROFILES,
    CAREER_TARGET_TRAITS,
    _tenth_lord_combination_signature,
    answer_contract,
    build_career_target_assessment,
    build_vocation_synthesis,
    career_profile,
    classify_manifestations,
    classify_career_decision,
    normalize_career_houses,
    is_career_decision,
    is_career_relationship,
    is_static_career_profile,
    career_question_family,
)
from instant_chat_v2.user_derivation import build_user_derivation
from instant_chat_v2.planner import build_query_plan
from chat.instant_chat_pipeline import (
    _build_event_timing_verdict,
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _compact_career_foundation,
    _instant_compact_profession_evidence,
    _requested_charts_from_intent,
)


def test_profession_evidence_passes_birth_record_to_time_dependent_calculator(monkeypatch):
    captured = {}

    class FakeProfessionCalculator:
        def __init__(self, chart_data, birth_data=None):
            captured["chart_data"] = chart_data
            captured["birth_data"] = birth_data

        def calculate_professional_analysis(self):
            return {}

    monkeypatch.setattr(
        "calculators.profession_calculator.ProfessionCalculator",
        FakeProfessionCalculator,
    )
    chart_data = {"planets": {"Sun": {"house": 10}}}
    birth_data = {"date": "1980-04-02", "time": "14:55:00"}

    _instant_compact_profession_evidence(chart_data, birth_data)

    assert captured == {"chart_data": chart_data, "birth_data": birth_data}


def test_every_career_subtype_has_d1_and_d10_and_distinct_business_matrix():
    for profile in CAREER_PROFILES.values():
        assert "D1" in profile["divisionals"]
        assert "D10" in profile["divisionals"]
    assert 7 in CAREER_PROFILES["business"]["houses"]
    assert 6 in CAREER_PROFILES["employment"]["houses"]
    assert "Karkamsa" in CAREER_PROFILES["career_fit"]["divisionals"]


def test_career_fit_chart_selection_uses_normalized_subtype():
    assert _requested_charts_from_intent(
        {"category": "career", "career_subtype": "career_fit"},
        answer_mode="timing_window",
    ) == ["D1", "D10", "KARAKAMSHA"]


def test_overall_career_topic_always_requests_jaimini_vocation_chart():
    assert _requested_charts_from_intent(
        {
            "category": "career",
            "career_subtype": "general",
            "chart_focus": {"requested": ["D1", "D10"]},
        },
        answer_mode="topic_reading",
    ) == ["D1", "D10", "KARAKAMSHA"]


def test_job_decision_is_not_treated_as_static_vocation_profile():
    assert is_career_decision("career", "resignation")
    assert not is_static_career_profile(
        "career", "resignation", answer_mode="topic_reading"
    )
    assert is_static_career_profile(
        "career", "general", answer_mode="topic_reading"
    )


def test_job_decision_requests_d1_and_d10_without_karakamsha():
    assert _requested_charts_from_intent(
        {"category": "career", "career_subtype": "resignation"},
        answer_mode="topic_reading",
    ) == ["D1", "D10"]


def test_job_decision_adjudicates_stay_change_separation_and_landing_separately():
    assert classify_career_decision([2, 6, 10, 11])["verdict"] == "stay_for_now"
    assert classify_career_decision([3, 10, 12])["verdict"] == "prepare_do_not_resign"
    assert classify_career_decision([2, 3, 6, 10, 11, 12])["verdict"] == "planned_transition_supported"
    assert classify_career_decision([8, 10, 12])["verdict"] == "instability_not_exit_permission"


def test_job_decision_accepts_readable_object_shaped_house_activations():
    houses = [
        {"house": 2, "meaning": "income"},
        {"house": 3, "meaning": "change initiative"},
        {"house": 6, "meaning": "employment"},
        {"house": 10, "meaning": "career"},
        {"house": 11, "meaning": "gains"},
        {"house": 12, "meaning": "separation"},
    ]
    assert normalize_career_houses(houses) == [2, 3, 6, 10, 11, 12]
    result = classify_career_decision(houses)
    assert result["active_houses"] == [2, 3, 6, 10, 11, 12]
    assert result["verdict"] == "planned_transition_supported"


def test_structured_router_subtype_gets_canonical_houses_and_divisionals():
    result = {"category": "career", "career_subtype": "business"}
    apply_career_routing_guards(result)
    assert result["category"] == "business"
    assert result["focus_houses"] == [7, 10, 11, 2]
    assert result["required_divisional_charts"] == ["D1", "D10"]


def test_named_career_target_keeps_vocation_chart_for_any_business_field():
    result = {
        "category": "career",
        "career_subtype": "business",
        "career_target": "software consulting",
        "career_target_structure": "business",
        "career_target_traits": ["technical_systems", "client_service"],
    }

    apply_career_routing_guards(result)

    assert result["career_target"] == "software consulting"
    assert result["career_subtype"] == "business"
    assert result["required_divisional_charts"] == ["D1", "D10", "Karkamsa"]


def test_query_plan_preserves_named_target_and_semantic_traits():
    plan = build_query_plan(
        question="Can I build a software consulting business?",
        intent={
            "category": "career",
            "career_subtype": "business",
            "career_target": "software consulting",
            "career_target_structure": "business",
            "career_target_traits": ["technical_systems", "client_service"],
        },
        answer_mode="potential_capacity",
        target_subject={"key": "self", "label": "self"},
        language="english",
    )

    assert plan["career_target"] == "software consulting"
    assert plan["career_target_structure"] == "business"
    assert plan["career_target_traits"] == ["technical_systems", "client_service"]


def test_named_target_contract_separates_field_fit_from_operating_structure():
    contract = answer_contract("potential_capacity", "business", "software consulting")

    assert contract["question_family"] == "target_fit"
    assert "separate field-fit verdict" in contract["required_shape"]
    assert "separate business/job/freelance fit verdict" in contract["required_shape"]
    assert "career_target_assessment" in contract["required_evidence"]
    assert "optional relevant follow-up" in contract["required_shape"]


def test_target_assessment_is_generic_and_trait_driven_not_astrology_specific():
    synthesis = {
        "ranked_planets": [
            {"planet": "Mercury", "score": 10, "reasons": ["Mercury repeats in D1 and D10"]},
            {"planet": "Saturn", "score": 8, "reasons": ["Saturn supports systems in D10"]},
            {"planet": "Jupiter", "score": 7, "reasons": ["Jupiter supports advice in D1"]},
            {"planet": "Venus", "score": 4, "reasons": ["Venus supports client rapport"]},
        ],
        "work_structure": {
            "business_score": 8,
            "employment_score": 6,
            "inclination": "business_or_hybrid",
            "reasons": ["Client and gains houses repeat across D1 and D10"],
        },
    }

    assessment = build_career_target_assessment(
        synthesis,
        target="software consulting",
        target_traits=["technical_systems", "analytical_research", "client_service"],
        target_structure="business",
    )

    assert assessment["target"] == "software consulting"
    assert assessment["target_traits"] == [
        "technical_systems", "analytical_research", "client_service"
    ]
    assert assessment["field_fit"]["verdict"] == "field_fit_supported"
    assert assessment["business_fit"]["verdict"] == "business_or_client_led_supported"
    assert set(assessment["target_traits"]).issubset(CAREER_TARGET_TRAITS)


def test_manifestations_do_not_upgrade_single_house_activity_to_offer_or_joining():
    single = classify_manifestations([10])
    assert [row["code"] for row in single] == ["role_visibility"]
    assert all(row["stage"] == "activation" for row in single)

    delivery = classify_manifestations([2, 3, 6, 10, 11])
    codes = {row["code"] for row in delivery}
    assert {"compensation_progress", "role_change_execution", "employment_joining"} <= codes
    assert all("does not guarantee" in row["certainty_rule"] for row in delivery)


def test_answer_contract_prevents_career_to_wealth_drift_and_requires_real_remedies():
    contract = answer_contract("remedy_action", "salary")
    assert "role, work and professional outcome first" in contract["career_not_wealth_rule"]
    assert "exactly three" in contract["remedy_rule"]
    assert "action, frequency" in contract["remedy_rule"]


def test_answer_spec_uses_structured_career_stages_not_legacy_generic_shortcut():
    query_plan = {
        "category": "career",
        "career_subtype": "employment",
        "answer_mode": "event_prediction",
        "time_scope": {"horizon_end": "2027-12-31"},
    }
    verdict = {"ranked_windows": [{"start": "2027-01-01", "end": "2027-02-01"}]}
    ledger = {"records": [{
        "evidence_id": "career-window",
        "kind": "event_timing_verdict",
        "value": {"material_future_progression": [{
            "start": "2027-01-01",
            "end": "2027-02-01",
            "chain": "Saturn-Rahu-Mercury",
            "activated_focus_houses": [2, 3, 6, 10, 11],
        }]},
    }]}
    spec = build_answer_spec(query_plan, verdict, ledger)
    manifestations = spec["event_rules"]["career_manifestations"]
    codes = {row["code"] for row in manifestations}
    assert "employment_joining" in codes
    assert "compensation_progress" in codes
    assert "more calls, effort, interviews, visibility" not in str(spec)
    assert spec["career_rules"]["required_foundation"] == {
        "D1": "Professional promise, work capacity, income linkage and natal obstacles.",
        "D10": "How profession, role, authority, execution and recognition express in practice.",
    }


def test_readable_derivation_carries_d1_d10_and_delivery_stages():
    context = {
        "intent_summary": {"focus_houses": [2, 6, 10, 11], "career_subtype": "employment"},
        "instant_parashari": {
            "focus_houses": [2, 6, 10, 11],
            "divisional_support": {"topic": {"support": "supportive", "charts": {"D10": {"rows": [
                {"h": 10, "lord": "Mercury", "lord_h": 10, "occ": ["Mercury"], "band": "supportive"}
            ]}}}},
            "forward_periods": [{
                "start": "2027-01-01", "end": "2027-02-01",
                "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Mercury",
                "activated_focus_houses": [2, 3, 6, 10, 11],
            }],
        },
        "_user_evidence": {"natal_topic_factors": {"source": "validated_d1_natal_promise", "houses": [{
            "house": 10, "lord": "Mars", "lord_placement_house": 2,
            "occupants": [], "aspecting_planets": ["Jupiter"], "tone": "supportive",
        }]}},
        "normalized_evidence": {"natal_promise": {"status": "supported", "topic_support": "supportive"}},
    }
    result = build_user_derivation(
        query_plan={"category": "career", "answer_mode": "event_prediction"},
        verdict={"direction": "supported", "confidence": 0.8},
        instant_context=context,
    )
    reading = result["career_reading"]
    assert reading["subtype"] == "employment"
    assert reading["professional_foundation"]
    assert reading["professional_expression"]
    stages = reading["delivery_windows"][0]["stages"]
    assert any(row["code"] == "employment_joining" for row in stages)


def test_overall_career_derivation_is_static_and_carries_jaimini_signature():
    context = {
        "intent_summary": {"focus_houses": [2, 6, 10, 11], "career_subtype": "general"},
        "instant_parashari": {
            "focus_houses": [2, 6, 10, 11],
            "forward_periods": [{
                "start": "2027-01-01", "end": "2027-02-01",
                "activated_focus_houses": [2, 6, 10, 11],
                "career_manifestations": [{"code": "role_visibility"}],
            }],
        },
        "_user_evidence": {"natal_topic_factors": {"source": "validated_d1_natal_promise", "houses": [{
            "house": 10, "lord": "Mars", "lord_placement_house": 2,
            "occupants": [], "aspecting_planets": ["Jupiter"], "tone": "supportive",
        }]}},
        "normalized_evidence": {
            "natal_promise": {"status": "supported", "topic_support": "supportive"},
            "career_foundation": {
                "amatyakaraka": {"planet": "Mercury", "house": 10, "sign": "Virgo"},
                "KARAKAMSHA": {"ascendant_sign": "Leo"},
            },
        },
    }
    result = build_user_derivation(
        query_plan={"category": "career", "answer_mode": "topic_reading"},
        verdict={"direction": "supported", "confidence": 0.8},
        instant_context=context,
    )
    reading = result["career_reading"]
    assert reading["delivery_windows"] == []
    assert reading["vocation_indicators"]["amatyakaraka"]["planet"] == "Mercury"
    assert reading["vocation_indicators"]["karkamsa_ascendant"] == "Leo"
    assert "no dasha, transit or dated timing" in reading["interpretation_rule"]


def test_overall_career_composer_boundary_removes_timing_and_keeps_vocation_evidence():
    career_foundation = {
        "D1": {"houses": [{"house": 10, "tone": "supportive"}]},
        "D10": {"calculated_chart": {"ascendant_sign": "Virgo"}},
        "amatyakaraka": {"planet": "Mercury", "house": 10},
        "KARAKAMSHA": {"ascendant_sign": "Leo"},
    }
    instant_context = {
        "intent_summary": {
            "category": "career",
            "answer_mode": "topic_reading",
            "period_window": {"start": "2026-01-01", "end": "2028-12-31"},
            "time_relation": "current",
        },
        "birth_summary": {"name": "Test"},
        "normalized_evidence": {
            "career_foundation": career_foundation,
            "natal_promise": {
                "status": "supported",
                "dasha_permission_segment_count": 10,
            },
            "current_timing": {"active_dashas": {"MD": "Saturn"}},
            "transit_activation_timeline": {
                "peak_windows": [{"start": "2028-02-01", "end": "2028-02-20"}],
            },
        },
        "recent_history": [{"role": "assistant", "content": "A 2028 career peak is likely."}],
    }
    packet = {
        "query_plan": {
            "category": "career",
            "answer_mode": "topic_reading",
            "user_goal": "How is my career overall?",
            "time_scope": {
                "semantic": "open_future",
                "as_of": "2026-08-23",
                "horizon_end": "2028-12-31",
            },
        },
        "verdict": {
            "direction": "supported with conditions",
            "confidence": "medium",
            "rationale": ["MD Saturn and AD Rahu activate career houses"],
            "ranked_windows": [{"start": "2028-02-01", "end": "2028-02-20"}],
        },
        "answer_spec": {
            "career_rules": {"static_profile_rule": "Do not mention timing."},
            "event_rules": {"allowed_timing_windows": [{"start": "2028-02-01"}]},
        },
    }

    result = _build_instant_composer_context(instant_context, packet)

    assert "time_scope" not in result["query_plan"]
    assert "period_window" not in result["intent"]
    assert "time_relation" not in result["intent"]
    assert "ranked_windows" not in result["verdict"]
    assert "rationale" not in result["verdict"]
    assert "current_timing" not in result["evidence"]
    assert "transit_activation_timeline" not in result["evidence"]
    assert "dasha_permission_segment_count" not in result["evidence"]["natal_promise"]
    assert result["evidence"]["career_foundation"] == career_foundation
    assert not result.get("recent_history")
    assert "event_rules" not in result["answer_contract"]
    sources = " ".join(row["source"] for row in result["answer_blueprint"]["slots"])
    assert "amatyakaraka" in sources
    assert "KARAKAMSHA" in sources


def test_career_capacity_composer_keeps_individual_vocation_synthesis():
    vocation_synthesis = {
        "tenth_lord_signature": {
            "planet": "Mars",
            "conjunct_planets": ["Jupiter", "Saturn", "Rahu"],
        },
        "combination_signatures": [
            {
                "planets": ["Mars", "Rahu"],
                "work_functions": ["AI", "software", "automation"],
            },
            {
                "planets": ["Mars", "Saturn"],
                "work_functions": ["technical systems", "engineering"],
            },
        ],
        "work_functions": ["technology", "AI", "software", "systems engineering"],
        "suitable_fields": ["AI and automation", "software systems"],
    }
    career_foundation = {
        "D1": {"houses": [{"house": 10, "lord": "Mars", "lord_placement_house": 2}]},
        "D10": {"calculated_chart": {"ascendant_sign": "Virgo"}},
        "amatyakaraka": {"planet": "Mercury", "house": 8},
        "KARAKAMSHA": {"ascendant_sign": "Scorpio"},
        "vocation_synthesis": vocation_synthesis,
    }
    instant_context = {
        "intent_summary": {
            "category": "career",
            "career_subtype": "career_fit",
            "answer_mode": "potential_capacity",
        },
        "birth_summary": {"name": "Test"},
        "normalized_evidence": {
            "career_foundation": career_foundation,
            "natal_promise": {"status": "supported"},
            "topic_confirmation": {
                "topic_signals": {
                    "fn": ["administration", "industry", "operations", "process"],
                },
            },
        },
    }
    packet = {
        "query_plan": {
            "category": "career",
            "career_subtype": "career_fit",
            "answer_mode": "potential_capacity",
            "user_goal": "What career will I do?",
        },
        "verdict": {"direction": "supported", "confidence": "medium"},
        "answer_spec": {"career_rules": {"static_profile_rule": "No timing."}},
    }

    result = _build_instant_composer_context(instant_context, packet)

    assert result["evidence"]["career_foundation"]["vocation_synthesis"] == vocation_synthesis
    topic_confirmation = result["evidence"].get("topic_confirmation") or {}
    assert "fn" not in (topic_confirmation.get("topic_signals") or {})
    assert result["answer_blueprint"]["purpose"].startswith(
        "semantic slots for a timeless career-profile reading"
    )
    sources = " ".join(row["source"] for row in result["answer_blueprint"]["slots"])
    assert "career_foundation" in sources


def test_named_field_composer_uses_separate_field_and_business_verdicts():
    vocation_synthesis = {
        "ranked_planets": [
            {"planet": "Mercury", "score": 10, "reasons": ["Mercury repeats in D1 and D10"]},
            {"planet": "Saturn", "score": 8, "reasons": ["Saturn supports structured systems"]},
            {"planet": "Venus", "score": 6, "reasons": ["Venus supports client rapport"]},
        ],
        "work_structure": {
            "business_score": 8,
            "employment_score": 6,
            "inclination": "business_or_hybrid",
            "reasons": ["Business houses repeat in D1 and D10"],
        },
    }
    career_foundation = {
        "D1": {"houses": [{"house": 10, "lord": "Mercury"}]},
        "D10": {"calculated_chart": {"ascendant_sign": "Virgo"}},
        "amatyakaraka": {"planet": "Mercury"},
        "KARAKAMSHA": {"ascendant_sign": "Gemini"},
        "vocation_synthesis": vocation_synthesis,
    }
    target_intent = {
        "category": "career",
        "career_subtype": "business",
        "career_target": "software consulting",
        "career_target_structure": "business",
        "career_target_traits": ["technical_systems", "analytical_research", "client_service"],
        "answer_mode": "potential_capacity",
    }
    instant_context = {
        "intent_summary": target_intent,
        "birth_summary": {"name": "Test"},
        "normalized_evidence": {
            "career_foundation": career_foundation,
            "natal_promise": {"status": "supported"},
            "current_timing": {"mahadasha": "Saturn"},
        },
    }
    packet = {
        "query_plan": {
            **target_intent,
            "user_goal": "Can I build a software consulting business?",
        },
        "verdict": {"direction": "supported", "confidence": "medium"},
        "answer_spec": {"career_rules": {"static_profile_rule": "No timing."}},
    }

    result = _build_instant_composer_context(instant_context, packet)

    assessment = result["evidence"]["career_target_assessment"]
    assert assessment["target"] == "software consulting"
    assert assessment["field_fit"]["verdict"] == "field_fit_supported"
    assert assessment["business_fit"]["verdict"] == "business_or_client_led_supported"
    assert result["answer_contract"]["career_contract"]["question_family"] == "target_fit"
    assert "exact requested field" in result["answer_blueprint"]["purpose"]
    assert "current_timing" not in result["evidence"]
    assert result["intent"]["career_target"] == "software consulting"
    prompt = _build_instant_composer_prompt_v3(
        "Can I build a software consulting business?",
        result,
        "english",
    )
    assert "A closing question is optional" in prompt
    assert "End the visible answer with exactly one natural" not in prompt


def test_resignation_subtype_survives_foundation_and_blocks_unsupported_exit_advice():
    instant_context = {
        "intent_summary": {
            "category": "career",
            "answer_mode": "topic_reading",
        },
        "birth_summary": {"name": "Test"},
        "normalized_evidence": {
            "career_foundation": {
                "career_subtype": "resignation",
                "D1": {"houses": [{"house": 10, "lord": "Mars"}]},
                "D10": {"houses": [{"house": 10, "lord": "Mercury"}]},
                "vocation_synthesis": {"work_functions": ["technology", "analysis"]},
            },
            "natal_promise": {"status": "supported_with_conditions"},
        },
    }
    packet = {
        "query_plan": {
            "category": "career",
            "answer_mode": "topic_reading",
            "user_goal": "Should I leave my current job?",
        },
        "verdict": {
            "direction": "supported_with_conditions",
            "confidence": "medium",
            "scope": "natal and vocational profile only; no event timing",
        },
        "answer_spec": {
            "career_rules": {
                "material_windows": [],
                "decision_gate": "Never infer resignation from career fit.",
            },
        },
    }

    result = _build_instant_composer_context(instant_context, packet)

    assert result["query_plan"]["career_subtype"] == "resignation"
    assert result["query_plan"]["forecast_shape"] == "career_decision"
    assert result["intent"]["career_subtype"] == "resignation"
    decision = result["evidence"]["career_decision"]
    assert decision["affirmative_exit_allowed"] is False
    assert decision["permission"] == "resignation_not_authorized"
    assert result["verdict"]["direction"] == "do not resign on the available evidence"
    assert "stay-or-change decision" in result["answer_blueprint"]["purpose"]
    assert result["answer_blueprint"]["hard_gate"]["affirmative_exit_allowed"] is False
    assert "timeless career-profile" not in result["answer_blueprint"]["purpose"]


def test_resignation_allows_only_calculated_planned_transition_window():
    instant_context = {
        "intent_summary": {
            "category": "career",
            "answer_mode": "topic_reading",
            "career_subtype": "resignation",
        },
        "birth_summary": {"name": "Test"},
        "normalized_evidence": {
            "career_foundation": {"career_subtype": "resignation"},
        },
    }
    packet = {
        "query_plan": {
            "category": "career",
            "answer_mode": "topic_reading",
            "user_goal": "Should I leave my current job?",
        },
        "verdict": {"direction": "supported", "confidence": "high"},
        "answer_spec": {
            "career_rules": {
                "material_windows": [
                    {
                        "start": "2027-01-01",
                        "end": "2027-02-15",
                        "chain": "Saturn-Rahu-Mercury",
                        "activated_focus_houses": [2, 3, 6, 10, 11, 12],
                        "decision_matrix": {
                            "verdict": "planned_transition_supported",
                            "continuity_support": True,
                            "change_momentum": True,
                            "separation_support": True,
                            "landing_support": True,
                        },
                        "why": "Saturn activates Houses 3 and 10; Venus activates Houses 2, 6, 11 and 12",
                    }
                ]
            }
        },
        "user_derivation": {
            "career_reading": {
                "delivery_windows": [{
                    "start": "2027-01-01",
                    "end": "2027-02-15",
                    "chain": "Saturn-Rahu-Mercury",
                    "dasha_carriers": [{
                        "planet": "Saturn",
                        "dasha_levels": ["MD"],
                        "natal_placement_house": 2,
                        "event_links": [{"house": 11, "mechanisms": ["natal_aspect"]}],
                    }],
                    "transit_confirmations": [{
                        "planet": "Rahu",
                        "start": "2027-01-01",
                        "end": "2027-01-20",
                        "transit_native_house": 8,
                        "natal_placement_house": 2,
                        "natal_reaspect_number": 7,
                    }],
                }],
            },
        },
    }

    result = _build_instant_composer_context(instant_context, packet)

    decision = result["evidence"]["career_decision"]
    assert decision["affirmative_exit_allowed"] is True
    assert decision["permission"] == "planned_transition_supported"
    assert decision["windows"][0]["start"] == "2027-01-01"
    assert decision["supported_transition_windows"][0]["start"] == "2027-01-01"
    assert decision.get("non_transition_windows", []) == []
    assert "Saturn activates" in decision["windows"][0]["why"]
    assert decision["windows"][0]["dasha_carriers"][0]["planet"] == "Saturn"
    assert decision["windows"][0]["transit_confirmations"][0]["planet"] == "Rahu"
    assert result["answer_blueprint"]["hard_gate"]["affirmative_exit_allowed"] is True
    assert "Never describe landing support as missing" in result["answer_blueprint"]["hard_gate"]["rule"]


def test_all_answer_modes_have_career_specific_shapes():
    for mode in (
        "topic_reading", "potential_capacity", "timing_window", "event_prediction",
        "problem_diagnosis", "comparison_choice", "remedy_action",
    ):
        contract = answer_contract(mode, career_profile("career")["subtype"])
        assert contract["required_shape"]
        assert "natural follow-up" in contract["required_shape"]
    topic = answer_contract("topic_reading", career_profile("career")["subtype"])
    assert "Do not mention dasha, transit, dates" in topic["static_profile_rule"]


def test_career_question_families_enforce_distinct_evidence_contracts():
    cases = (
        ("topic_reading", "general", "profile"),
        ("potential_capacity", "career_fit", "vocation"),
        ("problem_diagnosis", "recognition", "diagnosis"),
        ("timing_window", "promotion", "timing"),
        ("comparison_choice", "job_vs_business", "comparison"),
        ("remedy_action", "career", "remedy"),
        ("topic_reading", "resignation", "decision"),
        ("topic_reading", "manager_relationship", "relationship"),
    )
    for mode, subtype, family in cases:
        assert career_question_family(mode, subtype) == family
        contract = answer_contract(mode, subtype)
        assert contract["question_family"] == family
        if family == "diagnosis":
            assert contract["allow_dated_timing"] is False
            assert contract["allow_future_windows"] is False


def test_role_aware_relationship_profiles_use_distinct_semantic_matrices():
    manager = career_profile("manager_relationship")
    colleague = career_profile("colleague_relationship")
    client = career_profile("client_relationship")
    mentor = career_profile("mentor_relationship")

    assert manager["relationship_target"] == "manager or reporting authority"
    assert manager["houses"] == [9, 10, 6, 11]
    assert "manager" in manager["house_roles"][9].lower()
    assert manager["divisionals"] == ["D1", "D10"]
    assert colleague["houses"] == [3, 6, 11, 10]
    assert client["houses"] == [7, 10, 11, 2]
    assert mentor["houses"] == [9, 5, 10, 11]
    assert len({tuple(manager["houses"]), tuple(colleague["houses"]), tuple(client["houses"]), tuple(mentor["houses"])}) == 4

    assert is_career_relationship("career", "manager_relationship")
    assert not is_static_career_profile("career", "manager_relationship", answer_mode="topic_reading")
    contract = answer_contract("topic_reading", "manager_relationship")
    assert contract["question_family"] == "relationship"
    assert "D1_role_houses" in contract["required_evidence"]
    assert "D10_role_confirmation" in contract["required_evidence"]


def test_manager_relationship_requests_role_charts_not_jaimini_vocation_chart():
    assert _requested_charts_from_intent(
        {"category": "career", "career_subtype": "manager_relationship"},
        answer_mode="topic_reading",
    ) == ["D1", "D10"]


def test_recognition_diagnosis_reaches_composer_without_future_windows():
    instant_context = {
        "intent_summary": {
            "category": "career", "answer_mode": "problem_diagnosis",
            "career_subtype": "recognition",
        },
        "normalized_evidence": {
            "career_foundation": {"D1": {}, "D10": {}},
            "current_timing": {"active_houses": [6]},
        },
        "birth_summary": {"name": "Test"},
    }
    diagnosis = {
        "kind": "recognition_conversion",
        "conversion_chain": [
            {"house": 6, "currently_activated": True},
            {"house": 10, "currently_activated": False},
            {"house": 11, "currently_activated": False},
            {"house": 2, "currently_activated": False},
        ],
        "conclusion": "Effort is active, but it is not yet converting into visibility or authority.",
    }
    packet = {
        "query_plan": {
            "category": "career", "answer_mode": "problem_diagnosis",
            "user_goal": "Why am I not getting recognition despite working hard?",
        },
        "verdict": {"direction": "mixed", "confidence": "medium"},
        "answer_spec": {},
        "user_derivation": {
            "career_reading": {
                "subtype": "recognition",
                "question_family": "diagnosis",
                "answer_contract": answer_contract("problem_diagnosis", "recognition"),
                "diagnosis": diagnosis,
                "delivery_windows": [{"start": "2027-01-01", "end": "2027-02-01"}],
            },
        },
    }
    result = _build_instant_composer_context(instant_context, packet)
    assert result["evidence"]["career_diagnosis"] == diagnosis
    assert "delivery_windows" not in result["evidence"]
    assert result["answer_contract"]["career_contract"]["allow_dated_timing"] is False


def test_compact_foundation_never_substitutes_d9_for_missing_d10():
    packet = _compact_career_foundation(
        "career",
        "employment",
        {"source": "validated_d1_natal_promise", "houses": [{
            "house": 10,
            "lord": "Mars",
            "lord_placement_house": 2,
            "occupants": [],
            "aspecting_planets": ["Jupiter"],
            "tone": "supportive",
        }]},
        {"topic": {"charts": {"D9": {"rows": [{"h": 10}]}}}},
        {"charts": {}},
        {},
        {},
    )
    assert packet["D1"]["houses"]
    assert packet["D10"] == {}
    assert packet["mandatory_evidence_complete"] is False
    assert packet["missing_mandatory_evidence"] == ["D10"]
    assert "negative career verdict" in " ".join(packet["interpretation_rules"])


def test_compact_foundation_uses_calculated_d10_and_vocation_confirmations():
    d10 = {"ascendant_sign": "Virgo", "planets": {"Mercury": {"house": 10}}}
    packet = _compact_career_foundation(
        "career",
        "career_fit",
        {"source": "validated_d1_natal_promise", "houses": [{
            "house": 1, "lord": "Moon", "occupants": [], "aspecting_planets": [],
        }, {
            "house": 10, "lord": "Mars", "occupants": ["Sun"], "aspecting_planets": [],
        }]},
        {},
        {"charts": {"D10": d10, "KARAKAMSHA": {"ascendant_sign": "Leo"}}},
        {"chara_karakas": {"Amatyakaraka": {"planet": "Mercury", "house": 10, "sign": "Virgo"}}},
        {
            "legacy_ranked_fields": [{"field": "generic strongest-planet answer", "score": 99}],
            "planetary_strengths": {
                "Mercury": {"shadbala_grade": "Good"},
                "Venus": {"shadbala_grade": "Excellent"},
            },
        },
    )
    assert packet["mandatory_evidence_complete"] is True
    assert packet["D10"]["calculated_chart"] == d10
    assert packet["amatyakaraka"]["planet"] == "Mercury"
    assert packet["KARAKAMSHA"]["ascendant_sign"] == "Leo"
    synthesis = packet["vocation_synthesis"]
    assert synthesis["source"] == "deterministic_cross_chart_vocation_synthesis"
    assert synthesis["ranked_planets"][0]["planet"] == "Mercury"
    assert packet["career_fit"]["ranked_fields"] == synthesis["suitable_fields"]
    assert all(row["name"] != "generic strongest-planet answer" for row in synthesis["suitable_fields"])


def test_vocation_synthesis_repetition_beats_unrelated_strongest_planet():
    synthesis = build_vocation_synthesis(
        d1_houses=[
            {"house": 6, "lord": "Mercury", "occupants": ["Mercury"]},
            {"house": 7, "lord": "Jupiter", "occupants": []},
            {"house": 10, "lord": "Mercury", "occupants": ["Mercury"], "aspects": []},
        ],
        d10_chart={
            "ascendant_sign": "Virgo",
            "planets": {"Mercury": {"house": 10}, "Venus": {"house": 3}},
        },
        amatyakaraka={"planet": "Mercury", "house": 10},
        karakamsha_chart={
            "ascendant_sign": "Gemini",
            "planets": {"Mercury": {"house": 10}},
        },
        planetary_strengths={
            "Mercury": {"shadbala_grade": "Average"},
            "Venus": {"shadbala_grade": "Excellent"},
        },
    )
    assert synthesis["ranked_planets"][0]["planet"] == "Mercury"
    assert "software, data and analytics" in [row["name"] for row in synthesis["suitable_fields"]]
    mercury_reasons = " ".join(synthesis["ranked_planets"][0]["reasons"])
    assert "D1 House 10" in mercury_reasons
    assert "D10 House 10" in mercury_reasons
    assert "Amatyakaraka" in mercury_reasons


def test_vocation_synthesis_reads_planets_joined_to_tenth_lord_as_combination():
    d1 = {
        "ascendant_sign": "Cancer",
        "planets": {
            "Mars": {"house": 2},
            "Saturn": {"house": 2},
            "Rahu": {"house": 2},
            "Jupiter": {"house": 2},
            "Mercury": {"house": 8},
        },
    }
    synthesis = build_vocation_synthesis(
        d1_houses=[
            {"house": 2, "lord": "Sun", "lord_placement_house": 9, "occupants": ["Jupiter", "Mars", "Rahu", "Saturn"]},
            {"house": 6, "lord": "Jupiter", "lord_placement_house": 2, "occupants": []},
            {"house": 10, "lord": "Mars", "lord_placement_house": 2, "occupants": [], "aspects": ["Jupiter", "Moon"]},
            {"house": 11, "lord": "Venus", "lord_placement_house": 11, "occupants": ["Venus"]},
        ],
        d1_chart=d1,
        d10_chart={"ascendant_sign": "Sagittarius", "planets": {"Mercury": {"house": 10}, "Saturn": {"house": 6}}},
        amatyakaraka={"planet": "Mercury", "house": 8},
        karakamsha_chart={"ascendant_sign": "Scorpio", "planets": {"Venus": {"house": 6}}},
    )

    signature = synthesis["tenth_lord_signature"]
    assert signature["planet"] == "Mars"
    assert signature["house"] == 2
    assert set(signature["conjunct_planets"]) == {"Jupiter", "Rahu", "Saturn"}
    combination_planets = {frozenset(row["planets"]) for row in synthesis["combination_signatures"]}
    assert frozenset({"Mars", "Saturn"}) in combination_planets
    assert frozenset({"Mars", "Rahu"}) in combination_planets
    assert frozenset({"Mars", "Jupiter"}) in combination_planets
    fields = [row["name"] for row in synthesis["suitable_fields"]]
    assert any("AI" in field or "technology" in field for field in fields)
    assert not fields[0].startswith("government")
    rahu_reasons = " ".join(next(row["reasons"] for row in synthesis["ranked_planets"] if row["planet"] == "Rahu"))
    assert "conjunct D1 House 10 lord Mars" in rahu_reasons


def test_every_planet_pair_has_a_combined_vocation_signature():
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    covered_pairs = set()
    for index, lord in enumerate(planets):
        for partner in planets[index + 1:]:
            signature = _tenth_lord_combination_signature(lord, partner)
            assert len(signature["functions"]) >= 2, (lord, partner)
            assert len(signature["fields"]) >= 2, (lord, partner)
            assert len(signature["environments"]) >= 2, (lord, partner)
            covered_pairs.add(frozenset({lord, partner}))
    assert len(covered_pairs) == 36


def test_compact_foundation_uses_calculated_d1_when_natal_audit_rows_are_absent():
    d1 = {
        "ascendant_sign": "Gemini",
        "planets": {
            "Mercury": {"house": 10, "aspects_to_houses": [4]},
            "Saturn": {"house": 6, "aspects_to_houses": [8, 12, 3]},
        },
        "houses": [
            {"house": house, "lord": lord, "occupants": occupants}
            for house, lord, occupants in (
                (1, "Mercury", []), (2, "Moon", []), (5, "Venus", []),
                (6, "Mars", ["Saturn"]), (7, "Jupiter", []),
                (10, "Jupiter", ["Mercury"]), (11, "Mars", []),
            )
        ],
    }
    d10 = {
        "ascendant_sign": "Virgo",
        "planets": {"Mercury": {"house": 10}, "Saturn": {"house": 6}},
    }
    karkamsa = {
        "ascendant_sign": "Gemini",
        "planets": {"Mercury": {"house": 10}},
    }
    packet = _compact_career_foundation(
        "career",
        "career_fit",
        {"source": "validated_d1_natal_promise"},
        {},
        {"charts": {"D1": d1, "D10": d10, "KARAKAMSHA": karkamsa}},
        {"chara_karakas": {"Amatyakaraka": {"planet": "Mercury", "house": 10}}},
        {},
    )

    assert packet["mandatory_evidence_complete"] is True
    assert len(packet["D1"]["houses"]) == 7
    synthesis = packet["vocation_synthesis"]
    assert synthesis["ranked_planets"][0]["planet"] == "Mercury"
    assert synthesis["primary_work_functions"]
    assert synthesis["suitable_fields"]
    assert synthesis["preferred_environments"]
    assert any("D1 House 10" in reason for reason in synthesis["ranked_planets"][0]["reasons"])


def test_event_timing_verdict_keeps_structured_career_subtype_and_stages():
    verdict = _build_event_timing_verdict(
        category="career",
        career_subtype="joining",
        forward_scan_periods=[{
            "start": "2027-01-01",
            "end": "2027-02-01",
            "mahadasha": "Saturn",
            "antardasha": "Rahu",
            "pratyantardasha": "Mercury",
            "relevance_score": 80,
            "activated_focus_houses": [3, 6, 10, 11],
            "why": "Houses 3, 6, 10 and 11 are active",
        }],
        horizon_segments=[],
        current_chain_rows=[],
        timing_policy={},
        focus_houses=[3, 6, 10, 11],
        current_transits={},
    )
    contract = verdict["career_layer_contract"]
    assert contract["profile"]["subtype"] == "joining"
    codes = {row["code"] for row in contract["manifestations"]}
    assert "role_change_execution" in codes
    assert "employment_joining" in codes
    assert all("does not guarantee" in row["certainty_rule"] for row in contract["manifestations"])
