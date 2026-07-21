"""Guard free-question Parashari finals against the full multi-school response schema."""

from ai.parallel_chat.prompt_blocks import (
    build_parashari_only_response_format,
    free_question_elaborate_instruction,
    scoped_lane_response_format,
)


def test_parashari_only_format_forbids_other_schools():
    fmt = build_parashari_only_response_format()
    assert "PARASHARI-ONLY" in fmt
    assert "Do NOT mention or imply other schools" in fmt
    for banned in (
        "The Jaimini View",
        "KP Stellar Perspective",
        "Nadi Interpretation",
        "Ashtakavarga",
    ):
        assert banned in fmt  # listed as forbidden section titles
    assert "Quick Answer" in fmt
    assert "Astrological Analysis" in fmt


def test_scoped_lane_prefers_parashari_only_for_free_question():
    default = "FULL MULTI SCHOOL SCHEMA WITH KP AND NADI"
    chosen = scoped_lane_response_format(
        free_question_parashari_only=True,
        remedy_followup_requested=False,
        default_format=default,
    )
    assert chosen == build_parashari_only_response_format()
    assert default not in chosen


def test_scoped_lane_remedy_overrides_default_and_free():
    default = "FULL MULTI SCHOOL SCHEMA"
    remedy = scoped_lane_response_format(
        free_question_parashari_only=False,
        remedy_followup_requested=True,
        default_format=default,
    )
    assert "REMEDY-ONLY" in remedy
    assert default not in remedy

    # Remedy follow-up is more specific than free Parashari lane.
    both = scoped_lane_response_format(
        free_question_parashari_only=True,
        remedy_followup_requested=True,
        default_format=default,
    )
    assert "REMEDY-ONLY" in both
    assert both != build_parashari_only_response_format()


def test_scoped_lane_keeps_default_when_not_scoped():
    default = "FULL MULTI SCHOOL SCHEMA"
    chosen = scoped_lane_response_format(
        free_question_parashari_only=False,
        remedy_followup_requested=False,
        default_format=default,
    )
    assert chosen is default


def test_free_question_elaborate_blocks_invented_schools():
    text = free_question_elaborate_instruction()
    assert "PARASHARI-ONLY" in text
    assert "Do NOT invent KP" in text
    assert "Do NOT include remedies" in text


def test_parashari_only_format_forbids_inline_remedies():
    fmt = build_parashari_only_response_format()
    assert "Do NOT include remedy layers" in fmt
    assert "wellness playbooks" in fmt or "yoga/pranayama" in fmt
