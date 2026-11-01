"""MTalkz SMS delivery-report parsing and persistence for campaign deliveries."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from db import execute


_DELIVERED = {"delivered", "delivery_success", "success"}
_SENT = {"sent", "submitted", "queued", "accepted", "in_progress"}
_FAILED = {
    "failed", "failure", "undelivered", "rejected", "expired", "dnd",
    "preference_not_matched", "preference not matched", "invalid_number",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _first(entry: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if value not in (None, ""):
            return _text(value)
    return ""


def _status(value: Any) -> Optional[str]:
    normalized = _text(value).lower().replace("-", "_")
    if normalized in _DELIVERED:
        return "delivered"
    if normalized in _SENT:
        return "sent"
    if normalized in _FAILED or "fail" in normalized or "reject" in normalized or "undeliver" in normalized:
        return "failed"
    return None


def parse_mtalkz_dlr(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Normalise field-name variants used by MTalkz DLR push callbacks."""
    candidates: Iterable[Any] = (
        payload.get("data")
        or payload.get("reports")
        or payload.get("dlr")
        or [payload]
    )
    if isinstance(candidates, dict):
        candidates = [candidates]
    if not isinstance(candidates, list):
        candidates = [payload]

    reports: List[Dict[str, str]] = []
    for raw in candidates:
        if not isinstance(raw, dict):
            continue
        message_id = _first(raw, "message_id", "messageId", "messageid", "msg_id", "msgid", "id")
        status = _status(_first(raw, "status", "delivery_status", "deliveryStatus", "dlr_status", "dlrStatus"))
        if not message_id or not status:
            continue
        error = _first(raw, "error", "error_message", "errorMessage", "reason", "description", "remarks")
        reports.append({"message_id": message_id, "status": status, "error": error[:1000]})
    return reports


def apply_mtalkz_dlr(conn, report: Dict[str, str]) -> int:
    """Apply one provider report without allowing an old failure to undo delivery."""
    status = report["status"]
    now = datetime.now(timezone.utc)
    cur = execute(
        conn,
        """
        UPDATE nudge_deliveries
        SET meta_status = CASE
                WHEN meta_delivered_at IS NOT NULL THEN 'delivered'
                WHEN %s = 'delivered' THEN 'delivered'
                WHEN %s = 'failed' THEN 'failed'
                WHEN %s = 'sent' AND COALESCE(meta_status, '') NOT IN ('delivered', 'failed') THEN 'sent'
                ELSE COALESCE(meta_status, 'accepted')
            END,
            meta_delivered_at = CASE WHEN %s = 'delivered'
                THEN COALESCE(meta_delivered_at, %s) ELSE meta_delivered_at END,
            meta_sent_at = CASE WHEN %s IN ('sent', 'delivered')
                THEN COALESCE(meta_sent_at, %s) ELSE meta_sent_at END,
            meta_failed_at = CASE WHEN %s = 'failed' AND meta_delivered_at IS NULL
                THEN COALESCE(meta_failed_at, %s) ELSE meta_failed_at END,
            meta_error = CASE WHEN %s = 'failed' THEN NULLIF(%s, '') ELSE meta_error END,
            meta_status_updated_at = GREATEST(COALESCE(meta_status_updated_at, %s), %s)
        WHERE channel = 'sms' AND meta_message_id = %s
        """,
        (
            status, status, status,
            status, now,
            status, now,
            status, now,
            status, report.get("error") or "",
            now, now,
            report["message_id"],
        ),
    )
    return int(cur.rowcount or 0)
