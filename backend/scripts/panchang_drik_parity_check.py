#!/usr/bin/env python3
"""
Panchang parity smoke report for Delhi + a DST city (New York).

Prints our computed values in a form that's easy to compare against Drik / Prokerala
for the same date. Does not scrape third-party sites.

Usage (from backend/):
  .venv/bin/python scripts/panchang_drik_parity_check.py
  .venv/bin/python scripts/panchang_drik_parity_check.py --date 2026-07-13
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from utils.timezone_service import get_timezone_from_coordinates
from calculators.panchang_calculator import PanchangCalculator
from panchang.monthly_panchang_calculator import MonthlyPanchangCalculator


CITIES = [
    {"name": "New Delhi", "lat": 28.6139, "lon": 77.2090, "drik_hint": "https://www.drikpanchang.com/"},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060, "drik_hint": "DST-sensitive; compare summer vs winter dates"},
]


def summarize(date: str, city: dict) -> dict:
    calc = PanchangCalculator()
    monthly = MonthlyPanchangCalculator()
    tz = get_timezone_from_coordinates(city["lat"], city["lon"], for_date=date)
    ss = calc.get_local_sunrise_sunset(date, city["lat"], city["lon"], tz)
    daily = monthly.calculate_daily_panchang(date, city["lat"], city["lon"], tz)
    chog = calc.calculate_choghadiya(date, city["lat"], city["lon"], tz)
    hora = calc.calculate_hora(date, city["lat"], city["lon"], tz)
    bp = daily.get("basic_panchang") or {}
    st = daily.get("special_times") or {}
    ctx = daily.get("day_context") or {}

    return {
        "city": city["name"],
        "date": date,
        "timezone": tz,
        "compare_against": city.get("drik_hint"),
        "sunrise": ss.get("sunrise"),
        "sunset": ss.get("sunset"),
        "moonrise": ss.get("moonrise"),
        "moonset": ss.get("moonset"),
        "brahma": {
            "start": ss.get("brahma_muhurta_start"),
            "end": ss.get("brahma_muhurta_end"),
        },
        "abhijit": {
            "start": ss.get("abhijit_muhurta_start"),
            "end": ss.get("abhijit_muhurta_end"),
        },
        "elements_at_sunrise": {
            "tithi": (bp.get("tithi") or {}).get("name"),
            "tithi_end": (bp.get("tithi") or {}).get("end_time"),
            "nakshatra": (bp.get("nakshatra") or {}).get("name"),
            "nakshatra_end": (bp.get("nakshatra") or {}).get("end_time"),
            "yoga": (bp.get("yoga") or {}).get("name"),
            "karana": (bp.get("karana") or {}).get("name"),
            "vara": (bp.get("vara") or {}).get("name"),
        },
        "rahu_kalam": st.get("rahu_kalam"),
        "dur_muhurtam": st.get("dur_muhurtam"),
        "varjyam": st.get("varjyam"),
        "amrit_kalam": st.get("amrit_kalam"),
        "day_context": ctx,
        "choghadiya_day_first": (chog.get("day_choghadiya") or [None])[0],
        "hora_day_first": (hora.get("day_horas") or [None])[0],
        "checklist": [
            "Sunrise/sunset within ~1–2 min of Drik for this city/date",
            "Moonset on civil date; moonrise may be next morning",
            "Tithi/nakshatra names match; end times within a few minutes",
            "Rahu Kaal weekday eighth matches Drik",
            "Monday Dur Muhurta should be 9th & 12th (8→9 except Wed)",
            "Amrit/Varjyam from daytime nakshatra (not only sunrise star)",
            "First daytime hora lord matches weekday planet",
            "NY: summer offset UTC-4, winter UTC-5",
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-07-13")
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    args = parser.parse_args()

    report = {
        "date": args.date,
        "cities": [summarize(args.date, c) for c in CITIES],
    }

    print(json.dumps(report, indent=2, default=str))
    if args.out:
        out = Path(args.out)
        out.write_text(json.dumps(report, indent=2, default=str))
        print(f"\nWrote {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
