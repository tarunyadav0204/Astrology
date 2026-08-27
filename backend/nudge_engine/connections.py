"""Role-specific database connections for the isolated notification system.

The notification workload has two non-application database roles:

* ``audience`` is read-only and points at the application read replica.
* ``notification`` is writable and owns campaigns, recipients and deliveries.

Production nudge services must set ``NUDGE_REQUIRE_ISOLATED_DATABASES=true`` so
missing role DSNs fail closed instead of silently falling back to the public
API database.  Local development and tests retain an explicit fallback path.
"""
from __future__ import annotations

import logging
import os
import threading
from contextlib import contextmanager
from typing import Dict, Iterator, Tuple

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

logger = logging.getLogger(__name__)

_POOLS: Dict[Tuple[int, str], ThreadedConnectionPool] = {}
_POOL_LOCK = threading.Lock()


def _truthy(name: str, default: str = "") -> bool:
    return (os.getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


def isolated_databases_required() -> bool:
    return _truthy("NUDGE_REQUIRE_ISOLATED_DATABASES", "false")


def _app_dsn() -> str:
    dsn = os.getenv("PGBOUNCER_DSN") or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    if not dsn:
        raise RuntimeError("POSTGRES_DSN (or DATABASE_URL) is required")
    return dsn


def role_dsn(role: str) -> str:
    role = str(role or "").strip().lower()
    if role == "audience":
        dsn = (
            os.getenv("NUDGE_AUDIENCE_DATABASE_URL")
            or os.getenv("APP_READ_REPLICA_DSN")
            or os.getenv("READ_REPLICA_DSN")
        )
    elif role == "notification":
        dsn = (
            os.getenv("NUDGE_NOTIFICATION_DATABASE_URL")
            or os.getenv("NOTIFICATION_DATABASE_URL")
            or os.getenv("NOTIFICATION_POSTGRES_DSN")
        )
    else:
        raise ValueError(f"Unsupported nudge database role: {role}")

    if dsn:
        return dsn
    if isolated_databases_required():
        raise RuntimeError(
            f"The {role} database DSN is not configured while "
            "NUDGE_REQUIRE_ISOLATED_DATABASES=true"
        )
    logger.warning("nudge %s database is using local-development app DB fallback", role)
    return _app_dsn()


def _pool_size(role: str) -> Tuple[int, int]:
    prefix = "NUDGE_AUDIENCE" if role == "audience" else "NUDGE_NOTIFICATION"
    try:
        minimum = max(1, int(os.getenv(f"{prefix}_DB_POOL_MIN", "1") or "1"))
    except Exception:
        minimum = 1
    try:
        maximum = max(minimum, int(os.getenv(f"{prefix}_DB_POOL_MAX", "8") or "8"))
    except Exception:
        maximum = max(minimum, 8)
    return minimum, maximum


def _pool(role: str) -> ThreadedConnectionPool:
    key = (os.getpid(), role)
    pool = _POOLS.get(key)
    if pool is not None:
        return pool
    with _POOL_LOCK:
        pool = _POOLS.get(key)
        if pool is not None:
            return pool
        minimum, maximum = _pool_size(role)
        pool = ThreadedConnectionPool(
            minimum,
            maximum,
            role_dsn(role),
            application_name=f"astroroshni-nudge-{role}"[:63],
            connect_timeout=max(1, int(os.getenv("DB_CONNECT_TIMEOUT_S", "5") or "5")),
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=3,
        )
        _POOLS[key] = pool
        return pool


@contextmanager
def get_role_conn(role: str, *, readonly: bool = False) -> Iterator[object]:
    pool = _pool(role)
    conn = pool.getconn()
    discard = False
    try:
        conn.autocommit = False
        if readonly:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            discard = True
        raise
    finally:
        try:
            if not conn.closed:
                conn.rollback()
            else:
                discard = True
        except Exception:
            discard = True
        pool.putconn(conn, close=discard)


def get_notification_conn():
    return get_role_conn("notification")


def get_audience_conn():
    return get_role_conn("audience", readonly=True)


def assert_isolated_database_configuration() -> None:
    """Validate production role DSNs without opening network connections."""
    notification = role_dsn("notification")
    audience = role_dsn("audience")
    if isolated_databases_required():
        app = _app_dsn()
        if notification == app:
            raise RuntimeError("Notification database must not equal the application primary DSN")
        if audience == app:
            raise RuntimeError("Audience database must not equal the application primary DSN")
        if notification == audience:
            raise RuntimeError("Notification database must not equal the read-replica DSN")


def assert_explicit_isolated_database_configuration() -> None:
    """Fail closed even in an API process that permits local fallback elsewhere."""
    audience = (
        os.getenv("NUDGE_AUDIENCE_DATABASE_URL")
        or os.getenv("APP_READ_REPLICA_DSN")
        or os.getenv("READ_REPLICA_DSN")
        or ""
    ).strip()
    notification = (
        os.getenv("NUDGE_NOTIFICATION_DATABASE_URL")
        or os.getenv("NOTIFICATION_DATABASE_URL")
        or os.getenv("NOTIFICATION_POSTGRES_DSN")
        or ""
    ).strip()
    if not audience or not notification:
        raise RuntimeError("Explicit notification database and audience read-replica DSNs are required")
    app = _app_dsn()
    if notification == app:
        raise RuntimeError("Notification database must not equal the application primary DSN")
    if audience == app:
        raise RuntimeError("Audience database must not equal the application primary DSN")
    if notification == audience:
        raise RuntimeError("Notification database must not equal the read-replica DSN")
