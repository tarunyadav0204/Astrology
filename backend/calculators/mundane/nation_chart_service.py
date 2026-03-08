"""Load national foundation charts and compute Vimshottari Dasha for nations."""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


def _get_nation_charts_path() -> str:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, 'data', 'nation_charts.json')


def get_nation_foundation(country_name: str) -> Optional[Dict[str, Any]]:
    """
    Return foundation date/time/location for a country if available.
    country_name should match keys in nation_charts.json (e.g. 'India', 'USA').
    """
    path = _get_nation_charts_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data.get(country_name)
    except Exception:
        return None


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
