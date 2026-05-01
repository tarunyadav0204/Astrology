from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from calculators.panchang_calculator import PanchangCalculator
from calculators.real_transit_calculator import RealTransitCalculator
from panchang.monthly_panchang_calculator import MonthlyPanchangCalculator
from utils.timezone_service import parse_timezone_offset
import swisseph as swe

TITHI_BASE_NAMES = (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
    "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
)
YOGA_NAMES = (
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti",
    "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi",
    "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
    "Brahma", "Indra", "Vaidhriti",
)
KARANA_MOVABLE = ("Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti")
SIGN_NAMES = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _human_window(start: Optional[str], end: Optional[str], label: str, source: str, quality: str) -> Optional[Dict[str, Any]]:
    sdt = _parse_iso(start)
    edt = _parse_iso(end)
    if not sdt or not edt:
        return None
    return {
        "label": label,
        "source": source,
        "quality": quality,
        "start": sdt.isoformat(),
        "end": edt.isoformat(),
    }


def _human_ampm_window(start_label: Optional[str], end_label: Optional[str], *, date_str: str, label: str, source: str, quality: str) -> Optional[Dict[str, Any]]:
    if not start_label or not end_label:
        return None
    try:
        sdt = datetime.strptime(f"{date_str} {start_label}", "%Y-%m-%d %I:%M %p")
        edt = datetime.strptime(f"{date_str} {end_label}", "%Y-%m-%d %I:%M %p")
    except Exception:
        return None
    return {
        "label": label,
        "source": source,
        "quality": quality,
        "start": sdt.isoformat(),
        "end": edt.isoformat(),
    }


def _segment_block(name: str, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> Optional[Dict[str, Any]]:
    if not start_dt or not end_dt:
        return None
    return {
        "segment": name,
        "start": start_dt.isoformat(),
        "end": end_dt.isoformat(),
    }


def _local_to_jd(local_dt: datetime, tz_offset_hours: float) -> float:
    utc_dt = local_dt - timedelta(hours=tz_offset_hours)
    utc_hour = utc_dt.hour + (utc_dt.minute / 60.0) + (utc_dt.second / 3600.0)
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_hour)


def _format_utc_offset(offset_hours: float) -> str:
    sign = "+" if offset_hours >= 0 else "-"
    absolute = abs(float(offset_hours))
    hours = int(absolute)
    minutes = int(round((absolute - hours) * 60))
    if minutes >= 60:
        hours += 1
        minutes -= 60
    return f"UTC{sign}{hours}" if minutes == 0 else f"UTC{sign}{hours}:{minutes:02d}"


def _normalize_timezone(timezone: Optional[str], latitude: float, longitude: float) -> str:
    """Preserve caller timezone; derive a UTC offset only when missing."""
    if timezone and str(timezone).strip():
        return str(timezone).strip()
    return _format_utc_offset(parse_timezone_offset("", latitude, longitude))


def _jd_to_local_dt(jd: float, tz_offset_hours: float) -> datetime:
    year, month, day, hour_fraction = swe.revjul(jd, swe.GREG_CAL)
    hour = int(hour_fraction)
    minute_fraction = (hour_fraction - hour) * 60.0
    minute = int(minute_fraction)
    second = int(round((minute_fraction - minute) * 60.0))
    if second >= 60:
        second -= 60
        minute += 1
    if minute >= 60:
        minute -= 60
        hour += 1
    base_dt = datetime(int(year), int(month), int(day), 0, 0, 0) + timedelta(
        hours=hour,
        minutes=minute,
        seconds=second,
    )
    return base_dt + timedelta(hours=tz_offset_hours)


def _moon_metrics(jd: float, rtc: RealTransitCalculator) -> Dict[str, Any]:
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    nk = rtc.get_nakshatra_from_longitude(moon_lon)
    sign_num = int(moon_lon / 30) % 12
    return {
        "longitude": moon_lon,
        "sign_num": sign_num + 1,
        "sign_name": SIGN_NAMES[sign_num],
        "nakshatra_num": int(nk.get("index", 0)) + 1,
        "nakshatra_name": nk.get("name"),
        "pada": nk.get("pada"),
    }


def _tithi_num(jd: float) -> int:
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    elongation = (moon_lon - sun_lon) % 360
    return int(elongation / 12) + 1


def _yoga_num(jd: float) -> int:
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    return int(((sun_lon + moon_lon) % 360) / 13.333333) + 1


def _karana_num(jd: float) -> int:
    sun_lon = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_lon = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    tithi_deg = (moon_lon - sun_lon) % 360
    return int(tithi_deg / 6) + 1


def _tithi_name(tithi_num: int) -> str:
    if tithi_num == 15:
        return "Purnima"
    if tithi_num == 30:
        return "Amavasya"
    return TITHI_BASE_NAMES[(tithi_num - 1) % 15]


def _yoga_name(yoga_num: int) -> str:
    return YOGA_NAMES[(yoga_num - 1) % 27]


def _karana_name(karana_num: int) -> str:
    if karana_num == 1:
        return "Kimstughna"
    if karana_num >= 58:
        fixed_map = {58: "Shakuni", 59: "Chatushpada", 60: "Naga"}
        return fixed_map.get(karana_num, "Naga")
    return KARANA_MOVABLE[(karana_num - 2) % 7]


def _find_transition_time(
    start_jd: float,
    end_jd: float,
    start_value: Any,
    value_at,
):
    left = start_jd
    right = end_jd
    for _ in range(30):
        mid = (left + right) / 2.0
        mid_value = value_at(mid)
        if mid_value == start_value:
            left = mid
        else:
            right = mid
    return right


def _scan_local_day_transitions(date_str: str, tz_offset_hours: float) -> Dict[str, List[Dict[str, Any]]]:
    day_start = datetime.strptime(date_str, "%Y-%m-%d")
    start_jd = _local_to_jd(day_start, tz_offset_hours)
    end_jd = _local_to_jd(day_start.replace(hour=23, minute=59, second=59), tz_offset_hours)
    step_minutes = 30
    rtc = RealTransitCalculator()

    transitions: Dict[str, List[Dict[str, Any]]] = {
        "moon_sign": [],
        "moon_nakshatra": [],
        "tithi": [],
        "yoga": [],
        "karana": [],
    }

    value_funcs = {
        "moon_sign": lambda jd: _moon_metrics(jd, rtc)["sign_num"],
        "moon_nakshatra": lambda jd: _moon_metrics(jd, rtc)["nakshatra_num"],
        "tithi": _tithi_num,
        "yoga": _yoga_num,
        "karana": _karana_num,
    }

    current_values = {key: fn(start_jd) for key, fn in value_funcs.items()}
    current_jd = start_jd
    while current_jd < end_jd:
        next_jd = min(end_jd, current_jd + (step_minutes / 1440.0))
        for key, fn in value_funcs.items():
            next_value = fn(next_jd)
            if next_value != current_values[key]:
                transition_jd = _find_transition_time(current_jd, next_jd, current_values[key], fn)
                transition_local = _jd_to_local_dt(transition_jd, tz_offset_hours)
                record: Dict[str, Any] = {
                    "from": current_values[key],
                    "to": next_value,
                    "at": transition_local.isoformat(),
                    "time_label": transition_local.strftime("%I:%M %p").lstrip("0"),
                }
                if key == "moon_sign":
                    from_info = _moon_metrics(current_jd, rtc)
                    to_info = _moon_metrics(next_jd, rtc)
                    record["from_name"] = from_info["sign_name"]
                    record["to_name"] = to_info["sign_name"]
                    record["label"] = f"Moon sign changes from {record['from_name']} to {record['to_name']}"
                elif key == "moon_nakshatra":
                    from_info = _moon_metrics(current_jd, rtc)
                    to_info = _moon_metrics(next_jd, rtc)
                    record["from_name"] = from_info["nakshatra_name"]
                    record["to_name"] = to_info["nakshatra_name"]
                    record["label"] = f"Moon nakshatra changes from {record['from_name']} to {record['to_name']}"
                elif key == "tithi":
                    record["from_name"] = _tithi_name(int(current_values[key]))
                    record["to_name"] = _tithi_name(int(next_value))
                    record["label"] = f"Tithi changes from {record['from_name']} to {record['to_name']}"
                elif key == "yoga":
                    record["from_name"] = _yoga_name(int(current_values[key]))
                    record["to_name"] = _yoga_name(int(next_value))
                    record["label"] = f"Yoga changes from {record['from_name']} to {record['to_name']}"
                elif key == "karana":
                    record["from_name"] = _karana_name(int(current_values[key]))
                    record["to_name"] = _karana_name(int(next_value))
                    record["label"] = f"Karana changes from {record['from_name']} to {record['to_name']}"
                transitions[key].append(record)
                current_values[key] = next_value
        current_jd = next_jd
    return transitions


def _flatten_transitions(transitions: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for kind, items in transitions.items():
        for item in items or []:
            rows.append({
                "kind": kind,
                "label": item.get("label"),
                "time_label": item.get("time_label"),
                "at": item.get("at"),
                "from_name": item.get("from_name"),
                "to_name": item.get("to_name"),
            })
    rows.sort(key=lambda row: str(row.get("at") or ""))
    return rows


def _top_good_horas(horas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    preferred = {"Mercury", "Venus", "Jupiter", "Moon", "Sun"}
    rows: List[Dict[str, Any]] = []
    for row in horas:
        planet = row.get("planet")
        if planet not in preferred:
            continue
        rows.append({
            "label": f"{planet} hora",
            "planet": planet,
            "start": row.get("start_time"),
            "end": row.get("end_time"),
            "quality": "supportive",
            "source": "hora",
        })
    return rows[:4]


def _top_caution_horas(horas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    caution = {"Mars", "Saturn"}
    rows: List[Dict[str, Any]] = []
    for row in horas:
        planet = row.get("planet")
        if planet not in caution:
            continue
        rows.append({
            "label": f"{planet} hora",
            "planet": planet,
            "start": row.get("start_time"),
            "end": row.get("end_time"),
            "quality": "caution",
            "source": "hora",
        })
    return rows[:3]


def build_daily_intraday(
    *,
    date_str: str,
    latitude: float,
    longitude: float,
    timezone: Optional[str],
) -> Dict[str, Any]:
    """Deterministic intraday timing layer for daily answers."""
    safe_timezone = _normalize_timezone(timezone, latitude, longitude)
    monthly = MonthlyPanchangCalculator()
    detailed = monthly.calculate_daily_panchang(date_str, latitude, longitude, safe_timezone)
    base = PanchangCalculator()
    hora = base.calculate_hora(date_str, latitude, longitude, safe_timezone)
    choghadiya = base.calculate_choghadiya(date_str, latitude, longitude, safe_timezone)
    tz_offset_hours = parse_timezone_offset(safe_timezone, latitude, longitude)
    transitions = _scan_local_day_transitions(date_str, tz_offset_hours)

    sunrise_sunset = detailed.get("sunrise_sunset") or {}
    special = detailed.get("special_times") or {}

    sunrise = _parse_iso(sunrise_sunset.get("sunrise"))
    sunset = _parse_iso(sunrise_sunset.get("sunset"))
    moonrise = _parse_iso(sunrise_sunset.get("moonrise"))
    moonset = _parse_iso(sunrise_sunset.get("moonset"))

    day_horas = hora.get("day_horas") or []
    night_horas = hora.get("night_horas") or []
    all_horas = list(day_horas) + list(night_horas)

    day_duration_hours = float(sunrise_sunset.get("day_duration") or 0.0)
    morning = _segment_block("morning", sunrise, sunrise + (sunset - sunrise) / 3) if sunrise and sunset else None
    afternoon = _segment_block("afternoon", sunrise + (sunset - sunrise) / 3, sunrise + ((sunset - sunrise) * 2 / 3)) if sunrise and sunset else None
    evening = _segment_block("evening", sunrise + ((sunset - sunrise) * 2 / 3), sunset) if sunrise and sunset else None

    favorable_windows: List[Dict[str, Any]] = []
    caution_windows: List[Dict[str, Any]] = []

    for key, label in (
        ("brahma_muhurta", "Brahma Muhurta"),
        ("abhijit", "Abhijit Muhurta"),
    ):
        row = special.get(key) or {}
        win = _human_ampm_window(row.get("start"), row.get("end"), date_str=date_str, label=label, source="special_times", quality="supportive")
        if win:
            favorable_windows.append(win)

    amrit_rows = special.get("amrit_kalam") or []
    for idx, row in enumerate(amrit_rows, start=1):
        win = _human_ampm_window(row.get("start"), row.get("end"), date_str=date_str, label=f"Amrit Kalam {idx}", source="special_times", quality="supportive")
        if win:
            favorable_windows.append(win)

    for key, label in (
        ("rahu_kalam", "Rahu Kalam"),
        ("gulikai_kalam", "Gulikai Kalam"),
        ("yamaganda", "Yamaganda"),
        ("varjyam", "Varjyam"),
    ):
        row = special.get(key) or {}
        win = _human_ampm_window(row.get("start"), row.get("end"), date_str=date_str, label=label, source="special_times", quality="caution")
        if win:
            caution_windows.append(win)

    for idx, row in enumerate(special.get("dur_muhurtam") or [], start=1):
        win = _human_ampm_window(row.get("start"), row.get("end"), date_str=date_str, label=f"Dur Muhurtam {idx}", source="special_times", quality="caution")
        if win:
            caution_windows.append(win)

    for row in transitions.get("moon_sign") or []:
        caution_windows.append({
            "label": f"Moon sign shift: {row.get('from_name')} to {row.get('to_name')}",
            "source": "moon_transition",
            "quality": "transition",
            "start": row.get("at"),
            "end": row.get("at"),
        })
    for row in transitions.get("moon_nakshatra") or []:
        caution_windows.append({
            "label": f"Moon nakshatra shift: {row.get('from_name')} to {row.get('to_name')}",
            "source": "moon_transition",
            "quality": "transition",
            "start": row.get("at"),
            "end": row.get("at"),
        })

    favorable_windows.extend(_top_good_horas(day_horas))
    caution_windows.extend(_top_caution_horas(day_horas))

    top_day_choghadiya = [row for row in (choghadiya.get("day_choghadiya") or []) if row.get("quality") in {"Best", "Good", "Gain"}][:3]
    top_night_choghadiya = [row for row in (choghadiya.get("night_choghadiya") or []) if row.get("quality") in {"Best", "Good", "Gain"}][:2]
    weak_choghadiya = [row for row in (choghadiya.get("day_choghadiya") or []) if row.get("quality") in {"Bad", "Loss", "Evil"}][:3]
    transition_windows = _flatten_transitions(transitions)

    return {
        "method": "daily_intraday_v1",
        "target_date": date_str,
        "sunrise_sunset": {
            "sunrise": sunrise.isoformat() if sunrise else None,
            "sunset": sunset.isoformat() if sunset else None,
            "moonrise": moonrise.isoformat() if moonrise else None,
            "moonset": moonset.isoformat() if moonset else None,
            "day_duration_hours": sunrise_sunset.get("day_duration"),
            "night_duration_hours": sunrise_sunset.get("night_duration"),
            "moon_phase": sunrise_sunset.get("moon_phase"),
            "moon_illumination": sunrise_sunset.get("moon_illumination"),
        },
        "segments": [seg for seg in (morning, afternoon, evening) if seg],
        "favorable_windows": favorable_windows[:8],
        "caution_windows": caution_windows[:8],
        "hora": {
            "day_horas": day_horas[:12],
            "night_horas": night_horas[:12],
            "supportive_examples": _top_good_horas(all_horas)[:4],
            "caution_examples": _top_caution_horas(all_horas)[:4],
        },
        "choghadiya": {
            "day_supportive": top_day_choghadiya,
            "night_supportive": top_night_choghadiya,
            "day_caution": weak_choghadiya,
        },
        "transitions": transitions,
        "transition_windows": transition_windows,
        "notes": [
            "Intraday windows are deterministic and based on sunrise/sunset, special kalas, hora, and choghadiya.",
            "Transition markers show where the Moon or a panchanga element changes inside the local day.",
            "These windows are practical timing aids and should be read together with the daily event triggers.",
        ],
    }
