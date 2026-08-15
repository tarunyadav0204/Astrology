#!/usr/bin/env python3
"""Initialize and synchronize the dedicated notification database.

The source should normally be the application read replica, keeping migration
traffic away from the public API primary.  The command is deliberately
idempotent: rows with primary keys are upserted and tables without primary keys
are copied with conflict-ignore semantics.  It can therefore run once before
cutover and once immediately afterwards to collect any final replicated writes.

Required environment variables:
    NUDGE_MIGRATION_SOURCE_DSN or NUDGE_AUDIENCE_DATABASE_URL
    NUDGE_NOTIFICATION_DATABASE_URL
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env", override=False)

from nudge_engine import db as nudge_db  # noqa: E402


COPY_PREFIXES = ("nudge_",)
COPY_EXACT = {"device_tokens"}
DEPENDENCY_ORDER = {
    "device_tokens": 0,
    "nudge_trigger_definitions": 1,
    "nudge_broadcast_templates": 2,
    "nudge_campaigns": 3,
    "nudge_broadcast_schedule": 4,
    "nudge_campaign_recipients": 5,
    "nudge_deliveries": 6,
    "nudge_conversions": 7,
    "nudge_admin_send_jobs": 8,
    "nudge_cron_runs": 9,
    "nudge_dead_letters": 10,
}


def _dsn(name: str, fallback: str | None = None) -> str:
    value = (os.getenv(name) or (os.getenv(fallback) if fallback else "") or "").strip()
    if not value:
        suffix = f" (or {fallback})" if fallback else ""
        raise RuntimeError(f"{name}{suffix} is required")
    # Some legacy Secret Manager DSNs encode the URL query value as
    # ``sslmode='require'``. SQLAlchemy tolerated that spelling, while libpq
    # correctly treats the quotes as part of the value. Normalize only this
    # known option without logging or otherwise exposing the credential.
    normalized = (
        value.replace("sslmode=%27require%27", "sslmode=require")
        .replace("sslmode='require'", "sslmode=require")
        .replace('sslmode="require"', "sslmode=require")
    )
    # The first version of the generated secrets wrapped every URL component
    # in literal single quotes (including port and sslmode). Those quotes are
    # not URL delimiters and libpq sees them as data. The generated database
    # credentials are URL-safe alphanumerics, so remove that legacy wrapping.
    previous = None
    while normalized != previous:
        previous = normalized
        normalized = normalized.replace("%2527", "%27")
    normalized = (
        normalized.replace("%27", "")
        .replace("\\'", "")
        .replace("'", "")
    )
    if "://" in normalized:
        parsed = urlsplit(normalized)
        query = []
        for key, item in parse_qsl(parsed.query, keep_blank_values=True):
            if key.lower() == "sslmode":
                # Both databases are reached over the private VPC address.
                # Drop malformed legacy sslmode query values entirely; Cloud
                # SQL's private endpoint does not require client-side TLS.
                continue
            query.append((key, item))
        normalized = urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
        )
    else:
        normalized = re.sub(r"(?i)\s*sslmode\s*=\s*\\?['\"]?[^\s]+", "", normalized)
        normalized = re.sub(
            r"(?i)(sslmode\s*=\s*)['\"]+([^'\"\s]+)['\"]+",
            r"\1\2",
            normalized,
        )
    return normalized


def _tables(conn) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
            """
        )
        names = [str(row[0]) for row in cur.fetchall()]
    selected = [
        name for name in names
        if name in COPY_EXACT or any(name.startswith(prefix) for prefix in COPY_PREFIXES)
    ]
    return sorted(selected, key=lambda name: (DEPENDENCY_ORDER.get(name, 100), name))


def _columns(conn, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table,),
        )
        return [str(row[0]) for row in cur.fetchall()]


def _primary_key(conn, table: str) -> List[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a
              ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = %s::regclass AND i.indisprimary
            ORDER BY array_position(i.indkey, a.attnum)
            """,
            (sql.Identifier("public", table).as_string(conn),),
        )
        return [str(row[0]) for row in cur.fetchall()]


def _chunks(rows: Iterable[Sequence[object]], size: int) -> Iterable[List[Sequence[object]]]:
    batch: List[Sequence[object]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


def _copy_table(source, target, table: str, batch_size: int) -> int:
    source_columns = _columns(source, table)
    target_columns = set(_columns(target, table))
    columns = [name for name in source_columns if name in target_columns]
    if not columns:
        return 0
    primary_key = [name for name in _primary_key(target, table) if name in columns]
    non_key = [name for name in columns if name not in primary_key]

    identifiers = sql.SQL(", ").join(sql.Identifier(name) for name in columns)
    query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
        sql.Identifier(table), identifiers
    )
    if primary_key:
        conflict = sql.SQL(", ").join(sql.Identifier(name) for name in primary_key)
        if non_key:
            assignments = sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(name), sql.Identifier(name))
                for name in non_key
            )
            query += sql.SQL(" ON CONFLICT ({}) DO UPDATE SET {}").format(conflict, assignments)
        else:
            query += sql.SQL(" ON CONFLICT ({}) DO NOTHING").format(conflict)
    else:
        query += sql.SQL(" ON CONFLICT DO NOTHING")

    select_sql = sql.SQL("SELECT {} FROM {}").format(identifiers, sql.Identifier(table))
    # Delivery history is append-heavy and can contain close to a million
    # rows. Resume after the highest already-copied id so an interrupted
    # bootstrap progresses instead of repeatedly upserting the same prefix.
    # Mutable operational tables (tokens, campaigns and schedules) continue
    # to use full upserts on every pass.
    if table in {"nudge_deliveries", "nudge_conversions", "nudge_cron_runs"} and primary_key == ["id"]:
        with target.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT COALESCE(MAX(id), 0) FROM {}").format(sql.Identifier(table))
            )
            resume_after = int((cur.fetchone() or [0])[0] or 0)
        if resume_after > 0:
            select_sql += sql.SQL(" WHERE id > %s ORDER BY id")
            select_params = (resume_after,)
        else:
            select_sql += sql.SQL(" ORDER BY id")
            select_params = ()
    else:
        select_params = ()
    copied = 0
    cursor_name = f"copy_{table}"[:63]
    with source.cursor(name=cursor_name) as read_cur:
        read_cur.itersize = batch_size
        read_cur.execute(select_sql, select_params)
        with target.cursor() as write_cur:
            for batch in _chunks(read_cur, batch_size):
                execute_values(write_cur, query.as_string(target), batch, page_size=batch_size)
                target.commit()
                copied += len(batch)
    return copied


def _repair_delivery_gaps(source, target, batch_size: int) -> int:
    """Copy delivery ids absent from an interrupted bootstrap pass."""
    with target.cursor() as cur:
        cur.execute("SELECT id FROM nudge_deliveries")
        target_ids = {int(row[0]) for row in cur.fetchall()}
    with source.cursor() as cur:
        cur.execute("SELECT id FROM nudge_deliveries")
        missing = [int(row[0]) for row in cur.fetchall() if int(row[0]) not in target_ids]
    if not missing:
        return 0

    columns = [
        name for name in _columns(source, "nudge_deliveries")
        if name in set(_columns(target, "nudge_deliveries"))
    ]
    identifiers = sql.SQL(", ").join(sql.Identifier(name) for name in columns)
    query = sql.SQL("INSERT INTO nudge_deliveries ({}) VALUES %s ON CONFLICT (id) DO UPDATE SET {}").format(
        identifiers,
        sql.SQL(", ").join(
            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(name), sql.Identifier(name))
            for name in columns if name != "id"
        ),
    )
    copied = 0
    for id_batch in _chunks(missing, batch_size):
        with source.cursor() as read_cur:
            read_cur.execute(
                sql.SQL("SELECT {} FROM nudge_deliveries WHERE id = ANY(%s) ORDER BY id").format(
                    identifiers
                ),
                (list(id_batch),),
            )
            rows = read_cur.fetchall()
        with target.cursor() as write_cur:
            execute_values(write_cur, query.as_string(target), rows, page_size=batch_size)
        target.commit()
        copied += len(rows)
    return copied


def _reset_sequences(conn, tables: Iterable[str]) -> None:
    with conn.cursor() as cur:
        for table in tables:
            columns = _columns(conn, table)
            for column in ("id",):
                if column not in columns:
                    continue
                cur.execute("SELECT pg_get_serial_sequence(%s, %s)", (f"public.{table}", column))
                row = cur.fetchone()
                sequence = row[0] if row else None
                if not sequence:
                    continue
                cur.execute(
                    sql.SQL("SELECT COALESCE(MAX({}), 0) FROM {}").format(
                        sql.Identifier(column), sql.Identifier(table)
                    )
                )
                maximum = int((cur.fetchone() or [0])[0] or 0)
                cur.execute(
                    "SELECT setval(%s, %s, %s)",
                    (sequence, max(1, maximum), maximum > 0),
                )
    conn.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--repair-delivery-gaps", action="store_true")
    args = parser.parse_args()
    batch_size = max(100, min(int(args.batch_size), 5000))

    source_dsn = _dsn("NUDGE_MIGRATION_SOURCE_DSN", "NUDGE_AUDIENCE_DATABASE_URL")
    target_dsn = _dsn("NUDGE_NOTIFICATION_DATABASE_URL")
    if source_dsn == target_dsn:
        raise RuntimeError("Source and target notification databases must be different")

    source = psycopg2.connect(
        source_dsn,
        application_name="astroroshni-notification-migration-source",
        connect_timeout=10,
    )
    target = psycopg2.connect(
        target_dsn,
        application_name="astroroshni-notification-migration-target",
        connect_timeout=10,
    )
    try:
        source.set_session(readonly=True, autocommit=False)
        # Only one synchronizer should mutate the target at a time.
        with target.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(hashtext('astroroshni-notification-migration'))")
        target.commit()

        nudge_db.init_nudge_tables(target)
        isolated_migration = BACKEND_ROOT / "migrations" / "add_isolated_notification_delivery.sql"
        if isolated_migration.is_file():
            with target.cursor() as cur:
                cur.execute(isolated_migration.read_text(encoding="utf-8"))
            target.commit()
        source_tables = _tables(source)
        target_tables = set(_tables(target))
        tables = [table for table in source_tables if table in target_tables]
        print(f"Synchronizing {len(tables)} notification tables")
        for table in tables:
            count = _copy_table(source, target, table, batch_size)
            print(f"  {table}: {count} source rows synchronized")
        if args.repair_delivery_gaps and "nudge_deliveries" in tables:
            repaired = _repair_delivery_gaps(source, target, batch_size)
            print(f"  nudge_deliveries: {repaired} missing rows repaired")
        _reset_sequences(target, tables)
        print("Notification database synchronization complete")
        return 0
    finally:
        try:
            with target.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(hashtext('astroroshni-notification-migration'))")
            target.commit()
        except Exception:
            target.rollback()
        source.close()
        target.close()


if __name__ == "__main__":
    raise SystemExit(main())
