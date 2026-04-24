"""
Feature flag for multi-branch parallel chat (opt-in; legacy path unchanged when off).
Safe deploy note: this file may be edited with comment-only changes to trigger backend rollout checks.

Where to set `ASTRO_PARALLEL_CHAT` (and related logging env vars):
- **Recommended:** `backend/.env` or repo-root `.env` (same files `load_dotenv` already reads for the API).
- **Alternative:** process / systemd / Docker `environment=`, Kubernetes Secret → env, PaaS dashboard.
- **Not required:** there is no separate JSON config file for this flag — it is read only from the environment.

Production rollout (parallel only for some users):
- Set ``ASTRO_PARALLEL_CHAT=1``.
- Set ``ASTRO_PARALLEL_CHAT_USER_IDS`` to a comma-separated list of numeric user IDs (e.g. ``42,1001``). Only those users get the parallel pipeline; everyone else stays on legacy chat for the same request types.
- Omit ``ASTRO_PARALLEL_CHAT_USER_IDS`` (or leave it empty) to allow **any** user when parallel is on (useful for staging; not recommended for broad production unless intentional).

Optional LLM round-trip logging (parallel path + any `generate_text_from_prompt` with `llm_log_tag`):
- `ASTRO_LLM_LOG_ROUNDS` — set to `0` / `false` to disable the one-line `[LLM_ROUNDTRIP]` summary (dump dir / bodies may still run).
- `ASTRO_LLM_LOG_BODIES=1` — print prompt/response bodies to stdout (see chunking below).
- `ASTRO_LLM_LOG_BODIES_MAX_CHARS` — max chars **per log chunk** when printing (default 12000). Long bodies print as `part 1/N` … with **no** dropped text. Set `0` or `ASTRO_LLM_LOG_FULL=1` for one block per request/response.
- `ASTRO_LLM_LOG_FULL=1` — print each body as a single block (no chunk headers); can be very large — prefer `ASTRO_LLM_LOG_DUMP_DIR` for huge Parashari prompts.
- `ASTRO_LLM_LOG_DUMP_DIR` — e.g. `/tmp/llm_dumps`: write **full** request+response per call to a `.txt` file (always, independent of chunking).

Parallel payload diagnostics (orchestrator):
- `ASTRO_PARALLEL_LOG_PROMPT_PARTS=1` — log static-instruction vs variable JSON char counts per branch + merge.
- `ASTRO_PARALLEL_LOG_PAYLOAD_KEYS=1` — log approximate JSON size per top-level payload key and per subkey inside `*_context` (finds huge `divisional_charts`, `planetary_analysis`, etc.).

Rate limits & long tails (429 / TPM / preview models fire many parallel handshakes at once):
- `ASTRO_PARALLEL_STAGGER_S` — seconds of delay **before** each branch starts after the first (default `0.55`). Spreads 7 LLM calls across ~3.3s instead of one burst (reduces HTTP 429 retry storms).
- `ASTRO_PARALLEL_BRANCH_TIMEOUT_S` — max wall time per **non-critical** branch LLM call (default `90`). On timeout/error, that branch returns `status=unavailable` and merge continues.
- `ASTRO_PARALLEL_CRITICAL_TIMEOUT_S` — same for the **Parashari** branch (default `120`). Lower than the generic 600s chat timeout so one stuck SDK retry loop cannot block the UI for many minutes.

Relational / partnership parallel rollout:
- Set ``ASTRO_PARALLEL_RELATIONAL_CHAT=1`` to route partnership mode through the relational multi-branch pipeline.
- It uses the same allowlist variable, ``ASTRO_PARALLEL_CHAT_USER_IDS``, so A/B testing can share one rollout control.
- Legacy partnership chat remains the default when this flag is off.

Agent-built branch payloads (compact JSON, not legacy `ChatContextBuilder` keys):
- `ASTRO_PARALLEL_AGENT_CONTEXT=1` — parallel branches send **context agent** output (`build_agent` / `context_agents/SCHEMA.md` short keys) instead of `context_slices` legacy blobs. Default off; requires same merged chart dict from the chat route (agents reuse `precomputed_static` / `precomputed_dynamic` when possible).
"""

from __future__ import annotations

import os
import re
from typing import Dict, Optional


def parallel_chat_enabled() -> bool:
    """When true, `GeminiChatAnalyzer.generate_chat_response` may use the parallel pipeline (subject to allowlist)."""
    return os.environ.get("ASTRO_PARALLEL_CHAT", "").strip().lower() in ("1", "true", "yes")


def parallel_relational_chat_enabled() -> bool:
    """When true, partnership/two-person chat may use the relational parallel pipeline."""
    return os.environ.get("ASTRO_PARALLEL_RELATIONAL_CHAT", "").strip().lower() in ("1", "true", "yes")


def parallel_chat_user_allowlist() -> Optional[frozenset[int]]:
    """
    Optional production gate: only these user IDs may use the parallel pipeline.

    Env: ``ASTRO_PARALLEL_CHAT_USER_IDS`` — comma/semicolon/whitespace-separated integers, e.g. ``42,1001,2048``.

    - If unset or empty after strip → **None** (no allowlist: any user may use parallel when other gates pass).
    - If set and parses to at least one ID → **only** those IDs; unknown callers without ``user_id`` are excluded.
    - If set but no valid integers → empty frozenset (**nobody** uses parallel).
    """
    raw = os.environ.get("ASTRO_PARALLEL_CHAT_USER_IDS", "").strip()
    if not raw:
        return None
    ids: set[int] = set()
    for part in re.split(r"[\s,;]+", raw):
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            continue
    return frozenset(ids)


def should_use_parallel_chat(context: dict, *, user_id: Optional[int] = None) -> bool:
    """
    Parallel pipeline is only for standard natal chart chat.
    Synastry, mundane, annual, prashna, and other modes keep the legacy single-call path.

    When ``ASTRO_PARALLEL_CHAT_USER_IDS`` is set, only listed ``user_id`` values pass (``user_id`` must be passed from routes).
    """
    if not parallel_chat_enabled():
        return False
    allow = parallel_chat_user_allowlist()
    if allow is not None:
        if not allow:
            return False
        if user_id is None or user_id not in allow:
            return False
    if not isinstance(context, dict):
        return False
    if context.get("analysis_type") == "synastry":
        return False
    if isinstance(context.get("native"), dict) and isinstance(context.get("partner"), dict):
        if context["native"].get("birth_details") and context["partner"].get("birth_details"):
            return False
    analysis_type = context.get("analysis_type") or "birth"
    if analysis_type != "birth":
        return False
    intent = context.get("intent") or {}
    mode = (intent.get("mode") or "").lower()
    if mode in ("prashna", "annual"):
        return False
    return True


def should_use_parallel_relational_chat(context: dict, *, user_id: Optional[int] = None) -> bool:
    """
    Opt-in two-person relationship/partnership pipeline.

    Uses the same user allowlist as natal parallel chat so production A/B testing has one control surface.
    """
    if not parallel_relational_chat_enabled():
        return False
    allow = parallel_chat_user_allowlist()
    if allow is not None:
        if not allow:
            return False
        if user_id is None or user_id not in allow:
            return False
    if not isinstance(context, dict):
        return False
    if context.get("analysis_type") not in ("synastry", "relational"):
        return False
    native = context.get("native")
    partner = context.get("partner")
    if not isinstance(native, dict) or not isinstance(partner, dict):
        return False
    return bool(native.get("birth_details") and partner.get("birth_details"))


def parallel_branch_stagger_s() -> float:
    """Delay between starting branch N and N+1 (branch 0 starts immediately)."""
    raw = (os.environ.get("ASTRO_PARALLEL_STAGGER_S") or "0.55").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.55


def parallel_branch_timeout_s(*, critical: bool) -> float:
    """
    Per-branch asyncio timeout for `generate_text_from_prompt` (caps SDK retry/backoff tails).
    """
    key = "ASTRO_PARALLEL_CRITICAL_TIMEOUT_S" if critical else "ASTRO_PARALLEL_BRANCH_TIMEOUT_S"
    default = "120" if critical else "90"
    raw = (os.environ.get(key) or default).strip()
    try:
        return max(5.0, min(600.0, float(raw)))
    except ValueError:
        return 120.0 if critical else 90.0
