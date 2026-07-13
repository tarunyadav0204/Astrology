"""
Professional timezone detection service using coordinates.
Returns UTC offset format for astrology calculations.
Offsets are computed for the requested date (DST-safe).
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

try:
    from timezonefinder import TimezoneFinder
    import pytz
    HAS_TIMEZONE_LIBS = True
except ImportError:
    HAS_TIMEZONE_LIBS = False

# Cache IANA names by rounded coordinates (offset itself is date-dependent).
_iana_cache = {}
# Backward-compatible alias for older tests/imports.
_timezone_cache = _iana_cache
_timezone_finder = None


def _get_timezone_finder():
    global _timezone_finder
    if _timezone_finder is None:
        _timezone_finder = TimezoneFinder()
    return _timezone_finder


def _coerce_date(for_date: Optional[Union[str, date, datetime]]) -> Optional[date]:
    if for_date is None:
        return None
    if isinstance(for_date, datetime):
        return for_date.date()
    if isinstance(for_date, date):
        return for_date
    text = str(for_date).strip()
    if "T" in text:
        text = text.split("T", 1)[0]
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        return None


def get_iana_timezone(lat: float, lon: float) -> str:
    if not HAS_TIMEZONE_LIBS:
        raise ImportError("Required libraries not installed: pip install timezonefinder pytz")

    cache_key = (round(lat, 2), round(lon, 2))
    if cache_key in _iana_cache:
        return _iana_cache[cache_key]

    tf = _get_timezone_finder()
    iana_timezone = tf.timezone_at(lat=lat, lng=lon)
    if not iana_timezone:
        raise ValueError(f"No timezone found for coordinates ({lat}, {lon})")

    _iana_cache[cache_key] = iana_timezone
    return iana_timezone


def format_utc_offset(offset_hours: float) -> str:
    hours = int(abs(offset_hours))
    minutes = int(round((abs(offset_hours) - hours) * 60))
    if minutes == 60:
        hours += 1
        minutes = 0
    sign = "+" if offset_hours >= 0 else "-"
    if minutes == 0:
        return f"UTC{sign}{hours}"
    return f"UTC{sign}{hours}:{minutes:02d}"


def get_utc_offset_hours(
    lat: float,
    lon: float,
    for_date: Optional[Union[str, date, datetime]] = None,
) -> float:
    """
    Return UTC offset in hours for coordinates on a specific civil date (noon local).
    Falls back to "now" when for_date is omitted.
    """
    if not HAS_TIMEZONE_LIBS:
        raise ImportError("Required libraries not installed: pip install timezonefinder pytz")

    iana_timezone = get_iana_timezone(lat, lon)
    tz = pytz.timezone(iana_timezone)
    target = _coerce_date(for_date)
    if target is None:
        aware = datetime.now(tz)
    else:
        naive = datetime(target.year, target.month, target.day, 12, 0, 0)
        aware = tz.localize(naive)
    return aware.utcoffset().total_seconds() / 3600.0


def get_timezone_from_coordinates(
    lat: float,
    lon: float,
    for_date: Optional[Union[str, date, datetime]] = None,
) -> str:
    """
    Professional timezone detection from coordinates using timezonefinder + pytz.

    Args:
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        for_date: Optional YYYY-MM-DD / date / datetime for DST-correct offset

    Returns:
        str: UTC offset format (e.g., 'UTC+5:30', 'UTC-8:00')
    """
    return format_utc_offset(get_utc_offset_hours(lat, lon, for_date=for_date))


def parse_timezone_offset(
    timezone_str,
    latitude: float = None,
    longitude: float = None,
    for_date: Optional[Union[str, date, datetime]] = None,
) -> float:
    """
    Parse timezone string to UTC offset in hours (as float).
    Uses coordinate-based detection if timezone_str is empty or invalid.
    When for_date is provided, DST is evaluated for that civil date.
    """
    if isinstance(timezone_str, (int, float)):
        return float(timezone_str)

    if timezone_str is None:
        timezone_str = ""

    timezone_str = str(timezone_str)

    try:
        return float(timezone_str)
    except (ValueError, TypeError):
        pass

    if (
        not timezone_str
        or timezone_str in ["UTC", "UTC+0", "UTC-0", "UTC0"]
        or timezone_str.strip() == ""
    ):
        if latitude is not None and longitude is not None:
            try:
                return get_utc_offset_hours(latitude, longitude, for_date=for_date)
            except Exception as e:
                print(f"⚠️ TIMEZONE: Failed to detect from coordinates: {e}")
                return 0.0
        return 0.0

    if timezone_str.startswith("UTC"):
        tz_str = timezone_str[3:]
        if tz_str:
            if ":" in tz_str:
                sign = 1 if tz_str[0] == "+" else -1
                parts = tz_str[1:].split(":")
                return sign * (float(parts[0]) + float(parts[1]) / 60)
            return float(tz_str)

    # IANA name support (date-aware when possible)
    if HAS_TIMEZONE_LIBS:
        try:
            tz = pytz.timezone(timezone_str)
            target = _coerce_date(for_date)
            if target is None:
                aware = datetime.now(tz)
            else:
                aware = tz.localize(datetime(target.year, target.month, target.day, 12, 0, 0))
            return aware.utcoffset().total_seconds() / 3600.0
        except Exception:
            pass

    return 0.0
