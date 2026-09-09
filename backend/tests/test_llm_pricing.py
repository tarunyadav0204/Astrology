from datetime import datetime, timezone

from utils.llm_pricing import (
    deepseek_rate_usd_per_million,
    mixed_stage_cost_usd,
    openai_rate_usd_per_million,
)


def test_openai_luna_official_token_rates():
    rate = openai_rate_usd_per_million("gpt-5.6-luna")

    assert rate == {
        "input": 0.20,
        "cached_input": 0.02,
        "output": 1.20,
        "tier": "openai_standard",
        "resolved_model": "gpt-5.6-luna",
    }


def test_admin_chat_cost_resolvers_use_luna_cached_rate():
    from chat_history.admin_routes import _resolve_model_rate
    from credits.routes import _question_cost_rate_for_model

    assert _resolve_model_rate("gpt-5.6-luna")["cached_input"] == 0.02
    assert _question_cost_rate_for_model("gpt-5.6-luna", 1000)["output"] == 1.20


def test_deepseek_v4_flash_off_peak_and_legacy_alias_match():
    saturday = datetime(2026, 8, 22, 7, 0, tzinfo=timezone.utc)
    current = deepseek_rate_usd_per_million("deepseek-v4-flash", priced_at=saturday)
    legacy = deepseek_rate_usd_per_million("deepseek-chat", priced_at=saturday)

    assert current["input"] == 0.22
    assert current["cached_input"] == 0.007
    assert current["output"] == 0.66
    assert legacy == current


def test_deepseek_v4_peak_window_doubles_rates():
    weekday_peak = datetime(2026, 8, 24, 7, 0, tzinfo=timezone.utc)
    rate = deepseek_rate_usd_per_million("deepseek-v4-pro", priced_at=weekday_peak)

    assert rate["input"] == 1.32
    assert rate["cached_input"] == 0.044
    assert rate["output"] == 3.96
    assert rate["tier"] == "deepseek_peak"


def test_mixed_stage_cost_uses_each_stage_model():
    usage = {
        "stages": [
            {
                "llm_model": "models/gemini-3.1-flash-lite",
                "input_tokens": 1000,
                "non_cached_input_tokens": 1000,
                "output_tokens": 100,
            },
            {
                "llm_model": "deepseek-chat",
                "input_tokens": 2000,
                "non_cached_input_tokens": 2000,
                "output_tokens": 200,
            },
        ]
    }

    def resolver(model, _tokens, *, priced_at=None):
        if model == "models/gemini-3.1-flash-lite":
            return {"input": 0.25, "cached_input": 0.025, "output": 1.5}
        return deepseek_rate_usd_per_million(model, priced_at=priced_at)

    result = mixed_stage_cost_usd(
        usage,
        fallback_model_name="deepseek-chat",
        priced_at=datetime(2026, 8, 22, 7, 0, tzinfo=timezone.utc),
        rate_resolver=resolver,
    )

    assert result["input_non_cached"] == 0.001 * 0.25 + 0.002 * 0.22
    assert result["output"] == 0.0001 * 1.5 + 0.0002 * 0.66
