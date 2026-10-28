"""Personalize the daily Moon nakshatra nudge with the user's Tara Bala."""
from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional

import swisseph as swe

from . import db
from .config import DEFAULT_CTA_DEEP_LINK
from .delivery import DEFAULT_WATERFALL_CHANNELS, deliver_nudge
from .task_queue import enqueue_nudge_task, nudge_tasks_are_isolated, nudge_tasks_enabled
from .triggers.moon_nakshatra import MoonNakshatraTrigger
from .triggers.natal_planet_return import _birth_jd

logger = logging.getLogger(__name__)

TRIGGER_ID = "moon_nakshatra_tara"
_TARAS = (
    ("Janma Tara", "an emotionally heightened, inward day", "Move deliberately and give yourself space before reacting."),
    ("Sampat Tara", "resource and opportunity themes", "Use it for practical gains and steady follow-through."),
    ("Vipat Tara", "friction and avoidable complications", "Keep plans simple and double-check details before committing."),
    ("Kshema Tara", "support, comfort, and consolidation", "Favour stable choices and work that strengthens what is already underway."),
    ("Pratyari Tara", "resistance or competing demands", "Avoid forcing outcomes; respond calmly and protect your focus."),
    ("Sadhaka Tara", "constructive effort and progress", "Choose one meaningful task and carry it through."),
    ("Naidhana Tara", "a lower-energy, closure-oriented tone", "Avoid impulsive commitments and prioritise rest, review, and risk control."),
    ("Mitra Tara", "cooperation and helpful exchanges", "Reach out, collaborate, or complete a useful conversation."),
    ("Parama Mitra Tara", "ease and supportive momentum", "Use the day for a worthwhile initiative or important connection."),
)


def _natal_moon_nakshatra(chart: Dict[str, Any]) -> Optional[int]:
    try:
        jd = _birth_jd(chart["date"], chart["time"], float(chart["latitude"]), float(chart["longitude"]), chart.get("timezone") or "")
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        longitude = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0] % 360.0
        return max(1, min(27, int(longitude / (360.0 / 27.0)) + 1))
    except Exception:
        logger.exception("Moon Tara birth calculation failed for user %s", chart.get("userid"))
        return None


def _tara(natal_index: int, transit_index: int) -> Dict[str, Any]:
    distance = ((int(transit_index) - int(natal_index)) % 27) + 1
    name, theme, guidance = _TARAS[(distance - 1) % 9]
    return {"name": name, "distance": distance, "theme": theme, "guidance": guidance}


def enqueue_moon_tara_batches(target_date: date) -> Dict[str, Any]:
    """Find today's Moon ingress once, then enqueue token holders in worker batches."""
    if not nudge_tasks_enabled() or not nudge_tasks_are_isolated():
        raise RuntimeError("Moon Tara notifications require isolated Cloud Tasks workers")
    events = MoonNakshatraTrigger().get_events(target_date)
    if not events:
        return {"date": target_date.isoformat(), "moon_transition": False, "candidates": 0, "batches_enqueued": 0}
    event = events[0]
    transit_index = int((event.params or {}).get("nakshatra_index") or 0)
    transit_name = str((event.params or {}).get("nakshatra_name") or "").strip()
    if not 1 <= transit_index <= 27 or not transit_name:
        raise RuntimeError("Moon transit did not provide a valid nakshatra")

    after_userid = batches = candidates = 0
    batch_size = 50
    while True:
        with db.get_conn() as conn:
            ids = db.get_push_enabled_user_ids_after(conn, after_userid=after_userid, limit=batch_size)
        if not ids:
            break
        candidates += len(ids)
        ok = enqueue_nudge_task(
            task_kind="moon-tara-batch",
            task_id=f"{target_date.isoformat()}-{ids[0]}-{ids[-1]}",
            payload={"scan_date": target_date.isoformat(), "user_ids": ids, "transit_nakshatra_index": transit_index, "transit_nakshatra_name": transit_name},
        )
        batches += int(bool(ok))
        after_userid = int(ids[-1])
    return {"date": target_date.isoformat(), "moon_transition": True, "candidates": candidates, "batches_enqueued": batches}


def process_moon_tara_batch(*, target_date: date, user_ids: List[int], transit_nakshatra_index: int, transit_nakshatra_name: str) -> Dict[str, int]:
    ids = [int(uid) for uid in (user_ids or []) if str(uid).isdigit()]
    if not ids:
        return {"targeted": 0, "delivered": 0, "deduped": 0}
    if not 1 <= int(transit_nakshatra_index) <= 27:
        raise ValueError("Invalid transit nakshatra")
    with db.get_read_conn() as conn:
        charts = db.get_self_charts_for_nudge(conn, ids)
    charts_by_user = {int(chart["userid"]): chart for chart in charts}
    delivered = deduped = 0
    for userid in ids:
        chart = charts_by_user.get(userid)
        if not chart or not chart.get("date") or not chart.get("time"):
            continue
        with db.get_conn() as conn:
            if db.has_delivery_for_user_trigger_on_date(conn, userid=userid, trigger_id=TRIGGER_ID, target_date=target_date):
                deduped += 1
                continue
        natal_index = _natal_moon_nakshatra(chart)
        if not natal_index:
            continue
        tara = _tara(natal_index, int(transit_nakshatra_index))
        title = f"Moon in {transit_nakshatra_name}: your {tara['name']}"
        body = f"Today’s Moon is activating {tara['theme']} for you. {tara['guidance']}"
        question = (
            f"Give me a concise daily reading for {target_date.isoformat()}. The Moon is in {transit_nakshatra_name}, "
            f"which is my {tara['name']}. Explain the practical effect and what to prioritise today."
        )
        try:
            with db.get_conn() as conn:
                if db.has_delivery_for_user_trigger_on_date(conn, userid=userid, trigger_id=TRIGGER_ID, target_date=target_date):
                    deduped += 1
                    continue
                deliver_nudge(
                    conn, userid=userid, trigger_id=TRIGGER_ID, title=title, body=body, question=question,
                    policy="waterfall", channels=DEFAULT_WATERFALL_CHANNELS, sent_at=target_date,
                    event_params=json.dumps({"birth_chart_id": chart["birth_chart_id"], "natal_nakshatra_index": natal_index, "transit_nakshatra_index": transit_nakshatra_index, "tara": tara["name"]}),
                    data_extra={"native_id": str(chart["birth_chart_id"]), "landing_screen": "chat"}, cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                )
                conn.commit()
            delivered += 1
        except Exception:
            logger.exception("Moon Tara delivery failed for user %s", userid)
    return {"targeted": len(ids), "delivered": delivered, "deduped": deduped}
