"""
Fail-safe Sentry for the FastAPI backend.

If SENTRY_DSN is unset or init fails, all helpers no-op and the API keeps running.
Host CPU/RAM/disk are attached to events at report time (not continuous infra monitoring).
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

_initialized = False

_SENSITIVE_HEADER_KEYS = frozenset(
    k.lower()
    for k in (
        "authorization",
        "cookie",
        "set-cookie",
        "x-api-key",
        "x-auth-token",
    )
)


def is_sentry_initialized() -> bool:
    return _initialized


def _collect_host_snapshot() -> Dict[str, Any]:
    """Process + system snapshot at error time (not a live metrics dashboard)."""
    out: Dict[str, Any] = {}
    try:
        import psutil

        proc = psutil.Process()
        mem = proc.memory_info()
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        out = {
            "process_memory_mb": round(mem.rss / 1024 / 1024, 2),
            "process_memory_percent": round(proc.memory_percent(), 2),
            "process_threads": proc.num_threads(),
            "system_memory_percent": round(vm.percent, 2),
            "system_memory_available_gb": round(vm.available / 1024**3, 2),
            "disk_root_percent": round(disk.percent, 2),
            "disk_root_free_gb": round(disk.free / 1024**3, 2),
        }
        try:
            out["process_cpu_percent"] = round(proc.cpu_percent(interval=0.0), 2)
        except Exception:
            pass
    except Exception:
        out["host_snapshot_error"] = "unavailable"
    return out


def _scrub_request(event: Dict[str, Any]) -> None:
    req = event.get("request")
    if not isinstance(req, dict):
        return
    headers = req.get("headers")
    if isinstance(headers, dict):
        for key in list(headers.keys()):
            if str(key).lower() in _SENSITIVE_HEADER_KEYS:
                headers[key] = "[Filtered]"
    if "data" in req:
        req["data"] = "[Filtered]"


def _before_send(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        _scrub_request(event)
        event.setdefault("contexts", {})
        event["contexts"]["host"] = _collect_host_snapshot()
    except Exception:
        pass
    return event


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set. Safe to call multiple times."""
    global _initialized
    if _initialized:
        return True

    dsn = (os.getenv("SENTRY_DSN") or "").strip()
    if not dsn:
        return False

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        print("WARNING: sentry-sdk not installed; skipping Sentry")
        return False

    environment = (os.getenv("SENTRY_ENVIRONMENT") or os.getenv("ENVIRONMENT") or "production").strip()
    try:
        traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))
    except ValueError:
        traces_sample_rate = 0.1
    traces_sample_rate = max(0.0, min(1.0, traces_sample_rate))

    try:
        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            send_default_pii=False,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                StarletteIntegration(transaction_style="endpoint"),
            ],
            before_send=_before_send,
        )
        sentry_sdk.set_tag("service", "astroroshni-api")
        _initialized = True
        print(f"Sentry initialized (environment={environment})")
        return True
    except Exception as e:
        print(f"WARNING: Sentry init failed; API continues without crash reporting: {e}")
        return False


def capture_exception(exc: BaseException, **extra: Any) -> None:
    if not _initialized:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            scope.set_context("host", _collect_host_snapshot())
            sentry_sdk.capture_exception(exc)
    except Exception:
        pass


def capture_message(message: str, level: str = "error", **extra: Any) -> None:
    if not _initialized:
        return
    try:
        import sentry_sdk

        with sentry_sdk.push_scope() as scope:
            for key, value in extra.items():
                scope.set_extra(key, value)
            scope.set_context("host", _collect_host_snapshot())
            sentry_sdk.capture_message(message, level=level)
    except Exception:
        pass
