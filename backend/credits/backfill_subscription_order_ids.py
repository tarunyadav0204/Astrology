#!/usr/bin/env python3
"""
Backfill Google Play subscription order IDs from the Play Developer API.

Uses purchase_token rows in play_subscription_token_map (saved when users verify/sync).
Play returns the latest GPA order for that subscription token — not full renewal history.

Usage (from backend/, with POSTGRES_DSN and Google Play service account configured):

  # Preview (calls Play API, no DB writes)
  python3 -m credits.backfill_subscription_order_ids

  # Apply updates
  python3 -m credits.backfill_subscription_order_ids --apply

  # Limit tokens (e.g. smoke test)
  python3 -m credits.backfill_subscription_order_ids --apply --limit 5
"""
from __future__ import annotations

import argparse
import json
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill subscription order IDs from Google Play API"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write order IDs to DB (default is dry-run: Play calls only, no writes)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max purchase tokens to process",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Seconds between Play API calls (rate limiting)",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    if not os.getenv("POSTGRES_DSN") and not os.getenv("DATABASE_URL"):
        print("ERROR: set POSTGRES_DSN or DATABASE_URL (e.g. in backend/.env)", file=sys.stderr)
        return 1

    from credits.credit_service import CreditService

    svc = CreditService()
    stats = svc.backfill_subscription_order_ids_from_play(
        dry_run=dry_run,
        limit=args.limit,
        sleep_seconds=max(0.0, args.sleep),
    )
    print(json.dumps(stats, indent=2, default=str))
    if stats.get("error"):
        return 1
    if dry_run:
        print("\nRe-run with --apply to save order IDs to the database.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
