"""Tests for context_agents.panch_maitri (Panchadha friendship matrix)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from calculators.friendship_calculator import FriendshipCalculator
from context_agents.base import AgentContext
from context_agents.compact_vedic import PLANET_ORDER
from context_agents.registry import build_agent, list_agent_ids

_CODES = {".", "++", "+", "0", "-", "--", "?"}


def _encode_cell(raw: str) -> str:
    return {
        "self": ".",
        "great_friend": "++",
        "friend": "+",
        "neutral": "0",
        "enemy": "-",
        "great_enemy": "--",
    }.get(raw, "?")


def test_panch_maitri_registered():
    assert "panch_maitri" in list_agent_ids()


def test_panch_maitri_shape_matches_friendship_calculator(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    fa = static.get("friendship_analysis") or {}
    if fa.get("error") or not fa.get("friendship_matrix"):
        pytest.skip("friendship_analysis missing or errored in static context")

    ctx_cached = AgentContext(birth_data=birth, precomputed_static=static)
    out = build_agent("panch_maitri", ctx_cached)

    assert out["a"] == "panch_maitri"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "F"}
    fm = fa["friendship_matrix"]

    for p1 in PLANET_ORDER:
        assert p1 in out["F"]
        row = out["F"][p1]
        assert len(row) == 9
        for p2 in PLANET_ORDER:
            raw = fm[p1][p2]
            assert row[p2] == _encode_cell(raw)
            assert row[p2] in _CODES
            if p1 == p2:
                assert row[p2] == "."


def test_panch_maitri_precomputed_matches_fresh_calc(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    fa = static.get("friendship_analysis") or {}
    if fa.get("error") or not fa.get("friendship_matrix"):
        pytest.skip("friendship_analysis missing or errored in static context")

    with_cached = build_agent(
        "panch_maitri",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    fresh = build_agent(
        "panch_maitri",
        AgentContext(birth_data=birth, precomputed_static=None),
    )
    assert with_cached == fresh


def test_panch_maitri_matches_standalone_calculator(context_agent_cached):
    birth = context_agent_cached["birth"]
    fm = FriendshipCalculator().calculate_friendship(birth)["friendship_matrix"]
    out = build_agent("panch_maitri", AgentContext(birth_data=birth, precomputed_static=None))
    for p1 in PLANET_ORDER:
        for p2 in PLANET_ORDER:
            assert out["F"][p1][p2] == _encode_cell(fm[p1][p2])
