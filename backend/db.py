import os
import socket
from contextlib import contextmanager
from typing import Dict, Iterable, Tuple


_POOLS: Dict[Tuple[int, bool], object] = {}


def _postgres_dsn() -> str:
    """
    DSN examples:
      postgresql://user:pass@127.0.0.1:5432/astrology
      postgresql://user:pass@/astrology?host=/cloudsql/PROJECT:REGION:INSTANCE

    PGBOUNCER_DSN, when set, is preferred so we can switch process families to a
    pooler without touching application code.
    """
    dsn = (
        os.getenv("PGBOUNCER_DSN")
        or os.getenv("POSTGRES_DSN")
        or os.getenv("DATABASE_URL")
    )
    if not dsn:
        raise RuntimeError("POSTGRES_DSN (or DATABASE_URL) is required for Postgres connections")
    return dsn


def _pool_enabled() -> bool:
    return (os.getenv("DB_USE_POOL") or "true").strip().lower() in {"1", "true", "yes", "on"}


def _pool_min_conn() -> int:
    try:
        return max(1, int(os.getenv("DB_POOL_MIN_CONN", "1") or "1"))
    except Exception:
        return 1


def _default_pool_max_conn() -> int:
    app_name = _detect_application_name()
    if app_name == "astroroshni-api":
        return 4
    if app_name in {
        "astroroshni-chat-worker",
        "astroroshni-nudge-worker",
        "astroroshni-nudge-worker-vm",
        "astroroshni-nudge-dispatch",
    }:
        return 2
    return 4


def _pool_max_conn() -> int:
    try:
        return max(
            _pool_min_conn(),
            int(os.getenv("DB_POOL_MAX_CONN", str(_default_pool_max_conn())) or str(_default_pool_max_conn())),
        )
    except Exception:
        return max(_pool_min_conn(), _default_pool_max_conn())


def _connect_timeout() -> int:
    try:
        return max(1, int(os.getenv("DB_CONNECT_TIMEOUT_S", "5") or "5"))
    except Exception:
        return 5


def _detect_application_name() -> str:
    explicit = (os.getenv("DB_APPLICATION_NAME") or "").strip()
    if explicit:
        return explicit[:63]

    hostname = (socket.gethostname() or "").strip().lower()
    nudge_role = (os.getenv("NUDGE_SERVICE_ROLE") or "").strip().lower()
    if nudge_role == "dispatch":
        return "astroroshni-nudge-dispatch"
    if nudge_role == "worker":
        return "astroroshni-nudge-worker"
    if hostname.startswith("astroroshni-chat-worker"):
        return "astroroshni-chat-worker"
    if hostname.startswith("astroroshni-nudge-worker"):
        return "astroroshni-nudge-worker-vm"
    if hostname.startswith("astroroshni-mig-s2b"):
        return "astroroshni-api"
    return "astroroshni-backend"


def _connection_kwargs(*, dict_rows: bool) -> Dict[str, object]:
    kwargs: Dict[str, object] = {
        "application_name": _detect_application_name(),
        "connect_timeout": _connect_timeout(),
        "keepalives": 1,
        "keepalives_idle": int(os.getenv("DB_TCP_KEEPALIVES_IDLE_S", "30") or "30"),
        "keepalives_interval": int(os.getenv("DB_TCP_KEEPALIVES_INTERVAL_S", "10") or "10"),
        "keepalives_count": int(os.getenv("DB_TCP_KEEPALIVES_COUNT", "3") or "3"),
    }
    if dict_rows:
        from psycopg2.extras import RealDictConnection

        kwargs["connection_factory"] = RealDictConnection
    return kwargs


def _new_connection(*, dict_rows: bool = False):
    import psycopg2

    return psycopg2.connect(_postgres_dsn(), **_connection_kwargs(dict_rows=dict_rows))


def _pool_key(*, dict_rows: bool) -> Tuple[int, bool]:
    return (os.getpid(), bool(dict_rows))


def _close_stale_pools() -> None:
    current_pid = os.getpid()
    stale_keys = [key for key in _POOLS.keys() if key[0] != current_pid]
    for key in stale_keys:
        pool = _POOLS.pop(key, None)
        if pool is None:
            continue
        try:
            pool.closeall()
        except Exception:
            pass


def _get_pool(*, dict_rows: bool = False):
    from psycopg2.pool import ThreadedConnectionPool

    if not _pool_enabled():
        return None

    _close_stale_pools()
    key = _pool_key(dict_rows=dict_rows)
    pool = _POOLS.get(key)
    if pool is not None:
        return pool

    pool = ThreadedConnectionPool(
        _pool_min_conn(),
        _pool_max_conn(),
        _postgres_dsn(),
        **_connection_kwargs(dict_rows=dict_rows),
    )
    _POOLS[key] = pool
    return pool


def _connect_postgres():
    pool = _get_pool(dict_rows=False)
    if pool is None:
        return _new_connection(dict_rows=False)
    return pool.getconn()


def _adapt_query_for_postgres(sql: str) -> str:
    # Convert sqlite positional placeholders '?' to psycopg2 '%s'
    # Assumption: queries don't contain literal '?' (true for our codebase).
    return sql.replace("?", "%s")


def _release_connection(conn, *, dict_rows: bool) -> None:
    if conn is None:
        return

    pool = _get_pool(dict_rows=dict_rows)
    if pool is None:
        try:
            conn.close()
        except Exception:
            pass
        return

    try:
        if conn.closed:
            pool.putconn(conn, close=True)
            return
    except Exception:
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass
        return

    try:
        conn.autocommit = False
    except Exception:
        pass

    try:
        pool.putconn(conn)
    except Exception:
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass


@contextmanager
def get_conn():
    """Get a Postgres connection (Cloud SQL / optional PgBouncer) with pooling."""
    conn = _connect_postgres()
    try:
        yield conn
    finally:
        try:
            if not conn.closed and getattr(conn, "status", None):
                conn.rollback()
        except Exception:
            pass
        _release_connection(conn, dict_rows=False)


@contextmanager
def get_conn_dict():
    """
    Postgres connection whose cursors return dict-like rows (RealDictCursor-compatible).
    """
    pool = _get_pool(dict_rows=True)
    conn = pool.getconn() if pool is not None else _new_connection(dict_rows=True)
    try:
        yield conn
    finally:
        try:
            if not conn.closed and getattr(conn, "status", None):
                conn.rollback()
        except Exception:
            pass
        _release_connection(conn, dict_rows=True)


def get_pool_debug_snapshot() -> Dict[str, object]:
    """Best-effort pool metadata for admin/debugging."""
    snapshot: Dict[str, object] = {
        "enabled": _pool_enabled(),
        "application_name": _detect_application_name(),
        "min_conn": _pool_min_conn(),
        "max_conn": _pool_max_conn(),
        "pid": os.getpid(),
        "pool_keys": [f"{pid}:{'dict' if dict_rows else 'plain'}" for pid, dict_rows in _POOLS.keys()],
    }
    return snapshot


# subscription_plans.is_active may be BOOLEAN or INTEGER (0/1) after SQLite -> Postgres migration.
# Using "= TRUE" or "= 1" alone fails for the other type; this matches both.
SQL_SUBSCRIPTION_PLAN_ACTIVE = (
    "(COALESCE(LOWER(TRIM(is_active::text)), '') IN ('1', 't', 'true'))"
)


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
