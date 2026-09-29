"""Privacy cleanup for generated Partner Portrait data."""

from __future__ import annotations

import json
import logging
from typing import Optional

from .storage import PartnerPortraitStorage


logger = logging.getLogger(__name__)


def delete_partner_portraits(conn, *, user_id: Optional[int] = None, chart_id: Optional[int] = None) -> None:
    """Delete DB rows and private images, while tolerating pre-feature databases."""
    if user_id is None and chart_id is None:
        raise ValueError("user_id or chart_id is required")

    clauses = []
    params: list[int] = []
    if user_id is not None:
        clauses.append("user_id = %s")
        params.append(int(user_id))
    if chart_id is not None:
        clauses.append("birth_chart_id = %s")
        params.append(int(chart_id))
    where = " AND ".join(clauses)

    cursor = conn.cursor()
    cursor.execute("SAVEPOINT sp_delete_partner_portraits")
    try:
        cursor.execute(f"SELECT assets_json FROM partner_portrait_jobs WHERE {where}", tuple(params))
        asset_rows = cursor.fetchall() or []
        cursor.execute(f"DELETE FROM partner_portrait_jobs WHERE {where}", tuple(params))
        cursor.execute("RELEASE SAVEPOINT sp_delete_partner_portraits")
    except Exception as exc:
        logger.info("Partner Portrait cleanup skipped (table may not exist): %s", exc)
        cursor.execute("ROLLBACK TO SAVEPOINT sp_delete_partner_portraits")
        cursor.execute("RELEASE SAVEPOINT sp_delete_partner_portraits")
        return

    storage = PartnerPortraitStorage()
    for row in asset_rows:
        try:
            assets = json.loads(row[0] or "[]")
        except (TypeError, ValueError):
            assets = []
        for asset in assets:
            try:
                storage.delete(str((asset or {}).get("stored_uri") or ""))
            except Exception:
                logger.exception("Could not delete a Partner Portrait asset")
