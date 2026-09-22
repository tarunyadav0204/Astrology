"""Authoritative four-gate intraday Jyotisha evidence for Instant Chat."""

from __future__ import annotations

from typing import Any, Mapping

from calculators.trading import ClassicalIntradayTradingEngine


_SIT_OUT_SIGNALS = frozenset({"RED", "CLOSED"})
_REDUCE_SIGNALS = frozenset({"YELLOW"})


def _compact_risk(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": row.get("type"),
        "name": row.get("name"),
        "desc": row.get("desc"),
    }


def _participation(*, signal: str, natal_qualified: bool, market_open: bool) -> str:
    if not market_open or signal in _SIT_OUT_SIGNALS:
        return "sit_out"
    if signal == "ORANGE":
        return "sit_out"
    if signal in _REDUCE_SIGNALS:
        return "reduce_size"
    if signal == "GREEN":
        return "participate"
    return "cautious"


def build_intraday_trading_session(
    *,
    natal_chart: Mapping[str, Any],
    birth_data: Mapping[str, Any],
    target_date: str,
    natal_qualified: bool = False,
    current_location: Mapping[str, Any] | None = None,
    exchange: str = "NSE",
) -> dict[str, Any]:
    """Calculate all four gates; expose failures instead of serving fallback text."""
    try:
        return ClassicalIntradayTradingEngine(natal_chart, birth_data).calculate(
            str(target_date or "")[:10], current_location=current_location, exchange=exchange,
        )
    except Exception as exc:
        return {
            "schema_version": "classical_intraday.v1", "date": str(target_date or "")[:10],
            "available": False, "market_open": False, "participation": "sit_out", "windows": [],
            "calculation_error": {"type": type(exc).__name__, "message": str(exc)},
            "claim_rule": "The classical session calculation failed; no trading indication was inferred.",
        }
