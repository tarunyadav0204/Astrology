#!/usr/bin/env python3
"""
Backfill play_subscription_event_log from user_subscriptions history.

Usage (from backend/, with POSTGRES_DSN set like production):

  # Preview counts and sample rows
  python3 -m credits.backfill_subscription_events

  # Write rows (idempotent)
  python3 -m credits.backfill_subscription_events --apply

Requires the new event log columns (userid, source, event_kind, …) — start the app
once or run deploy so CreditService.init_tables() migrates the table.
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill subscription event log from DB history")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert rows (default is dry-run preview only)",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    _backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        from dotenv import load_dotenv

        load_dotenv(os.path.join(_backend_dir, ".env"))
        load_dotenv()
    except ImportError:
        pass

    if not os.getenv("POSTGRES_DSN") and not os.getenv("DATABASE_URL"):
        env_path = os.path.join(_backend_dir, ".env")
        print(
            "ERROR: POSTGRES_DSN or DATABASE_URL is not set.\n"
            f"  - Add it to {env_path}\n"
            "  - Or export POSTGRES_DSN before running.",
            file=sys.stderr,
        )
        return 1

    from credits.credit_service import CreditService

    svc = CreditService()
    stats = svc.backfill_subscription_events_from_history(dry_run=dry_run)
    print(json.dumps(stats, indent=2, default=str))
    if dry_run:
        print("\nRe-run with --apply to insert events.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
