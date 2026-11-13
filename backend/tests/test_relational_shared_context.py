from copy import deepcopy
from ai.parallel_chat.relational_shared import build_relational_shared, relational_call_payload


def test_saved_facts_keep_subjects_categories_and_conflicting_reports_without_truncation():
    rows = [f'Reported event {i}' for i in range(1500)]
    rows += ['Rohini wants separation', 'Rohini does not want separation', 'Reported event 0']
    context = {'native': {'birth_details': {'name': 'Varun'}},
               'user_facts': {'relationships': rows, 'family': ['Children live with Varun']}}
    original = deepcopy(context)
    shared = build_relational_shared(context, {'kind': 'marriage'}, {'profile': {'kind': 'marriage'}}, [])
    assert shared['user_facts']['saved_on_chart'] == 'Varun'
    assert shared['user_facts']['source'] == 'user_reported'
    assert len(shared['user_facts']['by_category']['relationships']) == 1502
    assert shared['user_facts']['by_category']['family'] == ['Children live with Varun']
    assert context == original
    assert 'profile' not in shared['relational_evidence']


def test_cache_hit_and_failure_supply_identical_evidence_once():
    shared = build_relational_shared({'user_facts': {'family': ['A fact']}},
                                     {'kind': 'marriage'}, {'profile': {}, 'cross': [1]},
                                     [{'question': 'earlier', 'response': 'answer'}])
    payload = {'relationship': {'stale': True}, 'relational_evidence': {'stale': True},
               'native': {'planet': 'Sun'}, 'partner': {'planet': 'Moon'}}
    cached = relational_call_payload(payload, shared, cached=True)
    uncached = relational_call_payload(payload, shared, cached=False)
    assert not set(shared).intersection(cached)
    assert {**cached, **shared} == uncached
    assert uncached['user_facts']['by_category']['family'] == ['A fact']


def test_relational_flash_default_is_independent_of_premium(monkeypatch):
    from utils import admin_settings
    monkeypatch.setattr(admin_settings, 'get_setting', lambda key:
                        'models/gemini-3.1-pro-preview' if key == 'gemini_premium_model' else None)
    assert admin_settings.get_gemini_relational_model() == 'models/gemini-3-flash-preview'


def test_pipeline_preserves_facts_on_cache_failure_and_cleans_cache_on_merge_failure(monkeypatch):
    import asyncio
    import json
    from types import SimpleNamespace
    import pytest
    from ai.parallel_chat import relational_orchestrator as module
    from test_relational_parallel_chat import _synastry_context

    context = _synastry_context()
    context['user_facts'] = {'family': ['Distinctive saved relationship fact']}
    captured, deleted = [], []
    resource = SimpleNamespace(usage_metadata=SimpleNamespace(total_token_count=1234))
    monkeypatch.setattr(module, 'get_chat_llm_provider_premium', lambda: 'gemini')
    monkeypatch.setattr(module, 'get_gemini_relational_model', lambda: 'models/gemini-3-flash-preview')
    monkeypatch.setattr(module, 'parallel_branch_stagger_s', lambda: 0)
    monkeypatch.setattr(module, '_enabled_relational_branches', lambda evidence: ['parashari_relational'])

    async def cache(**kwargs):
        captured.append(('shared', kwargs['cache_payload']))
        return resource, object() if hit else None, 100, 25

    async def delete(item, **kwargs):
        deleted.append(item)

    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            captured.append((kwargs['llm_log_tag'], prompt))
            assert kwargs['model_name_override'] == 'models/gemini-3-flash-preview'
            if kwargs['llm_log_tag'] == 'parallel_relational_merge':
                raise RuntimeError('merge failed')
            return {'success': True, 'response': json.dumps({'analysis': 'branch', 'bullets': []}),
                    'chat_llm_model': kwargs['model_name_override'], 'token_usage': {}}

    monkeypatch.setattr(module, '_create_gemini_parallel_cache', cache)
    monkeypatch.setattr(module, '_delete_parallel_cache', delete)
    for hit in (True, False):
        captured.clear()
        deleted.clear()
        with pytest.raises(RuntimeError, match='merge failed'):
            asyncio.run(module.run_parallel_relational_chat_pipeline(Analyzer(),
                user_question='How is our relationship?', astrological_context=context,
                conversation_history=[], language='english', response_style='technical',
                user_context=None, premium_analysis=True, mode='birth', total_request_start=0))
        assert deleted == [resource]
        shared = captured[0][1]
        assert shared['user_facts']['by_category']['family'] == ['Distinctive saved relationship fact']
        for _, prompt in captured[1:]:
            assert prompt.count('Distinctive saved relationship fact') == (0 if hit else 1)


def test_explicit_timing_survives_general_relationship_profile():
    from ai.parallel_chat.relational_payloads import build_relationship_profile, _compact_transit_windows
    context = {'relationship': {'raw_label': 'Husband & Wife'}}
    for question, granularity in [('When will the relationship improve?', 'month'),
                                  ('Could she marry again in 2028/29?', 'year')]:
        profile = build_relationship_profile(context, question)
        assert profile['timing_request']['requested_granularity'] == granularity
        assert profile['question_mode'] == 'predictive_timing'
    windows = {'Saturn': [{'sign': 'Aries', 'house': 7,
                          'start_date': '2028-02-23', 'end_date': '2029-08-07'}]}
    result = _compact_transit_windows({'macro_transits_timeline': windows}, {})
    assert result['available']
    assert result['rows'][0] == dict(transit_planet='Saturn', **windows['Saturn'][0])
