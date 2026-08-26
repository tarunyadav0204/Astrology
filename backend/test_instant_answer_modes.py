import os
import sys
import types
from datetime import datetime, timedelta

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)


def _stub_module(name: str, **attrs):
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    sys.modules[name] = mod
    return mod


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass


_stub_module("ai.parallel_chat.parallel_agent_payloads", build_parashari_agent_payload=lambda *args, **kwargs: {})
_stub_module("calculators.chart_calculator", ChartCalculator=_Dummy)
_stub_module("calculators.real_transit_calculator", RealTransitCalculator=_Dummy)
_stub_module("chat.chat_context_builder", ChatContextBuilder=_Dummy)
_stub_module("context_agents.base", AgentContext=_Dummy, ContextAgent=_Dummy)
_stub_module("shared.dasha_calculator", DashaCalculator=_Dummy)
_stub_module(
    "utils.admin_settings",
    CHAT_LLM_DEEPSEEK="deepseek",
    CHAT_LLM_GEMINI="gemini",
    get_instant_chat_llm_provider=lambda: "gemini",
    get_instant_chat_model=lambda: "stub-model",
)
# Keep real remedy-CTA helpers; only stub time resolution for period-window tests.
import utils.query_context as _qc_mod

_stub_module(
    "utils.query_context",
    resolve_query_now=lambda qc=None: __import__("datetime").datetime(2026, 5, 1, 12, 0, 0),
    normalize_query_context=_qc_mod.normalize_query_context,
    is_remedy_followup_request=_qc_mod.is_remedy_followup_request,
    is_remedy_chain_question=_qc_mod.is_remedy_chain_question,
    clamp_remedy_modes_on_intent=_qc_mod.clamp_remedy_modes_on_intent,
    ensure_remedy_cta_next_action=_qc_mod.ensure_remedy_cta_next_action,
    NO_INLINE_REMEDY_PLAN_RULE=_qc_mod.NO_INLINE_REMEDY_PLAN_RULE,
    NEXT_ACTION_NONE_IN_REMEDY_MODE=_qc_mod.NEXT_ACTION_NONE_IN_REMEDY_MODE,
    apply_normal_answer_remedy_guards=_qc_mod.apply_normal_answer_remedy_guards,
    REMEDY_CARD_FOMO_COPY_RULES=_qc_mod.REMEDY_CARD_FOMO_COPY_RULES,
)

from ai.evidence_planner_schema import normalize_evidence_plan
from ai.intent_router import IntentRouter, apply_transit_timing_guards
from chat.instant_chat_pipeline import (
    _all_house_activation_from_levels,
    _build_answer_mode_contract,
    _build_month_tone_signals,
    _build_person_profile_axes,
    _build_target_chart_context,
    _divisional_specific_lines,
    _fallback_target_subject,
    _infer_answer_mode,
    _looks_like_open_ended_life_event_when,
    _mode_selection_from_intent,
    _is_conversational_non_question,
    _instant_lifetime_event_year_clarification_response,
    _merge_adjacent_low_score_event_periods,
    _normalize_event_category,
    _normalize_question_text,
    _normalize_instant_evidence,
    _period_anchor_datetime,
    _planet_aspect_number_from,
    _planet_aspects_house_from,
    _is_dasha_calculator_fallback_payload,
    _authoritative_active_dasha_context,
    _build_named_dasha_lookup_from_evidence_plan,
    _build_event_timing_verdict,
    _build_instant_composer_context,
    _compact_context_for_speech,
    _compact_divisional_support,
    _build_instant_prompt,
    _event_divisional_category,
    _polish_speech_event_answer,
    _risk_specific_lines,
    _resolve_period_window,
    _rotate_instant_parashari_for_target,
    _target_context_as_birth_summary,
)


def test_remedy_blueprint_reaches_verdict_first_composer():
    remedy_blueprint = {
        "question_focus": "career remedies",
        "candidate_planets": [{"planet": "Saturn", "house": 2}],
        "priority_order": ["Saturn", "Rahu"],
        "remedy_sections": {
            "house_expression": [
                {
                    "action": "Keep a written record of financial commitments",
                    "frequency": "daily",
                    "why": "Saturn is active in the second house",
                }
            ],
            "mantras": [{"planet": "Saturn", "mantra": "Om Sham Shanicharaya Namah"}],
            "charity": [{"planet": "Saturn", "action": "Support elderly workers on Saturdays"}],
        },
        "caution": "Use one or two remedies consistently instead of starting many at once.",
    }
    context = _build_instant_composer_context(
        {
            "intent_summary": {
                "category": "career",
                "answer_mode": "remedy_action",
                "language": "english",
            },
            "normalized_evidence": {
                "remedy_blueprint": remedy_blueprint,
                "question_focus": "career remedies",
                "remedy_sections": remedy_blueprint["remedy_sections"],
                "caution": remedy_blueprint["caution"],
            },
            "birth_summary": {"name": "Test"},
        },
        {
            "query_plan": {
                "category": "career",
                "answer_mode": "remedy_action",
                "language": "english",
            },
            "verdict": {"direction": "supported", "confidence": "medium"},
            "answer_spec": {"composer_word_target": "120-180 words"},
        },
    )

    assert context["context_profile"] == "instant_composer_v3"
    assert context["evidence"]["remedy_blueprint"] == remedy_blueprint
    assert context["evidence"]["remedy_sections"]["mantras"][0]["planet"] == "Saturn"
    assert context["evidence"]["caution"] == remedy_blueprint["caution"]
    prompt = _build_instant_prompt("Show my career remedies", context, "english")
    assert "This is an explicit remedy request. Give remedies" in prompt
    assert "Do not add remedies" not in prompt
    assert "exactly three prioritized, concrete remedies" in prompt


def test_remedy_blueprint_reaches_speech_compact_context():
    context = _compact_context_for_speech(
        {
            "intent_summary": {"category": "career", "answer_mode": "remedy_action"},
            "normalized_evidence": {
                "remedy_blueprint": {"priority_order": ["Saturn"]},
                "remedy_sections": {"mantras": [{"planet": "Saturn"}]},
                "caution": "Keep gemstone advice optional.",
            },
        }
    )

    normalized = context["normalized_evidence"]
    assert normalized["remedy_blueprint"]["priority_order"] == ["Saturn"]
    assert normalized["remedy_sections"]["mantras"][0]["planet"] == "Saturn"
    assert normalized["caution"] == "Keep gemstone advice optional."


def test_instant_dialogue_state_persists_llm_owned_clarification():
    router = IntentRouter.__new__(IntentRouter)
    result = router._finalize_instant_dialogue_state(
        {
            "status": "CLARIFY",
            "clarification_question": "Who are you referring to?",
            "extracted_context": {},
            "dialogue_state": {
                "request_summary": "User asks whether an unresolved person will return",
                "known_facts": {"event": "return"},
                "unresolved_facts": ["person's relationship to the native"],
                "corrections": [],
                "ready_to_calculate": False,
            },
        }
    )

    state = result["extracted_context"]["instant_dialogue"]
    assert result["status"] == "CLARIFY"
    assert state["known_facts"] == {"event": "return"}
    assert state["last_clarification_question"] == "Who are you referring to?"
    assert state["ready_to_calculate"] is False


def test_instant_dialogue_state_accepts_llm_correction_and_next_question():
    router = IntentRouter.__new__(IntentRouter)
    prior = {
        "known_facts": {"event": "return", "person": "boyfriend"},
        "unresolved_facts": ["person's relationship to the native"],
        "corrections": [],
        "ready_to_calculate": False,
        "last_clarification_question": "Are you asking about a boyfriend?",
    }
    result = router._finalize_instant_dialogue_state(
        {
            "status": "CLARIFY",
            "clarification_question": "Is this your first marriage?",
            "extracted_context": {},
            "dialogue_state": {
                "request_summary": "User asks whether her husband will return",
                "known_facts": {"event": "return", "person": "husband"},
                "unresolved_facts": ["marriage order"],
                "corrections": ["The person is husband, not boyfriend"],
                "ready_to_calculate": False,
            },
        },
        prior_dialogue_state=prior,
    )

    state = result["dialogue_state"]
    assert state["known_facts"]["person"] == "husband"
    assert state["corrections"] == ["The person is husband, not boyfriend"]
    assert state["unresolved_facts"] == ["marriage order"]


def test_instant_dialogue_state_blocks_inconsistent_ready_response():
    router = IntentRouter.__new__(IntentRouter)
    prior = {
        "known_facts": {"event": "return"},
        "unresolved_facts": ["person identity"],
        "corrections": [],
        "ready_to_calculate": False,
        "last_clarification_question": "Who do you mean by he?",
    }
    result = router._finalize_instant_dialogue_state(
        {
            "status": "READY",
            "clarification_question": "",
            "extracted_context": {},
            "dialogue_state": {
                "known_facts": {"event": "return"},
                "unresolved_facts": ["person identity"],
                "ready_to_calculate": False,
            },
        },
        prior_dialogue_state=prior,
    )

    assert result["status"] == "CLARIFY"
    assert result["clarification_question"] == "Who do you mean by he?"


def test_new_request_discards_abandoned_clarification_state():
    router = IntentRouter.__new__(IntentRouter)
    prior = {
        "request_summary": "Choose marriage timing or future spouse career",
        "known_facts": {"topic": "marriage"},
        "unresolved_facts": ["chosen_topic"],
        "corrections": [],
        "ready_to_calculate": False,
        "last_clarification_question": "Which question would you like to ask first?",
        "pending_choice_kind": "compound_plan",
        "answer_mode": "compound_plan",
    }
    result = router._finalize_instant_dialogue_state(
        {
            "turn_relation": "new_request",
            "status": "READY",
            "answer_mode": "topic_reading",
            "category": "career",
            "extracted_context": {},
            "dialogue_state": {
                "request_summary": "Career remedy guidance",
                "known_facts": {"topic": "career", "requested_action": "remedies"},
                "unresolved_facts": [],
                "corrections": [],
                "ready_to_calculate": True,
            },
        },
        prior_dialogue_state=prior,
    )

    assert result["status"] == "READY"
    assert result["category"] == "career"
    assert result["dialogue_state"]["known_facts"] == {
        "topic": "career",
        "requested_action": "remedies",
    }
    assert "last_clarification_question" not in result["dialogue_state"]
    assert "pending_choice_kind" not in result["dialogue_state"]


def test_instant_dialogue_state_allows_ready_only_after_llm_resolves_facts():
    router = IntentRouter.__new__(IntentRouter)
    result = router._finalize_instant_dialogue_state(
        {
            "status": "READY",
            "clarification_question": "",
            "extracted_context": {},
            "dialogue_state": {
                "request_summary": "First marriage husband return after separation",
                "known_facts": {
                    "person": "husband",
                    "marriage_order": "first",
                    "current_status": "separated",
                },
                "unresolved_facts": [],
                "corrections": [],
                "ready_to_calculate": True,
                "readiness_reason": "Relationship and event are clear",
            },
        }
    )

    assert result["status"] == "READY"
    assert result["dialogue_state"]["ready_to_calculate"] is True
    assert "last_clarification_question" not in result["dialogue_state"]


def test_instant_router_finalizer_preserves_llm_semantics_without_text_rules():
    router = IntentRouter.__new__(IntentRouter)
    result = router._finalize_instant_router_result(
        {
            "status": "CLARIFY",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "category": "relationship",
            "context_type": "birth",
            "needs_transits": False,
            "divisional_charts": ["D1", "D9"],
            "extracted_context": {"subject": "unresolved"},
            "evidence_plan": {},
        },
        current_year=2026,
        normalized_query_context=None,
    )

    assert result["status"] == "CLARIFY"
    assert result["mode"] == "ANALYZE_TOPIC_POTENTIAL"
    assert result["category"] == "relationship"
    assert result["needs_transits"] is False
    assert result["divisional_charts"] == ["D1", "D9"]


def test_evidence_plan_normalizes_dasha_lookup_enums():
    plan = normalize_evidence_plan(
        {
            "question_parts": [
                {
                    "part_id": "p1",
                    "text": "When will my Mercury dasha start?",
                    "intent_families": ["Factual_Chart_Lookup"],
                    "life_domain": "General",
                    "subject": "Self",
                    "timeframe": {"kind": "Open_Future", "granularity": "Exact_Fact"},
                    "confidence": "High",
                }
            ],
            "evidence_needs": [
                {
                    "need_id": "n1",
                    "kind": "Dasha_Timeline_Lookup",
                    "system": "Vimshottari",
                    "topic": "General",
                    "supports_parts": ["p1"],
                    "params": {"planet": "mercury", "level": "MAHADASHA", "operation": "Find_Start_End"},
                    "priority": "Required",
                }
            ],
        },
        question="When will my Mercury dasha start?",
    )

    assert plan["question_parts"][0]["intent_families"] == ["factual_chart_lookup"]
    assert plan["question_parts"][0]["timeframe"]["kind"] == "open_future"
    assert plan["question_parts"][0]["timeframe"]["granularity"] == "exact_fact"
    need = plan["evidence_needs"][0]
    assert need["kind"] == "dasha_timeline_lookup"
    assert need["system"] == "vimshottari"
    assert need["params"]["planet"] == "Mercury"
    assert need["params"]["level"] == "mahadasha"
    assert need["params"]["operation"] == "find_start_end"


def test_evidence_plan_preserves_retrospective_timing_enums():
    plan = normalize_evidence_plan(
        {
            "question_parts": [{
                "part_id": "p1",
                "text": "When did I get married?",
                "intent_families": ["event_timing"],
                "life_domain": "marriage",
                "event_profile": "marriage",
                "subject": "self",
                "timeframe": {"kind": "open_past"},
            }],
            "evidence_needs": [
                {
                    "kind": "historical_dasha_event_windows",
                    "system": "vimshottari",
                    "topic": "marriage",
                    "supports_parts": ["p1"],
                },
                {
                    "kind": "historical_transit_event_windows",
                    "system": "transits",
                    "topic": "marriage",
                    "supports_parts": ["p1"],
                },
            ],
        },
        question="When did I get married?",
    )

    assert plan["question_parts"][0]["timeframe"]["kind"] == "open_past"
    assert [need["kind"] for need in plan["evidence_needs"]] == [
        "historical_dasha_event_windows",
        "historical_transit_event_windows",
    ]


def test_evidence_plan_dasha_lookup_for_future_mercury_mahadasha():
    as_of = datetime(2026, 7, 9, 16, 51, 38)
    current_dashas = {
        "maha_dashas": [
            {"planet": "Saturn", "start": datetime(2018, 9, 26), "end": datetime(2037, 9, 26) - timedelta(seconds=1), "years": 19},
            {"planet": "Mercury", "start": datetime(2037, 9, 26), "end": datetime(2054, 9, 26) - timedelta(seconds=1), "years": 17},
        ]
    }
    evidence_plan = {
        "evidence_needs": [
            {
                "need_id": "n1",
                "kind": "dasha_timeline_lookup",
                "system": "vimshottari",
                "topic": "general",
                "supports_parts": ["p1"],
                "params": {"planet": "Mercury", "level": "mahadasha", "operation": "find_start_end"},
                "priority": "required",
            }
        ]
    }

    lookup = _build_named_dasha_lookup_from_evidence_plan(
        evidence_plan=evidence_plan,
        current_dashas=current_dashas,
        as_of=as_of,
    )
    assert lookup["matches"][0]["planet"] == "Mercury"
    assert lookup["matches"][0]["level"] == "mahadasha"
    assert lookup["matches"][0]["relation_to_as_of"] == "future"
    assert lookup["matches"][0]["start"] == "2037-09-26"
    assert "Mercury Mahadasha starts on 2037-09-26" in lookup["matches"][0]["authoritative_fact"]


def test_speech_compact_context_keeps_event_horizon_scan():
    instant_context = {
        "intent_summary": {"answer_mode": "event_prediction", "focus_houses": [7, 2, 11]},
        "current_dashas": {"as_of": "2026-07-10", "levels": {"md": {"planet": "Saturn"}}},
        "instant_parashari": {
            "forward_event_dasha_scan": {
                "horizon_days": 1095,
                "horizon_end": "2029-07-09",
                "focus_houses": [7, 2, 11],
                "periods": [
                    {
                        "start": "2028-08-24",
                        "end": "2028-09-23",
                        "mahadasha": "Saturn",
                        "antardasha": "Jupiter",
                        "pratyantardasha": "Saturn",
                        "relevance_score": 66,
                        "activated_focus_houses": [2, 7, 11],
                        "why": "MD Saturn rules focus house(s) [7]",
                    }
                ],
            },
            "horizon_dasha_segments": {
                "enabled": True,
                "label": "next 3 years",
                "focus_houses": [7, 2, 11],
                "segments": [
                    {
                        "start": "2028-08-24",
                        "end": "2028-09-23",
                        "mahadasha": "Saturn",
                        "antardasha": "Jupiter",
                        "pratyantardasha": "Saturn",
                        "relevance_score": 66,
                        "activated_focus_houses": [2, 7, 11],
                        "why": "MD Saturn rules focus house(s) [7]",
                    }
                ],
            },
        },
        "normalized_evidence": {
            "forward_event_dasha_scan": {
                "horizon_days": 1095,
                "horizon_end": "2029-07-09",
                "periods": [
                    {
                        "start": "2028-08-24",
                        "end": "2028-09-23",
                        "mahadasha": "Saturn",
                        "antardasha": "Jupiter",
                        "pratyantardasha": "Saturn",
                        "relevance_score": 66,
                    }
                ],
            },
            "horizon_dasha_segments": {
                "enabled": True,
                "segments": [
                    {
                        "start": "2028-08-24",
                        "end": "2028-09-23",
                        "mahadasha": "Saturn",
                        "antardasha": "Jupiter",
                        "pratyantardasha": "Saturn",
                        "relevance_score": 66,
                    }
                ],
            },
        },
    }

    compact = _compact_context_for_speech(instant_context)
    assert len(compact["normalized_evidence"]["forward_event_dasha_scan"]["periods"]) == 1
    assert len(compact["normalized_evidence"]["horizon_dasha_segments"]["segments"]) == 1
    assert "forward_event_dasha_scan" not in compact["instant_parashari"]
    assert "horizon_dasha_segments" not in compact["instant_parashari"]


def test_event_timing_verdict_respects_small_score_delta():
    verdict = _build_event_timing_verdict(
        category="marriage",
        forward_scan_periods=[
            {
                "start": "2026-07-10",
                "end": "2026-08-09",
                "mahadasha": "Saturn",
                "antardasha": "Rahu",
                "pratyantardasha": "Saturn",
                "time_status": "current",
                "relevance_score": 64,
                "activated_focus_houses": [2, 5, 7, 11],
                "why": "MD Saturn rules focus house(s) [7]; AD Rahu occupies focus house 2",
            },
            {
                "start": "2028-08-24",
                "end": "2028-09-23",
                "mahadasha": "Saturn",
                "antardasha": "Jupiter",
                "pratyantardasha": "Saturn",
                "time_status": "future",
                "relevance_score": 66,
                "activated_focus_houses": [2, 5, 7, 11],
                "why": "MD Saturn rules focus house(s) [7]; AD Jupiter occupies focus house 2",
            },
        ],
        horizon_segments=[],
        current_chain_rows=[
            {"level": "MD", "planet": "Saturn", "natal_house": 2, "lordships": [7, 8]},
            {
                "level": "AD",
                "planet": "Rahu",
                "natal_house": 2,
                "lordships": [],
                "conjunctions": [{"planet": "Mars"}, {"planet": "Jupiter"}],
            },
        ],
        timing_policy={},
    )

    assert verdict["score_delta"] == 2
    assert verdict["comparison"] == "current_active_future_slightly_cleaner"
    assert verdict["answer_event_label"] == "marriage"
    assert "Do not imply current potential is absent" in verdict["answer_rule"]
    assert any("Rahu" in item for item in verdict["pressure_factors"])


def test_event_timing_verdict_adds_house_claim_contract():
    verdict = _build_event_timing_verdict(
        category="promotion",
        forward_scan_periods=[
            {
                "start": "2028-04-22",
                "end": "2028-05-22",
                "mahadasha": "Saturn",
                "antardasha": "Jupiter",
                "pratyantardasha": "Jupiter",
                "time_status": "future",
                "relevance_score": 68,
                "activated_focus_houses": [2, 6, 11],
                "why": "AD Jupiter rules focus house(s) [6]; AD Jupiter aspects focus house 11 from natal",
            }
        ],
        horizon_segments=[],
        current_chain_rows=[],
        timing_policy={},
    )

    contract = verdict["claim_contract"]["best_future_window"]
    assert contract["activated_focus_houses"] == [2, 6, 11]
    assert verdict["answer_event_label"] == "promotion"
    assert 10 in contract["inactive_focus_houses"]
    assert any(row["house"] == 6 and "work routines" in row["theme"] for row in contract["allowed_house_themes"])
    assert "Do not convert a possible focus house" in verdict["claim_contract"]["house_claim_rule"]
    assert any("named domain house" in row for row in verdict["forbidden_answer_moves"])


def test_event_prediction_prompt_contains_claim_discipline():
    prompt = _build_instant_prompt(
        "When will I get promotion?",
        {
            "intent_summary": {
                "category": "promotion",
                "mode": "LIFESPAN_EVENT_TIMING",
                "answer_mode": "event_prediction",
            },
            "instant_parashari": {},
            "normalized_evidence": {
                "answer_mode_contract": {"answer_mode": "event_prediction"},
                "event_timing_verdict": {
                    "answer_event_label": "promotion",
                    "claim_contract": {
                        "best_future_window": {
                            "activated_focus_houses": [2, 6, 11],
                            "inactive_focus_houses": [10],
                        }
                    }
                },
            },
        },
        "english",
        speech_mode=True,
    )

    assert "claim_contract" in prompt
    assert "answer_event_label" in prompt
    assert "name that event plainly in the first sentence" in prompt
    assert "sound like a live guide" in prompt
    assert "astrological indicators suggest" in prompt
    assert "not active in a timing window unless" in prompt
    assert "do not say \"career house\"" in prompt.lower()


def test_instant_chat_prompt_closes_as_a_conversation_not_an_upsell():
    prompt = _build_instant_prompt(
        "What does my current dasha mean for career?",
        {
            "intent_summary": {
                "category": "career",
                "mode": "ANALYZE_TOPIC_POTENTIAL",
                "answer_mode": "topic_reading",
            },
            "instant_parashari": {},
            "normalized_evidence": {},
        },
        "english",
    )

    assert "exactly one short, natural question" in prompt
    assert "Is something at work worrying you right now" in prompt
    assert "a deeper reading would be better" not in prompt
    assert "Use everyday language people actually use" in prompt
    assert "Use daily-use language, not consultant language" in prompt
    assert "Create a gentle sense that the current situation is worth paying attention to" in prompt
    assert "Never manufacture FOMO" in prompt
    assert "answer the user's question fully" in prompt


def test_instant_year_career_answer_contract_is_user_facing_not_a_house_dump():
    contract = _build_answer_mode_contract(
        "timing_window",
        "career",
        {"kind": "year", "span_days": 365},
        "current",
    )
    skeleton = contract["answer_skeleton"]
    assert skeleton.startswith("Plain-language year verdict")
    assert "Concrete likely outcomes" in skeleton
    assert "At most one compact astrological reason" in skeleton
    assert "MD/AD/PD" not in skeleton

    prompt = _build_instant_prompt(
        "How is my career this year?",
        {
            "intent_summary": {
                "category": "career",
                "mode": "ANALYZE_TOPIC_POTENTIAL",
                "answer_mode": "timing_window",
                "period_window": {"kind": "year", "span_days": 365},
            },
            "instant_parashari": {},
            "normalized_evidence": {
                "answer_mode_contract": contract,
                "active_areas": [
                    {"house": 2, "theme": "income and financial security"},
                    {"house": 6, "theme": "workload and professional tasks"},
                    {"house": 11, "theme": "gains, recognition, and networks"},
                ],
            },
        },
        "english",
    )

    assert "The astrology context is evidence, not the answer" in prompt
    assert "Never respond mainly with dasha date ranges" in prompt
    assert "Translate house themes into ordinary outcomes" in prompt
    assert "no more than one sentence of astrological proof" in prompt


def test_speech_event_answer_polish_replaces_placeholders_and_jargon():
    polished = _polish_speech_event_answer(
        "While your current period is active, it is not the primary window for this event. "
        "The house of fortune and dharma supports these matters.",
        {
            "intent_summary": {"category": "child"},
            "normalized_evidence": {
                "event_timing_verdict": {
                    "answer_event_label": "having a child",
                }
            },
        },
    )

    assert "this event" not in polished.lower()
    assert "these matters" not in polished.lower()
    assert "fortune and dharma" not in polished.lower()
    assert "having a child" in polished
    assert "long-range support" in polished


def test_event_category_ontology_keeps_promotion_and_childbirth_specific():
    assert _normalize_event_category("promotion") == "promotion"
    assert _normalize_event_category("job") == "job"
    assert _normalize_event_category("childbirth") == "progeny"
    assert _normalize_event_category("conception") == "progeny"
    assert _event_divisional_category("progeny") == "child"
    assert _event_divisional_category("promotion") == "promotion"


def test_compact_divisional_support_keeps_requested_and_available_charts():
    compact = _compact_divisional_support(
        {
            "requested_charts": ["D1", "D9", "D10", "Karkamsa"],
            "available_charts": ["D9", "D10", "Karkamsa"],
            "topic": {
                "support": "supportive",
                "codes": ["D10", "Karkamsa", "D9"],
                "charts": {
                    "D10": {
                        "support": "supportive",
                        "best": [10, 11],
                        "hard": [],
                        "rows": [{"h": 10, "lord": "Sun", "band": "supportive"}],
                    }
                },
            },
        }
    )

    assert compact["requested_charts"] == ["D1", "D9", "D10", "Karkamsa"]
    assert "D10" in compact["available_charts"]
    assert compact["topic"]["charts"]["D10"]["rows"][0]["h"] == 10


def test_infer_answer_mode_for_explanation():
    mode = _infer_answer_mode(
        "You said Rahu activates my 10th house. How exactly?",
        {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "career"},
        [{"question": "career", "response": "Rahu activates 10th"}],
    )
    assert mode == "explanation_mechanism"


def test_infer_answer_mode_named_varga_uses_llm_chart_focus_not_question_language():
    hindi = _infer_answer_mode(
        "मेरी द्वादशांश कुंडली समझाओ",
        {
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "category": "family",
            "answer_mode": "topic_reading",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D12",
                "explicit": True,
                "requested": ["D12"],
            },
        },
        [],
    )
    assert hindi == "factual_chart_lookup"


def test_infer_answer_mode_does_not_keyword_match_english_d12():
    mode = _infer_answer_mode(
        "Explain my D12 chart",
        {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "family"},
        [],
    )
    assert mode == "topic_reading"


def test_infer_answer_mode_named_varga_this_year_keeps_llm_timing():
    mode = _infer_answer_mode(
        "इस साल मेरा दशमांश कैसा है?",
        {
            "mode": "PREDICT_PERIOD_OUTLOOK",
            "category": "career",
            "answer_mode": "timing_window",
            "needs_transits": True,
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D10",
                "explicit": True,
                "requested": ["D10"],
            },
        },
        [],
    )
    assert mode == "timing_window"


def test_mode_selection_honors_llm_factual_chart_lookup_in_any_language():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "factual_chart_lookup",
            "category": "family",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "target_subject_key": "self",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "D12",
                "explicit": True,
                "requested": ["D12"],
            },
        },
        "मेरी D12 कुंडली समझाओ",
    )
    assert selection is not None
    assert selection["answer_mode"] == "factual_chart_lookup"


def test_mode_selection_coerces_topic_reading_from_llm_chart_focus():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "topic_reading",
            "category": "family",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "chart_focus": {
                "kind": "chart_specific",
                "primary": "Karkamsa",
                "explicit": True,
                "requested": ["Karkamsa"],
            },
        },
        "mera karakamsha chart batao",
    )
    assert selection is not None
    assert selection["answer_mode"] == "factual_chart_lookup"


def test_mode_selection_does_not_parse_question_text_for_chart_facts():
    selection = _mode_selection_from_intent(
        {
            "answer_mode": "topic_reading",
            "category": "family",
            "mode": "ANALYZE_TOPIC_POTENTIAL",
            "target_subject_key": "self",
        },
        "Explain my D12 chart",
    )
    assert selection is not None
    assert selection["answer_mode"] == "topic_reading"


def test_build_answer_mode_contract_for_factual_chart_lookup():
    contract = _build_answer_mode_contract(
        "factual_chart_lookup",
        "family",
        {"kind": "current", "span_days": 1},
        "current",
    )
    assert contract["answer_mode"] == "factual_chart_lookup"
    assert "chart_facts" in contract["primary_evidence"]
    assert "current dasha dominating the answer" in contract["avoid_drift"]
    assert "Direct prediction" in contract["answer_skeleton"]


def test_infer_answer_mode_for_trait_question():
    mode = _infer_answer_mode(
        "Tell me about my behaviour",
        {"mode": "ANALYZE_PERSONALITY", "category": "general"},
        [],
    )
    assert mode == "trait_nature"


def test_build_answer_mode_contract_for_trait_nature_uses_personality_axes():
    contract = _build_answer_mode_contract(
        "trait_nature",
        "general",
        {"kind": "current", "span_days": 1},
        "current",
    )
    assert contract["answer_mode"] == "trait_nature"
    assert "personality_axes" in contract["primary_evidence"]
    assert "area_behavior_axes" in contract["primary_evidence"]
    assert "Core temperament" in contract["answer_skeleton"]
    assert "Two area-specific behavior patterns" in contract["answer_skeleton"]
    assert "current dasha dominating the answer" in contract["avoid_drift"]


def test_infer_answer_mode_for_period_window():
    mode = _infer_answer_mode(
        "How will October 2026 be for me?",
        {"mode": "PREDICT_PERIOD_OUTLOOK", "category": "general", "needs_transits": True},
        [],
    )
    assert mode == "timing_window"


def test_infer_answer_mode_for_tomorrow_outlook_questions():
    for question in ("What will be happen tomorrow?", "How will be my day tomorrow?"):
        mode = _infer_answer_mode(
            question,
            {"mode": "PREDICT_DAILY", "category": "general", "needs_transits": True},
            [],
        )
        assert mode == "timing_window"


def test_resolve_period_window_for_tomorrow_day_and_next_year():
    now = datetime(2026, 7, 10, 12, 0, 0)
    tomorrow = _resolve_period_window(
        {
            "mode": "PREDICT_DAILY",
            "dasha_as_of": "2026-07-11",
            "extracted_context": {
                "specific_date": "2026-07-11",
                "specific_date_basis": "relative_user_day",
                "timeframe": "tomorrow",
            },
        },
        now,
        "How will be my day tomorrow?",
    )
    assert tomorrow["kind"] == "day"
    assert tomorrow["start"] == "2026-07-11"
    assert tomorrow["end"] == "2026-07-11"
    assert tomorrow["use_pd"] is True
    assert tomorrow["use_sk_pr"] is True

    next_year = _resolve_period_window(
        {
            "mode": "PREDICT_PERIOD_OUTLOOK",
            "extracted_context": {"timeframe": "next year"},
        },
        now,
        "How will be my next year?",
    )
    assert next_year["kind"] == "window"
    assert next_year["start"] == "2027-01-01"
    assert next_year["end"] == "2027-12-31"
    assert next_year["use_pd"] is True
    assert next_year["use_sk_pr"] is False


def test_resolve_period_window_uses_router_month_map_without_year_word():
    now = datetime(2026, 7, 10, 12, 0, 0)
    window = _resolve_period_window(
        {
            "mode": "PREDICT_PERIOD_OUTLOOK",
            "extracted_context": {"timeframe": "october"},
            "transit_request": {"yearMonthMap": {"2026": ["October"]}},
        },
        now,
        "How will October be?",
    )
    assert window["kind"] == "window"
    assert window["start"] == "2026-10-01"
    assert window["end"] == "2026-10-31"
    assert window["use_sk_pr"] is True


def test_daily_transit_guard_keeps_tomorrow_as_daily():
    result = {
        "mode": "PREDICT_DAILY",
        "category": "general",
        "daily_intent_confirmed": True,
        "extracted_context": {
            "specific_date": "2026-07-11",
            "specific_date_basis": "relative_user_day",
            "timeframe": "tomorrow",
        },
    }
    apply_transit_timing_guards(
        result,
        "What will be happen tomorrow?",
        current_year=2026,
        now=datetime(2026, 7, 10, 12, 0, 0),
    )
    assert result["mode"] == "PREDICT_DAILY"
    assert result["dasha_as_of"] == "2026-07-11"
    assert result["needs_transits"] is True
    assert result["transit_request"]["yearMonthMap"] == {"2026": ["July"]}


def test_build_answer_mode_contract_for_relationship_person():
    contract = _build_answer_mode_contract(
        "relationship_person",
        "spouse",
        {"kind": "current", "span_days": 1},
        "current",
    )
    assert contract["answer_mode"] == "relationship_person"
    assert "person_profile_axes" in contract["primary_evidence"]
    assert "target_subject" in contract["primary_evidence"]
    assert "target_chart_context" in contract["primary_evidence"]
    assert "current-period narrative unless asked" in contract["avoid_drift"]
    assert "native's ascendant" in " ".join(contract["avoid_drift"])


def test_fallback_target_subject_handles_second_child_and_younger_brother():
    second_child = _fallback_target_subject("What is my second child's nature?")
    younger_brother = _fallback_target_subject("Tell me about my younger brother")
    assert second_child["key"] == "second_child"
    assert second_child["base_house"] == 7
    assert younger_brother["key"] == "younger_brother"
    assert younger_brother["base_house"] == 3


def test_build_person_profile_axes_uses_target_house_not_native_lagna():
    axes = _build_person_profile_axes(
        {
            "house_lordships": {
                "Moon": [1],
                "Sun": [2],
                "Mercury": [3, 12],
                "Venus": [4, 11],
                "Mars": [5, 10],
                "Jupiter": [6, 9],
                "Saturn": [7, 8],
            },
            "key_planets": {
                "Moon": {"sign": "Libra", "house": 4},
                "Sun": {"sign": "Pisces", "house": 9},
                "Mercury": {"sign": "Aquarius", "house": 8},
                "Venus": {"sign": "Taurus", "house": 11},
                "Mars": {"sign": "Leo", "house": 2},
                "Jupiter": {"sign": "Leo", "house": 2},
                "Saturn": {"sign": "Leo", "house": 2},
                "Rahu": {"sign": "Leo", "house": 2},
            },
        },
        {},
        {"key": "younger_brother", "label": "younger brother", "base_house": 3},
    )
    assert axes
    joined = " ".join(axes).lower()
    assert "younger brother" in joined
    assert "key house is 3" in joined


def test_build_target_chart_context_rotates_houses_for_target():
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        {
            "key_planets": {
                "Saturn": {"sign": "Leo", "house": 2},
                "Moon": {"sign": "Libra", "house": 4},
            }
        },
        {
            "Jupiter": {"sign": "Gemini", "house_from_lagna": 12},
        },
        {"key": "younger_brother", "label": "younger brother", "base_house": 3},
    )
    assert ctx["anchor_house"] == 3
    assert ctx["target_ascendant_sign"] == "Virgo"
    assert ctx["target_key_planets"]["Saturn"]["house"] == 12
    assert ctx["target_key_planets"]["Saturn"]["native_house"] == 2
    assert ctx["target_key_planets"]["Saturn"]["house_from_target"] == 12
    assert ctx["target_transits"]["Jupiter"]["house"] == 10
    assert ctx["target_transits"]["Jupiter"]["house_from_native"] == 12
    assert ctx["target_transits"]["Jupiter"]["house_from_target"] == 10


def test_target_context_as_birth_summary_uses_target_ascendant():
    ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        {
            "key_planets": {
                "Moon": {"sign": "Libra", "house": 4},
            }
        },
        {},
        {"key": "wife", "label": "wife", "base_house": 7},
    )
    summary = _target_context_as_birth_summary(ctx)
    assert summary["ascendant"]["sign"] == "Capricorn"
    assert summary["moon"]["house"] == 10


def test_rotate_instant_parashari_for_target_reanchors_houses():
    target_ctx = _build_target_chart_context(
        {"ascendant": {"sign": "Cancer"}},
        {
            "key_planets": {
                "Saturn": {"sign": "Leo", "house": 2},
                "Moon": {"sign": "Libra", "house": 4},
            }
        },
        {
            "Saturn": {"sign": "Pisces", "house_from_lagna": 9},
        },
        {"key": "wife", "label": "wife", "base_house": 7},
    )
    rotated = _rotate_instant_parashari_for_target(
        {
            "focus_houses": [1, 6, 8, 12],
            "active_dashas": {"md": {"p": "Saturn", "rh": [7, 8], "h": 2, "ahs": [2, 4, 8, 11]}},
            "active_dashas_formatted": {"md": {"planet": "Saturn", "natal_house": 2, "natal_sign": "Leo", "lordships": [7, 8]}},
            "house_activation": {"2": {"r": [], "o": ["md"], "a": ["md"]}, "8": {"r": ["md"], "o": [], "a": ["md"]}},
            "transit_pressure": {"dp": [{"tp": "Saturn", "np": "Mercury", "th": 9, "nh": 8, "at": "9th_house"}]},
            "top_supports": ["MD runs through Saturn from house 2, linking houses 7, 8."],
            "top_risks": ["Health pattern is tied to house 8."],
        },
        target_ctx,
        [1, 6, 8, 12],
    )
    assert rotated["active_dashas_formatted"]["md"]["natal_house"] == 8
    assert rotated["active_dashas"]["md"]["h"] == 8
    assert rotated["active_dashas"]["md"]["rh"] == [1, 2]
    assert rotated["transit_pressure"]["dp"][0]["th"] == 3
    assert rotated["transit_pressure"]["dp"][0]["nh"] == 2


def test_build_answer_mode_contract_for_timing_window_prefers_ranked_areas():
    contract = _build_answer_mode_contract(
        "timing_window",
        "general",
        {"kind": "window", "span_days": 31},
        "future",
    )
    assert contract["answer_mode"] == "timing_window"
    assert "dasha_level_effects" in contract["primary_evidence"]
    assert "dasha_chain_synthesis" in contract["primary_evidence"]
    assert "active_areas" in contract["primary_evidence"]
    assert "MD/AD/PD" in contract["answer_skeleton"]
    assert "month_tone" in contract["secondary_evidence"]
    assert "whole-month prose from one-day fast-planet snapshots" in contract["avoid_drift"]


def test_timing_window_contract_specializes_day_and_year_outlooks():
    day_contract = _build_answer_mode_contract(
        "timing_window",
        "general",
        {"kind": "day", "span_days": 1, "use_sk_pr": True},
        "future",
    )
    assert "Exact date anchor" in day_contract["answer_skeleton"]
    assert "Sookshma/Prana" in day_contract["answer_skeleton"]
    assert "month/year generalization" in day_contract["avoid_drift"]

    year_contract = _build_answer_mode_contract(
        "timing_window",
        "general",
        {"kind": "window", "span_days": 365},
        "future",
    )
    assert "Year verdict" in year_contract["answer_skeleton"]
    assert "stronger and weaker phases" in year_contract["answer_skeleton"].lower()
    assert "one static dasha summary for the whole year" in year_contract["avoid_drift"]


def test_timing_policy_blocks_imminent_marriage_for_child():
    from chat.instant_chat_pipeline import _timing_policy_for_instant_event

    pol = _timing_policy_for_instant_event(age_years=10, life_stage="child", category="marriage")
    assert pol["life_stage"] == "child"
    assert any("legal marriage" in r for r in pol["restrictions"])


def test_build_answer_mode_contract_for_event_prediction_is_investigative():
    contract = _build_answer_mode_contract(
        "event_prediction",
        "career",
        {"kind": "window", "span_days": 365},
        "future",
    )
    assert contract["answer_mode"] == "event_prediction"
    assert "question-led yes bias" in contract["avoid_drift"]
    assert "timing_policy" in contract["primary_evidence"]
    assert "forward_event_dasha_scan" in contract["primary_evidence"]
    assert "horizon_dasha_segments" in contract["primary_evidence"]
    assert "next 3 years" in contract["answer_skeleton"]
    assert "Support vs obstruction vs uncertainty" in contract["answer_skeleton"]


def test_normalize_event_category_maps_rare_aliases():
    assert _normalize_event_category("property_sale") == "property"
    assert _normalize_event_category("travel_abroad") == "travel"
    assert _normalize_event_category("unknown_rare_thing") == "general"


def test_merge_adjacent_low_score_event_periods_collapses_contiguous_rows():
    rows = [
        {
            "start": "2026-01-01",
            "end": "2026-03-01",
            "mahadasha": "Saturn",
            "antardasha": "Mercury",
            "relevance_score": 2,
            "why": "weak link a",
        },
        {
            "start": "2026-03-02",
            "end": "2026-05-10",
            "mahadasha": "Saturn",
            "antardasha": "Ketu",
            "relevance_score": 1,
            "why": "weak link b",
        },
        {
            "start": "2026-05-11",
            "end": "2026-07-01",
            "mahadasha": "Saturn",
            "antardasha": "Venus",
            "relevance_score": 5,
            "why": "strong window",
        },
    ]
    merged = _merge_adjacent_low_score_event_periods(rows)
    assert len(merged) == 2
    assert merged[0]["antardasha"] == "Mercury->Ketu"
    assert merged[0]["merged_segments"] == 2
    assert "Low-support stretch:" in merged[0]["why"]
    assert merged[0]["period_strength"] == "background_weak"
    assert merged[0]["period_label"] == "background/weak period"


def test_instant_lifetime_event_year_clarification_skips_charge():
    res = _instant_lifetime_event_year_clarification_response("english", speech_mode=False)
    assert res["success"] is True
    assert "specific year" in res["response"].lower()
    assert "standard or premium" in res["response"].lower()
    assert res["skip_instant_credit_charge"] is True


def test_normalized_event_prediction_exposes_current_dasha_chain():
    norm = _normalize_instant_evidence(
        answer_mode="event_prediction",
        category="career",
        instant_parashari={
            "period_window": {"kind": "current", "use_pd": True},
            "time_relation": "current",
            "active_dashas": {},
            "top_supports": [],
            "top_risks": [],
            "activation_mechanisms": [],
            "dominant_houses": [],
            "divisional_support": {},
            "topic_signals": {},
            "transit_pressure": {},
            "forward_event_dasha_scan": {"periods": []},
            "horizon_dasha_segments": {"segments": []},
        },
        current_transits_formatted={},
        current_dashas_context={
            "md": {"planet": "Saturn"},
            "ad": {"planet": "Mercury"},
            "pd": {"planet": "Jupiter"},
        },
        birth_summary={},
        natal_snapshot={},
        relationship_target=None,
        target_chart_context=None,
    )
    assert (norm.get("current_timing") or {}).get("current_dasha_chain") == "Saturn > Mercury > Jupiter"
    assert "horizon_dasha_segments" in norm


def test_authoritative_active_dasha_context_uses_dasha_calculator_chain():
    rows = _authoritative_active_dasha_context(
        current_dashas={
            "mahadasha": {"planet": "Saturn"},
            "antardasha": {"planet": "Rahu"},
            "pratyantardasha": {"planet": "Saturn"},
            "sookshma": {"planet": "Mercury"},
            "prana": {"planet": "Moon"},
        },
        chart_data={
            "planets": {
                "Saturn": {"house": 10, "sign_name": "Aquarius"},
                "Rahu": {"house": 4, "sign_name": "Taurus"},
                "Mercury": {"house": 9, "sign_name": "Capricorn"},
                "Moon": {"house": 1, "sign_name": "Virgo"},
            }
        },
        house_lordships={"Saturn": [5, 6], "Rahu": [], "Mercury": [1, 10], "Moon": [11]},
        period_window={"use_sk_pr": False},
    )
    assert rows["md"]["planet"] == "Saturn"
    assert rows["ad"]["planet"] == "Rahu"
    assert rows["pd"]["planet"] == "Saturn"


def test_period_anchor_datetime_uses_now_when_inside_window():
    now_local = __import__("datetime").datetime(2026, 5, 4, 18, 0, 0)
    anchor = _period_anchor_datetime(
        {"kind": "window", "start": "2026-01-01", "end": "2026-12-31"},
        now_local,
    )
    assert anchor.strftime("%Y-%m-%d %H:%M:%S") == "2026-05-04 12:00:00"


def test_planet_aspects_house_from_vedic_offsets():
    assert _planet_aspects_house_from(2, 8, "Saturn") is True  # Saturn 7th
    assert _planet_aspects_house_from(2, 4, "Saturn") is True  # Saturn 3rd
    assert _planet_aspects_house_from(2, 11, "Saturn") is True  # Saturn 10th
    assert _planet_aspects_house_from(2, 6, "Saturn") is False


def test_instant_activation_excludes_rahu_ketu_fifth_and_ninth_aspects():
    for planet in ("Rahu", "Ketu"):
        assert _planet_aspects_house_from(2, 6, planet) is False  # 5th
        assert _planet_aspects_house_from(2, 8, planet) is True   # 7th
        assert _planet_aspects_house_from(2, 10, planet) is False  # 9th
        assert _planet_aspect_number_from(2, 6, planet) is None
        assert _planet_aspect_number_from(2, 8, planet) == 7
        assert _planet_aspect_number_from(2, 10, planet) is None


def test_is_dasha_calculator_fallback_payload_detects_sun_moon_mars_stub():
    assert _is_dasha_calculator_fallback_payload(
        {
            "mahadasha": {"planet": "Sun"},
            "antardasha": {"planet": "Moon"},
            "pratyantardasha": {"planet": "Mars"},
            "maha_dashas": [],
            "moon_lord": "Sun",
        }
    ) is True
    assert _is_dasha_calculator_fallback_payload(
        {
            "mahadasha": {"planet": "Saturn"},
            "antardasha": {"planet": "Rahu"},
            "pratyantardasha": {"planet": "Saturn"},
            "maha_dashas": [{"planet": "Saturn"}],
            "moon_lord": "Moon",
        }
    ) is False


def test_build_answer_mode_contract_for_problem_diagnosis_uses_target_context():
    contract = _build_answer_mode_contract(
        "problem_diagnosis",
        "health",
        {"kind": "window", "span_days": 30},
        "past",
    )
    assert contract["answer_mode"] == "problem_diagnosis"
    assert "target_subject" in contract["primary_evidence"]
    assert "target_chart_context" in contract["primary_evidence"]
    assert "cinematic injury narrative" in contract["avoid_drift"]
    assert "target-relative houses" in contract["answer_skeleton"]
    assert "dramatic injury phrasing" in contract["avoid_drift"]
    assert "overstated causal certainty" in contract["avoid_drift"]


def test_all_house_activation_from_levels_covers_full_chart():
    hi = _all_house_activation_from_levels(
        {
            "md": {"p": "Saturn", "rh": [7, 8], "h": 2, "ahs": [2, 4, 8, 11]},
            "ad": {"p": "Rahu", "rh": [], "h": 2, "ahs": [2, 6, 8, 10]},
            "pd": {"p": "Mercury", "rh": [3, 12], "h": 8, "ahs": [2, 8]},
        }
    )
    assert hi["2"]["o"] == ["md", "ad"]
    assert hi["7"]["r"] == ["md"]
    assert hi["10"]["a"] == ["ad"]
    assert hi["12"]["r"] == ["pd"]


def test_build_month_tone_signals_disabled_without_sun_contact():
    out = _build_month_tone_signals(
        {"Sun": {"sign": "Aries", "house_from_lagna": 10}},
        {
            "md": {"planet": "Saturn", "natal_house": 2, "natal_sign": "Leo"},
            "ad": {"planet": "Rahu", "natal_house": 2, "natal_sign": "Leo"},
        },
        [{"house": 2, "score": 10}, {"house": 8, "score": 8}, {"house": 7, "score": 6}],
        [],
        {"kind": "window", "start": "2026-05-01", "end": "2026-05-31"},
    )
    assert out["enabled"] is False
    assert out["signals"] == []


def test_build_month_tone_signals_enabled_for_dasha_activated_house():
    out = _build_month_tone_signals(
        {"Sun": {"sign": "Aries", "house_from_lagna": 10}},
        {
            "md": {"planet": "Saturn", "natal_house": 2, "natal_sign": "Leo"},
            "ad": {"planet": "Rahu", "natal_house": 2, "natal_sign": "Leo"},
        },
        [{"house": 2, "score": 10}, {"house": 8, "score": 8}, {"house": 7, "score": 6}],
        [{"house": 10, "links": ["AD Rahu aspects house 10"], "summary": "AD Rahu aspects house 10"}],
        {"kind": "window", "start": "2026-05-01", "end": "2026-05-31"},
    )
    assert out["enabled"] is True
    assert any("house 10" in signal for signal in out["signals"])


def test_divisional_specific_lines_extracts_concrete_detail():
    out = _divisional_specific_lines(
        {
            "topic": {
                "charts": {
                    "D9": {
                        "rows": [
                            {"h": 10, "lord": "Jupiter", "occ": ["Moon", "Sun"]},
                        ]
                    }
                }
            },
            "current_topic": {},
        },
        [],
    )
    assert out
    assert "D9" in out[0]
    assert "house 10" in out[0]


def test_event_prompt_prefers_compact_divisional_chart_mentions():
    prompt = _build_instant_prompt(
        "When will I get promotion?",
        {
            "intent_summary": {
                "category": "promotion",
                "mode": "LIFESPAN_EVENT_TIMING",
                "answer_mode": "event_prediction",
            },
            "normalized_evidence": {
                "divisional_specifics": [
                    "Topic divisional support in D10 specifically highlights house 1, lord Jupiter."
                ],
                "claim_gates": {"allow_divisional_mentions": True},
                "event_timing_verdict": {"answer_event_label": "promotion"},
            },
            "instant_parashari": {},
        },
        "english",
        speech_mode=True,
    )
    assert "mention one relevant chart code naturally" in prompt
    assert "D7, D9, D10, or Karkamsa" in prompt


def test_risk_specific_lines_extracts_house_mechanism():
    out = _risk_specific_lines(
        ["Financial risk factors are active."],
        [{"house": 8, "summary": "MD Saturn rules house 8; AD Rahu aspects house 8"}],
        {},
    )
    assert out
    assert "house 8" in out[0]


def test_timing_window_contract_keeps_claim_gate_support():
    contract = _build_answer_mode_contract(
        "timing_window",
        "finance",
        {"kind": "window", "span_days": 90},
        "future",
    )
    assert "month_tone" in contract["secondary_evidence"]


def test_normalize_question_text_treats_same_retry_as_same_question():
    assert _normalize_question_text("How will be my this month.") == _normalize_question_text("  how will be my this month.  ")


def test_infer_answer_mode_married_this_year_prefers_event_prediction():
    intent = {"mode": "LIFESPAN_EVENT_TIMING", "category": "marriage"}
    assert _infer_answer_mode("When will I get married this year?", intent, []) == "event_prediction"


def test_infer_answer_mode_marriage_possibility_in_chart_is_natal_promise():
    intent = {"mode": "LIFESPAN_EVENT_TIMING", "category": "marriage"}
    assert _infer_answer_mode(
        "Is there any possibility of marriage in my birth chart or kundali?",
        intent,
        [],
    ) == "potential_capacity"


def test_infer_answer_mode_remedy_with_cta_or_semantic_router_flag():
    from chat.instant_chat_pipeline import _clamp_remedy_answer_mode, _explicit_remedy_followup_requested

    plain = {"mode": "RECOMMEND_REMEDY_FOR_PROBLEM", "answer_mode": "remedy_action", "category": "health"}
    assert not _explicit_remedy_followup_requested(plain)
    assert _infer_answer_mode("What remedies for my anxiety?", plain, []) != "remedy_action"
    assert _clamp_remedy_answer_mode("remedy_action", plain, "what should I do for anxiety") == "problem_diagnosis"

    semantic = {
        "mode": "RECOMMEND_REMEDY_FOR_PROBLEM",
        "answer_mode": "remedy_action",
        "category": "career",
        "explicit_remedy_request": True,
    }
    assert _explicit_remedy_followup_requested(semantic)
    assert _infer_answer_mode("Show my career remedies", semantic, []) == "remedy_action"
    assert _clamp_remedy_answer_mode("remedy_action", semantic, "Show my career remedies") == "remedy_action"

    cta = {
        "category": "health",
        "query_context": {"remedy_followup": True, "follow_up_type": "remedy_action"},
    }
    assert _explicit_remedy_followup_requested(cta)
    assert _infer_answer_mode("Show me remedies", cta, []) == "remedy_action"
    assert _clamp_remedy_answer_mode("remedy_action", cta, "Show me remedies") == "remedy_action"


def test_open_ended_life_event_when_detects_job_and_ex():
    assert _looks_like_open_ended_life_event_when("When will I get a job?", {"mode": "ANALYZE_TOPIC_POTENTIAL"})
    assert _looks_like_open_ended_life_event_when("When will my ex come back?", {"mode": "LIFESPAN_EVENT_TIMING"})
    assert not _looks_like_open_ended_life_event_when("How will this month be for me?", {"mode": "PREDICT_PERIOD_OUTLOOK"})


def test_conversational_non_question_detects_deferrals():
    assert _is_conversational_non_question("Nothing for now.")
    assert _is_conversational_non_question("no thanks")
    assert _is_conversational_non_question("I'm good for now")
    assert not _is_conversational_non_question("What about my career next month?")
    assert not _is_conversational_non_question("Is there nothing good in my chart?")


if __name__ == "__main__":
    test_infer_answer_mode_for_explanation()
    test_infer_answer_mode_named_varga_uses_llm_chart_focus_not_question_language()
    test_infer_answer_mode_does_not_keyword_match_english_d12()
    test_infer_answer_mode_named_varga_this_year_keeps_llm_timing()
    test_mode_selection_honors_llm_factual_chart_lookup_in_any_language()
    test_mode_selection_coerces_topic_reading_from_llm_chart_focus()
    test_mode_selection_does_not_parse_question_text_for_chart_facts()
    test_build_answer_mode_contract_for_factual_chart_lookup()
    test_infer_answer_mode_for_trait_question()
    test_build_answer_mode_contract_for_trait_nature_uses_personality_axes()
    test_infer_answer_mode_for_period_window()
    test_infer_answer_mode_for_tomorrow_outlook_questions()
    test_resolve_period_window_for_tomorrow_day_and_next_year()
    test_resolve_period_window_uses_router_month_map_without_year_word()
    test_daily_transit_guard_keeps_tomorrow_as_daily()
    test_build_answer_mode_contract_for_relationship_person()
    test_fallback_target_subject_handles_second_child_and_younger_brother()
    test_build_person_profile_axes_uses_target_house_not_native_lagna()
    test_build_target_chart_context_rotates_houses_for_target()
    test_target_context_as_birth_summary_uses_target_ascendant()
    test_rotate_instant_parashari_for_target_reanchors_houses()
    test_build_answer_mode_contract_for_timing_window_prefers_ranked_areas()
    test_timing_window_contract_specializes_day_and_year_outlooks()
    test_build_answer_mode_contract_for_event_prediction_is_investigative()
    test_build_answer_mode_contract_for_problem_diagnosis_uses_target_context()
    test_all_house_activation_from_levels_covers_full_chart()
    test_build_month_tone_signals_disabled_without_sun_contact()
    test_build_month_tone_signals_enabled_for_dasha_activated_house()
    test_divisional_specific_lines_extracts_concrete_detail()
    test_event_prompt_prefers_compact_divisional_chart_mentions()
    test_risk_specific_lines_extracts_house_mechanism()
    test_timing_window_contract_keeps_claim_gate_support()
    test_normalize_question_text_treats_same_retry_as_same_question()
    test_conversational_non_question_detects_deferrals()
    test_infer_answer_mode_married_this_year_prefers_event_prediction()
    test_infer_answer_mode_remedy_only_with_cta_flags()
    test_open_ended_life_event_when_detects_job_and_ex()
    print("instant answer mode tests passed")
