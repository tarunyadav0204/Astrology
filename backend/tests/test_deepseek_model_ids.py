from utils import admin_settings


def test_deepseek_v4_admin_options_use_api_model_ids():
    values = {value for value, _label in admin_settings.DEEPSEEK_CHAT_MODEL_OPTIONS}

    assert "deepseek-v4-flash" in values
    assert "deepseek-v4-pro" in values
    assert "deepseek-v4" not in values
    assert "deepseek-v4-reasoner" not in values


def test_legacy_deepseek_v4_settings_are_normalized(monkeypatch):
    monkeypatch.setattr(
        admin_settings,
        "get_setting",
        lambda key: {
            "deepseek_instant_chat_model": "deepseek-v4",
            "deepseek_premium_model": "deepseek-v4-reasoner",
        }.get(key),
    )

    assert admin_settings.get_deepseek_instant_model() == "deepseek-v4-flash"
    assert admin_settings.get_deepseek_premium_model() == "deepseek-v4-pro"
