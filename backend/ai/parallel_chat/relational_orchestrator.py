"""Opt-in relational/two-person parallel chat pipeline."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.output_schema import FAQ_META_INSTRUCTION, build_multi_question_focus_instruction
from ai.parallel_chat.orchestrator import (
    _create_gemini_parallel_cache,
    _delete_parallel_cache,
    _json_compact,
    _llm_call_metrics,
    _log_parallel_llm_summary,
    _run_branch_json,
    _totals_from_rows,
)
from ai.parallel_chat.config import parallel_branch_stagger_s
from ai.parallel_chat.relational_payloads import (
    build_relational_branch_payloads,
    build_relational_evidence_spine,
    build_relationship_profile,
)
from ai.parallel_chat.relational_prompt_blocks import (
    build_relational_branch_static,
    build_relational_merge_static,
)
from ai.relational_answer_evaluator import RelationalAnswerEvaluator
from ai.relational_response_contract import RelationalResponseContract
from ai.response_parser import ResponseParser
from ai.term_matcher import find_terms_in_text
from utils.admin_settings import (
    get_chat_llm_provider,
    get_chat_llm_provider_premium,
    get_gemini_chat_model,
    get_gemini_premium_model,
)

logger = logging.getLogger(__name__)

_CORE_RELATIONAL_BRANCHES = (
    "parashari_relational",
    "jaimini_relational",
    "nadi_relational",
    "kp_relational",
    "nakshatra_relational",
    "timing_relational",
)
_OPTIONAL_RELATIONAL_BRANCHES = (
    "ashtakavarga_relational",
    "sudarshan_relational",
)


def _compact_branch_output(branch: str, output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        return {"branch": branch, "status": "unavailable"}
    bullets = output.get("bullets") or []
    if not isinstance(bullets, list):
        bullets = []
    limits = output.get("limits") or []
    if not isinstance(limits, list):
        limits = []
    analysis = str(output.get("analysis") or "")
    compact: Dict[str, Any] = {
        "branch": branch,
        "status": output.get("status"),
        "scope": output.get("scope"),
        "confidence": output.get("confidence"),
        "bullets": [str(item) for item in bullets[:5]],
        "limits": [str(item) for item in limits[:4]],
    }
    if analysis:
        compact["analysis_excerpt"] = analysis[:1200]
    if output.get("error"):
        compact["error"] = output.get("error")
    if output.get("skip_reason"):
        compact["skip_reason"] = output.get("skip_reason")
    return compact


async def run_parallel_relational_chat_pipeline(
    analyzer: Any,
    *,
    user_question: str,
    astrological_context: Dict[str, Any],
    conversation_history: List[Dict[str, Any]],
    language: str,
    response_style: str,
    user_context: Optional[Dict],
    premium_analysis: bool,
    mode: str,
    total_request_start: float,
) -> Dict[str, Any]:
    del response_style, user_context, mode  # Relational merge is question-shaped; these remain in signature parity.

    ctx = astrological_context
    t_parallel = time.time()
    payloads = build_relational_branch_payloads(ctx, user_question)
    relation_profile = build_relationship_profile(ctx, user_question)
    evidence_spine = build_relational_evidence_spine(ctx, user_question)
    enabled_branches = _enabled_relational_branches(evidence_spine)
    stagger_s = parallel_branch_stagger_s()
    llm_provider = get_chat_llm_provider_premium() if premium_analysis else get_chat_llm_provider()
    gemini_model_name = get_gemini_premium_model() if premium_analysis else get_gemini_chat_model()
    cache_payload = {
        "relationship": relation_profile,
        "relational_evidence": evidence_spine,
        "history": conversation_history or [],
        "current_question": user_question,
    }
    cache_resource, cached_model, cache_setup_input_chars, cache_setup_input_tokens = await _create_gemini_parallel_cache(
        llm_provider=llm_provider,
        model_name=gemini_model_name,
        cache_payload=cache_payload,
        cache_label="parallel_relational",
    )

    tasks = []
    for idx, branch in enumerate(enabled_branches):
        tasks.append(
            asyncio.create_task(
                _run_branch_json(
                    analyzer,
                    build_relational_branch_static(branch),
                    payloads[branch],
                    premium_analysis,
                    branch,
                    critical=branch == "parashari_relational",
                    start_delay_s=idx * stagger_s,
                    model_override=cached_model,
                    model_name_override=gemini_model_name if cached_model else None,
                )
            )
        )
    try:
        branch_results = await asyncio.gather(*tasks)
    except Exception:
        await _delete_parallel_cache(cache_resource, cache_label="parallel_relational")
        raise
    branch_outputs = {branch: out for branch, (out, _metrics) in zip(enabled_branches, branch_results)}
    branch_llm_rows = [metrics for _out, metrics in branch_results]
    parallel_ms = round((time.time() - t_parallel) * 1000, 1)

    hist_text = _format_history(conversation_history)
    mq_focus = build_multi_question_focus_instruction(str(language or "english"))
    compact_branches = {branch: _compact_branch_output(branch, branch_outputs[branch]) for branch in enabled_branches}
    merge_bundle = {
        "relationship": relation_profile,
        "relational_evidence": evidence_spine,
        "branches": compact_branches,
        "partial": {
            branch: branch_outputs[branch].get("status") == "unavailable" or bool(branch_outputs[branch].get("error"))
            for branch in enabled_branches
        },
        "enabled_branches": list(enabled_branches),
    }
    merge_static = build_relational_merge_static(language or "english")
    merge_user = (
        f"CURRENT_DATE: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"RELATIONSHIP_PROFILE_JSON:\n{_json_compact(relation_profile)}\n\n"
        f"RELATIONAL_EVIDENCE_SPINE_JSON:\n{_json_compact(evidence_spine)}\n\n"
        f"SPECIALIST_BRANCH_OUTPUTS_JSON:\n{_json_compact(merge_bundle)}\n"
        f"{hist_text}\n{mq_focus}\nCURRENT QUESTION: {user_question}\n"
        f"{FAQ_META_INSTRUCTION.strip()}"
    )
    merge_prompt = f"{merge_static}\n\n{merge_user}"

    t_syn = time.time()
    syn = await analyzer.generate_text_from_prompt(
        merge_prompt,
        premium_analysis=premium_analysis,
        model_override=cached_model,
        model_name_override=gemini_model_name if cached_model else None,
        llm_log_tag="parallel_relational_merge",
    )
    synthesis_ms = round((time.time() - t_syn) * 1000, 1)
    merge_raw = (syn.get("response") or "") if isinstance(syn, dict) else ""
    merge_ok = bool(syn.get("success") and merge_raw)
    merge_metrics = _llm_call_metrics(
        "parallel_relational_merge",
        merge_prompt,
        merge_raw,
        syn if isinstance(syn, dict) else None,
        success=merge_ok,
        elapsed_ms=synthesis_ms,
        static_chars=len(merge_static),
        dynamic_chars=len(merge_prompt) - len(merge_static),
    )

    usage_rows = branch_llm_rows + [merge_metrics]
    totals = _totals_from_rows(usage_rows)
    if cache_setup_input_tokens > 0:
        totals["cache_setup_input_chars"] = int(cache_setup_input_chars)
        totals["cache_setup_input_tokens"] = int(cache_setup_input_tokens)
    usage_payload = {
        "stages": usage_rows,
        "totals": totals,
        "specialist_branch_outputs": merge_bundle,
        "specialist_branch_outputs_full": {
            "relationship": relation_profile,
            "relational_evidence": evidence_spine,
            "branches": branch_outputs,
            "partial": merge_bundle["partial"],
            "enabled_branches": list(enabled_branches),
        },
    }

    if not merge_ok:
        _log_parallel_llm_summary(usage_rows)
        await _delete_parallel_cache(cache_resource, cache_label="parallel_relational")
        return {
            "success": False,
            "response": "I could not generate the relational synthesis. Please try again.",
            "error": syn.get("error") or "relational_synthesis_empty",
            "timing": {
                "parallel_chat_ms": parallel_ms,
                "synthesis_ms": synthesis_ms,
                "total_request_time": time.time() - total_request_start,
                "parallel_pipeline": True,
                "parallel_relational": True,
                "parallel_llm_usage": usage_payload,
            },
        }

    cleaned_text = "".join(char for char in merge_raw if ord(char) >= 32 or char in "\n\r\t")
    cleaned_text = analyzer._fix_response_formatting(cleaned_text)
    cleaned_text, faq_metadata = ResponseParser.parse_faq_metadata(cleaned_text)
    if len(cleaned_text) < 50:
        _log_parallel_llm_summary(usage_rows)
        await _delete_parallel_cache(cache_resource, cache_label="parallel_relational")
        return {
            "success": False,
            "response": "I received a partial relational response. Please try again.",
            "error": "relational_response_too_short",
            "timing": {
                "parallel_chat_ms": parallel_ms,
                "synthesis_ms": synthesis_ms,
                "total_request_time": time.time() - total_request_start,
                "parallel_pipeline": True,
                "parallel_relational": True,
                "parallel_llm_usage": usage_payload,
            },
        }

    parsed = ResponseParser.parse_images_in_chat_response(cleaned_text)
    contract_ok, contract_errors = RelationalResponseContract.validate(
        parsed["content"] + ("\nFAQ_META: " + json.dumps(faq_metadata) if faq_metadata else ""),
        relation_profile,
        question=user_question,
    )
    if not contract_ok:
        logger.warning("RELATIONAL_RESPONSE_CONTRACT failed: %s", ", ".join(contract_errors))
    answer_eval = RelationalAnswerEvaluator.evaluate(
        text=parsed["content"] + ("\nFAQ_META: " + json.dumps(faq_metadata) if faq_metadata else ""),
        profile=relation_profile,
        question=user_question,
        evidence_spine=evidence_spine,
    )
    if not answer_eval.get("passed"):
        logger.warning("RELATIONAL_ANSWER_EVAL failed: %s", ", ".join(answer_eval.get("failed_checks") or []))
    matched_term_ids, matched_glossary = find_terms_in_text(parsed["content"], language=language)
    token_usage = {
        "input_tokens": int(totals["input_tokens"]),
        "output_tokens": int(totals["output_tokens"]),
        "cached_tokens": int(totals.get("cached_tokens") or 0),
        "non_cached_input_tokens": int(totals.get("non_cached_input_tokens") or 0),
        "cache_setup_input_tokens": int(totals.get("cache_setup_input_tokens") or 0),
    }
    _log_parallel_llm_summary(usage_rows)
    await _delete_parallel_cache(cache_resource, cache_label="parallel_relational")

    return {
        "success": True,
        "response": parsed["content"],
        "terms": matched_term_ids,
        "glossary": matched_glossary,
        "summary_image": None,
        "follow_up_questions": parsed.get("follow_up_questions", []),
        "analysis_steps": parsed.get("analysis_steps", []),
        "faq_metadata": faq_metadata,
        "raw_response": merge_raw,
        "has_transit_request": False,
        "chat_llm_model": syn.get("chat_llm_model"),
        "token_usage": token_usage,
        "llm_prompt_chars": int(totals["input_chars"]),
        "llm_response_chars": int(len(parsed.get("content") or "")),
        "timing": {
            "total_request_time": time.time() - total_request_start,
            "parallel_chat_ms": parallel_ms,
            "synthesis_ms": synthesis_ms,
            "parallel_pipeline": True,
            "parallel_relational": True,
            "response_contract_ok": contract_ok,
            "response_contract_errors": contract_errors,
            "answer_eval_passed": bool(answer_eval.get("passed")),
            "answer_eval_failed_checks": answer_eval.get("failed_checks") or [],
            "answer_eval_score": answer_eval.get("score"),
            "answer_eval_max_score": answer_eval.get("max_score"),
            "parallel_llm_usage": usage_payload,
        },
    }


def _format_history(history: List[Dict[str, Any]]) -> str:
    if not history:
        return ""
    trimmed = []
    for item in history[-3:]:
        q = str(item.get("question") or "")[:600]
        r = str(item.get("response") or "")[:1000]
        if q or r:
            trimmed.append({"question": q, "response": r})
    if not trimmed:
        return ""
    return f"\nRECENT_CONVERSATION_JSON:\n{json.dumps(trimmed, ensure_ascii=False, default=str)}\n"


def _enabled_relational_branches(evidence_spine: Dict[str, Any]) -> List[str]:
    activation = ((evidence_spine or {}).get("branch_activation") or {}) if isinstance(evidence_spine, dict) else {}
    profile = ((evidence_spine or {}).get("profile") or {}) if isinstance(evidence_spine, dict) else {}
    relation_specific = ((evidence_spine or {}).get("relation_specific_evidence") or {}) if isinstance(evidence_spine, dict) else {}
    timing_strategy = ((evidence_spine or {}).get("timing_strategy") or {}) if isinstance(evidence_spine, dict) else {}

    enabled: List[str] = []
    for branch in _CORE_RELATIONAL_BRANCHES:
        meta = activation.get(branch) or {}
        if meta.get("priority") == "skipped":
            continue
        if meta.get("data_available") is False:
            continue
        priority = str(meta.get("priority") or "supporting")
        if branch == "parashari_relational":
            enabled.append(branch)
            continue
        if priority == "primary":
            enabled.append(branch)
            continue
        if branch == "timing_relational" and str((timing_strategy.get("requested_granularity") or "none")) != "none":
            enabled.append(branch)
            continue
        if branch == "nakshatra_relational":
            nf_native = relation_specific.get("nakshatra_flavor_native") or {}
            nf_partner = relation_specific.get("nakshatra_flavor_partner") or {}
            if nf_native or nf_partner:
                enabled.append(branch)
            continue
        if branch == "nadi_relational":
            summary = (evidence_spine.get("cross_chart_contact_summary") or {}) if isinstance(evidence_spine, dict) else {}
            if int(summary.get("nodal") or 0) > 0 or int(summary.get("saturn_pressure") or 0) > 0:
                enabled.append(branch)
            continue
        if branch == "kp_relational" and meta.get("data_available") is not False:
            if profile.get("question_mode") in {"predictive_yes_no", "predictive_timing"}:
                enabled.append(branch)
            continue
        if branch == "jaimini_relational" and profile.get("relation_family") == "spouse_romantic":
            enabled.append(branch)
            continue
    for branch in _OPTIONAL_RELATIONAL_BRANCHES:
        meta = activation.get(branch) or {}
        if meta.get("priority") == "skipped":
            continue
        if meta.get("data_available") is False:
            continue
        enabled.append(branch)
    seen = set()
    ordered: List[str] = []
    for branch in [*_CORE_RELATIONAL_BRANCHES, *_OPTIONAL_RELATIONAL_BRANCHES]:
        if branch in enabled and branch not in seen:
            seen.add(branch)
            ordered.append(branch)
    return ordered
