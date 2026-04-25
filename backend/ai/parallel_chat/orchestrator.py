"""
Parallel Parashari / Jaimini / Nadi / Nakshatra / KP / Ashtakavarga / Sudarshan LLM branches + synthesis merge.

Legacy `generate_chat_response` delegates here only when `should_use_parallel_chat`
is true. Default production path is unchanged (flag off).
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_ALL_BRANCHES: Tuple[str, ...] = (
    "parashari",
    "jaimini",
    "nadi",
    "nakshatra",
    "kp",
    "ashtakavarga",
    "sudarshan",
)


def _chart_focus_branch_plan(intent: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
    """
    Narrow specialist fan-out when the user explicitly asks for a specific chart/lens
    such as Lagna, D9, or D10. This prevents irrelevant schools from muddying a
    chart-scoped reading.
    """
    focus = intent.get("chart_focus")
    if not isinstance(focus, dict) or focus.get("kind") != "chart_specific":
        return list(_ALL_BRANCHES), None

    primary = str(focus.get("primary") or "").strip()
    label = str(focus.get("label") or primary or "chart")
    enabled = {"parashari", "nakshatra"}

    if primary in {"D9", "D10", "Karkamsa", "Swamsa"}:
        enabled.add("jaimini")
    if primary in {"D1"} and str(focus.get("label") or "").strip().lower() == "lagna":
        enabled.discard("jaimini")

    ordered = [b for b in _ALL_BRANCHES if b in enabled]
    reason = f"chart_focus:{label}"
    return ordered, reason


def _skipped_branch_output(branch_label: str, reason: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return (
        {
            "branch": branch_label,
            "status": "skipped",
            "analysis": "",
            "bullets": [],
            "skip_reason": reason,
        },
        {
            "branch": f"parallel_{branch_label}",
            "success": True,
            "skipped": True,
            "elapsed_ms": 0.0,
            "output_chars": 0,
            "output_tokens": 0,
            "input_tokens": 0,
            "cached_tokens": 0,
            "non_cached_input_tokens": 0,
            "static_chars": 0,
            "dynamic_chars": 0,
        },
    )


def _parallel_diag_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def _log_parallel_branch_diagnostics(
    branch_label: str,
    static_instruction: str,
    body: str,
    payload: Dict[str, Any],
) -> None:
    """Optional: static vs JSON size + per-key JSON sizes (find what bloats Parashari)."""
    log_parts = _parallel_diag_enabled("ASTRO_PARALLEL_LOG_PROMPT_PARTS")
    log_keys = _parallel_diag_enabled("ASTRO_PARALLEL_LOG_PAYLOAD_KEYS")
    if not log_parts and not log_keys:
        return
    from ai.llm_roundtrip_log import json_serialized_size

    sep = "\n\nVARIABLE_DATA_JSON:\n"
    total = len(static_instruction) + len(sep) + len(body)
    if log_parts:
        logger.info(
            "PARALLEL_PROMPT_PARTS parallel_%s static_instruction_chars=%s variable_json_chars=%s "
            "prompt_total_chars=%s",
            branch_label,
            len(static_instruction),
            len(body),
            total,
        )
    if not log_keys:
        return
    lines = [
        f"PARALLEL_PAYLOAD_KEY_SIZES parallel_{branch_label} "
        f"payload_json_chars≈{json_serialized_size(payload)}"
    ]
    for k in sorted(payload.keys()):
        lines.append(f"  top.{k}: ~{json_serialized_size(payload[k])} chars")
    ctx_keys = (
        "parashari_context",
        "parashari_agents",
        "jaimini_context",
        "jaimini",
        "nadi_context",
        "nadi",
        "nakshatra_context",
        "nakshatra",
        "kp_context",
        "kp",
        "ashtakavarga_context",
        "ashtakavarga",
        "sudarshana_context",
    )
    for ck in ctx_keys:
        blob = payload.get(ck)
        if not isinstance(blob, dict) or not blob:
            continue
        lines.append(f"  {ck} subkeys (largest first):")
        ranked = sorted(blob.items(), key=lambda kv: json_serialized_size(kv[1]), reverse=True)
        for sk, sv in ranked[:50]:
            lines.append(f"    .{sk}: ~{json_serialized_size(sv)} chars")
        if len(ranked) > 50:
            lines.append(f"    ... [{len(ranked) - 50} more keys]")
    logger.info("\n".join(lines))

from ai.output_schema import (
    FAQ_META_INSTRUCTION,
    VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION,
    build_multi_question_focus_instruction,
    get_response_schema_for_mode,
)
from ai.parallel_chat.agent_context_factory import (
    merged_context_to_agent_context,
    parallel_agent_context_enabled,
)
from ai.parallel_chat.context_slices import (
    build_ashtakavarga_slice,
    build_jaimini_slice,
    build_kp_slice,
    build_nadi_slice,
    build_nakshatra_slice,
    build_parashari_slice,
    build_shared_kernel_lite,
    build_sudarshan_branch_payload,
    format_history_for_prompt,
    without_keys,
)
from ai.parallel_chat.parallel_agent_payloads import build_all_parallel_agent_payloads
from ai.parallel_chat.json_utils import parse_branch_json
from ai.parallel_chat.config import parallel_branch_stagger_s, parallel_branch_timeout_s
from ai.parallel_chat.prompt_blocks import (
    MERGE_ROLE_PREAMBLE,
    build_ashtakavarga_branch_static,
    build_ashtakavarga_branch_static_agent,
    build_jaimini_branch_static,
    build_jaimini_branch_static_agent,
    build_kp_branch_static,
    build_kp_branch_static_agent,
    build_nadi_branch_static,
    build_nadi_branch_static_agent,
    build_nakshatra_branch_static,
    build_nakshatra_branch_static_agent,
    build_parashari_branch_static,
    build_parashari_branch_static_agent,
    build_sudarshan_branch_static,
    build_sudarshan_branch_static_agent,
)
from ai.response_parser import ResponseParser
from ai.term_matcher import find_terms_in_text
from chat.system_instruction_config import build_merge_synthesis_instruction


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return bool(default)
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def _intent_mode(context: Dict[str, Any], mode: str) -> str:
    intent_block = context.get("intent", {}) or {}
    intent_mode = intent_block.get("mode", mode)
    analysis_type = context.get("analysis_type", "birth")
    if analysis_type == "mundane":
        intent_mode = "MUNDANE"
    if intent_block.get("lab_mode"):
        intent_mode = "LAB_EDUCATION"
    if not intent_mode:
        intent_mode = mode or "DEFAULT"
    return str(intent_mode)


def _merge_instruction_blocks(
    user_question: str,
    context: Dict[str, Any],
    language: str,
    _response_style: str,
    user_context: Optional[Dict],
    premium_analysis: bool,
    mode: str,
) -> Tuple[str, str, str, str, str, str]:
    """Mirror `build_final_prompt` tail: language, elaborate, schema, user context, final checks."""
    intent_mode = _intent_mode(context, mode)
    chart_focus = context.get("intent", {}).get("chart_focus")
    _lang = str(language or "english").strip() or "english"

    from ai.output_schema import build_output_language_blocks

    _, language_instruction, final_check = build_output_language_blocks(_lang, user_question)

    elaborate_instruction = """
CRITICAL - RESPONSE LENGTH & DEPTH (NON-NEGOTIABLE):
Your full response MUST be comprehensive. Short or summary-style answers are FORBIDDEN.
- For Birth Chart queries: Aim for 12,000 characters. Expand every section with planetary reasoning, classical references, and technical detail.
- For Mundane/Event queries: Aim for 3,000-5,000 characters. Focus on precision, house comparison (1st vs 7th), dasha synchronization, and critical timing.
- Prioritize depth and clarity. Output sufficient detail to justify the prediction.
"""

    response_format_instruction = get_response_schema_for_mode(
        intent_mode,
        premium_analysis=premium_analysis,
        chart_focus=chart_focus if isinstance(chart_focus, dict) else None,
    )

    user_context_instruction = ""
    if user_context:
        user_name = user_context.get("user_name", "User")
        native_name = context.get("birth_details", {}).get("name", "the native")
        relationship = user_context.get("user_relationship", "self")
        if relationship == "self" or (
            user_name and native_name and user_name.lower() == native_name.lower()
        ):
            user_context_instruction = (
                f"USER CONTEXT - SELF CONSULTATION:\nThe person asking questions is {native_name} themselves. "
                f"Use direct personal language: 'Your chart shows...', 'You have...'"
            )
        else:
            user_context_instruction = (
                f"🚨 CRITICAL USER CONTEXT - THIRD PARTY CONSULTATION 🚨\nThe person asking is {user_name} "
                f"about {native_name}'s chart. You MUST use '{native_name}' or 'they/their' in your response. "
                f"NEVER use 'you/your'."
            )

    return (
        language_instruction,
        elaborate_instruction,
        response_format_instruction,
        user_context_instruction,
        final_check,
        intent_mode,
    )


def _json_serializer(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _json_compact(data: Any) -> str:
    """Compact JSON for LLM variable blocks (indent=2 was inflating char/token counts)."""
    return json.dumps(data, default=_json_serializer, ensure_ascii=False, separators=(",", ":"))


def _llm_call_metrics(
    stage: str,
    prompt: str,
    raw_response: str,
    res: Optional[Dict[str, Any]],
    *,
    success: bool,
    elapsed_ms: Optional[float] = None,
    static_chars: Optional[int] = None,
    dynamic_chars: Optional[int] = None,
) -> Dict[str, Any]:
    tu = (res or {}).get("token_usage") or {}
    row: Dict[str, Any] = {
        "stage": stage,
        "input_chars": len(prompt),
        "output_chars": len(raw_response or ""),
        "input_tokens": int(tu.get("input_tokens") or 0),
        "output_tokens": int(tu.get("output_tokens") or 0),
        "cached_tokens": int(tu.get("cached_tokens") or 0),
        "non_cached_input_tokens": int(
            tu.get("non_cached_input_tokens")
            or max(
                0,
                int(tu.get("input_tokens") or 0) - int(tu.get("cached_tokens") or 0),
            )
        ),
        "success": success,
    }
    if elapsed_ms is not None:
        row["elapsed_ms"] = round(float(elapsed_ms), 1)
    if static_chars is not None:
        row["static_chars"] = int(static_chars)
    if dynamic_chars is not None:
        row["dynamic_chars"] = int(dynamic_chars)
    return row


def _log_parallel_llm_summary(rows: List[Dict[str, Any]]) -> None:
    """One log block: per-stage chars/tokens plus totals (parallel branches + merge)."""
    if not rows:
        return
    tot_ic = tot_oc = tot_it = tot_ot = tot_ct = tot_ncit = 0
    lines: List[str] = ["PARALLEL_CHAT_LLM_SUMMARY"]
    for row in rows:
        tot_ic += int(row.get("input_chars") or 0)
        tot_oc += int(row.get("output_chars") or 0)
        tot_it += int(row.get("input_tokens") or 0)
        tot_ot += int(row.get("output_tokens") or 0)
        tot_ct += int(row.get("cached_tokens") or 0)
        tot_ncit += int(row.get("non_cached_input_tokens") or 0)
        st = row.get("stage", "?")
        em = row.get("elapsed_ms")
        sc = row.get("static_chars")
        dc = row.get("dynamic_chars")
        extra = ""
        if em is not None or sc is not None or dc is not None:
            extra = (
                f" elapsed_ms={em} static_chars={sc} dynamic_chars={dc}"
            )
        lines.append(
            f"  {st}: input_chars={row.get('input_chars')} output_chars={row.get('output_chars')} "
            f"input_tokens={row.get('input_tokens')} output_tokens={row.get('output_tokens')} "
            f"cached_tokens={row.get('cached_tokens')} "
            f"non_cached_input_tokens={row.get('non_cached_input_tokens')} "
            f"success={row.get('success')}{extra}"
        )
    lines.append(
        f"  TOTAL: input_chars={tot_ic} output_chars={tot_oc} "
        f"input_tokens={tot_it} output_tokens={tot_ot} "
        f"cached_tokens={tot_ct} non_cached_input_tokens={tot_ncit}"
    )
    logger.info("\n".join(lines))


def _totals_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "input_chars": sum(int(r.get("input_chars") or 0) for r in rows),
        "output_chars": sum(int(r.get("output_chars") or 0) for r in rows),
        "input_tokens": sum(int(r.get("input_tokens") or 0) for r in rows),
        "output_tokens": sum(int(r.get("output_tokens") or 0) for r in rows),
        "cached_tokens": sum(int(r.get("cached_tokens") or 0) for r in rows),
        "non_cached_input_tokens": sum(
            int(r.get("non_cached_input_tokens") or 0) for r in rows
        ),
    }
    if any(r.get("elapsed_ms") is not None for r in rows):
        out["elapsed_ms_sum"] = round(
            sum(float(r.get("elapsed_ms") or 0) for r in rows), 1
        )
    if any(r.get("static_chars") is not None for r in rows):
        out["static_chars"] = sum(int(r.get("static_chars") or 0) for r in rows)
    if any(r.get("dynamic_chars") is not None for r in rows):
        out["dynamic_chars"] = sum(int(r.get("dynamic_chars") or 0) for r in rows)
    return out


def _parallel_cache_ttl_s() -> int:
    # This cache is explicitly deleted after each request; TTL is only a fallback.
    return max(300, int(os.getenv("ASTRO_PARALLEL_CHAT_CACHE_TTL_S", "300") or 300))


async def _create_gemini_parallel_cache(
    *,
    llm_provider: str,
    model_name: str,
    cache_payload: Dict[str, Any],
    cache_label: str,
    cache_enabled_env: str = "ASTRO_PARALLEL_CHAT_CONTEXT_CACHE",
) -> Tuple[Optional[Any], Optional[Any], int, int]:
    """
    Create a short-lived Gemini CachedContent resource for intra-request branch fan-out.

    Returns: (cache_resource, cached_model, setup_chars, setup_tokens)
    """
    if llm_provider != "gemini" or not _env_bool(cache_enabled_env, default=True):
        return None, None, 0, 0
    try:
        from google.generativeai import caching as genai_caching
        import google.generativeai as genai

        cache_text = f"{cache_label.upper()}_SHARED_CONTEXT_JSON:\n{_json_compact(cache_payload)}"
        cache_setup_input_chars = len(cache_text)
        cache_setup_input_tokens = max(1, int(round(cache_setup_input_chars / 4.0)))
        ttl_s = _parallel_cache_ttl_s()
        logger.info(
            "%s_CACHE create model=%s ttl_s=%s context_chars=%s",
            cache_label.upper(),
            model_name,
            ttl_s,
            cache_setup_input_chars,
        )
        cache_resource = await asyncio.to_thread(
            genai_caching.CachedContent.create,
            model=model_name,
            display_name=f"{cache_label}-{int(time.time())}",
            system_instruction="Use cached shared context for all branch and merge reasoning.",
            contents=[cache_text],
            ttl=ttl_s,
        )
        cached_model = await asyncio.to_thread(
            genai.GenerativeModel.from_cached_content,
            cache_resource,
        )
        logger.info(
            "%s_CACHE created name=%s",
            cache_label.upper(),
            getattr(cache_resource, "name", "unknown"),
        )
        return cache_resource, cached_model, cache_setup_input_chars, cache_setup_input_tokens
    except Exception as e:
        logger.warning("%s_CACHE failed; continuing without cache: %s", cache_label.upper(), e)
        return None, None, 0, 0


async def _delete_parallel_cache(cache_resource: Optional[Any], *, cache_label: str) -> None:
    if cache_resource is None:
        return
    try:
        await asyncio.to_thread(cache_resource.delete)
        logger.info("%s_CACHE deleted", cache_label.upper())
    except Exception as e:
        logger.warning("%s_CACHE delete failed: %s", cache_label.upper(), e)


async def _run_branch_json(
    analyzer: Any,
    static_instruction: str,
    payload: Dict[str, Any],
    premium_analysis: bool,
    branch_label: str,
    *,
    critical: bool,
    start_delay_s: float = 0.0,
    model_override: Optional[Any] = None,
    model_name_override: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if start_delay_s > 0:
        await asyncio.sleep(start_delay_s)
    body = _json_compact(payload)
    prompt = f"{static_instruction}\n\nVARIABLE_DATA_JSON:\n{body}"
    static_chars = len(static_instruction)
    dynamic_chars = len(prompt) - static_chars
    branch_timeout_s = parallel_branch_timeout_s(critical=critical)
    _log_parallel_branch_diagnostics(branch_label, static_instruction, body, payload)
    last_err: Optional[BaseException] = None
    last_res: Optional[Dict[str, Any]] = None
    last_raw = ""
    attempts = 1 if critical else 2
    elapsed_ms_acc = 0.0
    for attempt in range(attempts):
        t0 = time.time()
        try:
            res = await analyzer.generate_text_from_prompt(
                prompt,
                premium_analysis=premium_analysis,
                model_override=model_override,
                model_name_override=model_name_override,
                llm_log_tag=f"parallel_{branch_label}",
                request_timeout_s=branch_timeout_s,
            )
            elapsed_ms_acc += (time.time() - t0) * 1000
            last_res = res
            raw = (res.get("response") or "") if isinstance(res, dict) else ""
            last_raw = raw
            if res.get("success") and raw:
                parsed = parse_branch_json(raw, branch_label)
                metrics = _llm_call_metrics(
                    f"parallel_{branch_label}",
                    prompt,
                    raw,
                    res,
                    success=True,
                    elapsed_ms=elapsed_ms_acc,
                    static_chars=static_chars,
                    dynamic_chars=dynamic_chars,
                )
                return parsed, metrics
            last_err = RuntimeError(res.get("error") or "branch_failed")
        except Exception as e:
            elapsed_ms_acc += (time.time() - t0) * 1000
            last_err = e
        if critical:
            break
        await asyncio.sleep(0.2 * (attempt + 1))
    # Soft-fail: merge can proceed; Parashari missing degrades quality but avoids 4+ minute stalls on 429/retry.
    if critical:
        logger.warning(
            "parallel branch %s failed after %s attempt(s); continuing merge without it: %s",
            branch_label,
            attempts,
            last_err,
        )
    fallback = {
        "branch": branch_label,
        "status": "unavailable",
        "analysis": "",
        "bullets": [],
        "error": str(last_err)[:500] if last_err else "unknown",
    }
    metrics = _llm_call_metrics(
        f"parallel_{branch_label}",
        prompt,
        last_raw,
        last_res,
        success=False,
        elapsed_ms=elapsed_ms_acc,
        static_chars=static_chars,
        dynamic_chars=dynamic_chars,
    )
    return fallback, metrics


async def run_parallel_chat_pipeline(
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
    from utils.admin_settings import (
        get_chat_llm_provider,
        get_chat_llm_provider_premium,
        get_gemini_chat_model,
        get_gemini_premium_model,
    )

    ctx = astrological_context
    intent = ctx.get("intent") or {}
    category = intent.get("category", "general")
    enabled_branches, branch_scope_reason = _chart_focus_branch_plan(intent)
    enabled_branch_set = set(enabled_branches)
    use_agent_ctx = parallel_agent_context_enabled()

    hist_text = format_history_for_prompt(conversation_history)

    if use_agent_ctx:
        agent_ctx = merged_context_to_agent_context(ctx, user_question=user_question)
        ap = build_all_parallel_agent_payloads(agent_ctx, user_question, merged_chart_context=ctx)
        par_payload = ap["parashari"]
        jm_payload = ap["jaimini"]
        nd_payload = ap["nadi"]
        nk_payload = ap["nakshatra"]
        kp_payload = ap["kp"]
        av_payload = ap["ashtakavarga"]
        par_static = build_parashari_branch_static_agent(category)
        jm_static = build_jaimini_branch_static_agent()
        nd_static = build_nadi_branch_static_agent(category)
        nk_static = build_nakshatra_branch_static_agent(category)
        kp_static = build_kp_branch_static_agent(category)
        av_static = build_ashtakavarga_branch_static_agent()
        sd_static = build_sudarshan_branch_static_agent(category)
    else:
        kernel_lite = build_shared_kernel_lite(ctx)
        par_slice = build_parashari_slice(ctx)
        jm_slice = build_jaimini_slice(ctx)
        nd_slice = build_nadi_slice(ctx)
        nk_slice = build_nakshatra_slice(ctx)
        kp_slice = build_kp_slice(ctx)
        av_slice = build_ashtakavarga_slice(ctx)
        par_static = build_parashari_branch_static(category)
        jm_static = build_jaimini_branch_static()
        nd_static = build_nadi_branch_static(category)
        nk_static = build_nakshatra_branch_static(category)
        kp_static = build_kp_branch_static(category)
        av_static = build_ashtakavarga_branch_static()
        sd_static = build_sudarshan_branch_static(category)
        par_payload = {"parashari_context": par_slice, "user_question": user_question}
        jm_payload = {
            "shared_kernel": without_keys(kernel_lite, {"current_dashas"}),
            "jaimini_context": jm_slice,
            "user_question": user_question,
        }
        nd_payload = {"shared_kernel": kernel_lite, "nadi_context": nd_slice, "user_question": user_question}
        nk_payload = {"shared_kernel": kernel_lite, "nakshatra_context": nk_slice, "user_question": user_question}
        kp_payload = {"shared_kernel": kernel_lite, "kp_context": kp_slice, "user_question": user_question}
        av_payload = {"shared_kernel": kernel_lite, "ashtakavarga_context": av_slice, "user_question": user_question}

    sd_payload = build_sudarshan_branch_payload(ctx, user_question)

    stagger_s = parallel_branch_stagger_s()
    if stagger_s > 0:
        logger.info(
            "PARALLEL_CHAT_STAGGER stagger_s=%.3f (~%.1fs spread across 7 branch starts)",
            stagger_s,
            6 * stagger_s,
        )
    if branch_scope_reason:
        logger.info(
            "PARALLEL_BRANCH_SCOPE reason=%s enabled=%s",
            branch_scope_reason,
            ",".join(enabled_branches),
        )

    t_parallel = time.time()
    llm_provider = get_chat_llm_provider_premium() if premium_analysis else get_chat_llm_provider()
    gemini_model_name = get_gemini_premium_model() if premium_analysis else get_gemini_chat_model()
    cache_resource = None
    cached_model = None
    cache_setup_input_chars = 0
    cache_setup_input_tokens = 0
    cache_payload = {
        "shared_kernel": build_shared_kernel_lite(ctx),
        "user_facts": ctx.get("user_facts"),
        "extracted_context": ctx.get("extracted_context"),
        "history": conversation_history or [],
        "current_question": user_question,
    }
    cache_resource, cached_model, cache_setup_input_chars, cache_setup_input_tokens = await _create_gemini_parallel_cache(
        llm_provider=llm_provider,
        model_name=gemini_model_name,
        cache_payload=cache_payload,
        cache_label="parallel_chat",
    )
    try:
        par_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                par_static,
                par_payload,
                premium_analysis,
                "parashari",
                critical=True,
                start_delay_s=0.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "parashari" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("parashari", branch_scope_reason or "branch_filtered"))
        )
        jm_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                jm_static,
                jm_payload,
                premium_analysis,
                "jaimini",
                critical=False,
                start_delay_s=1.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "jaimini" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("jaimini", branch_scope_reason or "branch_filtered"))
        )
        nd_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                nd_static,
                nd_payload,
                premium_analysis,
                "nadi",
                critical=False,
                start_delay_s=2.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "nadi" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("nadi", branch_scope_reason or "branch_filtered"))
        )
        nk_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                nk_static,
                nk_payload,
                premium_analysis,
                "nakshatra",
                critical=False,
                start_delay_s=3.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "nakshatra" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("nakshatra", branch_scope_reason or "branch_filtered"))
        )
        kp_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                kp_static,
                kp_payload,
                premium_analysis,
                "kp",
                critical=False,
                start_delay_s=4.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "kp" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("kp", branch_scope_reason or "branch_filtered"))
        )
        av_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                av_static,
                av_payload,
                premium_analysis,
                "ashtakavarga",
                critical=False,
                start_delay_s=5.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "ashtakavarga" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("ashtakavarga", branch_scope_reason or "branch_filtered"))
        )
        sd_task = asyncio.create_task(
            _run_branch_json(
                analyzer,
                sd_static,
                sd_payload,
                premium_analysis,
                "sudarshan",
                critical=False,
                start_delay_s=6.0 * stagger_s,
                model_override=cached_model,
                model_name_override=gemini_model_name if cached_model else None,
            ) if "sudarshan" in enabled_branch_set else asyncio.sleep(0, result=_skipped_branch_output("sudarshan", branch_scope_reason or "branch_filtered"))
        )
        (
            (par_out, par_m),
            (jm_out, jm_m),
            (nd_out, nd_m),
            (nk_out, nk_m),
            (kp_out, kp_m),
            (av_out, av_m),
            (sd_out, sd_m),
        ) = await asyncio.gather(
            par_task, jm_task, nd_task, nk_task, kp_task, av_task, sd_task
        )
        branch_llm_rows: List[Dict[str, Any]] = [par_m, jm_m, nd_m, nk_m, kp_m, av_m, sd_m]
    except Exception as e:
        logger.exception("parallel gather failed: %s", e)
        await _delete_parallel_cache(cache_resource, cache_label="parallel_chat")
        raise

    parallel_ms = round((time.time() - t_parallel) * 1000, 1)

    intent_mode = _intent_mode(ctx, mode)
    merge_system_instruction = build_merge_synthesis_instruction(mode=intent_mode)
    single_native_format_guard = """
FORMAT GUARD FOR SINGLE-NATIVE READINGS:
- This is NOT a two-person synastry/relational reading.
- Do NOT use fixed two-person relational section labels such as "Core Nature", "Behavioral Texture", or "Interaction Pattern".
- Do NOT frame the answer as native-vs-partner comparison, spouse-vs-spouse behavior, or compatibility scoring unless the request actually contains two charts.
- If the topic is marriage/relationship, still answer from the single native chart unless a second chart is explicitly present.
"""
    (
        language_instruction,
        elaborate_instruction,
        response_format_instruction,
        user_context_instruction,
        final_check,
        _,
    ) = _merge_instruction_blocks(
        user_question, ctx, language, response_style, user_context, premium_analysis, mode
    )

    current_date = datetime.now()
    ascendant_info = ctx.get("ascendant_info", {})
    ascendant_summary = (
        f"ASCENDANT: {ascendant_info.get('sign_name', 'Unknown')} at "
        f"{ascendant_info.get('exact_degree_in_sign', 0):.2f}°"
    )
    time_context = (
        f"IMPORTANT CURRENT DATE INFORMATION:\n- Today's Date: {current_date.strftime('%B %d, %Y')}\n"
        f"- Current Time: {current_date.strftime('%H:%M UTC')}\n"
        f"- Current Year: {current_date.year}\n\nCRITICAL CHART INFORMATION:\n{ascendant_summary}"
    )

    branch_bundle = {
        "parashari": par_out,
        "jaimini": jm_out,
        "nadi": nd_out,
        "nakshatra": nk_out,
        "kp": kp_out,
        "ashtakavarga": av_out,
        "sudarshan": sd_out,
        "scope": {
            "enabled_branches": enabled_branches,
            "reason": branch_scope_reason,
            "chart_focus": copy.deepcopy(intent.get("chart_focus")) if isinstance(intent.get("chart_focus"), dict) else None,
        },
        "partial": {
            "jaimini": jm_out.get("status") == "unavailable" or bool(jm_out.get("error")),
            "nadi": nd_out.get("status") == "unavailable" or bool(nd_out.get("error")),
            "nakshatra": nk_out.get("status") == "unavailable" or bool(nk_out.get("error")),
            "kp": kp_out.get("status") == "unavailable" or bool(kp_out.get("error")),
            "ashtakavarga": av_out.get("status") == "unavailable" or bool(av_out.get("error")),
            "sudarshan": sd_out.get("status") == "unavailable" or bool(sd_out.get("error")),
        },
    }
    _merge_lang = str(language or "english").strip() or "english"
    mq_focus = build_multi_question_focus_instruction(_merge_lang)
    merge_user = (
        f"{time_context}\n\nSPECIALIST_BRANCH_OUTPUTS_JSON:\n"
        f"{_json_compact(branch_bundle)}\n"
        f"{hist_text}\n{mq_focus}\nCURRENT QUESTION: {user_question}\n{final_check}\n{FAQ_META_INSTRUCTION.strip()}"
    )
    merge_static = "\n\n".join(
        [
            MERGE_ROLE_PREAMBLE,
            merge_system_instruction,
            language_instruction,
            elaborate_instruction,
            response_format_instruction,
            user_context_instruction,
            single_native_format_guard,
            VEDIC_ASTROLOGY_SYSTEM_INSTRUCTION.strip(),
        ]
    )
    merge_prompt = f"{merge_static}\n\n{merge_user}"
    if _parallel_diag_enabled("ASTRO_PARALLEL_LOG_PROMPT_PARTS"):
        logger.info(
            "PARALLEL_PROMPT_PARTS parallel_merge merge_static_chars=%s merge_user_chars=%s "
            "merge_prompt_total_chars=%s",
            len(merge_static),
            len(merge_user),
            len(merge_prompt),
        )

    t_syn = time.time()
    syn = await analyzer.generate_text_from_prompt(
        merge_prompt,
        premium_analysis=premium_analysis,
        model_override=cached_model,
        model_name_override=gemini_model_name if cached_model else None,
        llm_log_tag="parallel_merge",
    )
    synthesis_ms = round((time.time() - t_syn) * 1000, 1)

    merge_raw = (syn.get("response") or "") if isinstance(syn, dict) else ""
    merge_ok = bool(syn.get("success") and merge_raw)
    merge_metrics = _llm_call_metrics(
        "parallel_merge",
        merge_prompt,
        merge_raw,
        syn if isinstance(syn, dict) else None,
        success=merge_ok,
        elapsed_ms=synthesis_ms,
        static_chars=len(merge_static),
        dynamic_chars=len(merge_prompt) - len(merge_static),
    )
    _parallel_usage_rows = branch_llm_rows + [merge_metrics]
    _parallel_totals = _totals_from_rows(_parallel_usage_rows)
    if cache_setup_input_tokens > 0:
        _parallel_totals["cache_setup_input_chars"] = int(cache_setup_input_chars)
        _parallel_totals["cache_setup_input_tokens"] = int(cache_setup_input_tokens)
    _parallel_usage_payload = {
        "stages": _parallel_usage_rows,
        "totals": _parallel_totals,
        # Persist specialist branch outputs for optional debug UX in clients/admin tools.
        "specialist_branch_outputs": branch_bundle,
    }

    if not syn.get("success") or not syn.get("response"):
        _log_parallel_llm_summary(_parallel_usage_rows)
        await _delete_parallel_cache(cache_resource, cache_label="parallel_chat")
        return {
            "success": False,
            "response": "I apologize, but I couldn't generate a merged response. Please try again.",
            "error": syn.get("error") or "synthesis_empty",
            "chat_llm_model": syn.get("chat_llm_model"),
            "timing": {
                "parallel_chat_ms": parallel_ms,
                "synthesis_ms": synthesis_ms,
                "total_request_time": time.time() - total_request_start,
                "chat_llm_provider": (
                    get_chat_llm_provider_premium() if premium_analysis else get_chat_llm_provider()
                ),
                "chat_llm_model": syn.get("chat_llm_model")
                or (get_gemini_premium_model() if premium_analysis else get_gemini_chat_model()),
                "parallel_llm_usage": _parallel_usage_payload,
                "parallel_agent_context": use_agent_ctx,
            },
        }

    response_text = syn["response"]
    allowed_chars = "\n\r\t"
    cleaned_text = "".join(
        char for char in response_text if ord(char) >= 32 or char in allowed_chars
    )
    cleaned_text = analyzer._fix_response_formatting(cleaned_text)
    if user_context and user_context.get("user_relationship") != "self":
        native_name = ctx.get("birth_details", {}).get("name", "the native")
        if native_name and native_name != "the native":
            cleaned_text = analyzer._fix_pronoun_usage(cleaned_text, native_name)

    cleaned_text, faq_metadata = ResponseParser.parse_faq_metadata(cleaned_text)
    if len(cleaned_text) < 50:
        _log_parallel_llm_summary(_parallel_usage_rows)
        await _delete_parallel_cache(cache_resource, cache_label="parallel_chat")
        return {
            "success": False,
            "response": "I received a partial merged response. Please try again.",
            "error": "merged_response_too_short",
            "chat_llm_model": syn.get("chat_llm_model"),
            "timing": {
                "parallel_chat_ms": parallel_ms,
                "synthesis_ms": synthesis_ms,
                "total_request_time": time.time() - total_request_start,
                "parallel_llm_usage": _parallel_usage_payload,
                "parallel_agent_context": use_agent_ctx,
            },
        }

    parsed_response = ResponseParser.parse_images_in_chat_response(cleaned_text)
    matched_term_ids, matched_glossary = find_terms_in_text(parsed_response["content"], language=language)

    summary_image_url = None
    if analyzer.flux_service and premium_analysis and parsed_response.get("summary_image_prompt"):
        try:
            image_result = await analyzer.flux_service.generate_image(parsed_response["summary_image_prompt"])
            if image_result:
                summary_image_url = image_result
        except Exception:
            pass

    model_name = syn.get("chat_llm_model")
    # Persist summed API usage across all parallel branches + merge (admin + billing visibility).
    token_usage = {
        "input_tokens": int(_parallel_totals["input_tokens"]),
        "output_tokens": int(_parallel_totals["output_tokens"]),
        "cached_tokens": int(_parallel_totals.get("cached_tokens") or 0),
        "non_cached_input_tokens": int(_parallel_totals.get("non_cached_input_tokens") or 0),
        "cache_setup_input_tokens": int(_parallel_totals.get("cache_setup_input_tokens") or 0),
    }
    total_time = time.time() - total_request_start
    _log_parallel_llm_summary(_parallel_usage_rows)
    await _delete_parallel_cache(cache_resource, cache_label="parallel_chat")

    return {
        "success": True,
        "response": parsed_response["content"],
        "terms": matched_term_ids,
        "glossary": matched_glossary,
        "summary_image": summary_image_url,
        "follow_up_questions": parsed_response.get("follow_up_questions", []),
        "analysis_steps": parsed_response.get("analysis_steps", []),
        "faq_metadata": faq_metadata,
        "raw_response": response_text,
        "has_transit_request": "transitRequest" in response_text and '"requestType"' in response_text,
        "chat_llm_model": model_name,
        "token_usage": token_usage,
        "llm_prompt_chars": int(_parallel_totals["input_chars"]),
        "llm_response_chars": int(len(parsed_response.get("content") or "")),
        "timing": {
            "total_request_time": total_time,
            "parallel_chat_ms": parallel_ms,
            "synthesis_ms": synthesis_ms,
            "chat_llm_provider": llm_provider,
            "chat_llm_model": model_name,
            "parallel_pipeline": True,
            "parallel_agent_context": use_agent_ctx,
            "parallel_llm_usage": _parallel_usage_payload,
        },
    }
