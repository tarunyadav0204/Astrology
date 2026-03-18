"""
Generate Postgres DDL from the existing SQLite astrology.db, in FK-safe order.

Usage (from backend/):

  python generate_postgres_schema_from_sqlite.py --out schema_postgres.sql

Then review the generated SQL, and optionally apply it:

  python generate_postgres_schema_from_sqlite.py --apply
"""

import argparse
import os
import sqlite3
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from db import get_conn, execute


SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "astrology.db")


def _ensure_sqlite_db_exists() -> None:
    if not os.path.exists(SQLITE_DB_PATH):
        raise FileNotFoundError(
            f"SQLite DB not found at {SQLITE_DB_PATH}. "
            f"Make sure you run this script from the backend directory "
            f"and that 'astrology.db' is present there."
        )


def _get_tables(conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    cur = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [(row[0], row[1]) for row in cur.fetchall()]


def _get_foreign_keys(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str]]:
    """
    Return list of (this_table, referenced_table) FKs from SQLite PRAGMA.
    """
    cur = conn.execute(f"PRAGMA foreign_key_list({table})")
    fks = []
    for row in cur.fetchall():
        # row[2] is the referenced table name
        ref_table = row[2]
        fks.append((table, ref_table))
    return fks


def _toposort_tables(tables: List[str], fk_edges: List[Tuple[str, str]]) -> List[str]:
    """
    Topologically sort tables based on FK dependencies.

    Edges are (table, referenced_table) meaning referenced_table must come first.
    """
    graph: Dict[str, Set[str]] = defaultdict(set)
    indegree: Dict[str, int] = {t: 0 for t in tables}

    for table, ref in fk_edges:
        if ref not in tables or table == ref:
            continue
        if table not in graph[ref]:
            graph[ref].add(table)
            indegree[table] += 1

    q = deque([t for t in tables if indegree[t] == 0])
    ordered: List[str] = []

    while q:
        t = q.popleft()
        ordered.append(t)
        for child in graph.get(t, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                q.append(child)

    # If we have remaining tables with indegree > 0, they are in cycles.
    # Append them at the end; we'll still create them, but may need to
    # relax FK creation later if needed.
    remaining = [t for t in tables if t not in ordered]
    return ordered + remaining


def _map_type(sqlite_type: str) -> str:
    t = (sqlite_type or "").upper()
    if "INT" in t:
        return "INTEGER"
    if "CHAR" in t or "CLOB" in t or "TEXT" in t:
        return "TEXT"
    if "BLOB" in t:
        return "BYTEA"
    if "REAL" in t or "FLOA" in t or "DOUB" in t:
        return "DOUBLE PRECISION"
    if "NUM" in t or "DEC" in t:
        return "NUMERIC"
    if "DATE" in t or "TIME" in t:
        return "TIMESTAMP"
    return "TEXT"


def _generate_table_ddl(conn: sqlite3.Connection, table: str) -> str:
    """
    Generate a best-effort Postgres CREATE TABLE statement from SQLite schema.
    """
    # Get column info
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk

    lines: List[str] = []
    pk_cols: List[str] = []

    for cid, name, coltype, notnull, dflt_value, pk in cols:
        col_line = f'    "{name}" {_map_type(coltype)}'
        if notnull:
            col_line += " NOT NULL"
        if dflt_value is not None:
            dv = str(dflt_value).strip()
            dv_lower = dv.lower()
            # Map common SQLite datetime defaults to Postgres
            if dv_lower.startswith("datetime('now'") or dv_lower == "current_timestamp":
                col_line += " DEFAULT CURRENT_TIMESTAMP"
            elif dv_lower in ("date('now')", "current_date"):
                col_line += " DEFAULT CURRENT_DATE"
            elif dv_lower in ("time('now')", "current_time"):
                col_line += " DEFAULT CURRENT_TIME"
            else:
                # If default is double-quoted, treat as string literal
                if dv.startswith('"') and dv.endswith('"'):
                    dv = dv[1:-1]
                # If it looks like a bare identifier (no quotes, no digits-only), also treat as text
                is_number = dv.replace(".", "", 1).isdigit()
                if not is_number and not dv_lower.startswith(("'", "(")):
                    col_line += f" DEFAULT '{dv}'"
                else:
                    col_line += f" DEFAULT {dv}"
        lines.append(col_line)
        if pk:
            pk_cols.append(name)

    # Primary key constraint
    if pk_cols:
        pk_cols_sql = ", ".join(f'"{c}"' for c in pk_cols)
        lines.append(f"    PRIMARY KEY ({pk_cols_sql})")

    # Foreign keys (conservative support: only if referenced column is known to exist)
    fk_cur = conn.execute(f"PRAGMA foreign_key_list({table})")
    for row in fk_cur.fetchall():
        # (id, seq, table, from, to, on_update, on_delete, match, ...)
        ref_table = row[2]
        from_col = row[3]
        to_col = row[4]  # may be None/empty in SQLite
        on_update = row[5]
        on_delete = row[6]

        # Discover referenced table columns and PKs
        ref_info = conn.execute(f"PRAGMA table_info({ref_table})").fetchall()
        ref_cols = {r[1] for r in ref_info}  # name is index 1
        ref_pk_cols = [r[1] for r in ref_info if r[5]]  # pk flag is index 5

        # Choose a referenced column safely
        chosen_to_col: Optional[str] = None
        if to_col and to_col in ref_cols:
            chosen_to_col = to_col
        elif len(ref_pk_cols) == 1:
            chosen_to_col = ref_pk_cols[0]

        # If we cannot confidently choose a target column, skip this FK
        if not chosen_to_col:
            continue

        fk_line = f'    FOREIGN KEY ("{from_col}") REFERENCES "{ref_table}" ("{chosen_to_col}")'
        if on_delete and on_delete.upper() != "NO ACTION":
            fk_line += f" ON DELETE {on_delete.upper()}"
        if on_update and on_update.upper() != "NO ACTION":
            fk_line += f" ON UPDATE {on_update.upper()}"
        lines.append(fk_line)

    columns_sql = ",\n".join(lines)
    ddl = f'DROP TABLE IF EXISTS "{table}" CASCADE;\nCREATE TABLE "{table}" (\n{columns_sql}\n);\n'
    return ddl


def generate_schema_sql() -> str:
    _ensure_sqlite_db_exists()
    src = sqlite3.connect(SQLITE_DB_PATH)
    try:
        tables_with_sql = _get_tables(src)
        table_names = [t for t, _ in tables_with_sql]

        # Build FK edges
        fk_edges: List[Tuple[str, str]] = []
        for t in table_names:
            fk_edges.extend(_get_foreign_keys(src, t))

        ordered_tables = _toposort_tables(table_names, fk_edges)

        ddl_parts: List[str] = ["-- Auto-generated from SQLite astrology.db\n"]
        for t in ordered_tables:
            ddl_parts.append(_generate_table_ddl(src, t))

        # Indexes
        ddl_parts.append("\n-- Indexes\n")
        cur = src.execute(
            "SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL"
        )
        for name, tbl_name, sql in cur.fetchall():
            # Basic adaptation: just replace backticks if any and use as-is.
            ddl_parts.append(f"{sql};\n")

        return "\n".join(ddl_parts)
    finally:
        src.close()


def apply_schema(ddl: str) -> None:
    print("Applying generated schema to Postgres...")
    with get_conn() as conn:
        # Split on semicolons; naive but fine for our simple DDL
        statements = [s.strip() for s in ddl.split(";") if s.strip()]
        for stmt in statements:
            execute(conn, stmt)
        conn.commit()
    print("Schema applied.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate Postgres schema from SQLite astrology.db"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="schema_postgres.sql",
        help="Path to write generated SQL (default: schema_postgres.sql)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the generated schema directly to Postgres (DANGEROUS: drops & recreates tables).",
    )
    args = parser.parse_args()

    ddl = generate_schema_sql()

    out_path = os.path.join(os.path.dirname(__file__), args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ddl)
    print(f"Generated schema written to {out_path}")

    if args.apply:
        print("WARNING: This will DROP and RECREATE tables in your Postgres DB.")
        apply_schema(ddl)


if __name__ == "__main__":
    main()

