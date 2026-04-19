"""Tests for context_agents.core_d1 (compact D1 agent).

Integration tests load the latest birth chart for userid 7 (override with
CONTEXT_AGENT_TEST_USER_ID). Requires POSTGRES_DSN or DATABASE_URL and at
least one birth_charts row for that user. Without DB/chart, those tests are
skipped so CI can still run test_core_d1_registered.

To print the agent JSON for manual structure review (no pytest), use:
  python3 -m context_agents.print_agent_json --user-id 7
"""

import json
import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.base import AgentContext
from context_agents.birth_from_db import fetch_latest_birth_for_user, load_backend_dotenv
from context_agents.compact_vedic import sign_name_from_1_12
from context_agents.registry import build_agent, list_agent_ids

load_backend_dotenv()

# Default: your user id; override for another account, e.g. CONTEXT_AGENT_TEST_USER_ID=12
TEST_USER_ID = int(os.environ.get("CONTEXT_AGENT_TEST_USER_ID", "7"))


@pytest.fixture(scope="module")
def birth_self_chart():
    """Birth dict for agents: latest birth_charts row for TEST_USER_ID (any relation)."""
    try:
        return fetch_latest_birth_for_user(TEST_USER_ID)
    except RuntimeError as e:
        pytest.skip(str(e))


def test_core_d1_registered():
    assert "core_d1" in list_agent_ids()


def test_sign_numbering_is_one_based_with_names():
    """1=Aries … 5=Leo, 6=Virgo (not 0-based)."""
    assert sign_name_from_1_12(5) == "Leo"
    assert sign_name_from_1_12(6) == "Virgo"


def test_core_d1_shape_and_size(birth_self_chart):
    ctx = AgentContext(birth_data=birth_self_chart, user_question="career?")
    out = build_agent("core_d1", ctx)

    assert out["a"] == "core_d1"
    assert out["v"] == 3
    assert set(out.keys()) == {"a", "v", "b", "L", "P", "H"}
    assert set(out["b"].keys()) == {"n", "d", "t"}

    assert out["b"]["n"] == birth_self_chart["name"]
    assert out["L"]["s"] in range(1, 13)
    assert 0 <= out["L"]["d"] < 30
    assert out["L"]["nm"] == sign_name_from_1_12(out["L"]["s"])

    assert len(out["P"]) == 9
    for row in out["P"]:
        assert len(row) == 5
        name, lon, s, snm, h = row
        assert name in (
            "Sun",
            "Moon",
            "Mars",
            "Mercury",
            "Jupiter",
            "Venus",
            "Saturn",
            "Rahu",
            "Ketu",
        )
        assert 0 <= lon < 360
        assert s in range(1, 13)
        assert isinstance(snm, str) and len(snm) > 2
        assert snm == sign_name_from_1_12(s)
        assert h in range(1, 13)

    assert isinstance(out["H"], dict)
    for lord, houses in out["H"].items():
        assert isinstance(houses, list)
        for hh in houses:
            assert hh in range(1, 13)

    raw = json.dumps(out, separators=(",", ":"))
    assert len(raw) < 12_000, f"payload unexpectedly large: {len(raw)} bytes"


def test_core_d1_no_duplicate_birth_in_p(birth_self_chart):
    out = build_agent("core_d1", AgentContext(birth_data=birth_self_chart))
    blob = json.dumps(out)
    assert blob.count('"n"') == 1
