"""
Per-user nudge: upcoming Vimshottari Mahadasha, Antardasha, or Pratyantardasha change.

Lead times (defaults): MD within 90 days, AD within 30 days, PD within 2 days — configurable in DB.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from ..models import NudgeEvent
from ..trigger_base import TriggerBase
from ..config import DEFAULT_CTA_DEEP_LINK
from .. import db
from ..trigger_def_loader import load_merged_definition
from ..vimshottari_next_changes import find_upcoming_dasha_changes

logger = logging.getLogger(__name__)

TRIGGER_KEY = "vimshottari_dasha_change"

LEVEL_ORDER: Tuple[Tuple[str, str], ...] = (
    ("mahadasha", "md_lead_days"),
    ("antardasha", "ad_lead_days"),
    ("pratyantardasha", "pd_lead_days"),
)

LEVEL_COPY: Dict[str, Tuple[str, str]] = {
    "mahadasha": ("Mahadasha (MD)", "MD"),
    "antardasha": ("Antardasha (AD)", "AD"),
    "pratyantardasha": ("Pratyantardasha (PD)", "PD"),
}


def _chart_to_birth_data(chart: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "date": chart["date"],
        "time": chart["time"],
        "timezone": chart["timezone"],
        "latitude": chart["latitude"],
        "longitude": chart["longitude"],
        "name": "Self",
    }


def _fmt_change_day(d: date) -> str:
    return d.strftime("%d %b %Y")


class VimshottariDashaChangeTrigger(TriggerBase):
    """Notify self-chart users when a Vimshottari boundary is within the configured lead window."""

    def get_events(self, target_date: date) -> List[NudgeEvent]:
        events: List[NudgeEvent] = []
        try:
            with db.get_conn() as conn:
                merged = load_merged_definition(conn, TRIGGER_KEY)
                if not merged.enabled:
                    return events
                charts = db.get_self_charts_for_nudge(conn)
                dedupe_since = target_date - timedelta(days=120)
                sent_keys = db.get_vimshottari_dasha_dedupe_keys(conn, dedupe_since)
        except Exception as e:
            logger.exception("Vimshottari dasha nudge DB prep failed: %s", e)
            return events

        if not charts:
            return events

        cfg = merged.config

        for chart in charts:
            uid = chart["userid"]
            bcid = chart["birth_chart_id"]
            try:
                bd = _chart_to_birth_data(chart)
                changes = find_upcoming_dasha_changes(bd, target_date)
            except Exception as e:
                logger.debug("Vimshottari skip user %s: %s", uid, e)
                continue

            for level_key, lead_cfg in LEVEL_ORDER:
                lead = int(cfg[lead_cfg])
                tup = changes.get(level_key)
                if not tup:
                    continue
                start_dt, from_planet, to_planet = tup
                change_day = start_dt.date()
                days_until = (change_day - target_date).days
                if days_until <= 0 or days_until > lead:
                    continue
                cs_iso = change_day.isoformat()
                dedupe_key = (uid, level_key, cs_iso)
                if dedupe_key in sent_keys:
                    continue
                sent_keys.add(dedupe_key)

                label, short = LEVEL_COPY[level_key]
                facts = {
                    "level_label": label,
                    "level_short": short,
                    "from_planet": from_planet,
                    "to_planet": to_planet,
                    "change_start": cs_iso,
                    "change_date_display": _fmt_change_day(change_day),
                }
                try:
                    title, body, question = merged.render_copy(facts)
                except Exception as e:
                    logger.warning("Vimshottari render skip user %s: %s", uid, e)
                    continue

                events.append(
                    NudgeEvent(
                        trigger_id=TRIGGER_KEY,
                        user_ids=[uid],
                        params={
                            "level": level_key,
                            "change_start": cs_iso,
                            "from_planet": from_planet,
                            "to_planet": to_planet,
                            "birth_chart_id": bcid,
                        },
                        title=title,
                        body=body,
                        cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                        question=question,
                        priority=merged.priority,
                    )
                )

        return events
