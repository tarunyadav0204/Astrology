"""
Email as a nudge channel: HTML wrapper around the nudge copy with a CTA
tracking link (GET /api/nudge/r/{delivery_group_id} → click log + redirect).
Uses the same SMTP configuration as OTP/support emails.
"""
from __future__ import annotations

import html
import logging
import os
from typing import Optional

from db import execute
from utils.smtp_mail import send_html_email

logger = logging.getLogger(__name__)


def _public_base_url() -> str:
    return (
        os.getenv("PUBLIC_API_BASE_URL")
        or os.getenv("NUDGE_TASKS_TARGET_BASE_URL")
        or "https://astroroshni.com"
    ).strip().rstrip("/")


def build_cta_tracking_url(delivery_group_id: str) -> str:
    return f"{_public_base_url()}/api/nudge/r/{str(delivery_group_id).strip()}"


def get_email_for_user(conn, userid: int) -> Optional[str]:
    try:
        cur = execute(
            conn,
            "SELECT COALESCE(NULLIF(TRIM(email), ''), '') FROM users WHERE userid = %s",
            (int(userid),),
        )
        row = cur.fetchone()
    except Exception as e:
        logger.warning("Email nudge lookup failed user=%s: %s", userid, e)
        return None
    email = str(row[0]).strip() if row and row[0] else ""
    return email or None


def _build_html(title: str, body: str, question: Optional[str], cta_url: str) -> str:
    title_h = html.escape((title or "").strip())
    body_h = html.escape((body or "").strip()).replace("\n", "<br/>")
    question_block = ""
    q = (question or "").strip()
    if q:
        question_block = f"""
        <div style="margin:16px 0;padding:12px 16px;background:#f6f1ff;border-left:4px solid #6c4bd8;border-radius:6px;">
          <div style="font-size:13px;color:#6c4bd8;font-weight:600;margin-bottom:4px;">Suggested question to ask in chat</div>
          <div style="font-size:14px;color:#333;">{html.escape(q)}</div>
        </div>"""
    return f"""<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f4f4f7;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;">
    <div style="max-width:560px;margin:0 auto;padding:24px 16px;">
      <div style="background:#ffffff;border-radius:12px;padding:28px 24px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        <div style="font-size:13px;letter-spacing:1px;color:#6c4bd8;font-weight:700;margin-bottom:12px;">ASTROROSHNI</div>
        <h2 style="margin:0 0 12px;font-size:20px;color:#1c1c28;">{title_h}</h2>
        <p style="margin:0 0 8px;font-size:15px;line-height:1.6;color:#444;">{body_h}</p>
        {question_block}
        <a href="{html.escape(cta_url)}"
           style="display:inline-block;margin-top:16px;padding:12px 28px;background:#6c4bd8;color:#ffffff;
                  text-decoration:none;border-radius:8px;font-size:15px;font-weight:600;">
          Continue in chat
        </a>
      </div>
      <p style="text-align:center;font-size:12px;color:#999;margin-top:16px;">
        You received this because you use AstroRoshni.
      </p>
    </div>
  </body>
</html>"""


def send_nudge_email(
    conn,
    *,
    userid: int,
    title: str,
    body: str,
    question: Optional[str],
    delivery_group_id: str,
) -> bool:
    """Best-effort email nudge. Returns True only when SMTP accepted the message."""
    to_email = get_email_for_user(conn, int(userid))
    if not to_email:
        return False
    cta_url = build_cta_tracking_url(delivery_group_id)
    subject = (title or "").strip()[:180] or "A message from AstroRoshni"
    text_parts = [(title or "").strip(), "", (body or "").strip()]
    q = (question or "").strip()
    if q:
        text_parts += ["", "Suggested question to ask in chat:", q]
    text_parts += ["", f"Continue in chat: {cta_url}"]
    try:
        return bool(
            send_html_email(
                to_email,
                subject,
                _build_html(title, body, question, cta_url),
                "\n".join(text_parts).strip(),
            )
        )
    except Exception as e:
        logger.warning("Email nudge send failed user=%s: %s", userid, e)
        return False
