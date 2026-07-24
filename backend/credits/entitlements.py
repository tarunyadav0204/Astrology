from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import HTTPException

from auth import User
from db import execute, get_conn


ASTROLOGER_SUBSCRIPTION_FAMILY = "astrologer"
ASTROLOGER_TOOLS_ENTITLEMENT = "astrologer_tools"


def get_active_entitlements(userid: int, *, role: Optional[str] = None) -> List[str]:
    """Return current paid capabilities. Admins receive an explicit access bypass."""
    entitlements = set()
    if str(role or "").strip().lower() == "admin":
        entitlements.add(ASTROLOGER_TOOLS_ENTITLEMENT)
    with get_conn() as conn:
        cursor = execute(
            conn,
            """
            SELECT DISTINCT sp.entitlement_key
            FROM user_subscriptions us
            JOIN subscription_plans sp ON sp.plan_id = us.plan_id
            WHERE us.userid = ?
              AND us.status = 'active'
              AND us.end_date >= CURRENT_DATE
              AND sp.entitlement_key IS NOT NULL
              AND TRIM(sp.entitlement_key) <> ''
            """,
            (int(userid),),
        )
        entitlements.update(str(row[0]).strip() for row in (cursor.fetchall() or []) if row[0])
    return sorted(entitlements)


def has_entitlement(user: User, entitlement_key: str) -> bool:
    return str(entitlement_key).strip() in get_active_entitlements(
        user.userid,
        role=user.role,
    )


def require_entitlement(user: User, entitlement_key: str) -> None:
    if has_entitlement(user, entitlement_key):
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "ASTROLOGER_LICENSE_REQUIRED",
            "message": "An active Astrologer License is required for this professional tool.",
            "entitlement": entitlement_key,
            "subscription_family": ASTROLOGER_SUBSCRIPTION_FAMILY,
            "product_id": "astrologer_license_monthly",
        },
    )


def entitlement_summary(user: User) -> Dict[str, object]:
    entitlements = get_active_entitlements(user.userid, role=user.role)
    return {
        "entitlements": entitlements,
        "is_astrologer_licensed": ASTROLOGER_TOOLS_ENTITLEMENT in entitlements,
        "admin_access": str(user.role or "").strip().lower() == "admin",
    }
