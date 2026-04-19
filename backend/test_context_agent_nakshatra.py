"""Tests for context_agents.nakshatra (P1/P9 nakshatra rows + optional R/NV/PK)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.agents.nakshatra import _nakshatra_lord
from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_nakshatra_registered():
    assert "nakshatra" in list_agent_ids()


def test_nakshatra_p1_matches_static(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]
    pa = static.get("planetary_analysis") or {}
    if not isinstance(pa, dict) or not pa:
        pytest.skip("planetary_analysis empty")

    out = build_agent(
        "nakshatra",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["a"] == "nakshatra"
    assert out["v"] == 1
    assert "P1" in out

    for planet, pdata in pa.items():
        if planet not in out["P1"]:
            continue
        bi = (pdata or {}).get("basic_info") or {}
        nk = bi.get("nakshatra")
        row = out["P1"][planet]
        if nk:
            assert row.get("nk") == nk
            assert row.get("nl") == _nakshatra_lord(nk)


def test_nakshatra_slice_builds():
    from ai.parallel_chat.context_slices import build_nakshatra_slice

    ctx = {
        "intent": {"category": "general"},
        "current_date_info": {"x": 1},
        "response_format": {"y": 2},
        "nakshatra_remedies": {"Sun": []},
        "navatara_warnings": {},
        "pushkara_navamsa": {"has_pushkara": False},
        "planetary_analysis": {
            "Sun": {
                "basic_info": {
                    "nakshatra": "Ashwini",
                    "nakshatra_pada": 2,
                    "house": 1,
                    "sign_name": "Aries",
                }
            }
        },
        "d9_planetary_analysis": {
            "Sun": {"basic_info": {"nakshatra": "Ashwini", "house": 1, "sign_name": "Aries"}},
        },
    }
    sl = build_nakshatra_slice(ctx)
    assert sl["nakshatra_remedies"] == {"Sun": []}
    assert sl["planetary_analysis"]["Sun"]["basic_info"]["nakshatra"] == "Ashwini"
    assert "degree" not in sl["planetary_analysis"]["Sun"]["basic_info"]
