from ai.parallel_chat.parallel_agent_payloads import (
    build_ashtakavarga_agent_payload,
    build_jaimini_agent_payload,
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


def test_parashari_payload_exposes_career_and_relationship_topic_blocks():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="What exactly will I do in career?",
            intent_result={"category": "career"},
            precomputed_static=static,
        ),
        "What exactly will I do in career?",
    )

    px = payload["px"]
    assert "career" in px
    assert "relationship" in px
    assert px["career"]["hs"] == [10, 6, 2, 11]
    assert "mode" in px["career"]
    assert "fn" in px["career"]
    assert "vis" in px["career"]
    assert isinstance(px["career"]["fn"], list)
    assert px["relationship"]["hs"] == [7, 2, 8, 11]
    assert "mat" in px["relationship"]
    assert "fr" in px["relationship"]
    assert "ct" in px["relationship"]
    assert "health" not in px


def test_parashari_payload_exposes_health_topic_block():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="How is my health pattern?",
            intent_result={"category": "health", "divisional_charts": ["D1", "D9", "D30"]},
            precomputed_static=static,
        ),
        "How is my health pattern?",
    )

    px = payload["px"]
    assert "health" in payload["parashari_agents"]
    assert "health" in px
    assert px["health"]["hs"] == [1, 6, 8, 12, 4, 5]
    assert px["health"]["dv"]["D30"] is True
    assert px["health"]["pattern"] in {"acute", "chronic", "sensitivity", "mixed", "preventive"}
    assert px["health"]["tone"] in {"flare-up", "wear-and-tear", "mind-body", "mixed"}
    assert "risk" in px["health"]
    assert "body" in px["health"]
    assert "charak" in px["health"]
    assert px["health"]["charak"]["charak"] in {"vata", "pitta", "kapha", "mixed"}
    assert "rw" in px["health"]
    assert "score" in px["health"]


def test_parashari_payload_exposes_divisional_reasoning_spine_for_career():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="What exactly will I do in career?",
            intent_result={"category": "career", "divisional_charts": ["D1", "D9", "D10", "Karkamsa"]},
            precomputed_static=static,
        ),
        "What exactly will I do in career?",
    )

    dx = payload["px"]["dx"]
    assert dx["cat"] == "career"
    assert isinstance(dx["rf"], list) and dx["rf"]
    assert "topic" in dx and "charts" in dx["topic"]
    assert dx["topic"]["avail"]["D10"] is True
    assert dx["topic"]["avail"]["Karkamsa"] is True
    assert "D10" in dx["topic"]["charts"]
    assert "rows" in dx["topic"]["charts"]["D10"]
    assert dx["topic"]["charts"]["D10"]["rows"]
    assert "support" in dx["topic"]["charts"]["D10"]
    assert "current" in dx
    assert "topic" in dx["current"]
    assert dx["current"]["topic"]["avail"]["D10"] is True
    assert "D10" in dx["current"]["topic"]["charts"]
    assert dx["current"]["topic"]["charts"]["D10"]["rows"]
    assert dx["current"]["topic"]["charts"]["D10"]["rows"][0]["lvl"] in {"md", "ad", "pd"}


def test_parashari_payload_exposes_divisional_reasoning_spine_for_relationship():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="Will marriage manifest well?",
            intent_result={"category": "marriage", "divisional_charts": ["D1", "D9", "D7"]},
            precomputed_static=static,
        ),
        "Will marriage manifest well?",
    )

    dx = payload["px"]["dx"]
    assert dx["cat"] == "marriage"
    assert dx["topic"]["avail"]["D9"] is True
    assert dx["topic"]["avail"]["D7"] is True
    assert "D9" in dx["topic"]["charts"]
    assert "D7" in dx["topic"]["charts"]
    assert dx["relationship"]["charts"]["D9"]["rows"]
    assert dx["relationship"]["charts"]["D7"]["rows"]
    assert dx["current"]["topic"]["avail"]["D9"] is True
    assert dx["current"]["topic"]["avail"]["D7"] is True
    assert dx["current"]["topic"]["charts"]["D9"]["rows"]
    assert dx["current"]["topic"]["charts"]["D7"]["rows"]


def test_parashari_divisional_payload_honors_missing_requested_chart():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_parashari_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="What exactly will I do in career?",
            intent_result={"category": "career"},
            precomputed_static=static,
        ),
        "What exactly will I do in career?",
    )

    dx = payload["px"]["dx"]
    assert payload["px"]["dv"]["D10"] is False
    assert dx["topic"]["avail"]["D10"] is False
    assert "D10" not in dx["topic"]["charts"]
    assert dx["current"]["topic"]["avail"]["D10"] is False
    assert "D10" not in dx["current"]["topic"]["charts"]


def test_jaimini_payload_exposes_career_and_relationship_topic_blocks():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_jaimini_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="Will marriage and career manifest well?",
            precomputed_static=static,
        ),
        "Will marriage and career manifest well?",
    )

    jx = payload["jx"]
    assert "career" in jx
    assert "relationship" in jx
    assert "rf" in jx["career"]
    assert "img" in jx["career"]
    assert "md" in jx["career"]
    assert "ad" in jx["career"]
    assert "rf" in jx["relationship"]
    assert "gk_a7" in jx["relationship"]
    assert "ul2_pp" in jx["relationship"]
    assert jx["relationship"]["a7"] == payload["jaimini"]["JP"]["A7"]["s"]


def test_ashtakavarga_payload_exposes_derived_ax_blocks():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_ashtakavarga_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="Will career improve this year?",
            intent_result={"category": "career"},
            precomputed_static=static,
        ),
        "Will career improve this year?",
    )

    ax = payload["ax"]
    assert ax["cat"] == "career"
    assert ax["hs"] == [10, 6, 2, 11]
    assert isinstance(ax["top"], list) and ax["top"]
    assert isinstance(ax["weak"], list) and ax["weak"]
    assert "rows" in ax["topic"]
    assert "support" in ax["topic"]
    assert "dasha" in ax and isinstance(ax["dasha"], dict)
    assert "transit" in ax and isinstance(ax["transit"], dict)
    assert "conflicts" in ax and isinstance(ax["conflicts"], list)
