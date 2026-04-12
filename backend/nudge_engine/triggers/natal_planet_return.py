"""
Per-user nudge: transiting planet within orb of the same planet's natal longitude
(planetary "return" / revisit). Notifies during the 30 days before the window starts.

Uses shared daily noon UT ephemeris samples for all users (efficient at scale).
Horizon is limited (~800d); slow outer returns beyond that are skipped until closer.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import swisseph as swe

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK
from .. import db
from ..trigger_def_loader import load_merged_definition
from utils.timezone_service import parse_timezone_offset

logger = logging.getLogger(__name__)

TRIGGER_KEY = "natal_planet_return"

PLANETS: Tuple[Tuple[int, str], ...] = (
    (swe.SUN, "Sun"),
    (swe.MOON, "Moon"),
    (swe.MERCURY, "Mercury"),
    (swe.VENUS, "Venus"),
    (swe.MARS, "Mars"),
    (swe.JUPITER, "Jupiter"),
    (swe.SATURN, "Saturn"),
)


def _angular_distance(lon_a: float, lon_b: float) -> float:
    d = abs(lon_a - lon_b) % 360.0
    return min(d, 360.0 - d)


def _birth_jd(date_str: str, time_str: str, lat: float, lon: float, tz: str) -> float:
    time_parts = time_str.split(":")
    h = int(time_parts[0])
    mi = int(time_parts[1]) if len(time_parts) > 1 else 0
    hour = float(h) + float(mi) / 60.0
    tz_offset = parse_timezone_offset(tz, lat, lon)
    utc_hour = float(hour) - float(tz_offset)
    y, m, d = (int(x) for x in date_str.split("-"))
    return swe.julday(y, m, d, utc_hour)


def _natal_longitude(planet_id: int, birth_jd: float) -> float:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    pos = swe.calc_ut(birth_jd, planet_id, swe.FLG_SIDEREAL)
    if not pos:
        return 0.0
    return pos[0][0] % 360.0


def _precompute_transit_series(
    scan_date: date, horizon: int, planet_pairs: Tuple[Tuple[int, str], ...]
) -> Dict[str, List[float]]:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    series: Dict[str, List[float]] = {name: [] for _, name in planet_pairs}
    for i in range(horizon + 1):
        d = scan_date + timedelta(days=i)
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        for pid, pname in planet_pairs:
            pos = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL)
            lon = pos[0][0] % 360.0 if pos else 0.0
            series[pname].append(lon)
    return series


def _find_next_return_window(
    lons: List[float], natal_lon: float, orb: float
) -> Optional[Tuple[int, int]]:
    """
    Return (start_offset, end_offset) from scan_date for the next ingress into orb
    after any return that is already active on scan day (day 0).
    """
    h = len(lons) - 1

    def in_orb(i: int) -> bool:
        return _angular_distance(lons[i], natal_lon) <= orb

    start_idx = 0
    while start_idx <= h and in_orb(start_idx):
        start_idx += 1
    if start_idx > h:
        return None

    prev = in_orb(start_idx)
    for k in range(start_idx + 1, h + 1):
        cur = in_orb(k)
        if cur and not prev:
            w_end = k
            while w_end + 1 <= h and in_orb(w_end + 1):
                w_end += 1
            return k, w_end
        prev = cur
    return None


def _format_date_range(w_start: date, w_end: date) -> str:
    if w_start.year == w_end.year and w_start.month == w_end.month:
        return f"{w_start.day}–{w_end.day} {w_start.strftime('%b %Y')}"
    return (
        f"{w_start.day} {w_start.strftime('%b %Y')} – "
        f"{w_end.day} {w_end.strftime('%b %Y')}"
    )


class NatalPlanetReturnTrigger(TriggerBase):
    """Per-user nudge when a planetary return is due within the configured advance window."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            with db.get_conn() as conn:
                merged = load_merged_definition(conn, TRIGGER_KEY)
                if not merged.enabled:
                    return events
                charts = db.get_self_charts_for_nudge(conn)
                dedupe_since = target_date - timedelta(days=45)
                sent_keys = db.get_planet_window_dedupe_keys(
                    conn, TRIGGER_KEY, dedupe_since
                )
        except Exception as e:
            logger.exception("Natal return trigger DB prep failed: %s", e)
            return events

        if not charts:
            return events

        cfg = merged.config
        horizon = int(cfg["horizon_days"])
        advance_days = int(cfg["advance_notice_days"])
        orb_deg = float(cfg["orb_deg"])
        allowed = set(cfg["planets"])
        planet_pairs = tuple((pid, n) for pid, n in PLANETS if n in allowed)
        if not planet_pairs:
            return events

        try:
            transit_series = _precompute_transit_series(target_date, horizon, planet_pairs)
        except Exception as e:
            logger.exception("Natal return ephemeris precompute failed: %s", e)
            return events

        for chart in charts:
            uid = chart["userid"]
            bcid = chart["birth_chart_id"]
            d_str, t_str = chart["date"], chart["time"]
            if not d_str or not t_str:
                continue
            try:
                bjd = _birth_jd(
                    d_str,
                    t_str,
                    chart["latitude"],
                    chart["longitude"],
                    chart["timezone"],
                )
            except Exception as e:
                logger.debug("Natal JD failed user %s: %s", uid, e)
                continue

            for planet_id, planet_name in planet_pairs:
                try:
                    natal_lon = _natal_longitude(planet_id, bjd)
                    lons = transit_series.get(planet_name)
                    if not lons:
                        continue
                    win = _find_next_return_window(lons, natal_lon, orb_deg)
                    if not win:
                        continue
                    off_start, off_end = win
                    w_start = target_date + timedelta(days=off_start)
                    w_end = target_date + timedelta(days=off_end)
                    days_until = (w_start - target_date).days
                    if days_until < 0 or days_until > advance_days:
                        continue
                    ws_iso = w_start.isoformat()
                    dedupe_key = (uid, planet_name, ws_iso)
                    if dedupe_key in sent_keys:
                        continue
                    sent_keys.add(dedupe_key)

                    dr = _format_date_range(w_start, w_end)
                    facts = {
                        "planet": planet_name,
                        "date_range": dr,
                        "window_start": w_start.isoformat(),
                        "window_end": w_end.isoformat(),
                    }
                    title, body, question = merged.render_copy(facts)
                    events.append(
                        NudgeEvent(
                            trigger_id=TRIGGER_KEY,
                            user_ids=[uid],
                            params={
                                "planet": planet_name,
                                "window_start": ws_iso,
                                "window_end": w_end.isoformat(),
                                "orb_deg": orb_deg,
                                "birth_chart_id": bcid,
                            },
                            title=title,
                            body=body,
                            cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                            question=question,
                            priority=merged.priority,
                        )
                    )
                except Exception as e:
                    logger.warning(
                        "Natal return skip user %s planet %s: %s",
                        uid,
                        planet_name,
                        e,
                        exc_info=True,
                    )
                    continue

        return events
