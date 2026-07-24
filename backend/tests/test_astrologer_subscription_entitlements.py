from __future__ import annotations

import asyncio
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import db
from auth import User
from credits import entitlements
from credits import razorpay_subscription_routes
from credits.credit_service import CreditService


class _Cursor:
    def __init__(self, *, one=None, all_rows=None, rowcount=1):
        self._one = one
        self._all = list(all_rows or [])
        self.rowcount = rowcount

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class _Connection:
    def commit(self):
        return None

    def rollback(self):
        return None


@contextmanager
def _connection():
    yield _Connection()


def _user(role: str = "user") -> User:
    return User(userid=42, name="Test", phone="9999999999", role=role)


def test_admin_receives_astrologer_access_without_paid_row(monkeypatch):
    monkeypatch.setattr(entitlements, "get_conn", _connection)
    monkeypatch.setattr(
        entitlements,
        "execute",
        lambda *_args, **_kwargs: _Cursor(all_rows=[]),
    )

    summary = entitlements.entitlement_summary(_user("admin"))

    assert summary["is_astrologer_licensed"] is True
    assert summary["admin_access"] is True
    assert entitlements.ASTROLOGER_TOOLS_ENTITLEMENT in summary["entitlements"]


def test_active_subscription_grants_astrologer_entitlement(monkeypatch):
    monkeypatch.setattr(entitlements, "get_conn", _connection)
    monkeypatch.setattr(
        entitlements,
        "execute",
        lambda *_args, **_kwargs: _Cursor(
            all_rows=[(entitlements.ASTROLOGER_TOOLS_ENTITLEMENT,)]
        ),
    )

    assert entitlements.has_entitlement(
        _user(),
        entitlements.ASTROLOGER_TOOLS_ENTITLEMENT,
    )


def test_missing_license_returns_machine_readable_403(monkeypatch):
    monkeypatch.setattr(entitlements, "get_conn", _connection)
    monkeypatch.setattr(
        entitlements,
        "execute",
        lambda *_args, **_kwargs: _Cursor(all_rows=[]),
    )

    with pytest.raises(HTTPException) as exc_info:
        entitlements.require_entitlement(
            _user(),
            entitlements.ASTROLOGER_TOOLS_ENTITLEMENT,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "ASTROLOGER_LICENSE_REQUIRED"
    assert exc_info.value.detail["subscription_family"] == "astrologer"


def test_subscription_replacement_is_scoped_to_its_family(monkeypatch):
    statements = []

    def fake_execute(_conn, sql, params=()):
        normalized = " ".join(str(sql).split())
        statements.append((normalized, tuple(params or ())))
        if normalized.startswith("SELECT platform"):
            return _Cursor(one=("astroroshni", "astrologer"))
        if normalized.startswith("SELECT id"):
            return _Cursor(one=None)
        return _Cursor(rowcount=1)

    monkeypatch.setattr(db, "get_conn", _connection)
    monkeypatch.setattr(db, "execute", fake_execute)

    assert CreditService().set_user_subscription(
        userid=42,
        plan_id=99,
        start_date="2026-07-23",
        end_date="2026-08-23",
        billing_provider="razorpay",
    )

    deactivations = [
        (sql, params)
        for sql, params in statements
        if sql.startswith("UPDATE user_subscriptions SET status = 'inactive'")
    ]
    assert deactivations
    assert all("COALESCE(subscription_family, 'vip') = ?" in sql for sql, _ in deactivations)
    assert all(params[-1] == "astrologer" for _, params in deactivations)


def test_razorpay_cancel_targets_astrologer_family(monkeypatch):
    calls = {}

    class _CreditService:
        def get_user_subscription_details(self, userid, family="vip"):
            calls["details"] = (userid, family)
            return {
                "billing_provider": "razorpay",
                "razorpay_subscription_id": "sub_test",
                "end_date": "2026-08-24",
            }

        def mark_razorpay_subscription_cancel_pending(self, userid, subscription_id):
            calls["marked"] = (userid, subscription_id)
            return True

    class _Response:
        status_code = 200
        text = ""

    monkeypatch.setattr(razorpay_subscription_routes, "credit_service", _CreditService())
    monkeypatch.setattr(
        razorpay_subscription_routes.requests,
        "post",
        lambda *_args, **_kwargs: _Response(),
    )
    monkeypatch.setattr(razorpay_subscription_routes, "_auth", lambda: ("key", "secret"))

    result = asyncio.run(
        razorpay_subscription_routes.razorpay_subscription_cancel(
            family="astrologer",
            current_user=_user(),
        )
    )

    assert calls["details"] == (42, "astrologer")
    assert calls["marked"] == (42, "sub_test")
    assert result["success"] is True
    assert result["end_date"] == "2026-08-24"
