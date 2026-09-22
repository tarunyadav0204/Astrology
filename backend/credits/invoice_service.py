"""Saved purchase invoices for completed credit-pack payments.

Created when Google Play or Razorpay credits are granted, and again on demand
for an older purchase that never received one. Gateway secrets stay in the
credit transaction metadata and are not copied onto the invoice.
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from credits.transaction_receipt import transaction_payment_view

logger = logging.getLogger(__name__)

PURCHASE_SOURCES = ("google_play", "razorpay")

DEFAULT_SELLER_NAME = "APEIRON LOGIC LLP"
DEFAULT_SELLER_ADDRESS = (
    "S1-41, Vatika Signature Vill, Narsinghpur, Kherki Daula Police Station, "
    "Narsinghpur, Gurgaon- 122004, Haryana, India"
)
DEFAULT_SELLER_GSTIN = "06ACNFA1124G1ZS"


class InvoiceUnavailable(Exception):
    """This credit row is not a completed credit-pack purchase."""


def _seller() -> Dict[str, str]:
    name = (os.environ.get("INVOICE_SELLER_NAME") or DEFAULT_SELLER_NAME).strip() or DEFAULT_SELLER_NAME
    address = (os.environ.get("INVOICE_SELLER_ADDRESS") or DEFAULT_SELLER_ADDRESS).strip()
    gstin = (os.environ.get("INVOICE_GSTIN") or DEFAULT_SELLER_GSTIN).strip()
    seller = {"name": name}
    if address:
        seller["address"] = address
    if gstin:
        seller["gstin"] = gstin
    return seller


def _paid_amount(money: Any) -> Optional[float]:
    if not isinstance(money, dict):
        return None
    try:
        paid = float(money.get("amount_paid"))
    except (TypeError, ValueError):
        return None
    return paid if paid > 0 else None


def _catalog_inr_money(product_id: Any, credits: int) -> Optional[Dict[str, Any]]:
    """List price for a credit pack when the gateway metadata has no amount."""
    from credits.transaction_receipt import money_from_total

    count = None
    match = re.match(r"^credits_(\d+)$", str(product_id or "").strip())
    if match:
        count = int(match.group(1))
    elif int(credits or 0) > 0:
        count = int(credits)
    if not count:
        return None
    try:
        from credits.razorpay_routes import _expected_paise_for_pack

        paise = int(_expected_paise_for_pack(count))
    except Exception:
        return None
    if paise <= 0:
        return None
    return money_from_total("INR", paise / 100.0)


def _text(value: Any) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def purchase_invoice_document(
    *,
    credits: int,
    source: str,
    reference_id: Optional[str],
    metadata: Any,
    amount_inr: Any,
    issued_at: str,
    buyer: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Public invoice body. Returns None unless this is a paid credit pack."""
    src = (source or "").strip()
    if src not in PURCHASE_SOURCES or int(credits or 0) <= 0:
        return None
    view = transaction_payment_view(src, metadata, amount_inr)
    if view.get("payment_method") not in PURCHASE_SOURCES:
        return None
    money = view.get("money") if isinstance(view.get("money"), dict) else None
    if not _paid_amount(money):
        money = _catalog_inr_money(view.get("product_id"), credits) or money
    meta = {}
    if isinstance(metadata, dict):
        meta = metadata
    elif isinstance(metadata, str) and metadata.strip():
        try:
            parsed = json.loads(metadata)
            meta = parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            meta = {}
    order_id = _text(meta.get("order_id")) or _text(reference_id)
    customer = {}
    for key in ("name", "phone", "email"):
        value = _text(buyer.get(key))
        if value:
            customer[key] = value
    document = {
        "issued_at": issued_at,
        "seller": _seller(),
        "buyer": customer,
        "credits": int(credits),
        "product_id": view.get("product_id"),
        "payment_method": view["payment_method"],
        "order_id": order_id,
        "payment_reference": _text(reference_id),
        "money": money,
    }
    return document


def _ensure_tables(conn) -> None:
    from db import execute

    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_invoice_counters (
            year INTEGER PRIMARY KEY,
            last_number INTEGER NOT NULL
        )
        """,
    )
    execute(
        conn,
        """
        CREATE TABLE IF NOT EXISTS credit_invoices (
            id SERIAL PRIMARY KEY,
            userid INTEGER NOT NULL,
            transaction_id INTEGER NOT NULL UNIQUE,
            invoice_number TEXT NOT NULL UNIQUE,
            payload TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    )


def _next_number(conn, year: int) -> str:
    from db import execute

    cursor = execute(
        conn,
        """
        INSERT INTO credit_invoice_counters (year, last_number)
        VALUES (?, 1)
        ON CONFLICT (year) DO UPDATE
        SET last_number = credit_invoice_counters.last_number + 1
        RETURNING last_number
        """,
        (year,),
    )
    row = cursor.fetchone()
    sequence = int(row[0]) if row else 1
    return f"AR-{year}-{sequence:06d}"


def _load_saved(conn, userid: int, transaction_id: int):
    from db import execute

    cursor = execute(
        conn,
        """
        SELECT id, invoice_number, payload
        FROM credit_invoices
        WHERE userid = ? AND transaction_id = ?
        """,
        (userid, transaction_id),
    )
    return cursor.fetchone()


def _document_for_transaction(conn, userid: int, transaction_id: int) -> Optional[Dict[str, Any]]:
    from db import execute

    cursor = execute(
        conn,
        """
        SELECT id, transaction_type, amount, source, reference_id, created_at, metadata
        FROM credit_transactions
        WHERE id = ? AND userid = ?
        """,
        (transaction_id, userid),
    )
    row = cursor.fetchone()
    if not row or (row[1] or "") != "earned" or (row[3] or "") not in PURCHASE_SOURCES:
        return None
    issued = row[5]
    if isinstance(issued, datetime):
        if issued.tzinfo is None:
            issued_at = issued.isoformat()
        else:
            issued_at = issued.astimezone(timezone.utc).isoformat()
    else:
        issued_at = str(issued or "")
    buyer_cursor = execute(
        conn,
        "SELECT name, phone, email FROM users WHERE userid = ?",
        (userid,),
    )
    buyer_row = buyer_cursor.fetchone()
    buyer = {
        "name": buyer_row[0] if buyer_row else None,
        "phone": buyer_row[1] if buyer_row else None,
        "email": buyer_row[2] if buyer_row else None,
    }
    return purchase_invoice_document(
        credits=int(row[2] or 0),
        source=row[3],
        reference_id=row[4],
        metadata=row[6],
        amount_inr=None,
        issued_at=issued_at,
        buyer=buyer,
    )


def _public_row(row) -> Dict[str, Any]:
    payload = json.loads(row[2]) if row[2] else {}
    if not isinstance(payload, dict):
        payload = {}
    payload["id"] = int(row[0])
    payload["invoice_number"] = row[1]
    return payload


def ensure_purchase_invoice(userid: int, transaction_id: int) -> Dict[str, Any]:
    """Return the saved invoice, creating it once for a completed purchase."""
    from db import execute, get_conn

    with get_conn() as conn:
        _ensure_tables(conn)
        existing = _load_saved(conn, userid, transaction_id)
        if existing:
            current = _public_row(existing)
            if _paid_amount(current.get("money")) and (
                str((current.get("money") or {}).get("currency") or "").upper() != "INR"
                or (current.get("money") or {}).get("tax_amount") is not None
            ):
                conn.commit()
                return current
            refreshed = _document_for_transaction(conn, userid, transaction_id)
            if refreshed and _paid_amount(refreshed.get("money")):
                current["money"] = refreshed["money"]
                if not current.get("product_id"):
                    current["product_id"] = refreshed.get("product_id")
                stored = {key: value for key, value in current.items() if key != "id"}
                execute(
                    conn,
                    "UPDATE credit_invoices SET payload = ? WHERE id = ? AND userid = ?",
                    (json.dumps(stored), current["id"], userid),
                )
                conn.commit()
                return current
            conn.commit()
            return current

        cursor = execute(
            conn,
            """
            SELECT id, transaction_type, amount, source, reference_id, created_at, metadata
            FROM credit_transactions
            WHERE id = ? AND userid = ?
            """,
            (transaction_id, userid),
        )
        row = cursor.fetchone()
        if not row or (row[1] or "") != "earned" or (row[3] or "") not in PURCHASE_SOURCES:
            raise InvoiceUnavailable()

        issued = row[5]
        if isinstance(issued, datetime):
            if issued.tzinfo is None:
                issued_at = issued.isoformat()
                year = issued.year
            else:
                issued_utc = issued.astimezone(timezone.utc)
                issued_at = issued_utc.isoformat()
                year = issued_utc.year
        else:
            issued_at = str(issued or "")
            year = datetime.now(timezone.utc).year
        buyer_cursor = execute(
            conn,
            "SELECT name, phone, email FROM users WHERE userid = ?",
            (userid,),
        )
        buyer_row = buyer_cursor.fetchone()
        buyer = {
            "name": buyer_row[0] if buyer_row else None,
            "phone": buyer_row[1] if buyer_row else None,
            "email": buyer_row[2] if buyer_row else None,
        }
        document = purchase_invoice_document(
            credits=int(row[2] or 0),
            source=row[3],
            reference_id=row[4],
            metadata=row[6],
            amount_inr=None,
            issued_at=issued_at,
            buyer=buyer,
        )
        if document is None:
            raise InvoiceUnavailable()
        number = _next_number(conn, year)
        document["invoice_number"] = number
        try:
            execute(
                conn,
                """
                INSERT INTO credit_invoices (userid, transaction_id, invoice_number, payload)
                VALUES (?, ?, ?, ?)
                """,
                (userid, transaction_id, number, json.dumps(document)),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            existing = _load_saved(conn, userid, transaction_id)
            if existing:
                return _public_row(existing)
            raise
        saved = _load_saved(conn, userid, transaction_id)
        if not saved:
            raise InvoiceUnavailable()
        return _public_row(saved)


def ensure_purchase_invoice_for_reference(userid: int, source: str, reference_id: str) -> None:
    """Save an invoice after a purchase is credited. Never fails the purchase."""
    if (source or "") not in PURCHASE_SOURCES or not (reference_id or "").strip():
        return
    try:
        from db import execute, get_conn

        with get_conn() as conn:
            cursor = execute(
                conn,
                """
                SELECT id
                FROM credit_transactions
                WHERE userid = ? AND source = ? AND reference_id = ? AND transaction_type = 'earned'
                ORDER BY id DESC
                LIMIT 1
                """,
                (userid, source, reference_id),
            )
            row = cursor.fetchone()
        if not row:
            return
        ensure_purchase_invoice(userid, int(row[0]))
    except Exception:
        logger.exception(
            "purchase invoice was not saved userid=%s source=%s reference_id=%s",
            userid,
            source,
            reference_id,
        )
