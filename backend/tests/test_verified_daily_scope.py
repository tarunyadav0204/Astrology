import pytest
from chat.verified_chat_pipeline import _verified_presentation_mode, _premium_writer_system, build_verified_baseline
from chat.instant_chat_pipeline import _slim_event_prediction_payload

@pytest.mark.parametrize('mode,window,expected', [
    ('PREDICT_DAILY', {'kind':'day','start':'2026-10-10','end':'2026-10-10'}, 'PREDICT_DAILY'),
    ('LIFESPAN_EVENT_TIMING', {'kind':'day','start':'2026-10-10','end':'2026-10-10'}, 'PREDICT_DAILY'),
    ('PREDICT_PERIOD_OUTLOOK', {'kind':'window','start':'2026-10-01','end':'2026-10-31'}, 'PREDICT_PERIOD_OUTLOOK'),
    ('LIFESPAN_EVENT_TIMING', {'kind':'window','start':'2026-01-01','end':'2036-01-01'}, 'LIFESPAN_EVENT_TIMING'),
])
def test_compact_payload_preserves_day_period_and_lifespan_scope(mode, window, expected):
    context=_slim_event_prediction_payload(
        birth_summary={}, natal_snapshot={}, target_chart_context={}, current_dashas_levels={},
        current_transits_formatted={},instant_parashari={},normalized_evidence={},period_window=window,
        category='general',question='How will be my day tomorrow',chart_data={'planets':{}},house_lordships={},source_intent_mode=mode,
        daily_prediction_spine={'moon':{'nakshatra':'Test'}})
    assert context['intent_summary']['mode']==expected
    assert _verified_presentation_mode(context)==expected
    if expected=='PREDICT_DAILY':
        baseline=build_verified_baseline(context)
        assert baseline['question_scope']['period_window']==window
        assert baseline['daily_calculations']['moon']['nakshatra']=='Test'
        prompt=_premium_writer_system(expected,'english',response_style='technical')
        assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
        assert 'Your Day: [Weekday, Date]' in prompt
        assert 'APPROVED DAILY READING CONTRACT' in prompt
        assert 'PARASHARI EVIDENCE DENSITY CONTRACT' not in prompt

@pytest.mark.parametrize('style',['simple','technical'])
def test_verified_daily_guard_overrides_stale_presentation_mode(style):
    context={'intent_summary':{'mode':'LIFESPAN_EVENT_TIMING','period_window':{'kind':'day','start':'2026-10-10'}}}
    prompt=_premium_writer_system(_verified_presentation_mode(context),'english',response_style=style)
    assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
    assert 'Do not assume career dominates' in prompt
    assert 'never invent a productive afternoon' in prompt

def test_event_timing_legacy_mode_uses_approved_event_contract():
    context={'intent_summary':{'mode':'LIFESPAN_EVENT_TIMING','period_window':{'kind':'window'}}}
    prompt=_premium_writer_system(_verified_presentation_mode(context),'english',response_style='technical')
    assert 'VERIFIED EVENT TIMING OUTPUT CONTRACT' in prompt
    assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt


def test_daily_inputs_use_structured_date_and_current_location_not_system_today():
    from chat.verified_daily import daily_inputs
    birth={'place':'Delhi','latitude':28.6139,'longitude':77.209,'timezone':'UTC+5:30'}
    context={'intent_summary':{'period_window':{'kind':'day','start':'2026-10-10'}},'query_context':{'current_location':{'name':'London','latitude':51.5,'longitude':0.0,'timezone':'Europe/London'}}}
    params,basis=daily_inputs(birth,context)
    assert params['start_date']=='2026-10-10'
    assert params['location']['longitude']==0
    assert params['location']['timezone']=='Europe/London'
    assert basis=='current_location'


def test_daily_inputs_explicit_saved_location_fallback_and_missing_date():
    from chat.verified_daily import daily_inputs
    birth={'place':'Delhi','latitude':28.6139,'longitude':77.209,'timezone':'UTC+5:30'}
    params,basis=daily_inputs(birth,{'intent_summary':{'period_window':{'kind':'day','start':'2026-10-10'}}})
    assert basis=='saved_birth_location'
    assert params['location']['name']=='Delhi'
    with pytest.raises(ValueError,match='date is unresolved'):daily_inputs(birth,{})
    with pytest.raises(ValueError,match='location'):daily_inputs({}, {'intent_summary':{'period_window':{'start':'2026-10-10'}}})


@pytest.mark.parametrize('style',['simple','technical'])
def test_approved_daily_sections_survive_final_writer_override(style):
    from chat.verified_chat_pipeline import _verified_final_writer_instruction
    final=_verified_final_writer_instruction(style,'PREDICT_DAILY')
    assert 'APPROVED DAILY READING CONTRACT' in final
    assert 'election.navatara' in final and 'election.panchang' in final
    assert 'Timing Through the Day' in final and 'Money, Purchases' in final
    assert 'Relationships and Communication' in final
    assert 'Best-fit fields' not in final
    if style=='simple':assert 'Your Mood and Momentum' in final
    else:assert 'Moon, Nakshatra and Navatara' in final


def test_daily_agent_runs_mandatory_tools_even_when_model_requests_none(monkeypatch):
    import json
    import openai
    from types import SimpleNamespace
    from chat import verified_chat_pipeline as pipeline
    from chat import calculator_menu
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-test-key')
    monkeypatch.setattr(pipeline,'_historical_vimshottari_timeline',lambda _: {})
    calls=[]
    def calculate(capability,birth,params):
        calls.append((capability,params))
        return {'calculator':capability,'facts':{'date':params['start_date']}}
    monkeypatch.setattr(calculator_menu,'run_calculator',calculate)
    sent=[]
    class Events:
        async def __aenter__(self):return self
        async def __aexit__(self,*args):return False
        def __aiter__(self):return self
        async def __anext__(self):raise StopAsyncIteration
        async def get_final_response(self):return SimpleNamespace(output_text='A detailed daily answer.',usage=None)
    class Responses:
        async def create(self,**kwargs):
            sent.append(kwargs)
            if len(sent)==1:
                return SimpleNamespace(id='baseline',usage=None,output=[SimpleNamespace(type='function_call',name='get_instant_baseline',call_id='base-call',arguments='{}')])
            return SimpleNamespace(id='decision',usage=None,output=[])
        def stream(self,**kwargs):sent.append(kwargs);return Events()
    monkeypatch.setattr(openai,'AsyncOpenAI',lambda **kwargs:SimpleNamespace(responses=Responses()))
    import asyncio
    result=asyncio.run(pipeline.run_verified_calculator_agent(question='How will tomorrow be?',language='english',birth_data={'place':'Delhi','latitude':28.6139,'longitude':77.209,'timezone':'UTC+5:30'},instant_context={'intent_summary':{'mode':'PREDICT_DAILY','period_window':{'kind':'day','start':'2026-10-10'}}},history=[],model_name='gpt-5.6-luna',timeout_s=60,response_style='simple'))
    assert {c[0] for c in calls}=={'election.navatara','election.panchang'}
    assert all(c[1]['start_date']=='2026-10-10' for c in calls)
    baseline=json.loads(sent[1]['input'][0]['output'])
    assert set(baseline['daily_required_calculations'])=={'election.navatara','election.panchang'}
    assert baseline['daily_location_basis']=='saved_birth_location'
    audit=result['information_rounds']['events']
    assert len([e for e in audit if e['kind']=='mandatory_daily_calculation'])==2
    assert 'Your Mood and Momentum' in sent[-1]['input'][-1]['content'][0]['text']


def test_navatara_uses_requested_local_snapshot_and_keeps_birth_moon_reference():
    from chat.calculator_menu import run_calculator
    from calculators.chart_calculator import ChartCalculator
    from types import SimpleNamespace
    birth=dict(name='Synthetic',date='1990-01-01',time='12:00:00',latitude=28.6139,longitude=77.209,timezone='UTC+5:30',place='Delhi')
    location=dict(name='London',latitude=51.5,longitude=0,timezone='Europe/London')
    result=run_calculator('election.navatara',birth,dict(start_date='2026-10-10',time='12:00:00',location=location))['facts']
    natal=ChartCalculator({}).calculate_chart(SimpleNamespace(**birth))
    transit=ChartCalculator({}).calculate_chart(SimpleNamespace(**{**birth,**location,'date':'2026-10-10','time':'12:00:00'}))
    assert result['birth_moon_nakshatra_index']==int(natal['planets']['Moon']['longitude']/(360/27))
    assert result['transit_positions']['Moon']['longitude']==transit['planets']['Moon']['longitude']
    assert result['timezone']=='Europe/London'
    assert result['snapshot_date']=='2026-10-10'
    assert result['intraday_transitions_calculated'] is False


def test_verified_router_daily_reaches_technical_contract():
    import asyncio
    import json
    from chat.verified_chat_pipeline import classify_verified_question

    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'USER LOCAL NOW: 2026-10-09' in prompt
            assert 'forecast_scope daily' in prompt
            return {'success': True, 'response': json.dumps({
                'answer_mode': 'timing_window', 'forecast_scope': 'daily',
                'target_date': '2026-10-10', 'category': 'general',
                'route_action': 'answer', 'needs_transits': True,
                'time_relation': 'future'})}

    intent = asyncio.run(classify_verified_question(
        Router(), question='How will be my day tomorrow', history=[], language='english',
        query_context={'client_now_iso': '2026-10-09T21:33:00+05:30', 'timezone_name': 'Asia/Kolkata'}))
    assert intent['mode'] == 'PREDICT_DAILY'
    assert intent['period_window'] == {'kind': 'day', 'start': '2026-10-10', 'end': '2026-10-10'}
    mode = _verified_presentation_mode({'intent_summary': intent})
    prompt = _premium_writer_system(mode, 'english', response_style='technical')
    assert 'Your Day: [Weekday, Date]' in prompt
    assert 'LIFESPAN EVENT TIMELINE (MANDATORY)' not in prompt
    assert 'Panchang' in prompt and 'Navatara' in prompt
