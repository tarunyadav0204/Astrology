"""Tests for context_agents.vim_dasha (current Vimshottari + maraka + chat parity hints)."""

import copy
import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids


def test_vim_dasha_registered():
    assert "vim_dasha" in list_agent_ids()


def test_vim_dasha_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]
    out = build_agent(
        "vim_dasha",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    assert out["a"] == "vim_dasha"
    assert out["v"] == 1
    assert set(out.keys()) == {"a", "v", "sc", "D"}
    d = out["D"]
    assert set(d.keys()) == {"md", "ad", "pd", "sk", "pr", "mn", "ml", "mk"}
    for key in ("md", "ad", "pd", "sk", "pr"):
        assert "p" in d[key]
        assert isinstance(d[key]["p"], str)
    assert isinstance(d["mn"], int)
    assert isinstance(d["ml"], str)
    assert isinstance(d["mk"], dict)


def test_vim_dasha_matches_augmented_dynamic(context_agent_cached):
    """Same enrichment as `build_complete_context` merge (no second full chat build)."""
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    dynamic = context_agent_cached["dynamic"]

    cd = copy.deepcopy(dynamic.get("current_dashas") or {})
    ChatContextBuilder().augment_current_dashas_with_chart_hints(
        cd,
        static.get("d1_chart") or {},
        dynamic.get("house_lordships") or {},
    )

    out = build_agent(
        "vim_dasha",
        AgentContext(
            birth_data=birth,
            precomputed_static=static,
            precomputed_dynamic=dynamic,
        ),
    )
    D = out["D"]

    assert D["md"]["p"] == cd["mahadasha"]["planet"]
    assert D["ad"]["p"] == cd["antardasha"]["planet"]
    assert D["pd"]["p"] == cd["pratyantardasha"]["planet"]
    assert D["sk"]["p"] == cd["sookshma"]["planet"]
    assert D["pr"]["p"] == cd["prana"]["planet"]
    assert D["mn"] == cd["moon_nakshatra"]
    assert D["ml"] == cd["moon_lord"]
    assert D["mk"] == cd.get("maraka_analysis", {})

    for level, comp in (
        ("mahadasha", "md"),
        ("antardasha", "ad"),
        ("pratyantardasha", "pd"),
    ):
        hint = cd.get(level, {}).get("analysis_hint")
        if hint:
            assert D[comp].get("ah") == hint
