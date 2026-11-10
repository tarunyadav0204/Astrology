from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from reel_studio import planner, costs


@pytest.mark.parametrize('stage', ['planning','plan_repair','presenter_rewrite','studio_reading'])
def test_gemini_routes_schema_and_meters_thinking(monkeypatch, stage):
    monkeypatch.setenv('GEMINI_API_KEY', 'test')
    finished = []
    @contextmanager
    def attempt(s, model):
        assert s == stage and model == 'gemini-3-flash-preview'
        yield SimpleNamespace(finish=lambda usage, rid: finished.append(usage))
    monkeypatch.setattr(costs, 'attempt', attempt)
    def post(url, **kwargs):
        assert 'gemini-3-flash-preview:generateContent' in url
        assert kwargs['json']['generationConfig']['responseJsonSchema'] == {'type':'object'}
        assert kwargs['headers']['x-goog-api-key'] == 'test'
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {
            'candidates':[{'finishReason':'STOP','content':{'parts':[{'thought':True,'text':'hidden'},{'text':'{"beats":[]}'}]}}],
            'usageMetadata':{'promptTokenCount':100, 'cachedContentTokenCount':20,'candidatesTokenCount':30,'thoughtsTokenCount':10}})
    monkeypatch.setattr(planner.httpx, 'post', post)
    result = planner.create(stage, input='story', text={'format':{'schema':{'type':'object'}}}, max_output_tokens=6500)
    assert result.output_text == '{"beats":[]}'
    assert finished[0]['output_tokens'] == 40
    cost, _ = costs.price(stage, planner.MODEL, finished[0], {'usd_to_inr': 85})
    assert cost == pytest.approx((80*.5 + 20*.05 + 40*3)/1_000_000*85)
