"""Adapter boundary between Instant Chat v2 and existing astrology calculators.

The current vertical slice consumes the already-calculated Instant context.  A
later calculator can be moved behind this boundary without changing planning,
fusion, verification, persistence, or either client inspector.
"""

from __future__ import annotations

from typing import Any, Dict

from .evidence import build_evidence_ledger


def execute_evidence_plan(
    *, instant_context: Dict[str, Any], evidence_plan: Dict[str, Any]
) -> Dict[str, Any]:
    return build_evidence_ledger(instant_context, evidence_plan)
