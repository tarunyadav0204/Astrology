"""
Find upcoming Vimshottari MD / AD / PD start times for nudge scheduling.
Uses shared.DashaCalculator (same engine as the rest of the app).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from shared.dasha_calculator import DashaCalculator


def _scan_dt(target_date: date) -> datetime:
    return datetime(target_date.year, target_date.month, target_date.day, 12, 0, 0)


def _parse_iso_dt(s: str) -> datetime:
    s = str(s).strip()
    if len(s) >= 19 and "T" in s:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    parts = s[:10].split("-")
    y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
    return datetime(y, m, d, 12, 0, 0)


def _iter_antardashas(calc: DashaCalculator, maha: Dict[str, Any]) -> List[Dict[str, Any]]:
    maha_planet = maha["planet"]
    maha_start, maha_end = maha["start"], maha["end"]
    start_index = calc.PLANET_ORDER.index(maha_planet)
    current = maha_start
    out: List[Dict[str, Any]] = []
    for i in range(9):
        antar_planet = calc.PLANET_ORDER[(start_index + i) % 9]
        antar_period = (
            calc.DASHA_PERIODS[maha_planet] * calc.DASHA_PERIODS[antar_planet]
        ) / 120
        antar_days = antar_period * 365.242199
        antar_end = current + timedelta(days=antar_days)
        out.append(
            {
                "planet": antar_planet,
                "start": current,
                "end": antar_end,
            }
        )
        current = antar_end
    return out


def _iter_pratyantardashas(
    calc: DashaCalculator, maha: Dict[str, Any], antar: Dict[str, Any]
) -> List[Dict[str, Any]]:
    maha_planet = maha["planet"]
    antar_planet = antar["planet"]
    antar_start, antar_end = antar["start"], antar["end"]
    start_index = calc.PLANET_ORDER.index(antar_planet)
    current = antar_start
    antar_period = (
        calc.DASHA_PERIODS[maha_planet] * calc.DASHA_PERIODS[antar_planet]
    ) / 120
    out: List[Dict[str, Any]] = []
    for i in range(9):
        pr_planet = calc.PLANET_ORDER[(start_index + i) % 9]
        pr_period = (antar_period * calc.DASHA_PERIODS[pr_planet]) / 120
        pr_days = pr_period * 365.242199
        pr_end = current + timedelta(days=pr_days)
        out.append({"planet": pr_planet, "start": current, "end": pr_end})
        current = pr_end
    return out


def _next_mahadasha(
    calc: DashaCalculator, birth_data: Dict[str, Any], scan_dt: datetime
) -> Optional[Tuple[datetime, str, str]]:
    d = calc.calculate_current_dashas(birth_data, scan_dt)
    maha_dashas = d.get("maha_dashas") or []
    if not maha_dashas:
        return None
    current = None
    idx = -1
    for i, m in enumerate(maha_dashas):
        if m["start"] <= scan_dt <= m["end"]:
            current = m
            idx = i
            break
    if current is None:
        return None
    if idx + 1 < len(maha_dashas):
        nxt = maha_dashas[idx + 1]
        return (nxt["start"], current["planet"], nxt["planet"])
    # End of 9-maha block: probe after current maha ends
    probe = current["end"] + timedelta(seconds=2)
    d2 = calc.calculate_current_dashas(birth_data, probe)
    ms = d2.get("mahadasha") or {}
    to_p = ms.get("planet")
    if not to_p or to_p == current["planet"]:
        return None
    try:
        nxt_start = _parse_iso_dt(ms["start"])
    except Exception:
        return None
    return (nxt_start, current["planet"], to_p)


def _next_antardasha(
    calc: DashaCalculator, birth_data: Dict[str, Any], scan_dt: datetime
) -> Optional[Tuple[datetime, str, str]]:
    d = calc.calculate_current_dashas(birth_data, scan_dt)
    maha_dashas = d.get("maha_dashas") or []
    if not maha_dashas:
        return None
    current_maha = None
    for m in maha_dashas:
        if m["start"] <= scan_dt <= m["end"]:
            current_maha = m
            break
    if not current_maha:
        return None
    ants = _iter_antardashas(calc, current_maha)
    for i, a in enumerate(ants):
        if a["start"] <= scan_dt <= a["end"]:
            if i + 1 < len(ants):
                nxt = ants[i + 1]
                return (nxt["start"], a["planet"], nxt["planet"])
            nm = _next_mahadasha(calc, birth_data, scan_dt)
            if not nm:
                return None
            n_start, _from_m, _to_m = nm
            probe = n_start + timedelta(hours=6)
            d2 = calc.calculate_current_dashas(birth_data, probe)
            m2 = None
            for m in d2.get("maha_dashas") or []:
                if m["start"] <= probe <= m["end"]:
                    m2 = m
                    break
            if not m2:
                return None
            first_ants = _iter_antardashas(calc, m2)
            if not first_ants:
                return None
            fa = first_ants[0]
            return (fa["start"], a["planet"], fa["planet"])
    return None


def _next_pratyantardasha(
    calc: DashaCalculator, birth_data: Dict[str, Any], scan_dt: datetime
) -> Optional[Tuple[datetime, str, str]]:
    d = calc.calculate_current_dashas(birth_data, scan_dt)
    maha_dashas = d.get("maha_dashas") or []
    if not maha_dashas:
        return None
    current_maha = None
    for m in maha_dashas:
        if m["start"] <= scan_dt <= m["end"]:
            current_maha = m
            break
    if not current_maha:
        return None
    ants = _iter_antardashas(calc, current_maha)
    current_antar = None
    for a in ants:
        if a["start"] <= scan_dt <= a["end"]:
            current_antar = a
            break
    if not current_antar:
        return None
    prs = _iter_pratyantardashas(calc, current_maha, current_antar)
    for i, p in enumerate(prs):
        if p["start"] <= scan_dt <= p["end"]:
            if i + 1 < len(prs):
                nxt = prs[i + 1]
                return (nxt["start"], p["planet"], nxt["planet"])
            na = _next_antardasha(calc, birth_data, scan_dt)
            if not na:
                return None
            a_start, _from_a, _to_a = na
            probe = a_start + timedelta(hours=6)
            d2 = calc.calculate_current_dashas(birth_data, probe)
            m2 = None
            for m in d2.get("maha_dashas") or []:
                if m["start"] <= probe <= m["end"]:
                    m2 = m
                    break
            if not m2:
                return None
            ants2 = _iter_antardashas(calc, m2)
            a2 = None
            for x in ants2:
                if x["start"] <= probe <= x["end"]:
                    a2 = x
                    break
            if not a2:
                return None
            prs2 = _iter_pratyantardashas(calc, m2, a2)
            if not prs2:
                return None
            fp = prs2[0]
            return (fp["start"], p["planet"], fp["planet"])
    return None


def find_upcoming_dasha_changes(
    birth_data: Dict[str, Any], scan_date: date
) -> Dict[str, Optional[Tuple[datetime, str, str]]]:
    """
    Return next start datetimes (and from/to planets) for MD, AD, PD strictly after scan moment.
    Keys: mahadasha, antardasha, pratyantardasha. Value None if unknown.
    """
    calc = DashaCalculator()
    scan_dt = _scan_dt(scan_date)
    return {
        "mahadasha": _next_mahadasha(calc, birth_data, scan_dt),
        "antardasha": _next_antardasha(calc, birth_data, scan_dt),
        "pratyantardasha": _next_pratyantardasha(calc, birth_data, scan_dt),
    }
