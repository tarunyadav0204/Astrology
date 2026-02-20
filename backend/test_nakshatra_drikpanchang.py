#!/usr/bin/env python3
"""
Compare our annual nakshatra timings with Drik Panchang for the same location.

Usage:
  # Use our calculator directly (no server). Compares to embedded DP reference for San Jose.
  python test_nakshatra_drikpanchang.py

  # Or call live API (server must be running). Default base URL: http://localhost:8000
  API_BASE_URL=http://localhost:8000 python test_nakshatra_drikpanchang.py

  # Test Indian location (New Delhi, IST):
  python test_nakshatra_drikpanchang.py --india

  # Or explicitly:
  python test_nakshatra_drikpanchang.py --latitude 28.6139 --longitude 77.2090

Reference: Drik Panchang Revati 2026 (San Jose, CA) was fetched once and embedded
so the test is deterministic. Location differs by timezone; same UTC crossing
gives different local times.

Ayanamsa: Use --ayanamsa-correction <degrees> to shift crossings (positive = earlier).
  --tune finds the best single value for 20 min tolerance; a constant cannot match
  all months if Drik Panchang uses different boundaries or ayanamsa by date.
  Use --tolerance 60 to allow ~1 hour; with 20 min a correction can improve matches.
"""

import os
import re
import sys
from datetime import datetime
from typing import List, Tuple, Optional

# Optional: fetch Drik Panchang page (respects robots.txt: Allow: / for normal User-Agent)
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    requests = None

# --- Embedded Drik Panchang reference: Revati 2026 for San Jose, CA (America/Los_Angeles) ---
# Source: https://www.drikpanchang.com/panchang/nakshatra/daily/revati-nakshatra-date-time.html?year=2026
# Fetched 2026-02; location was San Jose. All timings local (12-hour).
DRIK_PANCHANG_REVATI_2026_SAN_JOSE = [
    ("2026-01-24", "12:46 AM", "2026-01-25", "12:05 AM"),
    ("2026-02-20", "06:37 AM", "2026-02-21", "05:37 AM"),
    ("2026-03-19", "03:35 PM", "2026-03-20", "01:57 PM"),
    ("2026-04-16", "01:29 AM", "2026-04-16", "11:32 PM"),
    ("2026-05-13", "11:47 AM", "2026-05-14", "10:04 AM"),
    ("2026-06-09", "08:51 PM", "2026-06-10", "07:46 PM"),
    ("2026-07-07", "03:54 AM", "2026-07-08", "03:30 AM"),
    ("2026-08-03", "09:30 AM", "2026-08-04", "09:24 AM"),
    ("2026-08-30", "03:14 PM", "2026-08-31", "02:53 PM"),
    ("2026-09-26", "10:38 PM", "2026-09-27", "09:46 PM"),
    ("2026-10-24", "08:02 AM", "2026-10-25", "06:52 AM"),
    ("2026-11-20", "05:20 PM", "2026-11-21", "04:24 PM"),
    ("2026-12-18", "02:40 AM", "2026-12-19", "02:28 AM"),
]

# --- Embedded Drik Panchang reference: Revati 2026 for New Delhi, India (Asia/Kolkata, IST +05:30) ---
# Source: https://www.drikpanchang.com/panchang/nakshatra/daily/revati-nakshatra-date-time.html?year=2026&geoname=Delhi
DRIK_PANCHANG_REVATI_2026_DELHI = [
    ("2026-01-24", "02:16 PM", "2026-01-25", "01:35 PM"),
    ("2026-02-20", "08:07 PM", "2026-02-21", "07:07 PM"),
    ("2026-03-20", "04:05 AM", "2026-03-21", "02:27 AM"),
    ("2026-04-16", "01:59 PM", "2026-04-17", "12:02 PM"),
    ("2026-05-14", "12:17 AM", "2026-05-14", "10:34 PM"),
    ("2026-06-10", "09:21 AM", "2026-06-11", "08:16 AM"),
    ("2026-07-07", "04:24 PM", "2026-07-08", "04:00 PM"),
    ("2026-08-03", "10:00 PM", "2026-08-04", "09:54 PM"),
    ("2026-08-31", "03:44 AM", "2026-09-01", "03:23 AM"),
    ("2026-09-27", "11:08 AM", "2026-09-28", "10:16 AM"),
    ("2026-10-24", "08:32 PM", "2026-10-25", "07:22 PM"),
    ("2026-11-21", "06:50 AM", "2026-11-22", "05:54 AM"),
    ("2026-12-18", "04:10 PM", "2026-12-19", "03:58 PM"),
]

# Default coordinates for embedded references (so we pick the right one)
DELHI_LAT, DELHI_LON = 28.6139, 77.2090
SAN_JOSE_LAT, SAN_JOSE_LON = 37.3352, -121.8811


def _parse_12h_time(s: str) -> Optional[Tuple[int, int]]:
    """Parse '06:37 AM' or '11:32 PM' -> (hour_24, minute). Returns None if invalid."""
    s = s.strip().upper()
    m = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", s)
    if not m:
        return None
    h, mi, ampm = int(m.group(1)), int(m.group(2)), m.group(3)
    if ampm == "PM" and h != 12:
        h += 12
    elif ampm == "AM" and h == 12:
        h = 0
    return (h, mi)


def _time_diff_minutes(start_date: str, start_time: str, end_date: str, end_time: str,
                       ref_start_date: str, ref_start_time: str, ref_end_date: str, ref_end_time: str) -> Tuple[int, int]:
    """Return (abs diff of start in minutes, abs diff of end in minutes)."""
    def to_minutes(date_str: str, time_str: str) -> Optional[int]:
        t = _parse_12h_time(time_str)
        if not t:
            return None
        h, mi = t
        try:
            y, mo, d = map(int, date_str.split("-"))
            return (datetime(y, mo, d, h, mi) - datetime(1970, 1, 1)).total_seconds() / 60
        except Exception:
            return None

    our_start = to_minutes(start_date, start_time)
    our_end = to_minutes(end_date, end_time)
    ref_start = to_minutes(ref_start_date, ref_start_time)
    ref_end = to_minutes(ref_end_date, ref_end_time)
    if None in (our_start, our_end, ref_start, ref_end):
        return (9999, 9999)
    return (int(abs(our_start - ref_start)), int(abs(our_end - ref_end)))


def get_our_revati_periods_2026(
    latitude: float,
    longitude: float,
    ayanamsa_correction_degrees: float = 0.0,
) -> List[dict]:
    """Get Revati periods for 2026 from our calculator (no server)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from calculators.annual_nakshatra_calculator import AnnualNakshatraCalculator
    calc = AnnualNakshatraCalculator()
    data = calc.calculate_annual_nakshatra_periods(
        "Revati", 2026, latitude, longitude, ayanamsa_correction_degrees=ayanamsa_correction_degrees
    )
    out = []
    for p in data["periods"]:
        start_dt = p["start_datetime"]
        end_dt = p["end_datetime"]
        out.append({
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "start_time": p.get("start_time") or start_dt.strftime("%I:%M %p"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "end_time": p.get("end_time") or end_dt.strftime("%I:%M %p"),
        })
    return out


def get_our_revati_periods_via_api(
    base_url: str,
    year: int,
    latitude: float,
    longitude: float,
    ayanamsa_correction: float = 0.0,
) -> List[dict]:
    """Get Revati periods from our API (year endpoint returns all nakshatras by month)."""
    if not requests:
        raise RuntimeError("requests required for API mode")
    url = f"{base_url.rstrip('/')}/api/nakshatra/year/{year}"
    params = {"latitude": latitude, "longitude": longitude}
    if ayanamsa_correction != 0.0:
        params["ayanamsa_correction"] = ayanamsa_correction
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    out = []
    for month_key in sorted(data.get("months", {}), key=int):
        for p in data["months"][month_key]:
            if p.get("nakshatra") == "Revati":
                out.append({
                    "start_date": p["start_date"],
                    "start_time": p.get("start_time", ""),
                    "end_date": p["end_date"],
                    "end_time": p.get("end_time", ""),
                })
    out.sort(key=lambda x: (x["start_date"], x["start_time"]))
    return out


def fetch_drikpanchang_revati_year(year: int) -> Optional[List[Tuple[str, str, str, str]]]:
    """Fetch Drik Panchang Revati page for year and parse Begins/Ends. Location = their default (varies)."""
    if not requests:
        return None
    url = f"https://www.drikpanchang.com/panchang/nakshatra/daily/revati-nakshatra-date-time.html"
    session = requests.Session()
    session.headers.update({
        "User-Agent": "AstrologyApp-NakshatraTest/1.0 (comparison test; respectful crawl)",
        "Accept": "text/html",
        "Accept-Language": "en-US,en;q=0.9",
    })
    retries = Retry(total=2, backoff_factor=1)
    session.mount("https://", HTTPAdapter(max_retries=retries))
    try:
        r = session.get(url, params={"year": year}, timeout=10)
        r.raise_for_status()
        html = r.text
    except Exception as e:
        print(f"  [DP fetch failed: {e}]")
        return None

    # Parse "Begins: HH:MM AM/PM, Mon DD" and "Ends: ..." plus month headers "### Jan 2026"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_num = {m: i + 1 for i, m in enumerate(months)}
    results = []
    for mo_name, mo_idx in month_num.items():
        # Find section for this month
        pat = rf"Begins:\s*(\d{{1,2}}:\d{{2}}\s*[AP]M),\s*{mo_name}\s*(\d{{1,2}})\s*Ends:\s*(\d{{1,2}}:\d{{2}}\s*[AP]M),\s*(?:{mo_name}|(\w+))\s*(\d{{1,2}})"
        for m in re.finditer(pat, html, re.IGNORECASE):
            start_time = m.group(1).strip()
            start_day = int(m.group(2))
            end_time = m.group(3).strip()
            end_month_name = m.group(4) or mo_name
            end_day = int(m.group(5))
            end_mo = month_num.get(end_month_name, mo_idx)
            start_date = f"{year}-{mo_idx:02d}-{start_day:02d}"
            end_date = f"{year}-{end_mo:02d}-{end_day:02d}"
            results.append((start_date, start_time, end_date, end_time))
    return results if results else None


def run_comparison(
    our_periods: List[dict],
    ref_periods: List[Tuple[str, str, str, str]],
    tolerance_minutes: int = 20,
) -> Tuple[int, int, list]:
    """Compare our periods to reference. Returns (matches, total, list of (our, ref, start_diff, end_diff))."""
    matches = 0
    details = []
    for i, ref in enumerate(ref_periods):
        ref_start_date, ref_start_time, ref_end_date, ref_end_time = ref
        if i >= len(our_periods):
            details.append((None, ref, None, None))
            continue
        our = our_periods[i]
        start_diff, end_diff = _time_diff_minutes(
            our["start_date"], our["start_time"], our["end_date"], our["end_time"],
            ref_start_date, ref_start_time, ref_end_date, ref_end_time,
        )
        ok = start_diff <= tolerance_minutes and end_diff <= tolerance_minutes
        if ok:
            matches += 1
        details.append((our, ref, start_diff, end_diff))
    return matches, len(ref_periods), details


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Compare nakshatra timings with Drik Panchang")
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--latitude", type=float, default=37.3352, help="Latitude (ignored if --india)")
    ap.add_argument("--longitude", type=float, default=-121.8811, help="Longitude (ignored if --india)")
    ap.add_argument("--india", action="store_true", help="Use New Delhi, India (28.6139, 77.2090) and Delhi DP reference")
    ap.add_argument("--ayanamsa-correction", type=float, default=0.0, help="Ayanamsa correction in degrees (e.g. -0.2 for Drik Panchang)")
    ap.add_argument("--tune", action="store_true", help="Try correction range and print best value for 20 min tolerance")
    ap.add_argument("--tolerance", type=int, default=20, help="Max minutes diff to count as match")
    ap.add_argument("--api", action="store_true", help="Use live API instead of calculator")
    ap.add_argument("--fetch-dp", action="store_true", help="Fetch Drik Panchang page (location may vary)")
    args = ap.parse_args()
    if args.india:
        args.latitude = DELHI_LAT
        args.longitude = DELHI_LON

    base_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    print("Nakshatra vs Drik Panchang comparison (Revati)")
    print(f"  Year: {args.year}  Location: ({args.latitude}, {args.longitude})  Tolerance: {args.tolerance} min")
    if args.ayanamsa_correction != 0.0:
        print(f"  Ayanamsa correction: {args.ayanamsa_correction:+.3f}°")
    print()

    def get_our_periods(correction: float = 0.0) -> List[dict]:
        if args.api and requests:
            try:
                return get_our_revati_periods_via_api(
                    base_url, args.year, args.latitude, args.longitude, ayanamsa_correction=correction
                )
            except Exception:
                return get_our_revati_periods_2026(args.latitude, args.longitude, correction)
        return get_our_revati_periods_2026(args.latitude, args.longitude, correction)

    # Tune: find best ayanamsa correction for 20 min tolerance
    if args.tune:
        ref_periods = DRIK_PANCHANG_REVATI_2026_DELHI if (args.india or (abs(args.latitude - DELHI_LAT) < 0.01 and abs(args.longitude - DELHI_LON) < 0.01)) else DRIK_PANCHANG_REVATI_2026_SAN_JOSE
        if args.year != 2026:
            print("  --tune uses embedded 2026 reference; use --year 2026 for meaningful result.")
        best_corr = 0.0
        best_matches = 0
        tol = 20
        for corr in [round(x * 0.05, 2) for x in range(-20, 21)]:  # -1.0 to +1.0 in 0.05 steps
            our_p = get_our_periods(corr)
            m, t, _ = run_comparison(our_p, ref_periods, tol)
            if m > best_matches:
                best_matches = m
                best_corr = corr
        print(f"  Best ayanamsa correction (20 min tolerance): {best_corr:+.2f}°  =>  {best_matches}/{len(ref_periods)} matches")
        if best_matches == len(ref_periods):
            print(f"  Use: --ayanamsa-correction {best_corr:+.2f}")
        return 0

    # Get our periods
    our_periods = get_our_periods(args.ayanamsa_correction)
    if args.api and requests:
        print("  Source: API @ " + base_url)
    else:
        print("  Source: AnnualNakshatraCalculator (no server)")
    print(f"  Our Revati periods: {len(our_periods)}")
    print()

    # Reference: embedded (San Jose) or fetched DP
    if args.fetch_dp and requests:
        ref_periods = fetch_drikpanchang_revati_year(args.year)
        if ref_periods:
            print(f"  Reference: Drik Panchang (fetched); count = {len(ref_periods)}")
        else:
            ref_periods = None
    else:
        ref_periods = None

    if not ref_periods:
        if args.year == 2026:
            if abs(args.latitude - DELHI_LAT) < 0.01 and abs(args.longitude - DELHI_LON) < 0.01:
                ref_periods = DRIK_PANCHANG_REVATI_2026_DELHI
                print("  Reference: embedded Drik Panchang (New Delhi, India, 2026)")
            elif abs(args.latitude - SAN_JOSE_LAT) < 0.01 and abs(args.longitude - SAN_JOSE_LON) < 0.01:
                ref_periods = DRIK_PANCHANG_REVATI_2026_SAN_JOSE
                print("  Reference: embedded Drik Panchang (San Jose, 2026)")
            else:
                print("  No embedded reference for this location. Use --india (Delhi) or --latitude 37.3352 --longitude -121.8811 (San Jose) for 2026.")
                return 0
        else:
            print("  No embedded reference for this year. Use --year 2026 with --india or San Jose coords.")
            return 0

    matches, total, details = run_comparison(our_periods, ref_periods, args.tolerance)
    print()
    print("Comparison (our start/end vs reference start/end):")
    print("-" * 80)
    for i, (our, ref, start_diff, end_diff) in enumerate(details):
        if ref is None:
            continue
        ref_sd, ref_st, ref_ed, ref_et = ref
        status = "OK" if (start_diff is not None and start_diff <= args.tolerance and end_diff is not None and end_diff <= args.tolerance) else "DIFF"
        our_str = f"{our['start_date']} {our['start_time']} -> {our['end_date']} {our['end_time']}" if our else "—"
        ref_str = f"{ref_sd} {ref_st} -> {ref_ed} {ref_et}"
        diff_str = f"  (start ±{start_diff} min, end ±{end_diff} min)" if start_diff is not None else ""
        print(f"  [{status}] #{i+1}  Our: {our_str}")
        print(f"         Ref:  {ref_str}{diff_str}")
    print("-" * 80)
    print(f"  Result: {matches}/{total} periods within {args.tolerance} minutes")
    if matches == total and total > 0:
        print("  => All match Drik Panchang within tolerance.")
        return 0
    elif total > 0:
        print("  => Some differences (check ayanamsa / timezone / boundary method).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
