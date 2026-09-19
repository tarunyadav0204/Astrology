"""Guided-question service for the versioned classical Prashna engine."""
from __future__ import annotations

from datetime import datetime, timezone as datetime_timezone, timedelta
import math
import re
from types import SimpleNamespace
from typing import Any, Dict

import pytz

from calculators.prashna_classical_chart import ClassicalPrashnaChartCalculator, SIGN_NAMES
from calculators.prashna_v2_calculator import PrashnaV2Calculator
from prashna.presenter import build_presentation
from prashna.question_interpreter import resolve_guided_question
from prashna.source_ledger import public_ledger
from utils.timezone_service import get_iana_timezone


RESULTS = {"favorable", "unfavorable", "mixed", "cannot_judge"}
PROFILE_ID = "hayanaratna_textual_precession_quadrant_v1"


def _validate_analysis_contract(analysis: Dict[str, Any]) -> None:
    missing = []
    if (analysis.get("verdict") or {}).get("result") not in RESULTS:
        missing.append("verdict.result")
    for key in ("heading", "summary", "decision_guidance", "tradition_label", "limits"):
        if not str((analysis.get("presentation") or {}).get(key) or "").strip():
            missing.append(f"presentation.{key}")
    for key in ("supporting_points", "blocking_points"):
        if not isinstance((analysis.get("presentation") or {}).get(key), list):
            missing.append(f"presentation.{key}")
    if (analysis.get("question") or {}).get("status") != "selected":
        missing.append("question.status")
    classical = analysis.get("classical") or {}
    for key in ("roles", "rules", "yogas", "contacts"):
        if not isinstance(classical.get(key), list):
            missing.append(f"classical.{key}")
    calculation = analysis.get("calculation") or {}
    if calculation.get("profile_id") != PROFILE_ID:
        missing.append("calculation.profile_id")
    if missing:
        raise RuntimeError("Incomplete Prashna result contract: " + ", ".join(missing))


def _question_clock(*, date: str, time: str, latitude: float, longitude: float,
                    timezone: str = "", place: str = "", name: str = "Prashna") -> SimpleNamespace:
    if not all(math.isfinite(float(v)) for v in (latitude, longitude)) or not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid question coordinates")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or not re.fullmatch(r"\d{2}:\d{2}(:\d{2})?", time):
        raise ValueError("Use YYYY-MM-DD and HH:MM[:SS] for the question clock")
    try:
        local = datetime.fromisoformat(f"{date}T{time}")
    except ValueError as exc:
        raise ValueError("The question date or time is invalid") from exc
    zone = timezone.strip() if timezone else get_iana_timezone(latitude, longitude)
    zone = {"Asia/Calcutta": "Asia/Kolkata"}.get(zone, zone)
    match = re.fullmatch(r"UTC([+-])(\d{1,2})(?::(\d{2}))?", zone)
    if zone == "UTC":
        aware = local.replace(tzinfo=datetime_timezone.utc)
    elif match:
        hours, minutes = int(match[2]), int(match[3] or 0)
        if minutes >= 60 or hours > 14 or (hours == 14 and minutes):
            raise ValueError("Invalid UTC offset")
        offset = (hours * 60 + minutes) * (1 if match[1] == "+" else -1)
        aware = local.replace(tzinfo=datetime_timezone(timedelta(minutes=offset)))
    else:
        try:
            aware = pytz.timezone(zone).localize(local, is_dst=None)
        except pytz.AmbiguousTimeError as exc:
            raise ValueError("This clock occurs twice during DST; supply an explicit UTC offset") from exc
        except pytz.NonExistentTimeError as exc:
            raise ValueError("This local clock does not exist during the DST transition") from exc
        except pytz.UnknownTimeZoneError as exc:
            raise ValueError("Unknown timezone; use an IANA name or UTC offset") from exc
    return SimpleNamespace(utc_datetime=aware.astimezone(datetime_timezone.utc), name=name or "Prashna",
        date=date, time=time, latitude=float(latitude), longitude=float(longitude), timezone=zone,
        place=place or "", gender="", relation="prashna")


def analyze_prashna(*, question_id: str, date: str, time: str, latitude: float,
                    longitude: float, timezone: str = "", place: str = "",
                    name: str = "Prashna") -> Dict[str, Any]:
    interpretation = resolve_guided_question(question_id)
    clock = _question_clock(date=date, time=time, latitude=latitude, longitude=longitude,
                            timezone=timezone, place=place, name=name)
    chart = ClassicalPrashnaChartCalculator().calculate_chart(clock)
    classical = PrashnaV2Calculator(chart).calculate(interpretation["topic"], interpretation["intent"])
    presentation = build_presentation(classical)
    result = {
        "verdict": {"result": classical["result"]},
        "presentation": presentation,
        "question": {**interpretation, "selected_at": clock.utc_datetime.isoformat()},
        "classical": classical,
        "calculation": chart["calculation"],
        "clock": {"utc": clock.utc_datetime.isoformat(), "date": clock.date, "time": clock.time,
                  "timezone": clock.timezone, "latitude": clock.latitude, "longitude": clock.longitude,
                  "place": clock.place, "source": "guided_question_selection",
                  "note": "The chart was fixed when the selected guided question was cast."},
        "chart_snapshot": {"ascendant": {"longitude": chart["ascendant"],
                            "sign_name": SIGN_NAMES[int(chart["ascendant"] // 30)],
                            "degree": chart["ascendant"] % 30},
                           "planets": chart["planets"], "houses": chart["houses"]},
        "source_ledger": public_ledger(),
        "chat_evidence": {"kind": "prashna_v2", "ruleset_version": classical["ruleset_version"],
                          "result": classical["result"], "presentation": presentation,
                          "matched_rule_ids": [r["id"] for r in classical["rules"] if r["matched"]]},
    }
    _validate_analysis_contract(result)
    return result
