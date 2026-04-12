"""
Per-user nudge: transiting planet re-enters the sidereal *sign* (whole-sign 30°)
where that planet sat at birth — broader than the exact degree conjunction.

Uses the same daily noon UT ephemeris grid as natal_planet_return.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK
from .. import db
from ..trigger_def_loader import load_merged_definition
from .planet_transit_sign import SIGNS
from .natal_planet_return import (
    PLANETS,
    _birth_jd,
    _format_date_range,
    _natal_longitude,
    _precompute_transit_series,
)

logger = logging.getLogger(__name__)

TRIGGER_ID = "natal_whole_sign_return"


def _sign_index(lon: float) -> int:
    return int(lon / 30.0) % 12


def _find_next_whole_sign_window(
    lons: List[float], natal_sign_idx: int
) -> Optional[Tuple[int, int]]:
    """
    Next span of consecutive days (noon UT) where transiting planet occupies natal_sign_idx,
    after skipping any current stay in that sign on scan day (day 0).
    """
    h = len(lons) - 1

    def in_natal_sign(i: int) -> bool:
        return _sign_index(lons[i]) == natal_sign_idx

    start_idx = 0
    while start_idx <= h and in_natal_sign(start_idx):
        start_idx += 1
    if start_idx > h:
        return None

    prev = in_natal_sign(start_idx)
    for k in range(start_idx + 1, h + 1):
        cur = in_natal_sign(k)
        if cur and not prev:
            w_end = k
            while w_end + 1 <= h and in_natal_sign(w_end + 1):
                w_end += 1
            return k, w_end
        prev = cur
    return None


class NatalWholeSignReturnTrigger(TriggerBase):
    """Per-user nudge when transiting planet will re-enter its natal sidereal sign soon."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            with db.get_conn() as conn:
                merged = load_merged_definition(conn, TRIGGER_ID)
                if not merged.enabled:
                    return events
                charts = db.get_self_charts_for_nudge(conn)
                dedupe_since = target_date - timedelta(days=45)
                sent_keys = db.get_planet_window_dedupe_keys(
                    conn, TRIGGER_ID, dedupe_since
                )
        except Exception as e:
            logger.exception("Natal whole-sign return DB prep failed: %s", e)
            return events

        if not charts:
            return events

        cfg = merged.config
        horizon = int(cfg["horizon_days"])
        advance_days = int(cfg["advance_notice_days"])
        allowed = set(cfg["planets"])
        planet_pairs = tuple((pid, n) for pid, n in PLANETS if n in allowed)
        if not planet_pairs:
            return events

        try:
            transit_series = _precompute_transit_series(
                target_date, horizon, planet_pairs
            )
        except Exception as e:
            logger.exception("Natal whole-sign ephemeris precompute failed: %s", e)
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
                    natal_sign_idx = _sign_index(natal_lon)
                    sign_name = SIGNS[natal_sign_idx]
                    lons = transit_series.get(planet_name)
                    if not lons:
                        continue
                    win = _find_next_whole_sign_window(lons, natal_sign_idx)
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
                        "sign": sign_name,
                        "date_range": dr,
                        "window_start": w_start.isoformat(),
                        "window_end": w_end.isoformat(),
                    }
                    title, body, question = merged.render_copy(facts)
                    events.append(
                        NudgeEvent(
                            trigger_id=TRIGGER_ID,
                            user_ids=[uid],
                            params={
                                "planet": planet_name,
                                "sign": sign_name,
                                "natal_sign_index": natal_sign_idx + 1,
                                "window_start": ws_iso,
                                "window_end": w_end.isoformat(),
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
                        "Natal whole-sign return skip user %s planet %s: %s",
                        uid,
                        planet_name,
                        e,
                        exc_info=True,
                    )
                    continue

        return events
