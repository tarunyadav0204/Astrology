from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from db import execute, get_conn
from reports.branding import normalize_report_branding, save_report_branding

PANDIT_FREE_PRODUCT_ID = "pandit_desk_free"
PANDIT_SUBSCRIPTION_FAMILY = "pandit"
DEFAULT_LANGUAGES = ["hindi", "english"]
ALLOWED_PUJA_TYPES = [
    "satyanarayan",
    "griha_pravesh",
    "vivah",
    "naamkaran",
    "mundan",
    "vastu",
    "navagraha",
    "rudrabhishek",
    "other",
]


def _json_list(value: Any, *, fallback: Optional[List[str]] = None) -> List[str]:
    if value is None:
        return list(fallback or [])
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v).strip() for v in parsed if str(v).strip()]
        except Exception:
            pass
        return [part.strip() for part in value.split(",") if part.strip()]
    return list(fallback or [])


def _row_to_profile(row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    (
        userid,
        display_name,
        city,
        pincode,
        languages,
        puja_types,
        status,
        tagline,
        phone,
        email,
        website,
        address,
        setup_complete,
        verified_jobs,
        created_at,
        updated_at,
    ) = row
    return {
        "userid": int(userid),
        "display_name": display_name or "",
        "city": city or "",
        "pincode": pincode or "",
        "languages": _json_list(languages, fallback=DEFAULT_LANGUAGES),
        "puja_types": _json_list(puja_types),
        "status": status or "active_tools",
        "tagline": tagline or "",
        "phone": phone or "",
        "email": email or "",
        "website": website or "",
        "address": address or "",
        "setup_complete": bool(setup_complete),
        "verified_jobs": bool(verified_jobs),
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
        "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else updated_at,
    }


def get_profile(userid: int) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT userid, display_name, city, pincode, languages, puja_types, status,
                   tagline, phone, email, website, address, setup_complete,
                   COALESCE(verified_jobs, FALSE) AS verified_jobs,
                   created_at, updated_at
            FROM pandit_profiles
            WHERE userid = ?
            """,
            (int(userid),),
        )
        return _row_to_profile(cursor.fetchone())


def _normalize_profile_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    languages = _json_list(payload.get("languages"), fallback=DEFAULT_LANGUAGES)
    if not languages:
        languages = list(DEFAULT_LANGUAGES)

    puja_types = [
        p for p in _json_list(payload.get("puja_types"))
        if p in ALLOWED_PUJA_TYPES
    ]

    display_name = str(payload.get("display_name") or "").strip()[:80]
    city = str(payload.get("city") or "").strip()[:80]
    pincode = "".join(ch for ch in str(payload.get("pincode") or "") if ch.isdigit())[:10]
    tagline = str(payload.get("tagline") or "").strip()[:120]
    phone = str(payload.get("phone") or "").strip()[:40]
    email = str(payload.get("email") or "").strip()[:80]
    website = str(payload.get("website") or "").strip()[:120]
    address = str(payload.get("address") or "").strip()[:160]

    setup_complete = bool(
        display_name and city and len(pincode) >= 6 and puja_types
    )

    return {
        "display_name": display_name,
        "city": city,
        "pincode": pincode,
        "languages": languages,
        "puja_types": puja_types,
        "tagline": tagline,
        "phone": phone,
        "email": email,
        "website": website,
        "address": address,
        "setup_complete": setup_complete,
        "status": str(payload.get("status") or "active_tools").strip() or "active_tools",
    }


def upsert_profile(userid: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = _normalize_profile_payload(payload)
    languages_json = json.dumps(data["languages"], ensure_ascii=False)
    puja_json = json.dumps(data["puja_types"], ensure_ascii=False)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO pandit_profiles (
                userid, display_name, city, pincode, languages, puja_types, status,
                tagline, phone, email, website, address, setup_complete, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (userid) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                city = EXCLUDED.city,
                pincode = EXCLUDED.pincode,
                languages = EXCLUDED.languages,
                puja_types = EXCLUDED.puja_types,
                status = EXCLUDED.status,
                tagline = EXCLUDED.tagline,
                phone = EXCLUDED.phone,
                email = EXCLUDED.email,
                website = EXCLUDED.website,
                address = EXCLUDED.address,
                setup_complete = EXCLUDED.setup_complete,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                int(userid),
                data["display_name"],
                data["city"],
                data["pincode"],
                languages_json,
                puja_json,
                data["status"],
                data["tagline"],
                data["phone"],
                data["email"],
                data["website"],
                data["address"],
                data["setup_complete"],
            ),
        )
        conn.commit()

    # Keep report branding in sync for Janam Kundli PDFs.
    branding = normalize_report_branding({
        "business_name": data["display_name"],
        "tagline": data["tagline"],
        "phone": data["phone"],
        "email": data["email"],
        "website": data["website"],
        "address": data["address"] or f"{data['city']} {data['pincode']}".strip(),
    })
    if branding.get("business_name"):
        save_report_branding(int(userid), branding, get_conn, execute)

    profile = get_profile(userid)
    if not profile:
        raise RuntimeError("Failed to load pandit profile after upsert")
    return profile


def get_free_plan_id() -> Optional[int]:
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT plan_id
            FROM subscription_plans
            WHERE platform = 'astroroshni'
              AND subscription_family = ?
              AND google_play_product_id = ?
              AND LOWER(CAST(is_active AS TEXT)) IN ('true', '1', 't', 'yes')
            ORDER BY plan_id ASC
            LIMIT 1
            """,
            (PANDIT_SUBSCRIPTION_FAMILY, PANDIT_FREE_PRODUCT_ID),
        )
        row = cursor.fetchone()
        return int(row[0]) if row else None


def grant_free_desk(userid: int) -> bool:
    """Grant complimentary pandit_desk entitlement (long Free window)."""
    from credits.credit_service import CreditService

    plan_id = get_free_plan_id()
    if not plan_id:
        return False

    today = date.today()
    # Free plan duration_months is 120; keep a generous window and renew on re-join.
    end = today + timedelta(days=3650)
    service = CreditService()
    return bool(
        service.set_user_subscription(
            int(userid),
            int(plan_id),
            today.isoformat(),
            end.isoformat(),
            billing_provider="complimentary",
        )
    )
