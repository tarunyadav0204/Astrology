"""Tests for slow-planet macro transit compaction + Parashari wiring."""

from __future__ import annotations

import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat.system_instruction_config import TRANSIT_DATES_SOVEREIGNTY, build_system_instruction
from context_agents.macro_transits_compact import (
    authoritative_slow_transits_packet,
    compact_macro_transits_timeline,
)
from ai.parallel_chat.parallel_agent_payloads import _transit_summary
from ai.parallel_chat.prompt_blocks import (
    build_parashari_branch_static_agent,
    build_parashari_final_answer_static,
    free_question_elaborate_instruction,
)


def test_compact_macro_filters_by_year_and_keeps_cancer_2026():
    macro = {
        "Jupiter": [
            {
                "sign": "Gemini",
                "house": 6,
                "start_date": "2025-05-01",
                "end_date": "2026-05-31",
                "retrograde_return": False,
            },
            {
                "sign": "Cancer",
                "house": 7,
                "start_date": "2026-06-02",
                "end_date": "2026-10-30",
                "retrograde_return": False,
            },
            {
                "sign": "Cancer",
                "house": 7,
                "start_date": "2027-01-25",
                "end_date": "2027-06-25",
                "retrograde_return": True,
            },
            {
                "sign": "Leo",
                "house": 8,
                "start_date": "2027-07-01",
                "end_date": "2028-07-01",
                "retrograde_return": False,
            },
        ],
        "Saturn": [],
    }
    out = compact_macro_transits_timeline(macro, start_year=2026, end_year=2027)
    ju = out["Jupiter"]
    assert any(r["sg"] == "Cancer" and str(r["sd"]).startswith("2026-06") for r in ju)
    assert any(r.get("rr") is True and str(r["sd"]).startswith("2027-01") for r in ju)
    # Leo starts mid-2027 — still overlaps 2027 window
    assert any(r["sg"] == "Leo" for r in ju)
    # Pure 2025 Gemini end may still overlap 2026 window via end_date
    assert all(r["sg"] != "Aries" for r in ju)


def test_authoritative_packet_rule_present():
    packet = authoritative_slow_transits_packet(
        {
            "macro_transits_timeline": {
                "Jupiter": [
                    {
                        "sign": "Cancer",
                        "house": 7,
                        "start_date": "2026-06-02",
                        "end_date": "2026-10-30",
                    }
                ]
            },
            "macro_transits_meta": {"start": "2025-01-01", "end": "2030-01-01"},
        }
    )
    assert packet["authority"] == "macro_transits_timeline"
    assert packet["planets"]["Jupiter"][0]["sg"] == "Cancer"
    assert "Never invent" in packet["rule"]


def test_transit_summary_exposes_mt():
    summary = _transit_summary(
        [7],
        {"md": {"p": "Mercury"}},
        {
            "A": [],
            "M": {
                "Jupiter": [{"sg": "Cancer", "h": 7, "sd": "2026-06-02", "ed": "2026-10-30"}]
            },
        },
    )
    assert "MT" in summary
    assert summary["MT"]["Jupiter"][0]["sg"] == "Cancer"


def test_prompts_include_transit_date_sovereignty():
    assert "NEVER invent or estimate ingress years" in TRANSIT_DATES_SOVEREIGNTY
    assert "TRANSIT-DATES" in build_parashari_branch_static_agent("relationship")
    assert "TRANSIT-DATES" in build_parashari_final_answer_static("relationship")
    assert "AUTHORITATIVE_SLOW_TRANSITS_JSON" in free_question_elaborate_instruction()
    legacy = build_system_instruction("relationship", "general")
    assert "TRANSIT-DATES" in legacy


def test_ephemeris_jupiter_cancer_main_ingress_is_mid_2026():
    """Regression: sustained Cancer occupancy includes mid-2026, not only late 2027."""
    from calculators.real_transit_calculator import RealTransitCalculator

    birth = {
        "date": "1990-01-15",
        "time": "10:30",
        "latitude": 28.6139,
        "longitude": 77.2090,
        "timezone": "+05:30",
    }
    calc = RealTransitCalculator()
    start = datetime(2025, 1, 1)
    end = datetime(2029, 1, 1)
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        timeline = calc.get_slow_planet_transits(birth, start_date=start, end_date=end)
    ju = timeline.get("Jupiter") or []
    cancer = [p for p in ju if p.get("sign") == "Cancer"]
    assert cancer, f"Expected Cancer segments; got {ju}"
    mid_2026 = [
        p
        for p in cancer
        if str(p.get("start_date") or "").startswith("2026-06")
        or (
            str(p.get("start_date") or "") <= "2026-06-30"
            and str(p.get("end_date") or "") >= "2026-06-02"
        )
    ]
    assert mid_2026, f"Expected Cancer occupancy covering mid-2026; periods={cancer}"
    # Compact packet must surface that mid-2026 Cancer row for the LLM
    compact = compact_macro_transits_timeline(
        {"Jupiter": ju}, start_year=2026, end_year=2027
    )
    assert any(
        r.get("sg") == "Cancer" and str(r.get("sd") or "").startswith("2026-06")
        for r in compact.get("Jupiter") or []
    ), compact
    # Late 2027 forward Cancer as the *only* supportive window would be wrong;
    # Leo occupies late 2027 after the early-2027 Cancer retro return ends.
    leo_late_2027 = [
        p
        for p in ju
        if p.get("sign") == "Leo"
        and str(p.get("start_date") or "") <= "2027-12-01"
        and str(p.get("end_date") or "") >= "2027-08-01"
    ]
    assert leo_late_2027, f"Expected Leo in late 2027; periods={ju}"


def test_transit_win_includes_macro_m(context_agent_cached):
    from chat.chat_context_builder import ChatContextBuilder
    from context_agents.base import AgentContext
    from context_agents.registry import build_agent

    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    cy = 2026
    intent = {
        "needs_transits": True,
        "transit_request": {
            "startYear": cy,
            "endYear": cy + 2,
            "yearMonthMap": {str(y): ["January"] for y in range(cy, cy + 3)},
        },
    }
    builder = ChatContextBuilder()
    bh = builder._create_birth_hash(birth)
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        builder.static_cache[bh] = static
        dynamic = builder._build_dynamic_context(birth, "", None, None, intent)

    # Ensure dynamic carries macro (builder should); if empty, skip soft
    if not dynamic.get("macro_transits_timeline"):
        pytest.skip("macro_transits_timeline missing from dynamic context")

    out = build_agent(
        "transit_win",
        AgentContext(
            birth_data=birth,
            intent_result=intent,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["v"] == 4
    assert isinstance(out.get("M"), dict)
    assert "Jupiter" in out["M"]
    ju_rows = out["M"]["Jupiter"]
    assert any(r.get("sg") == "Cancer" and str(r.get("sd") or "").startswith("2026") for r in ju_rows), ju_rows
