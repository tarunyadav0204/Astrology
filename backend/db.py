import os
from contextlib import contextmanager
from typing import Iterable, Tuple


def _postgres_dsn() -> str:
    """
    DSN examples:
      postgresql://user:pass@127.0.0.1:5432/astrology
      postgresql://user:pass@/astrology?host=/cloudsql/PROJECT:REGION:INSTANCE
    """
    dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN (or DATABASE_URL) is required for Postgres connections")
    return dsn


def _connect_postgres():
    import psycopg2
    return psycopg2.connect(_postgres_dsn())


def _adapt_query_for_postgres(sql: str) -> str:
    # Convert sqlite positional placeholders '?' to psycopg2 '%s'
    # Assumption: queries don't contain literal '?' (true for our codebase).
    return sql.replace("?", "%s")


@contextmanager
def get_conn():
    """Get a Postgres connection (Cloud SQL)."""
    conn = _connect_postgres()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def execute(conn, sql: str, params=None):
    params = params or ()
    sql = _adapt_query_for_postgres(sql)
    cur = conn.cursor()
    cur.execute(sql, params)
    return cur


def executemany(conn, sql: str, params_seq: Iterable[Tuple]):
    sql = _adapt_query_for_postgres(sql)
    cur = conn.cursor()
    cur.executemany(sql, list(params_seq))
    return cur

