"""
Middleware to log each API request as an activity event (action=api_request) to Pub/Sub.
Runs after the request; does not block the response.
"""
import json
import time
import logging
import os
import jwt
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from activity.publisher import publish_activity
from db import get_conn, execute

logger = logging.getLogger(__name__)

# Cache only positive name lookups so we retry when name was missing or DB failed
_name_cache = {}
_MAX_NAME_CACHE = 10_000

# Skip activity for these paths to reduce noise (health, static, etc.)
SKIP_PATHS = frozenset({"/", "/health", "/favicon.ico", "/docs", "/redoc", "/openapi.json"})

# Alert ops when password reset SMS flow fails (HTTP error or unhandled exception)
_SEND_RESET_CODE_PATH = "/api/send-reset-code"
_SEND_RESET_CODE_ALERT_RECIPIENTS = ("anil.asnani@gmail.com", "tarun.yadav@gmail.com")

# Max body size to buffer for activity logging (replay + metadata). Larger bodies pass through unread.
_MAX_ACTIVITY_BODY = 131_072

_EXACT_REDACT_KEYS = frozenset({
    "password",
    "new_password",
    "current_password",
    "token",
    "refresh_token",
    "access_token",
    "code",
    "otp",
    "otp_code",
    "reset_code",
    "authorization",
    "secret",
    "api_key",
    "apikey",
})
_SUBSTR_REDACT = ("password", "secret", "token", "authorization", "otp", "credit_card", "cvv")


def _redact_key(key: str) -> bool:
    kl = str(key).lower().replace("-", "_")
    if kl in _EXACT_REDACT_KEYS:
        return True
    return any(s in kl for s in _SUBSTR_REDACT)


def _redact_obj(obj, depth: int = 0):
    if depth > 12:
        return "[max_depth]"
    if isinstance(obj, dict):
        out = {}
        for i, (k, v) in enumerate(obj.items()):
            if i >= 200:
                out["[truncated_keys]"] = len(obj) - 200
                break
            ks = str(k)
            out[ks] = "***redacted***" if _redact_key(ks) else _redact_obj(v, depth + 1)
        return out
    if isinstance(obj, list):
        return [_redact_obj(x, depth + 1) for x in obj[:100]]
    if isinstance(obj, str) and len(obj) > 4000:
        return obj[:4000] + "…[truncated]"
    return obj


def _header_subset(request: Request) -> dict:
    out = {}
    for k in ("content-type", "content-length", "accept", "x-forwarded-for", "x-request-id"):
        v = request.headers.get(k)
        if v:
            out[k] = str(v)[:500]
    return out


def _snapshot_from_body(request: Request, body: bytes) -> dict:
    meta = {
        "method": request.method,
        "path": request.url.path,
        "query": dict(request.query_params),
        "headers": _header_subset(request),
    }
    if not body:
        return meta
    ct = (request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in ct:
        meta["body"] = f"<omitted multipart {len(body)} bytes>"
        return meta
    if "application/json" in ct:
        try:
            meta["json"] = _redact_obj(json.loads(body.decode("utf-8")))
        except Exception:
            meta["body_text"] = body[:8000].decode("utf-8", errors="replace")
        return meta
    try:
        text = body.decode("utf-8", errors="replace")
        meta["body_text"] = text[:16000] if len(text) > 16000 else text
    except Exception:
        meta["body"] = f"<binary {len(body)} bytes>"
    return meta


async def _buffer_request_if_small(request: Request) -> tuple[Request, dict]:
    """
    For small bodies, read once and re-wrap Request so downstream sees the same body.
    Returns (possibly new Request, snapshot dict for BigQuery metadata on errors / 4xx).
    """
    method = request.method
    path = request.url.path
    if method not in ("POST", "PUT", "PATCH", "DELETE"):
        return request, {
            "method": method,
            "path": path,
            "query": dict(request.query_params),
            "headers": _header_subset(request),
        }

    cl_header = request.headers.get("content-length")
    try:
        if cl_header is not None and int(cl_header) > _MAX_ACTIVITY_BODY:
            return request, {
                "method": method,
                "path": path,
                "query": dict(request.query_params),
                "headers": _header_subset(request),
                "body_omitted": "content-length exceeds activity capture cap",
                "content_length": int(cl_header),
            }
    except ValueError:
        pass

    try:
        body = await request.body()
    except Exception as exc:
        return request, {
            "method": method,
            "path": path,
            "query": dict(request.query_params),
            "body_capture_error": str(exc)[:500],
        }

    if len(body) > _MAX_ACTIVITY_BODY:
        async def receive_large():
            return {"type": "http.request", "body": body, "more_body": False}

        return Request(request.scope, receive_large), {
            "method": method,
            "path": path,
            "query": dict(request.query_params),
            "headers": _header_subset(request),
            "body_omitted": f"body {len(body)} bytes exceeds activity snapshot cap",
        }

    snap = _snapshot_from_body(request, body)

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(request.scope, receive), snap


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


def _is_send_reset_code_path(path: str) -> bool:
    p = (path or "").rstrip("/") or "/"
    return p == _SEND_RESET_CODE_PATH.rstrip("/") or path == _SEND_RESET_CODE_PATH


def _send_reset_code_error_email(
    status_code: int,
    req_meta: dict,
    error_type: str | None = None,
    error_message: str | None = None,
    stack_trace: str | None = None,
) -> None:
    """
    Notify ops about send-reset-code failures. Uses same SMTP as OTP (utils.smtp_mail).
    req_meta already contains redacted JSON/body snapshot from _buffer_request_if_small.
    Never raises.
    """
    try:
        from utils.smtp_mail import send_plain_text_email

        parts = [
            "The /api/send-reset-code endpoint returned an error or raised an exception.",
            f"HTTP status: {status_code}",
            "",
            "Request snapshot (passwords, tokens, OTP codes redacted):",
            json.dumps(req_meta or {}, indent=2, ensure_ascii=False, default=str),
        ]
        if error_type or error_message:
            parts.extend(["", f"Exception type: {error_type or '—'}", f"Exception message: {error_message or '—'}"])
        if stack_trace:
            st = stack_trace if len(stack_trace) <= 25_000 else stack_trace[:25_000] + "\n…[truncated]"
            parts.extend(["", "Stack trace:", st])
        body = "\n".join(parts)
        subject = f"[AstroRoshni] send-reset-code error (HTTP {status_code})"
        send_plain_text_email(
            list(_SEND_RESET_CODE_ALERT_RECIPIENTS),
            subject,
            body,
        )
    except Exception:
        logger.exception("send-reset-code ops alert email failed")


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
        path = request.url.path
        if path in SKIP_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        request, req_meta = await _buffer_request_if_small(request)
        start = time.perf_counter()
        duration_ms = None

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

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
                    req_meta,
                )
                if _is_send_reset_code_path(path) and response.status_code >= 400:
                    loop.run_in_executor(
                        None,
                        _send_reset_code_error_email,
                        int(response.status_code),
                        req_meta,
                    )
            except Exception as e:
                logger.debug("Activity: failed to schedule publish: %s", e)

            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000

            user_phone, user_id, user_name = _get_user_from_request(request)
            try:
                import asyncio
                loop = asyncio.get_running_loop()
                loop.run_in_executor(
                    None,
                    _publish_api_error,
                    path,
                    request.method,
                    500,
                    duration_ms,
                    user_phone,
                    user_id,
                    user_name,
                    request.client.host if request.client else None,
                    request.headers.get("user-agent"),
                    type(e).__name__,
                    str(e),
                    traceback.format_exc(),
                    req_meta,
                )
                if _is_send_reset_code_path(path):
                    loop.run_in_executor(
                        None,
                        _send_reset_code_error_email,
                        500,
                        req_meta,
                        type(e).__name__,
                        str(e),
                        traceback.format_exc(),
                    )
            except Exception as schedule_err:
                logger.debug("Activity: failed to schedule error publish: %s", schedule_err)

            raise


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
        with get_conn() as conn:
            cur = execute(conn, "SELECT name FROM users WHERE userid = %s", (user_id,))
            row = cur.fetchone()
        if row and row[0] is not None and str(row[0]).strip():
            name = str(row[0]).strip()
            if len(_name_cache) < _MAX_NAME_CACHE:
                _name_cache[user_id] = name
            return name
    except Exception as e:
        logger.warning("Activity: name lookup for user_id=%s failed: %s", user_id, e)
    return None


def _publish_api_request(
    path,
    method,
    status_code,
    duration_ms,
    user_phone,
    user_id,
    user_name,
    ip,
    user_agent,
    request_metadata,
):
    # Always prefer DB for name when we have user_id so BigQuery gets current name (fixes old JWTs without name and stale tokens)
    if user_id is not None:
        looked_up = _get_user_name_by_id(user_id)
        if looked_up:
            user_name = looked_up
        # else keep user_name from JWT if DB returned None (e.g. NULL in users.name)
    resource_type, resource_id = _resource_from_path(path)
    meta = None
    if request_metadata and status_code is not None and status_code >= 400:
        meta = {"request": request_metadata}
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
        metadata=meta,
        ip=ip,
        user_agent=user_agent,
    )


def _publish_api_error(
    path,
    method,
    status_code,
    duration_ms,
    user_phone,
    user_id,
    user_name,
    ip,
    user_agent,
    error_type,
    error_message,
    stack_trace,
    request_metadata,
):
    """Publish an API exception to BigQuery via Pub/Sub."""
    if user_id is not None:
        looked_up = _get_user_name_by_id(user_id)
        if looked_up:
            user_name = looked_up

    resource_type, resource_id = _resource_from_path(path)
    meta = {"request": request_metadata} if request_metadata else None
    publish_activity(
        "api_error",
        path=path,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        user_id=user_id,
        user_phone=user_phone,
        user_name=user_name,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=meta,
        ip=ip,
        user_agent=user_agent,
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
    )
