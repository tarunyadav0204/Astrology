from datetime import date
from contextlib import contextmanager
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import admin_expense_gcp_routes as gcp


def test_billing_table_ref_requires_fully_qualified_name(monkeypatch):
    monkeypatch.delenv("GCP_BILLING_EXPORT_TABLE", raising=False)
    with pytest.raises(HTTPException) as missing:
        gcp._billing_table_ref()
    assert missing.value.status_code == 503

    monkeypatch.setenv("GCP_BILLING_EXPORT_TABLE", "project.dataset.table; DROP TABLE users")
    with pytest.raises(HTTPException) as invalid:
        gcp._billing_table_ref()
    assert invalid.value.status_code == 503

    monkeypatch.setenv(
        "GCP_BILLING_EXPORT_TABLE",
        "tradebest-465307.billing.gcp_billing_export_v1_ABCDEF_123456",
    )
    assert (
        gcp._billing_table_ref()
        == "tradebest-465307.billing.gcp_billing_export_v1_ABCDEF_123456"
    )


def test_expense_date_uses_invoice_month_end():
    assert gcp._expense_date("202402") == date(2024, 2, 29)
    assert gcp._expense_date("202601") == date(2026, 1, 31)


def test_import_status_keeps_current_month_provisional():
    current = date.today().strftime("%Y%m")
    assert gcp._import_status(current) == "provisional"
    assert gcp._import_status("202001") == "finalized"


def test_fetch_cost_lines_queries_net_cost_after_credits(monkeypatch):
    captured = {}

    class _Query:
        def result(self):
            return []

    class _Client:
        def query(self, query, job_config=None):
            captured["query"] = query
            captured["job_config"] = job_config
            return _Query()

    monkeypatch.setenv("GCP_BILLING_EXPORT_TABLE", "project.dataset.billing_table")
    monkeypatch.setattr(gcp, "_bigquery_client", lambda: _Client())

    assert gcp._fetch_cost_lines(["ABC-123"]) == []
    assert "UNNEST(credits)" in captured["query"]
    assert "billing_account_id IN UNNEST(@billing_account_ids)" in captured["query"]
    parameters = {item.name: item for item in captured["job_config"].query_parameters}
    assert parameters["billing_account_ids"].values == ["ABC-123"]


def test_fetch_cost_lines_skips_bigquery_for_empty_account_list(monkeypatch):
    monkeypatch.setattr(
        gcp,
        "_bigquery_client",
        lambda: (_ for _ in ()).throw(AssertionError("BigQuery should not be called")),
    )
    assert gcp._fetch_cost_lines([]) == []


def test_sync_upserts_one_monthly_expense_with_stable_external_id(monkeypatch):
    class _Cursor:
        def __init__(self, one=None):
            self._one = one

        def fetchone(self):
            return self._one

    class _Connection:
        def commit(self):
            return None

    statements = []

    @contextmanager
    def fake_get_conn():
        yield _Connection()

    def fake_execute(_conn, sql, params=()):
        statements.append((sql, params))
        if "SELECT id" in sql and "admin_company_expenses" in sql:
            return _Cursor(None)
        return _Cursor()

    config = {
        "billing_account_id": "ABC-123",
        "vendor": "Google Cloud",
        "vendor_id": 2,
        "paid_by_id": 3,
        "category": "Cloud infrastructure",
    }
    lines = [
        {
            "billing_account_id": "ABC-123",
            "invoice_month": "202607",
            "currency": "INR",
            "usage_date": date(2026, 7, 10),
            "project_id": "astro-prod",
            "service_name": "Compute Engine",
            "amount": Decimal("125.125"),
        },
        {
            "billing_account_id": "ABC-123",
            "invoice_month": "202607",
            "currency": "INR",
            "usage_date": date(2026, 7, 10),
            "project_id": "astro-prod",
            "service_name": "Cloud Storage",
            "amount": Decimal("4.875"),
        },
    ]
    monkeypatch.setattr(gcp, "get_conn", fake_get_conn)
    monkeypatch.setattr(gcp, "execute", fake_execute)
    monkeypatch.setattr(gcp, "_fetch_cost_lines", lambda _ids: lines)
    monkeypatch.setattr(gcp, "_start_sync_run", lambda _account: 99)
    monkeypatch.setattr(gcp, "_finish_sync_run", lambda *_args, **_kwargs: None)

    result = gcp._sync_accounts([config], SimpleNamespace(userid=7))

    assert result["expenses_created"] == 1
    expense_insert = next(
        (sql, params)
        for sql, params in statements
        if "INSERT INTO admin_company_expenses" in sql
    )
    assert "ON CONFLICT (source_provider, source_external_id)" in expense_insert[0]
    assert "ABC-123:202607:INR" in expense_insert[1]
    assert "130.00" in expense_insert[1]
