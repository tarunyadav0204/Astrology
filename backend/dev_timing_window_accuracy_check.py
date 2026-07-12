#!/usr/bin/env python3
"""Dev-only live accuracy check for speech/instant timing-window answers.

This script intentionally calls the configured LLM provider unless
`--context-only` is used. Run it only from a trusted local machine with a chart
you are allowed to test.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    "What will be happen tomorrow?",
    "How will be my day tomorrow?",
    "How will be my next year?",
]


def _safe_lower(value: Any) -> str:
    return str(value or "").lower()


def _contains_any(text: str, needles: List[str]) -> bool:
    hay = _safe_lower(text)
    return any(_safe_lower(needle) in hay for needle in needles)


def _client_now(args: argparse.Namespace) -> datetime:
    raw = str(args.client_now_iso or "").strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime(2026, 7, 10, 12, 0, 0)


def _expected_window(question: str, now_local: datetime) -> Dict[str, Any]:
    q = _safe_lower(question)
    if "tomorrow" in q:
        dt = now_local + timedelta(days=1)
        return {
            "kind": "day",
            "start": dt.strftime("%Y-%m-%d"),
            "end": dt.strftime("%Y-%m-%d"),
            "span_days": 1,
            "label_terms": ["tomorrow", dt.strftime("%Y"), dt.strftime("%d %B"), dt.strftime("%B %d")],
            "use_pd": True,
            "use_sk_pr": True,
        }
    if "next year" in q:
        year = now_local.year + 1
        return {
            "kind": "window",
            "start": f"{year}-01-01",
            "end": f"{year}-12-31",
            "span_days": 365,
            "label_terms": ["next year", str(year), f"year {year}"],
            "use_pd": True,
            "use_sk_pr": False,
        }
    return {}


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


def manual_intent(question: str, query_context: Dict[str, Any], now_local: datetime) -> Dict[str, Any]:
    q = _safe_lower(question)
    if "tomorrow" in q:
        specific_date = (now_local + timedelta(days=1)).strftime("%Y-%m-%d")
        return {
            "status": "READY",
            "mode": "PREDICT_DAILY",
            "category": "general",
            "answer_mode": "timing_window",
            "target_subject_key": "self",
            "needs_transits": True,
            "daily_intent_confirmed": True,
            "dasha_as_of": specific_date,
            "extracted_context": {
                "timeframe": "tomorrow",
                "specific_date": specific_date,
                "specific_date_basis": "relative_user_day",
            },
            "query_context": query_context,
            "evidence_plan": {
                "schema_version": "evidence_plan.v1",
                "question_parts": [
                    {
                        "part_id": "p1",
                        "text": question,
                        "intent_families": ["daily_forecast", "topic_outlook"],
                        "life_domain": "general",
                        "event_profile": None,
                        "subject": "self",
                        "timeframe": {"kind": "relative_day", "granularity": "exact_day"},
                        "confidence": "high",
                    }
                ],
                "evidence_needs": [
                    {
                        "need_id": "n1",
                        "kind": "period_forecast_context",
                        "system": "vimshottari",
                        "topic": "general",
                        "supports_parts": ["p1"],
                        "params": {"period_kind": "day", "date": specific_date, "include_deeper_levels": True},
                        "priority": "required",
                    },
                    {
                        "need_id": "n2",
                        "kind": "transit_snapshot",
                        "system": "transits",
                        "topic": "general",
                        "supports_parts": ["p1"],
                        "params": {"date": specific_date},
                        "priority": "required",
                    },
                ],
            },
        }
    year = now_local.year + 1
    return {
        "status": "READY",
        "mode": "PREDICT_PERIOD_OUTLOOK",
        "category": "general",
        "answer_mode": "timing_window",
        "target_subject_key": "self",
        "needs_transits": True,
        "extracted_context": {"timeframe": "next year", "specific_date_basis": "not_date_bound"},
        "query_context": query_context,
        "transit_request": {"startYear": year, "endYear": year},
        "evidence_plan": {
            "schema_version": "evidence_plan.v1",
            "question_parts": [
                {
                    "part_id": "p1",
                    "text": question,
                    "intent_families": ["period_forecast", "topic_outlook"],
                    "life_domain": "general",
                    "event_profile": None,
                    "subject": "self",
                    "timeframe": {"kind": "relative_year", "granularity": "year_window"},
                    "confidence": "high",
                }
            ],
            "evidence_needs": [
                {
                    "need_id": "n1",
                    "kind": "period_forecast_context",
                    "system": "vimshottari",
                    "topic": "general",
                    "supports_parts": ["p1"],
                    "params": {"period_kind": "year", "start": f"{year}-01-01", "end": f"{year}-12-31"},
                    "priority": "required",
                },
                {
                    "need_id": "n2",
                    "kind": "transit_period_anchors",
                    "system": "transits",
                    "topic": "general",
                    "supports_parts": ["p1"],
                    "params": {"start_year": year, "end_year": year, "slow_planets_only": True},
                    "priority": "required",
                },
            ],
        },
    }


def evaluate_case(item: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    warnings: List[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    router = item.get("router") or {}
    period_window = item.get("period_window") or {}
    window_rules = item.get("window_rules") or {}
    segments = ((item.get("window_dasha_segments") or {}).get("segments") or [])
    answer = str(item.get("answer") or "")
    answer_lower = _safe_lower(answer)
    expected_kind = expected.get("kind")
    has_answer = bool(answer.strip())

    add_check("answer_mode_timing_window", router.get("answer_mode") == "timing_window", "Router/override should produce answer_mode=timing_window.")
    if expected_kind == "day":
        add_check("router_daily_or_period", router.get("mode") in {"PREDICT_DAILY", "PREDICT_PERIOD_OUTLOOK"}, "Tomorrow should be daily mode, or at least period outlook if router is conservative.")
    else:
        add_check("router_period_outlook", router.get("mode") == "PREDICT_PERIOD_OUTLOOK", "Next year should route as PREDICT_PERIOD_OUTLOOK.")
    add_check("needs_transits", bool(router.get("needs_transits")), "Timing-window questions need transits.")
    add_check("period_kind", period_window.get("kind") == expected.get("kind"), f"Expected period kind {expected.get('kind')}.")
    add_check("period_start", period_window.get("start") == expected.get("start"), f"Expected start {expected.get('start')}.")
    add_check("period_end", period_window.get("end") == expected.get("end"), f"Expected end {expected.get('end')}.")
    add_check("period_use_pd", bool(period_window.get("use_pd")) == bool(expected.get("use_pd")), f"Expected use_pd={expected.get('use_pd')}.")
    add_check("period_use_sk_pr", bool(period_window.get("use_sk_pr")) == bool(expected.get("use_sk_pr")), f"Expected use_sk_pr={expected.get('use_sk_pr')}.")
    add_check("window_segments_present", bool(segments), "Expected window_dasha_segments to be built.")

    if expected_kind == "day":
        add_check("window_rules_day_like", bool(window_rules.get("day_like")), "Expected normalized window_rules.day_like=true.")
        if has_answer:
            add_check("answer_mentions_day_anchor", _contains_any(answer, expected.get("label_terms") or []), "Answer should mention tomorrow/date anchor.")
            add_check("answer_uses_deeper_day_language", _contains_any(answer_lower, ["sookshma", "prana", "micro", "fine trigger", "day"]), "Day answer should show day-level/deeper timing awareness.")
    elif expected_kind == "window":
        add_check("window_rules_year_like", bool(window_rules.get("year_like")), "Expected normalized window_rules.year_like=true.")
        if has_answer:
            add_check("answer_mentions_year_anchor", _contains_any(answer, expected.get("label_terms") or []), "Answer should mention next-year/year anchor.")
            add_check("answer_mentions_phases", _contains_any(answer_lower, ["phase", "part of the year", "early", "mid", "later", "stronger", "weaker"]), "Year answer should mention phases or stronger/weaker parts.")

    if has_answer:
        stiff_hits = [
            phrase
            for phrase in ["astrological indicators suggest", "materialization window", "this event", "these matters"]
            if phrase in answer_lower
        ]
        add_check("speech_naturalness_no_stiff_placeholders", not stiff_hits, f"Stiff phrases: {stiff_hits}" if stiff_hits else "No stiff placeholder phrases found.")
    else:
        warnings.append("Context-only run skipped answer wording checks.")

    if len(answer) > 900:
        warnings.append("Speech answer is long for voice UX; consider tightening.")
    return {"passed": all(row["passed"] for row in checks), "checks": checks, "warnings": warnings}


def print_human_report(report: Dict[str, Any]) -> None:
    print("\n=== Timing Window Speech Accuracy Report ===")
    chart = report["chart"]
    print(f"Chart: {chart.get('name')} (id={chart.get('id')}, user={chart.get('userid')})")
    print(f"Generated: {report['generated_at']}")
    print(f"Mode: {'manual intents' if report.get('manual_intents') else 'real router'}")
    for idx, item in enumerate(report["results"], 1):
        evaluation = item.get("evaluation") or {}
        period_window = item.get("period_window") or {}
        print(f"\n--- {idx}. {item['question']} ---")
        print(
            "Router:",
            f"status={item['router'].get('status')}",
            f"mode={item['router'].get('mode')}",
            f"category={item['router'].get('category')}",
            f"answer_mode={item['router'].get('answer_mode')}",
            f"needs_transits={item['router'].get('needs_transits')}",
        )
        print(
            "Window:",
            f"kind={period_window.get('kind')}",
            f"start={period_window.get('start')}",
            f"end={period_window.get('end')}",
            f"use_pd={period_window.get('use_pd')}",
            f"use_sk_pr={period_window.get('use_sk_pr')}",
        )
        print(
            "Timing:",
            f"router={item['timing_ms'].get('router')}",
            f"context={item['timing_ms'].get('context')}",
            f"answer_total={item['timing_ms'].get('answer_total')}",
            f"llm_s={item['timing_ms'].get('main_llm_s')}",
        )
        print(
            "Context:",
            f"full={item['context_sizes'].get('full_chars')}",
            f"compact={item['context_sizes'].get('compact_chars')}",
            f"prompt={item['context_sizes'].get('llm_prompt_chars')}",
            f"response={item['context_sizes'].get('llm_response_chars')}",
        )
        segs = (item.get("window_dasha_segments") or {}).get("segments") or []
        print(f"Segments: {len(segs)}")
        for seg in segs[:3]:
            print(
                f"  - {seg.get('start')} to {seg.get('end')}: "
                f"{seg.get('mahadasha')}-{seg.get('antardasha')}-{seg.get('pratyantardasha')} "
                f"score={seg.get('relevance_score')} houses={seg.get('activated_focus_houses')}"
            )
        print("Answer:")
        print(item.get("answer") or "(context-only: answer not generated)")
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
    context_only: bool,
    verbose_llm_log: bool,
    now_local: datetime,
) -> Dict[str, Any]:
    router_ms: Optional[float] = None
    if manual:
        intent = manual_intent(question, query_context, now_local)
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
        answer_mode_override=str(intent.get("answer_mode") or "timing_window"),
        target_subject_override={
            "key": intent.get("target_subject_key") or "self",
            "label": intent.get("target_subject_key") or "self",
            "base_house": 1,
        },
    )
    context_ms = round((time.perf_counter() - started) * 1000, 1)
    compact = _compact_context_for_speech(ctx)
    normalized = compact.get("normalized_evidence") if isinstance(compact.get("normalized_evidence"), dict) else {}
    compact_parashari = compact.get("instant_parashari") if isinstance(compact.get("instant_parashari"), dict) else {}

    result: Dict[str, Any] = {"response": "", "timing": {}, "llm_prompt_chars": None, "llm_response_chars": None}
    stdout_capture = None
    answer_ms = None
    if not context_only:
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

    item = {
        "question": question,
        "router": {
            "status": intent.get("status"),
            "mode": intent.get("mode"),
            "category": intent.get("category"),
            "answer_mode": intent.get("answer_mode"),
            "needs_transits": intent.get("needs_transits"),
            "daily_intent_confirmed": intent.get("daily_intent_confirmed"),
            "specific_date": (intent.get("extracted_context") or {}).get("specific_date") if isinstance(intent.get("extracted_context"), dict) else None,
            "timeframe": (intent.get("extracted_context") or {}).get("timeframe") if isinstance(intent.get("extracted_context"), dict) else None,
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
        "period_window": compact_parashari.get("period_window") or (normalized.get("current_timing") or {}).get("period_window") or {},
        "window_rules": normalized.get("window_rules") or {},
        "current_timing": normalized.get("current_timing") or {},
        "primary_drivers": list(normalized.get("primary_drivers") or [])[:6],
        "window_dasha_segments": normalized.get("window_dasha_segments") or {},
        "active_areas": list(normalized.get("active_areas") or [])[:4],
        "answer": str(result.get("response") or ""),
        "followups": result.get("follow_up_questions") or [],
        "llm_stdout_capture": stdout_capture[-4000:] if stdout_capture else "",
    }
    item["evaluation"] = evaluate_case(item, _expected_window(question, now_local))
    return item


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

    now_local = _client_now(args)
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
                context_only=args.context_only,
                verbose_llm_log=args.verbose_llm_log,
                now_local=now_local,
            )
        )
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "manual_intents": args.manual_intents,
        "context_only": args.context_only,
        "chart": _chart_summary_for_output(birth),
        "query_context": query_context,
        "results": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chart-id", type=int, default=int(os.getenv("TIMING_WINDOW_TEST_CHART_ID", "10261")))
    parser.add_argument("--find-chart", help="Decrypt recent chart names locally and list matches; does not call LLM.")
    parser.add_argument("--find-limit", type=int, default=3000)
    parser.add_argument("--question", action="append", default=None, help="Question to test. Repeat for multiple.")
    parser.add_argument("--manual-intents", action="store_true", help="Skip real intent router and use built-in timing-window intents.")
    parser.add_argument("--context-only", action="store_true", help="Build/evaluate context only; skip final answer LLM call.")
    parser.add_argument("--client-now-iso", default=os.getenv("TIMING_WINDOW_TEST_NOW", "2026-07-10T12:00:00+05:30"))
    parser.add_argument("--timezone-name", default=os.getenv("TIMING_WINDOW_TEST_TZ", "Asia/Kolkata"))
    parser.add_argument("--utc-offset-minutes", type=int, default=int(os.getenv("TIMING_WINDOW_TEST_UTC_OFFSET", "330")))
    parser.add_argument("--json-out", default=str(BACKEND_DIR / "dev_timing_window_accuracy_report.json"))
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
