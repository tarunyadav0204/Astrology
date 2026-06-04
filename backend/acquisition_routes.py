"""
Mobile acquisition funnel: first app open (anonymous) and link to user after auth.
Admin: list installs with attribution and registration status.
"""
from __future__ import annotations

import logging
import re
import json
from typing import Any, Optional
from urllib.parse import parse_qs, unquote_plus, urlparse

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


def _query_from_candidate(value: str) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    if "://" in raw:
        return urlparse(raw).query or None
    if raw.startswith("?"):
        return raw[1:] or None
    return raw


def _first_utm_from_query(query: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    parsed = parse_qs(query, keep_blank_values=False)
    src = (parsed.get("utm_source") or [None])[0]
    med = (parsed.get("utm_medium") or [None])[0]
    camp = (parsed.get("utm_campaign") or [None])[0]
    return (
        str(src).strip() if src else None,
        str(med).strip() if med else None,
        str(camp).strip() if camp else None,
    )


def _parse_utm_from_referrer(referrer_raw: Optional[str]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    if not referrer_raw or not str(referrer_raw).strip():
        return None, None, None
    raw = str(referrer_raw).strip()
    try:
        candidates = [raw]
        for line in raw.splitlines():
            line = line.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            decoded_value = unquote_plus(value.strip())
            if key in {"initial_url", "play_install_referrer", "install_referrer", "referrer", "referrer_raw"}:
                candidates.append(decoded_value)
            else:
                candidates.append(line)

        for candidate in candidates:
            query = _query_from_candidate(candidate)
            if not query:
                continue
            src, med, camp = _first_utm_from_query(query)
            if src or med or camp:
                return src, med, camp
        return None, None, None
    except Exception:
        return None, None, None


class AcquisitionFirstOpenBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    platform: str = Field("", max_length=32)
    app_version: Optional[str] = Field(None, max_length=64)
    referrer_raw: Optional[str] = Field(None, max_length=8192)


class AcquisitionLinkBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)


class AcquisitionEventBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    event_name: str = Field(..., min_length=1, max_length=120)
    event_status: Optional[str] = Field(None, max_length=32)
    screen_name: Optional[str] = Field(None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


def _validate_installation_id(s: str) -> str:
    t = (s or "").strip()
    if not _UUID_RE.match(t):
        raise HTTPException(status_code=400, detail="installation_id must be a UUID")
    return t


def _safe_token(value: Optional[str], *, max_len: int) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r"[^a-zA-Z0-9_.:-]+", "_", str(value).strip())
    text = text.strip("_")[:max_len]
    return text or None


def _sanitize_event_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    safe: dict[str, Any] = {}
    blocked = {"password", "token", "access_token", "auth", "authorization", "otp", "code", "phone", "email"}
    for key, value in list(metadata.items())[:20]:
        safe_key = _safe_token(str(key), max_len=80)
        if not safe_key or safe_key.lower() in blocked:
            continue
        if isinstance(value, (bool, int, float)) or value is None:
            safe[safe_key] = value
        elif isinstance(value, str):
            safe[safe_key] = value.strip()[:300]
        else:
            safe[safe_key] = str(value)[:300]
    return safe


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


@router.post("/acquisition/event")
async def acquisition_event(body: AcquisitionEventBody):
    """Anonymous funnel breadcrumb tied to installation_id before login/registration."""
    iid = _validate_installation_id(body.installation_id)
    event_name = _safe_token(body.event_name, max_len=120)
    if not event_name:
        raise HTTPException(status_code=400, detail="event_name is required")
    event_status = _safe_token(body.event_status, max_len=32)
    screen_name = _safe_token(body.screen_name, max_len=120)
    metadata = _sanitize_event_metadata(body.metadata or {})

    with get_conn() as conn:
        execute(
            conn,
            """
            INSERT INTO app_installations (
                installation_id, platform, first_open_at, last_open_at, open_count
            )
            VALUES (?::uuid, 'unknown', NOW(), NOW(), 1)
            ON CONFLICT (installation_id) DO UPDATE SET
                last_open_at = NOW()
            """,
            (iid,),
        )
        execute(
            conn,
            """
            INSERT INTO app_installation_events (
                installation_id, event_name, event_status, screen_name, metadata, created_at
            )
            VALUES (?::uuid, ?, ?, ?, ?::jsonb, NOW())
            """,
            (iid, event_name, event_status, screen_name, json.dumps(metadata)),
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
                u.name AS user_name,
                le.event_name AS last_event_name,
                le.event_status AS last_event_status,
                le.screen_name AS last_event_screen,
                le.created_at AS last_event_at
            FROM app_installations ai
            LEFT JOIN users u ON u.userid = ai.userid
            LEFT JOIN LATERAL (
                SELECT event_name, event_status, screen_name, created_at
                FROM app_installation_events aie
                WHERE aie.installation_id = ai.installation_id
                ORDER BY aie.created_at DESC
                LIMIT 1
            ) le ON TRUE
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
                "last_event_name": r[14],
                "last_event_status": r[15],
                "last_event_screen": r[16],
                "last_event_at": r[17].isoformat() if r[17] else None,
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
