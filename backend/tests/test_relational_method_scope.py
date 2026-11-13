import asyncio
import json
from copy import deepcopy
import pytest
from ai.parallel_chat import relational_orchestrator as pipeline
from ai.parallel_chat.relational_scope import scoped_relational_evidence


@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('cache_hit', [False, True])
def test_tier_scope_reaches_every_model_input(monkeypatch, premium, cache_hit):
    from test_relational_parallel_chat import _synastry_context
    context = _synastry_context()
    context['user_facts'] = {'family': ['Saved relationship fact']}
    original = deepcopy(context)
    calls, shared = [], []
    monkeypatch.setattr(pipeline, 'get_parallel_branch_enabled', lambda tier: {
        m: tier or m not in ('nadi', 'sudarshan') for m in ('parashari','jaimini','nadi','nakshatra','kp','ashtakavarga','sudarshan')})
    monkeypatch.setattr(pipeline, '_enabled_relational_branches', lambda evidence: ['parashari_relational','nadi_relational','sudarshan_relational'])
    async def cache(**kw):
        shared.append(kw['cache_payload'])
        return None, object() if cache_hit else None, 0, 0
    async def delete(*a, **kw): pass
    async def branch(analyzer, static, payload, premium, label, **kw):
        calls.append((label, static, payload))
        return {'analysis':'Selected evidence supports the relationship.\n\nNadi injected finding must not reach a restricted merge.', 'bullets':[], 'status':'ok'}, {}
    monkeypatch.setattr(pipeline, '_create_gemini_parallel_cache', cache)
    monkeypatch.setattr(pipeline, '_delete_parallel_cache', delete)
    monkeypatch.setattr(pipeline, '_run_branch_json', branch)
    class StopAtMerge(Exception): pass
    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kw):
            calls.append(('merge',prompt,{}))
            raise StopAtMerge()
    with pytest.raises(StopAtMerge):
        asyncio.run(pipeline.run_parallel_relational_chat_pipeline(Analyzer(), user_question='How is our relationship?',
            astrological_context=context, conversation_history=[], language='english', response_style='technical',
            user_context=None, premium_analysis=premium, mode='birth', total_request_start=0))
    assert context == original
    labels=[c[0] for c in calls]
    assert ('nadi_relational' in labels) == premium
    assert ('sudarshan_relational' in labels) == premium
    assert shared[0]['user_facts']['by_category']['family'] == ['Saved relationship fact']
    if not premium:
        evidence=json.dumps(shared[0]).lower()
        assert 'sudarshana_relational_evidence' not in evidence
        assert 'cross_chart_contacts' not in evidence
        assert 'nadi_relational' not in evidence
        for label,prompt,payload in calls:
            assert 'sudarshana_relational_evidence' not in json.dumps(payload).lower()
            assert 'strongest 3-5' not in prompt
            assert 'Excluded methods:' in prompt
            assert 'Nadi' in prompt.split('Excluded methods:')[1]
            assert 'current tri-perspective activation confirmation' not in prompt
            assert 'Nadi injected finding' not in prompt


def test_nested_packets_and_user_facts():
    data={'sudarshana_dasha':{'secret':1}, 'nadi_relational':{'secret':2},
          'native':{'nadi_context':{'secret':3}},
          'user_facts':{'family':['User previously asked about Nadi']}}
    out=scoped_relational_evidence(data, {'parashari'})
    assert out == {'native':{},'user_facts':data['user_facts']}
