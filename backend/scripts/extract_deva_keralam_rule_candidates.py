#!/usr/bin/env python3
"""Create governed draft rule candidates from catalogued Deva Keralam passages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from classical_sources.deva_keralam_rule_extraction import (
    GeminiRuleCandidateProvider,
    RuleCandidateRepository,
    preview_batch,
    run_extraction_batch,
)
from db import get_conn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract validated draft/review candidates. This command cannot publish rules."
    )
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--after-passage-key", default="")
    parser.add_argument("--page-start", type=int, default=26, help="first PDF page owned by this worker")
    parser.add_argument("--page-end", type=int, help="last PDF page owned by this worker")
    parser.add_argument("--resume-run-key")
    parser.add_argument("--model", help="Gemini model id; defaults to the extraction environment setting")
    parser.add_argument("--thinking-level", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="list eligible passages without calling Gemini or writing to the database",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.resume_run_key and args.dry_run:
        raise SystemExit("--resume-run-key cannot be combined with --dry-run")
    load_dotenv(BACKEND_DIR / ".env", override=False)
    with get_conn() as conn:
        repository = RuleCandidateRepository(conn)
        if args.dry_run:
            result = preview_batch(
                repository,
                after_passage_key=args.after_passage_key,
                batch_size=args.batch_size,
                pdf_page_start=args.page_start,
                pdf_page_end=args.page_end,
            )
        else:
            provider = GeminiRuleCandidateProvider(args.model, args.thinking_level)
            result = run_extraction_batch(
                repository,
                provider,
                batch_size=args.batch_size,
                resume_run_key=args.resume_run_key,
                after_passage_key=args.after_passage_key,
                pdf_page_start=args.page_start,
                pdf_page_end=args.page_end,
            )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
