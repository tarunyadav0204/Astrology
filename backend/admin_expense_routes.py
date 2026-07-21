"""
Admin-only internal expense log with optional invoice attachment (PDF / images).
Invoices are stored in a private GCS bucket (EXPENSE_INVOICE_GCS_BUCKET). Optional local disk for dev
when EXPENSE_INVOICE_ALLOW_LOCAL=1 and bucket unset.
"""
from __future__ import annotations

import io
import logging
import os
import re
import secrets
import zipfile
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional, Tuple
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/expenses", tags=["admin_expenses"])

EXPENSE_INVOICE_DIR = Path(
    os.getenv("EXPENSE_INVOICE_DIR") or (Path(__file__).resolve().parent / "storage" / "admin_expense_invoices")
)
EXPENSE_INVOICE_MAX_BYTES = int(os.getenv("EXPENSE_INVOICE_MAX_BYTES") or str(20 * 1024 * 1024))

_ALLOW_LOCAL = os.getenv("EXPENSE_INVOICE_ALLOW_LOCAL", "").strip().lower() in ("1", "true", "yes")

_ALLOWED_MIME_EXT: dict[str, str] = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _sanitize_original_filename(name: str, ext: str) -> str:
    raw = os.path.basename((name or "").strip()) or f"invoice{ext}"
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".", " ") else "_" for ch in raw).strip()
    if not safe:
        safe = f"invoice{ext}"
    return safe[:200]


def _guess_ext_from_filename(filename: str) -> Optional[str]:
    lower = (filename or "").lower().strip()
    for ext in (".pdf", ".jpg", ".jpeg", ".png", ".webp"):
        if lower.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return None


async def _validate_and_read_invoice(upload: UploadFile) -> Tuple[str, str, bytes, str]:
    """Returns (original_filename, ext, file_bytes, mime)."""
    blob = await upload.read()
    if not blob:
        raise HTTPException(status_code=400, detail="Invoice file is empty.")
    if len(blob) > EXPENSE_INVOICE_MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Invoice too large (max {EXPENSE_INVOICE_MAX_BYTES // (1024 * 1024)} MB).",
        )

    mime = (upload.content_type or "").strip().lower().split(";")[0].strip()
    if mime == "image/jpg":
        mime = "image/jpeg"
    ext = _ALLOWED_MIME_EXT.get(mime)
    if ext is None:
        ext = _guess_ext_from_filename(upload.filename or "")
        if ext == ".jpg":
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"
        elif ext == ".webp":
            mime = "image/webp"
        elif ext == ".pdf":
            mime = "application/pdf"

    if ext is None or mime not in _ALLOWED_MIME_EXT:
        raise HTTPException(
            status_code=400,
            detail="Invoice must be PDF, JPEG, PNG, or WebP.",
        )

    if mime == "application/pdf" and not blob.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file.")
    if mime == "image/png" and not blob.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(status_code=400, detail="Invalid PNG file.")
    if mime == "image/jpeg" and not blob.startswith(b"\xff\xd8\xff"):
        raise HTTPException(status_code=400, detail="Invalid JPEG file.")
    if mime == "image/webp" and (len(blob) < 12 or blob[0:4] != b"RIFF" or blob[8:12] != b"WEBP"):
        raise HTTPException(status_code=400, detail="Invalid WebP file.")

    original = _sanitize_original_filename(upload.filename or "", ext)
    return original, ext, blob, mime


def _persist_invoice_bytes(_original: str, ext: str, blob: bytes, mime: str) -> Tuple[str, int]:
    """
    Store invoice; returns (storage_ref, size_bytes).
    storage_ref is gs://bucket/key when EXPENSE_INVOICE_GCS_BUCKET is set, else absolute file path if allow_local.
    """
    from utils import expense_invoice_gcs as gcs

    bucket = gcs.expense_invoice_bucket_name()
    if bucket:
        try:
            suffix = f"{secrets.token_hex(16)}{ext}"
            uri = gcs.upload_invoice_bytes(blob, object_suffix=suffix, content_type=mime)
            return uri, len(blob)
        except Exception as e:
            logger.exception("GCS invoice upload failed")
            raise HTTPException(status_code=502, detail=f"Could not upload invoice to storage: {e!s}") from e

    if _ALLOW_LOCAL:
        stored_name = f"{secrets.token_hex(16)}{ext}"
        EXPENSE_INVOICE_DIR.mkdir(parents=True, exist_ok=True)
        stored_path = EXPENSE_INVOICE_DIR / stored_name
        stored_path.write_bytes(blob)
        return str(stored_path.resolve()), len(blob)

    raise HTTPException(
        status_code=503,
        detail=(
            "Invoice storage is not configured. Set EXPENSE_INVOICE_GCS_BUCKET (and GOOGLE_SERVICE_ACCOUNT_KEY) "
            "for Google Cloud Storage, or for local development only set EXPENSE_INVOICE_ALLOW_LOCAL=1."
        ),
    )


def _is_gs_storage(storage_path: str) -> bool:
    return (storage_path or "").strip().lower().startswith("gs://")


def _invoice_local_path_allowed(storage_path: str) -> bool:
    try:
        p = Path(storage_path).resolve()
        root = EXPENSE_INVOICE_DIR.resolve()
        return str(p).startswith(str(root) + os.sep) and p.is_file()
    except Exception:
        return False


def _delete_invoice_storage(storage_path: Optional[str]) -> None:
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
            logger.warning("Could not delete GCS invoice %s: %s", path, e)
    elif _invoice_local_path_allowed(path):
        try:
            Path(path).unlink(missing_ok=True)
        except OSError as e:
            logger.warning("Could not delete local invoice file %s: %s", path, e)


def _parse_spent_date(s: str) -> date:
    t = (s or "").strip()
    try:
        return date.fromisoformat(t)
    except ValueError:
        raise HTTPException(status_code=400, detail="spent_date must be YYYY-MM-DD")


def _parse_amount(s: str) -> Decimal:
    t = (s or "").strip().replace(",", "")
    try:
        v = Decimal(t)
    except InvalidOperation:
        raise HTTPException(status_code=400, detail="amount must be a decimal number")
    if v <= 0:
        raise HTTPException(status_code=400, detail="amount must be greater than zero")
    if v > Decimal("999999999999.99"):
        raise HTTPException(status_code=400, detail="amount too large")
    return v.quantize(Decimal("0.01"))


def _parse_required_int_id(name: str, raw: str) -> int:
    try:
        i = int(str(raw).strip())
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{name} must be a positive integer")
    if i < 1:
        raise HTTPException(status_code=400, detail=f"{name} must be positive")
    return i


def _expense_filters(
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    vendor_id: Optional[int] = None,
    paid_by_id: Optional[int] = None,
) -> tuple[str, list[Any]]:
    conditions = ["1=1"]
    params: list[Any] = []
    if date_from and date_from.strip():
        conditions.append("e.spent_date >= ?::date")
        params.append(_parse_spent_date(date_from).isoformat())
    if date_to and date_to.strip():
        conditions.append("e.spent_date <= ?::date")
        params.append(_parse_spent_date(date_to).isoformat())
    if category and category.strip():
        conditions.append("e.category ILIKE ?")
        params.append(f"%{category.strip()}%")
    if vendor_id is not None:
        conditions.append("e.vendor_id = ?")
        params.append(int(vendor_id))
    if paid_by_id is not None:
        conditions.append("e.paid_by_id = ?")
        params.append(int(paid_by_id))
    return " AND ".join(conditions), params


def _expense_summary(conn, where_sql: str, params: list[Any]) -> dict[str, Any]:
    cur = execute(
        conn,
        f"""
        SELECT
            UPPER(COALESCE(NULLIF(TRIM(e.currency), ''), 'INR')) AS currency,
            COUNT(*) AS expense_count,
            COALESCE(SUM(e.amount), 0)::text AS total_amount
        FROM admin_company_expenses e
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY 1
        """,
        params,
    )
    totals = [
        {"currency": str(r[0] or "INR"), "count": int(r[1] or 0), "amount": str(r[2] or "0")}
        for r in (cur.fetchall() or [])
    ]
    return {
        "count": sum(item["count"] for item in totals),
        "totals_by_currency": totals,
    }


def _xlsx_col(index: int) -> str:
    out = ""
    n = int(index)
    while n:
        n, remainder = divmod(n - 1, 26)
        out = chr(65 + remainder) + out
    return out


def _xlsx_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return escape(text)


def _build_expenses_xlsx(rows: list[tuple[Any, ...]], summary: dict[str, Any]) -> bytes:
    """Build a small standards-compliant XLSX without adding a runtime dependency."""
    sheet_rows: list[str] = []

    def add_row(
        values: list[Any],
        *,
        header: bool = False,
        numeric_columns: set[int] | None = None,
        money_columns: set[int] | None = None,
    ) -> int:
        row_num = len(sheet_rows) + 1
        cells = []
        numeric_columns = numeric_columns or set()
        money_columns = money_columns or set()
        for col_num, value in enumerate(values, start=1):
            ref = f"{_xlsx_col(col_num)}{row_num}"
            if (col_num in numeric_columns or col_num in money_columns) and value not in (None, ""):
                style = ' s="2"' if col_num in money_columns else ""
                cells.append(f'<c r="{ref}"{style}><v>{_xlsx_text(value)}</v></c>')
            else:
                style = ' s="1"' if header else ""
                cells.append(
                    f'<c r="{ref}" t="inlineStr"{style}><is><t xml:space="preserve">'
                    f"{_xlsx_text(value)}</t></is></c>"
                )
        sheet_rows.append(f'<row r="{row_num}">{"".join(cells)}</row>')
        return row_num

    add_row(["Expense export"], header=True)
    add_row(["Filtered expense count", summary.get("count", 0)], numeric_columns={2})
    for total in summary.get("totals_by_currency") or []:
        add_row(
            [f"Total ({total['currency']})", total["amount"], f"{total['count']} entries"],
            money_columns={2},
        )
    add_row([])
    header_row = add_row(
        [
            "ID",
            "Spent date",
            "Vendor",
            "Paid by",
            "Category",
            "Amount",
            "Currency",
            "Notes",
            "Invoice filename",
            "Created at",
        ],
        header=True,
    )
    for row in rows:
        add_row(
            [
                row[0],
                row[1].isoformat() if row[1] else "",
                row[4] or "",
                row[11] or "",
                row[5] or "",
                row[2] or "0",
                row[3] or "INR",
                row[14] or "",
                row[7] or "",
                row[9].isoformat() if row[9] else "",
            ],
            numeric_columns={1},
            money_columns={6},
        )

    last_row = len(sheet_rows)
    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <dimension ref="A1:J{last_row}"/>
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="{header_row}" topLeftCell="A{header_row + 1}" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <cols>
    <col min="1" max="1" width="10" customWidth="1"/><col min="2" max="2" width="14" customWidth="1"/>
    <col min="3" max="4" width="24" customWidth="1"/><col min="5" max="5" width="20" customWidth="1"/>
    <col min="6" max="7" width="14" customWidth="1"/><col min="8" max="8" width="42" customWidth="1"/>
    <col min="9" max="10" width="24" customWidth="1"/>
  </cols>
  <sheetData>{"".join(sheet_rows)}</sheetData>
  <autoFilter ref="A{header_row}:J{last_row}"/>
</worksheet>"""
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="Expenses" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""
    styles = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF5B3CC4"/><bgColor indexed="64"/></patternFill></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1"/><xf numFmtId="4" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", styles)
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)
    return output.getvalue()


@router.post("")
async def admin_create_expense(
    spent_date: str = Form(...),
    amount: str = Form(...),
    vendor_id: str = Form(...),
    paid_by_id: str = Form(...),
    currency: str = Form("INR"),
    category: str = Form(""),
    notes: str = Form(""),
    invoice: Optional[UploadFile] = File(None),
    current_user: User = Depends(_require_admin),
):
    sd = _parse_spent_date(spent_date)
    amt = _parse_amount(amount)
    vid = _parse_required_int_id("vendor_id", vendor_id)
    pid = _parse_required_int_id("paid_by_id", paid_by_id)
    cur = (currency or "INR").strip().upper()[:8] or "INR"
    cat = (category or "").strip()[:200]
    note = (notes or "").strip()[:8000] or None

    inv_name: Optional[str] = None
    inv_path: Optional[str] = None
    inv_mime: Optional[str] = None
    inv_size = 0
    if invoice is not None and (invoice.filename or "").strip():
        inv_name, ext, blob, inv_mime = await _validate_and_read_invoice(invoice)
        inv_path, inv_size = _persist_invoice_bytes(inv_name, ext, blob, inv_mime)

    try:
        with get_conn() as conn:
            cur_v = execute(
                conn,
                "SELECT label FROM admin_expense_vendors WHERE id = ? AND is_active = TRUE",
                (vid,),
            )
            vrow = cur_v.fetchone()
            if not vrow:
                raise HTTPException(status_code=400, detail="Invalid or inactive vendor")
            vendor_label = (vrow[0] or "").strip()[:500]
            if not vendor_label:
                raise HTTPException(status_code=400, detail="Invalid vendor")

            cur_p = execute(
                conn,
                "SELECT label FROM admin_expense_paid_by WHERE id = ? AND is_active = TRUE",
                (pid,),
            )
            prow = cur_p.fetchone()
            if not prow:
                raise HTTPException(status_code=400, detail="Invalid or inactive paid-by entry")

            cur_db = execute(
                conn,
                """
                INSERT INTO admin_company_expenses (
                    spent_date, amount, currency, vendor, vendor_id, paid_by_id, category, notes,
                    invoice_original_name, invoice_storage_path, invoice_mime, invoice_size_bytes,
                    created_by_userid, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW())
                RETURNING id
                """,
                (
                    sd,
                    str(amt),
                    cur,
                    vendor_label,
                    vid,
                    pid,
                    cat,
                    note,
                    inv_name,
                    inv_path,
                    inv_mime,
                    inv_size,
                    int(current_user.userid),
                ),
            )
            row = cur_db.fetchone()
            if not row:
                raise HTTPException(status_code=500, detail="Failed to save expense")
            eid = int(row[0])
            conn.commit()
    except HTTPException:
        if inv_path:
            _delete_invoice_storage(inv_path)
        raise
    except Exception:
        if inv_path:
            _delete_invoice_storage(inv_path)
        raise

    return {"id": eid, "ok": True}


@router.get("")
async def admin_list_expenses(
    current_user: User = Depends(_require_admin),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    vendor_id: Optional[int] = Query(None, ge=1),
    paid_by_id: Optional[int] = Query(None, ge=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    where_sql, params = _expense_filters(
        date_from=date_from,
        date_to=date_to,
        category=category,
        vendor_id=vendor_id,
        paid_by_id=paid_by_id,
    )
    offset = (page - 1) * limit

    with get_conn() as conn:
        cur = execute(
            conn,
            f"SELECT COUNT(*) FROM admin_company_expenses e WHERE {where_sql}",
            params,
        )
        total = int(cur.fetchone()[0])
        summary = _expense_summary(conn, where_sql, params)

        cur = execute(
            conn,
            f"""
            SELECT
                e.id,
                e.spent_date,
                e.amount::text,
                e.currency,
                COALESCE(v.label, e.vendor, '') AS vendor_label,
                e.category,
                LEFT(COALESCE(e.notes, ''), 200) AS notes_preview,
                e.invoice_original_name,
                (e.invoice_storage_path IS NOT NULL AND e.invoice_storage_path <> '') AS has_invoice,
                e.created_at,
                e.created_by_userid,
                COALESCE(pb.label, '') AS paid_by_label,
                e.vendor_id,
                e.paid_by_id,
                COALESCE(e.notes, '') AS notes
            FROM admin_company_expenses e
            LEFT JOIN admin_expense_vendors v ON v.id = e.vendor_id
            LEFT JOIN admin_expense_paid_by pb ON pb.id = e.paid_by_id
            WHERE {where_sql}
            ORDER BY e.spent_date DESC, e.id DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset],
        )
        rows = cur.fetchall() or []

    items = []
    for r in rows:
        items.append(
            {
                "id": r[0],
                "spent_date": r[1].isoformat() if r[1] else None,
                "amount": r[2],
                "currency": r[3],
                "vendor": r[4],
                "category": r[5],
                "notes_preview": r[6],
                "invoice_original_name": r[7],
                "has_invoice": bool(r[8]),
                "created_at": r[9].isoformat() if r[9] else None,
                "created_by_userid": r[10],
                "paid_by": r[11],
                "vendor_id": r[12],
                "paid_by_id": r[13],
                "notes": r[14],
            }
        )

    return {"total": total, "page": page, "limit": limit, "summary": summary, "items": items}


@router.get("/export")
async def admin_export_expenses(
    current_user: User = Depends(_require_admin),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    vendor_id: Optional[int] = Query(None, ge=1),
    paid_by_id: Optional[int] = Query(None, ge=1),
):
    where_sql, params = _expense_filters(
        date_from=date_from,
        date_to=date_to,
        category=category,
        vendor_id=vendor_id,
        paid_by_id=paid_by_id,
    )
    with get_conn() as conn:
        summary = _expense_summary(conn, where_sql, params)
        cur = execute(
            conn,
            f"""
            SELECT
                e.id,
                e.spent_date,
                e.amount::text,
                e.currency,
                COALESCE(v.label, e.vendor, '') AS vendor_label,
                e.category,
                LEFT(COALESCE(e.notes, ''), 200) AS notes_preview,
                e.invoice_original_name,
                (e.invoice_storage_path IS NOT NULL AND e.invoice_storage_path <> '') AS has_invoice,
                e.created_at,
                e.created_by_userid,
                COALESCE(pb.label, '') AS paid_by_label,
                e.vendor_id,
                e.paid_by_id,
                COALESCE(e.notes, '') AS notes
            FROM admin_company_expenses e
            LEFT JOIN admin_expense_vendors v ON v.id = e.vendor_id
            LEFT JOIN admin_expense_paid_by pb ON pb.id = e.paid_by_id
            WHERE {where_sql}
            ORDER BY e.spent_date DESC, e.id DESC
            """,
            params,
        )
        rows = list(cur.fetchall() or [])

    workbook = _build_expenses_xlsx(rows, summary)
    filename = f"expenses-{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        io.BytesIO(workbook),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{expense_id}")
async def admin_update_expense(
    expense_id: int,
    spent_date: str = Form(...),
    amount: str = Form(...),
    vendor_id: str = Form(...),
    paid_by_id: str = Form(...),
    currency: str = Form("INR"),
    category: str = Form(""),
    notes: str = Form(""),
    remove_invoice: bool = Form(False),
    invoice: Optional[UploadFile] = File(None),
    current_user: User = Depends(_require_admin),
):
    sd = _parse_spent_date(spent_date)
    amt = _parse_amount(amount)
    vid = _parse_required_int_id("vendor_id", vendor_id)
    pid = _parse_required_int_id("paid_by_id", paid_by_id)
    cur_code = (currency or "INR").strip().upper()[:8] or "INR"
    cat = (category or "").strip()[:200]
    note = (notes or "").strip()[:8000] or None

    new_name: Optional[str] = None
    new_path: Optional[str] = None
    new_mime: Optional[str] = None
    new_size = 0
    if invoice is not None and (invoice.filename or "").strip():
        new_name, ext, blob, new_mime = await _validate_and_read_invoice(invoice)
        new_path, new_size = _persist_invoice_bytes(new_name, ext, blob, new_mime)

    old_path: Optional[str] = None
    try:
        with get_conn() as conn:
            existing_cur = execute(
                conn,
                """
                SELECT invoice_original_name, invoice_storage_path, invoice_mime, invoice_size_bytes
                FROM admin_company_expenses
                WHERE id = ?
                """,
                (expense_id,),
            )
            existing = existing_cur.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Expense not found")
            old_path = existing[1]

            vendor_cur = execute(
                conn,
                """
                SELECT label
                FROM admin_expense_vendors
                WHERE id = ?
                  AND (
                    is_active = TRUE
                    OR id = (SELECT vendor_id FROM admin_company_expenses WHERE id = ?)
                  )
                """,
                (vid, expense_id),
            )
            vendor_row = vendor_cur.fetchone()
            if not vendor_row or not (vendor_row[0] or "").strip():
                raise HTTPException(status_code=400, detail="Invalid or inactive vendor")
            vendor_label = (vendor_row[0] or "").strip()[:500]

            paid_cur = execute(
                conn,
                """
                SELECT label
                FROM admin_expense_paid_by
                WHERE id = ?
                  AND (
                    is_active = TRUE
                    OR id = (SELECT paid_by_id FROM admin_company_expenses WHERE id = ?)
                  )
                """,
                (pid, expense_id),
            )
            if not paid_cur.fetchone():
                raise HTTPException(status_code=400, detail="Invalid or inactive paid-by entry")

            if new_path:
                invoice_values = (new_name, new_path, new_mime, new_size)
            elif remove_invoice:
                invoice_values = (None, None, None, 0)
            else:
                invoice_values = (existing[0], existing[1], existing[2], int(existing[3] or 0))

            execute(
                conn,
                """
                UPDATE admin_company_expenses
                SET spent_date = ?,
                    amount = ?,
                    currency = ?,
                    vendor = ?,
                    vendor_id = ?,
                    paid_by_id = ?,
                    category = ?,
                    notes = ?,
                    invoice_original_name = ?,
                    invoice_storage_path = ?,
                    invoice_mime = ?,
                    invoice_size_bytes = ?,
                    updated_at = NOW()
                WHERE id = ?
                """,
                (
                    sd,
                    str(amt),
                    cur_code,
                    vendor_label,
                    vid,
                    pid,
                    cat,
                    note,
                    *invoice_values,
                    expense_id,
                ),
            )
            conn.commit()
    except Exception:
        if new_path:
            _delete_invoice_storage(new_path)
        raise

    if old_path and (new_path or remove_invoice) and old_path != new_path:
        _delete_invoice_storage(old_path)
    return {"id": expense_id, "ok": True}


@router.get("/{expense_id}/invoice")
async def admin_download_invoice(expense_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT invoice_original_name, invoice_storage_path, invoice_mime
            FROM admin_company_expenses
            WHERE id = ?
            """,
            (expense_id,),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Expense not found")
    orig, path, mime = row[0], row[1], row[2] or "application/octet-stream"
    if not path or not str(path).strip():
        raise HTTPException(status_code=404, detail="No invoice on file")

    dl_name = orig or f"expense-{expense_id}-invoice"
    safe_name = re.sub(r"[^\w.\- ]+", "_", str(dl_name))[:180]

    if _is_gs_storage(str(path)):
        try:
            from utils import expense_invoice_gcs as gcs

            data, ct = gcs.download_invoice_bytes(str(path).strip())
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Invoice file not found in storage")
        except Exception as e:
            logger.exception("GCS invoice download failed")
            raise HTTPException(status_code=502, detail=f"Could not read invoice: {e!s}") from e
        disp = f'attachment; filename="{safe_name}"'
        use_mime = mime if (not ct or ct == "application/octet-stream") else ct
        return StreamingResponse(
            io.BytesIO(data),
            media_type=use_mime,
            headers={"Content-Disposition": disp},
        )

    if not _invoice_local_path_allowed(str(path)):
        raise HTTPException(status_code=404, detail="No invoice on file")

    return FileResponse(
        str(path),
        media_type=mime,
        filename=safe_name,
    )


@router.delete("/{expense_id}")
async def admin_delete_expense(expense_id: int, current_user: User = Depends(_require_admin)):
    with get_conn() as conn:
        cur = execute(
            conn,
            "SELECT invoice_storage_path FROM admin_company_expenses WHERE id = ?",
            (expense_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Expense not found")
        storage_path = row[0]
        execute(conn, "DELETE FROM admin_company_expenses WHERE id = ?", (expense_id,))
        conn.commit()

    _delete_invoice_storage(storage_path)

    return {"ok": True}
