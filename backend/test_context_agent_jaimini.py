"""Tests for context_agents.jaimini (points, chara karakas, argala)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_jaimini_registered():
    assert "jaimini" in list_agent_ids()


def test_jaimini_aligns_with_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    jp_raw = static.get("jaimini_points") or {}
    ck_raw = static.get("chara_karakas") or {}
    ag_raw = (static.get("relationships") or {}).get("argala_analysis") or {}
    if not jp_raw or not ck_raw.get("chara_karakas"):
        pytest.skip("jaimini_points or chara_karakas missing")

    out = build_agent(
        "jaimini",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "jaimini"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "sc", "JP", "CK", "AG"}

    for long_k, short_k in (
        ("arudha_lagna", "AL"),
        ("upapada_lagna", "UL"),
        ("karkamsa_lagna", "KL"),
    ):
        block = jp_raw.get(long_k) or {}
        sid = block.get("sign_id")
        if isinstance(sid, int) and short_k in out["JP"]:
            assert out["JP"][short_k]["s"] == (int(sid) % 12) + 1

    inner = ck_raw.get("chara_karakas") or {}
    ak = inner.get("Atmakaraka") or {}
    if ak.get("planet"):
        assert out["CK"]["AK"]["p"] == ak["planet"]
        assert out["CK"]["AK"]["h"] == ak.get("house")
        assert out["CK"]["AK"]["s"] == int(ak.get("sign", 0)) + 1

    if isinstance(ag_raw, dict) and ag_raw:
        h1 = ag_raw.get(1) or ag_raw.get("1")
        if isinstance(h1, dict):
            g1 = out["AG"].get("1")
            assert g1 is not None
            assert g1["n"] == h1.get("net_argala_strength")
            assert len(g1["ap"]) == len(h1.get("argala_planets") or [])
            assert len(g1["vp"]) == len(h1.get("virodha_argala_planets") or [])
            assert isinstance(g1["g"], int) and 1 <= g1["g"] <= 7


def test_jaimini_cached_vs_full_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    if not static.get("jaimini_points"):
        pytest.skip("no jaimini_points")

    a = build_agent("jaimini", AgentContext(birth_data=birth, precomputed_static=static))
    b = build_agent("jaimini", AgentContext(birth_data=birth, precomputed_static=None))
    assert a == b
