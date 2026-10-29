"""Last-mile integrity checks for lifespan timing answers.

The timing calculator already ranks viable AD/PD bands deterministically.  A
language model may still summarise only the strongest band and accidentally
turn a lower-ranked viable period into vague "preparation".  This module keeps
the calculated ranking visible without changing the model's interpretation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


_DASH_RE = re.compile(r"[^a-z0-9]+")


def _normalise(value: Any) -> str:
    return _DASH_RE.sub("", str(value or "").lower())


def _years(value: Any) -> List[str]:
    return re.findall(r"\b(?:19|20)\d{2}\b", str(value or ""))


def _candidate_is_explicitly_present(answer: str, candidate: Dict[str, Any]) -> bool:
    """Require a numbered window plus its own dates/chain, not a passing mention.

    A reference to "Jupiter–Mercury" in a risk paragraph must not count as
    presenting the Jupiter–Mercury candidate window.
    """
    rank = int(candidate.get("rank") or 0)
    if rank <= 0:
        return False
    numbered = re.search(rf"\b(?:window|rank)\s*#?{rank}\b", answer, re.IGNORECASE)
    if not numbered:
        return False

    start_years = _years(candidate.get("start"))
    end_years = _years(candidate.get("end"))
    has_period = bool(start_years and end_years and start_years[0] in answer and end_years[0] in answer)

    chain = _normalise(candidate.get("dasha_chain"))
    compact_answer = _normalise(answer)
    # The answer may use an en dash, hyphen, spaces, or "Jupiter Mercury".
    has_chain = bool(chain and chain in compact_answer)
    return has_period and has_chain


def _window_label(candidate: Dict[str, Any]) -> str:
    rank = int(candidate.get("rank") or 0)
    if rank == 1:
        return "Primary"
    return "Secondary viable window"


def _render_candidate(candidate: Dict[str, Any]) -> str:
    rank = int(candidate.get("rank") or 0)
    start = str(candidate.get("start") or "—")
    end = str(candidate.get("end") or "—")
    execution_start = str(candidate.get("execution_start") or "")
    execution_end = str(candidate.get("execution_end") or "")
    execution = f"{execution_start} – {execution_end}" if execution_start and execution_end else "Not separately calculated"
    dasha = str(candidate.get("dasha_chain") or "Not supplied")
    transit = str(candidate.get("double_transit") or "none").replace("_", " ")
    reasons = [str(reason).strip() for reason in (candidate.get("why") or []) if str(reason).strip()]
    reason = reasons[0] if reasons else "Calculated dasha and transit support."
    return (
        f"- **Window {rank} — {_window_label(candidate)}**: {start} – {end}\n"
        f"  - Ripe period: {start} – {end}; execution refinement: {execution}\n"
        f"  - Dasha: {dasha}; transit support: {transit}.\n"
        f"  - Why it is ranked here: {reason}"
    )


def ensure_complete_ranked_lifespan_windows(
    answer: str,
    lifespan_timing_evidence: Dict[str, Any] | None,
) -> str:
    """Append only candidate windows the draft failed to present explicitly.

    This is deliberately a deterministic, no-LLM correction: dates, rank, and
    dasha chain remain exactly those produced by the timing calculator.
    """
    if not isinstance(lifespan_timing_evidence, dict) or not answer:
        return answer
    candidates: Iterable[Any] = lifespan_timing_evidence.get("candidate_windows") or []
    ranked = sorted(
        (candidate for candidate in candidates if isinstance(candidate, dict) and candidate.get("rank")),
        key=lambda candidate: int(candidate.get("rank") or 0),
    )[:5]
    if not ranked:
        return answer

    missing = [
        candidate for candidate in ranked
        if not _candidate_is_explicitly_present(answer, candidate)
    ]
    if not missing:
        return answer

    heading = (
        "### Calculated timing windows — complete strength order"
        if len(missing) == len(ranked)
        else "### Additional calculated timing window(s)"
    )
    intro = (
        "These are listed by calculated strength, not calendar order. A secondary "
        "window remains a viable period; it must not be treated as preparation only."
    )
    return answer.rstrip() + "\n\n" + heading + "\n\n" + intro + "\n\n" + "\n".join(
        _render_candidate(candidate) for candidate in missing
    )
