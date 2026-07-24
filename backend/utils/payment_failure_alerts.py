"""Best-effort, deduplicated operational email alerts for payment failures."""
from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, Optional

from utils.smtp_mail import send_plain_text_email

logger = logging.getLogger(__name__)

DEFAULT_RECIPIENTS = (
    "tarun.yadav@gmail.com",
    "anilasnani@gmail.com",
)
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="payment-alert")
_SAFE_VALUE_RE = re.compile(r"[^A-Za-z0-9@._:+/ -]")


def _recipients() -> list[str]:
    configured = (os.getenv("PAYMENT_FAILURE_ALERT_EMAILS") or "").strip()
    values: Iterable[str] = configured.split(",") if configured else DEFAULT_RECIPIENTS
    return list(dict.fromkeys(x.strip() for x in values if x and x.strip()))


def _safe(value: Any, limit: int = 300) -> str:
    text = str(value or "").replace("\n", " ").replace("\r", " ").strip()
    return _SAFE_VALUE_RE.sub("?", text)[:limit] or "n/a"


def _dedupe_key(
    *,
    provider: str,
    stage: str,
    reference_id: Optional[str],
    userid: Optional[int],
) -> str:
    # Missing-reference failures (for example provider order creation) are grouped
    # into 15-minute buckets so an outage cannot flood the operational inbox.
    reference = _safe(reference_id, 160)
    if reference == "n/a":
        reference = f"bucket:{int(time.time()) // 900}"
    raw = "|".join(
        [
            _safe(provider, 40).lower(),
            _safe(stage, 80).lower(),
            reference,
            str(userid or "unknown"),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _claim_alert(
    dedupe_key: str,
    provider: str,
    stage: str,
    reference_id: str,
    userid: Optional[int],
) -> Optional[int]:
    """Return row id when claimed, 0 when duplicate, None when DB is unavailable."""
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            if userid is not None:
                rate_cur = execute(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM payment_failure_alerts
                    WHERE userid = ?
                      AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
                    """,
                    (int(userid),),
                )
                rate_row = rate_cur.fetchone()
                if rate_row and int(rate_row[0] or 0) >= 5:
                    conn.rollback()
                    logger.warning("Payment failure email rate-limited user=%s", userid)
                    return 0
            cur = execute(
                conn,
                """
                INSERT INTO payment_failure_alerts (
                    dedupe_key, provider, stage, userid, reference_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING id
                """,
                (dedupe_key, provider, stage, int(userid) if userid is not None else None, reference_id or None),
            )
            row = cur.fetchone()
            conn.commit()
            return int(row[0]) if row else 0
    except Exception:
        logger.exception("Could not claim payment failure alert; sending without DB dedupe")
        return None


def _mark_delivery(alert_id: Optional[int], sent: bool) -> None:
    if not alert_id:
        return
    try:
        from db import get_conn, execute

        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE payment_failure_alerts
                SET email_sent = ?,
                    email_attempted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (bool(sent), int(alert_id)),
            )
            conn.commit()
    except Exception:
        logger.exception("Could not mark payment failure alert delivery id=%s", alert_id)


def _deliver_payment_failure_alert(payload: Dict[str, Any]) -> bool:
    provider = _safe(payload.get("provider"), 40)
    stage = _safe(payload.get("stage"), 80)
    userid = payload.get("userid")
    reference_id = _safe(payload.get("reference_id"), 160)
    error_code = _safe(payload.get("error_code"), 120)
    dedupe_key = _dedupe_key(
        provider=provider,
        stage=stage,
        reference_id=reference_id,
        userid=userid,
    )
    alert_id = _claim_alert(dedupe_key, provider, stage, reference_id, userid)
    if alert_id == 0:
        return False

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    lines = [
        "AstroRoshni payment failure",
        "",
        f"Provider: {provider}",
        f"Stage: {stage}",
        f"User ID: {_safe(userid, 40)}",
        f"Reference: {reference_id}",
        f"Product: {_safe(payload.get('product_id'), 120)}",
        f"Error: {error_code}",
        f"Detail: {_safe(payload.get('detail'), 500)}",
    ]
    for key, value in sorted(metadata.items()):
        if "token" in str(key).lower() or "secret" in str(key).lower() or "signature" in str(key).lower():
            continue
        lines.append(f"{_safe(key, 80)}: {_safe(value, 300)}")
    body = "\n".join(lines)
    subject = f"[AstroRoshni Payment Failure] {provider} · {stage}"
    sent = send_plain_text_email(_recipients(), subject, body)
    _mark_delivery(alert_id, sent)
    return sent


def notify_payment_failure(
    *,
    provider: str,
    stage: str,
    userid: Optional[int] = None,
    reference_id: Optional[str] = None,
    product_id: Optional[str] = None,
    error_code: str = "payment_failure",
    detail: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Queue an operational alert without delaying or changing payment handling."""
    payload = {
        "provider": provider,
        "stage": stage,
        "userid": userid,
        "reference_id": reference_id,
        "product_id": product_id,
        "error_code": error_code,
        "detail": detail,
        "metadata": metadata or {},
    }
    try:
        _EXECUTOR.submit(_deliver_payment_failure_alert, payload)
    except Exception:
        logger.exception("Could not queue payment failure alert")
