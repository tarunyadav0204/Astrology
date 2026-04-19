"""Tests for context_agents.nadi (nadi_links + nadi_age_activation)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_nadi_registered():
    assert "nadi" in list_agent_ids()


def test_nadi_links_match_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]
    raw = static.get("nadi_links") or {}
    if not raw:
        pytest.skip("nadi_links empty")

    out = build_agent(
        "nadi",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["a"] == "nadi"
    assert out["v"] == 1
    assert set(out.keys()) >= {"a", "v", "sc", "LK", "AA"}

    for planet, row in raw.items():
        if planet not in out["LK"]:
            continue
        c = out["LK"][planet]
        si = row.get("sign_info") or {}
        sid = si.get("sign_id")
        if isinstance(sid, int):
            assert c["s"] == sid + 1
        assert c["rv"] is bool(si.get("is_retro"))
        assert c["ex"] is bool(si.get("is_exchange"))
        conn = row.get("connections") or {}
        assert c["t"] == sorted(conn.get("trine") or [])
        assert c["f"] == sorted(conn.get("next") or [])
        assert c["b"] == sorted(conn.get("prev") or [])
        assert c["o"] == sorted(conn.get("opposite") or [])
        assert c["a"] == sorted(row.get("all_links") or [])


def test_nadi_aa_matches_dynamic_when_present(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]
    raw = dynamic.get("nadi_age_activation")
    if not isinstance(raw, dict):
        pytest.skip("nadi_age_activation not active for this age")

    out = build_agent(
        "nadi",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["AA"] is not None
    assert out["AA"]["y"] == raw.get("age")
    assert out["AA"]["k"] == raw.get("activated_nakshatras")
    assert len(out["AA"]["pl"]) == len(raw.get("activated_planets") or [])
