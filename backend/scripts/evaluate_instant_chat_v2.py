#!/usr/bin/env python3
"""Run a small, evidence-visible Instant Chat v2 evaluation set.

This is intentionally an engineering/astrology QA tool, not a production API.
It exercises the same intent router, calculators, composer, and evidence packet
used by Instant Chat and prints a compact report for human review.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from ai.gemini_chat_analyzer import GeminiChatAnalyzer  # noqa: E402
from ai.intent_router import IntentRouter  # noqa: E402
from chat.instant_chat_pipeline import generate_instant_chat_response  # noqa: E402


REFERENCE_CHART: Dict[str, Any] = {
    "name": "Tarun",
    "gender": "Male",
    "date": "1980-04-02",
    "time": "14:55:00",
    "place": "Hisar, Haryana, India",
    "latitude": 29.1492,
    "longitude": 75.7217,
    "timezone": 5.5,
}

SYNTHETIC_QA_CHART: Dict[str, Any] = {
    "name": "Synthetic QA",
    "gender": "Male",
    "date": "1990-01-01",
    "time": "12:00:00",
    "place": "Synthetic equatorial test coordinate",
    "latitude": 0.0,
    "longitude": 0.0,
    "timezone": 0.0,
}

QUESTIONS = [
    "What is my strongest marriage window during the next three years?",
    "Am I more likely to receive a promotion or change jobs during the next twelve months?",
    "Why has money felt unstable recently, and when is it likely to improve?",
    "Which health area needs the most caution during the next six months?",
    "Is my wife's career likely to improve during the coming year?",
    "When was I married?",
    "When did I get married?",
]


def _preview(value: Any, limit: int = 1800) -> str:
    rendered = json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    return rendered if len(rendered) <= limit else f"{rendered[:limit]}…"


def _compact_result(question: str, intent: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    packet = result.get("instant_evidence_debug") or {}
    ledger = packet.get("evidence_ledger") or {}
    plan = packet.get("query_plan") or {}
    spec = packet.get("answer_spec") or {}
    return {
        "question": question,
        "packet_build_error": packet.get("build_error"),
        "router": {
            "status": intent.get("status"),
            "category": intent.get("category"),
            "answer_mode": intent.get("answer_mode"),
            "needs_clarification": intent.get("needs_clarification"),
            "target_subject": intent.get("target_subject") or (intent.get("extracted_context") or {}).get("target_subject"),
            "extracted_context": intent.get("extracted_context"),
            "evidence_plan": intent.get("evidence_plan"),
        },
        "answer": result.get("response"),
        "timing": result.get("timing"),
        "generation": {
            "model": result.get("chat_llm_model"),
            "prompt_chars": result.get("llm_prompt_chars"),
            "response_chars": len(result.get("response") or ""),
            "composer_metrics": packet.get("composer_metrics"),
        },
        "composer_brief": packet.get("composer_brief"),
        "query_plan": {
            key: plan.get(key)
            for key in ("category", "answer_mode", "time_scope", "target_subject", "required_capabilities")
        },
        "capabilities": [
            {
                key: capability.get(key)
                for key in ("capability", "status", "evidence_ids", "reason")
            }
            for capability in (ledger.get("capabilities") or [])
        ],
        "evidence_records": [
            {
                "evidence_id": record.get("evidence_id"),
                "kind": record.get("kind"),
                "source": record.get("source"),
                "confidence": record.get("confidence"),
                "value": _preview(record.get("value")),
            }
            for record in (ledger.get("records") or [])
        ],
        "verdict": packet.get("verdict"),
        "answer_spec": {
            "opening": spec.get("opening"),
            "claims": [
                {
                    key: claim.get(key)
                    for key in ("claim_id", "text", "evidence_ids", "confidence")
                }
                for claim in (spec.get("claims") or [])
            ],
            "follow_up": spec.get("follow_up"),
            "forbidden_claims": spec.get("forbidden_claims"),
        },
        "verification": packet.get("verification"),
    }


def _parse_json_object(text: str) -> Dict[str, Any]:
    clean = str(text or "").strip()
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", clean, flags=re.I | re.S)
    try:
        value = json.loads(clean)
        return value if isinstance(value, dict) else {"parse_error": "not_an_object", "raw": clean[:800]}
    except Exception:
        match = re.search(r"\{.*\}", clean, flags=re.S)
        if match:
            try:
                value = json.loads(match.group(0))
                return value if isinstance(value, dict) else {"parse_error": "not_an_object"}
            except Exception:
                pass
    return {"parse_error": "invalid_json", "raw": clean[:800]}


async def _judge_answer(analyzer: GeminiChatAnalyzer, row: Dict[str, Any]) -> Dict[str, Any]:
    """Independent Flash review of the Lite answer against surfaced evidence."""
    prompt = f"""You are the independent senior Vedic-astrology QA reviewer for a concise instant-chat product.
Judge the answer ONLY against the supplied evidence. Do not reward confident prose. A derived-house reading
for a spouse is evidence from the native's chart, never the spouse's own dasha/chart. A timing answer must
respect the as-of date and the user's requested horizon. A comparison may choose an option only if evidence
distinguishes the options. Health body-area specificity requires explicit body-area evidence.
A dasha chain shown as MD-AD-PD has three distinct levels: Mahadasha, Antardasha, and Pratyantardasha.
Calling the whole chain a Mahadasha/Antardasha or calling its PD planet the sub-period lord is a grounding error.

Return one JSON object only:
{{"pass": boolean, "scores": {{"directness": 0-5, "grounding": 0-5, "timing": 0-5,
"target_framing": 0-5, "brevity": 0-5, "conversation": 0-5}}, "unsupported_claims": [string],
"missed_evidence": [string], "critical_issues": [string], "better_answer": string}}
Pass only when there is no materially unsupported claim, no wrong target ownership, no expired timing window,
and all scores are at least 4. The better answer must be 70-120 words and end with one natural question.

QUESTION: {row.get('question')}
ROUTER: {json.dumps(row.get('router'), ensure_ascii=False, default=str)}
QUERY PLAN: {json.dumps(row.get('query_plan'), ensure_ascii=False, default=str)}
CAPABILITIES: {json.dumps(row.get('capabilities'), ensure_ascii=False, default=str)}
EVIDENCE: {json.dumps(row.get('evidence_records'), ensure_ascii=False, default=str)}
VERDICT: {json.dumps(row.get('verdict'), ensure_ascii=False, default=str)}
ANSWER: {row.get('answer')}
"""
    judged = await analyzer.generate_text_from_prompt(
        prompt,
        premium_analysis=False,
        force_gemini=True,
        llm_log_tag=None,
        request_timeout_s=45.0,
    )
    parsed = _parse_json_object(judged.get("response") or "")
    parsed["model"] = judged.get("chat_llm_model")
    parsed["elapsed_s"] = round(float(judged.get("elapsed_s") or 0), 3)
    return parsed


def _summary(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "question": row.get("question"),
        "router": row.get("router"),
        "answer": row.get("answer"),
        "generation": row.get("generation"),
        "query_plan": row.get("query_plan"),
        "verdict": {
            key: (row.get("verdict") or {}).get(key)
            for key in ("direction", "confidence", "ranked_windows", "missing_required_capabilities")
        },
        "verification": row.get("verification"),
        "judge": row.get("judge"),
    }


async def run(
    question_indexes: list[int] | None = None,
    *,
    judge: bool = True,
    birth_data: Dict[str, Any] | None = None,
) -> list[Dict[str, Any]]:
    logging.disable(logging.CRITICAL)
    router = IntentRouter()
    analyzer = GeminiChatAnalyzer()
    rows: list[Dict[str, Any]] = []
    selected = [QUESTIONS[index] for index in question_indexes] if question_indexes else QUESTIONS
    for question in selected:
        # Several legacy calculators still print diagnostics directly. Keep the
        # evaluator's stdout machine-readable while exercising the real path.
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            intent = await router.classify_instant_intent(
                question,
                [],
                language="english",
                force_ready=True,
            )
            result = await generate_instant_chat_response(
                analyzer,
                question=question,
                birth_data=birth_data or REFERENCE_CHART,
                intent=intent,
                history=[],
                language="english",
                speech_mode=False,
            )
        row = _compact_result(question, intent, result)
        if judge:
            row["judge"] = await _judge_answer(analyzer, row)
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--index", type=int, action="append", choices=range(len(QUESTIONS)))
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument(
        "--synthetic-chart",
        action="store_true",
        help="Use an explicitly fictional chart so provider-facing QA transmits no real birth details.",
    )
    args = parser.parse_args()
    rows = asyncio.run(run(
        args.index,
        judge=not args.no_judge,
        birth_data=SYNTHETIC_QA_CHART if args.synthetic_chart else REFERENCE_CHART,
    ))
    if not args.details:
        rows = [_summary(row) for row in rows]
    print(json.dumps(rows, ensure_ascii=False, indent=2 if args.pretty else None, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
