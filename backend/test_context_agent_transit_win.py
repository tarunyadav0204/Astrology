"""Tests for context_agents.transit_win (compact transit activations)."""

import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat.chat_context_builder import ChatContextBuilder
from context_agents.agents.transit_win import _compact_activation
from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_transit_win_registered():
    assert "transit_win" in list_agent_ids()


def test_transit_win_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    cy = 2026
    intent = {
        "needs_transits": True,
        "transit_request": {
            "startYear": cy,
            "endYear": cy,
            "yearMonthMap": {str(cy): ["January"]},
        },
    }
    builder = ChatContextBuilder()
    bh = builder._create_birth_hash(birth)
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        builder.static_cache[bh] = static
        dynamic = builder._build_dynamic_context(birth, "", None, None, intent)

    out = build_agent(
        "transit_win",
        AgentContext(
            birth_data=birth,
            intent_result=intent,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["a"] == "transit_win"
    assert out["v"] == 3
    assert set(out.keys()) >= {"a", "v", "sc", "Y", "n", "A"}
    assert out["Y"]["sy"] == cy
    assert out["Y"]["ey"] == cy
    assert isinstance(out["n"], int)
    assert isinstance(out["A"], list)
    for row in out["A"][:3]:
        assert "tp" in row and "np" in row and "sd" in row and "ed" in row
        assert "all_aspects_cast" not in row
        assert "comprehensive_dashas" not in row


def test_compact_activation_strips_bulk():
    bulky = {
        "transit_planet": "Jupiter",
        "natal_planet": "Venus",
        "aspect_number": 5,
        "start_date": "2026-01-01",
        "end_date": "2026-02-01",
        "transit_house": 3,
        "natal_house": 7,
        "aspect_type": "5th_house",
        "dasha_reference": {"peak_date": "2026-01-15"},
        "all_aspects_cast": [{"x": "y"}] * 50,
        "comprehensive_dashas": {"vimshottari_periods": [1, 2, 3]},
    }
    c = _compact_activation(bulky)
    assert c["tp"] == "Jupiter"
    assert "all_aspects_cast" not in c
    assert "comprehensive_dashas" not in c
    assert "ak" not in c
