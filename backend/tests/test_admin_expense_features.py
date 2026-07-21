import io
import zipfile
from contextlib import contextmanager
from datetime import date, datetime, timezone
from xml.etree import ElementTree

import admin_expense_routes as expenses


class _Cursor:
    def __init__(self, rows=None, one=None):
        self._rows = rows
        self._one = one

    def fetchall(self):
        return self._rows or []

    def fetchone(self):
        return self._one


def test_expense_filters_include_vendor_and_paid_by():
    where_sql, params = expenses._expense_filters(
        date_from="2026-07-01",
        date_to="2026-07-31",
        category="infra",
        vendor_id=4,
        paid_by_id=8,
    )

    assert "e.spent_date >= ?::date" in where_sql
    assert "e.spent_date <= ?::date" in where_sql
    assert "e.category ILIKE ?" in where_sql
    assert "e.vendor_id = ?" in where_sql
    assert "e.paid_by_id = ?" in where_sql
    assert params == ["2026-07-01", "2026-07-31", "%infra%", 4, 8]


def test_expense_summary_keeps_currencies_separate(monkeypatch):
    monkeypatch.setattr(
        expenses,
        "execute",
        lambda *_args: _Cursor([("INR", 3, "1250.50"), ("USD", 1, "20.00")]),
    )

    summary = expenses._expense_summary(object(), "1=1", [])

    assert summary == {
        "count": 4,
        "totals_by_currency": [
            {"currency": "INR", "count": 3, "amount": "1250.50"},
            {"currency": "USD", "count": 1, "amount": "20.00"},
        ],
    }


def test_expense_export_is_valid_xlsx_with_summary_and_rows():
    rows = [
        (
            12,
            date(2026, 7, 20),
            "2499.50",
            "INR",
            "Google Cloud",
            "Hosting",
            "Monthly invoice",
            "invoice.pdf",
            True,
            datetime(2026, 7, 20, 8, 30, tzinfo=timezone.utc),
            1,
            "Company card",
            2,
            3,
            "Monthly invoice & usage <details>",
        )
    ]
    summary = {
        "count": 1,
        "totals_by_currency": [{"currency": "INR", "count": 1, "amount": "2499.50"}],
    }

    payload = expenses._build_expenses_xlsx(rows, summary)

    assert payload.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert {
            "[Content_Types].xml",
            "_rels/.rels",
            "xl/workbook.xml",
            "xl/_rels/workbook.xml.rels",
            "xl/styles.xml",
            "xl/worksheets/sheet1.xml",
        }.issubset(archive.namelist())
        sheet = archive.read("xl/worksheets/sheet1.xml")
        ElementTree.fromstring(sheet)
        text = sheet.decode("utf-8")
        assert "Expense export" in text
        assert "Google Cloud" in text
        assert "Monthly invoice &amp; usage &lt;details&gt;" in text


def test_update_expense_preserves_existing_invoice(monkeypatch):
    class _Connection:
        committed = False

        def commit(self):
            self.committed = True

    connection = _Connection()
    update_params = []

    @contextmanager
    def fake_get_conn():
        yield connection

    def fake_execute(_conn, sql, params):
        if "SELECT invoice_original_name" in sql:
            return _Cursor(one=("invoice.pdf", "gs://bucket/invoice.pdf", "application/pdf", 123))
        if "FROM admin_expense_vendors" in sql:
            return _Cursor(one=("Google Cloud",))
        if "FROM admin_expense_paid_by" in sql:
            return _Cursor(one=("Company card",))
        if "UPDATE admin_company_expenses" in sql:
            update_params.extend(params)
            return _Cursor()
        raise AssertionError(sql)

    monkeypatch.setattr(expenses, "get_conn", fake_get_conn)
    monkeypatch.setattr(expenses, "execute", fake_execute)

    import asyncio

    result = asyncio.run(
        expenses.admin_update_expense(
            12,
            spent_date="2026-07-20",
            amount="2499.50",
            vendor_id="2",
            paid_by_id="3",
            currency="INR",
            category="Hosting",
            notes="Updated notes",
            remove_invoice=False,
            invoice=None,
            current_user=object(),
        )
    )

    assert result == {"id": 12, "ok": True}
    assert connection.committed is True
    assert "gs://bucket/invoice.pdf" in update_params
    assert update_params[-1] == 12
