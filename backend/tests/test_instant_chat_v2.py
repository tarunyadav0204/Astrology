from datetime import datetime

from instant_chat_v2.orchestrator import build_instant_v2_packet, finalize_instant_v2_packet
from instant_chat_v2.planner import build_query_plan
from instant_chat_v2.answer_spec import build_answer_spec
from chat.instant_chat_pipeline import (
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _build_event_timing_verdict,
    _instant_real_chart_facts,
    _should_force_event_current_window,
    _repair_common_utf8_mojibake,
    _resolve_period_window,
    _target_focus_calculation_frame,
)


def test_event_prediction_keeps_exact_day_window():
    assert _should_force_event_current_window(
        "event_prediction",
        {"kind": "day", "start": "2026-08-17", "end": "2026-08-17"},
    ) is False
    assert _should_force_event_current_window(
        "event_prediction",
        {"kind": "year", "start": "2026-01-01", "end": "2026-12-31"},
    ) is True


def test_daily_router_mode_resolves_to_exact_day_before_legacy_event_logic():
    window = _resolve_period_window(
        {"mode": "PREDICT_DAILY", "extracted_context": {"period": "today"}},
        datetime(2026, 8, 17, 10, 0, 0),
        "How is my day today?",
    )
    assert window == {
        "kind": "day",
        "start": "2026-08-17",
        "end": "2026-08-17",
        "span_days": 1,
        "label": "17 August 2026",
        "use_pd": True,
        "use_sk_pr": True,
    }


def _intent(category="marriage"):
    return {
        "category": category,
        "query_context": {
            "event_profile": category,
            "required_evidence": [
                "future_dasha_event_windows",
                "transit_event_windows",
            ],
        },
    }


def _context():
    return {
        "current_dashas": {
            "as_of": "2026-08-16",
            "levels": [{"level": "mahadasha", "planet": "Saturn"}],
        },
        "instant_parashari": {
            "dominant_houses": [2, 7, 11],
            "activation_mechanisms": ["dasha", "transit"],
            "active_dashas_formatted": "Saturn - Venus",
        },
        "current_transits": {
            "as_of": "2026-08-16",
            "planets": [{"planet": "Jupiter", "house": 7}],
        },
        "normalized_evidence": {
            "primary_drivers": ["The 7th house is active"],
            "secondary_modifiers": ["Saturn can delay"],
            "divisional_specifics": {"d9": "supportive"},
            "kp_evidence": {"significators": [2, 7, 11]},
            "event_timing_verdict": {
                "verdict": "supportive_window",
                "confidence": 0.86,
                "windows": [{"start": "2027-02", "end": "2027-06"}],
                "why": ["Dasha and transit agree"],
            },
            "forward_event_dasha_scan": [{
                "start": "2027-02-01", "end": "2027-06-30",
                "chain": "Saturn - Venus - Jupiter",
            }],
            "transit_activation_timeline": {
                "peak_windows": [{"start": "2027-02-01", "end": "2027-06-30"}],
            },
            "claim_gates": {"allow_timing": True},
        },
    }


def _daily_context():
    context = _context()
    context["intent_summary"] = {
        "category": "general",
        "mode": "PREDICT_DAILY",
        "answer_mode": "event_prediction",
        "period_window": {"kind": "day", "start": "2026-08-17", "end": "2026-08-17"},
        "time_relation": "current",
        "target_subject": {"key": "self", "label": "self"},
    }
    context["daily_prediction_spine"] = {
        "target_date": "2026-08-17",
        "panchanga": {"vara": "Monday", "tithi": "Chaturthi"},
        "moon": {
            "transit": {"nakshatra": "Hasta", "house": 3},
            "tara_bala": {"tara": "Sadhana", "quality": "supportive"},
        },
        "dasha_stack": [
            {"level": "Mahadasha", "planet": "Saturn", "natal": {"house": 2, "lordships": [7, 8]}, "transit": {"house": 9}, "trigger": {"score": 2}},
            {"level": "Antardasha", "planet": "Rahu", "natal": {"house": 2}, "transit": {"house": 8}, "trigger": {"score": 3}},
            {"level": "Pratyantardasha", "planet": "Saturn", "natal": {"house": 2}, "transit": {"house": 9}, "trigger": {"score": 4}},
            {"level": "Sookshma", "planet": "Mercury", "natal": {"house": 11, "lordships": [3, 12]}, "transit": {"house": 1}, "trigger": {"score": 8, "flags": ["same_nakshatra_return"]}},
            {"level": "Prana", "planet": "Moon", "natal": {"house": 4}, "transit": {"house": 3}, "trigger": {"score": 9}},
        ],
        "daily_judgment": {
            "top_activated_houses": [{"house": 3, "score": 72}, {"house": 11, "score": 61}],
            "top_event_domains": [{"domain": "communication", "score": 72}, {"domain": "gains", "score": 61}],
            "support_houses": [3, 11],
            "caution_houses": [],
            "moon_tara_quality": {"tara": "Sadhana", "quality": "supportive"},
            "massive_result_factors": [{"level": "Sookshma", "planet": "Mercury", "flags": ["same_nakshatra_return"]}],
            "prediction_rule": "Prioritize Prana, Sookshma and PD; MD/AD are background.",
        },
        "school_judgments": {
            "kp": {"available": True, "event_houses": [3, 11], "verdict": "supportive_for_intent"},
            "parashari": {"verdict": "supportive_for_intent"},
            "merge_rule": "KP confirms materialisation; Moon and micro dashas time the day.",
        },
        "interpretation_rules": [
            "Prana and Sookshma are the sharpest event triggers.",
            "MD and AD are background permission only.",
        ],
    }
    context["normalized_evidence"]["daily_prediction_spine"] = context["daily_prediction_spine"]
    return context


def test_exact_day_uses_daily_evidence_contract_not_generic_timing():
    context = _daily_context()
    intent = _intent("general")
    intent.update(context["intent_summary"])
    packet = build_instant_v2_packet(
        question="How is my day today?",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self", "label": "self"},
        language="english",
        instant_context=context,
    )

    assert packet["query_plan"]["time_scope"]["is_exact_day"] is True
    assert packet["evidence_plan"]["forecast_shape"] == "daily_forecast"
    capabilities = {row["capability"]: row for row in packet["evidence_ledger"]["capabilities"]}
    assert set(capabilities) == {
        "daily.five_level_dasha",
        "daily.moon_tara_bala",
        "daily.kp_fructification",
        "daily.school_synthesis",
    }
    assert all(row["status"] == "available" for row in capabilities.values())
    assert packet["verdict"]["direction"] == "supportive_day"
    assert packet["answer_spec"]["daily_rules"]["decision_hierarchy"][0].startswith("KP")
    assert "MD/AD/PD alone" in packet["answer_spec"]["daily_rules"]["instruction"]
    assert "claim-timing-window" not in {
        row["claim_id"] for row in packet["answer_spec"]["claims"]
    }


def test_daily_composer_receives_micro_timing_and_mandatory_shape():
    context = _daily_context()
    packet = build_instant_v2_packet(
        question="How is today?",
        intent=context["intent_summary"],
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )
    brief = _build_instant_composer_context(context, packet)
    prompt = _build_instant_composer_prompt_v3("How is today?", brief, "english")

    assert brief["query_plan"]["forecast_shape"] == "daily_forecast"
    levels = [row["level"] for row in brief["evidence"]["daily_prediction"]["five_level_dasha"]]
    assert levels[-2:] == ["Sookshma", "Prana"]
    assert brief["evidence"]["daily_prediction"]["kp"]["event_houses"] == [3, 11]
    assert set(brief["evidence"]).issubset({"natal_promise", "daily_prediction"})
    assert "daily_prediction" in brief["evidence"]
    assert "Never decide or describe today mainly from MD/AD/PD" in prompt
    assert "Sentence 1 must give a plain overall outlook" in prompt


def test_exact_day_missing_daily_calculators_is_not_replaced_by_period_evidence():
    context = _context()
    context["intent_summary"] = {
        "category": "general",
        "mode": "PREDICT_DAILY",
        "period_window": {"kind": "day", "start": "2026-08-17"},
    }
    packet = build_instant_v2_packet(
        question="How is today?",
        intent=context["intent_summary"],
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )
    assert packet["verdict"]["direction"] == "insufficient_evidence"
    assert "daily.five_level_dasha" in packet["verdict"]["missing_required_capabilities"]


def test_common_utf8_mojibake_is_repaired_without_touching_other_scripts():
    assert _repair_common_utf8_mojibake("things arenâ\x80\x99t moving — ठीक") == "things aren’t moving — ठीक"


def test_planner_does_not_keyword_route_raw_question():
    first = build_query_plan(
        question="When will I marry?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english",
    )
    second = build_query_plan(
        question="Completely unrelated wording", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english",
    )

    assert first["category"] == second["category"] == "marriage"
    assert first["requested_evidence"] == second["requested_evidence"]


def test_planner_preserves_llm_resolved_user_goal():
    intent = _intent("career")
    intent["query_context"]["user_goal"] = "understand whether career improves this year"
    plan = build_query_plan(
        question="How is my career this year?",
        intent=intent,
        answer_mode="timing_window",
        target_subject={"key": "self"},
        language="english",
    )

    assert plan["user_goal"] == "understand whether career improves this year"


def test_marriage_packet_exposes_plan_evidence_and_claim_bindings():
    packet = build_instant_v2_packet(
        question="When will I get married?",
        intent=_intent(),
        answer_mode="event_timing",
        target_subject={"key": "self", "label": "self"},
        language="english",
        instant_context=_context(),
    )

    capabilities = {
        item["capability"] for item in packet["evidence_plan"]["capability_requests"]
    }
    assert "parashari.d9_confirmation" in capabilities
    assert "kp.seventh_cusp_chain" in capabilities
    assert "transit.marriage_triggers" in capabilities
    capability_rows = {
        item["capability"]: item for item in packet["evidence_ledger"]["capabilities"]
    }
    assert capability_rows["transit.marriage_triggers"]["status"] == "available"
    assert capability_rows["transit.marriage_triggers"]["evidence_ids"]
    assert capability_rows["jaimini.darakaraka_upapada"]["status"] == "not_exposed"
    assert packet["evidence_ledger"]["record_count"] >= 7
    assert packet["verdict"]["direction"] == "supportive_window"
    assert packet["verification"]["passed"] is True

    finalized = finalize_instant_v2_packet(packet, answer="A supported window appears in early 2027.")
    assert finalized["verification"]["answer_present"] is True
    assert finalized["verification"]["passed"] is True


def test_large_calculator_values_are_compacted_before_persistence():
    context = _context()
    context["normalized_evidence"]["primary_drivers"] = ["x" * 1200] * 30
    packet = build_instant_v2_packet(
        question="When?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english", instant_context=context,
    )
    record = next(
        item for item in packet["evidence_ledger"]["records"]
        if item["kind"] == "primary_drivers"
    )
    assert len(record["value"]) == 13
    assert record["value"][-1] == {"_omitted_items": 18}
    assert len(record["value"][0]) == 800


def test_resolved_instant_intent_drives_the_evidence_plan():
    context = _context()
    context["intent_summary"] = {
        "category": "career",
        "time_relation": "future",
        "target_subject": {"key": "self", "label": "self"},
    }
    packet = build_instant_v2_packet(
        question="What happens next?",
        intent=_intent("general"),
        answer_mode="event_timing",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )

    assert packet["query_plan"]["category"] == "career"
    assert packet["query_plan"]["time_scope"]["relation"] == "future"
    assert packet["test_mode"] is True


def test_semantic_timeframe_and_derived_subject_survive_planning():
    intent = _intent("career")
    intent["extracted_context"] = {"timeframe": "next twelve months"}
    intent["evidence_plan"] = {}
    intent["evidence_plan"]["question_parts"] = [
        {"timeframe": {"kind": "relative_range", "amount": 12, "unit": "months"}}
    ]
    plan = build_query_plan(
        question="Will my wife's career improve?",
        intent=intent,
        answer_mode="timing_window",
        target_subject={"key": "wife", "label": "wife", "base_house": 7},
        language="english",
    )

    assert plan["time_scope"]["requested"] == "next twelve months"
    assert plan["time_scope"]["semantic"]["amount"] == 12
    assert plan["interpretation_frame"] == "native_chart_derived_house"


def test_comparison_does_not_pass_as_specific_without_option_evidence():
    packet = build_instant_v2_packet(
        question="Promotion or job change?",
        intent=_intent("career"),
        answer_mode="comparison_choice",
        target_subject={"key": "self"},
        language="english",
        instant_context=_context(),
    )

    assert packet["verdict"]["direction"] == "insufficient_option_evidence"
    assert "comparison.option_specific_evidence" in packet["verdict"]["missing_required_capabilities"]


def test_answer_contract_limits_instant_reply_and_protects_derived_framing():
    packet = build_instant_v2_packet(
        question="Will my wife's career improve?",
        intent=_intent("career"),
        answer_mode="timing_window",
        target_subject={"key": "wife", "label": "wife", "base_house": 7},
        language="english",
        instant_context=_context(),
    )

    assert packet["answer_spec"]["max_words"] == 320
    assert "derived indication" in packet["answer_spec"]["target_framing"]


def test_event_prediction_contract_preserves_current_cause_and_earliest_relief():
    context = _context()
    context["normalized_evidence"]["event_timing_verdict"] = {
        "direction": "conditional",
        "comparison": "current_active_future_slightly_cleaner",
        "score_delta": 2,
        "answer_rule": "Say the future window is only slightly cleaner/stronger.",
        "current_window": {
            "start": "2026-08-16",
            "end": "2026-09-18",
            "why": "Saturn and Rahu occupy focus house 2",
        },
        "earliest_material_future_window": {
            "start": "2027-04-15",
            "end": "2027-10-04",
            "chain": "Saturn - Rahu - Venus",
        },
        "best_future_window": {
            "start": "2029-07-21",
            "end": "2029-08-15",
            "chain": "Saturn - Jupiter - Venus",
        },
        "current_topic_transits": [
            {"planet": "Ketu", "house": 2, "sign": "Leo"},
        ],
    }
    packet = build_instant_v2_packet(
        question="Why is money unstable and when does it improve?",
        intent=_intent("wealth"),
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )

    spec = packet["answer_spec"]
    assert spec["timing_sequence"]["order"][1] == "earliest_material_improvement"
    assert spec["current_cause_rules"]["allowed_current_topic_transits"][0]["planet"] == "Ketu"
    assert packet["verdict"]["ranked_windows"][1]["start"] == "2027-04-15"


def test_close_comparison_contract_forbids_a_soft_winner():
    context = _context()
    context["normalized_evidence"]["option_comparison"] = {
        "options": [
            {"event_profile": "promotion", "peak_score": 45, "best_window": {"start": "2027-04-15"}},
            {"event_profile": "job_change", "peak_score": 47, "best_window": {"start": "2026-09-19"}},
        ],
        "comparison": {"direction": "close_call", "favored_option": None, "score_gap": 2},
    }
    packet = build_instant_v2_packet(
        question="Promotion or job change?",
        intent=_intent("career"),
        answer_mode="comparison_choice",
        target_subject={"key": "self"},
        language="english",
        instant_context=context,
    )

    rules = packet["answer_spec"]["comparison_rules"]
    assert packet["verdict"]["direction"] == "close_call"
    assert "neither option" in rules["required_conclusion"].lower()
    assert "slightly favored" in rules["instruction"]


def test_derived_event_contract_blocks_unmapped_transits_and_sets_horizon():
    context = _context()
    context["intent_summary"] = {
        "category": "career",
        "target_subject": {"key": "wife", "label": "wife", "base_house": 7},
        "extracted_context": {"timeframe": "next twelve months"},
    }
    context["evidence_plan"] = {
        "question_parts": [
            {"timeframe": {"kind": "relative_range", "amount": 12, "unit": "months"}}
        ]
    }
    context["normalized_evidence"]["event_timing_verdict"] = {
        "direction": "conditional",
        "comparison": "current_active_future_slightly_cleaner",
        "score_delta": 2,
        "answer_rule": "Say the future window is only slightly cleaner/stronger.",
        "current_window": {"start": "2026-08-16", "end": "2026-09-18"},
        "material_future_progression": [
            {"start": "2027-04-15", "end": "2027-08-16"},
        ],
        "current_topic_transits": [{"planet": "Rahu", "house": 2}],
    }
    intent = _intent("career")
    intent["extracted_context"] = {"timeframe": "next twelve months"}
    intent["evidence_plan"] = context["evidence_plan"]
    packet = build_instant_v2_packet(
        question="Will my wife's career improve in the next twelve months?",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "wife", "label": "wife", "base_house": 7},
        language="english",
        instant_context=context,
    )

    spec = packet["answer_spec"]
    assert spec["current_cause_rules"]["allowed_current_topic_transits"] == []
    assert spec["event_rules"]["hard_horizon_end"] == "2027-08-16"
    assert spec["event_rules"]["window_score_delta"] == 2
    assert "slightly cleaner" in spec["event_rules"]["window_answer_rule"]
    assert spec["event_rules"]["allowed_timing_windows"][-1]["end"] == "2027-08-16"
    assert "interviews" in spec["event_rules"]["career_manifestations"]
    assert "your wife" in spec["required_derived_opening"].lower()
    assert "never 'her/his nth house'" in spec["event_rules"]["derived_subject_rule"].lower()
    assert spec["event_rules"]["required_material_windows"] == [
        {
            "start": "2027-04-15",
            "end": "2027-08-16",
            "chain": None,
            "activated_focus_houses": [],
            "why": None,
        }
    ]
    assert spec["event_rules"]["dasha_level_terms"]["PD"] == "Pratyantardasha / sub-sub-period"


def test_spouse_career_focus_houses_are_calculated_natively_and_displayed_relatively():
    native_houses, native_to_target = _target_focus_calculation_frame([2, 6, 10, 11], 7)

    assert native_houses == [8, 12, 4, 5]
    assert native_to_target == {8: 2, 12: 6, 4: 10, 5: 11}


def test_event_progression_keeps_distinct_material_windows_even_when_second_scores_lower():
    verdict = _build_event_timing_verdict(
        category="career",
        forward_scan_periods=[
            {
                "start": "2026-08-16",
                "end": "2026-09-18",
                "chain": "Saturn - Rahu - Saturn",
                "mahadasha": "Saturn",
                "antardasha": "Rahu",
                "pratyantardasha": "Saturn",
                "relevance_score": 26,
                "time_status": "current",
            },
            {
                "start": "2026-09-19",
                "end": "2027-02-12",
                "chain": "Saturn - Rahu - Mercury",
                "mahadasha": "Saturn",
                "antardasha": "Rahu",
                "pratyantardasha": "Mercury",
                "relevance_score": 42,
                "time_status": "future",
            },
            {
                "start": "2027-04-15",
                "end": "2027-08-16",
                "chain": "Saturn - Rahu - Venus",
                "mahadasha": "Saturn",
                "antardasha": "Rahu",
                "pratyantardasha": "Venus",
                "relevance_score": 39,
                "time_status": "future",
            },
        ],
        horizon_segments=[],
        current_chain_rows=[],
        timing_policy={},
        focus_houses=[2, 6, 10, 11],
        current_transits={},
    )

    assert [row["chain"] for row in verdict["material_future_progression"]] == [
        "Saturn - Rahu - Mercury",
        "Saturn - Rahu - Venus",
    ]


def test_event_progression_drops_weaker_redundant_stage_to_keep_later_escalation():
    verdict = _build_event_timing_verdict(
        category="wealth",
        forward_scan_periods=[
            {
                "start": "2026-08-16", "end": "2026-09-18",
                "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Saturn",
                "relevance_score": 33, "time_status": "current", "activated_focus_houses": [2, 9],
            },
            {
                "start": "2027-04-15", "end": "2027-10-04",
                "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Venus",
                "relevance_score": 56, "time_status": "future", "activated_focus_houses": [2, 9, 11],
            },
            {
                "start": "2027-10-05", "end": "2027-11-25",
                "mahadasha": "Saturn", "antardasha": "Rahu", "pratyantardasha": "Sun",
                "relevance_score": 53, "time_status": "future", "activated_focus_houses": [2, 9],
            },
            {
                "start": "2028-04-22", "end": "2028-08-22",
                "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Jupiter",
                "relevance_score": 66, "time_status": "future", "activated_focus_houses": [2, 9, 11],
            },
            {
                "start": "2029-07-21", "end": "2029-08-15",
                "mahadasha": "Saturn", "antardasha": "Jupiter", "pratyantardasha": "Venus",
                "relevance_score": 68, "time_status": "future", "activated_focus_houses": [2, 9, 11],
            },
        ],
        horizon_segments=[], current_chain_rows=[], timing_policy={},
        focus_houses=[2, 9, 11], current_transits={},
    )

    assert [row["chain"] for row in verdict["material_future_progression"]] == [
        "Saturn - Rahu - Venus",
        "Saturn - Jupiter - Jupiter",
        "Saturn - Jupiter - Venus",
    ]


def test_answer_spec_preserves_window_facts_without_inviting_fact_fusion():
    query_plan = {
        "category": "marriage",
        "answer_mode": "event_prediction",
        "time_scope": {"horizon_end": "2029-08-16"},
    }
    why = "MD Saturn rules focus house(s) [7]; AD Jupiter occupies focus house 2"
    verdict = {
        "direction": "conditional",
        "ranked_windows": [{
            "start": "2028-08-23",
            "end": "2029-01-16",
            "chain": "Saturn - Jupiter - Saturn",
            "why": why,
        }],
    }
    ledger = {"records": [{
        "evidence_id": "ev-001",
        "kind": "event_timing_verdict",
        "value": {"material_future_progression": []},
    }]}

    spec = build_answer_spec(query_plan, verdict, ledger)

    assert spec["event_rules"]["allowed_timing_windows"][0]["why"] == why
    assert "Never fuse two facts" in spec["event_rules"]["instruction"]


def test_timing_confidence_requires_named_calculator_families():
    limited = build_instant_v2_packet(
        question="When will I marry?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english", instant_context=_context(),
    )
    assert limited["verdict"]["confidence_tier"] == "limited_timing_support"

    high_context = _context()
    high_context["normalized_evidence"]["karaka_evidence"] = {
        "chara_karakas": {"Darakaraka": {"planet": "Venus"}}
    }
    high = build_instant_v2_packet(
        question="When will I marry?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english", instant_context=high_context,
    )
    assert high["verdict"]["confidence_tier"] == "high_confidence"

    support_context = _context()
    support_context["normalized_evidence"].update({
        "karaka_evidence": {"chara_karakas": {"Darakaraka": {"planet": "Venus"}}},
        "double_transit": {"windows": [{"house": 7, "start": "2027-02-01"}]},
    })
    supported = build_instant_v2_packet(
        question="When will I marry?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english", instant_context=support_context,
    )
    assert supported["verdict"]["confidence_tier"] == "high_support"


def test_fused_verdict_and_current_transits_do_not_replace_dasha_or_trigger_windows():
    context = _context()
    context["normalized_evidence"].pop("forward_event_dasha_scan")
    context["normalized_evidence"].pop("transit_activation_timeline")
    packet = build_instant_v2_packet(
        question="When will I marry?", intent=_intent(), answer_mode="event_timing",
        target_subject={"key": "self"}, language="english", instant_context=context,
    )
    capability_rows = {
        item["capability"]: item for item in packet["evidence_ledger"]["capabilities"]
    }
    assert capability_rows["parashari.dasha_windows"]["status"] == "not_exposed"
    assert capability_rows["transit.trigger_windows"]["status"] == "not_exposed"
    assert packet["verdict"]["direction"] == "insufficient_evidence"


def test_routing_only_flows_request_no_astrology_calculators():
    for mode in ("compound_plan", "dedicated_partnership_flow"):
        packet = build_instant_v2_packet(
            question="One routed request", intent=_intent("general"), answer_mode=mode,
            target_subject={"key": "self"}, language="english", instant_context=_context(),
        )
        assert packet["evidence_plan"]["capability_requests"] == []


def test_dedicated_calculator_flows_cannot_answer_from_generic_chart_evidence():
    cases = (
        ("factual_chart_lookup", "general", "chart.all_supported_facts"),
        ("location_recommendation", "location", "location.goal_based_recommendation"),
        ("dedicated_muhurat_flow", "muhurat", "muhurat.ranked_slots"),
    )
    for mode, category, required_capability in cases:
        packet = build_instant_v2_packet(
            question="A dedicated calculator request", intent=_intent(category), answer_mode=mode,
            target_subject={"key": "self"}, language="english", instant_context=_context(),
        )
        capability_rows = {
            row["capability"]: row for row in packet["evidence_ledger"]["capabilities"]
        }
        assert capability_rows[required_capability]["status"] == "not_exposed"
        assert packet["verdict"]["direction"] == "insufficient_evidence"


def test_muhurat_location_query_survives_llm_plan_without_invented_coordinates():
    intent = _intent("muhurat")
    intent["extracted_context"] = {
        "muhurat_event_type": "business_opening",
        "muhurat_start_date": "2026-10-01",
        "muhurat_end_date": "2026-10-15",
        "muhurat_location_query": "Pune, Maharashtra",
    }
    plan = build_query_plan(
        question="Find a business opening muhurat in Pune", intent=intent,
        answer_mode="dedicated_muhurat_flow", target_subject={"key": "self"},
        language="english",
    )
    assert plan["special_flow"]["muhurat_location_query"] == "Pune, Maharashtra"


def test_requested_divisional_and_jaimini_chart_facts_are_really_calculated():
    longitudes = {
        "Sun": 12.0, "Moon": 48.0, "Mars": 79.0, "Mercury": 103.0,
        "Jupiter": 137.0, "Venus": 166.0, "Saturn": 201.0,
        "Rahu": 250.0, "Ketu": 70.0,
    }
    chart = {
        "ascendant": 95.0,
        "ayanamsa": 24.1,
        "planets": {
            name: {
                "longitude": longitude,
                "sign": int(longitude / 30),
                "house": ((int(longitude / 30) - 3) % 12) + 1,
            }
            for name, longitude in longitudes.items()
        },
    }
    karakas = {
        "chara_karakas": {
            "Atmakaraka": {"planet": "Mars"},
        }
    }
    facts = _instant_real_chart_facts(
        chart_data=chart,
        requested_charts=["D12", "Swamsa", "Karakamsha"],
        requested_fact="planet placements",
        karaka_evidence=karakas,
        d1_snapshot={},
    )
    assert facts["calculation_complete"] is True
    assert set(facts["charts"]) == {"D12", "SWAMSA", "KARAKAMSHA"}
    assert facts["charts"]["D12"]["planets"]["Ketu"]["house"] >= 1
    assert facts["charts"]["SWAMSA"]["atmakaraka"] == "Mars"


def test_unsupported_chart_fact_is_unavailable_instead_of_guessed():
    facts = _instant_real_chart_facts(
        chart_data={"ascendant": 0.0, "planets": {}},
        requested_charts=["D13"], requested_fact="placements",
        karaka_evidence={}, d1_snapshot={},
    )
    assert facts["calculation_complete"] is False
    assert facts["missing_requested_charts"] == ["D13"]
