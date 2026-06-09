from __future__ import annotations

import json
import logging
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


def _extract_json_object(text: str) -> Dict[str, Any]:
    cleaned = (text or "").replace("```json", "").replace("```", "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _question_summary(ctx: Dict[str, Any]) -> Dict[str, Any]:
    bd = ctx.get("birth_details") or {}
    intent = ctx.get("intent") or {}
    summary = {
        "analysis_type": ctx.get("analysis_type") or "birth",
        "category": intent.get("category") or "general",
        "mode": intent.get("mode") or "",
        "needs_transits": bool(intent.get("needs_transits")),
        "chart_focus": intent.get("chart_focus") if isinstance(intent.get("chart_focus"), dict) else None,
        "requested_divisionals": intent.get("divisional_charts") if isinstance(intent.get("divisional_charts"), list) else [],
        "native": {
            "name": bd.get("name"),
            "gender": bd.get("gender"),
            "date": bd.get("date"),
        },
    }
    return summary


def _normalize_branch_list(raw: Any, allowed: List[str]) -> List[str]:
    if not isinstance(raw, list):
        return []
    allowed_set = set(allowed)
    out: List[str] = []
    for item in raw:
        branch = str(item or "").strip().lower()
        if branch in allowed_set and branch not in out:
            out.append(branch)
    return out


def _normalize_branch_scores(raw: Any, allowed: List[str]) -> Dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    allowed_set = set(allowed)
    out: Dict[str, float] = {}
    for key, value in raw.items():
        branch = str(key or "").strip().lower()
        if branch not in allowed_set:
            continue
        try:
            score = float(value)
        except (TypeError, ValueError):
            continue
        out[branch] = max(0.0, min(1.0, score))
    return out


def _normalize_reasoning(raw: Any, allowed: List[str]) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    allowed_set = set(allowed)
    out: Dict[str, str] = {}
    for key, value in raw.items():
        branch = str(key or "").strip().lower()
        if branch not in allowed_set:
            continue
        text = str(value or "").strip()
        if text:
            out[branch] = text[:240]
    return out


def _planner_prompt(
    *,
    user_question: str,
    language: str,
    context_summary: Dict[str, Any],
    allowed_branches: List[str],
) -> str:
    return f"""
You are a multilingual branch planner for an astrology system. Your job is NOT to answer the user's question.
Your only job is to choose the MINIMUM specialist branches needed for a high-confidence answer.

RULES:
- Understand the question semantically in any language. Do not rely on surface keywords.
- Return valid JSON only.
- Use the minimum set of branches that materially improves answer quality.
- Always include parashari unless it is unavailable in allowed_branches.
- Do not include a branch just because it exists.
- If uncertain, prefer a slightly broader but still disciplined set.
- You are planning branches, not writing astrology.

BRANCH CAPABILITIES:
- parashari: core promise, house lords, divisional grounding, dasha backbone, main prediction structure
- jaimini: chara karakas, UL/DK/A7, argala, chara-dasha relational and role-based framing
- nadi: compressed signature-style karmic patterning, dominant graha linkage, repeating life motifs
- nakshatra: nakshatra/pada/Tara/pushkara nuance, subtle motivation and timing texture
- kp: cusp and sub-lord precision, sharper trigger/timing confirmation, yes-no narrowing
- ashtakavarga: strength/filtering, support vs depletion, transit carrying capacity
- sudarshan: Lagna/Moon/Sun three-frame synthesis, current activation across body-mind-soul

CURRENT REQUEST SUMMARY:
{json.dumps(context_summary, ensure_ascii=False)}

ALLOWED_BRANCHES:
{json.dumps(allowed_branches, ensure_ascii=False)}

USER LANGUAGE:
{language}

USER QUESTION:
{user_question}

Return ONLY JSON with this schema:
{{
  "required_branches": ["parashari", "kp"],
  "optional_branches": ["nakshatra"],
  "branch_scores": {{
    "parashari": 1.0,
    "kp": 0.82,
    "nakshatra": 0.61
  }},
  "reasoning": {{
    "parashari": "Needed for promise and dasha backbone",
    "kp": "Needed for timing precision",
    "nakshatra": "Helpful for fine-grained nuance"
  }},
  "confidence": 0.0
}}

CONSTRAINTS:
- confidence must be a number between 0 and 1
- required_branches and optional_branches must be subsets of ALLOWED_BRANCHES
- required_branches should usually contain 2 to 4 items
- optional_branches should be empty or small
- If the question is broad and chart-wide, prefer parashari plus the most additive specialists
- If the question is narrowly chart-specific, keep the set tight
""".strip()


async def plan_parallel_branches(
    analyzer: Any,
    *,
    user_question: str,
    language: str,
    context: Dict[str, Any],
    allowed_branches: List[str],
    model_name: str,
) -> Dict[str, Any]:
    prompt = _planner_prompt(
        user_question=user_question,
        language=language,
        context_summary=_question_summary(context),
        allowed_branches=allowed_branches,
    )
    model = analyzer.get_named_gemini_model(model_name, premium_analysis=False)
    llm_out = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        model_override=model,
        model_name_override=model_name,
        force_gemini=True,
        llm_log_tag="parallel_branch_planner",
        request_timeout_s=20.0,
    )
    raw_text = str((llm_out or {}).get("response") or "").strip()
    if not llm_out.get("success") or not raw_text:
        raise RuntimeError(str((llm_out or {}).get("error") or "planner_empty"))
    raw = _extract_json_object(raw_text)
    required = _normalize_branch_list(raw.get("required_branches"), allowed_branches)
    optional = _normalize_branch_list(raw.get("optional_branches"), allowed_branches)
    scores = _normalize_branch_scores(raw.get("branch_scores"), allowed_branches)
    reasoning = _normalize_reasoning(raw.get("reasoning"), allowed_branches)
    try:
        confidence = float(raw.get("confidence"))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    if "parashari" in allowed_branches and "parashari" not in required:
        required = ["parashari"] + [b for b in required if b != "parashari"]
    final_required: List[str] = []
    for branch in required:
        if branch not in final_required:
            final_required.append(branch)
    final_optional: List[str] = []
    for branch in optional:
        if branch not in final_required and branch not in final_optional:
            final_optional.append(branch)

    selected = final_required + final_optional
    if not selected:
        selected = list(allowed_branches)
    return {
        "selected_branches": selected,
        "required_branches": final_required,
        "optional_branches": final_optional,
        "branch_scores": scores,
        "reasoning": reasoning,
        "confidence": confidence,
        "llm_provider": str((llm_out or {}).get("chat_llm_provider") or "gemini"),
        "llm_model": str((llm_out or {}).get("chat_llm_model") or model_name),
        "token_usage": (llm_out or {}).get("token_usage") or {},
        "elapsed_s": float((llm_out or {}).get("elapsed_s") or 0.0),
        "raw_response": raw_text,
    }
