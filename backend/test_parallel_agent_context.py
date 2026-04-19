"""Tests for parallel chat agent-context path (ASTRO_PARALLEL_AGENT_CONTEXT)."""

from __future__ import annotations

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext

from ai.parallel_chat.agent_context_factory import (
    merged_context_to_agent_context,
    merged_context_to_birth_data,
    parallel_agent_context_enabled,
)
from ai.parallel_chat import parallel_agent_payloads as pap


def test_parallel_agent_context_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ASTRO_PARALLEL_AGENT_CONTEXT", raising=False)
    assert parallel_agent_context_enabled() is False


def test_parallel_agent_context_env(monkeypatch):
    monkeypatch.setenv("ASTRO_PARALLEL_AGENT_CONTEXT", "1")
    assert parallel_agent_context_enabled() is True


def test_merged_context_to_birth_data():
    merged = {
        "birth_details": {
            "name": "X",
            "date": "1980-01-01",
            "time": "12:00",
            "place": "Y",
            "latitude": 1.0,
            "longitude": 2.0,
            "timezone": "Asia/Kolkata",
        }
    }
    bd = merged_context_to_birth_data(merged)
    assert bd["date"] == "1980-01-01"
    assert bd["latitude"] == 1.0


def test_merged_context_to_agent_context_splits_dynamic():
    merged = {
        "birth_details": {
            "name": "X",
            "date": "1980-01-01",
            "time": "12:00",
            "place": "Y",
            "latitude": 1.0,
            "longitude": 2.0,
        },
        "planetary_analysis": {"Sun": {}},
        "current_dashas": {"mahadasha": {"planet": "Jupiter"}},
        "intent": {"mode": "birth", "category": "general"},
    }
    ac = merged_context_to_agent_context(merged, user_question="test q")
    assert ac.user_question == "test q"
    assert ac.precomputed_static is not None
    assert "planetary_analysis" in ac.precomputed_static
    assert ac.precomputed_dynamic is not None
    assert "current_dashas" in ac.precomputed_dynamic


def test_build_all_parallel_agent_payloads_structure(monkeypatch):
    def fake_build(agent_id: str, ctx: AgentContext) -> dict:
        return {"a": agent_id, "v": 1}

    monkeypatch.setattr(pap, "build_agent", fake_build)
    ctx = AgentContext(
        birth_data={"date": "2000-01-01", "time": "12:00", "latitude": 0, "longitude": 0},
        user_question="q",
    )
    out = pap.build_all_parallel_agent_payloads(ctx, "hello")
    assert "parashari_agents" in out["parashari"]
    assert out["parashari"]["parashari_agents"]["core_d1"]["a"] == "core_d1"
    assert out["jaimini"]["jaimini"]["a"] == "jaimini"
    assert "vim_dasha" in out["nakshatra"]
    assert "vim_dasha" in out["kp"]
    assert out["ashtakavarga"]["ashtakavarga"]["a"] == "ashtakavarga"


def test_parashari_agent_payload_includes_special_points_from_merged(monkeypatch):
    def fake_build(agent_id: str, ctx: AgentContext) -> dict:
        return {"a": agent_id}

    monkeypatch.setattr(pap, "build_agent", fake_build)
    ac = AgentContext(
        birth_data={"date": "2000-01-01", "time": "12:00", "latitude": 0, "longitude": 0},
        user_question="q",
    )
    merged = {
        "special_points": {
            "yogi_points": {"yogi": {"lord": "Jupiter"}},
            "gandanta_analysis": {"planets": []},
        }
    }
    pl = pap.build_parashari_agent_payload(ac, "hi", merged_chart_context=merged)
    assert pl["special_points"]["yogi_points"]["yogi"]["lord"] == "Jupiter"
