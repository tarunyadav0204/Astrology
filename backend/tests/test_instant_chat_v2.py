from datetime import datetime

import pytest

from instant_chat_v2.orchestrator import build_instant_v2_packet, finalize_instant_v2_packet
from instant_chat_v2.planner import build_query_plan
from instant_chat_v2.answer_spec import build_answer_spec
from instant_chat_v2.evidence import build_evidence_ledger
from instant_chat_v2.user_derivation import build_user_derivation
from chat.instant_chat_pipeline import (
    _build_budgeted_instant_prompt,
    _build_period_topic_forecast,
    _build_instant_composer_context,
    _build_instant_composer_prompt_v3,
    _build_instant_prompt,
    _constitutional_health_required_rows,
    _fit_composer_brief,
    _build_event_timing_verdict,
    _instant_real_chart_facts,
    _is_retrospective_event_request,
    _instant_answer_language_error,
    _instant_relational_voice_contract,
    _instant_response_language,
    _mode_selection_from_intent,
    _requested_charts_from_intent,
    _should_force_event_current_window,
    _strip_constitutional_health_validation_markers,
    _repair_common_utf8_mojibake,
    _resolve_constitutional_health_rules,
    _resolve_period_window,
    _slim_event_prediction_payload,
    _target_focus_calculation_frame,
    _validate_constitutional_health_answer,
)


def test_all_instant_answer_prompt_paths_share_relational_voice_contract():
    marker = "RELATIONAL VOICE CONTRACT"
    required_phrases = (
        "emotionally perceptive",
        "lived experience",
        "Protect the user's agency",
        "Never encourage dependency",
    )
    prompts = [
        _build_budgeted_instant_prompt("How is my career?", {}, "english"),
        _build_instant_prompt(
            "How is my career?",
            {"intent_summary": {"category": "career", "answer_mode": "topic_reading"}},
            "english",
        ),
        _build_instant_composer_prompt_v3(
            "How is my career?",
            {
                "context_profile": "instant_composer_v3",
                "query_plan": {"category": "career", "answer_mode": "topic_reading"},
                "intent": {"category": "career", "answer_mode": "topic_reading"},
                "verdict": {}, "evidence": {}, "answer_contract": {},
            },
            "english",
        ),
        _build_instant_composer_prompt_v3(
            "Explain my D9 chart",
            {
                "context_profile": "instant_composer_v3",
                "query_plan": {"answer_mode": "factual_chart_lookup", "forecast_shape": "chart_fact_reading"},
                "intent": {"answer_mode": "factual_chart_lookup"},
                "verdict": {}, "evidence": {"chart_facts": {"charts": {}}}, "answer_contract": {},
            },
            "english",
        ),
        _build_instant_composer_prompt_v3(
            "What are my health vulnerabilities?",
            {
                "context_profile": "instant_composer_v3",
                "query_plan": {"category": "health", "answer_mode": "topic_reading"},
                "intent": {"category": "health", "answer_mode": "topic_reading"},
                "verdict": {}, "evidence": {},
                "answer_contract": {"health_rules": {"is_time_bound_question": False}},
            },
            "english",
        ),
    ]

    assert marker in _instant_relational_voice_contract()
    for prompt in prompts:
        assert marker in prompt
        for phrase in required_phrases:
            assert phrase in prompt


def test_instant_response_language_prefers_latest_message_router_over_app_locale():
    assert _instant_response_language(
        "What are my health vulnerabilities?",
        {"response_language": "english"},
        "hindi",
    ) == "english"
    assert _instant_response_language(
        "मेरी स्वास्थ्य कमजोरियाँ क्या हैं?",
        {"response_language": "hindi"},
        "english",
    ) == "hindi"
    assert _instant_response_language(
        "What are my health vulnerabilities?",
        {"response_language": "hindi"},
        "hindi",
    ) == "english"


def test_instant_response_language_uses_script_for_older_intent_payloads():
    assert _instant_response_language(
        "मेरी स्वास्थ्य कमजोरियाँ क्या हैं?", {}, "english"
    ) == "hindi"


def test_instant_health_language_gate_rejects_hindi_for_english_question():
    hindi = "आपकी कुंडली के अनुसार मुख्य स्वास्थ्य संवेदनशीलता नाक और हृदय से जुड़ी है।"
    assert "expected English" in _instant_answer_language_error(hindi, "english")
    assert _instant_answer_language_error("Your chart highlights the nose and upper back.", "english") is None


def test_health_evidence_ledger_preserves_late_anatomy_causes():
    # Real calculator rows are wider than the generic audit compactor's
    # 24-key limit. Cause fields must not disappear merely because they were
    # inserted late in the dictionary.
    wide_zone = {f"diagnostic_{index}": index for index in range(30)}
    wide_zone.update({
        "zone": "anorectal and pelvic region",
        "confidence": "medium",
        "confluence_count": 2,
        "primary_medical_reasons": [
            "House 6 lord Mars is placed in House 8; that house's anatomical field includes anus, rectum, pelvis."
        ],
    })
    wide_chain = {f"diagnostic_{index}": index for index in range(30)}
    wide_chain.update({
        "sixth_lord": "Mars",
        "sixth_lord_house": 8,
        "sixth_lord_house_zones": ["anus", "rectum", "pelvis"],
    })
    ledger = build_evidence_ledger(
        {
            "normalized_evidence": {
                "health_body_area": {
                    "major_vulnerabilities": [wide_zone],
                    "sixth_house_chain": wide_chain,
                }
            },
            "instant_parashari": {},
        },
        {"capability_requests": []},
    )
    record = next(row for row in ledger["records"] if row["kind"] == "health_body_area")
    health_value = record["value"]
    assert health_value["major_vulnerabilities"][0]["primary_medical_reasons"]
    assert health_value["sixth_house_chain"]["sixth_lord_house"] == 8

    answer_spec = build_answer_spec(
        {
            "category": "health",
            "answer_mode": "topic_reading",
            "time_scope": {"requested": "natal", "is_exact_day": False},
        },
        {"direction": "constitutional susceptibility", "confidence": 0.72},
        ledger,
    )
    zone_row = answer_spec["health_rules"]["allowed_zone_evidence"][0]
    assert zone_row["anatomy_basis"] == wide_zone["primary_medical_reasons"]


def test_oversized_composer_brief_never_drops_health_anatomy_causes():
    cause = (
        "House 6 lord Mars is placed in House 8; its anatomical field "
        "includes anus, rectum and pelvis"
    )
    health_rules = {
        "is_time_bound_question": False,
        "allowed_zone_names": ["anorectal and pelvic region"],
        "required_zone_count": 1,
        "allowed_zone_evidence": [{
            "zone": "anorectal and pelvic region",
            "confidence": "medium",
            "confluence_count": 2,
            "anatomy_basis": [cause],
            "why": ["House 6 lord Mars is placed in House 8"],
        }],
    }
    context = {
        "evidence": {
            "health_rules": health_rules,
            "optional_diagnostics": ["x" * 500 for _ in range(20)],
        },
        "answer_contract": {"health_rules": health_rules},
        "oversized_optional_context": [
            {"diagnostic": "y" * 500, "nested": ["z" * 500]}
            for _ in range(20)
        ],
    }

    fitted = _fit_composer_brief(context, target_chars=1200)
    rows = _constitutional_health_required_rows(
        fitted["evidence"]["health_rules"]
    )

    assert rows[0]["required_cause_facts"] == [cause]
    assert (
        fitted["answer_contract"]["health_rules"]
        ["allowed_zone_evidence"][0]["anatomy_basis"]
    ) == [cause]

    prompt = _build_instant_composer_prompt_v3(
        "What are my health vulnerabilities?",
        fitted,
        "english",
    )
    assert cause in prompt
    assert '"required_cause_facts":[]' not in prompt


def test_slim_event_prediction_preserves_d1_promise_for_readable_evidence():
    natal_topic_factors = {
        "source": "validated_d1_natal_promise",
        "houses": [{
            "house": 10,
            "lord": "Mars",
            "occupants": ["Jupiter"],
            "aspecting_planets": ["Saturn"],
            "tone": "supportive",
            "supportive_weight": 4.0,
            "challenging_weight": 1.0,
            "factors": [],
        }],
    }
    context = _slim_event_prediction_payload(
        birth_summary={},
        natal_snapshot={},
        target_chart_context={},
        current_dashas_levels={},
        current_transits_formatted={},
        instant_parashari={
            "focus_houses": [2, 6, 10, 11],
            "natal_topic_factors": natal_topic_factors,
            "divisional_support": {},
        },
        normalized_evidence={
            "natal_promise": {"status": "supported", "topic_support": "supportive"},
        },
        period_window={"start": "2026-08-20", "end": "2027-08-20"},
        category="career",
        question="How is my career this year?",
        chart_data={"planets": {}},
        house_lordships={},
    )

    derivation = build_user_derivation(
        query_plan={"category": "career", "answer_mode": "event_prediction"},
        verdict={"direction": "supported", "confidence": "medium"},
        instant_context=context,
    )

    assert context["normalized_evidence"]["natal_promise"]["status"] == "supported"
    assert context["_user_evidence"]["natal_topic_factors"] == natal_topic_factors
    assert derivation["natal_promise"]["d1_house_factors"][0]["house"] == 10


def test_slim_retrospective_marriage_keeps_only_transit_confirmed_ranked_windows():
    confirmed = {
        "start": "2012-12-01", "end": "2013-06-01",
        "mahadasha": "Saturn", "antardasha": "Saturn", "pratyantardasha": "Venus",
        "relevance_score": 94, "transit_trigger_score": 14,
        "activated_focus_houses": [2, 7, 11],
        "peak_activation_windows": [{
            "start": "2013-05-08", "end": "2013-05-08", "planet": "Venus",
            "trigger_score": 14, "trigger_kinds": ["event_house_delivery"],
        }],
        "transit_trigger_windows": [{"large_raw_row": "must not cross the slim boundary"}],
        "why": "Saturn dasha permission with a Venus delivery peak",
    }
    unconfirmed = {
        "start": "2011-11-04", "end": "2012-04-24",
        "mahadasha": "Saturn", "antardasha": "Saturn", "pratyantardasha": "Saturn",
        "relevance_score": 84, "transit_trigger_score": 0,
        "activated_focus_houses": [2, 7, 11], "peak_activation_windows": [],
        "why": "Dasha permission without historical transit delivery",
    }
    context = _slim_event_prediction_payload(
        birth_summary={}, natal_snapshot={}, target_chart_context={},
        current_dashas_levels={"md": {"planet": "Saturn"}},
        current_transits_formatted={"Saturn": {"house_from_lagna": 7}},
        instant_parashari={
            "focus_houses": [2, 7, 11],
            "historical_event_dasha_scan": {
                "horizon_start": "1996-04-02", "horizon_end": "2026-08-26",
                "periods": [confirmed, unconfirmed],
                "claim_rule": "Probable periods only.",
            },
        },
        normalized_evidence={
            "timing_policy": {"time_direction": "retrospective"},
            "historical_event_dasha_scan": {"periods": [confirmed, unconfirmed]},
        },
        period_window={
            "kind": "historical_range", "start": "1996-04-02", "end": "2026-08-26",
        },
        category="marriage", question="When was I married?",
        chart_data={"planets": {}}, house_lordships={},
    )

    normalized = context["normalized_evidence"]
    assert context["intent_summary"]["time_relation"] == "past"
    assert normalized["current_timing"] == {}
    assert normalized["forward_event_dasha_scan"] == {}
    assert context["current_dashas"] == {}
    assert context["current_transits"] == {}
    assert "transit_trigger_windows" not in normalized["historical_event_dasha_scan"]["periods"][0]
    assert normalized["event_timing_verdict"]["ranked_windows"] == [
        normalized["historical_event_dasha_scan"]["periods"][0]
    ]

    ledger = build_evidence_ledger(context, {"capability_requests": []})
    by_kind = {row["kind"]: row for row in ledger["records"]}
    assert "historical_dasha_windows" in by_kind
    assert "historical_event_windows" in by_kind


def test_historical_transit_evidence_is_absent_without_a_delivery_peak():
    scan = {
        "periods": [{
            "start": "2011-11-04", "end": "2012-04-24",
            "transit_trigger_score": 0, "peak_activation_windows": [],
        }]
    }
    ledger = build_evidence_ledger(
        {
            "normalized_evidence": {"historical_event_dasha_scan": scan},
            "instant_parashari": {"historical_event_dasha_scan": scan},
        },
        {"capability_requests": []},
    )
    assert "historical_dasha_windows" in {row["kind"] for row in ledger["records"]}
    assert "historical_event_windows" not in {row["kind"] for row in ledger["records"]}


def test_explicit_d9_does_not_override_marriage_promise_mode():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "potential_capacity",
            "category": "marriage",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D9",
                "explicit": True,
                "requested": ["D9"],
            },
            "evidence_plan": {
                "question_parts": [{"intent_families": ["factual_chart_lookup"]}],
            },
        },
        "Does my D9 promise marriage?",
    )

    assert selection["raw_answer_mode"] == "potential_capacity"
    assert selection["answer_mode"] == "potential_capacity"


def test_explicit_named_chart_still_repairs_generic_topic_mode():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "topic_reading",
            "category": "general",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D9",
                "explicit": True,
                "requested": ["D9"],
            },
        },
        "Explain my D9 chart",
    )

    assert selection["answer_mode"] == "factual_chart_lookup"


def test_llm_life_outcome_repairs_conflicting_factual_marriage_mode():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "factual_chart_lookup",
            "requested_object": "life_outcome",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "category": "marriage",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D9",
                "explicit": True,
                "requested": ["D9"],
            },
        },
        "Is marriage possible in my kundali?",
    )

    assert selection["raw_answer_mode"] == "factual_chart_lookup"
    assert selection["requested_object"] == "life_outcome"
    assert selection["answer_mode"] == "potential_capacity"


def test_llm_named_chart_keeps_factual_mode():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "factual_chart_lookup",
            "requested_object": "named_chart",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "category": "general",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D9",
                "explicit": True,
                "requested": ["D9"],
            },
        },
        "Explain my D9 chart",
    )

    assert selection["answer_mode"] == "factual_chart_lookup"


def test_factual_chart_derivation_does_not_render_generic_natal_promise():
    derivation = build_user_derivation(
        query_plan={"answer_mode": "factual_chart_lookup", "category": "marriage"},
        verdict={"direction": "calculated_chart", "confidence": "medium"},
        instant_context={
            "normalized_evidence": {
                "chart_facts": {
                    "requested_charts": ["D9"],
                    "source": "DivisionalChartCalculator",
                    "calculation_complete": True,
                    "reading_lines": ["D9 lagna: Pisces", "D9 Mercury: Aries, house 2"],
                    "charts": {
                        "D9": {
                            "domain": {"life_area": "marriage and dharma"},
                            "lagna": {
                                "sign_name": "Pisces", "lord": "Jupiter",
                                "lord_house": 4, "lord_dignity": "enemy",
                            },
                            "support_signals": ["Moon supports the lagna lord."],
                            "caution_signals": ["Saturn influences the partnership house."],
                            "houses": [],
                        },
                    },
                },
                "natal_promise": {"status": "not_established"},
            },
        },
    )

    assert "chart_reading" in derivation
    assert "natal_promise" not in derivation
    assert derivation["chart_reading"]["fact_groups"][0]["chart"] == "D9"
    assert derivation["chart_reading"]["fact_groups"][0]["lines"][0] == "D9 ascendant is Pisces."


def test_natal_derivation_keeps_relevant_special_astrology_factors():
    derivation = build_user_derivation(
        query_plan={"answer_mode": "potential_capacity", "category": "marriage"},
        verdict={"direction": "supported_natal_promise", "confidence": "medium"},
        instant_context={
            "intent_summary": {"category": "marriage", "focus_houses": [2, 7]},
            "instant_parashari": {
                "focus_houses": [2, 7],
                "natal_topic_factors": {
                    "houses": [{
                        "house": 7,
                        "lord": "Saturn",
                        "tone": "mixed",
                        "occupants": [],
                        "aspecting_planets": [],
                        "factors": [
                            {
                                "source": "planet_gandanta",
                                "planet": "Saturn",
                                "polarity": "challenging",
                                "weight": 0.35,
                                "facts": {"gandanta_name": "Jyeshtha-Mula Gandanta", "intensity": "high"},
                            },
                            {
                                "source": "yogi_lord",
                                "planet": "Saturn",
                                "polarity": "supportive",
                                "weight": 0.25,
                                "facts": {"special_sign_name": "Capricorn"},
                            },
                            {
                                "source": "avayogi_lord",
                                "planet": "Saturn",
                                "polarity": "challenging",
                                "weight": 0.25,
                                "facts": {"special_sign_name": "Cancer"},
                            },
                            {
                                "source": "planet_in_dagdha_rashi",
                                "planet": "Saturn",
                                "polarity": "challenging",
                                "weight": 0.25,
                                "facts": {"dagdha_sign_name": "Leo"},
                            },
                            {
                                "source": "planet_in_tithi_shunya_rashi",
                                "planet": "Saturn",
                                "polarity": "challenging",
                                "weight": 0.25,
                                "facts": {"tithi_shunya_sign_name": "Virgo"},
                            },
                        ],
                    }],
                },
            },
            "normalized_evidence": {
                "natal_promise": {"status": "supported", "topic_support": "mixed"},
            },
        },
    )

    house = derivation["natal_promise"]["d1_house_factors"][0]
    rendered = " ".join([*house["support_notes"], *house["caution_notes"]])
    assert "Yogi lord" in rendered
    assert "Gandanta" in rendered
    assert "Avayogi" in rendered
    assert "Dagdha Rashi" in rendered
    assert "Tithi Shunya Rashi" in rendered

    composer = _build_instant_composer_context(
        {
            "intent_summary": {"category": "marriage", "answer_mode": "potential_capacity"},
            "normalized_evidence": {
                "natal_promise": {"status": "supported", "topic_support": "mixed"},
            },
        },
        {
            "query_plan": {"answer_mode": "potential_capacity", "category": "marriage"},
            "verdict": {"direction": "supported_natal_promise", "confidence": "medium"},
            "answer_spec": {},
            "user_derivation": derivation,
        },
    )
    composer_special = composer["evidence"]["special_natal_factors"]
    assert any("Gandanta" in row["effect"] for row in composer_special)
    assert any("Yogi lord" in row["effect"] for row in composer_special)
    assert any("Dagdha Rashi" in row["effect"] for row in composer_special)
    assert any("Tithi Shunya Rashi" in row["effect"] for row in composer_special)


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
            "natal_promise": {
                "status": "supported",
                "topic_support": "supportive",
                "rule": "Natal and divisional evidence only",
            },
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


def test_marriage_possibility_uses_natal_promise_without_current_timing():
    context = _context()
    context["intent_summary"] = {
        "category": "marriage",
        "answer_mode": "potential_capacity",
        "target_subject": {"key": "self", "label": "self"},
    }
    packet = build_instant_v2_packet(
        question="Is marriage possible in my kundali?",
        intent=context["intent_summary"],
        answer_mode="potential_capacity",
        target_subject={"key": "self", "label": "self"},
        language="english",
        instant_context=context,
    )
    capabilities = {row["capability"]: row for row in packet["evidence_ledger"]["capabilities"]}
    assert capabilities["parashari.marriage_promise"]["status"] == "available"
    assert capabilities["parashari.d9_confirmation"]["status"] == "available"
    assert packet["verdict"]["direction"] == "supported_natal_promise"
    composer = _build_instant_composer_context(context, packet)
    assert "current_timing" not in composer["evidence"]
    assert "active_areas" not in composer["evidence"]
    assert composer["answer_contract"]["capacity_rules"]["verdict_direction"] == "supported_natal_promise"
    prompt = _build_instant_composer_prompt_v3(
        "Is marriage possible in my kundali?", composer, "english"
    )
    assert "static natal-promise question" in prompt
    assert "Houses 2 or 8 alone cannot establish marriage promise" in prompt


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


def test_common_utf8_mojibake_repairs_hindi_answer():
    original = "आपके लग्न का उदय हो रहा है और विवाह का योग है।"
    broken = original.encode("utf-8").decode("latin-1")
    assert _repair_common_utf8_mojibake(broken) == original


def test_common_utf8_mojibake_leaves_valid_multilingual_text_unchanged():
    original = "Marriage is supported — विवाह का योग है।"
    assert _repair_common_utf8_mojibake(original) == original


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


def test_planner_uses_resolved_calendar_end_for_this_year():
    intent = _intent("health")
    intent["period_window"] = {
        "kind": "year",
        "start": "2026-01-01",
        "end": "2026-12-31",
    }
    intent.setdefault("evidence_plan", {})["question_parts"] = [{
        "timeframe": {
            "kind": "relative_range",
            "value": "this year",
            "duration_months": 12,
        },
    }]
    intent["extracted_context"] = {"timeframe": "this year"}

    plan = build_query_plan(
        question="How will be my health this year?",
        intent=intent,
        answer_mode="timing_window",
        target_subject={"key": "self"},
        language="english",
        as_of="2026-08-22",
    )

    assert plan["time_scope"]["as_of"] == "2026-08-22"
    assert plan["time_scope"]["horizon_end"] == "2026-12-31"


@pytest.mark.parametrize(
    ("months", "expected"),
    [(6, "2027-02-26"), (12, "2027-08-26"), (36, "2029-08-26")],
)
def test_planner_bounded_future_duration_overrides_current_day_period_window(months, expected):
    intent = _intent("career")
    intent["period_window"] = {
        "kind": "day",
        "start": "2026-08-26",
        "end": "2026-08-26",
    }
    intent.setdefault("evidence_plan", {})["question_parts"] = [{
        "timeframe": {
            "kind": "bounded_future",
            "duration_months": months,
        },
    }]

    plan = build_query_plan(
        question="A bounded future question",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        as_of="2026-08-26",
    )

    assert plan["time_scope"]["horizon_end"] == expected


def test_planner_marks_open_past_event_discovery_as_retrospective():
    intent = _intent("marriage")
    intent["time_relation"] = "past"
    intent.setdefault("evidence_plan", {})["question_parts"] = [{
        "timeframe": {"kind": "open_past"},
        "event_profile": "marriage",
    }]
    plan = build_query_plan(
        question="When was I married?",
        intent=intent,
        answer_mode="event_prediction",
        target_subject={"key": "self"},
        language="english",
        as_of="2026-08-26",
    )
    assert plan["time_scope"]["retrospective"] is True
    assert plan["time_scope"]["relation"] == "past"
    assert plan["time_scope"]["horizon_end"] == "2026-08-26"


def test_planner_recovers_retrospective_direction_from_router_dialogue_facts():
    intent = _intent("marriage")
    intent["evidence_plan"] = {
        "question_parts": [{
            "part_id": "p1", "event_profile": "marriage",
            "timeframe": {"kind": "none"},
        }],
        "evidence_needs": [{"kind": "natal_topic_foundation"}],
    }
    intent["extracted_context"] = {
        "requested_fact": "marriage timing (past)",
        "instant_dialogue": {
            "known_facts": {"event": "marriage", "timing_type": "past_event"},
            "ready_to_calculate": True,
        },
    }

    plan = build_query_plan(
        question="When was I married?", intent=intent,
        answer_mode="event_prediction", target_subject={"key": "self"},
        language="english", as_of="2026-08-26",
    )

    assert plan["time_scope"]["retrospective"] is True
    assert plan["time_scope"]["semantic"]["kind"] == "open_past"
    assert plan["time_scope"]["relation"] == "past"
    assert "historical_dasha_event_windows" in plan["requested_evidence"]
    assert "historical_transit_event_windows" in plan["requested_evidence"]
    assert "future_dasha_event_windows" not in plan["requested_evidence"]
    assert _is_retrospective_event_request(
        intent,
        answer_mode="event_prediction",
        category="marriage",
    ) is True


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
    # Wealth timing now requires the same calculated D1/D2 foundation used by
    # the live Wealth graph; a timing window cannot create financial promise.
    context["normalized_evidence"]["wealth_foundation"] = {
        "d1_available": True,
        "availability": {"d2": True},
    }
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
    # No focus-house activation was supplied for this synthetic window, so the
    # resolver must not invent interviews (or any other career manifestation).
    assert spec["event_rules"]["career_manifestations"] == []
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


def test_health_answer_spec_only_allows_confluent_major_vulnerabilities():
    query_plan = {
        "category": "surgery",
        "answer_mode": "topic_reading",
        "time_scope": {},
    }
    verdict = {"ranked_windows": []}
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {
            "major_vulnerabilities": [{
                "zone": "knees",
                "confidence": "high",
                "confluence_count": 3,
                "sources": ["H10 Capricorn", "Saturn in H6"],
                "why": ["H10 lord Saturn sits in dusthana H6"],
                "mechanisms": ["chronic / degenerative"],
            }],
            "priority_zones": [
                {"zone": "heart", "confidence": "directional"},
                {"zone": "knees", "confidence": "high"},
            ],
        },
    }]}

    spec = build_answer_spec(query_plan, verdict, ledger)

    assert spec["health_rules"]["allowed_zone_names"] == ["knees"]
    assert spec["health_rules"]["health_question_type"] == "surgery"
    assert spec["health_rules"]["allowed_mechanisms"] == ["chronic / degenerative"]
    assert spec["health_rules"]["allowed_zone_evidence"][0]["sources"] == [
        "H10 Capricorn", "Saturn in H6"
    ]
    assert "Never state that surgery is required" in spec["health_rules"]["category_safety"]
    assert "heart" not in spec["health_rules"]["allowed_zone_names"]


def test_health_answer_spec_reconstructs_exact_sixth_chain_causes_after_profile_compaction():
    query_plan = {"category": "health", "answer_mode": "topic_reading", "time_scope": {}}
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {
            # This mirrors the production failure: ranked regions survived but
            # their verbose reason arrays were compacted away.
            "major_vulnerabilities": [
                {"zone": "hair", "anatomical_members": ["hair"]},
                {"zone": "shoulders", "anatomical_members": ["shoulders", "arms", "hands"]},
                {"zone": "head", "anatomical_members": ["head", "brain", "face"]},
                {"zone": "anorectal and pelvic region"},
            ],
            "sixth_house_chain": {
                "sixth_lord": "Mars",
                "sixth_house_sign": "Aries",
                "sixth_house_sign_zones": ["head", "brain", "face", "eyes"],
                "sixth_lord_sign": "Gemini",
                "sixth_lord_sign_zones": ["shoulders", "arms", "hands", "lungs"],
                "sixth_lord_nakshatra": "Ardra",
                "sixth_lord_nakshatra_pada": 2,
                "sixth_lord_nakshatra_lord": "Rahu",
                "sixth_lord_nakshatra_zones": ["hair"],
                "sixth_lord_house": 8,
                "sixth_lord_house_zones": ["anus", "rectum", "pelvis", "excretory organs"],
            },
        },
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": []}, ledger)
    rows = {
        row["zone"]: row["anatomy_basis"]
        for row in spec["health_rules"]["allowed_zone_evidence"]
    }

    assert any("Ardra" in fact for fact in rows["hair"])
    assert any("Mars is in Gemini" in fact for fact in rows["shoulders"])
    assert not any("House 3" in fact for fact in rows["shoulders"])
    assert any("sign in House 6 is Aries" in fact for fact in rows["head"])
    assert any("Mars is placed in House 8" in fact for fact in rows["anorectal and pelvic region"])


def test_broad_health_vulnerability_question_forbids_current_period_narration():
    query_plan = {
        "category": "health",
        "answer_mode": "topic_reading",
        "time_scope": {
            "requested": None,
            "semantic": {"kind": "none"},
            "relation": "current_or_next",
            "as_of": "2026-08-21",
            "is_exact_day": False,
        },
    }
    verdict = {"ranked_windows": []}
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {
            "major_vulnerabilities": [{
                "zone": "spine",
                "confidence": "high",
                "sources": ["Sun in H2", "H5 Leo"],
                "mechanisms": ["chronic / degenerative"],
                "activation_sources": ["Current mahadasha: Saturn"],
            }],
            "priority_zones": [],
        },
    }]}

    spec = build_answer_spec(query_plan, verdict, ledger)

    rule = spec["health_rules"]["constitutional_question_rule"]
    assert "standing health vulnerabilities" in rule
    assert "Do not narrate the current dasha" in rule


@pytest.mark.parametrize(
    "router_scope",
    [
        "current", "birth", "birth_chart", "natal", "natal_chart",
        "constitutional", "constitution", "lifetime",
    ],
)
def test_router_default_scope_does_not_turn_health_vulnerability_into_timing(router_scope):
    query_plan = {
        "category": "health",
        "answer_mode": "topic_reading",
        "time_scope": {
            "requested": router_scope,
            "semantic": {"kind": "none"},
            "relation": "current_or_next",
            "as_of": "2026-08-21",
            "is_exact_day": False,
        },
    }
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {
            "major_vulnerabilities": [{
                "zone": "heart and upper spine/back",
                "confidence": "medium",
                "sources": ["Sixth lord in Leo"],
                "activation_sources": ["Current Saturn-Rahu period"],
            }],
        },
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": []}, ledger)

    assert spec["health_rules"]["is_time_bound_question"] is False
    assert "current dasha or MD/AD/PD" in spec["health_rules"]["forbidden_topics"]


def test_explicit_health_timing_mode_still_allows_supported_current_activation():
    query_plan = {
        "category": "health",
        "answer_mode": "event_prediction",
        "time_scope": {
            "requested": "right now",
            "semantic": {"kind": "relative_range", "value": "right now"},
            "relation": "current_or_next",
            "as_of": "2026-08-21",
            "is_exact_day": False,
        },
    }
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {"major_vulnerabilities": [{"zone": "spine", "confidence": "medium"}]},
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": []}, ledger)

    assert spec["health_rules"]["is_time_bound_question"] is True
    assert spec["health_rules"]["forbidden_topics"] == []


def test_health_risk_question_is_not_timed_by_generic_event_prediction_mode():
    query_plan = {
        "category": "health",
        "answer_mode": "event_prediction",
        "time_scope": {
            "requested": "current",
            "semantic": {"kind": "current"},
            "relation": "current_or_next",
            "as_of": "2026-08-22",
            "horizon_end": "2028-12-31",
            "is_exact_day": False,
        },
    }
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {"major_vulnerabilities": [{"zone": "cardiovascular regulation"}]},
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": [{
        "start": "2026-01-01", "end": "2026-04-06",
    }]}, ledger)

    assert spec["health_rules"]["is_time_bound_question"] is False
    assert "timing windows or calendar forecasts" in spec["health_rules"]["forbidden_topics"]


def test_health_vulnerability_ignores_inferred_semantic_horizon_without_user_time_request():
    query_plan = {
        "category": "health",
        "answer_mode": "topic_reading",
        "time_scope": {
            "requested": "current",
            # Some router paths derive this from the system horizon even when
            # the user's words contain no timing request.
            "semantic": {"kind": "date_range", "value": "through 2028"},
            "as_of": "2026-08-22",
            "horizon_end": "2028-12-31",
            "is_exact_day": False,
        },
    }
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {"major_vulnerabilities": [{"zone": "head"}]},
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": []}, ledger)

    assert spec["health_rules"]["is_time_bound_question"] is False
    assert "timing windows or calendar forecasts" in spec["health_rules"]["forbidden_topics"]


def test_composer_removes_ranked_and_transit_windows_before_as_of_date():
    brief = _build_instant_composer_context(
        {
            "intent_summary": {"category": "career", "answer_mode": "timing_window"},
            "normalized_evidence": {
                "transit_activation_timeline": {"peak_windows": [
                    {"start": "2026-01-01", "end": "2026-04-06", "planet": "Rahu"},
                    {"start": "2026-09-01", "end": "2026-10-01", "planet": "Mercury"},
                ]},
            },
        },
        {
            "query_plan": {
                "category": "career",
                "answer_mode": "timing_window",
                "time_scope": {"as_of": "2026-08-22", "horizon_end": "2026-12-31"},
            },
            "verdict": {"ranked_windows": [
                {"start": "2026-01-01", "end": "2026-04-06", "label": "past"},
                {"start": "2026-09-01", "end": "2026-10-01", "label": "future"},
            ]},
            "answer_spec": {},
        },
    )

    assert [row["label"] for row in brief["verdict"]["ranked_windows"]] == ["future"]
    assert [
        row["planet"] for row in brief["evidence"]["transit_activation_timeline"]["peak_windows"]
    ] == ["Mercury"]


def test_yearly_health_contract_requires_activation_chain_and_strict_horizon():
    query_plan = {
        "category": "health",
        "answer_mode": "timing_window",
        "time_scope": {
            "requested": "this year",
            "semantic": {"kind": "relative_range", "value": "this year"},
            "relation": "current_to_future",
            "as_of": "2026-08-22",
            "horizon_end": "2026-12-31",
            "is_exact_day": False,
        },
    }
    ledger = {"records": [{
        "evidence_id": "ev-health",
        "kind": "health_body_area",
        "value": {
            "major_vulnerabilities": [{
                "zone": "heart and upper spine/back",
                "confidence": "medium",
                "why": ["Sixth lord occupies Leo"],
                "mechanisms": ["chronic / structural"],
            }],
            "medical_profile": {
                "protective_factors": ["Jupiter supports the disease axis"],
                "condition_susceptibilities": [],
            },
        },
    }]}

    spec = build_answer_spec(query_plan, {"ranked_windows": []}, ledger)
    health = spec["health_rules"]
    forecast = health["period_forecast_rule"]

    assert health["is_time_bound_question"] is True
    assert forecast["hard_horizon"]["end"] == "2026-12-31"
    assert "explicit dasha activation and transit confirmation" in forecast["activation_gate"]
    assert "Gandanta is a natal sensitivity modifier only" in forecast["gandanta_rule"]
    assert "Do not recommend, reject, delay, or prefer any treatment" in forecast["medical_advice_rule"]
    assert "Do not extend 'this year' into the next year" in forecast["scope_rule"]
    assert health["protective_factors"] == ["Jupiter supports the disease axis"]


def test_yearly_health_forecast_joins_dates_to_calculated_vulnerabilities():
    normalized = {
        "window_rules": {"year_like": True},
        "current_timing": {"period_window": {"start": "2026-08-22", "end": "2026-12-31"}},
        "window_dasha_segments": {"segments": [{
            "start": "2026-09-19",
            "end": "2026-12-31",
            "mahadasha": "Saturn",
            "antardasha": "Rahu",
            "pratyantardasha": "Mercury",
            "relevance_score": 17,
            "natal_promise_status": "supported_by_active_dasha_carriers",
            "activated_focus_houses": [6, 8],
            "peak_activation_windows": [{
                "start": "2026-10-13", "end": "2026-11-02",
                "trigger_score": 8, "why": "Mercury reinforces the natal health axis",
            }],
        }]},
    }
    health_rules = {
        "allowed_zone_evidence": [{
            "zone": "heart and upper spine/back",
            "confidence": "medium",
            "mechanisms": ["chronic / structural"],
            "why": ["Sixth lord occupies Leo"],
        }],
        "condition_susceptibilities": [{
            "title": "vascular-pressure susceptibility",
            "risk_level": "directional",
            "interpretation": "monitor pressure-related sensitivity",
        }],
        "protective_factors": ["Jupiter supports House 6"],
    }

    forecast = _build_period_topic_forecast(
        normalized,
        "health",
        {"as_of": "2026-08-22", "horizon_end": "2026-12-31"},
        health_rules=health_rules,
    )

    phase = forecast["chronological_phases"][0]
    health = phase["health_forecast"]
    assert health["health_level"] == "strongest_watch_period"
    assert health["activated_health_houses"] == [6, 8]
    assert health["transit_confirmed"] is True
    assert health["possible_body_regions"][0]["zone"] == "heart and upper spine/back"
    assert health["possible_condition_patterns"][0]["title"] == "vascular-pressure susceptibility"
    assert "general wellness advice" in forecast["health_narration_contract"]


def test_broad_health_composer_receives_only_ranked_zone_contract():
    health_rules = {
        "health_question_type": "health",
        "is_time_bound_question": False,
        "allowed_zone_names": ["face", "spine", "mouth", "anorectal and pelvic region"],
        "required_zone_count": 4,
        "require_all_allowed_zones": True,
        "allowed_zone_evidence": [
            {
                "zone": "face",
                "confidence": "high",
                "why": ["Malefics in House 2"],
                "mechanisms": ["chronic / degenerative"],
                "activation_sources": ["Current Saturn period"],
            },
            {
                "zone": "spine",
                "confidence": "high",
                "why": ["House 5 lord under pressure"],
                "mechanisms": ["structural"],
                "activation_sources": ["Current Rahu transit"],
            },
            {
                "zone": "mouth",
                "confidence": "high",
                "why": ["Sixth lord shares House 2 with Mars"],
                "mechanisms": ["acute / inflammatory"],
            },
            {
                "zone": "anorectal and pelvic region",
                "confidence": "medium",
                "anatomy_basis": ["House 6 lord Mars is placed in House 8; its anatomical field includes anus, rectum and pelvis"],
                "why": ["House 6 lord Mars is placed in House 8"],
                "mechanisms": ["acute / inflammatory"],
            },
        ],
        "constitutional_question_rule": "Standing natal susceptibility only.",
        "forbidden_topics": ["current dasha", "current transit"],
    }
    brief = _build_instant_composer_context(
        {
            "intent_summary": {"category": "health", "answer_mode": "topic_reading"},
            "normalized_evidence": {
                "current_timing": {"mahadasha": "Saturn"},
                "active_areas": [6, 8],
                "transit_activation_timeline": {"peak_windows": [{"planet": "Rahu"}]},
                "health_body_area": {"current_dasha": "Saturn-Rahu-Saturn"},
                "natal_promise": {"status": "supported"},
            },
            "birth_summary": {"name": "Test"},
            "recent_history": [
                {"question": "What period am I in?", "answer": "Saturn-Rahu-Saturn."}
            ],
        },
        {
            "query_plan": {
                "category": "health",
                "answer_mode": "topic_reading",
                "user_goal": "Understand health vulnerabilities",
                "time_scope": {"is_exact_day": False},
            },
            "verdict": {"direction": "constitutional susceptibility"},
            "answer_spec": {"health_rules": health_rules},
        },
    )

    assert set(brief["evidence"]) == {"health_rules"}
    compact_rules = brief["evidence"]["health_rules"]
    assert [row["zone"] for row in compact_rules["allowed_zone_evidence"]] == [
        "face", "spine", "mouth", "anorectal and pelvic region"
    ]
    assert compact_rules["required_zone_count"] == 4
    assert compact_rules["require_all_allowed_zones"] is True
    assert compact_rules["allowed_zone_evidence"][3]["anatomy_basis"] == [
        "House 6 lord Mars is placed in House 8; its anatomical field includes anus, rectum and pelvis"
    ]
    assert all("activation_sources" not in row for row in compact_rules["allowed_zone_evidence"])
    assert brief["answer_blueprint"]["slots"][0]["slot"].startswith("ranked susceptibility")
    assert brief["verdict"]["scope"] == "natal constitution only; no current timing"
    assert "rationale" not in brief["verdict"]
    assert not brief.get("recent_history")
    assert compact_rules["forbidden_topics"] == ["current dasha", "current transit"]
    prompt = _build_instant_composer_prompt_v3(
        "What are my health vulnerabilities?", brief, "english"
    )
    assert "Do not mention a current period" in prompt
    assert "NATAL-ONLY HEALTH EVIDENCE" in prompt
    assert "every supplied anatomical region" in prompt
    assert "every region its own explicit explanatory sentence" in prompt
    assert "name the evidence-bound planet" in prompt
    assert "do not expose chart codes, numbered houses" in prompt.lower()
    assert "validation_marker` exactly" in prompt
    assert "never replace, infer, or change those facts" in prompt
    assert "copy that row's `validation_marker` exactly" in prompt.lower()
    assert "app-language fallback" in prompt
    assert "140-220 visible words" in prompt
    prompt_context = prompt.split("NATAL-ONLY HEALTH EVIDENCE:\n", 1)[1]
    assert '"required_zone_rows"' in prompt_context
    assert '"required_cause_facts"' in prompt_context
    assert '"health_rules"' not in prompt_context
    assert "Saturn-Rahu-Saturn" not in prompt
    assert '"verdict"' not in prompt
    assert '"recent_history"' not in prompt


def test_constitutional_health_answer_rejects_invented_region_causes():
    rows = _constitutional_health_required_rows({
        "allowed_zone_evidence": [
            {"zone": "hair", "anatomy_basis": ["House 6 lord Mars occupies Ardra pada 2; its anatomical focus is hair"]},
            {"zone": "shoulders", "anatomy_basis": ["House 6 lord Mars is in Gemini, focusing its health indication on shoulders, arms and hands"]},
            {"zone": "head", "anatomy_basis": ["The sign in House 6 is Aries, linking the disease axis to head, brain and face"]},
            {"zone": "anorectal and pelvic region", "anatomy_basis": ["House 6 lord Mars is placed in House 8; its anatomical field includes anus, rectum and pelvis"]},
        ]
    })
    wrong = (
        "Hair is highlighted because the Moon is in the 6th house. "
        "Shoulders are sensitive because Mars is in the 3rd house. "
        "The head is sensitive because the Moon is in Aries. "
        "The anorectal and pelvic region is sensitive because the Ascendant is Scorpio."
    )

    errors = _validate_constitutional_health_answer(wrong, rows)

    assert any("hair" in error and "Ardra" in error for error in errors)
    assert any("shoulders" in error and "Gemini" in error for error in errors)
    assert any("head" in error and "House 6" in error for error in errors)
    assert any("anorectal" in error and "House 8" in error for error in errors)


def test_constitutional_health_answer_accepts_exact_calculated_causes_per_region():
    rows = _constitutional_health_required_rows({
        "allowed_zone_evidence": [
            {"zone": "hair", "anatomy_basis": ["House 6 lord Mars occupies Ardra pada 2; its anatomical focus is hair"]},
            {"zone": "shoulders", "anatomy_basis": ["House 6 lord Mars is in Gemini, focusing its health indication on shoulders, arms and hands"]},
            {"zone": "head", "anatomy_basis": ["The sign in House 6 is Aries, linking the disease axis to head, brain and face"]},
            {"zone": "anorectal and pelvic region", "anatomy_basis": ["House 6 lord Mars is placed in House 8; its anatomical field includes anus, rectum and pelvis"]},
        ]
    })
    correct = (
        "Hair is highlighted because the 6th lord Mars occupies Ardra nakshatra. "
        "The shoulders are sensitive because the 6th lord Mars is in Gemini. "
        "The head is highlighted because Aries is the sign in House 6. "
        "The anorectal and pelvic region is highlighted because the 6th lord Mars is placed in House 8."
    )

    assert _validate_constitutional_health_answer(correct, rows) == []


def test_constitutional_health_answer_accepts_localized_prose_with_exact_row_markers():
    rows = _constitutional_health_required_rows({
        "allowed_zone_evidence": [
            {
                "zone": "nose",
                "anatomy_basis": [
                    "House 6 lord Jupiter occupies Magha pada 3, ruled by Ketu; its anatomical focus is nose"
                ],
            },
            {
                "zone": "heart and upper spine/back",
                "anatomy_basis": [
                    "House 6 lord Jupiter is in Leo, focusing its health indication on heart, spine, upper back"
                ],
            },
        ]
    })
    hindi = (
        f"पहला क्षेत्र नाक है। छठे भाव के स्वामी गुरु मघा में हैं। {rows[0]['validation_marker']} "
        f"दूसरा क्षेत्र हृदय और ऊपरी रीढ़ है। गुरु सिंह राशि में हैं। {rows[1]['validation_marker']}"
    )

    assert _validate_constitutional_health_answer(
        hindi, rows, strict_sentence_binding=False
    ) == []
    visible = _strip_constitutional_health_validation_markers(hindi)
    assert "HEALTH_EVIDENCE" not in visible
    assert "नाक" in visible
    assert "हृदय" in visible


def test_constitutional_health_localized_answer_without_markers_still_fails_closed():
    rows = _constitutional_health_required_rows({
        "allowed_zone_evidence": [{
            "zone": "nose",
            "anatomy_basis": [
                "House 6 lord Jupiter occupies Magha pada 3, ruled by Ketu; its anatomical focus is nose"
            ],
        }]
    })
    errors = _validate_constitutional_health_answer(
        "नाक के लिए छठे भाव के स्वामी गुरु मघा में हैं।",
        rows,
        strict_sentence_binding=False,
    )
    assert any("missing region: nose" in error for error in errors)


def test_constitutional_health_gate_resolves_rules_from_v2_answer_spec():
    rules = {
        "is_time_bound_question": False,
        "allowed_zone_evidence": [{
            "zone": "anorectal and pelvic region",
            "anatomy_basis": [
                "House 6 lord Mars is placed in House 8; its anatomical field includes anus, rectum and pelvis"
            ],
        }],
    }

    resolved = _resolve_constitutional_health_rules(
        {"evidence": {}},
        {"answer_spec": {"health_rules": rules}},
        {},
    )

    assert resolved is rules
    assert _constitutional_health_required_rows(resolved)[0]["region"] == "anorectal and pelvic region"


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
    d12 = facts["charts"]["D12"]
    assert d12["planets"]["Ketu"]["house"] >= 1
    assert d12["domain"]["code"] == "D12"
    assert "parents" in d12["domain"]["life_area"]
    assert d12["lagna"]["lord"]
    assert d12["planets"]["Sun"]["dignity"]
    assert isinstance(d12["planets"]["Sun"]["aspects_to_houses"], list)
    assert d12["houses"]
    assert d12["support_signals"] or d12["caution_signals"]
    assert facts["charts"]["SWAMSA"]["atmakaraka"] == "Mars"
    assert facts["charts"]["KARAKAMSHA"]["domain"]["code"] == "Karkamsa"
    assert any(line.startswith("D12 lagna:") for line in facts["reading_lines"])
    assert "D12 Ketu:" in facts["reading_text"]
    assert "predicts" in (facts.get("analysis_brief") or "")


def test_unsupported_chart_fact_is_unavailable_instead_of_guessed():
    facts = _instant_real_chart_facts(
        chart_data={"ascendant": 0.0, "planets": {}},
        requested_charts=["D13"], requested_fact="placements",
        karaka_evidence={}, d1_snapshot={},
    )
    assert facts["calculation_complete"] is False
    assert facts["missing_requested_charts"] == ["D13"]


def test_requested_charts_come_from_llm_fields_not_question_text():
    assert _requested_charts_from_intent(
        {
            "answer_mode": "topic_reading",
            "category": "family",
            "divisional_charts": ["D1", "D9", "D12"],
        },
        answer_mode="topic_reading",
    ) == []
    assert _requested_charts_from_intent(
        {
            "chart_focus": {"explicit": True, "primary": "D12", "requested": ["D12"]},
            "extracted_context": {"requested_chart": "D12"},
        },
        answer_mode="factual_chart_lookup",
    ) == ["D12"]
    assert "D12" in _requested_charts_from_intent(
        {
            "divisional_charts": ["D1", "D9", "D12"],
            "category": "family",
        },
        answer_mode="factual_chart_lookup",
    )


def test_composer_v3_sends_chart_facts_instead_of_family_topic_for_d12():
    brief = _build_instant_composer_context(
        {
            "intent_summary": {"category": "family", "answer_mode": "factual_chart_lookup"},
            "normalized_evidence": {
                "chart_facts": {
                    "requested_charts": ["D12"],
                    "reading_text": "D12 lagna: Gemini\nD12 Sun: Virgo, house 4",
                    "reading_lines": ["D12 lagna: Gemini", "D12 Sun: Virgo, house 4"],
                    "source": "DivisionalChartCalculator",
                    "charts": {
                        "D12": {
                            "ascendant_sign": 2,
                            "planets": {"Sun": {"sign": 5, "sign_name": "Virgo", "house": 4}},
                        }
                    },
                },
                "topic_confirmation": {"topic": "family"},
                "active_areas": ["parents"],
            },
            "birth_summary": {"name": "Test"},
        },
        {
            "query_plan": {
                "category": "family",
                "answer_mode": "factual_chart_lookup",
                "special_flow": {"requested_chart": "D12"},
            },
            "verdict": {"direction": "calculated_chart"},
            "answer_spec": {
                "answer_mode": "factual_chart_lookup",
                "chart_fact_rules": {"instruction": "Read only evidence.chart_facts."},
            },
        },
    )
    prompt = _build_instant_composer_prompt_v3("Explain my D12 chart", brief, "english")

    assert brief["query_plan"]["forecast_shape"] == "chart_fact_reading"
    assert "D12 lagna: Gemini" in (brief["evidence"]["chart_facts"]["reading_text"] or "")
    assert "topic_confirmation" not in (brief.get("evidence") or {})
    d12 = ((brief.get("evidence") or {}).get("chart_facts") or {}).get("charts") or {}
    assert d12["D12"]["domain"]["life_area"]
    assert d12["D12"]["lagna"]["lord"] == "Mercury"
    assert brief["answer_blueprint"]["slots"][0]["slot"] == "direct prediction in this chart's life area"
    assert "Never open with planets" not in prompt
    assert "predict from that chart" in prompt
    assert "planet-by-planet placement list" in prompt
    assert "D12 predicts parents/elders/ancestry FROM this D12 packet" in prompt
    assert "D12 lagna: Gemini" in prompt
    assert "reply in english" not in prompt.lower()
    assert "same language and script as the USER QUESTION" in prompt


def test_composer_v3_follows_user_language_after_short_clarification():
    prompt = _build_instant_composer_prompt_v3(
        "apni",
        {
            "query_plan": {"answer_mode": "event_prediction", "category": "child"},
            "intent": {"answer_mode": "event_prediction", "category": "child"},
            "verdict": {"direction": "conditional"},
            "evidence": {},
            "answer_blueprint": {"slots": [{"slot": "direct real-life verdict"}]},
            "answer_contract": {},
            "recent_history": [
                {
                    "question": "Muje baby kab hoga ye janana ha",
                    "answer": "यह जानने के लिए कि संतान प्राप्ति कब होगी, क्या आप अपनी स्वयं की कुंडली के बारे में पूछ रहे हैं?",
                }
            ],
            "app_language_fallback": "english",
        },
        "english",
    )
    assert "reply in english" not in prompt.lower()
    assert "same language and script as the USER QUESTION" in prompt
    assert "never switch the user-facing answer to English" in prompt
    assert "apni" in prompt
    assert "Muje baby kab hoga ye janana ha" in prompt
