from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from psycopg2.pool import PoolError
from starlette.requests import Request

import auth


def _request() -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/credits/remedy-funnel/event",
            "headers": [],
        }
    )


def _credentials(payload) -> HTTPAuthorizationCredentials:
    token = auth.jwt.encode(payload, auth.SECRET_KEY, algorithm=auth.ALGORITHM)
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_modern_analytics_token_uses_signed_userid_without_database(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_current_user",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("modern analytics token must not query users")
        ),
    )
    credentials = _credentials(
        {
            "sub": "+910000000000",
            "userid": 73,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )

    assert auth.get_best_effort_analytics_user_id(_request(), credentials) == 73


def test_legacy_analytics_token_skips_when_pool_is_busy(monkeypatch):
    monkeypatch.setattr(
        auth,
        "get_current_user",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            PoolError("connection pool exhausted")
        ),
    )
    credentials = _credentials(
        {
            "sub": "+910000000000",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        }
    )

    assert auth.get_best_effort_analytics_user_id(_request(), credentials) is None


def test_invalid_analytics_token_is_rejected():
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="not-a-valid-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        auth.get_best_effort_analytics_user_id(_request(), credentials)

    assert exc_info.value.status_code == 401
