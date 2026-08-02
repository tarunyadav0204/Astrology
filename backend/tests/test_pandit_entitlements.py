from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from auth import User
from credits import entitlements


class _Cursor:
    def __init__(self, *, all_rows=None):
        self._all = list(all_rows or [])

    def fetchall(self):
        return self._all


class _Connection:
    def commit(self):
        return None


@contextmanager
def _connection():
    yield _Connection()


def _user(role: str = "user") -> User:
    return User(userid=42, name="Test", phone="9999999999", role=role)


def test_admin_receives_pandit_desk_access(monkeypatch):
    monkeypatch.setattr(entitlements, "get_conn", _connection)
    monkeypatch.setattr(
        entitlements,
        "execute",
        lambda *_args, **_kwargs: _Cursor(all_rows=[]),
    )

    summary = entitlements.entitlement_summary(_user("admin"))
    assert summary["is_pandit_licensed"] is True
    assert entitlements.PANDIT_DESK_ENTITLEMENT in summary["entitlements"]


def test_active_pandit_subscription_grants_desk(monkeypatch):
    monkeypatch.setattr(entitlements, "get_conn", _connection)
    monkeypatch.setattr(
        entitlements,
        "execute",
        lambda *_args, **_kwargs: _Cursor(
            all_rows=[(entitlements.PANDIT_DESK_ENTITLEMENT,)]
        ),
    )

    assert entitlements.has_entitlement(_user(), entitlements.PANDIT_DESK_ENTITLEMENT)
    assert entitlements.entitlement_summary(_user())["is_pandit_licensed"] is True
