"""Admin pandit directory: list, filter by pincode, mark verified_jobs candidates."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth import User, get_current_user
from db import execute, get_conn
from pandit import service as pandit_service

router = APIRouter(prefix="/admin/pandits", tags=["admin_pandits"])


class PanditAdminUpdateRequest(BaseModel):
    verified_jobs: Optional[bool] = None


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _admin_row_to_item(row) -> Dict[str, Any]:
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
        user_name,
        user_phone,
        user_email,
    ) = row
    profile = {
        "userid": int(userid),
        "display_name": display_name or "",
        "city": city or "",
        "pincode": pincode or "",
        "languages": pandit_service._json_list(languages, fallback=pandit_service.DEFAULT_LANGUAGES),
        "puja_types": pandit_service._json_list(puja_types),
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
    return {
        **profile,
        "user_name": user_name or "",
        "user_phone": user_phone or "",
        "user_email": user_email or "",
    }


@router.get("")
async def list_admin_pandits(
    pincode: Optional[str] = Query(None, max_length=10),
    verified_jobs: Optional[bool] = Query(None),
    setup_complete: Optional[bool] = Query(None),
    q: Optional[str] = Query(None, max_length=80),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    _admin: User = Depends(_require_admin),
):
    pin = "".join(ch for ch in str(pincode or "") if ch.isdigit())[:10]
    search = (q or "").strip()
    offset = (page - 1) * limit

    where: List[str] = ["1=1"]
    params: List[Any] = []

    if pin:
        where.append("p.pincode LIKE ?")
        params.append(f"{pin}%")
    if verified_jobs is not None:
        where.append("p.verified_jobs = ?")
        params.append(bool(verified_jobs))
    if setup_complete is not None:
        where.append("p.setup_complete = ?")
        params.append(bool(setup_complete))
    if search:
        like = f"%{search}%"
        where.append(
            "(p.display_name ILIKE ? OR p.city ILIKE ? OR COALESCE(u.name, '') ILIKE ? OR COALESCE(u.phone, '') ILIKE ?)"
        )
        params.extend([like, like, like, like])

    where_sql = " AND ".join(where)

    with get_conn() as conn:
        count_cur = execute(
            conn,
            f"""
            SELECT COUNT(*)
            FROM pandit_profiles p
            LEFT JOIN users u ON u.userid = p.userid
            WHERE {where_sql}
            """,
            tuple(params),
        )
        total = int((count_cur.fetchone() or [0])[0] or 0)

        list_cur = execute(
            conn,
            f"""
            SELECT
                p.userid, p.display_name, p.city, p.pincode, p.languages, p.puja_types,
                p.status, p.tagline, p.phone, p.email, p.website, p.address,
                p.setup_complete, p.verified_jobs, p.created_at, p.updated_at,
                u.name, u.phone, u.email
            FROM pandit_profiles p
            LEFT JOIN users u ON u.userid = p.userid
            WHERE {where_sql}
            ORDER BY p.created_at DESC, p.userid DESC
            LIMIT ? OFFSET ?
            """,
            tuple(params + [limit, offset]),
        )
        items = [_admin_row_to_item(row) for row in (list_cur.fetchall() or [])]

    return {
        "success": True,
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.patch("/{userid}")
async def patch_admin_pandit(
    userid: int,
    body: PanditAdminUpdateRequest,
    _admin: User = Depends(_require_admin),
):
    if body.verified_jobs is None:
        raise HTTPException(status_code=400, detail="Provide verified_jobs to update.")

    with get_conn() as conn:
        exists = execute(
            conn,
            "SELECT 1 FROM pandit_profiles WHERE userid = ?",
            (int(userid),),
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Pandit profile not found")

        execute(
            conn,
            """
            UPDATE pandit_profiles
            SET verified_jobs = ?, updated_at = CURRENT_TIMESTAMP
            WHERE userid = ?
            """,
            (bool(body.verified_jobs), int(userid)),
        )
        conn.commit()

        row = execute(
            conn,
            """
            SELECT
                p.userid, p.display_name, p.city, p.pincode, p.languages, p.puja_types,
                p.status, p.tagline, p.phone, p.email, p.website, p.address,
                p.setup_complete, p.verified_jobs, p.created_at, p.updated_at,
                u.name, u.phone, u.email
            FROM pandit_profiles p
            LEFT JOIN users u ON u.userid = p.userid
            WHERE p.userid = ?
            """,
            (int(userid),),
        ).fetchone()

    return {
        "success": True,
        "item": _admin_row_to_item(row),
    }
