from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore


def normalize_query_context(query_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(query_context, dict):
        return {}
    out: Dict[str, Any] = {}

    timezone_name = (
        query_context.get("timezone_name")
        or query_context.get("query_timezone_name")
        or query_context.get("timeZone")
    )
    if timezone_name:
        out["timezone_name"] = str(timezone_name).strip()

    client_now_iso = (
        query_context.get("client_now_iso")
        or query_context.get("clientNowIso")
        or query_context.get("now_iso")
    )
    if client_now_iso:
        out["client_now_iso"] = str(client_now_iso).strip()

    utc_offset_minutes = (
        query_context.get("utc_offset_minutes")
        if query_context.get("utc_offset_minutes") is not None
        else query_context.get("utcOffsetMinutes")
    )
    if utc_offset_minutes is not None:
        try:
            out["utc_offset_minutes"] = int(float(utc_offset_minutes))
        except (TypeError, ValueError):
            pass

    for src_key, dst_key in (
        ("latitude", "latitude"),
        ("longitude", "longitude"),
        ("query_latitude", "latitude"),
        ("query_longitude", "longitude"),
    ):
        value = query_context.get(src_key)
        if value is None or dst_key in out:
            continue
        try:
            out[dst_key] = float(value)
        except (TypeError, ValueError):
            continue

    return out


def _parse_client_now(value: str) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def resolve_query_now(query_context: Optional[Dict[str, Any]]) -> datetime:
    normalized = normalize_query_context(query_context)
    tz_name = normalized.get("timezone_name")
    tz_obj = None
    if tz_name and ZoneInfo is not None:
        try:
            tz_obj = ZoneInfo(str(tz_name))
        except Exception:
            tz_obj = None

    offset_minutes = normalized.get("utc_offset_minutes")
    offset_tz = None
    if offset_minutes is not None:
        try:
            offset_tz = timezone(timedelta(minutes=int(offset_minutes)))
        except Exception:
            offset_tz = None

    parsed = _parse_client_now(str(normalized.get("client_now_iso") or ""))
    if parsed is not None:
        if parsed.tzinfo is None:
            if tz_obj is not None:
                return parsed.replace(tzinfo=tz_obj)
            if offset_tz is not None:
                return parsed.replace(tzinfo=offset_tz)
            return parsed
        if tz_obj is not None:
            return parsed.astimezone(tz_obj)
        if offset_tz is not None:
            return parsed.astimezone(offset_tz)
        return parsed

    if tz_obj is not None:
        return datetime.now(tz_obj)
    if offset_tz is not None:
        return datetime.now(offset_tz)
    return datetime.now()
