"""Load national foundation charts and compute Vimshottari Dasha for nations."""

import json
import os
from typing import Dict, Any, Optional


def _get_nation_charts_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'data', 'nation_charts.json')


def _load_nation_charts_raw() -> Dict[str, Any]:
    path = _get_nation_charts_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def resolve_nation_chart_key(label: str, data: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Return the canonical key in nation_charts.json for a user-facing label, or None.
    Matches case-insensitively on JSON keys (e.g. 'usa' -> 'USA', 'iran' -> 'Iran').
    Pass `data` from a single load to avoid reading the file twice.
    """
    label = (label or "").strip()
    if not label:
        return None
    if data is None:
        data = _load_nation_charts_raw()
    if not data:
        return None
    if label in data:
        return label
    ll = label.lower()
    for k in data:
        if k.lower() == ll:
            return k
    return None


def get_nation_foundation(country_name: str) -> Optional[Dict[str, Any]]:
    """
    Return foundation date/time/location for a country if available.
    country_name should match keys in nation_charts.json (e.g. 'India', 'USA'); casing is normalized.
    """
    data = _load_nation_charts_raw()
    key = resolve_nation_chart_key(country_name, data)
    if not key:
        return None
    return data.get(key)


def get_nation_birth_dict_for_dasha(country_name: str) -> Optional[Dict[str, Any]]:
    """
    Return a birth_data dict suitable for DashaCalculator.calculate_current_dashas.
    Keys: date, time, timezone, latitude, longitude.
    """
    rec = get_nation_foundation(country_name)
    if not rec:
        return None
    time_str = rec.get('time', '00:00:00')
    if len(time_str.split(':')) == 2:
        time_str = time_str + ':00'
    return {
        'date': rec['date'],
        'time': time_str,
        'timezone': float(rec.get('timezone', 0)),
        'latitude': float(rec['lat']),
        'longitude': float(rec['lon']),
    }
