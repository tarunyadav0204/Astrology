"""Per-user report branding (pandit / practice identity on PDFs)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Optional

from db import execute

SETTING_KEY = "report_branding"

_MAX_LEN = {
    "business_name": 80,
    "tagline": 120,
    "phone": 40,
    "email": 80,
    "website": 120,
    "address": 160,
}


def _clip(value: Any, max_len: int) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    # Collapse whitespace / newlines for PDF chrome
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def normalize_report_branding(raw: Any) -> Dict[str, Any]:
    """Normalize branding payload. Empty business_name ⇒ AstroRoshni default branding."""
    data = raw if isinstance(raw, dict) else {}
    if hasattr(raw, "model_dump"):
        data = raw.model_dump()
    elif hasattr(raw, "dict"):
        data = raw.dict()

    business_name = _clip(data.get("business_name"), _MAX_LEN["business_name"])

    return {
        "business_name": business_name,
        "tagline": _clip(data.get("tagline"), _MAX_LEN["tagline"]),
        "phone": _clip(data.get("phone"), _MAX_LEN["phone"]),
        "email": _clip(data.get("email"), _MAX_LEN["email"]),
        "website": _clip(data.get("website"), _MAX_LEN["website"]),
        "address": _clip(data.get("address"), _MAX_LEN["address"]),
        # Always credit AstroRoshni on pandit-branded reports (not user-toggleable).
        "show_powered_by": True,
    }


def branding_fingerprint(branding: Any) -> str:
    normalized = normalize_report_branding(branding)
    blob = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def has_custom_branding(branding: Any) -> bool:
    normalized = normalize_report_branding(branding)
    return bool(normalized.get("business_name"))


def branding_contact_line(branding: Any) -> str:
    normalized = normalize_report_branding(branding)
    parts = [
        p
        for p in [
            normalized.get("phone"),
            normalized.get("email"),
            normalized.get("website"),
        ]
        if p
    ]
    return " · ".join(parts)


def get_saved_report_branding(userid: int, get_conn, execute_fn=execute) -> Dict[str, Any]:
    with get_conn() as conn:
        cur = execute_fn(
            conn,
            """
            SELECT setting_value FROM user_settings
            WHERE user_id = ? AND setting_key = ?
            """,
            (userid, SETTING_KEY),
        )
        row = cur.fetchone()
    if not row:
        return normalize_report_branding({})
    raw = row[0]
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        parsed = {}
    return normalize_report_branding(parsed)


def save_report_branding(userid: int, branding: Any, get_conn, execute_fn=execute) -> Dict[str, Any]:
    normalized = normalize_report_branding(branding)
    value_json = json.dumps(normalized, ensure_ascii=False)
    with get_conn() as conn:
        cur = execute_fn(
            conn,
            """
            UPDATE user_settings
            SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND setting_key = ?
            """,
            (value_json, userid, SETTING_KEY),
        )
        if cur.rowcount == 0:
            execute_fn(
                conn,
                """
                INSERT INTO user_settings (user_id, setting_key, setting_value)
                VALUES (?, ?, ?)
                """,
                (userid, SETTING_KEY, value_json),
            )
        conn.commit()
    return normalized


def resolve_report_branding(
    userid: int,
    request_branding: Any,
    get_conn,
    execute_fn=execute,
    *,
    persist: bool = True,
) -> Dict[str, Any]:
    """
    Prefer branding sent on the request (and optionally persist it).
    Otherwise load the user's saved branding.
    """
    if request_branding is not None:
        normalized = normalize_report_branding(request_branding)
        if persist:
            save_report_branding(userid, normalized, get_conn, execute_fn)
        return normalized
    return get_saved_report_branding(userid, get_conn, execute_fn)


def apply_branding_to_cached_report(
    cached: Dict[str, Any],
    branding: Dict[str, Any],
    *,
    store_pdf_fn,
) -> Dict[str, Any]:
    """Attach branding and re-render PDF when the fingerprint changed."""
    out = dict(cached or {})
    normalized = normalize_report_branding(branding)
    old_fp = branding_fingerprint(out.get("branding"))
    new_fp = branding_fingerprint(normalized)
    out["branding"] = normalized
    if old_fp != new_fp or not out.get("pdf_gcs_path"):
        out.pop("pdf_url", None)
        out.update(store_pdf_fn(out))
    return out
