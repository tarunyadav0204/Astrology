"""
Pytest hooks and shared fixtures for tests under `backend/`.

Context-agent integration tests share one heavy `_build_static_context` +
`_build_dynamic_context` per test session so each test file does not repeat
full chart builds (see `context_agent_cached`).
"""

from __future__ import annotations

import os
import sys
from contextlib import redirect_stderr, redirect_stdout

import pytest

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)


@pytest.fixture(scope="session")
def context_agent_birth():
    """Latest `birth_charts` row for CONTEXT_AGENT_TEST_USER_ID (default 7)."""
    from context_agents.birth_from_db import fetch_latest_birth_for_user, load_backend_dotenv

    load_backend_dotenv()
    uid = int(os.environ.get("CONTEXT_AGENT_TEST_USER_ID", "7"))
    try:
        return fetch_latest_birth_for_user(uid)
    except RuntimeError as e:
        pytest.skip(str(e))


@pytest.fixture(scope="session")
def context_agent_cached(context_agent_birth):
    """
    One static + one dynamic context for the session (same pipeline as chat).

    Keys: ``birth``, ``static``, ``dynamic``. Pass into ``AgentContext`` as
    ``precomputed_static`` / ``precomputed_dynamic`` so agents skip rebuilds.
    """
    from chat.chat_context_builder import ChatContextBuilder

    birth = context_agent_birth
    builder = ChatContextBuilder()
    birth_hash = builder._create_birth_hash(birth)
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        builder.static_cache[birth_hash] = builder._build_static_context(birth)
        static = builder.static_cache[birth_hash]
        dynamic = builder._build_dynamic_context(birth, "", None, None, None)
    return {"birth": birth, "static": static, "dynamic": dynamic}
