"""
Mobile acquisition funnel: first app open (anonymous) and link to user after auth.
Admin: list installs with attribution and registration status.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(tags=["acquisition"])

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _parse_utm_from_referrer(referrer_raw: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not referrer_raw or not str(referrer_raw).strip():
        return None, None, None
    raw = str(referrer_raw).strip()
    try:
        if "://" in raw:
            q = urlparse(raw).query
        elif raw.startswith("?"):
            q = raw[1:]
        else:
            q = raw
        if not q:
            return None, None, None
        parsed = parse_qs(q, keep_blank_values=False)
        src = (parsed.get("utm_source") or [None])[0]
        med = (parsed.get("utm_medium") or [None])[0]
        camp = (parsed.get("utm_campaign") or [None])[0]
        return (
            str(src).strip() if src else None,
            str(med).strip() if med else None,
            str(camp).strip() if camp else None,
        )
    except Exception:
        return None, None, None


class AcquisitionFirstOpenBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    platform: str = Field("", max_length=32)
    app_version: Optional[str] = Field(None, max_length=64)
    referrer_raw: Optional[str] = Field(None, max_length=8192)


class AcquisitionLinkBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)


def _validate_installation_id(s: str) -> str:
    t = (s or "").strip()
    if not _UUID_RE.match(t):
        raise HTTPException(status_code=400, detail="installation_id must be a UUID")
    return t


@router.post("/acquisition/first-open")
async def acquisition_first_open(body: AcquisitionFirstOpenBody):
    """
    Idempotent: same installation_id updates last_open_at and increments open_count.
    Fills referrer / utm fields on first insert; on conflict fills only if previously null.
    """
    iid = _validate_installation_id(body.installation_id)
    platform = (body.platform or "").strip()[:32] or "unknown"
    app_version = (body.app_version or "").strip()[:64] if body.app_version else None
    referrer_raw = body.referrer_raw
    if referrer_raw is not None:
        referrer_raw = str(referrer_raw)[:8192]

    utm_s, utm_m, utm_c = _parse_utm_from_referrer(referrer_raw)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO app_installations (
                installation_id, platform, app_version, referrer_raw,
                utm_source, utm_medium, utm_campaign,
                first_open_at, last_open_at, open_count
            )
            VALUES (
                ?::uuid, ?, ?, ?,
                ?, ?, ?,
                NOW(), NOW(), 1
            )
            ON CONFLICT (installation_id) DO UPDATE SET
                last_open_at = NOW(),
                open_count = app_installations.open_count + 1,
                app_version = COALESCE(EXCLUDED.app_version, app_installations.app_version),
                referrer_raw = COALESCE(app_installations.referrer_raw, EXCLUDED.referrer_raw),
                utm_source = COALESCE(app_installations.utm_source, EXCLUDED.utm_source),
                utm_medium = COALESCE(app_installations.utm_medium, EXCLUDED.utm_medium),
                utm_campaign = COALESCE(app_installations.utm_campaign, EXCLUDED.utm_campaign)
            """,
            (iid, platform, app_version, referrer_raw, utm_s, utm_m, utm_c),
        )
        conn.commit()

    return {"ok": True}


@router.post("/acquisition/link-user")
async def acquisition_link_user(body: AcquisitionLinkBody, current_user: User = Depends(get_current_user)):
    """Attach the logged-in user to an installation row (first successful auth after install)."""
    iid = _validate_installation_id(body.installation_id)
    uid = int(current_user.userid)

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO app_installations (
                installation_id, platform, app_version, referrer_raw,
                utm_source, utm_medium, utm_campaign,
                first_open_at, last_open_at, open_count, userid, registered_at
            )
            VALUES (
                ?::uuid, 'unknown', NULL, NULL,
                NULL, NULL, NULL,
                NOW(), NOW(), 1, ?, NOW()
            )
            ON CONFLICT (installation_id) DO UPDATE SET
                userid = CASE
                    WHEN app_installations.userid IS NULL OR app_installations.userid = EXCLUDED.userid
                    THEN EXCLUDED.userid
                    ELSE app_installations.userid
                END,
                registered_at = CASE
                    WHEN app_installations.userid IS NULL OR app_installations.userid = EXCLUDED.userid
                    THEN COALESCE(app_installations.registered_at, NOW())
                    ELSE app_installations.registered_at
                END,
                last_open_at = NOW()
            """,
            (iid, uid),
        )
        conn.commit()

    return {"ok": True}


@router.get("/admin/acquisition-installations")
async def admin_acquisition_installations(
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None, description="first_open_at on or after YYYY-MM-DD (IST boundary: use UTC dates conservatively)"),
    date_to: Optional[str] = Query(None, description="first_open_at on or before YYYY-MM-DD"),
    registered: Optional[str] = Query(None, description="yes | no | all"),
    utm_campaign: Optional[str] = Query(None, description="ILIKE filter"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    conditions: list[str] = ["1=1"]
    params: list[Any] = []

    if date_from and date_from.strip():
        conditions.append("ai.first_open_at >= ?::date")
        params.append(date_from.strip())
    if date_to and date_to.strip():
        conditions.append("ai.first_open_at < (?::date + INTERVAL '1 day')")
        params.append(date_to.strip())

    reg = (registered or "all").strip().lower()
    if reg == "yes":
        conditions.append("ai.userid IS NOT NULL")
    elif reg == "no":
        conditions.append("ai.userid IS NULL")

    if utm_campaign and utm_campaign.strip():
        conditions.append("ai.utm_campaign ILIKE ?")
        params.append(f"%{utm_campaign.strip()}%")

    where_sql = " AND ".join(conditions)
    offset = (page - 1) * limit

    with get_conn() as conn:
        cur = execute(
            conn,
            f"SELECT COUNT(*) FROM app_installations ai WHERE {where_sql}",
            params,
        )
        total = int(cur.fetchone()[0])

        cur = execute(
            conn,
            f"""
            SELECT
                ai.installation_id::text,
                ai.platform,
                ai.app_version,
                LEFT(COALESCE(ai.referrer_raw, ''), 500) AS referrer_preview,
                ai.utm_source,
                ai.utm_medium,
                ai.utm_campaign,
                ai.first_open_at,
                ai.last_open_at,
                ai.open_count,
                ai.userid,
                ai.registered_at,
                u.phone AS user_phone,
                u.name AS user_name
            FROM app_installations ai
            LEFT JOIN users u ON u.userid = ai.userid
            WHERE {where_sql}
            ORDER BY ai.first_open_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall() or []

    items = []
    for r in rows:
        items.append(
            {
                "installation_id": r[0],
                "platform": r[1],
                "app_version": r[2],
                "referrer_preview": r[3],
                "utm_source": r[4],
                "utm_medium": r[5],
                "utm_campaign": r[6],
                "first_open_at": r[7].isoformat() if r[7] else None,
                "last_open_at": r[8].isoformat() if r[8] else None,
                "open_count": r[9],
                "userid": r[10],
                "registered_at": r[11].isoformat() if r[11] else None,
                "user_phone": r[12],
                "user_name": r[13],
            }
        )

    return {"total": total, "page": page, "limit": limit, "items": items}


@router.get("/admin/acquisition-installations/summary")
async def admin_acquisition_installations_summary(
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    conditions: list[str] = ["1=1"]
    params: list[Any] = []
    if date_from and date_from.strip():
        conditions.append("first_open_at >= ?::date")
        params.append(date_from.strip())
    if date_to and date_to.strip():
        conditions.append("first_open_at < (?::date + INTERVAL '1 day')")
        params.append(date_to.strip())
    where_sql = " AND ".join(conditions)

    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT
                COUNT(*)::int AS installs,
                COUNT(*) FILTER (WHERE userid IS NOT NULL)::int AS registered
            FROM app_installations
            WHERE {where_sql}
            """,
            params,
        )
        row = cur.fetchone() or (0, 0)

    installs = int(row[0] or 0)
    registered = int(row[1] or 0)
    return {
        "installs": installs,
        "registered": registered,
        "not_registered": max(0, installs - registered),
        "registration_rate": round(registered / installs, 4) if installs else 0.0,
    }
