"""Instant's calculated baseline, reviewed by the shared calculator agent."""
import os
import time
import logging

logger = logging.getLogger(__name__)


async def generate_conversation_response(*, stage_timings_ms, pipeline_started, **kwargs):
    from chat.verified_chat_pipeline import run_verified_calculator_agent
    from utils.admin_settings import get_verified_chat_model

    model = os.getenv("INSTANT_CHAT_AGENT_MODEL") or get_verified_chat_model()
    try:
        timeout = max(15, min(180, float(os.getenv("INSTANT_CHAT_AGENT_TIMEOUT_SECONDS", "120"))))
    except ValueError:
        timeout = 120
    result = await run_verified_calculator_agent(
        **kwargs, model_name=model, timeout_s=timeout, conversation_mode=True,
    )
    elapsed = max(0, time.perf_counter() - pipeline_started)
    from chat.instant_chat_pipeline import _build_instant_usage_stage
    stage = _build_instant_usage_stage(
        "instant_calculator_agent", model, result.get("prompt_chars", 0),
        len(result["response"]), result.get("token_usage"), result.get("success"),
        result.get("elapsed_s", elapsed),
    )
    stage["llm_provider"] = "openai"
    terms, glossary = [], {}
    try:
        from ai.term_matcher import find_terms_in_text
        terms, glossary = find_terms_in_text(result["response"], language=kwargs["language"])
    except Exception:
        logger.warning("Instant conversation glossary unavailable", exc_info=True)
    result.update({
        "raw_response": result["response"], "terms": terms, "glossary": glossary,
        "instant_llm_usage_stages": [stage],
        "follow_up_questions": [], "llm_prompt_chars": result.get("prompt_chars", 0),
        "llm_response_chars": len(result["response"]),
        "timing": {"instant_chat": True, "chat_llm_provider": "openai",
                   "chat_llm_model": model, "total_request_time": elapsed,
                   "instant_stage_timings_ms": {**stage_timings_ms, "pipeline_total": elapsed * 1000},
                   "route_action": "clarify" if result.get("message_type") == "clarification" else "answer"},
    })
    return result
