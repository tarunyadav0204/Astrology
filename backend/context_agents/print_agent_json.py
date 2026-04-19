"""
Print exactly one JSON object to stdout: the payload from a context agent.

Use this to verify structure (not pytest). Library print/warn noise during the
build is discarded; only the final JSON is written.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import redirect_stderr, redirect_stdout


def _backend_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    backend = _backend_dir()
    if backend not in sys.path:
        sys.path.insert(0, backend)

    parser = argparse.ArgumentParser(description="Print one agent JSON to stdout (no extra logs).")
    parser.add_argument("--agent", default="core_d1", help="Registered agent id (default: core_d1)")
    parser.add_argument("--user-id", type=int, default=7, help="birth_charts.userid when using DB")
    parser.add_argument(
        "--birth-json",
        metavar="PATH",
        help="Birth dict JSON file; if set, DB is not used",
    )
    parser.add_argument(
        "--intent-json",
        metavar="PATH",
        help="Optional intent_result JSON (e.g. {\"divisional_charts\":[\"D9\",\"D10\"]}) for agents like div_intent",
    )
    parser.add_argument(
        "--time-scope",
        metavar="SCOPE",
        choices=("full", "intent_window", "current"),
        help="Optional ContextTimeScope override (same as AgentContext.time_scope)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Single-line JSON (smaller; default is indented for reading)",
    )
    args = parser.parse_args()

    from context_agents.birth_from_db import fetch_latest_birth_for_user, load_backend_dotenv
    from context_agents.base import AgentContext
    from context_agents.registry import build_agent

    load_backend_dotenv()

    if args.birth_json:
        with open(os.path.expanduser(args.birth_json), encoding="utf-8") as f:
            birth = json.load(f)
    else:
        birth = fetch_latest_birth_for_user(args.user_id)

    intent_result = None
    if args.intent_json:
        with open(os.path.expanduser(args.intent_json), encoding="utf-8") as f:
            intent_result = json.load(f)

    # Discard stdout/stderr from calculators during build (structure check only).
    with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
        ctx_kw: dict = {"birth_data": birth, "intent_result": intent_result}
        if args.time_scope:
            ctx_kw["time_scope"] = args.time_scope
        out = build_agent(
            args.agent,
            AgentContext(**ctx_kw),
        )

    if args.compact:
        sys.stdout.write(json.dumps(out, separators=(",", ":"), ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(json.dumps(out, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
