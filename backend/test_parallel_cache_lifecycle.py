from ai.base_ai_context_generator import BaseAIContextGenerator
from chat.chat_context_builder import ChatContextBuilder


def test_chat_context_builder_cache_expires(monkeypatch):
    builder = ChatContextBuilder()
    builder._static_cache_ttl_s = 10

    clock = {"now": 1000.0}
    monkeypatch.setattr("chat.chat_context_builder.time.time", lambda: clock["now"])

    builder._cache_set(builder.static_cache, builder._static_cache_ts, "a", {"v": 1}, 8)
    assert builder._cache_get(builder.static_cache, builder._static_cache_ts, "a", 10) == {"v": 1}

    clock["now"] = 1011.0
    assert builder._cache_get(builder.static_cache, builder._static_cache_ts, "a", 10) is None
    assert "a" not in builder.static_cache


def test_chat_context_builder_cache_evicts_oldest(monkeypatch):
    builder = ChatContextBuilder()
    clock = {"now": 1000.0}
    monkeypatch.setattr("chat.chat_context_builder.time.time", lambda: clock["now"])

    builder._cache_set(builder.static_cache, builder._static_cache_ts, "a", {"v": 1}, 2)
    clock["now"] = 1001.0
    builder._cache_set(builder.static_cache, builder._static_cache_ts, "b", {"v": 2}, 2)
    clock["now"] = 1002.0
    builder._cache_set(builder.static_cache, builder._static_cache_ts, "c", {"v": 3}, 2)

    assert set(builder.static_cache.keys()) == {"b", "c"}
    assert "a" not in builder._static_cache_ts


def test_base_context_generator_cache_expires(monkeypatch):
    generator = BaseAIContextGenerator()
    generator._static_cache_ttl_s = 10

    clock = {"now": 2000.0}
    monkeypatch.setattr("ai.base_ai_context_generator.time.time", lambda: clock["now"])

    generator._cache_set("a", {"v": 1})
    assert generator._cache_get("a") == {"v": 1}

    clock["now"] = 2011.0
    assert generator._cache_get("a") is None
    assert "a" not in generator.static_cache


def test_base_context_generator_cache_evicts_oldest(monkeypatch):
    generator = BaseAIContextGenerator()
    generator._static_cache_max_entries = 2

    clock = {"now": 2000.0}
    monkeypatch.setattr("ai.base_ai_context_generator.time.time", lambda: clock["now"])

    generator._cache_set("a", {"v": 1})
    clock["now"] = 2001.0
    generator._cache_set("b", {"v": 2})
    clock["now"] = 2002.0
    generator._cache_set("c", {"v": 3})

    assert set(generator.static_cache.keys()) == {"b", "c"}
    assert "a" not in generator._static_cache_ts
