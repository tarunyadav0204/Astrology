"""Compact L/P/H wheel geometry shared by D1, divisional inners, and Jaimini recast charts."""

from __future__ import annotations

from typing import Any, Dict, List

from context_agents.compact_vedic import (
    PLANET_ORDER,
    house_lordships_from_ascendant,
    sign_1_12_from_lon,
    sign_name_from_1_12,
    sign_name_from_index_0,
)


def compact_wheel_chart(inner: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build `L` (lagna), `P` (planet rows), `H` (whole-sign lords from that lagna).
    Expects `inner` with sidereal `ascendant` (0–360°) and `planets` dict like
    ChartCalculator / divisional_chart / Jaimini recast outputs.
    """
    asc_deg = float(inner.get("ascendant", 0.0))
    asc_sign_0 = int(asc_deg / 30.0) % 12
    lagna_sign_1_12 = asc_sign_0 + 1
    lagna_deg_in_sign = asc_deg % 30.0

    planets = inner.get("planets") or {}
    rows: List[List[Any]] = []
    for name in PLANET_ORDER:
        pdata = planets.get(name)
        if not isinstance(pdata, dict):
            continue
        lon = float(pdata.get("longitude", 0.0))
        if pdata.get("sign") is not None:
            s_12 = (int(pdata["sign"]) % 12) + 1
        else:
            s_12 = sign_1_12_from_lon(lon)
        h = int(pdata.get("house", 0) or 0)
        snm = str(pdata.get("sign_name") or "").strip() or sign_name_from_1_12(s_12)
        rows.append([name, round(lon, 4), s_12, snm, h])

    return {
        "L": {
            "s": lagna_sign_1_12,
            "d": round(lagna_deg_in_sign, 4),
            "nm": sign_name_from_index_0(asc_sign_0),
        },
        "P": rows,
        "H": house_lordships_from_ascendant(asc_sign_0),
    }
