"""Compare full-contract Instant routes across two models."""
from __future__ import annotations

import asyncio
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.pop("INSTANT_INTENT_ROUTER_FAST_PROMPT", None)

from ai.intent_router import IntentRouter


QUESTIONS = [
    "What are my main career strengths?",
    "When will I get married?",
    "मेरी पदोन्नति कब होगी?",
    "Will the person I proposed to accept me?",
    "Can astrology tell if my pending biopsy report will be normal?",
    "Explain the 10th house of my D10 chart",
    "Tell me about my career and when I will marry",
    "कल मेरी परीक्षा कैसी जाएगी?",
]
MODELS = ["models/gemini-3-flash-preview", "models/gemini-3.1-flash-lite"]
FIELDS = (
    "status", "route_action", "mode", "answer_mode", "category",
    "career_subtype", "marriage_subtype", "target_subject_key",
    "response_language", "response_script", "needs_transits",
)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    rows = []
    questions = QUESTIONS[args.start:]
    if args.limit is not None:
        questions = questions[:args.limit]
    for question in questions:
        variants = {}
        for model in MODELS:
            router = IntentRouter()
            router._get_instant_model_name = lambda selected=model: selected
            started = time.perf_counter()
            result = await router.classify_instant_intent(
                question, [], language="english", force_ready=False
            )
            variants[model] = {
                "ms": round((time.perf_counter() - started) * 1000, 1),
                **{key: result.get(key) for key in FIELDS},
                "medical_urgency": (result.get("medical_triage") or {}).get("urgency"),
                "evidence_kinds": [
                    item.get("kind")
                    for item in ((result.get("evidence_plan") or {}).get("evidence_needs") or [])
                    if isinstance(item, dict)
                ],
            }
        rows.append({"question": question, "variants": variants})
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
