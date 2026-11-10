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


def test_provider_schema_removes_nested_array_bounds_without_mutating_contract():
    from copy import deepcopy
    source = {'type': 'object', 'properties': {
        'beats': {'type':'array', 'minItems':2, 'maxItems':24, 'items':{
            'type':'object', 'properties': {'refs': {'type':'array', 'maxItems':0,
                'items':{'type':'string','enum':['known_id']}}}}},
        'maxItems': {'type':'string'}}, 'required':['beats']}
    original = deepcopy(source)
    actual = planner.provider_schema(source)
    assert source == original
    assert 'maxItems' in actual['properties']
    beats = actual['properties']['beats']
    assert 'minItems' not in beats and 'maxItems' not in beats
    refs = beats['items']['properties']['refs']
    assert 'maxItems' not in refs
    assert refs['items']['enum'] == ['known_id']


def test_provider_rejection_is_recorded_without_exposing_key(monkeypatch):
    import httpx
    monkeypatch.setenv('GEMINI_API_KEY', 'private-test-key')
    event = SimpleNamespace(metadata={})
    @contextmanager
    def attempt(*args):
        yield event
    monkeypatch.setattr(costs, 'attempt', attempt)
    def post(url, **kwargs):
        return httpx.Response(400, request=httpx.Request('POST',url),
            json={'error':{'status':'INVALID_ARGUMENT','message':'Invalid schema private-test-key'}})
    monkeypatch.setattr(planner.httpx, 'post', post)
    with pytest.raises(httpx.HTTPStatusError):
        planner.create('planning',input='story',text={'format':{'schema':{'type':'object'}}},max_output_tokens=100)
    assert event.metadata['http_status'] == 400
    assert event.metadata['provider_status'] == 'INVALID_ARGUMENT'
    assert 'private-test-key' not in event.metadata['provider_message']
