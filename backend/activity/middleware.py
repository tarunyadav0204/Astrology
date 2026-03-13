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


def _get_user_phone_from_request(request: Request) -> str | None:
    """Extract phone (JWT 'sub') from Authorization header without DB. Returns None if missing/invalid."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            return None
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("sub")
    except Exception:
        return None


class ActivityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        path = request.url.path
        if path in SKIP_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return response

        user_phone = _get_user_phone_from_request(request)
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
                request.client.host if request.client else None,
                request.headers.get("user-agent"),
            )
        except Exception as e:
            logger.debug("Activity: failed to schedule publish: %s", e)

        return response


def _publish_api_request(path, method, status_code, duration_ms, user_phone, ip, user_agent):
    publish_activity(
        "api_request",
        path=path,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        user_phone=user_phone,
        ip=ip,
        user_agent=user_agent,
    )
