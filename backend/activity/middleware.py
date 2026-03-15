"""
Middleware to log each API request as an activity event (action=api_request) to Pub/Sub.
Runs after the request; does not block the response.
"""
import os
import time
import logging
import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from activity.publisher import publish_activity

logger = logging.getLogger(__name__)

# Resolve DB path so lookup works from any CWD (e.g. when run in executor thread)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_PATH = os.environ.get("ASTROLOGY_DB_PATH") or os.path.join(_BACKEND_DIR, "astrology.db")
# Cache only positive name lookups so we retry when name was missing or DB failed
_name_cache = {}
_MAX_NAME_CACHE = 10_000

# Skip activity for these paths to reduce noise (health, static, etc.)
SKIP_PATHS = frozenset({"/", "/health", "/favicon.ico", "/docs", "/redoc", "/openapi.json"})


def _resource_from_path(path: str) -> tuple[str | None, str | None]:
    """
    Derive resource_type and resource_id from request path for api_request events.
    - resource_type: first segment after /api/ (e.g. credits, chat, charts, tts), or first segment if no /api/
    - resource_id: last path segment if it looks like a number (e.g. session id, chart id), else None
    """
    if not path or not path.startswith("/"):
        return None, None
    parts = [p for p in path.split("/") if p]
    if not parts:
        return None, None
    # resource_type: for /api/credits/balance use "credits"; for /api/chat/sessions/5 use "chat"
    if parts[0] == "api" and len(parts) >= 2:
        resource_type = parts[1]
    else:
        resource_type = parts[0]
    # resource_id: last segment if numeric
    resource_id = None
    if parts:
        last = parts[-1]
        if last.isdigit():
            resource_id = last
    return resource_type or None, resource_id


def _get_user_from_request(request: Request) -> tuple[str | None, int | None, str | None]:
    """Extract phone (JWT 'sub'), userid (JWT 'userid'), and name (JWT 'name') from Authorization header. Returns (phone, user_id, name)."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None, None, None
    token = auth[7:].strip()
    if not token:
        return None, None, None
    try:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            return None, None, None
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        phone = payload.get("sub")
        user_id = payload.get("userid")
        if user_id is not None and not isinstance(user_id, int):
            try:
                user_id = int(user_id)
            except (TypeError, ValueError):
                user_id = None
        name = payload.get("name")
        if name is not None:
            name = str(name).strip() or None
        return phone, user_id, name
    except Exception:
        return None, None, None


class ActivityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        path = request.url.path
        if path in SKIP_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return response

        user_phone, user_id, user_name = _get_user_from_request(request)
        try:
            # Fire-and-forget: run in executor so we don't block
            import asyncio
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                None,
                _publish_api_request,
                path,
                request.method,
                response.status_code,
                duration_ms,
                user_phone,
                user_id,
                user_name,
                request.client.host if request.client else None,
                request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.debug("Activity: failed to schedule publish: %s", e)

        return response


def _get_user_name_by_id(user_id: int) -> str | None:
    """
    Look up name from DB when JWT has userid but no name (e.g. old token).
    Only caches positive results so we retry when name was missing or DB path was wrong.
    Runs in executor thread; uses resolved _DB_PATH so CWD does not matter.
    """
    if user_id is None:
        return None
    if user_id in _name_cache:
        return _name_cache[user_id]
    try:
        import sqlite3
        conn = sqlite3.connect(_DB_PATH)
        cur = conn.execute("SELECT name FROM users WHERE userid = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row and row[0] is not None and str(row[0]).strip():
            name = str(row[0]).strip()
            if len(_name_cache) < _MAX_NAME_CACHE:
                _name_cache[user_id] = name
            return name
    except Exception as e:
        logger.warning("Activity: name lookup for user_id=%s failed (db=%s): %s", user_id, _DB_PATH, e)
    return None


def _publish_api_request(path, method, status_code, duration_ms, user_phone, user_id, user_name, ip, user_agent):
    # Always prefer DB for name when we have user_id so BigQuery gets current name (fixes old JWTs without name and stale tokens)
    if user_id is not None:
        looked_up = _get_user_name_by_id(user_id)
        if looked_up:
            user_name = looked_up
        # else keep user_name from JWT if DB returned None (e.g. NULL in users.name)
    resource_type, resource_id = _resource_from_path(path)
    publish_activity(
        "api_request",
        path=path,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        user_phone=user_phone,
        user_name=user_name,
        resource_type=resource_type,
        resource_id=resource_id,
        ip=ip,
        user_agent=user_agent,
    )
