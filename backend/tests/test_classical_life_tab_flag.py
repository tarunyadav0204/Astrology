from __future__ import annotations

import inspect

import pytest
from fastapi.params import Depends

from auth import get_current_user
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
