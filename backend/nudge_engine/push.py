"""
Send push notifications via Expo Push API.
Uses stdlib urllib; no extra dependencies.
Token format: ExponentPushToken[xxxx] (from expo-notifications in the app).
"""
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_expo_push(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    sound: str = "default",
) -> bool:
    """
    Send one notification to an Expo push token.
    Returns True if the request was accepted by Expo (HTTP 200), False otherwise.
    """
    token = (token or "").strip()
    if not token or not token.startswith("ExponentPushToken["):
        logger.warning("Invalid or non-Expo push token (expected ExponentPushToken[...])")
        return False
    payload = {
        "to": token,
        "title": title[:100] if title else "",
        "body": body[:200] if body else "",
        "sound": sound,
        "data": data or {},
    }
    try:
        req = urllib.request.Request(
            EXPO_PUSH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                logger.warning("Expo push returned status %s", resp.status)
                return False
            return True
    except urllib.error.HTTPError as e:
        logger.warning("Expo push HTTP error %s: %s", e.code, e.read())
        return False
    except Exception as e:
        logger.exception("Expo push failed: %s", e)
        return False
