"""Tests for lifespan scan-window vs judgment-epoch split."""

from datetime import datetime

from chat.chat_context_builder import resolve_timing_focus
from chat.system_instruction_config import (
    LIFESPAN_MERGE_TIMING_RULE,
    MARRIAGE_TIMING_STACK_RULES,
    build_merge_synthesis_instruction,
    build_system_instruction,
)


def test_open_ended_lifespan_focuses_now_keeps_scan_window():
    now = datetime(2026, 7, 16, 12, 0, 0)
    focus = resolve_timing_focus(
        {
            "mode": "LIFESPAN_EVENT_TIMING",
            "transit_request": {"startYear": 2008, "endYear": 2051},
        },
        now=now,
    )
    assert focus["open_ended_lifespan"] is True
    assert focus["judgment_year"] == 2026
    assert focus["focus_source"] == "lifespan_open_ended_now"
    assert focus["scan_start_year"] == 2008
    assert focus["scan_end_year"] == 2051


def test_asked_year_overrides_open_ended_focus():
    now = datetime(2026, 7, 16)
    focus = resolve_timing_focus(
        {
            "mode": "LIFESPAN_EVENT_TIMING",
            "transit_request": {"startYear": 2008, "endYear": 2051},
            "extracted_context": {"specific_year": 2028},
        },
        now=now,
    )
    assert focus["open_ended_lifespan"] is False
    assert focus["judgment_year"] == 2028
    assert focus["focus_source"] == "extracted_asked_year"


def test_narrow_window_uses_start_year():
    now = datetime(2026, 7, 16)
    focus = resolve_timing_focus(
        {
            "mode": "PREDICT_PERIOD_OUTLOOK",
            "transit_request": {"startYear": 2027, "endYear": 2028},
        },
        now=now,
    )
    assert focus["open_ended_lifespan"] is False
    assert focus["judgment_year"] == 2027
    assert focus["focus_source"] == "narrow_transit_window"


def test_marriage_stack_not_in_career_lifespan_instruction():
    career = build_system_instruction(
        analysis_type="LIFESPAN_EVENT_TIMING",
        intent_category="career",
    )
    marriage = build_system_instruction(
        analysis_type="LIFESPAN_EVENT_TIMING",
        intent_category="marriage",
    )
    assert "MARRIAGE TIMING STACK" not in career
    assert "MARRIAGE TIMING STACK" in marriage
    assert "LIFESPAN-VOCAB" in career
    assert MARRIAGE_TIMING_STACK_RULES.strip()[:40] in marriage


def test_job_alias_gets_career_sutras():
    text = build_system_instruction(
        analysis_type="LIFESPAN_EVENT_TIMING",
        intent_category="job",
    )
    assert "CAREER" in text.upper() or "10th" in text


def test_merge_includes_lean_lifespan_rule():
    merge = build_merge_synthesis_instruction(mode="LIFESPAN_EVENT_TIMING")
    assert "MERGE-LIFESPAN" in merge
    assert LIFESPAN_MERGE_TIMING_RULE.strip()[:20] in merge
    default_merge = build_merge_synthesis_instruction(mode="DEFAULT")
    assert "MERGE-LIFESPAN" not in default_merge
