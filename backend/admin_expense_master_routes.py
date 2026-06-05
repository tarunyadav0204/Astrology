"""
Admin CRUD for expense dropdown masters: vendors (who you paid) and paid by (card/account/person).
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/expense-masters", tags=["admin_expense_masters"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class MasterCreateBody(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)
    sort_order: int = Field(0, ge=0, le=1_000_000)


class MasterPatchBody(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=200)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, le=1_000_000)


def _normalize_label(s: str) -> str:
    return " ".join((s or "").strip().split())


# --- Vendors ---


@router.get("/vendors")
async def list_vendors(
    current_user: User = Depends(_require_admin),
    include_inactive: bool = False,
):
    where = "1=1" if include_inactive else "is_active = TRUE"
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT id, label, is_active, sort_order, created_at
            FROM admin_expense_vendors
            WHERE {where}
            ORDER BY sort_order ASC, LOWER(label) ASC
            """,
        )
        rows = cur.fetchall() or []
    return {
        "items": [
            {
                "id": r[0],
                "label": r[1],
                "is_active": bool(r[2]),
                "sort_order": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    }


@router.post("/vendors")
async def create_vendor(body: MasterCreateBody, current_user: User = Depends(_require_admin)):
    label = _normalize_label(body.label)
    if not label:
        raise HTTPException(status_code=400, detail="label is required")
    with get_conn() as conn:
        try:
            cur = execute(
                conn,
                """
                INSERT INTO admin_expense_vendors (label, sort_order)
                VALUES (?, ?)
                RETURNING id
                """,
                (label, int(body.sort_order)),
            )
            row = cur.fetchone()
            conn.commit()
        except HTTPException:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                raise HTTPException(status_code=409, detail="A vendor with this name already exists") from e
            logger.exception("create_vendor failed")
            raise HTTPException(status_code=500, detail="Could not create vendor") from e
    return {"id": int(row[0]), "ok": True}


@router.patch("/vendors/{vendor_id}")
async def patch_vendor(
    vendor_id: int, body: MasterPatchBody, current_user: User = Depends(_require_admin)
):
    fields: list[str] = []
    params: list[Any] = []
    if body.label is not None:
        nl = _normalize_label(body.label)
        if not nl:
            raise HTTPException(status_code=400, detail="label cannot be empty")
        fields.append("label = ?")
        params.append(nl)
    if body.is_active is not None:
        fields.append("is_active = ?")
        params.append(bool(body.is_active))
    if body.sort_order is not None:
        fields.append("sort_order = ?")
        params.append(int(body.sort_order))
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(vendor_id)
    with get_conn() as conn:
        try:
            cur = execute(
                conn,
                f"UPDATE admin_expense_vendors SET {', '.join(fields)} WHERE id = ? RETURNING id",
                params,
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Vendor not found")
            conn.commit()
        except HTTPException:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                raise HTTPException(status_code=409, detail="A vendor with this name already exists") from e
            raise
    return {"ok": True}


@router.delete("/vendors/{vendor_id}")
async def delete_vendor(vendor_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT COUNT(*) FROM admin_company_expenses WHERE vendor_id = ?",
            (vendor_id,),
        )
        n = int(cur.fetchone()[0])
        if n > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: {n} expense(s) reference this vendor. Deactivate it instead.",
            )
        cur = execute(conn, "DELETE FROM admin_expense_vendors WHERE id = ? RETURNING id", (vendor_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vendor not found")
        conn.commit()
    return {"ok": True}


# --- Paid by ---


@router.get("/paid-by")
async def list_paid_by(
    current_user: User = Depends(_require_admin),
    include_inactive: bool = False,
):
    where = "1=1" if include_inactive else "is_active = TRUE"
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT id, label, is_active, sort_order, created_at
            FROM admin_expense_paid_by
            WHERE {where}
            ORDER BY sort_order ASC, LOWER(label) ASC
            """,
        )
        rows = cur.fetchall() or []
    return {
        "items": [
            {
                "id": r[0],
                "label": r[1],
                "is_active": bool(r[2]),
                "sort_order": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    }


@router.post("/paid-by")
async def create_paid_by(body: MasterCreateBody, current_user: User = Depends(_require_admin)):
    label = _normalize_label(body.label)
    if not label:
        raise HTTPException(status_code=400, detail="label is required")
    with get_conn() as conn:
        try:
            cur = execute(
                conn,
                """
                INSERT INTO admin_expense_paid_by (label, sort_order)
                VALUES (?, ?)
                RETURNING id
                """,
                (label, int(body.sort_order)),
            )
            row = cur.fetchone()
            conn.commit()
        except HTTPException:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                raise HTTPException(status_code=409, detail="A paid-by entry with this name already exists") from e
            logger.exception("create_paid_by failed")
            raise HTTPException(status_code=500, detail="Could not create paid-by entry") from e
    return {"id": int(row[0]), "ok": True}


@router.patch("/paid-by/{paid_by_id}")
async def patch_paid_by(
    paid_by_id: int, body: MasterPatchBody, current_user: User = Depends(_require_admin)
):
    fields: list[str] = []
    params: list[Any] = []
    if body.label is not None:
        nl = _normalize_label(body.label)
        if not nl:
            raise HTTPException(status_code=400, detail="label cannot be empty")
        fields.append("label = ?")
        params.append(nl)
    if body.is_active is not None:
        fields.append("is_active = ?")
        params.append(bool(body.is_active))
    if body.sort_order is not None:
        fields.append("sort_order = ?")
        params.append(int(body.sort_order))
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(paid_by_id)
    with get_conn() as conn:
        try:
            cur = execute(
                conn,
                f"UPDATE admin_expense_paid_by SET {', '.join(fields)} WHERE id = ? RETURNING id",
                params,
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Paid-by entry not found")
            conn.commit()
        except HTTPException:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                raise HTTPException(status_code=409, detail="A paid-by entry with this name already exists") from e
            raise
    return {"ok": True}


@router.delete("/paid-by/{paid_by_id}")
async def delete_paid_by(paid_by_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT COUNT(*) FROM admin_company_expenses WHERE paid_by_id = ?",
            (paid_by_id,),
        )
        n = int(cur.fetchone()[0])
        if n > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete: {n} expense(s) reference this paid-by entry. Deactivate it instead.",
            )
        cur = execute(conn, "DELETE FROM admin_expense_paid_by WHERE id = ? RETURNING id", (paid_by_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Paid-by entry not found")
        conn.commit()
    return {"ok": True}
