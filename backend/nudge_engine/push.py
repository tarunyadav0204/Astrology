"""
Send push notifications via Expo Push API.
Uses stdlib urllib; no extra dependencies.
Token format: ExponentPushToken[xxxx] (from expo-notifications in the app).
"""
import gzip
import json
import logging
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"

# Expo accepts up to 100 messages per request (https://docs.expo.dev/push-notifications/sending-notifications/).
_EXPO_BATCH_SIZE = 100

# Do not send Accept-Encoding: gzip — urllib does not always decompress the body before
# .read(), and json.loads would fail on binary gzip. If we ever get gzip anyway, decode below.


def _expo_response_body_text(resp) -> str:
    """Read HTTP response body as UTF-8 text, decompressing gzip when needed."""
    raw = resp.read()
    if not raw:
        return ""
    enc = ""
    try:
        gh = getattr(resp, "getheader", None)
        if callable(gh):
            enc = (gh("Content-Encoding") or "").lower()
    except Exception:
        pass
    if not enc:
        try:
            enc = (resp.headers.get("Content-Encoding") or "").lower()
        except Exception:
            try:
                enc = (resp.info().get("Content-Encoding") or "").lower()
            except Exception:
                pass
    if "gzip" in enc or (len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B):
        try:
            raw = gzip.decompress(raw)
        except Exception as e:
            logger.warning("Expo push: gzip decompress failed: %s", e)
            return ""
    return raw.decode("utf-8", errors="replace")


def send_expo_push_messages(messages: List[Dict[str, Any]], timeout: int = 45) -> List[bool]:
    """
    Send many notifications via Expo in batches of up to 100 per HTTP request.
    `messages` is a list of dicts in Expo's push message shape (to, title, body, sound, data, ...).
    Returns a list of bool, one per input message (True if Expo reported status ok for that entry).
    """
    if not messages:
        return []
    out: List[bool] = []
    for i in range(0, len(messages), _EXPO_BATCH_SIZE):
        chunk = messages[i : i + _EXPO_BATCH_SIZE]
        try:
            req = urllib.request.Request(
                EXPO_PUSH_URL,
                data=json.dumps(chunk).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    logger.warning("Expo batch push returned status %s", resp.status)
                    out.extend([False] * len(chunk))
                    continue
                raw = _expo_response_body_text(resp)
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    preview = (raw[:200] + "…") if len(raw) > 200 else raw
                    logger.warning(
                        "Expo batch push: invalid JSON (len=%s preview=%r)",
                        len(raw),
                        preview,
                    )
                    out.extend([False] * len(chunk))
                    continue
                data = parsed.get("data")
                if not isinstance(data, list) or len(data) != len(chunk):
                    logger.warning(
                        "Expo batch push: unexpected data shape (got %s items, expected %s)",
                        len(data) if isinstance(data, list) else 0,
                        len(chunk),
                    )
                    out.extend([False] * len(chunk))
                    continue
                for item in data:
                    if isinstance(item, dict) and item.get("status") == "ok":
                        out.append(True)
                    else:
                        out.append(False)
        except urllib.error.HTTPError as e:
            logger.warning("Expo batch push HTTP error %s: %s", e.code, e.read())
            out.extend([False] * len(chunk))
        except Exception as e:
            logger.exception("Expo batch push failed: %s", e)
            out.extend([False] * len(chunk))
    return out


def send_expo_push(
    token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    sound: str = "default",
    image_url: Optional[str] = None,
) -> bool:
    """
    Send one notification to an Expo push token.
    Returns True if the request was accepted by Expo (HTTP 200), False otherwise.
    image_url: optional URL for rich notification image (Android shows it; iOS needs Notification Service Extension).
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
    if image_url and isinstance(image_url, str) and image_url.strip().startswith("http"):
        payload["richContent"] = {"image": image_url.strip()}
    try:
        req = urllib.request.Request(
            EXPO_PUSH_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                logger.warning("Expo push returned status %s", resp.status)
                return False
            # Drain body (Expo returns JSON receipts); gzip-safe for parity with batch path.
            _expo_response_body_text(resp)
            return True
    except urllib.error.HTTPError as e:
        logger.warning("Expo push HTTP error %s: %s", e.code, e.read())
        return False
    except Exception as e:
        logger.exception("Expo push failed: %s", e)
        return False
