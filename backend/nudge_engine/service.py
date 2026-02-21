"""
Orchestrate daily nudge scan: ensure tables exist, scan triggers, dedupe, deliver.
Full exception handling and logging.
"""
import logging
from datetime import date
from typing import Any, Dict, Optional

from . import db
from .scanner import scan
from .dedupe import resolve_and_cap
from .delivery import deliver

logger = logging.getLogger(__name__)


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
    try:
        conn = db.get_conn()
        try:
            db.init_nudge_tables(conn)
        except Exception as e:
            logger.exception("Init nudge tables failed: %s", e)
            summary["error"] = str(e)
            return summary
        finally:
            conn.close()

        events = scan(target_date)
        summary["events_found"] = len(events)
        if not events:
            logger.info("Nudge scan for %s: no events.", target_date)
            return summary

        to_send = resolve_and_cap(events, target_date)
        summary["users_targeted"] = len(to_send)
        delivered = deliver(target_date, to_send)
        summary["delivered"] = delivered
        logger.info(
            "Nudge scan for %s: events=%s, targeted=%s, delivered=%s",
            target_date, summary["events_found"], summary["users_targeted"], delivered,
        )
    except Exception as e:
        logger.exception("Nudge scan failed for %s: %s", target_date, e)
        summary["error"] = str(e)
    return summary
