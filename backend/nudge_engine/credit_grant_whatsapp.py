"""Isolated WhatsApp sender for permanent-credit grant notices."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Iterable

from whatsapp.messaging import send_whatsapp_template
from credits.credit_grant_campaigns import (
    mark_credit_grant_whatsapp_result,
    mark_credit_grant_whatsapp_suppressed,
    opted_out_credit_grant_whatsapp_userids,
)

logger = logging.getLogger(__name__)


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", str(phone or ""))


def process_credit_grant_whatsapp_batch(*, recipients: Iterable[Dict[str, Any]], template_name: str, language: str) -> Dict[str, int]:
    """Send body {{1}} credits, {{2}} balance, and URL {{1}} campaign key."""
    phone_number_id = (os.getenv("WHATSAPP_NUDGE_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID") or "").strip()
    if not phone_number_id:
        raise RuntimeError("WHATSAPP_NUDGE_PHONE_NUMBER_ID or WHATSAPP_PHONE_NUMBER_ID is required")
    accepted = failed = skipped = 0
    recipients = list(recipients)
    opted_out_userids = opted_out_credit_grant_whatsapp_userids(
        recipient["userid"] for recipient in recipients if recipient.get("userid") is not None
    )
    for recipient in recipients:
        campaign_id = int(recipient["campaign_id"])
        userid = int(recipient["userid"])
        if userid in opted_out_userids:
            mark_credit_grant_whatsapp_suppressed(campaign_id, userid)
            skipped += 1
            continue
        phone = _digits(recipient.get("phone", ""))
        if len(phone) < 8:
            skipped += 1
            continue
        ok, error, meta = send_whatsapp_template(
            to=phone, phone_number_id=phone_number_id, template_name=template_name,
            language_code=language, body_params=[str(int(recipient["credits"])), str(int(recipient["balance"]))],
            url_button_suffix=f"cg-{campaign_id}", return_meta=True,
        )
        message_id = str((meta or {}).get("message_id") or "") or None
        mark_credit_grant_whatsapp_result(campaign_id, userid, accepted=ok, message_id=message_id, error=error)
        if ok:
            accepted += 1
        else:
            failed += 1
            logger.warning("Credit grant WhatsApp rejected userid=%s: %s", recipient.get("userid"), error)
    return {"accepted": accepted, "failed": failed, "skipped": skipped}
