"""
Admin-only Google Cloud Billing importer.

The importer reads the standard or detailed Cloud Billing export table in
BigQuery, normalizes it to daily values, and maintains one expense per billing
account / invoice month / currency. BigQuery authentication uses the runtime
Google identity (or the existing GOOGLE_SERVICE_ACCOUNT_KEY fallback).
"""
from __future__ import annotations

import calendar
import hmac
import json
import logging
import os
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from auth import User, get_current_user
from db import execute, get_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/expense-integrations/gcp", tags=["admin_expense_gcp"])

_TABLE_REF_RE = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+$")
_PROVIDER = "gcp"


class GcpAccountConfig(BaseModel):
    billing_account_id: str = Field(min_length=3, max_length=100)
    display_name: str = Field(default="", max_length=200)
    vendor_id: int = Field(ge=1)
    paid_by_id: int = Field(ge=1)
    category: str = Field(default="Cloud infrastructure", max_length=200)
    is_active: bool = True


class GcpSyncRequest(BaseModel):
    billing_account_id: Optional[str] = Field(default=None, max_length=100)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _billing_table_ref() -> str:
    raw = (os.getenv("GCP_BILLING_EXPORT_TABLE") or "").strip().strip("`")
    if not raw:
        raise HTTPException(
            status_code=503,
            detail=(
                "GCP billing import is not configured. Set GCP_BILLING_EXPORT_TABLE "
                "to project.dataset.gcp_billing_export_v1_XXXXXX."
            ),
        )
    if not _TABLE_REF_RE.fullmatch(raw):
        raise HTTPException(
            status_code=503,
            detail="GCP_BILLING_EXPORT_TABLE must be a fully-qualified project.dataset.table name.",
        )
    return raw


def _bigquery_client():
    try:
        from google.cloud import bigquery
        from google.oauth2 import service_account
        from utils.env_json import parse_json_from_env

        project = (
            os.getenv("GCP_BILLING_QUERY_PROJECT")
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT_ID")
            or ""
        ).strip()
        key = (
            os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
            or os.getenv("GOOGLE_TTS_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")
            or ""
        )
        credentials = None
        if key and str(key).strip():
            raw = str(key).strip()
            info = parse_json_from_env(raw)
            if isinstance(info, dict):
                credentials = service_account.Credentials.from_service_account_info(info)
            elif os.path.isfile(raw):
                credentials = service_account.Credentials.from_service_account_file(raw)
        return bigquery.Client(project=project or None, credentials=credentials)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Could not initialize BigQuery client for expense import")
        raise HTTPException(status_code=502, detail=f"Could not initialize BigQuery: {exc!s}") from exc


def _month_start_n_months_ago(months: int = 3) -> str:
    today = date.today()
    year = today.year
    month = today.month - months
    while month <= 0:
        year -= 1
        month += 12
    return f"{year:04d}{month:02d}"


def _expense_date(invoice_month: str) -> date:
    year = int(invoice_month[:4])
    month = int(invoice_month[4:6])
    return date(year, month, calendar.monthrange(year, month)[1])


def _import_status(invoice_month: str) -> str:
    period_end = _expense_date(invoice_month)
    return "provisional" if (date.today() - period_end).days < 7 else "finalized"


def _discover_accounts() -> list[dict[str, Any]]:
    from google.cloud import bigquery

    table = _billing_table_ref()
    client = _bigquery_client()
    query = f"""
        SELECT
            billing_account_id,
            ARRAY_AGG(currency ORDER BY invoice.month DESC LIMIT 1)[SAFE_OFFSET(0)] AS currency,
            MAX(invoice.month) AS latest_invoice_month
        FROM `{table}`
        WHERE billing_account_id IS NOT NULL
          AND invoice.month >= @month_from
        GROUP BY billing_account_id
        ORDER BY billing_account_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("month_from", "STRING", _month_start_n_months_ago(12)),
        ]
    )
    try:
        return [
            {
                "billing_account_id": str(row.billing_account_id),
                "currency": str(row.currency or ""),
                "latest_invoice_month": str(row.latest_invoice_month or ""),
            }
            for row in client.query(query, job_config=job_config).result()
        ]
    except Exception as exc:
        logger.exception("Could not discover GCP billing accounts")
        raise HTTPException(status_code=502, detail=f"Could not read GCP billing export: {exc!s}") from exc


def _fetch_cost_lines(account_ids: list[str]) -> list[dict[str, Any]]:
    if not account_ids:
        return []
    from google.cloud import bigquery

    table = _billing_table_ref()
    client = _bigquery_client()
    query = f"""
        SELECT
            billing_account_id,
            invoice.month AS invoice_month,
            currency,
            COALESCE(DATE(usage_start_time), PARSE_DATE('%Y%m', invoice.month)) AS usage_date,
            COALESCE(project.id, '(unassigned)') AS project_id,
            COALESCE(service.description, '(unassigned)') AS service_name,
            SUM(
                cost + IFNULL(
                    (SELECT SUM(credit.amount) FROM UNNEST(credits) AS credit),
                    0
                )
            ) AS net_amount
        FROM `{table}`
        WHERE invoice.month >= @month_from
          AND billing_account_id IN UNNEST(@billing_account_ids)
        GROUP BY billing_account_id, invoice_month, currency, usage_date, project_id, service_name
        ORDER BY invoice_month, usage_date, billing_account_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("month_from", "STRING", _month_start_n_months_ago(3)),
            bigquery.ArrayQueryParameter("billing_account_ids", "STRING", account_ids),
        ]
    )
    try:
        return [
            {
                "billing_account_id": str(row.billing_account_id),
                "invoice_month": str(row.invoice_month),
                "currency": str(row.currency or "INR").upper(),
                "usage_date": row.usage_date,
                "project_id": str(row.project_id or "(unassigned)"),
                "service_name": str(row.service_name or "(unassigned)"),
                "amount": Decimal(str(row.net_amount or 0)),
            }
            for row in client.query(query, job_config=job_config).result()
        ]
    except Exception as exc:
        logger.exception("Could not query GCP billing costs")
        raise HTTPException(status_code=502, detail=f"Could not query GCP billing costs: {exc!s}") from exc


def _configured_accounts(*, active_only: bool = False) -> list[dict[str, Any]]:
    active_clause = "AND i.is_active = TRUE" if active_only else ""
    with get_conn() as conn:
        cur = execute(
            conn,
            f"""
            SELECT
                i.source_account_id,
                i.display_name,
                i.vendor_id,
                COALESCE(v.label, ''),
                i.paid_by_id,
                COALESCE(pb.label, ''),
                i.category,
                i.is_active,
                i.last_sync_started_at,
                i.last_sync_completed_at,
                i.last_sync_status,
                COALESCE(i.last_sync_error, '')
            FROM admin_expense_integrations i
            LEFT JOIN admin_expense_vendors v ON v.id = i.vendor_id
            LEFT JOIN admin_expense_paid_by pb ON pb.id = i.paid_by_id
            WHERE i.provider = ?
            {active_clause}
            ORDER BY i.source_account_id
            """,
            (_PROVIDER,),
        )
        rows = cur.fetchall() or []
    return [
        {
            "billing_account_id": r[0],
            "display_name": r[1],
            "vendor_id": r[2],
            "vendor": r[3],
            "paid_by_id": r[4],
            "paid_by": r[5],
            "category": r[6],
            "is_active": bool(r[7]),
            "last_sync_started_at": r[8].isoformat() if r[8] else None,
            "last_sync_completed_at": r[9].isoformat() if r[9] else None,
            "last_sync_status": r[10],
            "last_sync_error": r[11],
        }
        for r in rows
    ]


def _start_sync_run(account_id: Optional[str]) -> int:
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            INSERT INTO admin_expense_sync_runs (provider, source_account_id, status)
            VALUES (?, ?, 'running')
            RETURNING id
            """,
            (_PROVIDER, account_id),
        )
        run_id = int(cur.fetchone()[0])
        conn.commit()
    return run_id


def _finish_sync_run(
    run_id: int,
    *,
    status: str,
    rows_fetched: int = 0,
    created: int = 0,
    updated: int = 0,
    error: Optional[str] = None,
) -> None:
    with get_conn() as conn:
        execute(
            conn,
            """
            UPDATE admin_expense_sync_runs
            SET status = ?, completed_at = NOW(), rows_fetched = ?,
                expenses_created = ?, expenses_updated = ?, error_message = ?
            WHERE id = ?
            """,
            (status, rows_fetched, created, updated, (error or "")[:4000] or None, run_id),
        )
        conn.commit()


def _sync_accounts(configs: list[dict[str, Any]], current_user: Optional[User]) -> dict[str, Any]:
    account_ids = [str(item["billing_account_id"]) for item in configs]
    requested_account = account_ids[0] if len(account_ids) == 1 else None
    run_id = _start_sync_run(requested_account)
    try:
        with get_conn() as conn:
            execute(
                conn,
                """
                UPDATE admin_expense_integrations
                SET last_sync_started_at = NOW(), last_sync_status = 'running',
                    last_sync_error = NULL, updated_at = NOW()
                WHERE provider = ? AND source_account_id = ANY(?)
                """,
                (_PROVIDER, account_ids),
            )
            conn.commit()

        lines = _fetch_cost_lines(account_ids)
        config_by_account = {str(item["billing_account_id"]): item for item in configs}
        daily: dict[tuple[str, str, date, str], dict[str, Any]] = {}
        monthly: defaultdict[tuple[str, str, str], Decimal] = defaultdict(Decimal)

        for line in lines:
            account_id = line["billing_account_id"]
            if account_id not in config_by_account:
                continue
            month_key = (account_id, line["invoice_month"], line["currency"])
            daily_key = (account_id, line["invoice_month"], line["usage_date"], line["currency"])
            monthly[month_key] += line["amount"]
            item = daily.setdefault(daily_key, {"amount": Decimal("0"), "breakdown": []})
            item["amount"] += line["amount"]
            if line["amount"]:
                item["breakdown"].append(
                    {
                        "project_id": line["project_id"],
                        "service": line["service_name"],
                        "amount": str(line["amount"].quantize(Decimal("0.000001"))),
                    }
                )

        created = 0
        updated = 0
        with get_conn() as conn:
            # Serializes the write/reconciliation phase across manual and cron
            # syncs without holding a database connection during the BQ query.
            execute(conn, "SELECT pg_advisory_xact_lock(hashtext(?))", ("admin_expense_gcp_sync",))
            execute(
                conn,
                """
                DELETE FROM admin_expense_import_daily
                WHERE provider = ?
                  AND source_account_id = ANY(?)
                  AND invoice_month >= ?
                """,
                (_PROVIDER, account_ids, _month_start_n_months_ago(3)),
            )
            for (account_id, invoice_month, usage_date, currency), item in daily.items():
                breakdown = sorted(
                    item["breakdown"],
                    key=lambda entry: abs(Decimal(entry["amount"])),
                    reverse=True,
                )
                execute(
                    conn,
                    """
                    INSERT INTO admin_expense_import_daily (
                        provider, source_account_id, invoice_month, usage_date,
                        currency, amount, source_payload, synced_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?::jsonb, NOW())
                    ON CONFLICT (provider, source_account_id, invoice_month, usage_date, currency)
                    DO UPDATE SET amount = EXCLUDED.amount,
                                  source_payload = EXCLUDED.source_payload,
                                  synced_at = NOW()
                    """,
                    (
                        _PROVIDER,
                        account_id,
                        invoice_month,
                        usage_date,
                        currency,
                        str(item["amount"]),
                        json.dumps({"breakdown": breakdown}),
                    ),
                )

            for (account_id, invoice_month, currency), amount in monthly.items():
                cfg = config_by_account[account_id]
                external_id = f"{account_id}:{invoice_month}:{currency}"
                existing = execute(
                    conn,
                    """
                    SELECT id
                    FROM admin_company_expenses
                    WHERE source_provider = ? AND source_external_id = ?
                    """,
                    (_PROVIDER, external_id),
                ).fetchone()
                status = _import_status(invoice_month)
                period = f"{invoice_month[:4]}-{invoice_month[4:6]}"
                note = (
                    f"Automatically imported from Google Cloud Billing for invoice month {period}. "
                    "Daily project/service detail is available in the GCP import view."
                )
                execute(
                    conn,
                    """
                    INSERT INTO admin_company_expenses (
                        spent_date, amount, currency, vendor, vendor_id, paid_by_id,
                        category, notes, created_by_userid, updated_at,
                        source_provider, source_account_id, source_period,
                        source_external_id, import_status, source_last_synced_at,
                        source_amount, manual_adjustment
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), ?, ?, ?, ?, ?, NOW(), ?, 0)
                    ON CONFLICT (source_provider, source_external_id)
                        WHERE source_external_id IS NOT NULL
                    DO UPDATE SET
                        spent_date = EXCLUDED.spent_date,
                        source_amount = EXCLUDED.source_amount,
                        amount = EXCLUDED.source_amount + admin_company_expenses.manual_adjustment,
                        currency = EXCLUDED.currency,
                        vendor = EXCLUDED.vendor,
                        vendor_id = EXCLUDED.vendor_id,
                        paid_by_id = EXCLUDED.paid_by_id,
                        category = EXCLUDED.category,
                        import_status = EXCLUDED.import_status,
                        source_last_synced_at = NOW(),
                        updated_at = NOW()
                    """,
                    (
                        _expense_date(invoice_month),
                        str(amount.quantize(Decimal("0.01"))),
                        currency,
                        cfg["vendor"],
                        cfg["vendor_id"],
                        cfg["paid_by_id"],
                        cfg["category"],
                        note,
                        int(current_user.userid) if current_user is not None else None,
                        _PROVIDER,
                        account_id,
                        period,
                        external_id,
                        status,
                        str(amount.quantize(Decimal("0.01"))),
                    ),
                )
                if existing:
                    updated += 1
                else:
                    created += 1

            execute(
                conn,
                """
                UPDATE admin_expense_integrations
                SET last_sync_completed_at = NOW(), last_sync_status = 'success',
                    last_sync_error = NULL, updated_at = NOW()
                WHERE provider = ? AND source_account_id = ANY(?)
                """,
                (_PROVIDER, account_ids),
            )
            conn.commit()

        _finish_sync_run(
            run_id,
            status="success",
            rows_fetched=len(lines),
            created=created,
            updated=updated,
        )
        return {
            "ok": True,
            "run_id": run_id,
            "accounts_synced": len(account_ids),
            "rows_fetched": len(lines),
            "expenses_created": created,
            "expenses_updated": updated,
        }
    except Exception as exc:
        error = exc.detail if isinstance(exc, HTTPException) else str(exc)
        try:
            with get_conn() as conn:
                execute(
                    conn,
                    """
                    UPDATE admin_expense_integrations
                    SET last_sync_completed_at = NOW(), last_sync_status = 'error',
                        last_sync_error = ?, updated_at = NOW()
                    WHERE provider = ? AND source_account_id = ANY(?)
                    """,
                    (str(error)[:4000], _PROVIDER, account_ids),
                )
                conn.commit()
            _finish_sync_run(run_id, status="error", error=str(error))
        except Exception:
            logger.exception("Could not record failed GCP expense sync")
        raise


@router.get("/status")
async def gcp_status(current_user: User = Depends(_require_admin)):
    del current_user
    table_ref = (os.getenv("GCP_BILLING_EXPORT_TABLE") or "").strip().strip("`")
    configured = _configured_accounts()
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT id, source_account_id, status, started_at, completed_at,
                   rows_fetched, expenses_created, expenses_updated, COALESCE(error_message, '')
            FROM admin_expense_sync_runs
            WHERE provider = ?
            ORDER BY started_at DESC
            LIMIT 10
            """,
            (_PROVIDER,),
        )
        runs = cur.fetchall() or []
    return {
        "table_configured": bool(table_ref and _TABLE_REF_RE.fullmatch(table_ref)),
        "table_ref": table_ref,
        "accounts": configured,
        "recent_runs": [
            {
                "id": r[0],
                "billing_account_id": r[1],
                "status": r[2],
                "started_at": r[3].isoformat() if r[3] else None,
                "completed_at": r[4].isoformat() if r[4] else None,
                "rows_fetched": r[5],
                "expenses_created": r[6],
                "expenses_updated": r[7],
                "error": r[8],
            }
            for r in runs
        ],
    }


@router.get("/accounts")
async def gcp_accounts(current_user: User = Depends(_require_admin)):
    del current_user
    discovered = _discover_accounts()
    configured = {item["billing_account_id"]: item for item in _configured_accounts()}
    return {
        "items": [
            {**item, "configuration": configured.get(item["billing_account_id"])}
            for item in discovered
        ]
    }


@router.put("/accounts/{billing_account_id}")
async def configure_gcp_account(
    billing_account_id: str,
    body: GcpAccountConfig,
    current_user: User = Depends(_require_admin),
):
    del current_user
    path_id = billing_account_id.strip()
    if path_id != body.billing_account_id.strip():
        raise HTTPException(status_code=400, detail="Billing account ID does not match request path")
    with get_conn() as conn:
        vendor = execute(
            conn,
            "SELECT label FROM admin_expense_vendors WHERE id = ? AND is_active = TRUE",
            (body.vendor_id,),
        ).fetchone()
        if not vendor:
            raise HTTPException(status_code=400, detail="Select an active vendor")
        paid_by = execute(
            conn,
            "SELECT label FROM admin_expense_paid_by WHERE id = ? AND is_active = TRUE",
            (body.paid_by_id,),
        ).fetchone()
        if not paid_by:
            raise HTTPException(status_code=400, detail="Select an active paid-by entry")
        execute(
            conn,
            """
            INSERT INTO admin_expense_integrations (
                provider, source_account_id, display_name, vendor_id,
                paid_by_id, category, is_active, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, NOW())
            ON CONFLICT (provider, source_account_id)
            DO UPDATE SET display_name = EXCLUDED.display_name,
                          vendor_id = EXCLUDED.vendor_id,
                          paid_by_id = EXCLUDED.paid_by_id,
                          category = EXCLUDED.category,
                          is_active = EXCLUDED.is_active,
                          updated_at = NOW()
            """,
            (
                _PROVIDER,
                path_id,
                body.display_name.strip() or f"GCP {path_id}",
                body.vendor_id,
                body.paid_by_id,
                body.category.strip() or "Cloud infrastructure",
                body.is_active,
            ),
        )
        conn.commit()
    return {"ok": True, "billing_account_id": path_id}


@router.post("/sync")
async def sync_gcp_expenses(
    body: GcpSyncRequest,
    current_user: User = Depends(_require_admin),
):
    configs = _configured_accounts(active_only=True)
    if body.billing_account_id:
        requested = body.billing_account_id.strip()
        configs = [item for item in configs if item["billing_account_id"] == requested]
    if not configs:
        raise HTTPException(status_code=400, detail="No active GCP billing accounts are configured")
    return await run_in_threadpool(_sync_accounts, configs, current_user)


@router.post("/cron/sync")
async def cron_sync_gcp_expenses(
    x_cron_secret: Optional[str] = Header(None, alias="X-Cron-Secret"),
):
    expected = (os.getenv("NUDGE_CRON_SECRET") or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="NUDGE_CRON_SECRET is not configured")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret.strip(), expected):
        raise HTTPException(status_code=401, detail="Invalid cron secret")
    configs = _configured_accounts(active_only=True)
    if not configs:
        return {"ok": True, "skipped": True, "reason": "No active GCP billing accounts are configured"}
    return await run_in_threadpool(_sync_accounts, configs, None)


@router.get("/accounts/{billing_account_id}/detail/{invoice_month}")
async def gcp_month_detail(
    billing_account_id: str,
    invoice_month: str,
    current_user: User = Depends(_require_admin),
):
    del current_user
    if not re.fullmatch(r"\d{6}", invoice_month):
        raise HTTPException(status_code=400, detail="invoice_month must be YYYYMM")
    with get_conn() as conn:
        cur = execute(
            conn,
            """
            SELECT usage_date, currency, amount::text, source_payload
            FROM admin_expense_import_daily
            WHERE provider = ? AND source_account_id = ? AND invoice_month = ?
            ORDER BY usage_date
            """,
            (_PROVIDER, billing_account_id, invoice_month),
        )
        rows = cur.fetchall() or []
    return {
        "billing_account_id": billing_account_id,
        "invoice_month": invoice_month,
        "days": [
            {
                "usage_date": r[0].isoformat(),
                "currency": r[1],
                "amount": r[2],
                "breakdown": (r[3] or {}).get("breakdown", []),
            }
            for r in rows
        ],
    }
