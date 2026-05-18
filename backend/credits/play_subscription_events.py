"""Google Play subscription event kinds (RTDN + in-app verify/sync)."""

# Google Play subscriptionNotification.notificationType
RTDN_NOTIFICATION_KIND = {
    1: "recovered",
    2: "renewed",
    3: "canceled",
    4: "purchased",
    5: "on_hold",
    6: "grace_period",
    7: "restarted",
    8: "price_change_confirmed",
    9: "deferred",
    10: "paused",
    11: "pause_schedule_changed",
    12: "revoked",
    13: "expired",
    20: "pending_purchase_canceled",
}

RTDN_NOTIFICATION_LABEL = {
    1: "Recovered",
    2: "Renewed",
    3: "Canceled",
    4: "Purchased",
    5: "On hold",
    6: "Grace period",
    7: "Restarted",
    8: "Price change confirmed",
    9: "Deferred",
    10: "Paused",
    11: "Pause schedule changed",
    12: "Revoked",
    13: "Expired",
    20: "Pending purchase canceled",
}

APP_EVENT_KIND_LABEL = {
    "purchased": "Purchased (first sync)",
    "renewed": "Renewed (extended end)",
    "upgraded": "Plan changed",
    "synced": "Synced (no change)",
    "updated": "Updated",
    "canceled": "Canceled",
    "expired": "Expired",
}


def rtdn_kind_for_notification_type(notification_type) -> str:
    try:
        n = int(notification_type)
    except (TypeError, ValueError):
        return "unknown"
    return RTDN_NOTIFICATION_KIND.get(n, "unknown")


def display_label_for_event(source: str, event_kind: str, notification_type) -> str:
    if source == "backfill":
        base = APP_EVENT_KIND_LABEL.get(event_kind or "", (event_kind or "Unknown").replace("_", " ").title())
        return f"Backfill — {base}"
    if source == "rtdn" and notification_type is not None:
        try:
            n = int(notification_type)
            if n in RTDN_NOTIFICATION_LABEL:
                return RTDN_NOTIFICATION_LABEL[n]
        except (TypeError, ValueError):
            pass
    return APP_EVENT_KIND_LABEL.get(event_kind or "", (event_kind or "Unknown").replace("_", " ").title())
