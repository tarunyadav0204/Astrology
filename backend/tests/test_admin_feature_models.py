from utils import admin_settings as settings


def test_feature_model_selections_are_independent_and_dynamic(monkeypatch):
    values = {'verified_chat_model': 'gpt-4o', 'verified_router_model': 'gpt-4o-mini', 'verified_planner_model': 'gpt-5.6-luna', 'chat_summary_model': 'gpt-4o-mini'}
    monkeypatch.setattr(settings, 'get_setting', values.get)
    monkeypatch.setenv('CHAT_SUMMARY_MODEL', 'ignored-env-model')
    assert settings.get_verified_chat_model() == 'gpt-4o'
    assert settings.get_verified_router_model() == 'gpt-4o-mini'
    assert settings.get_verified_planner_model() == 'gpt-5.6-luna'
    assert settings.get_chat_summary_model() == 'gpt-4o-mini'
    values['chat_summary_model'] = 'gpt-4o'
    assert settings.get_chat_summary_model() == 'gpt-4o'


def test_timeline_admin_model_takes_precedence_over_environment(monkeypatch):
    monkeypatch.setattr(settings, 'get_setting', lambda key: 'models/admin-timeline' if key == 'event_timeline_narration_model' else None)
    monkeypatch.setenv('EVENT_TIMELINE_V3_NARRATION_MODEL', 'models/env-timeline')
    assert settings.get_event_timeline_narration_model() == 'models/admin-timeline'
