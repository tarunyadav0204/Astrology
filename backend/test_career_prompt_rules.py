from backend.ai.parallel_chat.prompt_blocks import (
    build_jaimini_branch_static_agent,
    build_parashari_branch_static_agent,
)
from backend.chat.system_instruction_config import (
    CAREER_SUTRAS,
    HOLISTIC_SYNTHESIS_RULE,
    MERGE_FINAL_SYNTHESIS_RULE,
    PARASHARI_PILLAR,
)


def test_parashari_pillar_includes_career_decision_stack_and_negative_evidence():
    assert "CAREER DECISION STACK" in PARASHARI_PILLAR
    assert "Aptitude" in PARASHARI_PILLAR
    assert "Field Selection" in PARASHARI_PILLAR
    assert "Work Function" in PARASHARI_PILLAR
    assert "Status/Visibility" in PARASHARI_PILLAR
    assert "Timing of Entry/Change" in PARASHARI_PILLAR
    assert "CAREER NEGATIVE-EVIDENCE RULE" in PARASHARI_PILLAR


def test_career_sutras_require_ranked_field_selection_and_work_function():
    assert "Aptitude" in CAREER_SUTRAS
    assert "Field Selection" in CAREER_SUTRAS
    assert "Work Function" in CAREER_SUTRAS
    assert "rank the top 1-3 strongest field signatures" in CAREER_SUTRAS
    assert "AmK + KL + AL" in CAREER_SUTRAS


def test_career_synthesis_rules_require_shaped_verdict():
    low = HOLISTIC_SYNTHESIS_RULE.lower()
    assert "best-fit field/domain" in low
    assert "likely work function" in low
    assert "employment vs business vs hybrid tendency" in low
    assert "status/visibility level" in low
    assert "timing of entry/change" in low
    assert "career activation exists, but recognition/public visibility is limited" in MERGE_FINAL_SYNTHESIS_RULE
    assert "aptitude is clear, but execution/timing is weaker" in MERGE_FINAL_SYNTHESIS_RULE


def test_parashari_agent_prompt_requires_career_stage_separation():
    prompt = build_parashari_branch_static_agent("career")
    assert "Aptitude -> Field Selection -> Work Function -> Status/Visibility -> Timing of Entry/Change" in prompt
    assert "field signatures" in prompt.lower()
    assert "service/business/hybrid" in prompt
    assert "rank the likely field signatures" in prompt.lower()


def test_jaimini_agent_prompt_requires_vocation_vs_visibility_split():
    prompt = build_jaimini_branch_static_agent()
    assert "vocation from status/image" in prompt
    assert "jx.career" in prompt
    assert "image/vocation sign occupants" in prompt
