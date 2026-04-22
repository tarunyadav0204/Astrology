from backend.ai.parallel_chat.prompt_blocks import build_jaimini_branch_static_agent
from backend.chat.system_instruction_config import (
    CAREER_SUTRAS,
    HOLISTIC_SYNTHESIS_RULE,
    JAIMINI_ANALYSIS_STRUCTURE,
    JAIMINI_PILLAR,
    MARRIAGE_SUTRAS,
    MERGE_FINAL_SYNTHESIS_RULE,
)


def test_jaimini_pillar_includes_decision_order_and_veto_rules():
    assert "JAIMINI DECISION ORDER" in JAIMINI_PILLAR
    assert "NEGATIVE-EVIDENCE / VETO RULE" in JAIMINI_PILLAR
    assert "CAREER EXECUTION RULE" in JAIMINI_PILLAR
    assert "MARRIAGE DECISION RULE" in JAIMINI_PILLAR


def test_jaimini_analysis_structure_requires_static_promise_and_manifestation_filter():
    assert "Static Promise" in JAIMINI_ANALYSIS_STRUCTURE
    assert "Manifestation Filter" in JAIMINI_ANALYSIS_STRUCTURE
    assert "AmK / Karkamsa / AL" in JAIMINI_ANALYSIS_STRUCTURE


def test_domain_sutras_encode_new_jaimini_threads():
    assert "AmK + KL + AL" in CAREER_SUTRAS
    assert "DK = partner nature" in MARRIAGE_SUTRAS
    assert "A7 = embodied lived relationship" in MARRIAGE_SUTRAS
    assert "Promise" in MARRIAGE_SUTRAS
    assert "Continuity" in MARRIAGE_SUTRAS


def test_agent_prompt_requires_static_promise_and_active_chara_conflict_handling():
    prompt = build_jaimini_branch_static_agent()
    assert "Static Promise" in prompt
    assert "Manifestation Filter" in prompt
    assert "Do not let a favorable static karaka story overrule a clearly adverse active MD/AD frame" in prompt
    assert "AmK / KL / AL" in prompt
    assert "`jx`" in prompt


def test_marriage_synthesis_rules_require_promise_timing_manifestation_continuity():
    assert "promise" in HOLISTIC_SYNTHESIS_RULE.lower()
    assert "timing window" in HOLISTIC_SYNTHESIS_RULE.lower()
    assert "continuity" in HOLISTIC_SYNTHESIS_RULE.lower()
    assert "promise exists, timing weak" in MERGE_FINAL_SYNTHESIS_RULE
    assert "timing active, manifestation/continuity mixed" in MERGE_FINAL_SYNTHESIS_RULE
