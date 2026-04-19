"""Tests for context_agents.sniper_pts (Bhrigu Bindu, Kharesh, 64th navamsa, Mrityu Bhaga)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.compact_vedic import SIGN_NAMES
from context_agents.registry import build_agent, list_agent_ids


def test_sniper_pts_registered():
    assert "sniper_pts" in list_agent_ids()


def test_sniper_pts_shape_and_aligns_with_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    raw = static.get("sniper_points")
    if not isinstance(raw, dict) or not raw:
        pytest.skip("sniper_points missing in static context")

    out = build_agent(
        "sniper_pts",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "sniper_pts"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "K", "N", "B", "M"}

    kh = raw.get("kharesh") or {}
    if kh.get("error"):
        assert "e" in out["K"]
    else:
        assert out["K"]["kl"] == kh.get("kharesh_lord")
        ds = kh.get("danger_sign")
        if ds in SIGN_NAMES:
            assert out["K"]["s"] == SIGN_NAMES.index(ds) + 1

    n64 = raw.get("navamsa_64th") or {}
    if n64.get("error"):
        assert "e" in out["N"]
    else:
        assert out["N"]["l"] == n64.get("danger_lord")
        ds = n64.get("danger_sign")
        if ds in SIGN_NAMES:
            assert out["N"]["s"] == SIGN_NAMES.index(ds) + 1

    bb = raw.get("bhrigu_bindu") or {}
    if bb.get("error"):
        assert "e" in out["B"]
    else:
        assert out["B"]["h"] == bb.get("house")
        assert out["B"]["ld"] == bb.get("lord")
        assert out["B"]["lon"] == round(float(bb["longitude"]), 2)
        sn = bb.get("sign")
        if sn in SIGN_NAMES:
            assert out["B"]["s"] == SIGN_NAMES.index(sn) + 1

    mb = raw.get("mrityu_bhaga") or {}
    if mb.get("error"):
        assert "e" in out["M"]
    else:
        assert out["M"]["x"] is bool(mb.get("has_affliction"))
        assert isinstance(out["M"]["r"], list)
        assert len(out["M"]["r"]) == len(mb.get("afflicted_points") or [])
        for row in out["M"]["r"]:
            assert "p" in row and "dg" in row and "o" in row and "i" in row
            assert row["i"] in (1, 2)

    assert "upcoming_transits" not in out["B"]


def test_sniper_pts_cached_vs_full_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    if not isinstance(static.get("sniper_points"), dict):
        pytest.skip("sniper_points missing")

    a = build_agent("sniper_pts", AgentContext(birth_data=birth, precomputed_static=static))
    b = build_agent("sniper_pts", AgentContext(birth_data=birth, precomputed_static=None))
    assert a == b
