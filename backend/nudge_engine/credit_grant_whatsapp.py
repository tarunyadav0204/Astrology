"""Isolated WhatsApp sender for permanent-credit grant notices."""
from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, Iterable

from whatsapp.messaging import send_whatsapp_template

logger = logging.getLogger(__name__)


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", str(phone or ""))


def process_credit_grant_whatsapp_batch(*, recipients: Iterable[Dict[str, Any]], template_name: str, language: str) -> Dict[str, int]:
    """Send approved two-body-variable template: {{1}} granted, {{2}} balance."""
    phone_number_id = (os.getenv("WHATSAPP_NUDGE_PHONE_NUMBER_ID") or os.getenv("WHATSAPP_PHONE_NUMBER_ID") or "").strip()
    if not phone_number_id:
        raise RuntimeError("WHATSAPP_NUDGE_PHONE_NUMBER_ID or WHATSAPP_PHONE_NUMBER_ID is required")
    accepted = failed = skipped = 0
    for recipient in recipients:
        phone = _digits(recipient.get("phone", ""))
        if len(phone) < 8:
            skipped += 1
            continue
        ok, error = send_whatsapp_template(
            to=phone, phone_number_id=phone_number_id, template_name=template_name,
            language_code=language, body_params=[str(int(recipient["credits"])), str(int(recipient["balance"]))],
            return_error=True,
        )
        if ok:
            accepted += 1
        else:
            failed += 1
            logger.warning("Credit grant WhatsApp rejected userid=%s: %s", recipient.get("userid"), error)
    return {"accepted": accepted, "failed": failed, "skipped": skipped}
