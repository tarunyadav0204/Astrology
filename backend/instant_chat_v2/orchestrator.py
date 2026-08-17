"""Facade for the first evidence-driven Instant Chat implementation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from .answer_spec import build_answer_spec, verify_answer_spec
from .capability_gateway import execute_evidence_plan
from .compiler import compile_evidence_plan
from .fusion import fuse_evidence
from .planner import build_query_plan


def build_instant_v2_packet(*, question: str, intent: Dict[str, Any] | None,
                            answer_mode: str, target_subject: Dict[str, Any] | None,
                            language: str, instant_context: Dict[str, Any]) -> Dict[str, Any]:
    # `_build_instant_context` is the last semantic-resolution stage in the
    # existing Instant pipeline. Prefer its resolved fields while preserving
    # the router's structured query context and requested evidence.
    planner_intent = dict(intent or {})
    resolved_intent = instant_context.get("intent_summary")
    if isinstance(resolved_intent, dict):
        for key in (
            "category",
            "mode",
            "period_window",
            "time_relation",
            "focus_houses",
            "focus_planets",
            "target_subject",
        ):
            value = resolved_intent.get(key)
            if value not in (None, "", [], {}):
                planner_intent[key] = value
    query_plan = build_query_plan(
        question=question, intent=planner_intent, answer_mode=answer_mode,
        target_subject=target_subject, language=language,
        as_of=(instant_context.get("current_dashas") or {}).get("as_of"),
    )
    evidence_plan = compile_evidence_plan(query_plan)
    ledger = execute_evidence_plan(instant_context=instant_context, evidence_plan=evidence_plan)
    verdict = fuse_evidence(query_plan, ledger)
    answer_spec = build_answer_spec(query_plan, verdict, ledger)
    verification = verify_answer_spec(answer_spec, ledger)
    return {
        "schema_version": "instant-audit-packet/v1",
        "test_mode": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "query_plan": query_plan,
        "evidence_plan": evidence_plan,
        "evidence_ledger": ledger,
        "verdict": verdict,
        "answer_spec": answer_spec,
        "verification": verification,
    }


def finalize_instant_v2_packet(packet: Dict[str, Any], *, answer: str) -> Dict[str, Any]:
    result = dict(packet or {})
    verification = dict(result.get("verification") or {})
    clean_answer = str(answer or "").strip()
    max_words = int((result.get("answer_spec") or {}).get("max_words") or 170)
    response_checks = {
        "answer_present": bool(clean_answer),
        "within_word_budget": len(clean_answer.split()) <= max_words,
        "ends_with_conversational_question": clean_answer.rstrip().endswith("?"),
    }
    verification["answer_present"] = response_checks["answer_present"]
    verification["response_checks"] = response_checks
    # `passed` deliberately describes contract integrity, not semantic proof of
    # every sentence. A later independent verifier will own that stronger claim.
    verification["passed"] = bool(verification.get("passed")) and response_checks["answer_present"]
    result["verification"] = verification
    result["answer_preview"] = clean_answer[:500]
    return result
