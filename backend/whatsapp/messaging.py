"""Outbound WhatsApp Cloud API messages (text + interactive list + Flows)."""
from __future__ import annotations

import json
import logging
import os
import re
from html import unescape
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)


def _graph_messages_url() -> Tuple[str, str]:
    raw = (os.environ.get("WHATSAPP_ACCESS_TOKEN") or "").strip()
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        raw = raw[1:-1].strip()
    token = raw
    ver = (os.environ.get("WHATSAPP_GRAPH_API_VERSION") or "v22.0").strip().lstrip("/")
    return token, ver


def fetch_whatsapp_message_templates(*, status: str = "APPROVED") -> List[Dict[str, Any]]:
    """Fetch message templates for the configured WhatsApp Business Account."""
    token, ver = _graph_messages_url()
    waba_id = (
        os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID")
        or os.environ.get("WHATSAPP_WABA_ID")
        or ""
    ).strip()
    if not token or not waba_id:
        raise RuntimeError(
            "missing WHATSAPP_ACCESS_TOKEN or WHATSAPP_BUSINESS_ACCOUNT_ID"
        )

    url = f"https://graph.facebook.com/{ver}/{waba_id}/message_templates"
    params: Optional[Dict[str, Any]] = {
        "fields": "id,name,status,category,language,components",
        "limit": 100,
    }
    templates: List[Dict[str, Any]] = []
    for _ in range(20):
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=30,
        )
        if not (200 <= response.status_code < 300):
            detail = (response.text or "")[:800]
            raise RuntimeError(f"Meta {response.status_code}: {detail}")
        payload = response.json()
        rows = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(rows, list):
            templates.extend(row for row in rows if isinstance(row, dict))
        next_url = ((payload.get("paging") or {}).get("next") if isinstance(payload, dict) else None)
        if not next_url:
            break
        if not str(next_url).startswith("https://graph.facebook.com/"):
            raise RuntimeError("Meta returned an unexpected template pagination URL")
        url = str(next_url)
        params = None

    wanted = str(status or "").strip().upper()
    if wanted:
        templates = [
            row for row in templates if str(row.get("status") or "").upper() == wanted
        ]
    return templates


def truncate_whatsapp(s: str, max_len: int) -> str:
    s = (s or "").strip().replace("\n", " ")
    if len(s) <= max_len:
        return s
    if max_len <= 1:
        return s[:max_len]
    return s[: max_len - 1] + "…"


def truncate_whatsapp_interactive_body(s: str, max_len: int) -> str:
    """Like truncate_whatsapp but keeps newlines (for interactive message body)."""
    s = (s or "").strip()
    if len(s) <= max_len:
        return s
    if max_len <= 1:
        return s[:max_len]
    return s[: max_len - 1] + "…"


def format_for_whatsapp_text(text: str) -> str:
    """Convert app/web rich chat output into WhatsApp-safe plain text."""
    body = unescape(str(text or ""))
    if not body.strip():
        return ""

    # Preserve meaningful layout before dropping tags.
    body = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", body)
    body = re.sub(r"(?i)</\s*(p|div|li|h[1-6])\s*>", "\n", body)
    body = re.sub(r"(?i)<\s*li(?:\s+[^>]*)?>", "- ", body)
    body = re.sub(r"(?is)<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", body)
    body = re.sub(r"(?is)<\s*style[^>]*>.*?<\s*/\s*style\s*>", "", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = unescape(body)

    # WhatsApp supports *bold*; convert common app markdown without exposing HTML.
    body = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", body)
    body = re.sub(r"\*\*([^*\n]+)\*\*", r"*\1*", body)
    body = re.sub(r"__([^_\n]+)__", r"*\1*", body)
    body = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1 (\2)", body)

    # Collapse noisy whitespace while keeping paragraph breaks and bullets readable.
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n[ \t]+", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = re.sub(r"[ \t]{2,}", " ", body)
    return body.strip()


def send_whatsapp_text(*, to_wa_id: str, body: str, phone_number_id: str) -> bool:
    token, ver = _graph_messages_url()
    if not token or not phone_number_id:
        logger.warning("Skipping WhatsApp send: missing WHATSAPP_ACCESS_TOKEN or phone_number_id")
        return False
    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4090]},
    }
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            logger.warning("WhatsApp text send failed: %s %s", r.status_code, (r.text or "")[:500])
            return False
        return True
    except Exception as e:
        logger.exception("WhatsApp text send error: %s", e)
        return False


def send_whatsapp_template(
    *,
    to: str,
    phone_number_id: str,
    template_name: str,
    language_code: str = "en",
    body_params: Optional[List[str]] = None,
    body_named_params: Optional[Dict[str, str]] = None,
    button_payload: Optional[str] = None,
    url_button_suffix: Optional[str] = None,
    url_button_index: str = "0",
    components_override: Optional[List[Dict[str, Any]]] = None,
    return_error: bool = False,
    return_meta: bool = False,
):
    """Send an approved WhatsApp message template to a phone/wa recipient.

    body_params: positional {{1}}, {{2}}, ... values.
    body_named_params: named vars e.g. {"customer_name": "Tarun"} for {{customer_name}}.
    url_button_suffix: dynamic suffix for a URL button variable
    (e.g. template URL `https://astroroshni.com/mobile/?c=` → pass the token only).

    When return_error=True, returns (ok: bool, error: Optional[str]).
    When return_meta=True, returns (ok, error, metadata), where metadata contains
    Meta's wamid. This is additive so existing boolean and two-tuple callers keep
    their original return shape.
    """
    def result(ok: bool, error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        if return_meta:
            return ok, error, metadata
        if return_error:
            return ok, error
        return ok

    token, ver = _graph_messages_url()
    if not token or not phone_number_id:
        msg = "missing WHATSAPP_ACCESS_TOKEN or phone_number_id"
        logger.warning("Skipping WhatsApp template send: %s", msg)
        return result(False, msg)
    to_s = (to or "").strip()
    if not to_s:
        msg = "missing recipient"
        logger.warning("Skipping WhatsApp template send: %s", msg)
        return result(False, msg)
    components: List[Dict[str, Any]] = []
    body_parameter_objs: List[Dict[str, Any]] = []
    named = body_named_params or {}
    for key, value in named.items():
        name = str(key or "").strip()
        if not name:
            continue
        body_parameter_objs.append(
            {
                "type": "text",
                "parameter_name": name,
                "text": str(value or "").strip()[:1024] or "there",
            }
        )
    if not body_parameter_objs:
        for p in body_params or []:
            body_parameter_objs.append({"type": "text", "text": str(p or "").strip()[:1024]})
    if body_parameter_objs:
        components.append(
            {
                "type": "body",
                "parameters": body_parameter_objs,
            }
        )
    if button_payload:
        components.append(
            {
                "type": "button",
                "sub_type": "quick_reply",
                "index": "0",
                "parameters": [
                    {
                        "type": "payload",
                        "payload": truncate_whatsapp(str(button_payload), 200),
                    }
                ],
            }
        )
    suffix = (url_button_suffix or "").strip()
    if suffix:
        components.append(
            {
                "type": "button",
                "sub_type": "url",
                "index": str(url_button_index or "0"),
                "parameters": [
                    {
                        "type": "text",
                        "text": suffix[:2000],
                    }
                ],
            }
        )
    if components_override is not None:
        components = components_override
    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": to_s,
        "type": "template",
        "template": {
            "name": (template_name or "").strip(),
            "language": {"code": (language_code or "en").strip()},
        },
    }
    if components:
        payload["template"]["components"] = components
    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            err_text = (r.text or "")[:800]
            logger.warning(
                "WhatsApp template send failed: status=%s template=%s lang=%s to=%s body=%s",
                r.status_code,
                template_name,
                language_code,
                to_s[-4:].rjust(len(to_s), "*") if len(to_s) > 4 else "****",
                err_text,
            )
            return result(False, f"Meta {r.status_code}: {err_text}")
        try:
            response_payload = r.json() if r.content else {}
        except ValueError:
            response_payload = {}
        messages = response_payload.get("messages") if isinstance(response_payload, dict) else None
        contacts = response_payload.get("contacts") if isinstance(response_payload, dict) else None
        message_id = (
            str(messages[0].get("id") or "").strip()
            if isinstance(messages, list) and messages and isinstance(messages[0], dict)
            else ""
        )
        wa_id = (
            str(contacts[0].get("wa_id") or "").strip()
            if isinstance(contacts, list) and contacts and isinstance(contacts[0], dict)
            else ""
        )
        return result(
            True,
            None,
            {
                "message_id": message_id or None,
                "wa_id": wa_id or None,
            },
        )
    except Exception as e:
        logger.exception("WhatsApp template send error: %s", e)
        return result(False, str(e))


def send_whatsapp_interactive_list(
    *,
    to_wa_id: str,
    phone_number_id: str,
    body: str,
    button_text: str,
    section_title: str,
    rows: List[Tuple[str, str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> bool:
    """
    Interactive list (user taps button → picks a row).
    Meta limits: button ≤20 chars, body ≤4096, header/footer/section/row titles per docs;
    max 10 rows total across sections.
    rows: list of (row_id, row_title, row_description) — description may be "".
    """
    token, ver = _graph_messages_url()
    if not token or not phone_number_id:
        logger.warning("Skipping WhatsApp list send: missing WHATSAPP_ACCESS_TOKEN or phone_number_id")
        return False
    if not rows:
        return send_whatsapp_text(to_wa_id=to_wa_id, body=body, phone_number_id=phone_number_id)

    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    section_rows: List[Dict[str, Any]] = []
    for row_id, title, desc in rows[:10]:
        rid = truncate_whatsapp(str(row_id), 200)
        rt = truncate_whatsapp(str(title), 24)
        entry: Dict[str, Any] = {"id": rid, "title": rt}
        d = (desc or "").strip()
        if d:
            entry["description"] = truncate_whatsapp(d, 72)
        section_rows.append(entry)

    interactive: Dict[str, Any] = {
        "type": "list",
        "body": {"text": truncate_whatsapp(body, 4096)},
        "action": {
            "button": truncate_whatsapp(button_text, 20),
            "sections": [
                {
                    "title": truncate_whatsapp(section_title, 24),
                    "rows": section_rows,
                }
            ],
        },
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": truncate_whatsapp(header_text, 60)}
    if footer_text:
        interactive["footer"] = {"text": truncate_whatsapp(footer_text, 60)}

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "interactive",
        "interactive": interactive,
    }
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            logger.warning("WhatsApp list send failed: %s %s", r.status_code, (r.text or "")[:800])
            return False
        return True
    except Exception as e:
        logger.exception("WhatsApp list send error: %s", e)
        return False


def send_whatsapp_interactive_buttons(
    *,
    to_wa_id: str,
    phone_number_id: str,
    body: str,
    buttons: List[Tuple[str, str]],
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
) -> bool:
    """
    Interactive reply buttons (max 3). Each button: (reply_id, title); title ≤ 20 chars (Meta).
    """
    token, ver = _graph_messages_url()
    if not token or not phone_number_id:
        logger.warning("Skipping WhatsApp buttons send: missing WHATSAPP_ACCESS_TOKEN or phone_number_id")
        return False
    if not buttons:
        return send_whatsapp_text(to_wa_id=to_wa_id, body=body, phone_number_id=phone_number_id)

    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    btn_objs: List[Dict[str, Any]] = []
    for bid, title in buttons[:3]:
        btn_objs.append(
            {
                "type": "reply",
                "reply": {
                    "id": truncate_whatsapp(str(bid), 200),
                    "title": truncate_whatsapp(str(title), 20),
                },
            }
        )

    interactive: Dict[str, Any] = {
        "type": "button",
        "body": {"text": truncate_whatsapp_interactive_body(body, 1024)},
        "action": {"buttons": btn_objs},
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": truncate_whatsapp(header_text, 60)}
    if footer_text:
        interactive["footer"] = {"text": truncate_whatsapp(footer_text, 60)}

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "interactive",
        "interactive": interactive,
    }
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            logger.warning("WhatsApp buttons send failed: %s %s", r.status_code, (r.text or "")[:800])
            return False
        return True
    except Exception as e:
        logger.exception("WhatsApp buttons send error: %s", e)
        return False


def send_whatsapp_interactive_flow(
    *,
    to_wa_id: str,
    phone_number_id: str,
    body_text: str,
    flow_cta: str,
    flow_token: str,
    flow_id: Optional[str] = None,
    flow_name: Optional[str] = None,
    header_text: Optional[str] = None,
    footer_text: Optional[str] = None,
    mode: str = "published",
    flow_action: str = "navigate",
    screen: Optional[str] = None,
    screen_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    WhatsApp Flow (interactive type `flow`). User taps CTA → Flow UI opens.
    Provide either flow_id (from WhatsApp Manager) or flow_name (Cloud API).
    See: https://developers.facebook.com/docs/whatsapp/flows/guides/sendingaflow/
    """
    token, ver = _graph_messages_url()
    if not token or not phone_number_id:
        logger.warning("Skipping WhatsApp Flow send: missing WHATSAPP_ACCESS_TOKEN or phone_number_id")
        return False
    if not flow_id and not flow_name:
        logger.warning("Skipping WhatsApp Flow send: need flow_id or flow_name")
        return False

    params: Dict[str, Any] = {
        "flow_message_version": "3",
        "flow_cta": truncate_whatsapp(flow_cta, 30),
        "mode": mode if mode in ("draft", "published") else "published",
        "flow_token": truncate_whatsapp(flow_token or "unused", 200),
        "flow_action": flow_action if flow_action in ("navigate", "data_exchange") else "navigate",
    }
    if flow_id:
        params["flow_id"] = str(flow_id).strip()
    else:
        params["flow_name"] = str(flow_name).strip()

    if flow_action == "navigate" and (screen or screen_data is not None):
        fap: Dict[str, Any] = {}
        if screen:
            fap["screen"] = screen
        if screen_data is not None and len(screen_data) > 0:
            fap["data"] = screen_data
        if fap:
            params["flow_action_payload"] = fap

    interactive: Dict[str, Any] = {
        "type": "flow",
        "body": {"text": truncate_whatsapp(body_text, 4096)},
        "action": {"name": "flow", "parameters": params},
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": truncate_whatsapp(header_text, 60)}
    if footer_text:
        interactive["footer"] = {"text": truncate_whatsapp(footer_text, 60)}

    payload: Dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_wa_id,
        "type": "interactive",
        "interactive": interactive,
    }
    url = f"https://graph.facebook.com/{ver}/{phone_number_id}/messages"
    try:
        r = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if not (200 <= r.status_code < 300):
            logger.warning("WhatsApp Flow send failed: %s %s", r.status_code, (r.text or "")[:800])
            return False
        return True
    except Exception as e:
        logger.exception("WhatsApp Flow send error: %s", e)
        return False
