import asyncio
from unittest.mock import AsyncMock

import pytest
from utils import admin_settings as settings
from ai.parallel_chat import orchestrator as pipeline


def select(premium=False, **kwargs):
    return asyncio.run(pipeline._select_natal_branches(
        object(), intent=kwargs.pop('intent', {}), ctx={}, user_question='Career?',
        language='english', premium_analysis=premium, **kwargs,
    ))


def test_defaults_and_tier_independence(monkeypatch):
    values = {}
    monkeypatch.setattr(settings, 'get_setting', values.get)
    assert all(settings.get_parallel_branch_enabled().values())
    values['parallel_branch_enabled_standard_jaimini'] = 'false'
    values['parallel_branch_enabled_premium_kp'] = 'false'
    assert settings.get_parallel_branch_enabled(False)['jaimini'] is False
    assert settings.get_parallel_branch_enabled(True)['jaimini'] is True
    assert settings.get_parallel_branch_enabled(False)['kp'] is True
    assert settings.get_parallel_branch_enabled(True)['kp'] is False
    values['parallel_branch_enabled_standard_parashari'] = 'false'
    values['parallel_branch_enabled_standard_merge'] = 'false'
    assert settings.get_parallel_branch_enabled()['parashari'] is True
    assert settings.get_parallel_branch_enabled()['merge'] is True


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setattr(settings, 'get_setting', lambda key: 'false' if key == 'parallel_branch_enabled_standard_jaimini' else None)
    monkeypatch.setattr(pipeline, 'is_parallel_branch_planner_enabled', lambda: True)
    monkeypatch.setattr(pipeline, 'get_parallel_branch_planner_model', lambda: 'test-model')


def test_planner_cannot_reenable_disabled_and_keeps_parashari(monkeypatch, configured):
    planner = AsyncMock(return_value={'selected_branches': ['jaimini', 'kp'], 'confidence': .9})
    monkeypatch.setattr(pipeline, 'plan_parallel_branches', planner)
    enabled, reason, _ = select()
    assert enabled == ['parashari', 'kp']
    assert 'jaimini' not in planner.call_args.kwargs['allowed_branches']
    assert 'admin_standard_disabled:jaimini' in reason
    assert select(premium=True)[0] == ['parashari', 'jaimini', 'kp']


@pytest.mark.parametrize('result', [RuntimeError('offline'), {'selected_branches': ['jaimini'], 'confidence': .9}, {'selected_branches': ['kp'], 'confidence': .1}])
def test_planner_fallback_never_restores_disabled(monkeypatch, configured, result):
    planner = AsyncMock(side_effect=result) if isinstance(result, Exception) else AsyncMock(return_value=result)
    monkeypatch.setattr(pipeline, 'plan_parallel_branches', planner)
    enabled, _, _ = select()
    assert 'jaimini' not in enabled
    assert 'parashari' in enabled
    assert 'kp' in enabled


def test_all_optional_disabled_skips_planner(monkeypatch, configured):
    monkeypatch.setattr(settings, 'get_setting', lambda key: 'false' if key.startswith('parallel_branch_enabled_standard_') else None)
    planner = AsyncMock()
    monkeypatch.setattr(pipeline, 'plan_parallel_branches', planner)
    assert select()[0] == ['parashari']
    planner.assert_not_called()


@pytest.mark.parametrize('options', [{'free_question_parashari_only': True}, {'remedy_followup_requested': True}])
def test_special_paths_stay_parashari_only(monkeypatch, configured, options):
    planner = AsyncMock()
    monkeypatch.setattr(pipeline, 'plan_parallel_branches', planner)
    assert select(**options)[0] == ['parashari']
    planner.assert_not_called()


def test_chart_scope_intersects_with_admin_settings(monkeypatch, configured):
    monkeypatch.setattr(pipeline, 'is_parallel_branch_planner_enabled', lambda: False)
    enabled, _, _ = select(intent={'chart_focus': {'kind': 'chart_specific', 'primary': 'D9'}})
    assert enabled == ['parashari', 'nakshatra']
