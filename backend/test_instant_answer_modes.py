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

from chat.instant_chat_pipeline import _all_house_activation_from_levels, _build_answer_mode_contract, _build_month_tone_signals, _divisional_specific_lines, _infer_answer_mode, _normalize_question_text, _risk_specific_lines


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
    assert "topic_signals" in contract["primary_evidence"]
    assert "current-period narrative unless asked" in contract["avoid_drift"]


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


def test_build_answer_mode_contract_for_event_prediction_is_investigative():
    contract = _build_answer_mode_contract(
        "event_prediction",
        "career",
        {"kind": "window", "span_days": 365},
        "future",
    )
    assert contract["answer_mode"] == "event_prediction"
    assert "question-led yes bias" in contract["avoid_drift"]
    assert "Evidence-led verdict" in contract["answer_skeleton"]


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


if __name__ == "__main__":
    test_infer_answer_mode_for_explanation()
    test_infer_answer_mode_for_trait_question()
    test_infer_answer_mode_for_period_window()
    test_build_answer_mode_contract_for_relationship_person()
    test_build_answer_mode_contract_for_timing_window_prefers_ranked_areas()
    test_build_answer_mode_contract_for_event_prediction_is_investigative()
    test_all_house_activation_from_levels_covers_full_chart()
    test_build_month_tone_signals_disabled_without_sun_contact()
    test_build_month_tone_signals_enabled_for_dasha_activated_house()
    test_divisional_specific_lines_extracts_concrete_detail()
    test_risk_specific_lines_extracts_house_mechanism()
    test_timing_window_contract_keeps_claim_gate_support()
    test_normalize_question_text_treats_same_retry_as_same_question()
    print("instant answer mode tests passed")
