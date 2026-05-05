import os
import sys
import types

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
_stub_module("context_agents.base", AgentContext=_Dummy)
_stub_module("shared.dasha_calculator", DashaCalculator=_Dummy)
_stub_module("utils.admin_settings", get_gemini_instant_model=lambda: "stub-model")
_stub_module("utils.query_context", resolve_query_now=lambda qc=None: __import__("datetime").datetime(2026, 5, 1, 12, 0, 0))

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
    _is_conversational_non_question,
    _instant_lifetime_event_year_clarification_response,
    _merge_adjacent_low_score_event_periods,
    _normalize_event_category,
    _normalize_question_text,
    _normalize_instant_evidence,
    _period_anchor_datetime,
    _planet_aspects_house_from,
    _is_dasha_calculator_fallback_payload,
    _authoritative_active_dasha_context,
    _risk_specific_lines,
    _rotate_instant_parashari_for_target,
    _target_context_as_birth_summary,
)


def test_infer_answer_mode_for_explanation():
    mode = _infer_answer_mode(
        "You said Rahu activates my 10th house. How exactly?",
        {"mode": "ANALYZE_TOPIC_POTENTIAL", "category": "career"},
        [{"question": "career", "response": "Rahu activates 10th"}],
    )
    assert mode == "explanation_mechanism"


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
    assert _planet_aspects_house_from(2, 9, "Saturn") is True  # Saturn 7th
    assert _planet_aspects_house_from(2, 5, "Saturn") is True  # Saturn 3rd
    assert _planet_aspects_house_from(2, 12, "Saturn") is True  # Saturn 10th
    assert _planet_aspects_house_from(2, 6, "Saturn") is False


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
    test_infer_answer_mode_for_trait_question()
    test_build_answer_mode_contract_for_trait_nature_uses_personality_axes()
    test_infer_answer_mode_for_period_window()
    test_build_answer_mode_contract_for_relationship_person()
    test_fallback_target_subject_handles_second_child_and_younger_brother()
    test_build_person_profile_axes_uses_target_house_not_native_lagna()
    test_build_target_chart_context_rotates_houses_for_target()
    test_target_context_as_birth_summary_uses_target_ascendant()
    test_rotate_instant_parashari_for_target_reanchors_houses()
    test_build_answer_mode_contract_for_timing_window_prefers_ranked_areas()
    test_build_answer_mode_contract_for_event_prediction_is_investigative()
    test_build_answer_mode_contract_for_problem_diagnosis_uses_target_context()
    test_all_house_activation_from_levels_covers_full_chart()
    test_build_month_tone_signals_disabled_without_sun_contact()
    test_build_month_tone_signals_enabled_for_dasha_activated_house()
    test_divisional_specific_lines_extracts_concrete_detail()
    test_risk_specific_lines_extracts_house_mechanism()
    test_timing_window_contract_keeps_claim_gate_support()
    test_normalize_question_text_treats_same_retry_as_same_question()
    test_conversational_non_question_detects_deferrals()
    test_infer_answer_mode_married_this_year_prefers_event_prediction()
    test_open_ended_life_event_when_detects_job_and_ex()
    print("instant answer mode tests passed")
