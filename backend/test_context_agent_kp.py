"""Tests for context_agents.kp (kp_analysis blob)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_kp_registered():
    assert "kp" in list_agent_ids()


def test_kp_matches_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]
    raw = static.get("kp_analysis")
    if raw is None:
        pytest.skip("kp_analysis missing")

    out = build_agent(
        "kp",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["a"] == "kp"
    assert out["v"] == 1
    assert out.get("KP") == raw


def test_kp_slice_builds():
    from ai.parallel_chat.context_slices import build_kp_slice

    ctx = {
        "intent": {"category": "career"},
        "current_date_info": {"d": 1},
        "response_format": {"x": 1},
        "kp_analysis": {"planet_lords": {"Sun": {}}, "cusp_lords": {}, "significators": {}},
        "ascendant_info": {"sign_name": "Aries"},
        "birth_details": {"name": "T"},
        "d1_chart": {},
        "house_lordships": {},
    }
    sl = build_kp_slice(ctx)
    assert sl["kp_analysis"]["planet_lords"] == {"Sun": {}}
    assert "ascendant_info" in sl
