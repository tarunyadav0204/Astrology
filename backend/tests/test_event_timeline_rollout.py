from utils import admin_settings


def _settings(monkeypatch, mode, user_ids):
    values = {
        "event_timeline_rollout_mode": mode,
        "event_timeline_rollout_user_ids": user_ids,
    }
    monkeypatch.setattr(admin_settings, "get_setting", lambda key: values.get(key))


def test_blank_user_ids_apply_deterministic_to_everyone(monkeypatch):
    _settings(monkeypatch, "deterministic", "")

    assert admin_settings.get_event_timeline_mode_for_user(12) == "deterministic"
    assert admin_settings.get_event_timeline_mode_for_user(999) == "deterministic"


def test_selected_users_get_deterministic_and_others_get_legacy(monkeypatch):
    _settings(monkeypatch, "deterministic", "12, 45\n78")

    assert admin_settings.get_event_timeline_mode_for_user(45) == "deterministic"
    assert admin_settings.get_event_timeline_mode_for_user(46) == "legacy_ai"


def test_selected_users_get_legacy_and_others_get_deterministic(monkeypatch):
    _settings(monkeypatch, "legacy_ai", "12 45")

    assert admin_settings.get_event_timeline_mode_for_user(12) == "legacy_ai"
    assert admin_settings.get_event_timeline_mode_for_user(99) == "deterministic"


def test_invalid_ids_are_ignored(monkeypatch):
    _settings(monkeypatch, "deterministic", "abc, 7, nope")

    assert admin_settings.get_event_timeline_rollout_user_ids() == {7}
    assert admin_settings.get_event_timeline_mode_for_user(None) == "legacy_ai"


def test_missing_mode_preserves_current_deterministic_default(monkeypatch):
    _settings(monkeypatch, None, "")

    assert admin_settings.get_event_timeline_rollout_mode() == "deterministic"
