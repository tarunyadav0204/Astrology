from backend.chat_history.routes import _merge_clarification_chain_parts


def test_merge_clarification_chain_keeps_topic_narrowing():
    merged = _merge_clarification_chain_parts(
        ["Tell me about my lagna chart", "career"],
        "potential",
        max_len=200,
    )

    lowered = merged.lower()
    assert "lagna chart" in lowered
    assert "career" in lowered
    assert "potential" in lowered

