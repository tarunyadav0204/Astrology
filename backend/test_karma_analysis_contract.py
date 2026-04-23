from ai.karma_gemini_analyzer import KarmaGeminiAnalyzer, json_dumps_karma_safe
from calculators.karma_context_builder import KarmaContextBuilder
from datetime import datetime


def test_shashtiamsa_deity_uses_reverse_order_for_even_signs():
    info = KarmaContextBuilder.get_shashtiamsa_deity_info(1.0, 2)

    assert info["raw_index"] == 2
    assert info["applied_index"] == 57
    assert info["direction"] == "reverse"
    assert info["deity"] == "Payodhi"


def test_shashtiamsa_deity_uses_direct_order_for_odd_signs():
    info = KarmaContextBuilder.get_shashtiamsa_deity_info(1.0, 1)

    assert info["raw_index"] == 2
    assert info["applied_index"] == 2
    assert info["direction"] == "direct"
    assert info["deity"] == "Deva"


def test_karma_prompt_has_confidence_and_safety_contract():
    analyzer = object.__new__(KarmaGeminiAnalyzer)
    prompt = analyzer._build_karma_prompt(
        {
            "karma_evidence": {
                "d60_confidence": {"boundary_risk": "high"},
                "current_activation": {"mahadasha": "Saturn"},
            },
            "karmic_timing": {
                "current_vimshottari": {
                    "mahadasha": "Saturn",
                    "antardasha": "Venus",
                    "pratyantardasha": "Moon",
                }
            },
        },
        native_name="Test",
    )

    assert "Treat \"past life\" language as a symbolic karmic pattern" in prompt
    assert "D60 is highly birth-time sensitive" in prompt
    assert "Do not invent exact classical citations" in prompt
    assert "Current Vimshottari" in prompt
    assert "### 1. Karma Snapshot" in prompt
    assert "### 10. Final Guidance" in prompt


def test_karma_prompt_serializes_datetime_chart_values():
    analyzer = object.__new__(KarmaGeminiAnalyzer)
    prompt = analyzer._build_karma_prompt(
        {
            "d1_chart": {
                "generated_at": datetime(2026, 4, 23, 9, 30),
                "planets": {"Sun": {"longitude": 10.0}},
            },
            "karma_evidence": {},
            "karmic_timing": {},
        }
    )

    assert "2026-04-23 09:30:00" in prompt


def test_karma_route_persistence_serializes_datetime_values():
    encoded = json_dumps_karma_safe({"generated_at": datetime(2026, 4, 23, 9, 30)})

    assert "2026-04-23 09:30:00" in encoded
