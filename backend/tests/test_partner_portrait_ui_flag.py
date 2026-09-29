from __future__ import annotations

import pytest

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
def test_partner_portrait_ui_global_switch_and_user_allowlist(
    monkeypatch,
    enabled,
    allowlist,
    user_id,
    expected,
):
    values = {
        "partner_portrait_ui_enabled": enabled,
        "partner_portrait_ui_user_allowlist": allowlist,
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))

    assert admin_settings.partner_portrait_ui_enabled_for_user(user_id) is expected
