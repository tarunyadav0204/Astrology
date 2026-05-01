from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from daily.daily_confidence import build_daily_confidence
from daily.daily_contract import build_daily_output_contract
from daily.daily_fast_planets import build_daily_fast_planets
from daily.daily_intraday import build_daily_intraday
from daily.daily_micro_intents import classify_daily_micro_intent


def _compact_birth_summary(context: Dict[str, Any]) -> Dict[str, Any]:
    birth = context.get("birth_details") or {}
    d1 = context.get("d1_chart") or {}
    planets = (d1.get("planets") or {})
    moon = planets.get("Moon") or {}
    asc_sign = d1.get("ascendant_sign")
    if not asc_sign and d1.get("ascendant") is not None:
        try:
            asc_index = int(float(d1.get("ascendant")) / 30) % 12
            asc_sign = (
                "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
            )[asc_index]
        except Exception:
            asc_sign = None
    return {
        "name": birth.get("name"),
        "date": birth.get("date"),
        "time": birth.get("time"),
        "place": birth.get("place"),
        "timezone": birth.get("timezone"),
        "ascendant_sign": asc_sign,
        "moon_sign": moon.get("sign_name"),
        "moon_house": moon.get("house"),
    }


def _conversation_tail(history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    tail = history[-2:] if history else []
    out: List[Dict[str, str]] = []
    for row in tail:
        if not isinstance(row, dict):
            continue
        q = str(row.get("question") or "").strip()
        a = str(row.get("response") or "").strip()
        if not q and not a:
            continue
        out.append({
            "question": q[:300],
            "response": a[:500],
        })
    return out


def reduce_daily_context(
    context: Dict[str, Any],
    *,
    user_question: str,
    conversation_history: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Return a compact, daily-only evidence payload for the LLM."""
    intent = context.get("intent") or {}
    daily_spine = context.get("daily_prediction_spine") or {}
    target_date = (
        daily_spine.get("target_date")
        or intent.get("dasha_as_of")
        or datetime.now().strftime("%Y-%m-%d")
    )

    extracted_context = intent.get("extracted_context") if isinstance(intent.get("extracted_context"), dict) else {}
    micro_intent = classify_daily_micro_intent(
        user_question,
        category=intent.get("category") or "general",
    )
    extracted_micro_intent = extracted_context.get("daily_micro_intent")
    if isinstance(extracted_micro_intent, dict) and extracted_micro_intent.get("name"):
        micro_intent = {
            **micro_intent,
            **extracted_micro_intent,
        }
    fast_planets = build_daily_fast_planets(
        birth_data=context.get("birth_details") or {},
        static_context=context,
        target_date=target_date,
    )
    birth = context.get("birth_details") or {}
    intraday = build_daily_intraday(
        date_str=target_date,
        latitude=float(birth.get("latitude") or 0.0),
        longitude=float(birth.get("longitude") or 0.0),
        timezone=birth.get("timezone"),
    )
    confidence = build_daily_confidence(
        daily_prediction_spine=daily_spine,
        fast_planets=fast_planets,
        intraday=intraday,
        daily_micro_intent=micro_intent,
    )
    output_contract = build_daily_output_contract(
        target_date=target_date,
        daily_prediction_spine=daily_spine,
        daily_micro_intent=micro_intent,
        daily_confidence=confidence,
        intraday=intraday,
    )

    return {
        "method": "daily_context_reducer_v1",
        "target_date": target_date,
        "intent": {
            "mode": intent.get("mode"),
            "category": intent.get("category"),
            "analysis_type": intent.get("analysis_type"),
            "specific_date": extracted_context.get("specific_date") or intent.get("dasha_as_of"),
            "daily_micro_intent": micro_intent,
        },
        "birth_summary": _compact_birth_summary(context),
        "daily_prediction_spine": daily_spine,
        "fast_planets": fast_planets,
        "intraday": intraday,
        "daily_micro_intent": micro_intent,
        "daily_confidence": confidence,
        "daily_output_contract": output_contract,
        "current_dashas": context.get("current_dashas") or {},
        "current_date_info": context.get("current_date_info") or {},
        "conversation_tail": _conversation_tail(conversation_history or []),
        "question": user_question,
        "rules": [
            "Use daily_prediction_spine as the primary evidence source.",
            "Use fast_planets as the practical same-day tone layer, especially for communication, relationships, conflict, and visibility.",
            "Use intraday for morning/afternoon/evening windows, favorable action slots, caution periods, and exact Moon/panchanga shift timings.",
            "Use daily_micro_intent to decide which houses, fast planets, and practical risks matter most for this exact question type.",
            "Use daily_confidence to state whether the day is favorable, mixed, or challenging and whether it is smooth, eventful-but-frictional, or low-manifestation.",
            "Use daily_output_contract as the final answer scaffold so the response stays direct, reusable, and structurally consistent.",
            "Treat PR and SK as the sharpest event triggers, PD as the day frame, and AD/MD as background permission.",
            "Use slow planets only as backdrop unless they directly connect to active daily triggers.",
            "Stay date-specific and practical; avoid lifetime narrative drift.",
        ],
    }
