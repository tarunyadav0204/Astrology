"""
Channel orchestrator: deliver one logical nudge over push / WhatsApp / email
with a per-send policy (waterfall or blast), and persist one nudge_deliveries
row per attempted channel sharing a delivery_group_id.

Every push/WhatsApp/email payload carries nudge_id = delivery_group_id so the
app and the chat ask endpoint can attribute "user asked a question" conversions.
"""
import json
import logging
import uuid
from datetime import date
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .models import NudgeEvent
from . import db
from . import push as push_module
from .whatsapp_fallback import send_whatsapp_nudge, send_whatsapp_nudge_template

logger = logging.getLogger(__name__)

SUPPORTED_CHANNELS: Tuple[str, ...] = ("push", "whatsapp", "email")
DEFAULT_WATERFALL_CHANNELS: Tuple[str, ...] = ("push", "whatsapp")


def new_delivery_group_id() -> str:
    return uuid.uuid4().hex


def _attempt_push(
    conn,
    userid: int,
    title: str,
    body: str,
    push_data: Dict[str, Any],
    image_url: Optional[str] = None,
) -> bool:
    tokens = db.get_device_tokens_for_user(conn, userid)
    for token, _platform in tokens or []:
        if push_module.send_expo_push(token, title, body, data=push_data, image_url=image_url):
            return True
    return False


def _attempt_whatsapp(conn, userid: int, title: str, body: str, question: Optional[str]) -> Optional[str]:
    if send_whatsapp_nudge(conn, userid=userid, title=title, body=body, question=question):
        return "whatsapp"
    if send_whatsapp_nudge_template(conn, userid=userid):
        return "whatsapp_template"
    return None


def _attempt_email(
    conn, userid: int, title: str, body: str, question: Optional[str], group_id: str
) -> bool:
    from .email_channel import send_nudge_email

    return bool(
        send_nudge_email(
            conn,
            userid=userid,
            title=title,
            body=body,
            question=question,
            delivery_group_id=group_id,
        )
    )


def deliver_nudge(
    conn,
    *,
    userid: int,
    trigger_id: str,
    title: str,
    body: str,
    question: Optional[str] = None,
    policy: str = "waterfall",
    channels: Sequence[str] = DEFAULT_WATERFALL_CHANNELS,
    campaign_id: Optional[int] = None,
    sent_at: Optional[date] = None,
    event_params: str = "",
    data_extra: Optional[Dict[str, Any]] = None,
    cta_deep_link: str = "astroroshni://chat",
    image_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deliver one logical nudge to one user:
    - policy "waterfall": try channels in order, stop at the first success.
    - policy "blast": attempt every requested channel the user is reachable on.

    Always writes nudge_deliveries rows (one per attempted channel; a single
    'stored' row when nothing succeeded so the nudge still reaches the in-app
    inbox). Exactly one row per group is is_primary (the inbox row).
    """
    userid = int(userid)
    sent_at = sent_at or date.today()
    group_id = new_delivery_group_id()
    policy = (policy or "waterfall").strip().lower()
    requested = [c for c in (channels or []) if c in SUPPORTED_CHANNELS] or list(
        DEFAULT_WATERFALL_CHANNELS
    )

    push_data: Dict[str, Any] = {
        "trigger_id": trigger_id,
        "cta": cta_deep_link,
        "nudge_id": group_id,
    }
    q = (question or "").strip()
    if q:
        push_data["question"] = q[:500]
    if data_extra:
        for key, value in data_extra.items():
            if value is not None:
                push_data[key] = value

    attempts: List[Tuple[str, bool]] = []
    for channel in requested:
        if channel == "push":
            ok = _attempt_push(conn, userid, title, body, push_data, image_url=image_url)
            actual_channel = "push"
        elif channel == "whatsapp":
            actual_channel = _attempt_whatsapp(conn, userid, title, body, q or None) or "whatsapp"
            ok = actual_channel in {"whatsapp", "whatsapp_template"}
        elif channel == "email":
            ok = _attempt_email(conn, userid, title, body, q or None, group_id)
            actual_channel = "email"
        else:
            continue
        attempts.append((actual_channel, ok))
        if ok and policy != "blast":
            break

    sent_channels = [c for c, ok in attempts if ok]
    primary_channel = sent_channels[0] if sent_channels else "stored"

    primary_assigned = False
    for channel, ok in attempts:
        is_primary = ok and not primary_assigned
        if is_primary:
            primary_assigned = True
        db.insert_delivery(
            conn,
            userid=userid,
            trigger_id=trigger_id,
            title=title,
            body=body,
            sent_at=sent_at,
            event_params=event_params or "",
            channel=channel,
            data_payload=push_data,
            campaign_id=campaign_id,
            delivery_group_id=group_id,
            send_status="sent" if ok else "failed",
            is_primary=is_primary,
        )
    if not primary_assigned:
        # Nothing succeeded (or no channel was attempted): keep an inbox row.
        db.insert_delivery(
            conn,
            userid=userid,
            trigger_id=trigger_id,
            title=title,
            body=body,
            sent_at=sent_at,
            event_params=event_params or "",
            channel="stored",
            data_payload=push_data,
            campaign_id=campaign_id,
            delivery_group_id=group_id,
            send_status="stored",
            is_primary=True,
        )

    return {
        "delivery_group_id": group_id,
        "channel": primary_channel,
        "channels_sent": sent_channels,
        "channels_failed": [c for c, ok in attempts if not ok],
    }


def deliver(
    target_date: date,
    to_send: List[Tuple[int, NudgeEvent]],
) -> int:
    """
    Daily astrology scan delivery (legacy entry point): waterfall push → WhatsApp,
    in-app inbox always. Routed through the channel orchestrator.
    """
    if not to_send:
        return 0
    count = 0
    with db.get_conn() as conn:
        for userid, ev in to_send:
            try:
                params_json = json.dumps(ev.params) if ev.params else ""
                data_extra: Dict[str, Any] = {}
                bcid = ev.params.get("birth_chart_id") if ev.params else None
                if bcid is not None and str(bcid).strip():
                    data_extra["native_id"] = str(bcid).strip()
                deliver_nudge(
                    conn,
                    userid=int(userid),
                    trigger_id=ev.trigger_id,
                    title=ev.title,
                    body=ev.body,
                    question=ev.question,
                    policy="waterfall",
                    channels=DEFAULT_WATERFALL_CHANNELS,
                    sent_at=target_date,
                    event_params=params_json,
                    data_extra=data_extra,
                    cta_deep_link=ev.cta_deep_link or "astroroshni://chat",
                )
                count += 1
            except Exception as e:
                logger.exception(
                    "Delivery failed for user %s, trigger %s: %s",
                    userid, ev.trigger_id, e,
                )
        try:
            conn.commit()
        except Exception:
            pass
    return count
