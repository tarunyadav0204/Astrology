"""Unit tests for context_agents.scope (no chart / DB)."""

import os
import sys

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.scope import ContextTimeScope, resolve_context_scope


def test_resolve_lifespan_is_full(monkeypatch):
    monkeypatch.delenv("CONTEXT_AGENT_TIME_SCOPE", raising=False)
    assert (
        resolve_context_scope({"mode": "LIFESPAN_EVENT_TIMING"}, None, None)
        == ContextTimeScope.FULL
    )


def test_resolve_daily_is_current(monkeypatch):
    monkeypatch.delenv("CONTEXT_AGENT_TIME_SCOPE", raising=False)
    assert resolve_context_scope({"mode": "PREDICT_DAILY"}, None, None) == ContextTimeScope.CURRENT


def test_resolve_transit_years_intent_window(monkeypatch):
    monkeypatch.delenv("CONTEXT_AGENT_TIME_SCOPE", raising=False)
    assert (
        resolve_context_scope(
            {"transit_request": {"startYear": 2026, "endYear": 2027}},
            None,
            None,
        )
        == ContextTimeScope.INTENT_WINDOW
    )


def test_explicit_override(monkeypatch):
    monkeypatch.delenv("CONTEXT_AGENT_TIME_SCOPE", raising=False)
    assert resolve_context_scope({}, None, "full") == ContextTimeScope.FULL


def test_env_override(monkeypatch):
    monkeypatch.setenv("CONTEXT_AGENT_TIME_SCOPE", "current")
    assert resolve_context_scope({"mode": "LIFESPAN_EVENT_TIMING"}, None, None) == ContextTimeScope.CURRENT
