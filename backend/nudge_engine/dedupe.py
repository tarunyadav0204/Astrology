"""
Resolve global events (user_ids=None) to concrete user lists, then cap at most
MAX_NUDGES_PER_USER_PER_DAY per user. Returns list of (userid, NudgeEvent) to send.
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
    Expand events with user_ids=None to all user ids, then for each user keep at most
    one nudge (highest priority). Users who already received a nudge on target_date are skipped.
    """
    conn = db.get_conn()
    try:
        all_user_ids = db.get_all_user_ids(conn)
        already_sent = db.get_user_ids_receiving_nudge_on_date(conn, target_date)
    finally:
        conn.close()

    # Build per-user candidate list: (userid, event) for each event and each target user
    candidates: List[Tuple[int, NudgeEvent]] = []
    for ev in events:
        if ev.user_ids is None:
            user_list = all_user_ids
        else:
            user_list = ev.user_ids
        for uid in user_list:
            candidates.append((uid, ev))

    # For each user, keep only the best event (by priority), and skip if already sent
    from collections import defaultdict
    by_user: dict[int, List[Tuple[int, NudgeEvent]]] = defaultdict(list)
    for uid, ev in candidates:
        if uid in already_sent:
            continue
        by_user[uid].append((uid, ev))

    result: List[Tuple[int, NudgeEvent]] = []
    for uid, user_candidates in by_user.items():
        if not user_candidates:
            continue
        best = max(user_candidates, key=lambda x: (x[1].priority, x[1].title))
        result.append(best)

    return result
