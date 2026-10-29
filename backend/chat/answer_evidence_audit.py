"""Non-blocking evidence audit for completed chat answers.

This is deliberately a shadow system: it receives the answer after it has been
saved and never changes the response, credits, or streaming path seen by a
user.  The compact brief is retained for Admin Chat History only.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

from db import execute, get_conn

logger = logging.getLogger(__name__)


def audit_enabled() -> bool:
    """Feature flag kept on by default once deployed; can be disabled instantly."""
    return str(os.getenv("CHAT_ANSWER_AUDIT_ENABLED", "true")).strip().lower() not in {"0", "false", "no", "off"}


def audit_model() -> str:
    """Independent, economical judge; override only for controlled tests."""
    return str(os.getenv("CHAT_ANSWER_AUDIT_MODEL", "gpt-5.6-luna")).strip() or "gpt-5.6-luna"


def ensure_answer_evidence_audit_table(conn) -> None:
    execute(conn, """
        CREATE TABLE IF NOT EXISTS chat_answer_evidence_audits (
            message_id BIGINT PRIMARY KEY REFERENCES chat_messages(message_id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'pending',
            evidence_brief TEXT NOT NULL DEFAULT '{}',
            evaluator_result TEXT,
            evaluator_provider TEXT,
            evaluator_model TEXT,
            error_message TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)


def _compact(value: Any, max_chars: int = 2600) -> Any:
    """Keep stored/evaluated evidence bounded and serialisable."""
    try:
        encoded = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)[:max_chars]
    if len(encoded) <= max_chars:
        return value
    return {"truncated": True, "preview": encoded[:max_chars]}


def _calculated_context_packet(context: Any) -> Dict[str, Any] | None:
    """Use the same calculator-backed QA packet, never the model's prose.

    Standard/Premium already have this exact context in memory before Tara is
    called. Reusing it is both more faithful and cheaper than recalculating a
    chart after delivery. Instant/Verified may have a deliberately slim context;
    their own result evidence remains separately included below.
    """
    if not isinstance(context, dict) or not context.get("d1_chart"):
        return None
    try:
        from ai.response_qa_auditor import compact_generation_context

        return compact_generation_context(context, max_chars=36000)
    except Exception:
        logger.exception("could not compact calculated context for answer audit")
        return None


def build_evidence_brief(*, question: str, answer: str, intent: Any, result: Any,
                         chat_tier: str, calculation_context: Any = None) -> Dict[str, Any]:
    """Create a generic, calculation-led brief without sending raw model prose.

    Instant/Verified already produce a deterministic verdict/answer specification.
    Those are preserved where available; other modes retain the routed intent and
    calculated metadata. This lets the evaluator say "evidence absent" rather
    than inventing a chart basis.
    """
    result = result if isinstance(result, dict) else {}
    intent = intent if isinstance(intent, dict) else {}
    gate = result.get("answer_gate_metadata") if isinstance(result.get("answer_gate_metadata"), dict) else {}
    information = result.get("information_rounds") if isinstance(result.get("information_rounds"), dict) else {}
    brief: Dict[str, Any] = {
        "version": 1,
        "chat_tier": str(chat_tier or "unknown"),
        "question": str(question or "")[:1800],
        "answer": str(answer or "")[:6000],
        "routed_intent": _compact({
            key: intent.get(key) for key in (
                "category", "mode", "answer_mode", "time_scope", "target_subject",
                "career_subtype", "education_subtype", "wealth_subtype", "marriage_subtype",
            ) if intent.get(key) not in (None, "", [], {})
        }),
    }
    for source, keys in (
        (result, (
            "instant_path", "answer_spec", "verdict", "knowledge_graph_policy",
            "event_timing_verdict", "instant_evidence_debug", "evidence_summary",
        )),
        (gate, ("reading_mode", "instant_path", "muhurat_context", "prashna_context")),
        (information, ("reading_mode", "verdict", "evidence_summary")),
    ):
        for key in keys:
            value = source.get(key) if isinstance(source, dict) else None
            if value not in (None, "", [], {}):
                brief[key] = _compact(value)
    calculated_packet = _calculated_context_packet(calculation_context)
    if calculated_packet:
        # This is the actual D1/divisional/dasha/transit/AV basis available to
        # Tara at answer time. It is intentionally much larger than UI metadata
        # but capped well below a full generation prompt.
        brief["calculated_context"] = calculated_packet
    else:
        brief["calculated_context"] = {
            "available": False,
            "note": "No full calculator packet was available for this delivery path; do not infer missing chart facts.",
        }
    return brief


def _parse_json(text: str) -> Dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end >= start:
        raw = raw[start:end + 1]
    value = json.loads(raw)
    return value if isinstance(value, dict) else {"raw": raw}


async def run_answer_evidence_audit(message_id: int, brief: Dict[str, Any]) -> None:
    """Evaluate a completed answer after persistence; failures are isolated."""
    try:
        from ai.gemini_chat_analyzer import GeminiChatAnalyzer
        prompt = """You are an internal Jyotish answer auditor. Return JSON only. Do not rewrite the answer.
Compare the answer with the supplied evidence brief. The `calculated_context` is the authoritative calculator-backed packet: use it to verify stated placements, house lords, dashas, divisionals, SAV/BAV and transits. Be strict about claims that promise an outcome or timing without evidence, but do not penalize ordinary interpretive language merely because astrology is interpretive.

Required JSON keys:
question_type (prediction|interpretation|factual|advice|other),
answer_outcome (yes|no|conditional|unclear|not_applicable),
claim_strength (none|qualified|strong|guarantee),
brief_alignment (aligned|partially_aligned|conflicts|insufficient_evidence|not_applicable),
claim_checks (array; for every material dasha, chart placement, divisional, SAV/BAV, transit, timing, or outcome claim include claim, status=supported|conflicts|not_found, and exact_evidence),
unsupported_claims (array of concise strings),
missing_evidence (array of concise strings),
summary (one concise sentence).

EVIDENCE BRIEF:
""" + json.dumps(brief, ensure_ascii=False, default=str)
        output = await GeminiChatAnalyzer().generate_text_from_prompt(
            prompt,
            provider_override="openai",
            model_name_override=audit_model(),
            openai_reasoning_effort="medium",
            request_timeout_s=180,
            llm_log_tag="answer_evidence_audit",
        )
        if not output.get("success"):
            raise RuntimeError(str(output.get("error") or "auditor returned no result"))
        report = _parse_json(output.get("response") or "")
        with get_conn() as conn:
            ensure_answer_evidence_audit_table(conn)
            execute(conn, """
                UPDATE chat_answer_evidence_audits
                SET status = %s, evaluator_result = %s, evaluator_provider = %s,
                    evaluator_model = %s, error_message = NULL, completed_at = %s
                WHERE message_id = %s
            """, ("completed", json.dumps(report, ensure_ascii=False), output.get("chat_llm_provider"),
                  output.get("chat_llm_model"), datetime.now(), int(message_id)))
            conn.commit()
    except Exception as exc:
        logger.exception("answer evidence audit failed message_id=%s", message_id)
        try:
            with get_conn() as conn:
                ensure_answer_evidence_audit_table(conn)
                execute(conn, """
                    UPDATE chat_answer_evidence_audits
                    SET status = %s, error_message = %s, completed_at = %s
                    WHERE message_id = %s
                """, ("failed", str(exc)[:1200], datetime.now(), int(message_id)))
                conn.commit()
        except Exception:
            logger.exception("answer evidence audit failure could not be saved message_id=%s", message_id)


def schedule_answer_evidence_audit(*, message_id: int, question: str, answer: str, intent: Any, result: Any,
                                   chat_tier: str, calculation_context: Any = None) -> None:
    if not audit_enabled() or not message_id:
        return
    brief = build_evidence_brief(
        question=question, answer=answer, intent=intent, result=result,
        chat_tier=chat_tier, calculation_context=calculation_context,
    )
    try:
        with get_conn() as conn:
            ensure_answer_evidence_audit_table(conn)
            execute(conn, """
                INSERT INTO chat_answer_evidence_audits (message_id, status, evidence_brief)
                VALUES (%s, 'pending', %s)
                ON CONFLICT (message_id) DO NOTHING
            """, (int(message_id), json.dumps(brief, ensure_ascii=False, default=str)))
            conn.commit()
    except Exception:
        logger.exception("answer evidence audit could not be queued message_id=%s", message_id)
        return
    try:
        asyncio.create_task(run_answer_evidence_audit(int(message_id), brief))
    except RuntimeError:
        logger.warning("No event loop available to run answer evidence audit message_id=%s", message_id)
