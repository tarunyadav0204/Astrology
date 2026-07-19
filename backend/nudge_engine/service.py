"""
Orchestrate daily nudge scan.

The dispatch role should only discover events and enqueue bounded worker tasks.
Inline delivery remains as a last-resort fallback when task queueing is disabled.
"""
import logging
from datetime import date
from typing import Any, Dict, Optional

from . import db
from .scanner import scan
from .dedupe import resolve_and_cap
from .delivery import deliver
from .models import NudgeEvent

logger = logging.getLogger(__name__)


def _fetch_user_id_page(*, after_userid: int, limit: int) -> list[int]:
    """Short-lived read so we never hold users locks across Cloud Tasks I/O."""
    with db.get_conn() as conn:
        user_ids = db.get_user_ids_after(conn, after_userid=after_userid, limit=limit)
        try:
            conn.commit()
        except Exception:
            pass
        return user_ids


def _enqueue_scan_batches(events: list[NudgeEvent], target_date: date) -> Dict[str, Any]:
    from .task_queue import enqueue_nudge_task, nudge_tasks_are_isolated, nudge_tasks_enabled

    if not nudge_tasks_enabled():
        raise RuntimeError("NUDGE_TASKS_ENABLED is false")
    if not nudge_tasks_are_isolated():
        raise RuntimeError("NUDGE_TASKS target is not isolated from public API host")

    batch_size = max(1, min(int(__import__("os").getenv("NUDGE_SCAN_BATCH_SIZE", "50")), 1000))
    pages_scanned = 0
    batches_enqueued = 0
    enqueue_failed = 0
    users_targeted = 0

    for event_index, event in enumerate(events):
        if event.user_ids is None:
            after_userid = 0
            page_index = 0
            while True:
                user_ids = _fetch_user_id_page(after_userid=after_userid, limit=batch_size)
                if not user_ids:
                    break
                pages_scanned += 1
                users_targeted += len(user_ids)
                task_id = (
                    f"{target_date.isoformat()}-{event.trigger_id}-{event_index}-"
                    f"{page_index}-{user_ids[0]}-{user_ids[-1]}"
                )
                ok = enqueue_nudge_task(
                    task_kind="scan-delivery-batch",
                    task_id=task_id,
                    payload={
                        "scan_date": target_date.isoformat(),
                        "event": event.to_payload(),
                        "user_ids": user_ids,
                    },
                )
                if ok:
                    batches_enqueued += 1
                else:
                    enqueue_failed += 1
                after_userid = int(user_ids[-1])
                page_index += 1
        else:
            concrete_ids = [int(uid) for uid in (event.user_ids or []) if str(uid).isdigit()]
            for batch_index in range(0, len(concrete_ids), batch_size):
                user_ids = concrete_ids[batch_index : batch_index + batch_size]
                users_targeted += len(user_ids)
                task_id = (
                    f"{target_date.isoformat()}-{event.trigger_id}-{event_index}-"
                    f"{batch_index // batch_size}"
                )
                ok = enqueue_nudge_task(
                    task_kind="scan-delivery-batch",
                    task_id=task_id,
                    payload={
                        "scan_date": target_date.isoformat(),
                        "event": event.to_payload(),
                        "user_ids": user_ids,
                    },
                )
                if ok:
                    batches_enqueued += 1
                else:
                    enqueue_failed += 1

    return {
        "queued": True,
        "batch_size": batch_size,
        "batches_enqueued": batches_enqueued,
        "enqueue_failed": enqueue_failed,
        "users_targeted": users_targeted,
        "pages_scanned": pages_scanned,
    }


def run_nudge_scan(target_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Run the full pipeline for target_date (default: today).
    Returns a summary dict: events_found, users_targeted, delivered, error (if any).
    """
    if target_date is None:
        target_date = date.today()
    summary: Dict[str, Any] = {
        "date": target_date.isoformat(),
        "events_found": 0,
        "users_targeted": 0,
        "delivered": 0,
        "error": None,
    }
    lock_cm = None
    lock_conn = None
    lock_held = False
    try:
        try:
            lock_cm = db.get_conn()
            lock_conn = lock_cm.__enter__()
            db.init_nudge_tables(lock_conn)
            if not db.try_advisory_lock(lock_conn, "nudge_scan_daily"):
                summary["skipped"] = "already_running"
                logger.warning("Nudge scan skipped for %s: already running", target_date)
                return summary
            lock_held = True
            # Session advisory locks survive commit; end the txn so we are not
            # idle-in-transaction for the whole scan (hours of fan-out).
            try:
                lock_conn.commit()
            except Exception:
                pass
        except Exception as e:
            logger.exception("Init nudge tables failed: %s", e)
            summary["error"] = str(e)
            return summary

        events = scan(target_date)
        summary["events_found"] = len(events)
        if not events:
            logger.info("Nudge scan for %s: no events.", target_date)
            return summary

        try:
            queued_summary = _enqueue_scan_batches(events, target_date)
            summary.update(queued_summary)
            summary["users_targeted"] = int(queued_summary.get("users_targeted") or 0)
            summary["delivered"] = 0
            logger.info(
                "Nudge scan for %s queued: events=%s targeted=%s batches=%s enqueue_failed=%s",
                target_date,
                summary["events_found"],
                summary["users_targeted"],
                queued_summary.get("batches_enqueued"),
                queued_summary.get("enqueue_failed"),
            )
            return summary
        except Exception as queue_exc:
            logger.exception("Nudge scan queue fan-out failed for %s: %s", target_date, queue_exc)
            fail_closed = (
                __import__("os").getenv("NUDGE_SCAN_REQUIRE_TASKS", "true").strip().lower()
                in {"1", "true", "yes", "on"}
            )
            if fail_closed:
                summary["queued"] = False
                summary["error"] = f"queue_fanout_failed: {queue_exc}"
                logger.error(
                    "Nudge scan for %s aborted because queue fan-out failed and NUDGE_SCAN_REQUIRE_TASKS=true",
                    target_date,
                )
                return summary

        to_send = resolve_and_cap(events, target_date)
        summary["users_targeted"] = len(to_send)
        delivered = deliver(target_date, to_send)
        summary["delivered"] = delivered
        summary["queued"] = False
        logger.info(
            "Nudge scan for %s inline fallback: events=%s, targeted=%s, delivered=%s",
            target_date, summary["events_found"], summary["users_targeted"], delivered,
        )
    except Exception as e:
        logger.exception("Nudge scan failed for %s: %s", target_date, e)
        summary["error"] = str(e)
    finally:
        if lock_held and lock_conn is not None:
            try:
                db.advisory_unlock(lock_conn, "nudge_scan_daily")
            except Exception:
                pass
            try:
                lock_conn.commit()
            except Exception:
                try:
                    lock_conn.rollback()
                except Exception:
                    pass
        if lock_cm is not None:
            try:
                lock_cm.__exit__(None, None, None)
            except Exception:
                pass
    return summary
