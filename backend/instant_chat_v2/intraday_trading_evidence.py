"""Bounded trader-session evidence for Instant Wealth `intraday_trading`.

Natal investment permission stays in the existing Wealth foundation. This
module only adds the day's climate and market-hour windows. It never picks a
security or predicts market direction.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from calculators.trading_calendar_service import TradingCalendarService


_SIT_OUT_SIGNALS = frozenset({"RED", "CLOSED"})
_REDUCE_SIGNALS = frozenset({"ORANGE"})


def _compact_risk(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": row.get("type"),
        "name": row.get("name"),
        "desc": row.get("desc"),
    }


def _participation(*, signal: str, natal_qualified: bool, market_open: bool) -> str:
    if not market_open or signal in _SIT_OUT_SIGNALS:
        return "sit_out"
    if signal in _REDUCE_SIGNALS or natal_qualified:
        return "reduce_size" if signal not in _SIT_OUT_SIGNALS else "sit_out"
    if signal == "GREEN" and not natal_qualified:
        return "participate"
    return "cautious"


def build_intraday_trading_session(
    *,
    natal_chart: Mapping[str, Any],
    birth_data: Mapping[str, Any],
    target_date: str,
    natal_qualified: bool = False,
) -> dict[str, Any]:
    """Return compact session climate + Choghadiya windows for one market day."""
    date_str = str(target_date or "")[:10]
    try:
        target_dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return {
            "date": date_str,
            "available": False,
            "market_open": False,
            "participation": "sit_out",
            "claim_rule": "Session date is unavailable, so do not invent windows or a trade.",
        }

    session: dict[str, Any] = {
        "date": date_str,
        "market_hours": {"start": "09:15", "end": "15:30", "timezone_note": "session clock uses the natal location"},
        "available": False,
        "market_open": target_dt.weekday() not in {5, 6},
        "participation": "sit_out",
        "claim_rule": (
            "This is the native's trading-session climate, not a market forecast. "
            "Never name a security, strike, index direction, leverage or guaranteed P&L. "
            "A green hora cannot override a sit-out day climate or a leaky natal speculation pattern."
        ),
    }
    if not session["market_open"]:
        session["available"] = True
        session["signal"] = "CLOSED"
        session["action"] = "Market closed"
        session["headline"] = "Weekend — cash-market session is closed."
        session["windows"] = []
        session["entry_windows"] = []
        session["caution_windows"] = []
        return session

    try:
        natal_copy = dict(natal_chart)
        service = TradingCalendarService(natal_copy, dict(birth_data))
        packed = service.get_session_forecast(target_dt)
    except Exception:
        return session

    luck = packed.get("luck") if isinstance(packed.get("luck"), Mapping) else {}
    timings = packed.get("timings") if isinstance(packed.get("timings"), Mapping) else {}
    details = luck.get("details") if isinstance(luck.get("details"), Mapping) else {}
    windows = [
        dict(row)
        for row in list(timings.get("timings") or [])
        if isinstance(row, dict) and row.get("start") and row.get("end")
    ]
    signal = str(luck.get("signal") or "ORANGE").upper()
    session.update({
        "available": True,
        "signal": signal,
        "action": luck.get("action"),
        "headline": luck.get("headline"),
        "luck_score": luck.get("luck_score"),
        "market_mood": luck.get("market_mood") if isinstance(luck.get("market_mood"), Mapping) else {},
        "risk_factors": [
            _compact_risk(row) for row in list(luck.get("risk_factors") or []) if isinstance(row, Mapping)
        ][:6],
        "tara_bala": details.get("tara_bala") if isinstance(details.get("tara_bala"), Mapping) else {},
        "chandra_bala": details.get("chandra_bala") if isinstance(details.get("chandra_bala"), Mapping) else {},
        "ashtakavarga": details.get("ashtakavarga") if isinstance(details.get("ashtakavarga"), Mapping) else {},
        "windows": windows,
        "entry_windows": [row for row in windows if str(row.get("quality") or "").startswith("Good")],
        "caution_windows": [
            row for row in windows
            if str(row.get("quality") or "") in {"Bad", "Neutral (Good for momentum)"}
        ],
        "window_note": timings.get("note"),
    })
    if natal_qualified and signal == "GREEN":
        signal_for_participation = "YELLOW"
    else:
        signal_for_participation = signal
    session["participation"] = _participation(
        signal=signal_for_participation,
        natal_qualified=bool(natal_qualified),
        market_open=True,
    )
    session["natal_permission"] = "qualified" if natal_qualified else "supported"
    return session
