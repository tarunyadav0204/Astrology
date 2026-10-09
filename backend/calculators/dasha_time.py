"""Explicit birth-time parsing shared by date-based dasha systems."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import re


def parse_birth_datetime(birth):
    value = datetime.fromisoformat(f"{birth['date']}T{birth.get('time') or '00:00:00'}")
    tz = birth.get('timezone')
    if tz is None or str(tz).strip() == '':
        return value  # Legacy callers without a timezone retain civil-time semantics.
    label = str(tz).strip()
    try:
        zone = ZoneInfo(label)
    except (KeyError, ValueError):
        label = re.sub(r'^(UTC|GMT)', '', label, flags=re.I) or '0'
        if ':' in label:
            sign = -1 if label.startswith('-') else 1
            hours, minutes = label.lstrip('+-').split(':')
            offset = sign * (float(hours) + float(minutes) / 60)
        else:
            offset = float(label)
        zone = timezone(timedelta(hours=offset))
    return value.replace(tzinfo=zone)


def normalize_focus(focus, birth):
    if focus is None:
        return datetime.now(birth.tzinfo)
    if birth.tzinfo:
        return focus.replace(tzinfo=birth.tzinfo) if focus.tzinfo is None else focus.astimezone(birth.tzinfo)
    if focus.tzinfo is not None:
        raise ValueError('Birth timezone is required for an absolute focus timestamp')
    return focus
