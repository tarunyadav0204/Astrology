"""Persist nudges to nudge_deliveries and send push when device tokens exist."""
import json
import logging
from datetime import date
from typing import List, Tuple

from .models import NudgeEvent
from . import db
from . import push as push_module

logger = logging.getLogger(__name__)


def deliver(
    target_date: date,
    to_send: List[Tuple[int, NudgeEvent]],
) -> int:
    """
    For each (userid, event): store in nudge_deliveries and, if the user has
    registered device token(s), send via Expo Push API. Channel is "push" if
    at least one push was sent, otherwise "stored".
    """
    if not to_send:
        return 0
    conn = db.get_conn()
    count = 0
    try:
        for userid, ev in to_send:
            try:
                params_json = json.dumps(ev.params) if ev.params else ""
                tokens = db.get_device_tokens_for_user(conn, userid)
                channel = "stored"
                push_data = {"trigger_id": ev.trigger_id, "cta": ev.cta_deep_link}
                if ev.question and (ev.question or "").strip():
                    push_data["question"] = (ev.question or "").strip()[:500]
                if tokens:
                    for token, platform in tokens:
                        if push_module.send_expo_push(
                            token, ev.title, ev.body,
                            data=push_data,
                        ):
                            channel = "push"
                            break
                db.insert_delivery(
                    conn,
                    userid=userid,
                    trigger_id=ev.trigger_id,
                    title=ev.title,
                    body=ev.body,
                    sent_at=target_date,
                    event_params=params_json,
                    channel=channel,
                )
                count += 1
            except Exception as e:
                logger.exception(
                    "Delivery failed for user %s, trigger %s: %s",
                    userid, ev.trigger_id, e,
                )
    finally:
        conn.close()
    return count
