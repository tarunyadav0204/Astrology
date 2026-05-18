"""
Google Play RTDN worker.

Consumes Pub/Sub messages from play-subscription-events subscription and applies
subscription updates in our DB.

Run (example):
  python -m credits.play_rtdn_worker
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from google.cloud import pubsub_v1

from credits.credit_service import CreditService
from credits.play_subscription_events import rtdn_kind_for_notification_type
from credits.routes import _sync_subscription_from_play, _credit_verified_google_play_purchase

logger = logging.getLogger("play_rtdn_worker")
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")


def _project_id() -> str:
    project = (os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID") or "").strip()
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID is required")
    return project


def _subscription_path(subscriber: pubsub_v1.SubscriberClient) -> str:
    sub = (os.getenv("PUBSUB_PLAY_SUB_SUBSCRIPTION") or "play-subscription-events-sub").strip()
    if sub.startswith("projects/"):
        return sub
    return subscriber.subscription_path(_project_id(), sub)


def _parse_message(data: bytes) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(data.decode("utf-8"))
        if isinstance(payload, dict):
            return payload
    except Exception:
        return None
    return None


def _event_id_from_payload(payload: Dict[str, Any], message_id: str) -> str:
    sn = payload.get("subscriptionNotification") if isinstance(payload.get("subscriptionNotification"), dict) else None
    on = payload.get("oneTimeProductNotification") if isinstance(payload.get("oneTimeProductNotification"), dict) else None
    if sn:
        prefix = "sub"
        token = str(sn.get("purchaseToken") or "").strip()
        product_id = str(sn.get("subscriptionId") or "").strip()
        ntype = str(sn.get("notificationType") or "").strip()
    else:
        prefix = "one"
        token = str((on or {}).get("purchaseToken") or "").strip()
        product_id = str((on or {}).get("sku") or (on or {}).get("productId") or "").strip()
        ntype = str((on or {}).get("notificationType") or "").strip()
    et = str(payload.get("eventTimeMillis") or "").strip()
    # Deterministic id for idempotency. Includes Pub/Sub message_id fallback.
    parts = [prefix, token, product_id, ntype, et, str(message_id or "").strip()]
    return "|".join(parts)


def _safe_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except Exception:
        return None


def _process_one(
    *,
    payload: Dict[str, Any],
    message_id: str,
    credit_service: CreditService,
) -> bool:
    # RTDN test message
    if isinstance(payload.get("testNotification"), dict):
        logger.info("RTDN test notification received (message_id=%s)", message_id)
        return True

    sub_notif = payload.get("subscriptionNotification")
    one_notif = payload.get("oneTimeProductNotification")
    if not isinstance(sub_notif, dict) and not isinstance(one_notif, dict):
        logger.warning("Skipping unsupported RTDN message_id=%s payload=%s", message_id, payload)
        return True

    is_subscription = isinstance(sub_notif, dict)
    purchase_token = str(
        (sub_notif or one_notif or {}).get("purchaseToken") or ""
    ).strip()
    product_id = str(
        (sub_notif or {}).get("subscriptionId")
        or (one_notif or {}).get("sku")
        or (one_notif or {}).get("productId")
        or ""
    ).strip()
    notification_type = _safe_int((sub_notif or one_notif or {}).get("notificationType"))
    event_time_millis = _safe_int(payload.get("eventTimeMillis"))
    event_id = _event_id_from_payload(payload, message_id)

    if not purchase_token or not product_id:
        logger.warning("RTDN missing token/product (message_id=%s)", message_id)
        return True

    if is_subscription and credit_service.has_processed_play_subscription_event(event_id):
        logger.info("Duplicate RTDN ignored (event_id=%s)", event_id)
        return True
    if (not is_subscription) and credit_service.has_processed_play_onetime_event(event_id):
        logger.info("Duplicate one-time RTDN ignored (event_id=%s)", event_id)
        return True

    userid = (
        credit_service.get_user_id_by_play_purchase_token(purchase_token)
        if is_subscription
        else credit_service.get_user_id_by_play_onetime_purchase_token(purchase_token)
    )
    if userid is None:
        logger.warning(
            "No user mapped for purchase token yet. event_id=%s product_id=%s",
            event_id,
            product_id,
        )
        # Ack intentionally: avoid endless retries for unknown tokens.
        return True

    if is_subscription:
        # Accept any payment state for RTDN sync so cancelled/non-renewing states update end_date.
        sync_result = _sync_subscription_from_play(
            userid=userid,
            product_id=product_id,
            purchase_token=purchase_token,
            accept_any_payment_state=True,
        )
        credit_service.log_play_subscription_event(
            event_id=event_id,
            purchase_token=purchase_token,
            product_id=product_id,
            notification_type=notification_type,
            event_time_millis=event_time_millis,
            payload_json=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
            userid=userid,
            source="rtdn",
            event_kind=rtdn_kind_for_notification_type(notification_type),
            start_date=sync_result.get("start_date"),
            end_date=sync_result.get("end_date"),
        )
    else:
        _credit_verified_google_play_purchase(
            userid=userid,
            user_phone=None,
            user_name=None,
            purchase_token=purchase_token,
            product_id=product_id,
            order_id_hint=None,
        )
        credit_service.log_play_onetime_event(
            event_id=event_id,
            purchase_token=purchase_token,
            product_id=product_id,
            notification_type=notification_type,
            event_time_millis=event_time_millis,
            payload_json=json.dumps(payload, separators=(",", ":"), ensure_ascii=False),
        )
    logger.info(
        "Processed RTDN event_id=%s user=%s product=%s type=%s",
        event_id,
        userid,
        product_id,
        notification_type,
    )
    return True


def run_worker() -> None:
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = _subscription_path(subscriber)
    logger.info("Starting RTDN worker on subscription: %s", sub_path)
    credit_service = CreditService()

    while True:
        response = subscriber.pull(
            request={
                "subscription": sub_path,
                "max_messages": 20,
            },
            timeout=20,
        )

        received = response.received_messages or []
        if not received:
            time.sleep(1.0)
            continue

        ack_ids = []
        for rm in received:
            msg = rm.message
            message_id = str(msg.message_id or "")
            payload = _parse_message(msg.data or b"")
            if payload is None:
                logger.warning("Invalid JSON RTDN message_id=%s; acking", message_id)
                ack_ids.append(rm.ack_id)
                continue

            try:
                ok = _process_one(payload=payload, message_id=message_id, credit_service=credit_service)
                if ok:
                    ack_ids.append(rm.ack_id)
            except Exception:
                logger.exception("RTDN processing failed (message_id=%s). Will retry.", message_id)

        if ack_ids:
            subscriber.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})


if __name__ == "__main__":
    run_worker()

