"""Tests for context_agents.d1_graha (PlanetAnalyzer + filtered planetary_analysis)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids

_GRAHA_KEYS = frozenset({"r", "d", "fn", "sm", "cb", "cz", "cs", "av", "cg", "sc"})


def test_d1_graha_registered():
    assert "d1_graha" in list_agent_ids()


def test_d1_graha_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    out = build_agent(
        "d1_graha",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "d1_graha"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "G"}
    g = out["G"]
    for name in (
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    ):
        assert name in g
        assert set(g[name].keys()) == _GRAHA_KEYS
        assert isinstance(g[name]["r"], bool)
        assert isinstance(g[name]["cb"], bool)
        assert isinstance(g[name]["cz"], bool)
        assert g[name]["d"] is not None
