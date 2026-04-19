"""Tests for context_agents.div_intent (router-driven divisional bundle)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.agents.div_d9 import _d9_inner
from context_agents.base import AgentContext
from context_agents.compact_chart_geometry import compact_wheel_chart
from context_agents.registry import build_agent, list_agent_ids


def test_div_intent_registered():
    assert "div_intent" in list_agent_ids()


def test_div_intent_default_d9_matches_div_d9(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    out = build_agent(
        "div_intent",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "div_intent"
    assert out["v"] == 1
    assert out["Q"] == ["D9"]
    assert set(out["C"]["D9"].keys()) == {"L", "P", "H"}
    d9_only = build_agent(
        "div_d9",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["C"]["D9"] == {k: d9_only[k] for k in ("L", "P", "H")}


def test_div_intent_multi_and_d1_subset(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    intent = {"divisional_charts": ["D1", "d9", "D10", "D9"]}
    out = build_agent(
        "div_intent",
        AgentContext(
            birth_data=birth,
            intent_result=intent,
            precomputed_static=static,
        ),
    )
    assert out["Q"] == ["D1", "D9", "D10"]
    for code in ("D1", "D9", "D10"):
        assert code in out["C"]
        assert set(out["C"][code].keys()) == {"L", "P", "H"}
        assert len(out["C"][code]["P"]) == 9

    assert out["C"]["D9"] == compact_wheel_chart(_d9_inner(static))
    d1 = static.get("d1_chart") or {}
    assert out["C"]["D1"] == compact_wheel_chart(d1)


def test_div_intent_omit_d1_d9_no_duplicate_with_core_div_d9(context_agent_cached):
    """Parallel Parashari: omit D1/D9 in div_intent when core_d1 + div_d9 provide them."""
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    intent = {"divisional_charts": ["D1", "D9", "D10"]}
    out = build_agent(
        "div_intent",
        AgentContext(
            birth_data=birth,
            intent_result=intent,
            precomputed_static=static,
            div_intent_omit_codes=frozenset({"D1", "D9"}),
        ),
    )
    assert out["Q"] == ["D10"]
    assert "D10" in out["C"]
    assert "D1" not in out["C"]
    assert "D9" not in out["C"]
    assert "S" in out
    assert "D1:omit_overlap" in out["S"]
    assert "D9:omit_overlap" in out["S"]
