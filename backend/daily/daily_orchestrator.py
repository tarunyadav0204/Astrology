from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ai.response_parser import ResponseParser
from ai.term_matcher import find_terms_in_text
from daily.daily_context_reducer import reduce_daily_context
from daily.daily_schema import DAILY_ENGINE_VERSION, build_daily_prompt


async def run_daily_chat_pipeline(
    analyzer,
    *,
    user_question: str,
    astrological_context: Dict[str, Any],
    conversation_history: Optional[List[Dict[str, Any]]],
    language: str,
    user_context: Optional[Dict[str, Any]],
    premium_analysis: bool,
) -> Dict[str, Any]:
    """Dedicated exact-day chat pipeline with reduced context and day-specific prompting."""
    start_time = time.time()
    reduced_context = reduce_daily_context(
        astrological_context,
        user_question=user_question,
        conversation_history=conversation_history or [],
    )
    prompt = build_daily_prompt(
        reduced_context=reduced_context,
        user_question=user_question,
        language=language,
    )

    llm_result = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=premium_analysis,
        llm_log_tag="daily_chat",
    )
    if not llm_result.get("success"):
        return llm_result

    cleaned_text = analyzer._fix_response_formatting(llm_result.get("response") or "")

    if user_context and user_context.get("user_relationship") != "self":
        native_name = astrological_context.get("birth_details", {}).get("name", "the native")
        if native_name and native_name != "the native":
            cleaned_text = analyzer._fix_pronoun_usage(cleaned_text, native_name)

    cleaned_text, faq_metadata = ResponseParser.parse_faq_metadata(cleaned_text)
    parsed = ResponseParser.parse_images_in_chat_response(cleaned_text)
    matched_term_ids, matched_glossary = find_terms_in_text(parsed.get("content") or "", language=language)

    elapsed_s = time.time() - start_time
    response_text = parsed.get("content") or ""
    return {
        "success": True,
        "response": response_text,
        "terms": matched_term_ids,
        "glossary": matched_glossary,
        "summary_image": None,
        "follow_up_questions": parsed.get("follow_up_questions", []),
        "analysis_steps": parsed.get("analysis_steps", []),
        "faq_metadata": faq_metadata,
        "raw_response": llm_result.get("raw_response") or response_text,
        "has_transit_request": False,
        "chat_llm_model": llm_result.get("chat_llm_model"),
        "token_usage": llm_result.get("token_usage") or {},
        "llm_prompt_chars": int(len(prompt)),
        "llm_response_chars": int(len(response_text)),
        "timing": {
            **(llm_result.get("timing") or {}),
            "daily_pipeline_version": DAILY_ENGINE_VERSION,
            "daily_pipeline_elapsed_s": elapsed_s,
        },
    }

