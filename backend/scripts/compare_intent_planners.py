"""Run one question through legacy LLM planning and deterministic planning."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from ai.intent_router import IntentRouter


SEMANTIC_FIELDS = (
    "status", "route_action", "mode", "answer_mode", "category",
    "career_subtype", "marriage_subtype", "wealth_subtype",
    "education_subtype", "children_subtype", "home_subtype",
    "foreign_subtype", "target_subject_key", "target_subject_keys",
    "response_language", "response_script",
)
PLANNING_FIELDS = (
    "context_type", "needs_transits", "divisional_charts", "transit_request",
)


def _evidence_summary(result: dict[str, Any]) -> dict[str, Any]:
    plan = result.get("evidence_plan") if isinstance(result.get("evidence_plan"), dict) else {}
    return {
        "parts": [
            {
                key: part.get(key)
                for key in ("intent_families", "life_domain", "event_profile", "subject", "timeframe")
            }
            for part in plan.get("question_parts") or []
            if isinstance(part, dict)
        ],
        "needs": [
            {
                key: need.get(key)
                for key in ("kind", "system", "topic", "params")
            }
            for need in plan.get("evidence_needs") or []
            if isinstance(need, dict)
        ],
    }


async def _curl_generate(prompt: str, model_name: str, timeout_s: float) -> SimpleNamespace:
    api_key = os.getenv("GEMINI_API_KEY") or ""
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    model_id = str(model_name or "").removeprefix("models/")
    body = json.dumps({
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "topP": 0.95,
            "topK": 40,
            "responseMimeType": "application/json",
        },
    }, ensure_ascii=False)

    def invoke() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "curl", "-fsS", "--max-time", str(max(3.0, timeout_s)),
                "-X", "POST", "-H", "Content-Type: application/json",
                "-H", f"x-goog-api-key: {api_key}", "--data-binary", "@-",
                f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent",
            ],
            input=body,
            text=True,
            capture_output=True,
            timeout=max(5.0, timeout_s + 3.0),
            check=False,
        )

    completed = await asyncio.to_thread(invoke)
    if completed.returncode != 0:
        raise RuntimeError(f"curl Gemini request failed: {completed.stderr.strip()[:500]}")
    payload = json.loads(completed.stdout)
    text = "".join(
        str(part.get("text") or "")
        for candidate in payload.get("candidates") or []
        for part in ((candidate.get("content") or {}).get("parts") or [])
        if isinstance(part, dict)
    )
    usage = payload.get("usageMetadata") or {}
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=int(usage.get("promptTokenCount") or 0),
            candidates_token_count=int(usage.get("candidatesTokenCount") or 0),
            cached_content_token_count=int(usage.get("cachedContentTokenCount") or 0),
            total_token_count=int(usage.get("totalTokenCount") or 0),
        ),
    )


async def _run(
    question: str, *, deterministic: bool, semantic_v2: bool,
    model: str | None, curl_transport: bool
) -> dict[str, Any]:
    env_name = "INSTANT_INTENT_ROUTER_DETERMINISTIC_PLAN"
    semantic_env_name = "INSTANT_INTENT_ROUTER_SEMANTIC_V2"
    previous = os.environ.get(env_name)
    previous_semantic = os.environ.get(semantic_env_name)
    os.environ[env_name] = "1" if deterministic else "0"
    os.environ[semantic_env_name] = "1" if semantic_v2 else "0"
    try:
        router = IntentRouter()
        if model:
            router._get_instant_model_name = lambda: model
        if curl_transport:
            router._generate_instant_content = _curl_generate
        started = time.perf_counter()
        result = await router.classify_instant_intent(question, [], language="english")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    finally:
        if previous is None:
            os.environ.pop(env_name, None)
        else:
            os.environ[env_name] = previous
        if previous_semantic is None:
            os.environ.pop(semantic_env_name, None)
        else:
            os.environ[semantic_env_name] = previous_semantic

    usage = result.get("_llm_usage_stage") if isinstance(result.get("_llm_usage_stage"), dict) else {}
    return {
        "elapsed_ms": elapsed_ms,
        "prompt_chars": usage.get("prompt_chars"),
        "response_chars": usage.get("response_chars"),
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "semantic": {field: result.get(field) for field in SEMANTIC_FIELDS if result.get(field) is not None},
        "planning": {field: result.get(field) for field in PLANNING_FIELDS},
        "evidence": _evidence_summary(result),
        "planning_source": result.get("planning_source") or "llm_legacy",
    }


def _diff(left: Any, right: Any, path: str = "") -> list[dict[str, Any]]:
    if isinstance(left, dict) and isinstance(right, dict):
        rows = []
        for key in sorted(set(left) | set(right)):
            rows.extend(_diff(left.get(key), right.get(key), f"{path}.{key}" if path else key))
        return rows
    if left != right:
        return [{"field": path, "legacy": left, "deterministic": right}]
    return []


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--model")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--request-timeout", type=float)
    parser.add_argument("--curl-transport", action="store_true")
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.request_timeout:
        timeout = str(max(3.0, args.request_timeout))
        os.environ["INSTANT_INTENT_ROUTER_TIMEOUT_S"] = timeout
        os.environ["INSTANT_INTENT_ROUTER_RETRY_TIMEOUT_S"] = timeout
        os.environ["INSTANT_INTENT_ROUTER_WALL_TIMEOUT_S"] = str(float(timeout) + 2.0)
        os.environ["INSTANT_INTENT_ROUTER_RETRY_WALL_TIMEOUT_S"] = str(float(timeout) + 2.0)

    legacy = await _run(
        args.question, deterministic=False, semantic_v2=False, model=args.model,
        curl_transport=args.curl_transport,
    )
    deterministic = await _run(
        args.question, deterministic=True, semantic_v2=True, model=args.model,
        curl_transport=args.curl_transport,
    )
    payload = {
        "question": args.question,
        "legacy": legacy,
        "deterministic": deterministic,
        "semantic_differences": _diff(legacy["semantic"], deterministic["semantic"]),
        "planning_differences": _diff(
            {"planning": legacy["planning"], "evidence": legacy["evidence"]},
            {"planning": deterministic["planning"], "evidence": deterministic["evidence"]},
        ),
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps({
        "question": args.question,
        "legacy_ms": legacy["elapsed_ms"],
        "deterministic_ms": deterministic["elapsed_ms"],
        "legacy_tokens": {"in": legacy["input_tokens"], "out": legacy["output_tokens"]},
        "deterministic_tokens": {"in": deterministic["input_tokens"], "out": deterministic["output_tokens"]},
        "semantic_difference_count": len(payload["semantic_differences"]),
        "planning_difference_count": len(payload["planning_differences"]),
        "report": str(args.output) if args.output else None,
    }, ensure_ascii=False), flush=True)
    if not args.output:
        print(rendered, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
