"""
Mobile acquisition funnel: first app open (anonymous) and link to user after auth.
Admin: list installs with attribution and registration status.
"""
from __future__ import annotations

import csv
import io
import logging
import re
import json
import hashlib
import zipfile
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import parse_qs, unquote_plus, urlparse
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(tags=["acquisition"])

IST_TZ = ZoneInfo("Asia/Kolkata")
_EXPORT_MAX_INSTALL_ROWS = 50_000

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

_FUNNEL_STEPS = [
    ("first_open", "First open"),
    ("auth_welcome_viewed", "Welcome viewed"),
    ("auth_mode_selected", "Mode selected"),
    ("auth_phone_submitted", "Phone submitted"),
    ("registration_otp_requested", "OTP requested"),
    ("registration_otp_screen_viewed", "OTP screen viewed"),
    ("registration_otp_verified", "OTP verified"),
    ("auth_email_screen_viewed", "Email viewed"),
    ("auth_email_submitted", "Email submitted"),
    ("registration_name_submitted", "Name submitted"),
    ("auth_password_screen_viewed", "Password viewed"),
    ("registration_submitted", "Registration submitted"),
    ("registration_completed", "Registration completed"),
]


def _reached_funnel_events(event_name: str) -> list[str]:
    """Events that prove an install reached this funnel step or a later one."""
    names = [name for name, _label in _FUNNEL_STEPS]
    if event_name == "first_open" or event_name not in names:
        return []
    idx = names.index(event_name)
    return [name for name in names[idx:] if name != "first_open"]


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


def _acquisition_filter_sql(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    registered: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    app_build: Optional[str] = None,
    alias: str = "ai",
) -> tuple[str, list[Any]]:
    conditions: list[str] = ["1=1"]
    params: list[Any] = []

    prefix = f"{alias}." if alias else ""
    if date_from and date_from.strip():
        conditions.append(f"{prefix}first_open_at >= ?::date")
        params.append(date_from.strip())
    if date_to and date_to.strip():
        conditions.append(f"{prefix}first_open_at < (?::date + INTERVAL '1 day')")
        params.append(date_to.strip())

    reg = (registered or "all").strip().lower()
    if reg == "yes":
        conditions.append(f"{prefix}userid IS NOT NULL")
    elif reg == "no":
        conditions.append(f"{prefix}userid IS NULL")

    if utm_campaign and utm_campaign.strip():
        conditions.append(f"{prefix}utm_campaign ILIKE ?")
        params.append(f"%{utm_campaign.strip()}%")
    if utm_source and utm_source.strip():
        conditions.append(f"{prefix}utm_source ILIKE ?")
        params.append(f"%{utm_source.strip()}%")
    if utm_medium and utm_medium.strip():
        conditions.append(f"{prefix}utm_medium ILIKE ?")
        params.append(f"%{utm_medium.strip()}%")
    if app_build and app_build.strip():
        conditions.append(f"{prefix}app_build = ?")
        params.append(app_build.strip())

    return " AND ".join(conditions), params


class AcquisitionFirstOpenBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    client_install_key: Optional[str] = Field(None, max_length=512)
    platform: str = Field("", max_length=32)
    app_version: Optional[str] = Field(None, max_length=64)
    app_build: Optional[str] = Field(None, max_length=64)
    referrer_raw: Optional[str] = Field(None, max_length=8192)


class AcquisitionLinkBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    client_install_key: Optional[str] = Field(None, max_length=512)


class AcquisitionEventBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    client_install_key: Optional[str] = Field(None, max_length=512)
    event_name: str = Field(..., min_length=1, max_length=120)
    event_status: Optional[str] = Field(None, max_length=32)
    screen_name: Optional[str] = Field(None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcquisitionContactBody(BaseModel):
    installation_id: str = Field(..., min_length=36, max_length=36)
    client_install_key: Optional[str] = Field(None, max_length=512)
    phone: Optional[str] = Field(None, max_length=64)
    email: Optional[str] = Field(None, max_length=255)


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


def _normalize_client_install_key(value: Optional[str]) -> Optional[str]:
    raw = str(value or "").strip()
    if len(raw) < 12:
        return None
    return "sha256:" + hashlib.sha256(raw[:512].encode("utf-8")).hexdigest()


def _clean_lead_phone(value: Optional[str]) -> Optional[str]:
    raw = str(value or "").strip()
    if not raw:
        return None
    text = re.sub(r"[^0-9+]", "", raw)[:64]
    return text if len(text) >= 7 else None


def _clean_lead_email(value: Optional[str]) -> Optional[str]:
    raw = str(value or "").strip().lower()
    if not raw or "@" not in raw or len(raw) > 255:
        return None
    return raw


def _upsert_installation_stub(conn, *, iid: str, client_install_key: Optional[str], platform: str = "unknown") -> str:
    normalized_key = _normalize_client_install_key(client_install_key)
    if normalized_key:
        cur = execute(
            conn,
            """
            INSERT INTO app_installations (
                installation_id, client_install_key, platform, first_open_at, last_open_at, open_count
            )
            VALUES (?::uuid, ?, ?, NOW(), NOW(), 1)
            ON CONFLICT (client_install_key) WHERE client_install_key IS NOT NULL DO UPDATE SET
                last_open_at = NOW()
            RETURNING installation_id::text
            """,
            (iid, normalized_key, platform or "unknown"),
        )
        row = cur.fetchone()
        return str(row[0]) if row and row[0] else iid

    execute(
        conn,
        """
        INSERT INTO app_installations (
            installation_id, platform, first_open_at, last_open_at, open_count
        )
        VALUES (?::uuid, ?, NOW(), NOW(), 1)
        ON CONFLICT (installation_id) DO UPDATE SET
            last_open_at = NOW()
        """,
        (iid, platform or "unknown"),
    )
    return iid


@router.post("/acquisition/first-open")
async def acquisition_first_open(body: AcquisitionFirstOpenBody):
    """
    Idempotent: same installation_id updates last_open_at and increments open_count.
    Fills referrer / utm fields on first insert; on conflict fills only if previously null.
    """
    iid = _validate_installation_id(body.installation_id)
    platform = (body.platform or "").strip()[:32] or "unknown"
    app_version = (body.app_version or "").strip()[:64] if body.app_version else None
    app_build = (body.app_build or "").strip()[:64] if body.app_build else None
    referrer_raw = body.referrer_raw
    if referrer_raw is not None:
        referrer_raw = str(referrer_raw)[:8192]

    utm_s, utm_m, utm_c = _parse_utm_from_referrer(referrer_raw)
    client_install_key = _normalize_client_install_key(body.client_install_key)

    with get_conn() as conn:
        if client_install_key:
            execute(
                conn,
                """
                INSERT INTO app_installations (
                    installation_id, client_install_key, platform, app_version, app_build, referrer_raw,
                    utm_source, utm_medium, utm_campaign,
                    first_open_at, last_open_at, open_count
                )
                VALUES (
                    ?::uuid, ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    NOW(), NOW(), 1
                )
                ON CONFLICT (client_install_key) WHERE client_install_key IS NOT NULL DO UPDATE SET
                    last_open_at = NOW(),
                    open_count = app_installations.open_count + 1,
                    app_version = COALESCE(EXCLUDED.app_version, app_installations.app_version),
                    app_build = COALESCE(EXCLUDED.app_build, app_installations.app_build),
                    referrer_raw = COALESCE(app_installations.referrer_raw, EXCLUDED.referrer_raw),
                    utm_source = COALESCE(app_installations.utm_source, EXCLUDED.utm_source),
                    utm_medium = COALESCE(app_installations.utm_medium, EXCLUDED.utm_medium),
                    utm_campaign = COALESCE(app_installations.utm_campaign, EXCLUDED.utm_campaign)
                """,
                (iid, client_install_key, platform, app_version, app_build, referrer_raw, utm_s, utm_m, utm_c),
            )
        else:
            execute(
                conn,
                """
                INSERT INTO app_installations (
                    installation_id, platform, app_version, app_build, referrer_raw,
                    utm_source, utm_medium, utm_campaign,
                    first_open_at, last_open_at, open_count
                )
                VALUES (
                    ?::uuid, ?, ?, ?, ?,
                    ?, ?, ?,
                    NOW(), NOW(), 1
                )
                ON CONFLICT (installation_id) DO UPDATE SET
                    last_open_at = NOW(),
                    open_count = app_installations.open_count + 1,
                    app_version = COALESCE(EXCLUDED.app_version, app_installations.app_version),
                    app_build = COALESCE(EXCLUDED.app_build, app_installations.app_build),
                    referrer_raw = COALESCE(app_installations.referrer_raw, EXCLUDED.referrer_raw),
                    utm_source = COALESCE(app_installations.utm_source, EXCLUDED.utm_source),
                    utm_medium = COALESCE(app_installations.utm_medium, EXCLUDED.utm_medium),
                    utm_campaign = COALESCE(app_installations.utm_campaign, EXCLUDED.utm_campaign)
                """,
                (iid, platform, app_version, app_build, referrer_raw, utm_s, utm_m, utm_c),
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
        resolved_iid = _upsert_installation_stub(
            conn,
            iid=iid,
            client_install_key=body.client_install_key,
            platform="unknown",
        )
        execute(
            conn,
            """
            INSERT INTO app_installation_events (
                installation_id, event_name, event_status, screen_name, metadata, created_at
            )
            VALUES (?::uuid, ?, ?, ?, ?::jsonb, NOW())
            """,
            (resolved_iid, event_name, event_status, screen_name, json.dumps(metadata)),
        )
        conn.commit()

    return {"ok": True}


@router.post("/acquisition/contact")
async def acquisition_contact(body: AcquisitionContactBody):
    """Store reachable lead contact for an anonymous install that has not completed registration yet."""
    iid = _validate_installation_id(body.installation_id)
    phone = _clean_lead_phone(body.phone)
    email = _clean_lead_email(body.email)
    if not phone and not email:
        return {"ok": True, "stored": False}

    with get_conn() as conn:
        resolved_iid = _upsert_installation_stub(
            conn,
            iid=iid,
            client_install_key=body.client_install_key,
            platform="unknown",
        )
        execute(
            conn,
            """
            UPDATE app_installations
            SET
                lead_phone = COALESCE(lead_phone, ?),
                lead_email = COALESCE(lead_email, ?),
                last_open_at = NOW()
            WHERE installation_id = ?::uuid
            """,
            (phone, email, resolved_iid),
        )
        conn.commit()

    return {"ok": True, "stored": True}


@router.post("/acquisition/link-user")
async def acquisition_link_user(body: AcquisitionLinkBody, current_user: User = Depends(get_current_user)):
    """Attach the logged-in user to an installation row (first successful auth after install)."""
    iid = _validate_installation_id(body.installation_id)
    uid = int(current_user.userid)
    client_install_key = _normalize_client_install_key(body.client_install_key)

    with get_conn() as conn:
        if client_install_key:
            execute(
                conn,
                """
                INSERT INTO app_installations (
                    installation_id, client_install_key, platform, app_version, referrer_raw,
                    utm_source, utm_medium, utm_campaign,
                    first_open_at, last_open_at, open_count, userid, registered_at
                )
                VALUES (
                    ?::uuid, ?, 'unknown', NULL, NULL,
                    NULL, NULL, NULL,
                    NOW(), NOW(), 1, ?, NOW()
                )
                ON CONFLICT (client_install_key) WHERE client_install_key IS NOT NULL DO UPDATE SET
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
                (iid, client_install_key, uid),
            )
        else:
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
    utm_source: Optional[str] = Query(None, description="ILIKE filter"),
    utm_medium: Optional[str] = Query(None, description="ILIKE filter"),
    app_build: Optional[str] = Query(None, description="Exact native build/version code"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    where_sql, params = _acquisition_filter_sql(
        date_from=date_from,
        date_to=date_to,
        registered=registered,
        utm_campaign=utm_campaign,
        utm_source=utm_source,
        utm_medium=utm_medium,
        app_build=app_build,
        alias="ai",
    )
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
                ai.app_build,
                LEFT(COALESCE(ai.referrer_raw, ''), 500) AS referrer_preview,
                ai.utm_source,
                ai.utm_medium,
                ai.utm_campaign,
                ai.first_open_at,
                ai.last_open_at,
                ai.open_count,
                ai.userid,
                ai.registered_at,
                ai.lead_phone,
                ai.lead_email,
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
                "app_build": r[3],
                "referrer_preview": r[4],
                "utm_source": r[5],
                "utm_medium": r[6],
                "utm_campaign": r[7],
                "first_open_at": r[8].isoformat() if r[8] else None,
                "last_open_at": r[9].isoformat() if r[9] else None,
                "open_count": r[10],
                "userid": r[11],
                "registered_at": r[12].isoformat() if r[12] else None,
                "lead_phone": r[13],
                "lead_email": r[14],
                "user_phone": r[15],
                "user_name": r[16],
                "last_event_name": r[17],
                "last_event_status": r[18],
                "last_event_screen": r[19],
                "last_event_at": r[20].isoformat() if r[20] else None,
            }
        )

    return {"total": total, "page": page, "limit": limit, "items": items}


@router.get("/admin/acquisition-installations/summary")
async def admin_acquisition_installations_summary(
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    app_build: Optional[str] = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    where_sql, params = _acquisition_filter_sql(
        date_from=date_from,
        date_to=date_to,
        utm_campaign=utm_campaign,
        utm_source=utm_source,
        utm_medium=utm_medium,
        app_build=app_build,
        alias="",
    )

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


@router.get("/admin/acquisition-installations/analytics")
async def admin_acquisition_installations_analytics(
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    app_build: Optional[str] = Query(None),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    where_sql, params = _acquisition_filter_sql(
        date_from=date_from,
        date_to=date_to,
        utm_campaign=utm_campaign,
        utm_source=utm_source,
        utm_medium=utm_medium,
        app_build=app_build,
        alias="ai",
    )

    try:
        with get_conn() as conn:
            return _acquisition_analytics_payload(conn, where_sql=where_sql, params=params)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_acquisition_installations_analytics failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load install funnel analytics") from e


@router.get("/admin/acquisition-installations/export")
async def admin_acquisition_installations_export(
    current_user: User = Depends(get_current_user),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    registered: Optional[str] = Query(None, description="yes | no | all"),
    utm_campaign: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    app_build: Optional[str] = Query(None),
):
    """Export install funnel data for marketing: ZIP with four UTF-8 CSV files."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    where_sql, params = _acquisition_filter_sql(
        date_from=date_from,
        date_to=date_to,
        registered=registered,
        utm_campaign=utm_campaign,
        utm_source=utm_source,
        utm_medium=utm_medium,
        app_build=app_build,
        alias="ai",
    )
    funnel_event_names = [name for name, _label in _FUNNEL_STEPS if name != "first_open"]
    funnel_placeholders = ", ".join(["?"] * len(funnel_event_names))

    try:
        with get_conn() as conn:
            analytics = _acquisition_analytics_payload(conn, where_sql=where_sql, params=params)

            cur = execute(
                conn,
                f"SELECT COUNT(*) FROM app_installations ai WHERE {where_sql}",
                params,
            )
            total = int((cur.fetchone() or [0])[0] or 0)
            if total > _EXPORT_MAX_INSTALL_ROWS:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Too many rows to export ({total}). Narrow the date range or filters "
                        f"(max {_EXPORT_MAX_INSTALL_ROWS:,})."
                    ),
                )

            classified_cte = _classified_cte_sql(where_sql)
            cur = execute(
                conn,
                f"""
                {classified_cte}
                SELECT
                    ai.installation_id::text,
                    ai.platform,
                    ai.app_version,
                    ai.app_build,
                    LEFT(COALESCE(ai.referrer_raw, ''), 500) AS referrer_preview,
                    ai.utm_source,
                    ai.utm_medium,
                    ai.utm_campaign,
                    ai.first_open_at,
                    ai.last_open_at,
                    ai.open_count,
                    ai.userid,
                    ai.registered_at,
                    ai.lead_phone,
                    ai.lead_email,
                    u.phone AS user_phone,
                    u.name AS user_name,
                    le.event_name AS last_event_name,
                    le.event_status AS last_event_status,
                    le.screen_name AS last_event_screen,
                    le.created_at AS last_event_at,
                    c.existing_user_install,
                    c.registration_flow_install
                FROM app_installations ai
                INNER JOIN classified c ON c.installation_id = ai.installation_id
                LEFT JOIN users u ON u.userid = ai.userid
                LEFT JOIN LATERAL (
                    SELECT event_name, event_status, screen_name, created_at
                    FROM app_installation_events aie
                    WHERE aie.installation_id = ai.installation_id
                    ORDER BY aie.created_at DESC
                    LIMIT 1
                ) le ON TRUE
                ORDER BY ai.first_open_at DESC
                LIMIT ?
                """,
                params + [_EXPORT_MAX_INSTALL_ROWS],
            )
            rows = cur.fetchall() or []

            reached_by_install: dict[str, set[str]] = {}
            if funnel_event_names:
                cur = execute(
                    conn,
                    f"""
                    SELECT aie.installation_id::text, aie.event_name
                    FROM app_installation_events aie
                    INNER JOIN app_installations ai ON ai.installation_id = aie.installation_id
                    WHERE {where_sql}
                      AND aie.event_name IN ({funnel_placeholders})
                    GROUP BY aie.installation_id, aie.event_name
                    """,
                    params + funnel_event_names,
                )
                for iid, event_name in cur.fetchall() or []:
                    if iid and event_name:
                        reached_by_install.setdefault(str(iid), set()).add(str(event_name))

        install_rows = []
        for r in rows:
            iid = r[0]
            install_rows.append(
                {
                    "installation_id": iid,
                    "platform": r[1],
                    "app_version": r[2],
                    "app_build": r[3],
                    "referrer_preview": r[4],
                    "utm_source": r[5],
                    "utm_medium": r[6],
                    "utm_campaign": r[7],
                    "first_open_at": r[8],
                    "last_open_at": r[9],
                    "open_count": r[10],
                    "userid": r[11],
                    "registered_at": r[12],
                    "lead_phone": r[13],
                    "lead_email": r[14],
                    "user_phone": r[15],
                    "user_name": r[16],
                    "last_event_name": r[17],
                    "last_event_status": r[18],
                    "last_event_screen": r[19],
                    "last_event_at": r[20],
                    "funnel_segment": _funnel_segment_label(
                        userid=r[11],
                        existing_user_install=bool(r[21]),
                        registration_flow_install=bool(r[22]),
                    ),
                    "reached_steps": reached_by_install.get(str(iid), set()),
                }
            )

        zip_bytes = _build_acquisition_export_zip(
            analytics=analytics,
            install_rows=install_rows,
            filters={
                "date_from": date_from,
                "date_to": date_to,
                "registered": registered or "all",
                "utm_source": utm_source,
                "utm_medium": utm_medium,
                "utm_campaign": utm_campaign,
                "app_build": app_build,
            },
        )

        from_part = (date_from or "all").strip()
        to_part = (date_to or "all").strip()
        filename = f"install-funnel_{from_part}_to_{to_part}.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("admin_acquisition_installations_export failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to export install funnel") from e


@router.get("/admin/acquisition-installations/{installation_id}/events")
async def admin_acquisition_installation_events(
    installation_id: str,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    iid = _validate_installation_id(installation_id)

    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT
                ai.installation_id::text,
                ai.first_open_at,
                ai.userid,
                ai.registered_at,
                ai.utm_source,
                ai.utm_medium,
                ai.utm_campaign,
                ai.app_version,
                ai.app_build,
                ai.lead_phone,
                ai.lead_email,
                u.phone,
                u.name
            FROM app_installations ai
            LEFT JOIN users u ON u.userid = ai.userid
            WHERE ai.installation_id = ?::uuid
            """,
            (iid,),
        )
        install = cur.fetchone()
        if not install:
            raise HTTPException(status_code=404, detail="Installation not found")

        cur = execute(
            conn,
            """
            SELECT event_name, event_status, screen_name, metadata, created_at
            FROM app_installation_events
            WHERE installation_id = ?::uuid
            ORDER BY created_at ASC
            """,
            (iid,),
        )
        events = cur.fetchall() or []

    return {
        "installation": {
            "installation_id": install[0],
            "first_open_at": install[1].isoformat() if install[1] else None,
            "userid": install[2],
            "registered_at": install[3].isoformat() if install[3] else None,
            "utm_source": install[4],
            "utm_medium": install[5],
            "utm_campaign": install[6],
            "app_version": install[7],
            "app_build": install[8],
            "lead_phone": install[9],
            "lead_email": install[10],
            "user_phone": install[11],
            "user_name": install[12],
        },
        "events": [
            {
                "event_name": r[0],
                "event_status": r[1],
                "screen_name": r[2],
                "metadata": r[3] if isinstance(r[3], dict) else {},
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in events
        ],
    }


def _format_ts_ist(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    raw = str(value).strip()
    if not raw:
        return ""
    try:
        normalized = raw.replace(" ", "T")
        if not re.search(r"(?:Z|[+-]\d{2}:?\d{2})$", normalized, re.IGNORECASE):
            normalized += "Z"
        dt = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    except Exception:
        return raw


def _csv_bytes(rows: list[list[Any]], headers: list[str]) -> bytes:
    buf = io.StringIO()
    buf.write("\ufeff")
    writer = csv.writer(buf)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8")


def _classified_cte_sql(where_sql: str) -> str:
    return f"""
        WITH filtered AS (
            SELECT ai.installation_id, ai.userid
            FROM app_installations ai
            WHERE {where_sql}
        ),
        signals AS (
            SELECT
                f.installation_id,
                f.userid,
                EXISTS (
                    SELECT 1
                    FROM app_installation_events e
                    WHERE e.installation_id = f.installation_id
                      AND (
                        e.event_name IN (
                            'login_submitted',
                            'login_completed',
                            'login_failed',
                            'registration_existing_user_redirected'
                        )
                        OR (
                            e.event_name = 'auth_mode_selected'
                            AND LOWER(COALESCE(e.metadata->>'mode', '')) = 'login'
                        )
                      )
                ) AS existing_user_install,
                EXISTS (
                    SELECT 1
                    FROM app_installation_events e
                    WHERE e.installation_id = f.installation_id
                      AND (
                        e.event_name IN (
                            'registration_otp_requested',
                            'registration_otp_screen_viewed',
                            'registration_otp_verified',
                            'registration_name_submitted',
                            'registration_submitted',
                            'registration_completed',
                            'registration_failed',
                            'registration_existing_user_redirected'
                        )
                        OR (
                            e.event_name = 'auth_mode_selected'
                            AND LOWER(COALESCE(e.metadata->>'mode', '')) = 'register'
                        )
                      )
                ) AS registration_flow_install
            FROM filtered f
        ),
        classified AS (
            SELECT
                installation_id,
                userid,
                (
                    existing_user_install
                    OR (userid IS NOT NULL AND NOT registration_flow_install)
                ) AS existing_user_install,
                registration_flow_install
            FROM signals
        )
    """


def _acquisition_analytics_payload(
    conn,
    *,
    where_sql: str,
    params: list[Any],
) -> dict[str, Any]:
    classified_cte = _classified_cte_sql(where_sql)

    cur = execute(
        conn,
        f"""
        {classified_cte}
        SELECT
            COUNT(*)::int AS installs,
            COUNT(*) FILTER (WHERE userid IS NOT NULL)::int AS linked,
            COUNT(*) FILTER (WHERE existing_user_install)::int AS existing_user_installs,
            COUNT(*) FILTER (WHERE NOT existing_user_install)::int AS new_user_candidate_installs,
            COUNT(*) FILTER (WHERE registration_flow_install)::int AS registration_flow_installs
        FROM classified
        """,
        params,
    )
    base = cur.fetchone() or (0, 0, 0, 0, 0)
    installs = int(base[0] or 0)
    linked = int(base[1] or 0)
    existing_user_installs = int(base[2] or 0)
    new_user_candidate_installs = int(base[3] or 0)
    registration_flow_installs = int(base[4] or 0)
    unknown_anonymous_installs = max(0, new_user_candidate_installs - registration_flow_installs)

    funnel: list[dict[str, Any]] = []
    previous = new_user_candidate_installs
    for event_name, label in _FUNNEL_STEPS:
        if event_name == "first_open":
            count = new_user_candidate_installs
        else:
            reached_events = _reached_funnel_events(event_name)
            placeholders = ", ".join(["?"] * len(reached_events))
            cur = execute(
                conn,
                f"""
                {classified_cte}
                SELECT COUNT(DISTINCT aie.installation_id)::int
                FROM app_installation_events aie
                JOIN classified c ON c.installation_id = aie.installation_id
                WHERE NOT c.existing_user_install AND aie.event_name IN ({placeholders})
                """,
                params + reached_events,
            )
            count = int((cur.fetchone() or [0])[0] or 0)
        funnel.append(
            {
                "event_name": event_name,
                "label": label,
                "count": count,
                "conversion_from_previous": round(count / previous, 4) if previous else 0.0,
                "conversion_from_install": round(count / new_user_candidate_installs, 4) if new_user_candidate_installs else 0.0,
                "drop_from_previous": max(0, previous - count),
            }
        )
        previous = count

    cur = execute(
        conn,
        f"""
        SELECT
            COALESCE(le.event_name, 'first_open_only') AS event_name,
            COALESCE(le.event_status, 'none') AS event_status,
            COALESCE(le.screen_name, '') AS screen_name,
            COUNT(*)::int AS installs
        FROM app_installations ai
        LEFT JOIN LATERAL (
            SELECT event_name, event_status, screen_name
            FROM app_installation_events aie
            WHERE aie.installation_id = ai.installation_id
            ORDER BY aie.created_at DESC
            LIMIT 1
        ) le ON TRUE
        WHERE {where_sql} AND ai.userid IS NULL
        GROUP BY 1, 2, 3
        ORDER BY installs DESC, event_name ASC
        LIMIT 50
        """,
        params,
    )
    dropoff_rows = cur.fetchall() or []

    unlinked = max(0, installs - linked)
    dropoff = [
        {
            "event_name": r[0],
            "event_status": r[1],
            "screen_name": r[2],
            "installs": int(r[3] or 0),
            "share_of_unlinked": round(int(r[3] or 0) / unlinked, 4) if unlinked else 0.0,
        }
        for r in dropoff_rows
    ]

    return {
        "installs": installs,
        "linked": linked,
        "unlinked": unlinked,
        "existing_user_installs": existing_user_installs,
        "new_user_candidate_installs": new_user_candidate_installs,
        "registration_flow_installs": registration_flow_installs,
        "unknown_anonymous_installs": unknown_anonymous_installs,
        "funnel": funnel,
        "dropoff": dropoff,
    }


def _funnel_segment_label(
    *,
    userid: Any,
    existing_user_install: bool,
    registration_flow_install: bool,
) -> str:
    if existing_user_install:
        return "existing_user"
    if registration_flow_install:
        return "new_user_registration"
    if userid is not None:
        return "linked_other"
    return "new_user_unknown"


def _build_acquisition_export_zip(
    *,
    analytics: dict[str, Any],
    install_rows: list[dict[str, Any]],
    filters: dict[str, Any],
) -> bytes:
    now_ist = datetime.now(IST_TZ).strftime("%Y-%m-%d %H:%M:%S IST")
    summary_rows = [[
        now_ist,
        filters.get("date_from") or "",
        filters.get("date_to") or "",
        filters.get("registered") or "all",
        filters.get("utm_source") or "",
        filters.get("utm_medium") or "",
        filters.get("utm_campaign") or "",
        filters.get("app_build") or "",
        analytics.get("installs", 0),
        analytics.get("linked", 0),
        analytics.get("unlinked", 0),
        round((analytics.get("linked", 0) / analytics.get("installs", 1)) * 100, 2) if analytics.get("installs") else 0,
        analytics.get("existing_user_installs", 0),
        analytics.get("new_user_candidate_installs", 0),
        analytics.get("registration_flow_installs", 0),
        analytics.get("unknown_anonymous_installs", 0),
        len(install_rows),
    ]]
    summary_csv = _csv_bytes(
        summary_rows,
        [
            "export_generated_at_ist",
            "filter_date_from",
            "filter_date_to",
            "filter_linked_user",
            "filter_utm_source_contains",
            "filter_utm_medium_contains",
            "filter_utm_campaign_contains",
            "filter_app_build",
            "total_first_opens",
            "linked_users",
            "not_linked",
            "registration_rate_pct",
            "existing_user_installs",
            "new_user_funnel_base",
            "registration_flow_installs",
            "unknown_anonymous_installs",
            "install_rows_exported",
        ],
    )

    funnel_rows = []
    for idx, step in enumerate(analytics.get("funnel") or [], start=1):
        funnel_rows.append([
            idx,
            step.get("event_name") or "",
            step.get("label") or "",
            step.get("count") or 0,
            round((step.get("conversion_from_previous") or 0) * 100, 2),
            round((step.get("conversion_from_install") or 0) * 100, 2),
            step.get("drop_from_previous") or 0,
        ])
    funnel_csv = _csv_bytes(
        funnel_rows,
        [
            "step_order",
            "event_name",
            "step_label",
            "install_count",
            "conversion_from_previous_pct",
            "conversion_from_funnel_start_pct",
            "drop_from_previous",
        ],
    )

    dropoff_rows = []
    for row in analytics.get("dropoff") or []:
        dropoff_rows.append([
            row.get("event_name") or "",
            row.get("event_status") or "",
            row.get("screen_name") or "",
            row.get("installs") or 0,
            round((row.get("share_of_unlinked") or 0) * 100, 2),
        ])
    dropoff_csv = _csv_bytes(
        dropoff_rows,
        [
            "last_event_name",
            "last_event_status",
            "last_screen_name",
            "installs",
            "share_of_unlinked_pct",
        ],
    )

    step_headers = [f"reached_{name}" for name, _label in _FUNNEL_STEPS if name != "first_open"]
    install_csv_rows = []
    for row in install_rows:
        reached = row.get("reached_steps") or set()
        install_csv_rows.append([
            row.get("installation_id") or "",
            _format_ts_ist(row.get("first_open_at")),
            _format_ts_ist(row.get("last_open_at")),
            row.get("platform") or "",
            row.get("app_version") or "",
            row.get("app_build") or "",
            row.get("utm_source") or "",
            row.get("utm_medium") or "",
            row.get("utm_campaign") or "",
            row.get("open_count") or 0,
            "yes" if row.get("userid") is not None else "no",
            row.get("userid") or "",
            row.get("user_phone") or "",
            row.get("user_name") or "",
            row.get("lead_phone") or "",
            row.get("lead_email") or "",
            _format_ts_ist(row.get("registered_at")),
            row.get("last_event_name") or "",
            row.get("last_event_status") or "",
            row.get("last_event_screen") or "",
            _format_ts_ist(row.get("last_event_at")),
            row.get("funnel_segment") or "",
            *[("yes" if step in reached else "no") for step, _label in _FUNNEL_STEPS if step != "first_open"],
            row.get("referrer_preview") or "",
        ])
    installs_csv = _csv_bytes(
        install_csv_rows,
        [
            "installation_id",
            "first_open_at_ist",
            "last_open_at_ist",
            "platform",
            "app_version",
            "app_build",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "open_count",
            "is_linked",
            "userid",
            "user_phone",
            "user_name",
            "lead_phone",
            "lead_email",
            "linked_at_ist",
            "last_event_name",
            "last_event_status",
            "last_event_screen",
            "last_event_at_ist",
            "funnel_segment",
            *step_headers,
            "referrer_preview",
        ],
    )

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("01_summary.csv", summary_csv)
        zf.writestr("02_funnel_steps.csv", funnel_csv)
        zf.writestr("03_dropoff.csv", dropoff_csv)
        zf.writestr("04_installs.csv", installs_csv)
    return zip_buf.getvalue()

