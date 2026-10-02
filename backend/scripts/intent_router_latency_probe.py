"""Measure the real Instant intent router without running chart calculations."""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from ai.intent_router import IntentRouter


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--model")
    parser.add_argument("--fast-prompt", action="store_true")
    parser.add_argument("--sparse-json", action="store_true")
    parser.add_argument("--explicit-cache", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

    router = IntentRouter()
    if args.model:
        router._get_instant_model_name = lambda: args.model
    if args.fast_prompt:
        import os
        os.environ["INSTANT_INTENT_ROUTER_FAST_PROMPT"] = "1"
    if args.sparse_json:
        import os
        os.environ["INSTANT_INTENT_ROUTER_SPARSE_JSON"] = "1"
    if args.explicit_cache:
        import os
        os.environ["INSTANT_INTENT_ROUTER_EXPLICIT_CACHE"] = "1"

    for run in range(max(1, args.repeat)):
        started = time.perf_counter()
        result = await router.classify_instant_intent(
            args.question,
            [],
            language="english",
            force_ready=True,
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
        route = {
            key: result.get(key)
            for key in ("status", "mode", "category", "answer_mode", "career_subtype")
        }
        print(f"RUN={run + 1} MEASURED_MS={elapsed_ms}")
        print(f"ROUTE={route}")


if __name__ == "__main__":
    asyncio.run(main())
