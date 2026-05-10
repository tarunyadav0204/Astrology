"""
Canonical birth fingerprint (date + time + lat + lon) for policy checks.
Uses normalized coordinates (6 dp) and short time (HH:MM) so clients agree with encrypted chart rows after backfill.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Tuple


def _normalize_date_str(d: Any) -> str:
    s = str(d or "").strip()
    if not s:
        return ""
    if "T" in s:
        s = s.split("T", 1)[0]
    return s


def _normalize_time_str(t: Any) -> str:
    s = str(t or "").strip()
    if not s:
        return ""
    if "T" in s:
        after = s.split("T", 1)[1]
        s = after[:5] if len(after) >= 5 else after
        return s
    # HH:MM:SS -> HH:MM
    if len(s) >= 8 and s[2] == ":" and s[5] == ":":
        s = s[:5]
    return s


def _normalize_coord(v: Any) -> Optional[str]:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return f"{round(x, 6):.6f}"


def normalize_birth_fields_for_hash(
    date_v: Any, time_v: Any, lat_v: Any, lon_v: Any
) -> Optional[Tuple[str, str, str, str]]:
    d = _normalize_date_str(date_v)
    t = _normalize_time_str(time_v)
    lat_s = _normalize_coord(lat_v)
    lon_s = _normalize_coord(lon_v)
    if not d or not t or lat_s is None or lon_s is None:
        return None
    return (d, t, lat_s, lon_s)


def birth_hash_from_parts(date_v: Any, time_v: Any, lat_v: Any, lon_v: Any) -> Optional[str]:
    parts = normalize_birth_fields_for_hash(date_v, time_v, lat_v, lon_v)
    if not parts:
        return None
    d, t, lat_s, lon_s = parts
    birth_string = f"{d}_{t}_{lat_s}_{lon_s}"
    return hashlib.sha256(birth_string.encode("utf-8")).hexdigest()


def birth_hash_from_birth_details_dict(bd: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(bd, dict):
        return None
    return birth_hash_from_parts(
        bd.get("date"),
        bd.get("time"),
        bd.get("latitude"),
        bd.get("longitude"),
    )
