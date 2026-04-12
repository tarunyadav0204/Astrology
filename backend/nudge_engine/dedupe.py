"""
Expand global events (user_ids=None) to concrete user lists.
Every triggered event is delivered to each target user, except pairs already
recorded for that date (idempotent re-scan).
"""
import logging
from datetime import date
from typing import List, Tuple

from .models import NudgeEvent
from . import db

logger = logging.getLogger(__name__)


def resolve_and_cap(
    events: List[NudgeEvent], target_date: date
) -> List[Tuple[int, NudgeEvent]]:
    """
    Expand events with user_ids=None to all user ids.
    Emit one (userid, event) per user per distinct trigger firing; skip if that
    exact notification was already stored for target_date (same userid, trigger_id, title).
    """
    with db.get_conn() as conn:
        all_user_ids = db.get_all_user_ids(conn)
        existing = db.get_delivery_fingerprints_on_date(conn, target_date)

    result: List[Tuple[int, NudgeEvent]] = []
    for ev in events:
        user_list = all_user_ids if ev.user_ids is None else ev.user_ids
        for uid in user_list:
            key = (uid, ev.trigger_id, ev.title)
            if key in existing:
                continue
            result.append((uid, ev))

    return result
