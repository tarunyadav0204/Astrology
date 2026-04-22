from backend.ai.parallel_chat.prompt_blocks import build_parashari_branch_static_agent
from backend.chat.system_instruction_config import MARRIAGE_SUTRAS, PARASHARI_PILLAR


def test_parashari_pillar_includes_marriage_timing_stack_and_negative_evidence():
    assert "MARRIAGE TIMING STACK" in PARASHARI_PILLAR
    assert "Promise" in PARASHARI_PILLAR
    assert "Timing" in PARASHARI_PILLAR
    assert "Manifestation" in PARASHARI_PILLAR
    assert "Continuity" in PARASHARI_PILLAR
    assert "MARRIAGE NEGATIVE-EVIDENCE RULE" in PARASHARI_PILLAR


def test_marriage_sutras_require_split_verdict_and_delay_language():
    assert "Promise" in MARRIAGE_SUTRAS
    assert "Timing" in MARRIAGE_SUTRAS
    assert "Manifestation" in MARRIAGE_SUTRAS
    assert "Continuity" in MARRIAGE_SUTRAS
    assert "delay" in MARRIAGE_SUTRAS.lower()
    assert "obstruction" in MARRIAGE_SUTRAS.lower()


def test_parashari_agent_prompt_requires_marriage_stage_separation():
    prompt = build_parashari_branch_static_agent("marriage")
    assert "Promise -> Timing -> Manifestation -> Continuity" in prompt
    assert "relationship activation" in prompt.lower()
    assert "legal or durable marriage" in prompt
    assert "materialization pressure" in prompt
    assert "supportive/mixed/obstructed" in prompt
