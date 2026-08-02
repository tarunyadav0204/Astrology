from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi import HTTPException

from auth import User
from pandit import admin_routes


def _admin() -> User:
    return User(userid=1, name="Admin", phone="9999999999", role="admin")


def _user() -> User:
    return User(userid=2, name="User", phone="8888888888", role="user")


def test_require_admin_rejects_non_admin():
    try:
        admin_routes._require_admin(_user())
        assert False, "expected 403"
    except HTTPException as exc:
        assert exc.status_code == 403


def test_require_admin_allows_admin():
    assert admin_routes._require_admin(_admin()).role == "admin"


def test_admin_row_to_item_maps_verified_jobs():
    row = (
        42,
        "Sharma Ji",
        "Delhi",
        "110001",
        '["hindi"]',
        '["satyanarayan"]',
        "active_tools",
        "tag",
        "9000000000",
        "a@b.com",
        "",
        "",
        True,
        True,
        None,
        None,
        "Account Name",
        "9000000000",
        "a@b.com",
    )
    item = admin_routes._admin_row_to_item(row)
    assert item["userid"] == 42
    assert item["pincode"] == "110001"
    assert item["verified_jobs"] is True
    assert item["puja_types"] == ["satyanarayan"]
    assert item["user_name"] == "Account Name"
