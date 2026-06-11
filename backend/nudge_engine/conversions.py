"""
Conversion attribution: when a chat ask request carries nudge_id (the
delivery_group_id from a push/WhatsApp/email nudge), record that the nudge
converted into a question and how long it took.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from . import db

logger = logging.getLogger(__name__)


def record_nudge_conversion(
    conn,
    *,
    delivery_group_id: str,
    userid: int,
    question: str,
    attribution: str = "tap",
) -> bool:
    """
    Best-effort, idempotent (first question per nudge group wins).
    Returns True when a new conversion row was created.
    """
    group_id = str(delivery_group_id or "").strip()
    if not group_id or len(group_id) > 64:
        return False
    delivery = db.find_primary_delivery_by_group(conn, group_id)
    if not delivery:
        return False
    if int(delivery["userid"]) != int(userid):
        logger.warning(
            "nudge conversion user mismatch group=%s delivery_user=%s ask_user=%s",
            group_id, delivery["userid"], userid,
        )
        return False
    seconds: Optional[int] = None
    created_at = delivery.get("created_at")
    if created_at is not None:
        try:
            now = datetime.now(timezone.utc)
            if created_at.tzinfo is None:
                now = datetime.utcnow()
            seconds = max(0, int((now - created_at).total_seconds()))
        except Exception:
            seconds = None
    return db.insert_conversion(
        conn,
        delivery_group_id=group_id,
        campaign_id=delivery.get("campaign_id"),
        userid=int(userid),
        trigger_id=delivery.get("trigger_id") or "",
        question=question or "",
        seconds_since_sent=seconds,
        attribution=attribution,
    )
