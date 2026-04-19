"""
Structured logging for individual LLM HTTP round-trips (parallel branches + merge).

Enable full prompt/response bodies with ASTRO_LLM_LOG_BODIES=1 (can be very large).

Environment:
- ASTRO_LLM_LOG_ROUNDS=0 — disable one-line [LLM_ROUNDTRIP] summaries.
- ASTRO_LLM_LOG_BODIES=1 — print request/response bodies (see chunking below).
- ASTRO_LLM_LOG_BODIES_MAX_CHARS — max characters **per printed chunk** (default 12000). Bodies longer than this
  are split across multiple log blocks (`part 1/N` …); the **full** text is still printed (no `[truncated]` loss).
  Set to `0` or use ASTRO_LLM_LOG_FULL=1 to print each of request/response as a **single** block (no part headers).
- ASTRO_LLM_LOG_FULL=1 — unlimited chunk size for stdout bodies (one print per request / per response).
- ASTRO_LLM_LOG_DUMP_DIR — if set (e.g. /tmp/llm_dumps), write each call to a file (always full text; avoids huge stdout).
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional

import logging

_logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _print_llm_body_to_stdout(
    tag: str,
    section: str,
    text: Optional[str],
    *,
    chunk_chars: Optional[int],
) -> None:
    """
    Print a full prompt or response. If chunk_chars is a positive int and text is longer,
    emit multiple blocks so log viewers are not overwhelmed by a single huge line, without dropping bytes.
    """
    t = "" if text is None else str(text)
    total = len(t)
    header = f"[LLM_ROUNDTRIP:{tag}] ===== {section}"
    if chunk_chars is None or chunk_chars <= 0:
        print(f"{header} ({total} chars) =====\n{t}")
        return
    if total <= chunk_chars:
        print(f"{header} ({total} chars) =====\n{t}")
        return
    n_parts = (total + chunk_chars - 1) // chunk_chars
    for i in range(n_parts):
        lo = i * chunk_chars
        hi = min(lo + chunk_chars, total)
        print(f"{header} part {i + 1}/{n_parts} (chars {lo}-{hi} of {total}) =====\n{t[lo:hi]}")


def _safe_tag_for_filename(tag: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", tag)[:120] or "llm"


def _maybe_write_dump_file(
    *,
    tag: str,
    prompt: str,
    response_text: Optional[str],
) -> None:
    dump_dir = (os.getenv("ASTRO_LLM_LOG_DUMP_DIR") or "").strip()
    if not dump_dir:
        return
    os.makedirs(dump_dir, exist_ok=True)
    name = f"{_safe_tag_for_filename(tag)}_{int(time.time() * 1000)}.txt"
    path = os.path.join(dump_dir, name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"=== TAG {tag} ===\n")
            f.write(f"=== REQUEST ({len(prompt or '')} chars) ===\n")
            f.write(prompt or "")
            f.write("\n\n")
            f.write(f"=== RESPONSE ({len(response_text or '')} chars) ===\n")
            f.write(response_text or "")
        _logger.info("LLM dump written: %s", path)
        print(f"[LLM_ROUNDTRIP] full dump file: {path}")
    except OSError as e:
        _logger.warning("LLM dump write failed: %s", e)


def log_llm_roundtrip(
    *,
    tag: str,
    provider: str,
    model: Optional[str],
    prompt: str,
    response_text: Optional[str],
    success: bool,
    error: Optional[str],
    usage: Dict[str, Any],
    elapsed_s: float,
) -> None:
    """
    One line: chars + token breakdown. Optional full bodies via ASTRO_LLM_LOG_BODIES=1.
    """
    pc = len(prompt or "")
    rc = len(response_text or "")
    it = int(usage.get("input_tokens") or usage.get("prompt_token_count") or 0)
    ot = int(usage.get("output_tokens") or usage.get("candidates_token_count") or 0)
    ct = int(usage.get("cached_tokens") or usage.get("cached_content_token_count") or 0)
    tt_raw = int(usage.get("total_tokens") or usage.get("total_token_count") or 0)
    if not tt_raw and (it or ot):
        tt_raw = it + ot
    sane_sum = it + ot + ct
    # Some Gemini paths report total_token_count inflated (e.g. accumulated across internal retries on 429).
    tt_log = tt_raw
    inflated_note = ""
    if tt_raw > 0 and sane_sum > 0 and tt_raw > max(sane_sum * 4, sane_sum + 20000):
        tt_log = sane_sum
        inflated_note = f" tokens_total_reported={tt_raw}"

    err_s = (error or "")[:200]
    # Parallel chat passes `tag`; disable one-line summary with ASTRO_LLM_LOG_ROUNDS=0
    # (dump dir / bodies can still run).
    if _env_bool("ASTRO_LLM_LOG_ROUNDS", default=True):
        print(
            f"[LLM_ROUNDTRIP] tag={tag} provider={provider} model={model or 'n/a'} "
            f"success={success} elapsed_s={elapsed_s:.2f} "
            f"prompt_chars={pc} response_chars={rc} "
            f"tokens_in={it} tokens_out={ot} tokens_cached={ct} tokens_total={tt_log}{inflated_note} "
            f"error={err_s!r}"
        )

    _maybe_write_dump_file(tag=tag, prompt=prompt, response_text=response_text)

    if _env_bool("ASTRO_LLM_LOG_BODIES"):
        if _env_bool("ASTRO_LLM_LOG_FULL"):
            chunk: Optional[int] = None
        else:
            raw_env = os.getenv("ASTRO_LLM_LOG_BODIES_MAX_CHARS")
            if raw_env is None or str(raw_env).strip() == "":
                chunk = 12000
            else:
                raw_max = str(raw_env).strip()
                chunk = None if raw_max == "0" else int(raw_max)
        _print_llm_body_to_stdout(tag, "REQUEST", prompt, chunk_chars=chunk)
        _print_llm_body_to_stdout(tag, "RESPONSE", response_text, chunk_chars=chunk)
        if chunk is None and (pc > 500_000 or rc > 200_000):
            _logger.info(
                "LLM full body logging: large payload (prompt_chars=%s response_chars=%s tag=%s). "
                "Prefer ASTRO_LLM_LOG_DUMP_DIR for inspection.",
                pc,
                rc,
                tag,
            )


def json_serialized_size(obj: Any) -> int:
    """UTF-8 length of compact JSON (for payload breakdown logging)."""
    try:
        return len(json.dumps(obj, default=str, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        return len(str(obj))
