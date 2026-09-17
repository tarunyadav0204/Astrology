"""Cast a D1 at question time/place, then run the classical Prashna engine.

Instant and live chat can later call ``analyze_prashna`` and attach
``result["chat_evidence"]`` to the LLM packet. Do not import chat from here.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Optional

from calculators.chart_calculator import ChartCalculator
from calculators.prashna_calculator import PrashnaCalculator


def _question_clock(
    *,
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str = "",
    place: str = "",
    name: str = "Prashna",
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name or "Prashna",
        date=str(date).split("T")[0],
        time=time,
        latitude=float(latitude),
        longitude=float(longitude),
        timezone=timezone or "",
        place=place or "",
        gender="",
        relation="prashna",
    )


def analyze_prashna(
    *,
    question: str,
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    category: Optional[str] = None,
    timezone: str = "",
    place: str = "",
    horary_number: Optional[int] = None,
    name: str = "Prashna",
) -> Dict[str, Any]:
    """Full Prashna payload for the standalone screen (and later, chat)."""
    clock = _question_clock(
        date=date,
        time=time,
        latitude=latitude,
        longitude=longitude,
        timezone=timezone,
        place=place,
        name=name,
    )
    chart = ChartCalculator({}).calculate_chart(clock)
    analysis = PrashnaCalculator(chart).analyze(
        question_text=question or "",
        category=category,
        horary_number=horary_number,
    )
    analysis["clock"] = {
        "source": "question",
        "date": clock.date,
        "time": clock.time,
        "latitude": clock.latitude,
        "longitude": clock.longitude,
        "timezone": clock.timezone or "",
        "place": clock.place or "",
        "note": "This D1 is cast for the question's time and place, not the natal chart.",
    }
    if horary_number is not None:
        analysis["clock"]["horary_number"] = int(horary_number)
    explanation = analysis.get("explanation") or {}
    place = clock.place or ""
    when = f"{clock.date} at {clock.time}"
    where = f" in {place}" if place else ""
    explanation["setup"] = (
        f"This question chart was cast for {when}{where}. " + (explanation.get("setup") or "")
    )
    analysis["explanation"] = explanation
    return analysis
