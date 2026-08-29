from ai.parallel_chat.presentation_style import (
    build_simple_final_precedence_block,
    build_simple_merge_depth_instruction,
    build_simple_merge_instruction,
    build_simple_merge_response_format,
    normalize_merge_response_style,
)
from ai.parallel_chat.orchestrator import _merge_instruction_blocks
from ai.output_schema import build_final_prompt


def test_only_explicit_simple_enables_simple_merge_presentation():
    assert normalize_merge_response_style("simple") == "simple"
    assert normalize_merge_response_style(" SIMPLE ") == "simple"

    for legacy_or_technical in (None, "", "technical", "detailed", "concise"):
        assert normalize_merge_response_style(legacy_or_technical) == "technical"
        assert build_simple_merge_instruction(legacy_or_technical) == ""


def test_simple_instruction_changes_presentation_not_specialist_analysis():
    instruction = build_simple_merge_instruction("simple")

    assert "FINAL SYNTHESIS ONLY" in instruction
    assert "Preserve their verdict, rankings, dates, timing windows" in instruction
    assert "name at least one evidence-bound planet" in instruction
    assert "Simple changes vocabulary and presentation, not analytical coverage" in instruction
    assert "Do not expose chart codes" in instruction


def test_simple_replaces_technical_depth_and_visible_response_schema():
    context = {"intent": {"mode": "DEFAULT", "category": "education"}}

    technical = _merge_instruction_blocks(
        "What does my chart show about education?",
        context,
        "english",
        "technical",
        None,
        False,
        "DEFAULT",
    )
    simple = _merge_instruction_blocks(
        "What does my chart show about education?",
        context,
        "english",
        "simple",
        None,
        False,
        "DEFAULT",
    )

    assert "Short or summary-style answers are FORBIDDEN" in technical[2]
    assert "SIMPLE STANDARD RESPONSE DEPTH" in simple[2]
    assert "Short or summary-style answers are FORBIDDEN" not in simple[2]
    assert simple[3] == build_simple_merge_response_format()
    assert "Do not output Key Insights" in simple[3]


def test_simple_depth_preserves_standard_and_premium_analysis_coverage():
    standard = build_simple_merge_depth_instruction(premium_analysis=False)
    premium = build_simple_merge_depth_instruction(premium_analysis=True)

    assert "complete Standard answer" in standard
    assert "complete Premium answer" in premium
    assert "2-4 strongest evidence-backed planetary reasons" in standard
    assert "Premium may cover more relevant conclusions" in premium


def test_final_simple_override_wins_over_later_timing_contracts():
    assert build_simple_final_precedence_block(
        "technical",
        premium_analysis=True,
    ) == ""

    simple = build_simple_final_precedence_block(
        "simple",
        premium_analysis=True,
    )
    assert "HIGHEST PRECEDENCE" in simple
    assert "Executive Summary" in simple
    assert "Ranked Potential Windows" in simple
    assert "translate that content into the Simple format" in simple


def test_legacy_single_prompt_honors_simple_without_changing_technical_path():
    context = {
        "analysis_type": "birth",
        "intent": {"mode": "DEFAULT", "category": "health"},
        "birth_details": {"name": "Test Native"},
        "ascendant_info": {"sign_name": "Cancer", "exact_degree_in_sign": 1.0},
        "response_format": {
            "mandatory_sections": "ALWAYS include Nakshatra Insights section",
            "header_enforcement": "Use exact technical headers",
        },
    }
    kwargs = {
        "user_question": "What are my health vulnerabilities?",
        "context": context,
        "history": [],
        "language": "english",
        "user_context": None,
        "premium_analysis": False,
        "mode": "DEFAULT",
    }

    technical = build_final_prompt(response_style="technical", **kwargs)
    legacy_detailed = build_final_prompt(response_style="detailed", **kwargs)
    simple = build_final_prompt(response_style="simple", **kwargs)

    assert technical == legacy_detailed
    assert "Short or summary-style answers are FORBIDDEN" in technical
    assert "Short or summary-style answers are FORBIDDEN" not in simple
    assert "SIMPLE STANDARD RESPONSE DEPTH" in simple
    assert "SIMPLE ANSWER FORMAT (VISIBLE RESPONSE)" in simple
    assert "ALWAYS include Nakshatra Insights section" in technical
    assert "ALWAYS include Nakshatra Insights section" not in simple
    assert simple.rfind("SIMPLE PRESENTATION MODE") > simple.rfind("VEDIC ASTROLOGY")


def test_legacy_lifespan_simple_override_comes_after_technical_timing_schema():
    context = {
        "analysis_type": "birth",
        "intent": {"mode": "LIFESPAN_EVENT_TIMING", "category": "career"},
        "birth_details": {"name": "Test Native"},
        "ascendant_info": {"sign_name": "Cancer", "exact_degree_in_sign": 1.0},
    }
    prompt = build_final_prompt(
        user_question="When will I get promotion?",
        context=context,
        history=[],
        language="english",
        response_style="simple",
        user_context=None,
        premium_analysis=True,
        mode="LIFESPAN_EVENT_TIMING",
    )

    assert "Technical Deep Dive" in prompt
    assert prompt.endswith(
        build_simple_final_precedence_block(
            "simple",
            premium_analysis=True,
        )
    )
