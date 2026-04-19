"""Tests for context_agents.dasha_win (window Vimshottari)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.agents.dasha_win import _parse_window
from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_dasha_win_registered():
    assert "dasha_win" in list_agent_ids()


def test_parse_window_year_only():
    w_s, w_e, sp = _parse_window(
        {"transit_request": {"startYear": 2028, "endYear": 2028}}
    )
    assert w_s.year == 2028 and w_s.month == 1 and w_s.day == 1
    assert w_e.year == 2028 and w_e.month == 12
    assert sp == 366  # 2028 leap


def test_dasha_win_long_window_no_sk_pr(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    intent = {
        "transit_request": {
            "startYear": 2027,
            "endYear": 2028,
            "yearMonthMap": {"2027": ["June", "July"], "2028": ["January"]},
        }
    }
    out = build_agent(
        "dasha_win",
        AgentContext(birth_data=birth, intent_result=intent, precomputed_static=static),
    )
    assert out["a"] == "dasha_win"
    assert out["v"] == 2
    assert out.get("sc") == "intent_window"
    assert "md" in out and "ad" in out and "pd" in out
    assert "sk" not in out and "pr" not in out
    assert out["W"]["sp"] > 31
    assert "T" in out and isinstance(out["T"], list)
    assert out["tn"] >= len(out["T"])
    assert len(out["T"]) >= 1


def test_dasha_win_short_window_has_sk_pr(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    intent = {"dasha_as_of": "2027-06-15"}
    out = build_agent(
        "dasha_win",
        AgentContext(birth_data=birth, intent_result=intent, precomputed_static=static),
    )
    assert out["v"] == 2
    assert out.get("sc") == "current"
    assert out["W"]["sp"] == 1
    assert "sk" in out and "pr" in out
    assert out["sk"].get("p")
    assert out["pr"].get("p")
    assert "T" in out and len(out["T"]) >= 1
