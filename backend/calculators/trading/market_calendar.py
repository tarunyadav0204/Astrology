from __future__ import annotations

from datetime import date, datetime
from typing import Any


# NSE Capital Market circular NSE/CMTR/71775, 12 December 2025.
# Special Sunday sessions are intentionally not guessed: they must be added with
# their exchange-published clock times before this calendar will open them.
_NSE_2026_HOLIDAYS = {
    "2026-01-15": "Municipal Corporation Election in Maharashtra",
    "2026-01-26": "Republic Day",
    "2026-03-03": "Holi",
    "2026-03-26": "Shri Ram Navami",
    "2026-03-31": "Shri Mahavir Jayanti",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-28": "Bakri Id",
    "2026-06-26": "Muharram",
    "2026-09-14": "Ganesh Chaturthi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-10": "Diwali-Balipratipada",
    "2026-11-24": "Prakash Gurpurb Sri Guru Nanak Dev",
    "2026-12-25": "Christmas",
}

_NSE_2026_SPECIAL_SESSIONS = {
    # NSE/CMTR/72349, 16 January 2026.
    "2026-02-01": {"open": "09:15", "close": "15:30", "reason": "Union Budget live trading session", "circular": "NSE/CMTR/72349"},
}


class MarketSessionCalendar:
    """Versioned exchange calendar. Unknown years fail closed instead of guessing."""

    source = {
        "exchange": "NSE Capital Market",
        "circular": "NSE/CMTR/71775",
        "published": "2025-12-12",
        "url": "https://nsearchives.nseindia.com/content/circulars/CMTR71775.pdf",
    }

    def session(self, value: str | date | datetime, exchange: str = "NSE") -> dict[str, Any]:
        day = value.date() if isinstance(value, datetime) else value
        if not isinstance(day, date):
            day = datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
        day_key = day.isoformat()
        if str(exchange).upper() != "NSE":
            return self._closed(day_key, "Unsupported exchange calendar", verified=False)
        if day.year != 2026:
            return self._closed(day_key, "Exchange calendar is not verified for this year", verified=False)
        if day_key in _NSE_2026_SPECIAL_SESSIONS:
            special = _NSE_2026_SPECIAL_SESSIONS[day_key]
            return {
                "date": day_key, "exchange": "NSE", "market_open": True,
                "open": special["open"], "close": special["close"], "timezone": "Asia/Kolkata",
                "calendar_verified": True, "reason": special["reason"],
                "source": {**self.source, "circular": special["circular"]},
            }
        if day.weekday() >= 5:
            return self._closed(day_key, "Weekend", verified=True)
        if day_key in _NSE_2026_HOLIDAYS:
            return self._closed(day_key, _NSE_2026_HOLIDAYS[day_key], verified=True)
        return {
            "date": day_key, "exchange": "NSE", "market_open": True,
            "open": "09:15", "close": "15:30", "timezone": "Asia/Kolkata",
            "calendar_verified": True, "reason": "Regular cash-market session",
            "source": dict(self.source),
        }

    def _closed(self, day_key: str, reason: str, *, verified: bool) -> dict[str, Any]:
        return {
            "date": day_key, "exchange": "NSE", "market_open": False,
            "open": None, "close": None, "timezone": "Asia/Kolkata",
            "calendar_verified": verified, "reason": reason, "source": dict(self.source),
        }
