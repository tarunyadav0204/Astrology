from instant_chat_v2.orchestrator import build_instant_v2_packet, finalize_instant_v2_packet
from instant_chat_v2.planner import build_query_plan
from instant_chat_v2.answer_spec import build_answer_spec
from chat.instant_chat_pipeline import (
    _build_event_timing_verdict,
    _target_focus_calculation_frame,
)


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
            "claim_gates": {"allow_timing": True},
        },
    }


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

    assert packet["answer_spec"]["max_words"] == 120
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
