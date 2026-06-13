"""
Admin issue / enhancement tracker with optional screenshot (same GCS bucket as expense invoices).
"""
from __future__ import annotations

import io
import logging
import os
import re
import secrets
from datetime import date
from pathlib import Path
from typing import Any, Optional, Tuple

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/issues", tags=["admin_issues"])

ISSUE_SCREENSHOT_DIR = Path(
    os.getenv("ISSUE_SCREENSHOT_DIR")
    or (Path(__file__).resolve().parent / "storage" / "admin_issue_screenshots")
)
ISSUE_SCREENSHOT_MAX_BYTES = int(os.getenv("ISSUE_SCREENSHOT_MAX_BYTES") or str(10 * 1024 * 1024))
_ALLOW_LOCAL = os.getenv("EXPENSE_INVOICE_ALLOW_LOCAL", "").strip().lower() in ("1", "true", "yes")

_VALID_STATUSES = frozenset({"open", "fixed", "closed"})

_ALLOWED_IMAGE_MIME_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class IssueUpdateRequest(BaseModel):
    status: Optional[str] = None
    due_date: Optional[str] = None
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=20000)


class IssueCommentRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=8000)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _sanitize_filename(name: str, ext: str) -> str:
    raw = os.path.basename((name or "").strip()) or f"screenshot{ext}"
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in raw).strip()
    return (safe or f"screenshot{ext}")[:200]


def _guess_image_ext(filename: str) -> Optional[str]:
    lower = (filename or "").lower().strip()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if lower.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return None


async def _validate_and_read_screenshot(upload: UploadFile) -> Tuple[str, str, bytes, str]:
    blob = await upload.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Screenshot file is empty.")
    if len(blob) > ISSUE_SCREENSHOT_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Screenshot too large (max {ISSUE_SCREENSHOT_MAX_BYTES // (1024 * 1024)} MB).",
        )

    mime = (upload.content_type or "").strip().lower().split(";")[0].strip()
    if mime == "image/jpg":
        mime = "image/jpeg"
    ext = _ALLOWED_IMAGE_MIME_EXT.get(mime)
    if ext is None:
        ext = _guess_image_ext(upload.filename or "")
        if ext == ".jpg":
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"
        elif ext == ".webp":
            mime = "image/webp"

    if ext is None or mime not in _ALLOWED_IMAGE_MIME_EXT:
        raise HTTPException(status_code=400, detail="Screenshot must be JPEG, PNG, or WebP.")

    if mime == "image/png" and not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="Invalid PNG file.")
    if mime == "image/jpeg" and not blob.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=400, detail="Invalid JPEG file.")
    if mime == "image/webp" and (len(blob) < 12 or blob[0:4] != b"RIFF" or blob[8:12] != b"WEBP"):
        raise HTTPException(status_code=400, detail="Invalid WebP file.")

    original = _sanitize_filename(upload.filename or "", ext)
    return original, ext, blob, mime


def _persist_screenshot_bytes(_original: str, ext: str, blob: bytes, mime: str) -> Tuple[str, int]:
    from utils import expense_invoice_gcs as gcs

    bucket = gcs.expense_invoice_bucket_name()
    if bucket:
        try:
            suffix = f"{secrets.token_hex(16)}{ext}"
            uri = gcs.upload_issue_screenshot_bytes(blob, object_suffix=suffix, content_type=mime)
            return uri, len(blob)
        except Exception as e:
            logger.exception("GCS issue screenshot upload failed")
            raise HTTPException(status_code=502, detail=f"Could not upload screenshot: {e!s}") from e

    if _ALLOW_LOCAL:
        stored_name = f"{secrets.token_hex(16)}{ext}"
        ISSUE_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        stored_path = ISSUE_SCREENSHOT_DIR / stored_name
        stored_path.write_bytes(blob)
        return str(stored_path.resolve()), len(blob)

    raise HTTPException(
        status_code=503,
        detail=(
            "Screenshot storage is not configured. Set EXPENSE_INVOICE_GCS_BUCKET "
            "(and GOOGLE_SERVICE_ACCOUNT_KEY), or for local dev EXPENSE_INVOICE_ALLOW_LOCAL=1."
        ),
    )


def _is_gs_storage(storage_path: str) -> bool:
    return (storage_path or "").strip().lower().startswith("gs://")


def _screenshot_local_path_allowed(storage_path: str) -> bool:
    try:
        p = Path(storage_path).resolve()
        root = ISSUE_SCREENSHOT_DIR.resolve()
        return str(p).startswith(str(root) + os.sep) and p.is_file()
    except Exception:
        return False


def _delete_screenshot_storage(storage_path: Optional[str]) -> None:
    if not storage_path or not str(storage_path).strip():
        return
    path = str(storage_path).strip()
    if _is_gs_storage(path):
        try:
            from utils import expense_invoice_gcs as gcs

            gcs.delete_invoice_object(path)
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning("Could not delete GCS screenshot %s: %s", path, e)
    elif _screenshot_local_path_allowed(path):
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as e:
            logger.warning("Could not delete local screenshot %s: %s", path, e)


def _parse_optional_date(raw: Optional[str], field: str) -> Optional[date]:
    if raw is None:
        return None
    t = str(raw).strip()
    if not t:
        return None
    try:
        return date.fromisoformat(t)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} must be YYYY-MM-DD")


def _normalize_status(raw: Optional[str]) -> str:
    s = (raw or "open").strip().lower()
    if s not in _VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}")
    return s


def _issue_row_to_dict(row: tuple, *, include_description: bool = False) -> dict[str, Any]:
    out = {
        "id": row[0],
        "title": row[1],
        "status": row[2],
        "opened_at": row[3].isoformat() if row[3] else None,
        "due_date": row[4].isoformat() if row[4] else None,
        "has_screenshot": bool(row[5]),
        "screenshot_original_name": row[6],
        "comment_count": int(row[7] or 0),
        "created_by_userid": row[8],
        "created_by_name": row[9] or "",
        "updated_at": row[10].isoformat() if row[10] else None,
    }
    if include_description:
        out["description"] = row[11] or ""
    return out


def _load_comments(conn, issue_id: int) -> list[dict[str, Any]]:
    cur = execute(
        conn,
        """
        SELECT c.id, c.body, c.created_at, c.created_by_userid, COALESCE(u.name, u.phone, '') AS author
        FROM admin_issue_comments c
        LEFT JOIN users u ON u.userid = c.created_by_userid
        WHERE c.issue_id = ?
        ORDER BY c.created_at ASC
        """,
        (issue_id,),
    )
    return [
        {
            "id": r[0],
            "body": r[1],
            "created_at": r[2].isoformat() if r[2] else None,
            "created_by_userid": r[3],
            "author": r[4] or "",
        }
        for r in (cur.fetchall() or [])
    ]


@router.get("")
async def admin_list_issues(
    current_user: User = Depends(_require_admin),
    status: Optional[str] = Query(None, description="open | fixed | closed"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
):
    conditions = ["1=1"]
    params: list[Any] = []
    if status and status.strip():
        st = _normalize_status(status)
        conditions.append("i.status = ?")
        params.append(st)

    where_sql = " AND ".join(conditions)
    offset = (page - 1) * limit

    with get_conn() as conn:
        cur = execute(conn, f"SELECT COUNT(*) FROM admin_issues i WHERE {where_sql}", params)
        total = int((cur.fetchone() or [0])[0] or 0)
        cur = execute(
            conn,
            f"""
            SELECT
                i.id,
                i.title,
                i.status,
                i.opened_at,
                i.due_date,
                (i.screenshot_storage_path IS NOT NULL AND i.screenshot_storage_path <> '') AS has_screenshot,
                i.screenshot_original_name,
                (SELECT COUNT(*)::int FROM admin_issue_comments c WHERE c.issue_id = i.id) AS comment_count,
                i.created_by_userid,
                u.name AS created_by_name,
                i.updated_at,
                i.description
            FROM admin_issues i
            LEFT JOIN users u ON u.userid = i.created_by_userid
            WHERE {where_sql}
            ORDER BY i.opened_at DESC, i.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall() or []

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": [_issue_row_to_dict(r, include_description=True) for r in rows],
    }


@router.post("")
async def admin_create_issue(
    title: str = Form(...),
    description: str = Form(""),
    due_date: str = Form(""),
    screenshot: Optional[UploadFile] = File(None),
    current_user: User = Depends(_require_admin),
):
    title_t = (title or "").strip()
    if not title_t:
        raise HTTPException(status_code=400, detail="title is required")
    if len(title_t) > 500:
        raise HTTPException(status_code=400, detail="title too long (max 500)")
    desc = (description or "").strip()[:20000]
    due = _parse_optional_date(due_date, "due_date")

    shot_name: Optional[str] = None
    shot_path: Optional[str] = None
    shot_mime: Optional[str] = None
    shot_size = 0
    if screenshot is not None and (screenshot.filename or "").strip():
        shot_name, ext, blob, shot_mime = await _validate_and_read_screenshot(screenshot)
        shot_path, shot_size = _persist_screenshot_bytes(shot_name, ext, blob, shot_mime)

    try:
        with get_conn() as conn:
            cur = execute(
                conn,
                """
                INSERT INTO admin_issues (
                    title, description, status, due_date,
                    screenshot_original_name, screenshot_storage_path, screenshot_mime, screenshot_size_bytes,
                    created_by_userid, updated_at
                )
                VALUES (?, ?, 'open', ?, ?, ?, ?, ?, ?, NOW())
                RETURNING id
                """,
                (
                    title_t,
                    desc,
                    due.isoformat() if due else None,
                    shot_name,
                    shot_path,
                    shot_mime,
                    shot_size,
                    int(current_user.userid),
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create issue")
            issue_id = int(row[0])
            conn.commit()
    except HTTPException:
        if shot_path:
            _delete_screenshot_storage(shot_path)
        raise
    except Exception:
        if shot_path:
            _delete_screenshot_storage(shot_path)
        raise

    return {"ok": True, "id": issue_id}


@router.get("/{issue_id}")
async def admin_get_issue(issue_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT
                i.id,
                i.title,
                i.status,
                i.opened_at,
                i.due_date,
                (i.screenshot_storage_path IS NOT NULL AND i.screenshot_storage_path <> '') AS has_screenshot,
                i.screenshot_original_name,
                (SELECT COUNT(*)::int FROM admin_issue_comments c WHERE c.issue_id = i.id) AS comment_count,
                i.created_by_userid,
                u.name AS created_by_name,
                i.updated_at,
                i.description
            FROM admin_issues i
            LEFT JOIN users u ON u.userid = i.created_by_userid
            WHERE i.id = ?
            """,
            (issue_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Issue not found")
        comments = _load_comments(conn, issue_id)

    return {"issue": _issue_row_to_dict(row, include_description=True), "comments": comments}


@router.patch("/{issue_id}")
async def admin_update_issue(
    issue_id: int,
    body: IssueUpdateRequest,
    current_user: User = Depends(_require_admin),
):
    fields: list[str] = []
    params: list[Any] = []

    if body.status is not None:
        fields.append("status = ?")
        params.append(_normalize_status(body.status))
    if body.due_date is not None:
        due = _parse_optional_date(body.due_date, "due_date")
        fields.append("due_date = ?")
        params.append(due.isoformat() if due else None)
    if body.title is not None:
        title_t = body.title.strip()
        if not title_t:
            raise HTTPException(status_code=400, detail="title cannot be empty")
        fields.append("title = ?")
        params.append(title_t[:500])
    if body.description is not None:
        fields.append("description = ?")
        params.append(body.description.strip()[:20000])

    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    fields.append("updated_at = NOW()")
    params.append(issue_id)

    with get_conn() as conn:
        cur = execute(
            conn,
            f"UPDATE admin_issues SET {', '.join(fields)} WHERE id = ? RETURNING id",
            params,
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Issue not found")
        conn.commit()

    return {"ok": True, "id": issue_id}


@router.post("/{issue_id}/comments")
async def admin_add_issue_comment(
    issue_id: int,
    body: IssueCommentRequest,
    current_user: User = Depends(_require_admin),
):
    text = body.body.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment body is required")

    with get_conn() as conn:
        cur = execute(conn, "SELECT id FROM admin_issues WHERE id = ?", (issue_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Issue not found")

        cur = execute(
            conn,
            """
            INSERT INTO admin_issue_comments (issue_id, body, created_by_userid)
            VALUES (?, ?, ?)
            RETURNING id, created_at
            """,
            (issue_id, text[:8000], int(current_user.userid)),
        )
        row = cur.fetchone()
        execute(conn, "UPDATE admin_issues SET updated_at = NOW() WHERE id = ?", (issue_id,))
        conn.commit()

    return {
        "ok": True,
        "comment": {
            "id": int(row[0]),
            "body": text[:8000],
            "created_at": row[1].isoformat() if row[1] else None,
            "created_by_userid": int(current_user.userid),
            "author": current_user.name or current_user.phone or "",
        },
    }


@router.get("/{issue_id}/screenshot")
async def admin_download_issue_screenshot(issue_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT screenshot_original_name, screenshot_storage_path, screenshot_mime
            FROM admin_issues
            WHERE id = ?
            """,
            (issue_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Issue not found")
    orig, path, mime = row[0], row[1], row[2] or "application/octet-stream"
    if not path or not str(path).strip():
        raise HTTPException(status_code=404, detail="No screenshot on file")

    dl_name = orig or f"issue-{issue_id}-screenshot"
    safe_name = re.sub(r"[^\w.\- ]+", "_", str(dl_name))[:180]

    if _is_gs_storage(str(path)):
        try:
            from utils import expense_invoice_gcs as gcs

            data, ct = gcs.download_invoice_bytes(str(path).strip())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Screenshot not found in storage")
        except Exception as e:
            logger.exception("GCS screenshot download failed")
            raise HTTPException(status_code=502, detail=f"Could not read screenshot: {e!s}") from e
        use_mime = mime if (not ct or ct == "application/octet-stream") else ct
        return StreamingResponse(
            io.BytesIO(data),
            media_type=use_mime,
            headers={"Content-Disposition": f'inline; filename="{safe_name}"'},
        )

    if not _screenshot_local_path_allowed(str(path)):
        raise HTTPException(status_code=404, detail="No screenshot on file")

    return FileResponse(str(path), media_type=mime, filename=safe_name)
