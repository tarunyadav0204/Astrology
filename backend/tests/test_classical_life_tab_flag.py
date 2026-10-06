from __future__ import annotations

import asyncio
import inspect

import pytest
from fastapi import HTTPException
from fastapi.params import Depends

from auth import User, get_current_user
from charts.routes import calculate_classical_natal_promise, calculate_classical_reading
from utils import admin_settings


@pytest.mark.parametrize(
    ("enabled", "allowlist", "user_id", "expected"),
    (
        (None, None, 12, False),
        ("false", "", 12, False),
        ("false", "12", 12, False),
        ("true", "", 12, True),
        ("true", "12, 45\n78", 45, True),
        ("true", "12, 45\n78", 46, False),
        ("true", "bad, -4, 78", 78, True),
        ("true", "12", None, False),
    ),
)
def test_classical_life_tab_global_switch_and_user_allowlist(
    monkeypatch,
    enabled,
    allowlist,
    user_id,
    expected,
):
    values = {
        "classical_life_tab_enabled": enabled,
        "classical_life_tab_user_allowlist": allowlist,
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))

    assert admin_settings.classical_life_tab_enabled_for_user(user_id) is expected


@pytest.mark.parametrize(
    "endpoint",
    (calculate_classical_natal_promise, calculate_classical_reading),
)
def test_classical_chart_endpoints_require_authenticated_user(endpoint):
    parameter = inspect.signature(endpoint).parameters["current_user"]
    assert isinstance(parameter.default, Depends)
    assert parameter.default.dependency is get_current_user


def test_classical_reading_requires_astrologer_entitlement(monkeypatch):
    checked = {}

    def reject_unlicensed(user, entitlement):
        checked["user"] = user.userid
        checked["entitlement"] = entitlement
        raise HTTPException(status_code=403, detail={"code": "ASTROLOGER_LICENSE_REQUIRED"})

    monkeypatch.setattr("charts.routes.require_entitlement", reject_unlicensed)
    user = User(userid=42, name="Tester", phone="000", role="user")

    with pytest.raises(HTTPException) as raised:
        asyncio.run(calculate_classical_reading({"chart_data": {"ascendant": 1, "planets": {}}}, user))

    assert raised.value.status_code == 403
    assert raised.value.detail["code"] == "ASTROLOGER_LICENSE_REQUIRED"
    assert checked == {"user": 42, "entitlement": "astrologer_tools"}
