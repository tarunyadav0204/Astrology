from ai.parallel_chat.parallel_agent_payloads import build_nadi_agent_payload
from ai.parallel_chat.prompt_blocks import build_nadi_branch_static_agent
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


def test_nadi_payload_includes_derived_nx_blocks():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_nadi_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="What kind of career is shown in Nadi?",
            precomputed_static=static,
        ),
        "What kind of career is shown in Nadi?",
    )

    assert "nadi" in payload
    assert "nx" in payload
    nx = payload["nx"]
    assert "top" in nx
    assert "sig" in nx
    assert "career" in nx
    assert "relationship" in nx
    assert "wealth" in nx
    assert isinstance(nx["top"], list)
    assert isinstance(nx["sig"], list)
    assert isinstance(nx["career"]["dom"], list)
    assert isinstance(nx["career"]["tags"], list)
    assert "sig" in nx["career"]
    assert "lead" in nx["career"]
    assert "aa_pl" in nx["career"]
    assert isinstance(nx["relationship"]["flags"], list)
    assert "sig" in nx["relationship"]
    assert "aa_pl" in nx["relationship"]
    assert "sig" in nx["wealth"]
    assert "health" not in nx


def test_nadi_agent_prompt_requires_dominant_grahas_and_age_activation_chain():
    prompt = build_nadi_branch_static_agent()
    assert "`nadi` and `nx`" in prompt
    assert "Dominant Nadi Grahas -> Linkage Logic -> Promise vs Activation -> Topic Verdict" in prompt
    assert "nx.top" in prompt
    assert "nx.sig" in prompt
    assert "nx.aa" in prompt
    assert "nx.career" in prompt
    assert "nx.relationship" in prompt
    assert "nx.wealth" in prompt
    assert "nx.health" not in prompt


def test_nadi_health_payload_and_prompt_are_only_present_for_health_questions():
    birth = _birth_data()
    static = ChatContextBuilder()._build_static_context(birth)
    payload = build_nadi_agent_payload(
        AgentContext(
            birth_data=birth,
            user_question="How is my health in Nadi?",
            intent_result={"category": "health"},
            precomputed_static=static,
        ),
        "How is my health in Nadi?",
    )

    nx = payload["nx"]
    assert "health" in nx
    assert "flags" in nx["health"]
    assert "systems" in nx["health"]

    prompt = build_nadi_branch_static_agent("health")
    assert "nx.health" in prompt
    assert "systems" in prompt
