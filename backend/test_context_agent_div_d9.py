"""Tests for context_agents.div_d9 (navamsa from static context)."""

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


def test_div_d9_registered():
    assert "div_d9" in list_agent_ids()


def test_div_d9_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    out = build_agent(
        "div_d9",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "div_d9"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "L", "P", "H"}
    assert set(out["L"].keys()) == {"s", "d", "nm"}
    assert 1 <= out["L"]["s"] <= 12
    assert len(out["P"]) == 9
    for row in out["P"]:
        assert len(row) == 5
        assert 1 <= row[2] <= 12
        assert 1 <= row[4] <= 12
    assert isinstance(out["H"], dict)


def test_div_d9_matches_static_extraction(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    inner = _d9_inner(static)
    assert inner.get("ascendant") is not None
    expected = compact_wheel_chart(inner)

    out = build_agent(
        "div_d9",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["L"] == expected["L"]
    assert out["P"] == expected["P"]
    assert out["H"] == expected["H"]
