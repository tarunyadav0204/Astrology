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

# Skip activity for these paths to reduce noise (health, static, etc.)
SKIP_PATHS = frozenset({"/", "/health", "/favicon.ico", "/docs", "/redoc", "/openapi.json"})


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


def _publish_api_request(path, method, status_code, duration_ms, user_phone, user_id, user_name, ip, user_agent):
    publish_activity(
        "api_request",
        path=path,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        user_phone=user_phone,
        user_name=user_name,
        ip=ip,
        user_agent=user_agent,
    )
