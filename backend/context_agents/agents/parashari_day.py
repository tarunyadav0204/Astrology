"""
Agent `parashari_day`: exact-day Parashari support block.

Provides a compact single-day payload for daily / specific-date questions:
  - exact target date
  - Panchanga (tithi / yoga / karana / vara)
  - Moon transit sign / house / nakshatra / pada / lord
  - fast transit positions (Sun, Moon, Mercury, Venus, Mars)

This fills the main gap in compact Parashari payloads where `transit_win` focuses on
slow-graha activations and `dasha_win` focuses on Vimshottari windows.
"""

from __future__ import annotations

import os
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any, Dict, List, Optional

from calculators.panchang_calculator import PanchangCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from chat.chat_context_builder import ChatContextBuilder
from context_agents.base import AgentContext, ContextAgent
from context_agents.scope import effective_time_scope

_FAST_PLANETS = ("Sun", "Moon", "Mercury", "Venus", "Mars")
_SIGN_NAMES = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
_NAKSHATRA_LORDS = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)


def _target_date_from_ctx(ctx: AgentContext) -> Optional[datetime]:
    ir = ctx.intent_result if isinstance(ctx.intent_result, dict) else {}
    as_of = ir.get("dasha_as_of")
    if isinstance(as_of, str) and len(as_of) >= 10:
        try:
            return datetime.strptime(as_of[:10], "%Y-%m-%d")
        except ValueError:
            return None

    mode = str(ir.get("mode") or "").upper()
    if mode == "PREDICT_DAILY":
        return datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)
    return None


def _nakshatra_lord(index_0: int) -> str:
    return _NAKSHATRA_LORDS[index_0 % 9]


def _planet_row(planet: str, longitude: float, asc_deg: float, rtc: RealTransitCalculator) -> Dict[str, Any]:
    sign0 = int(longitude / 30) % 12
    nk = rtc.get_nakshatra_from_longitude(longitude)
    return {
        "p": planet,
        "s": sign0 + 1,
        "sn": _SIGN_NAMES[sign0],
        "h": ((sign0 - int(asc_deg / 30)) % 12) + 1,
        "dg": round(longitude % 30, 2),
        "nk": nk["name"],
        "pd": nk["pada"],
        "nl": _nakshatra_lord(int(nk["index"])),
    }


class ParashariDayAgent(ContextAgent):
    agent_id = "parashari_day"
    schema_version = 1

    def build(self, ctx: AgentContext) -> Dict[str, Any]:
        target_dt = _target_date_from_ctx(ctx)
        if target_dt is None:
            return {"a": self.agent_id, "v": self.schema_version, "x": False}

        birth = ctx.birth_data or {}
        if ctx.precomputed_static is not None:
            static = ctx.precomputed_static
        else:
            builder = ChatContextBuilder()
            birth_hash = builder._create_birth_hash(birth)
            with open(os.devnull, "w", encoding="utf-8") as dn, redirect_stdout(dn), redirect_stderr(dn):
                if birth_hash not in builder.static_cache:
                    builder.static_cache[birth_hash] = builder._build_static_context(birth)
                static = builder.static_cache[birth_hash]

        d1 = static.get("d1_chart") or {}
        asc_deg = float(d1.get("ascendant", 0.0) or 0.0)

        lat = float(birth.get("latitude") or 0.0)
        lon = float(birth.get("longitude") or 0.0)
        tz = birth.get("timezone")
        tz_s = str(tz) if tz is not None else None

        panchang = PanchangCalculator().calculate_panchang(
            target_dt.strftime("%Y-%m-%d"),
            "12:00:00",
            lat,
            lon,
            timezone=tz_s,
        )

        rtc = RealTransitCalculator()
        fast_rows: List[Dict[str, Any]] = []
        moon_row: Dict[str, Any] = {}
        for planet in _FAST_PLANETS:
            lon_deg = rtc.get_planet_position(target_dt, planet)
            if lon_deg is None:
                continue
            row = _planet_row(planet, lon_deg, asc_deg, rtc)
            fast_rows.append(row)
            if planet == "Moon":
                moon_row = row

        return {
            "a": self.agent_id,
            "v": self.schema_version,
            "x": True,
            "sc": effective_time_scope(ctx).value,
            "dt": target_dt.strftime("%Y-%m-%d"),
            "P": {
                "vr": ((panchang.get("vara") or {}).get("name") or "")[:16],
                "ti": ((panchang.get("tithi") or {}).get("name") or "")[:24],
                "pk": ((panchang.get("tithi") or {}).get("paksha") or "")[:8],
                "yg": ((panchang.get("yoga") or {}).get("name") or "")[:24],
                "ka": ((panchang.get("karana") or {}).get("name") or "")[:24],
            },
            "M": moon_row,
            "F": fast_rows,
        }
