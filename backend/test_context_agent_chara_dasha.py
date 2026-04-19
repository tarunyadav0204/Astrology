"""Tests for context_agents.chara_dasha (full Chara MD+AD from CharaDashaCalculator)."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_chara_dasha_registered():
    assert "chara_dasha" in list_agent_ids()


def test_chara_dasha_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    out = build_agent(
        "chara_dasha",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            time_scope="full",
        ),
    )
    assert out["a"] == "chara_dasha"
    assert out["v"] == 1
    assert "err" not in out
    assert set(out.keys()) == {"a", "v", "sc", "fn", "sys", "n", "P"}
    assert isinstance(out["P"], list)
    # Calculator emits one full cycle: 12 mahadashas
    assert len(out["P"]) == 12
    for md in out["P"]:
        assert set(md.keys()) == {"s", "nm", "y", "ds", "de", "ic", "ad"}
        assert 1 <= md["s"] <= 12
        assert isinstance(md["ad"], list)
        assert len(md["ad"]) == 12
        for ad in md["ad"]:
            assert set(ad.keys()) == {"s", "nm", "ds", "de", "ic"}
            assert 1 <= ad["s"] <= 12


def test_chara_dasha_missing_date():
    out = build_agent(
        "chara_dasha",
        AgentContext(birth_data={}, precomputed_static={}),
    )
    assert out.get("err") == "missing_birth_date"
