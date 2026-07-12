#!/usr/bin/env python3
"""Dev-only live accuracy check for speech/instant event-timing answers.

This script intentionally calls the configured LLM provider. Run it only from a
trusted local machine with a chart you are allowed to test.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

from ai.gemini_chat_analyzer import GeminiChatAnalyzer  # noqa: E402
from ai.intent_router import IntentRouter  # noqa: E402
from chat.instant_chat_pipeline import (  # noqa: E402
    _build_instant_context,
    _compact_context_for_speech,
    _json_size,
    generate_instant_chat_response,
)
from db import execute, get_conn  # noqa: E402
from encryption_utils import EncryptionManager  # noqa: E402


DEFAULT_CASES = [
    "When will I get married",
    "When will I get a child",
    "When will I get promotion",
]

MANUAL_CASE_METADATA = {
    "When will I get married": {
        "category": "marriage",
        "event_profile": "marriage",
        "charts": ["D1", "D9", "D7"],
    },
    "When will I get a child": {
        "category": "progeny",
        "event_profile": "childbirth",
        "charts": ["D1", "D7", "D9"],
    },
    "When will I get promotion": {
        "category": "promotion",
        "event_profile": "promotion",
        "charts": ["D1", "D10", "D9"],
    },
}


def _safe_lower(value: Any) -> str:
    return str(value or "").lower()


def _contains_any(text: str, needles: List[str]) -> bool:
    return any(needle in text for needle in needles)


def _divisional_codes_from_specifics(lines: List[Any]) -> List[str]:
    codes: List[str] = []
    seen = set()
    for line in lines or []:
        for code in re.findall(r"\b(D(?:7|9|10)|Karkamsa)\b", str(line or ""), flags=re.IGNORECASE):
            normalized = "Karkamsa" if code.lower() == "karkamsa" else code.upper()
            if normalized not in seen:
                seen.add(normalized)
                codes.append(normalized)
    return codes


def _year_from_date(value: Any) -> str:
    raw = str(value or "")
    return raw[:4] if re.match(r"^\d{4}", raw) else ""


def _chain_planets(chain: str) -> List[str]:
    return [part.strip().lower() for part in str(chain or "").split("-") if part.strip()]


DOMAIN_HOUSE_CLAIM_TERMS = {
    5: ["progeny house", "house of progeny", "children house", "house of children", "child house"],
    7: ["marriage house", "house of marriage", "spouse house", "partner house"],
    10: ["career house", "house of career", "profession house", "public role house"],
    6: ["service house", "house of service", "daily work house"],
    11: ["gains house", "house of gains", "network house"],
}

EVENT_LABEL_TERMS = {
    "marriage": ["marriage", "spouse", "partner"],
    "promotion": ["promotion", "career advancement", "advancement"],
    "having a child": ["child", "children", "progeny", "baby", "pregnancy"],
    "career growth": ["career", "professional", "work"],
    "health recovery": ["health", "recovery"],
    "wealth growth": ["wealth", "money", "financial", "finance"],
}

STIFF_SPEECH_PHRASES = [
    "astrological indicators suggest",
    "astrological indicators point",
    "materialization window",
    "this event",
    "these matters",
    "planetary influences",
    "fortune and dharma",
    "house of fortune",
]


def _chart_summary_for_output(birth: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": birth.get("id"),
        "userid": birth.get("userid"),
        "name": birth.get("name"),
        "date": birth.get("date"),
        "time": birth.get("time"),
        "place": birth.get("place"),
        "timezone": birth.get("timezone"),
        "relation": birth.get("relation"),
    }


def load_chart_by_id(chart_id: int) -> Dict[str, Any]:
    encryptor = EncryptionManager()
    with get_conn() as conn:
        row = execute(
            conn,
            """
            SELECT id, userid, name, date, time, latitude, longitude, timezone, place, gender, relation
            FROM birth_charts
            WHERE id = %s
            """,
            (chart_id,),
        ).fetchone()
    if not row:
        raise RuntimeError(f"No birth_charts row found for id={chart_id}")
    return {
        "id": row[0],
        "birth_chart_id": row[0],
        "userid": row[1],
        "name": encryptor.decrypt(row[2]) if row[2] else "",
        "date": encryptor.decrypt(row[3]) if row[3] else "",
        "time": encryptor.decrypt(row[4]) if row[4] else "",
        "latitude": float(encryptor.decrypt(str(row[5]))),
        "longitude": float(encryptor.decrypt(str(row[6]))),
        "timezone": row[7] or "UTC",
        "place": encryptor.decrypt(row[8]) if row[8] else "",
        "gender": row[9] or "",
        "relation": row[10] or "",
    }


def find_chart_by_name(name_query: str, *, limit: int = 3000) -> List[Dict[str, Any]]:
    query = _safe_lower(name_query).strip()
    if not query:
        return []
    encryptor = EncryptionManager()
    matches: List[Dict[str, Any]] = []
    with get_conn() as conn:
        rows = execute(
            conn,
            """
            SELECT id, userid, name, timezone, relation, created_at
            FROM birth_charts
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        ).fetchall()
    for row in rows or []:
        try:
            name = encryptor.decrypt(row[2]) if row[2] else ""
        except Exception:
            continue
        if query in _safe_lower(name):
            matches.append(
                {
                    "id": row[0],
                    "userid": row[1],
                    "name": name,
                    "timezone": row[3],
                    "relation": row[4],
                    "created_at": str(row[5]),
                }
            )
    return matches


def manual_intent(question: str, category: str, event_profile: str, charts: List[str], query_context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "READY",
        "mode": "LIFESPAN_EVENT_TIMING",
        "category": category,
        "answer_mode": "event_prediction",
        "target_subject_key": "self",
        "needs_transits": True,
        "divisional_charts": charts,
        "extracted_context": {"timeframe": question},
        "query_context": query_context,
        "evidence_plan": {
            "schema_version": "evidence_plan.v1",
            "question_parts": [
                {
                    "part_id": "p1",
                    "text": question,
                    "intent_families": ["event_timing"],
                    "life_domain": category,
                    "event_profile": event_profile,
                    "subject": "self",
                    "timeframe": {"kind": "open_future"},
                    "confidence": "high",
                }
            ],
            "evidence_needs": [
                {
                    "need_id": "n1",
                    "kind": "natal_topic_foundation",
                    "system": "parashari",
                    "topic": category,
                    "supports_parts": ["p1"],
                    "params": {"event_profile": event_profile, "required_charts": charts},
                    "priority": "required",
                },
                {
                    "need_id": "n2",
                    "kind": "future_dasha_event_windows",
                    "system": "vimshottari",
                    "topic": category,
                    "supports_parts": ["p1"],
                    "params": {"event_profile": event_profile},
                    "priority": "required",
                },
                {
                    "need_id": "n3",
                    "kind": "transit_event_windows",
                    "system": "transits",
                    "topic": category,
                    "supports_parts": ["p1"],
                    "params": {"event_profile": event_profile},
                    "priority": "required",
                },
            ],
            "safety": {
                "blocked_content_checks": [
                    {"check_id": "death_prediction", "action_if_detected": "refuse_and_redirect"},
                    {"check_id": "fetal_sex_determination", "action_if_detected": "refuse_and_redirect"},
                ],
                "answer_safety_checks": [
                    "no_fatalism",
                    "no_guaranteed_prediction",
                    "no_unsupported_exact_date",
                ],
            },
            "answer_plan": {
                "style": "speech_concise",
                "must_answer_parts": ["p1"],
                "answer_order": ["p1"],
            },
        },
    }


def evaluate_answer(answer: str, verdict: Dict[str, Any], divisional_specifics: Optional[List[Any]] = None) -> Dict[str, Any]:
    ans = _safe_lower(answer)
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    current_window = verdict.get("current_window") if isinstance(verdict.get("current_window"), dict) else {}
    future_cluster = verdict.get("best_future_cluster") if isinstance(verdict.get("best_future_cluster"), dict) else {}
    comparison = str(verdict.get("comparison") or "")
    answer_rule = str(verdict.get("answer_rule") or "")
    answer_event_label = str(verdict.get("answer_event_label") or verdict.get("event_category") or "").strip().lower()

    if answer_event_label and answer_event_label not in {"general", "this event"}:
        event_terms = EVENT_LABEL_TERMS.get(answer_event_label, [answer_event_label])
        add_check(
            "names_asked_event",
            _contains_any(ans, event_terms),
            f"Answer should plainly name the asked event: {answer_event_label}.",
        )

    if current_window:
        add_check(
            "acknowledges_current_window",
            _contains_any(ans, ["current", "now", "active", "present", "right now"]),
            "Required when verdict.current_window exists.",
        )
    else:
        add_check(
            "does_not_need_current_window",
            True,
            "No prominent current window in verdict.",
        )

    future_year = _year_from_date(future_cluster.get("start"))
    if future_year:
        add_check(
            "mentions_best_future_year",
            future_year in ans,
            f"Expected year {future_year} from best_future_cluster.start.",
        )
    else:
        add_check("no_future_year_required", True, "No best future cluster.")

    chain = str(future_cluster.get("chain") or "")
    planets = _chain_planets(chain)
    if planets:
        add_check(
            "mentions_future_chain_planets",
            all(planet in ans for planet in planets),
            f"Expected chain planets from {chain}.",
        )

    if comparison == "current_active_future_slightly_cleaner":
        overstate_terms = [
            "clearly superior",
            "overwhelming",
            "only real",
            "no chance now",
            "far stronger",
            "much stronger",
            "definitely",
            "guaranteed",
        ]
        add_check(
            "does_not_overstate_small_delta",
            not _contains_any(ans, overstate_terms),
            "Small score delta must not become a dramatic future-only verdict.",
        )
        measured_terms = ["slight", "slightly", "cleaner", "mixed", "less settled", "not overwhelmingly", "not absent"]
        if not _contains_any(ans, measured_terms):
            warnings.append("Small-delta verdict would be stronger if answer used measured wording like slightly/cleaner/mixed.")

    forbidden_moves = verdict.get("forbidden_answer_moves") if isinstance(verdict.get("forbidden_answer_moves"), list) else []
    if forbidden_moves:
        exact_date_claim = bool(re.search(r"\b(on|exactly on)\s+\d{1,2}\s+[a-z]+\s+\d{4}\b", ans))
        add_check(
            "does_not_invent_exact_date",
            not exact_date_claim,
            "Avoid exact event dates beyond supplied windows.",
        )

    if "current evidence is not the main materialization window" in answer_rule:
        add_check(
            "future_window_lead_ok",
            bool(future_year and future_year in ans),
            "Future-window verdict should lead with supplied best future cluster.",
        )

    claim_contract = verdict.get("claim_contract") if isinstance(verdict.get("claim_contract"), dict) else {}
    future_contract = claim_contract.get("best_future_window") if isinstance(claim_contract.get("best_future_window"), dict) else {}
    current_contract = claim_contract.get("current_window") if isinstance(claim_contract.get("current_window"), dict) else {}
    active_houses = {
        int(h)
        for h in list(future_contract.get("activated_focus_houses") or [])
        + list(current_contract.get("activated_focus_houses") or [])
        if str(h).isdigit()
    }
    unsupported_terms = []
    for house, terms in DOMAIN_HOUSE_CLAIM_TERMS.items():
        if house in active_houses:
            continue
        unsupported_terms.extend([term for term in terms if term in ans])
    add_check(
        "no_inactive_named_house_claims",
        not unsupported_terms,
        "Named domain-house claims must match houses active in the supplied timing window. "
        + (f"Unsupported terms: {unsupported_terms}" if unsupported_terms else "No unsupported named house claims found."),
    )

    stiff_hits = [phrase for phrase in STIFF_SPEECH_PHRASES if phrase in ans]
    add_check(
        "speech_naturalness_no_stiff_placeholders",
        not stiff_hits,
        "Speech answer should avoid report-like/vague phrases. "
        + (f"Found: {stiff_hits}" if stiff_hits else "No stiff placeholder phrases found."),
    )

    divisional_codes = _divisional_codes_from_specifics(divisional_specifics or [])
    if divisional_codes:
        mentioned_codes = [
            code
            for code in divisional_codes
            if re.search(rf"\b{re.escape(code)}\b", answer, flags=re.IGNORECASE)
        ]
        add_check(
            "mentions_available_divisional_chart",
            bool(mentioned_codes),
            "Event answers should mention one supplied divisional chart code for credibility. "
            + (f"Mentioned: {mentioned_codes}; available: {divisional_codes}" if mentioned_codes else f"Available but not mentioned: {divisional_codes}"),
        )

    passed = all(row["passed"] for row in checks)
    return {"passed": passed, "checks": checks, "warnings": warnings}


def compact_verdict(verdict: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_category": verdict.get("event_category"),
        "answer_event_label": verdict.get("answer_event_label"),
        "comparison": verdict.get("comparison"),
        "score_delta": verdict.get("score_delta"),
        "confidence": verdict.get("confidence"),
        "current_window": verdict.get("current_window"),
        "best_future_cluster": verdict.get("best_future_cluster"),
        "answer_rule": verdict.get("answer_rule"),
        "claim_contract": verdict.get("claim_contract"),
        "required_answer_points": verdict.get("required_answer_points"),
        "forbidden_answer_moves": verdict.get("forbidden_answer_moves"),
    }


def print_human_report(report: Dict[str, Any]) -> None:
    print("\n=== Event Timing Accuracy Report ===")
    chart = report["chart"]
    print(f"Chart: {chart.get('name')} (id={chart.get('id')}, user={chart.get('userid')})")
    print(f"Generated: {report['generated_at']}")
    print(f"Mode: {'manual intents' if report.get('manual_intents') else 'real router'}")
    for idx, item in enumerate(report["results"], 1):
        verdict = item.get("event_timing_verdict") or {}
        evaluation = item.get("evaluation") or {}
        print(f"\n--- {idx}. {item['question']} ---")
        print(
            "Router:",
            f"status={item['router'].get('status')}",
            f"mode={item['router'].get('mode')}",
            f"category={item['router'].get('category')}",
            f"answer_mode={item['router'].get('answer_mode')}",
        )
        print(
            "Timing:",
            f"router={item['timing_ms'].get('router')}",
            f"context={item['timing_ms'].get('context')}",
            f"answer_total={item['timing_ms'].get('answer_total')}",
            f"llm_s={item['timing_ms'].get('main_llm_s')}",
        )
        print(
            "Verdict:",
            f"event={verdict.get('event_category')}",
            f"label={verdict.get('answer_event_label')}",
            f"comparison={verdict.get('comparison')}",
            f"delta={verdict.get('score_delta')}",
            f"confidence={verdict.get('confidence')}",
        )
        if verdict.get("current_window"):
            cw = verdict["current_window"]
            print(f"Current: {cw.get('start')} to {cw.get('end')} | {cw.get('chain')} | score {cw.get('score')}")
        if verdict.get("best_future_cluster"):
            fw = verdict["best_future_cluster"]
            print(f"Future:  {fw.get('start')} to {fw.get('end')} | {fw.get('chain')} | score {fw.get('score')}")
        if item.get("divisional_specifics"):
            print("Divisionals:")
            for line in item.get("divisional_specifics") or []:
                print(f"  - {line}")
        print(f"Rule: {verdict.get('answer_rule')}")
        print("Answer:")
        print(item.get("answer") or "")
        print(f"Evaluation: {'PASS' if evaluation.get('passed') else 'FAIL'}")
        for check in evaluation.get("checks") or []:
            icon = "OK" if check.get("passed") else "FAIL"
            print(f"  [{icon}] {check.get('name')}: {check.get('detail')}")
        for warning in evaluation.get("warnings") or []:
            print(f"  [WARN] {warning}")


async def run_case(
    *,
    question: str,
    birth: Dict[str, Any],
    query_context: Dict[str, Any],
    manual: bool,
    verbose_llm_log: bool,
) -> Dict[str, Any]:
    router_ms: Optional[float] = None
    if manual:
        meta = MANUAL_CASE_METADATA.get(question) or {
            "category": "general",
            "event_profile": "general_event",
            "charts": ["D1", "D9"],
        }
        intent = manual_intent(question, meta["category"], meta["event_profile"], meta["charts"], query_context)
    else:
        started = time.perf_counter()
        intent = await IntentRouter().classify_instant_intent(
            question,
            [],
            clarification_count=0,
            max_clarifications=1,
            language="english",
            query_context=query_context,
        )
        router_ms = round((time.perf_counter() - started) * 1000, 1)

    started = time.perf_counter()
    ctx = _build_instant_context(
        birth,
        question,
        intent,
        [],
        answer_mode_override=str(intent.get("answer_mode") or "event_prediction"),
        target_subject_override={
            "key": intent.get("target_subject_key") or "self",
            "label": intent.get("target_subject_key") or "self",
            "base_house": 1,
        },
    )
    context_ms = round((time.perf_counter() - started) * 1000, 1)
    compact = _compact_context_for_speech(ctx)

    stdout_capture = None
    answer_started = time.perf_counter()
    if verbose_llm_log:
        result = await generate_instant_chat_response(
            GeminiChatAnalyzer(),
            question=question,
            birth_data=birth,
            intent=intent,
            history=[],
            language="english",
            speech_mode=True,
        )
    else:
        import io

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            result = await generate_instant_chat_response(
                GeminiChatAnalyzer(),
                question=question,
                birth_data=birth,
                intent=intent,
                history=[],
                language="english",
                speech_mode=True,
            )
        stdout_capture = buf.getvalue()
    answer_ms = round((time.perf_counter() - answer_started) * 1000, 1)

    normalized = compact.get("normalized_evidence") if isinstance(compact.get("normalized_evidence"), dict) else {}
    compact_parashari = compact.get("instant_parashari") if isinstance(compact.get("instant_parashari"), dict) else {}
    verdict = normalized.get("event_timing_verdict") if isinstance(normalized.get("event_timing_verdict"), dict) else {}
    answer = str(result.get("response") or "")
    divisional_specifics = list(normalized.get("divisional_specifics") or [])[:4]
    evaluation = evaluate_answer(answer, verdict, divisional_specifics)

    return {
        "question": question,
        "router": {
            "status": intent.get("status"),
            "mode": intent.get("mode"),
            "category": intent.get("category"),
            "answer_mode": intent.get("answer_mode"),
            "needs_transits": intent.get("needs_transits"),
            "divisional_charts": intent.get("divisional_charts"),
        },
        "timing_ms": {
            "router": router_ms,
            "context": context_ms,
            "answer_total": answer_ms,
            "main_llm_s": (result.get("timing") or {}).get("total_request_time"),
        },
        "context_sizes": {
            "full_chars": _json_size(ctx),
            "compact_chars": _json_size(compact),
            "llm_prompt_chars": result.get("llm_prompt_chars"),
            "llm_response_chars": result.get("llm_response_chars"),
        },
        "event_timing_verdict": compact_verdict(verdict),
        "primary_drivers": list(normalized.get("primary_drivers") or [])[:6],
        "divisional_specifics": divisional_specifics,
        "divisional_support": compact_parashari.get("divisional_support") or normalized.get("divisional_support") or {},
        "answer": answer,
        "followups": result.get("follow_up_questions") or [],
        "evaluation": evaluation,
        "llm_stdout_capture": stdout_capture[-4000:] if stdout_capture else "",
    }


async def async_main(args: argparse.Namespace) -> Dict[str, Any]:
    os.environ.setdefault("SPEECH_COMPACT_CONTEXT", "true")
    if args.no_llm_roundtrip_log:
        os.environ.setdefault("ASTROROSHNI_SUPPRESS_LLM_ROUNDTRIP_LOG", "true")

    if args.find_chart:
        matches = find_chart_by_name(args.find_chart, limit=args.find_limit)
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "find_chart": args.find_chart,
            "matches": matches,
        }

    birth = load_chart_by_id(args.chart_id)
    query_context = {
        "client_now_iso": args.client_now_iso,
        "timezone_name": args.timezone_name,
        "utc_offset_minutes": args.utc_offset_minutes,
    }
    results = []
    for question in args.question:
        results.append(
            await run_case(
                question=question,
                birth=birth,
                query_context=query_context,
                manual=args.manual_intents,
                verbose_llm_log=args.verbose_llm_log,
            )
        )
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "manual_intents": args.manual_intents,
        "chart": _chart_summary_for_output(birth),
        "query_context": query_context,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", type=int, default=int(os.getenv("EVENT_TIMING_TEST_CHART_ID", "10289")))
    parser.add_argument("--find-chart", help="Decrypt recent chart names locally and list matches; does not call LLM.")
    parser.add_argument("--find-limit", type=int, default=3000)
    parser.add_argument("--question", action="append", default=None, help="Question to test. Repeat for multiple.")
    parser.add_argument("--manual-intents", action="store_true", help="Skip real intent router and use built-in event timing intents.")
    parser.add_argument("--client-now-iso", default=os.getenv("EVENT_TIMING_TEST_NOW", "2026-07-10T12:00:00+05:30"))
    parser.add_argument("--timezone-name", default=os.getenv("EVENT_TIMING_TEST_TZ", "Asia/Kolkata"))
    parser.add_argument("--utc-offset-minutes", type=int, default=int(os.getenv("EVENT_TIMING_TEST_UTC_OFFSET", "330")))
    parser.add_argument("--json-out", default=str(BACKEND_DIR / "dev_event_timing_accuracy_report.json"))
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--verbose-llm-log", action="store_true", help="Do not capture internal LLM roundtrip prints.")
    parser.add_argument("--no-llm-roundtrip-log", action="store_true", help="Set suppression env if supported by local analyzer.")
    args = parser.parse_args()
    if args.question is None:
        args.question = list(DEFAULT_CASES)
    return args


def main() -> None:
    args = parse_args()
    report = asyncio.run(async_main(args))
    if args.json_out and not args.find_chart:
        out_path = Path(args.json_out)
        out_path.write_text(json.dumps(report, ensure_ascii=False, default=str, indent=2), encoding="utf-8")
    if args.json_only:
        print(json.dumps(report, ensure_ascii=False, default=str, indent=2))
    else:
        print_human_report(report)
        if args.json_out and not args.find_chart:
            print(f"\nJSON report written to: {args.json_out}")


if __name__ == "__main__":
    main()
