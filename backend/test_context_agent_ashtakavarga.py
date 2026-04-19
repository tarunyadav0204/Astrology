"""Tests for context_agents.ashtakavarga."""

import os
import sys

import pytest

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from context_agents.agents import ashtakavarga as av_mod
from context_agents.base import AgentContext
from context_agents.registry import build_agent, list_agent_ids

from ai.parallel_chat.context_slices import build_ashtakavarga_slice


def test_ashtakavarga_registered():
    assert "ashtakavarga" in list_agent_ids()


def test_build_ashtakavarga_slice_injects_ho():
    """Legacy parallel slice gets Ho/La on d1_rashi when ascendant + AV exist."""
    ctx = {
        "ashtakavarga": {
            "d1_rashi": {
                "sarvashtakavarga": {
                    "sarvashtakavarga": {str(i): [30, 32, 38, 18, 30, 23, 32, 32, 20, 26, 27, 31][i] for i in range(12)},
                    "total_bindus": 337,
                },
                "bhinnashtakavarga": {
                    p: {"bindus": {str(i): (i + ord(p[0])) % 7 for i in range(12)}}
                    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                },
            }
        },
        "ascendant_info": {"sign_number": 5},
        "d1_chart": {"ascendant": 120.0},
        "birth_details": {},
        "house_lordships": {},
        "intent": {},
        "current_date_info": {},
        "response_format": {},
    }
    sl = build_ashtakavarga_slice(ctx)
    ho = sl["ashtakavarga"]["d1_rashi"]["Ho"]
    assert ho["4"]["s"] == 32 and ho["12"]["s"] == 18


def test_houses_from_lagna_leo_asc_matches_zodiac_rows():
    """Leo lagna (sign index 4): 4th house = Scorpio (idx 7), 12th = Cancer (idx 3)."""
    sav = [30, 32, 38, 18, 30, 23, 32, 32, 20, 26, 27, 31]
    bav = {p: [i % 7 for i in range(12)] for p in av_mod._PLANETS}
    ho = av_mod._houses_from_lagna(sav, bav, asc_sign_0=4)
    assert ho["4"]["zn"] == "Scorpio" and ho["4"]["s"] == 32
    assert ho["12"]["zn"] == "Cancer" and ho["12"]["s"] == 18
    assert ho["10"]["zn"] == "Taurus" and ho["10"]["s"] == 32


def test_ashtakavarga_shape(context_agent_cached):
    birth = context_agent_cached["birth"]
    static = context_agent_cached["static"]
    out = build_agent(
        "ashtakavarga",
        AgentContext(birth_data=birth, precomputed_static=static),
    )
    assert out["a"] == "ashtakavarga"
    assert out["v"] == 2
    assert "sc" in out
    assert "D1" in out
    d1 = out["D1"]
    assert "S" in d1 and len(d1["S"]) == 12
    assert "B" in d1 and isinstance(d1["B"], dict)
    # v2: house-from-lagna map when static has ascendant (integration fixture does)
    assert "Ho" in d1 and "La" in d1
    assert set(d1["Ho"].keys()) == {str(i) for i in range(1, 13)}
    h1 = d1["Ho"]["1"]
    assert "z" in h1 and "zn" in h1 and "s" in h1 and "B" in h1
    si = int(h1["z"]) - 1
    assert d1["S"][si] == h1["s"]
    assert d1["B"]["Sun"][si] == h1["B"]["Sun"]
