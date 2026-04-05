"""
Plain-text email via SMTP. Same configuration as OTP (SMTP_* env vars).
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import List, Union

logger = logging.getLogger(__name__)


def send_plain_text_email(
    to: Union[str, List[str]],
    subject: str,
    body: str,
) -> bool:
    """
    Send a single plain-text email. Returns True if SMTP accepted the message.
    If SMTP is not configured, logs a warning and returns False.
    """
    recipients: List[str]
    if isinstance(to, str):
        recipients = [to] if to.strip() else []
    else:
        recipients = [x.strip() for x in to if x and str(x).strip()]
    if not recipients:
        return False

    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL") or smtp_user
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

    if not smtp_host or not from_email:
        logger.warning("Email not sent: SMTP env not configured")
        return False

    try:
        message = MIMEText(body, "plain", "utf-8")
        message["Subject"] = subject
        message["From"] = from_email
        message["To"] = ", ".join(recipients)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            if use_tls:
                server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.sendmail(from_email, recipients, message.as_string())
        return True
    except Exception:
        logger.exception("Failed sending email to %s", recipients)
        return False
