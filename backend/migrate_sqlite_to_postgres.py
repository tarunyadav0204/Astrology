import argparse
import json
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

# Load backend/.env so POSTGRES_DSN / DATABASE_URL / SQLITE_DB_PATH match production (same as main.py).
_backend_dir = os.path.dirname(os.path.abspath(__file__))
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(_backend_dir, ".env"))
except ImportError:
    pass

from db import get_conn, execute


def _get_sqlite_path() -> str:
    return os.environ.get("SQLITE_DB_PATH") or os.path.join(os.path.dirname(__file__), "astrology.db")


def _ensure_sqlite_db_exists(sqlite_path: str) -> None:
    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(
            f"SQLite DB not found at {sqlite_path}. "
            f"Set SQLITE_DB_PATH or place 'astrology.db' in the backend directory "
            f"(e.g. rename astrology.db.bak back to astrology.db)."
        )


def _list_sqlite_tables(sqlite_path: str) -> list[str]:
    """Return all non-internal table names from the SQLite DB."""
    _ensure_sqlite_db_exists(sqlite_path)
    conn = sqlite3.connect(sqlite_path)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
        names = [r[0] for r in cur.fetchall()]
        # Put users first if present (helps with FK ordering), keep others sorted.
        users_first = []
        others = []
        for n in sorted(names):
            if n == "users":
                users_first.append(n)
            else:
                others.append(n)
        return users_first + others
    finally:
        conn.close()


def _apply_postgres_schema() -> None:
    """Apply schema_postgres.sql to the target Postgres DB (drop & recreate schema)."""
    schema_path = os.path.join(os.path.dirname(__file__), "schema_postgres.sql")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Postgres schema file not found at {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    print(f"Applying Postgres schema from {schema_path}...")
    with get_conn() as dst:
        cur = dst.cursor()
        cur.execute(schema_sql)
        dst.commit()
    print("Postgres schema applied successfully.")


def _postgres_serial_columns(conn) -> List[Tuple[str, str]]:
    """
    Return list of (table_name, column_name) for columns that appear to be
    auto-generated via a sequence (SERIAL or IDENTITY).
    """
    cur = execute(
        conn,
        """
        SELECT c.table_name, c.column_name
        FROM information_schema.columns c
        WHERE c.table_schema = 'public'
          AND (
            c.is_identity = 'YES'
            OR c.column_default LIKE 'nextval(%%'
          )
        ORDER BY c.table_name, c.ordinal_position
        """,
        (),
    )
    return [(r[0], r[1]) for r in (cur.fetchall() or [])]


def _fix_postgres_sequences(conn) -> int:
    """
    After bulk inserting rows with explicit IDs, sequences can lag behind and cause
    duplicate key errors. This bumps every SERIAL/IDENTITY sequence to MAX(col)+1.

    Returns number of sequences updated.
    """
    cols = _postgres_serial_columns(conn)
    if not cols:
        return 0

    fixed = 0
    for table, col in cols:
        cur = execute(conn, "SELECT pg_get_serial_sequence(%s, %s)", (table, col))
        seq_row = cur.fetchone()
        seq = seq_row[0] if seq_row else None
        if not seq:
            continue
        execute(
            conn,
            f'SELECT setval(%s, COALESCE((SELECT MAX(\"{col}\") FROM \"{table}\"), 0) + 1, false)',
            (seq,),
        )
        fixed += 1
    return fixed


def _clean_orphaned_rows(conn, fk_constraints) -> list:
    """Delete orphaned rows for each FK and return a log of what was removed."""
    orphan_log = []
    for constraint_name, table_name, col, ref_table, ref_col in fk_constraints:
        # Find orphaned rows
        cur = execute(conn, f"""
            SELECT t.* FROM "{table_name}" t
            LEFT JOIN "{ref_table}" r ON t."{col}" = r."{ref_col}"
            WHERE r."{ref_col}" IS NULL AND t."{col}" IS NOT NULL
        """)
        col_names = [desc[0] for desc in cur.description] if cur.description else []
        orphans = cur.fetchall()
        if not orphans:
            continue

        # Log orphaned rows
        entry = {
            "constraint": constraint_name,
            "table": table_name,
            "column": col,
            "references": f"{ref_table}.{ref_col}",
            "deleted_count": len(orphans),
            "deleted_at": datetime.utcnow().isoformat(),
            "rows": [dict(zip(col_names, row)) for row in orphans],
        }
        orphan_log.append(entry)

        # Delete orphaned rows
        execute(conn, f"""
            DELETE FROM "{table_name}" WHERE "{col}" NOT IN (
                SELECT "{ref_col}" FROM "{ref_table}"
            ) AND "{col}" IS NOT NULL
        """)
        print(f"  Cleaned {len(orphans)} orphaned rows from {table_name}.{col} -> {ref_table}.{ref_col}")

    conn.commit()
    return orphan_log


def migrate_table(
    table: str,
    target_table: Optional[str] = None,
    where: Optional[str] = None,
    truncate_first: bool = False,
    sqlite_path: Optional[str] = None,
    pg_conn=None,
) -> int:
    """
    Migrate all rows from a SQLite table into the corresponding Postgres table.

    - table:         source table name in SQLite
    - target_table:  destination table name in Postgres (defaults to same as source)
    - where:         optional WHERE clause to filter source rows
    - truncate_first: if True, TRUNCATE the destination table before inserting
    - sqlite_path:   path to SQLite DB (default: SQLITE_DB_PATH env or backend/astrology.db)

    Returns: number of rows inserted.
    """
    path = sqlite_path or _get_sqlite_path()
    _ensure_sqlite_db_exists(path)
    target_table = target_table or table

    src = sqlite3.connect(path)
    src.row_factory = sqlite3.Row

    try:
        sql = f"SELECT * FROM {table}"
        if where:
            sql += f" WHERE {where}"
        cur = src.execute(sql)
        rows = cur.fetchall()
        if not rows:
            print(f"[{table}] No rows to migrate.")
            return 0

        col_names = [d[0] for d in cur.description]
        columns_sql = ", ".join(col_names)
        placeholders = ", ".join(["%s"] * len(col_names))

        print(f"[{table}] Migrating {len(rows)} rows into Postgres table '{target_table}'...")

        # Preload known user IDs for FK-cleaning in promo_codes
        valid_user_ids = set()
        if table == "promo_codes":
            uc = src.execute("SELECT userid FROM users")
            valid_user_ids = {r[0] for r in uc.fetchall()}

        inserted = 0
        own_conn = pg_conn is None
        dst = get_conn().__enter__() if own_conn else pg_conn
        try:
            if truncate_first:
                # Safe only when you are sure this env is dedicated for migration/testing
                print(f"[{table}] Truncating destination table '{target_table}' before insert...")
                execute(dst, f"TRUNCATE {target_table} RESTART IDENTITY CASCADE")

            for row in rows:
                # Special-case cleanup for promo_codes.created_by: if it points to a non-existent user,
                # set it to NULL to avoid FK violations while preserving the promo code itself.
                if table == "promo_codes" and "created_by" in col_names:
                    created_by = row["created_by"]
                    if created_by is not None and created_by not in valid_user_ids:
                        row = dict(row)
                        row["created_by"] = None

                values = [row[c] for c in col_names]
                execute(
                    dst,
                    f"INSERT INTO {target_table} ({columns_sql}) VALUES ({placeholders})",
                    values,
                )
                inserted += 1

            dst.commit()
        finally:
            if own_conn:
                try:
                    dst.close()
                except Exception:
                    pass

        print(f"[{table}] Done. Inserted {inserted} rows.")
        return inserted
    finally:
        src.close()


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Migrate data from SQLite astrology.db into Postgres using backend/db.py."
    )
    parser.add_argument(
        "tables",
        nargs="*",
        help=(
            "Tables to migrate (source table names in SQLite).\n"
            "If empty and --preset is not used, a default set (users, birth_charts) will be migrated."
        ),
    )
    parser.add_argument(
        "--sqlite",
        default=None,
        metavar="PATH",
        help="Path to SQLite DB (default: SQLITE_DB_PATH env or backend/astrology.db).",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate destination tables before inserting (dangerous on shared DBs).",
    )

    parser.add_argument(
        "--preset",
        choices=["core", "all"],
        help=(
            "Named preset for FK-safe migration order.\n"
            "core = users, chat history, credits (user_credits, credit_transactions, promo tables).\n"
            "all  = ALL user tables discovered in SQLite (users first)."
        ),
    )
    parser.add_argument(
        "--recreate-schema",
        action="store_true",
        help="Drop & recreate Postgres schema from schema_postgres.sql before migrating.",
    )
    parser.add_argument(
        "--no-fix-sequences",
        action="store_true",
        help="Skip bumping SERIAL/IDENTITY sequences after migration.",
    )

    args = parser.parse_args(argv)

    sqlite_path = args.sqlite or _get_sqlite_path()
    print(f"Using SQLite DB at: {sqlite_path}")

    if args.recreate_schema:
        _apply_postgres_schema()

    if args.preset == "core":
        # FK-safe order for core app data:
        # 1) users
        # 2) chat_sessions -> chat_messages
        # 3) credits: promo_codes, credit_settings, user_credits, credit_transactions, promo_code_usage
        tables = [
            "users",
            "chat_sessions",
            "chat_messages",
            "promo_codes",
            "credit_settings",
            "user_credits",
            "credit_transactions",
            "promo_code_usage",
        ]
    elif args.preset == "all":
        tables = _list_sqlite_tables(sqlite_path)
    elif args.tables:
        tables = args.tables
    else:
        # Safe starter set for ad-hoc use
        tables = ["users", "birth_charts"]
    print(f"Destination Postgres DSN is read from POSTGRES_DSN / DATABASE_URL.")
    print(f"Tables to migrate (in order): {tables}")
    if args.truncate:
        print("WARNING: --truncate is enabled; destination tables will be cleared before insert.")

    total_inserted = 0

    with get_conn() as conn:
        # Collect all FK constraints so we can drop them before migration and restore after
        cur = execute(conn, """
            SELECT tc.constraint_name, tc.table_name,
                   kcu.column_name, ccu.table_name AS foreign_table,
                   ccu.column_name AS foreign_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                 ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                 ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        """)
        fk_constraints = cur.fetchall()

        # Drop all FKs
        for constraint_name, table_name, col, ref_table, ref_col in fk_constraints:
            execute(conn, f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{constraint_name}"')
        if fk_constraints:
            print(f"Dropped {len(fk_constraints)} FK constraints.")
        conn.commit()

        for t in tables:
            inserted = migrate_table(t, truncate_first=args.truncate, sqlite_path=sqlite_path, pg_conn=conn)
            total_inserted += inserted

        # Clean orphaned rows before restoring FKs
        orphan_log = _clean_orphaned_rows(conn, fk_constraints)

        # Restore all FKs — should succeed now that orphans are cleaned
        for constraint_name, table_name, col, ref_table, ref_col in fk_constraints:
            execute(conn, f"""
                ALTER TABLE "{table_name}"
                ADD CONSTRAINT "{constraint_name}"
                FOREIGN KEY ("{col}") REFERENCES "{ref_table}" ("{ref_col}")
            """)
        conn.commit()
        print(f"Restored all {len(fk_constraints)} FK constraints.")

        if orphan_log:
            log_path = os.path.join(os.path.dirname(__file__), "logs", "orphaned_rows.json")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as f:
                json.dump(orphan_log, f, indent=2, default=str)
            print(f"Orphaned row details logged to {log_path}")

        if not args.no_fix_sequences:
            fixed = _fix_postgres_sequences(conn)
            conn.commit()
            print(f"Updated {fixed} Postgres sequences to MAX(id)+1.")

    print(f"All done. Total rows inserted across all tables: {total_inserted}")


if __name__ == "__main__":
    main()

