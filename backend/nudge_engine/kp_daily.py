"""High-confidence, personalized KP daily opportunity notifications.

Audience/chart data is read exclusively from the app read replica.  This module
only runs in the isolated nudge dispatch/worker services; it never runs in API
or chat request paths.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from . import db
from .config import DEFAULT_CTA_DEEP_LINK
from .delivery import DEFAULT_WATERFALL_CHANNELS, deliver_nudge
from .task_queue import enqueue_nudge_task, nudge_tasks_are_isolated, nudge_tasks_enabled

logger = logging.getLogger(__name__)

TRIGGER_ID = "kp_daily_opportunity"
TITLE = "Your KP daily opportunity"

_HOUSE_ACTIONS = {
    10: ("career or an important work task", "career and focused work"),
    6: ("a focused work or problem-solving task", "work, service, or a problem to solve"),
    11: ("a gain, outcome, or useful connection", "gains, outcomes, or helpful connections"),
    2: ("a money or value decision", "money, resources, or a value decision"),
    7: ("an important one-to-one conversation", "partnerships or one-to-one conversations"),
    3: ("a message, pitch, or decisive follow-up", "communication, outreach, or follow-up"),
    5: ("a creative or social initiative", "creative expression or social connection"),
}


def _batch_size() -> int:
    return max(1, min(int(os.getenv("NUDGE_KP_DAILY_BATCH_SIZE", "10") or "10"), 25))


def enqueue_kp_daily_batches(target_date: date) -> Dict[str, Any]:
    """Page opt-in push recipients and enqueue bounded worker-only KP jobs."""
    if not nudge_tasks_enabled() or not nudge_tasks_are_isolated():
        raise RuntimeError("KP daily notifications require isolated Cloud Tasks workers")

    after_userid = 0
    page = 0
    queued = 0
    candidates = 0
    batch_size = _batch_size()
    while True:
        # The notification DB holds only token eligibility. Birth charts are not
        # read here; the worker fetches them from the read replica per batch.
        with db.get_conn() as conn:
            user_ids = db.get_push_enabled_user_ids_after(
                conn, after_userid=after_userid, limit=batch_size
            )
        if not user_ids:
            break
        candidates += len(user_ids)
        task_id = f"{target_date.isoformat()}-{page}-{user_ids[0]}-{user_ids[-1]}"
        if enqueue_nudge_task(
            task_kind="kp-daily-batch",
            task_id=task_id,
            payload={"scan_date": target_date.isoformat(), "user_ids": user_ids},
            dispatch_deadline_s=900,
        ):
            queued += 1
        after_userid = int(user_ids[-1])
        page += 1
    return {"date": target_date.isoformat(), "candidates": candidates, "batches_enqueued": queued}


def _select_opportunity(result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Only surface a practical opportunity with fine-period and RP confirmation."""
    rows = ((result.get("today") or {}).get("houses_giving_results") or [])
    for row in rows:
        house = int(row.get("house") or 0)
        if house not in _HOUSE_ACTIONS:
            continue
        # A primary score alone is insufficient: require actual day RP and
        # Sookshma/PD-level period support before a user receives a push.
        score = float(row.get("activation_score") or 0)
        rp = list(row.get("rp_confirmation") or [])
        levels = {str(item.get("level") or "") for item in (row.get("period_support") or [])}
        if score < 4.0 or not rp or not ({"sookshma", "pratyantardasha"} & levels):
            continue
        if str(row.get("tone") or "").lower() == "challenging":
            continue
        action, focus = _HOUSE_ACTIONS[house]
        return {"house": house, "action": action, "focus": focus, "score": round(score, 2)}
    return None


def _calculate_event(chart: Dict[str, Any], target_date: date) -> Optional[Dict[str, Any]]:
    from app.kp.services.fructification_service import compute_fructification

    result = asyncio.run(compute_fructification(
        birth_date=chart["date"], birth_time=chart["time"],
        latitude=float(chart["latitude"]), longitude=float(chart["longitude"]),
        timezone=chart.get("timezone") or "", as_of_date=target_date.isoformat(),
        as_of_time="09:00", synthesize=False,
    ))
    opportunity = _select_opportunity(result)
    if not opportunity:
        return None
    question = (
        f"Give me a concise, practical KP daily reading for {target_date.isoformat()}. "
        f"Explain the {opportunity['focus']} opportunity indicated by House {opportunity['house']}, "
        "the supporting dasha and ruling planets, and what I should do today."
    )
    return {
        "title": TITLE,
        "body": f"KP timing supports {opportunity['action']} today. Open your focused daily reading.",
        "question": question,
        "params": {"birth_chart_id": chart["birth_chart_id"], "house": opportunity["house"], "score": opportunity["score"]},
    }


def process_kp_daily_batch(*, target_date: date, user_ids: List[int]) -> Dict[str, int]:
    """Worker-only calculation and delivery; no API/chat DB reads or LLM calls."""
    ids = [int(uid) for uid in (user_ids or []) if str(uid).isdigit()]
    if not ids:
        return {"targeted": 0, "qualified": 0, "delivered": 0, "deduped": 0}
    with db.get_read_conn() as conn:
        charts = db.get_self_charts_for_nudge(conn, ids)
    chart_by_user = {int(chart["userid"]): chart for chart in charts}
    qualified = delivered = deduped = 0
    for userid in ids:
        chart = chart_by_user.get(userid)
        if not chart or not chart.get("date") or not chart.get("time"):
            continue
        with db.get_conn() as conn:
            if db.has_delivery_for_user_trigger_on_date(
                conn, userid=userid, trigger_id=TRIGGER_ID, target_date=target_date
            ):
                deduped += 1
                continue
        try:
            event = _calculate_event(chart, target_date)
        except Exception:
            logger.exception("KP daily calculation failed for user %s", userid)
            continue
        if not event:
            continue
        qualified += 1
        try:
            with db.get_conn() as conn:
                # Repeat the guard immediately before the only write; Cloud Task
                # retries and duplicate task delivery cannot create a second push.
                if db.has_delivery_for_user_trigger_on_date(
                    conn, userid=userid, trigger_id=TRIGGER_ID, target_date=target_date
                ):
                    deduped += 1
                    continue
                deliver_nudge(
                    conn, userid=userid, trigger_id=TRIGGER_ID, title=event["title"], body=event["body"],
                    question=event["question"], policy="waterfall", channels=DEFAULT_WATERFALL_CHANNELS,
                    sent_at=target_date, event_params=json.dumps(event["params"]),
                    # The mobile client opens chat with its normal/simple
                    # notification flow when landing_screen is chat; do not
                    # force a premium or verified tier from a push.
                    data_extra={"native_id": str(event["params"]["birth_chart_id"]), "landing_screen": "chat"},
                    cta_deep_link=DEFAULT_CTA_DEEP_LINK,
                )
                conn.commit()
            delivered += 1
        except Exception:
            logger.exception("KP daily delivery failed for user %s", userid)
    return {"targeted": len(ids), "qualified": qualified, "delivered": delivered, "deduped": deduped}
