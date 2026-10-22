"""DLT-locked SMS delivery for marketing campaigns."""
from __future__ import annotations

import os
import re
from typing import Any, Dict, Optional, Tuple

import requests

PARTNER_PORTRAIT_TEMPLATE_KEY = "partner_portrait"
PARTNER_PORTRAIT_DLT_TEMPLATE_ID = "1077020640025488277"
PARTNER_PORTRAIT_BODY = (
    "Hi {name}, curious about the relationship patterns and partner qualities reflected in "
    "your birth chart? Explore your personalised Partner Portrait on AstroRoshni: "
    "https://astroroshni.com/go/partner-portrait"
)


def partner_portrait_template() -> Dict[str, str]:
    return {
        "key": PARTNER_PORTRAIT_TEMPLATE_KEY,
        "dlt_template_id": PARTNER_PORTRAIT_DLT_TEMPLATE_ID,
        "body": PARTNER_PORTRAIT_BODY,
        "landing_url": "https://astroroshni.com/go/partner-portrait",
    }


def campaign_sms_configuration() -> Dict[str, Any]:
    """Safe public configuration for the admin console; never exposes secrets."""
    mtalkz_required = ("MTALKZ_API_KEY", "MTALKZ_SENDER_ID", "MTALKZ_PE_ID")
    msg91_required = ("MSG91_SMS_AUTHKEY", "MSG91_SMS_TEMPLATE_ID")
    mtalkz_ready = all(bool((os.getenv(key) or "").strip()) for key in mtalkz_required)
    msg91_ready = all(bool((os.getenv(key) or "").strip()) for key in msg91_required)
    return {
        "primary_provider": "mtalkz" if mtalkz_ready else ("msg91" if msg91_ready else None),
        "fallback_provider": "msg91" if mtalkz_ready and msg91_ready else None,
        "configured": mtalkz_ready or msg91_ready,
        "providers": {
            "mtalkz": {
                "configured": mtalkz_ready,
                "sender_id": (os.getenv("MTALKZ_SENDER_ID") or "").strip() or None,
                "pe_id": (os.getenv("MTALKZ_PE_ID") or "").strip() or None,
                "required_environment": mtalkz_required,
            },
            "msg91": {
                "configured": msg91_ready,
                "template_id": (os.getenv("MSG91_SMS_TEMPLATE_ID") or "").strip() or None,
                "required_environment": msg91_required,
            },
        },
        "template": partner_portrait_template(),
    }


def _india_mobile(phone: str) -> Optional[str]:
    digits = "".join(char for char in str(phone or "") if char.isdigit())
    if len(digits) == 10 and digits[0] in "6789":
        return f"91{digits}"
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return digits
    return None


def _dlt_name(value: str) -> str:
    """The approved DLT variable is alphanumeric; never send unapproved text."""
    return re.sub(r"[^A-Za-z0-9]", "", str(value or ""))[:30] or "there"


def _send_mtalkz(*, mobile: str, name: str) -> Tuple[bool, Optional[str], Dict[str, str]]:
    template = partner_portrait_template()
    payload = {
        "apikey": os.getenv("MTALKZ_API_KEY", "").strip(),
        "senderid": os.getenv("MTALKZ_SENDER_ID", "").strip(),
        "number": mobile,
        "message": template["body"].format(name=_dlt_name(name)),
        "template_id": template["dlt_template_id"],
        "pe_id": os.getenv("MTALKZ_PE_ID", "").strip(),
        "format": "json",
    }
    endpoint = (os.getenv("MTALKZ_SMS_URL") or "https://msg.mtalkz.com/V2/http-api-post.php").strip()
    try:
        response = requests.post(endpoint, json=payload, timeout=(3, 12))
        if not response.ok:
            return False, f"SMS provider returned HTTP {response.status_code}", {}
        data = response.json()
        rows = data.get("data") if isinstance(data, dict) else None
        row = rows[0] if isinstance(rows, list) and rows else {}
        message_id = str((row or {}).get("id") or "").strip()
        accepted = str((row or {}).get("status") or "").upper() in {"SUBMITTED", "SENT", "QUEUED"}
        if not accepted or not message_id:
            return False, "MTalkz did not accept the DLT submission", {"provider": "mtalkz"}
        return True, None, {"message_id": message_id, "recipient": mobile, "provider": "mtalkz"}
    except requests.RequestException as exc:
        return False, f"MTalkz request failed: {type(exc).__name__}", {"provider": "mtalkz"}
    except ValueError:
        return False, "MTalkz returned an invalid response", {"provider": "mtalkz"}


def _send_msg91(*, mobile: str, name: str) -> Tuple[bool, Optional[str], Dict[str, str]]:
    """Submit the matching MSG91 Flow template as the provider fallback.

    MSG91 needs its own Flow template ID; a DLT template ID cannot be reused as
    an MSG91 Flow ID. Configure the Flow with one ``VAR1`` variable and the
    same approved Airtel DLT content.
    """
    authkey = (os.getenv("MSG91_SMS_AUTHKEY") or "").strip()
    template_id = (os.getenv("MSG91_SMS_TEMPLATE_ID") or "").strip()
    if not authkey or not template_id:
        return False, "MSG91 fallback is not configured", {"provider": "msg91"}
    try:
        response = requests.post(
            (os.getenv("MSG91_SMS_URL") or "https://control.msg91.com/api/v5/flow").strip(),
            headers={"accept": "application/json", "content-type": "application/json", "authkey": authkey},
            json={
                "template_id": template_id,
                "short_url": "0",
                "realTimeResponse": "1",
                "recipients": [{"mobiles": mobile, "VAR1": _dlt_name(name)}],
            },
            timeout=(3, 12),
        )
        if not response.ok:
            return False, f"MSG91 returned HTTP {response.status_code}", {"provider": "msg91"}
        data = response.json()
        accepted = isinstance(data, dict) and (
            str(data.get("type") or "").lower() == "success" or data.get("success") is True
        )
        message_id = str(data.get("request_id") or data.get("id") or "").strip() if isinstance(data, dict) else ""
        if not accepted:
            return False, "MSG91 did not accept the DLT submission", {"provider": "msg91"}
        return True, None, {"message_id": message_id or f"msg91-{mobile}", "recipient": mobile, "provider": "msg91"}
    except requests.RequestException as exc:
        return False, f"MSG91 request failed: {type(exc).__name__}", {"provider": "msg91"}
    except ValueError:
        return False, "MSG91 returned an invalid response", {"provider": "msg91"}


def send_partner_portrait_sms(*, phone: str, name: str) -> Tuple[bool, Optional[str], Dict[str, str]]:
    """Submit through MTalkz, then MSG91 if the primary provider rejects it."""
    mobile = _india_mobile(phone)
    if not mobile:
        return False, "Recipient has no valid Indian mobile number", {}
    config = campaign_sms_configuration()
    if not config["configured"]:
        return False, "No SMS campaign provider is configured", {}
    if config["providers"]["mtalkz"]["configured"]:
        ok, error, meta = _send_mtalkz(mobile=mobile, name=name)
        if ok or not config["providers"]["msg91"]["configured"]:
            return ok, error, meta
        fallback_ok, fallback_error, fallback_meta = _send_msg91(mobile=mobile, name=name)
        if fallback_ok:
            fallback_meta["fallback_from"] = "mtalkz"
            return True, None, fallback_meta
        return False, f"{error}; fallback: {fallback_error}", fallback_meta
    return _send_msg91(mobile=mobile, name=name)
