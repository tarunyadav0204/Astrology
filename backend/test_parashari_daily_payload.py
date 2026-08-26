from ai.parallel_chat.parallel_agent_payloads import (
    _aspect_targets_from_house,
    _transit_summary,
    build_parashari_agent_payload,
)
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext


def _birth_data():
    return {
        "name": "Reference Chart",
        "date": "1980-04-02",
        "time": "14:55",
        "latitude": 29.1492,
        "longitude": 75.7217,
        "place": "Hisar, Haryana, India",
        "timezone": 5.5,
    }


def test_compact_parashari_nodal_activation_has_no_fifth_or_ninth_target():
    # From House 2: conjunction=H2, fifth=H6, seventh=H8, ninth=H10.
    assert _aspect_targets_from_house(2, "Rahu") == [2, 8]
    assert _aspect_targets_from_house(2, "Ketu") == [2, 8]


def test_compact_parashari_filters_precomputed_nodal_fifth_and_ninth_transits():
    summary = _transit_summary(
        [6, 8, 10],
        {"ad": {"p": "Rahu"}},
        {
            "A": [
                {"tp": "Rahu", "np": "Sun", "an": 5, "th": 6, "nh": 1},
                {"tp": "Rahu", "np": "Moon", "an": 7, "th": 8, "nh": 2},
                {"tp": "Ketu", "np": "Mars", "an": 9, "th": 10, "nh": 3},
                # Jupiter's 5th aspect remains valid even when Rahu is the natal target.
                {"tp": "Jupiter", "np": "Rahu", "an": 5, "th": 6, "nh": 2},
            ]
        },
    )

    assert summary["n"] == 2
    assert summary["th"] == {"6": 1, "8": 1}
    assert [(row["tp"], row["an"]) for row in summary["dp"]] == [
        ("Rahu", 7),
        ("Jupiter", 5),
    ]


def test_parashari_payload_includes_exact_day_block_when_dasha_as_of_present():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="How is tomorrow?",
            intent_result={
                "mode": "PREDICT_DAILY",
                "category": "general",
                "needs_transits": True,
                "dasha_as_of": "2026-04-23",
                "transit_request": {"startYear": 2026, "endYear": 2026, "yearMonthMap": {"2026": ["April"]}},
            },
            precomputed_static=static,
        ),
        "How is tomorrow?",
    )

    agents = payload["parashari_agents"]
    assert "parashari_day" in agents
    assert payload["px"]["src"] == "day"
    assert payload["px"]["cat"] == "general"
    assert payload["px"]["hs"] == [1, 5, 7, 10]
    assert payload["px"]["dv"]["D9"] is True
    day = agents["parashari_day"]
    assert day["x"] is True
    assert day["dt"] == "2026-04-23"
    assert day["M"]["p"] == "Moon"
    assert day["P"]["vr"]
    fast_planets = {row["p"] for row in day["F"]}
    assert {"Sun", "Moon", "Mercury", "Venus", "Mars"}.issubset(fast_planets)


def test_parashari_payload_day_block_is_disabled_without_exact_day():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="How is 2027 for career?",
            intent_result={
                "mode": "PREDICT_PERIOD_OUTLOOK",
                "category": "career",
                "needs_transits": True,
                "transit_request": {"startYear": 2027, "endYear": 2027, "yearMonthMap": {"2027": ["January", "February"]}},
            },
            precomputed_static=static,
        ),
        "How is 2027 for career?",
    )

    assert payload["parashari_agents"]["parashari_day"]["x"] is False
    assert payload["px"]["src"] == "window"
    assert payload["px"]["cat"] == "career"
    assert payload["px"]["hs"] == [10, 6, 2, 11]
    assert "D10" in payload["px"]["dv"]
    assert payload["px"]["D"]["md"]["p"]
    assert "10" in payload["px"]["HI"]
