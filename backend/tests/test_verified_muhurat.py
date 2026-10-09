import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from zoneinfo import ZoneInfo
import pytest
import swisseph as swe
from chat.verified_muhurat import MuhuratRequest, prepare_muhurat_intent, calculate_muhurat_tool, muhurat_contract
from calculators.verified_muhurat_calculator import VerifiedMuhuratCalculator, julian, sidereal_ascendant

PLACE={'name':'Gurugram','latitude':28.4595,'longitude':77.0266,'timezone':'Asia/Kolkata'}
REQUEST={'event_type':'vehicle','start_date':'2026-09-07','end_date':'2026-09-07','location':PLACE,'personalized':False,'allowed_start':'08:00','allowed_end':'18:00','minimum_duration_minutes':15,'weekdays':[],'excluded_dates':[]}

def test_same_day_and_bounds():
    assert MuhuratRequest.model_validate(REQUEST).end_date.isoformat()=='2026-09-07'
    for patch in ({'end_date':'2026-09-06'},{'end_date':'2026-11-07'},{'weekdays':[7]},{'allowed_end':'07:00'},{'minimum_duration_minutes':2}):
        with pytest.raises(ValueError): MuhuratRequest.model_validate({**REQUEST,**patch})

def test_missing_city_requires_setup_card():
    result=prepare_muhurat_intent({'reading_type':'muhurat','muhurat_request':{'event_type':'vehicle','start_date':'2026-09-07','end_date':'2026-09-07'}},'Choose a purchase time',{})
    assert result['status']=='CLARIFY'
    assert result['muhurat_setup']['choice_kind']=='muhurat_setup'

def test_confirmed_event_city_timezone_resolved_not_birthplace():
    result=prepare_muhurat_intent({'reading_type':'muhurat'},'Choose a purchase time',{'muhurat_request':{**REQUEST,'location':{**PLACE,'timezone':'UTC'}}})
    assert result['status']=='READY'
    assert result['query_context']['muhurat_request']['location']['timezone']=='Asia/Kolkata'

def test_followup_refinement_explicit_and_exit_clears_request():
    qc={'_muhurat_previous':REQUEST,'muhurat_choice':'next_30_days'}
    result=prepare_muhurat_intent({'reading_type':'muhurat','muhurat_transition':'continue'},'Search the next month',qc)
    request=result['query_context']['muhurat_request']
    assert request['start_date']=='2026-09-08' and request['end_date']=='2026-10-07'
    exited=prepare_muhurat_intent({'reading_type':'default'},'Explain my D9',{'muhurat_request':REQUEST})
    assert 'muhurat_request' not in exited['query_context']

def test_supplement_cannot_expand_dates_or_use_natal_without_consent():
    for cap,params in [('election.panchang',{'start_date':'2026-09-08','time':'10:00'}),('election.navatara',{'start_date':'2026-09-07','time':'10:00'}),('election.panchang',{'start_date':'2026-09-07'})]:
        with pytest.raises(ValueError): calculate_muhurat_tool(cap,REQUEST,{},params)

def test_sidereal_ascendant_and_timezone_equivalence():
    local=datetime(2026,9,7,10,tzinfo=ZoneInfo('Asia/Kolkata'))
    utc=local.astimezone(ZoneInfo('UTC'))
    assert julian(local)==julian(utc)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd=julian(local)
    tropical=swe.houses_ex(jd,PLACE['latitude'],PLACE['longitude'],b'W')[1][0]
    sidereal=sidereal_ascendant(jd,PLACE['latitude'],PLACE['longitude'])
    assert 20<(tropical-sidereal)%360<30

def test_real_election_windows_fit_selected_hours_and_exclusions():
    engine=VerifiedMuhuratCalculator()
    result=engine.search(REQUEST)
    assert result['status']=='completed' and result['candidates']
    solar=engine.panchang_calc.get_local_sunrise_sunset(REQUEST['start_date'],PLACE['latitude'],PLACE['longitude'],PLACE['timezone'])
    sunrise=datetime.fromisoformat(solar['sunrise']).replace(tzinfo=ZoneInfo(PLACE['timezone']))
    sunset=datetime.fromisoformat(solar['sunset']).replace(tzinfo=ZoneInfo(PLACE['timezone']))
    forbidden=[(sunrise+(sunset-sunrise)*i/8,sunrise+(sunset-sunrise)*(i+1)/8) for i in (1,3,5)]
    for row in result['candidates']:
        start,end=map(datetime.fromisoformat,(row['start_time'],row['end_time']))
        assert start.date().isoformat()==REQUEST['start_date']
        assert 8<=start.hour and end.hour<=18 and row['duration_minutes']>=15
        assert all(not(start<e and end>s) for s,e in forbidden)
        assert start.utcoffset().total_seconds()==19800
        assert row['panchang']['tithi_number'] not in {4,9,14,19,24,29,30}
    excluded=engine.search({**REQUEST,'excluded_dates':['2026-09-07']})
    assert not excluded['candidates'] and excluded['rejection_counts']['user_availability']==1

def test_unsupported_never_substitutes_activity():
    for event in ('marriage','property','surgery','childbirth','travel'):
        result=VerifiedMuhuratCalculator().search({**REQUEST,'event_type':event})
        assert result['status']=='unsupported' and result['event_type']==event and not result['candidates']

def test_day_calculation_failure_is_partial_not_no_good_times(monkeypatch):
    engine=VerifiedMuhuratCalculator()
    def fail(*args,**kwargs): raise ValueError('Solar data unavailable')
    monkeypatch.setattr(engine.panchang_calc,'get_local_sunrise_sunset',fail)
    result=engine.search(REQUEST)
    assert result['status']=='partial' and result['errors']

def test_contract_requires_constraints_and_honest_coverage():
    contract=muhurat_contract('technical')
    assert 'NEVER silently expand' in contract and 'not percentages' in contract
    assert 'Panchang and Activity Fit' in contract and 'Personal Suitability' in contract

def test_confirmed_fields_override_router_guess():
    result=prepare_muhurat_intent({'reading_type':'muhurat','muhurat_request':{'start_date':'2026-12-01','end_date':'2026-12-02','event_type':'gold'}},'Check my selected details',{'muhurat_request':REQUEST})
    assert result['query_context']['muhurat_request']['start_date']==REQUEST['start_date']
    assert result['query_context']['muhurat_request']['event_type']=='vehicle'


def test_personalized_natal_seconds_and_missing_time():
    engine=VerifiedMuhuratCalculator()
    birth={'date':'1990-01-01','time':'10:20:30','latitude':28.4595,'longitude':77.0266,'timezone':'Asia/Kolkata'}
    natal=engine._build_natal_context(birth)
    assert natal is not None
    assert abs(natal['birth_jd']-julian(datetime(1990,1,1,10,20,30,tzinfo=ZoneInfo('Asia/Kolkata'))))<1e-8
    assert engine._build_natal_context({**birth,'time':None}) is None


def test_semantic_router_can_leave_prashna_for_election():
    import asyncio,json
    from chat.verified_chat_pipeline import classify_verified_question
    from chat.prashna_workflow import apply_prashna_transition
    class Router:
        async def generate_text_from_prompt(self,prompt,**kwargs):
            assert 'choosing a wedding date from predicting when marriage occurs' in prompt
            return {'success':True,'response':json.dumps({'reading_type':'muhurat','muhurat_transition':'new','answer_mode':'topic_reading','category':'general','route_action':'answer','muhurat_request':{'event_type':'vehicle'},'resolved_question':'Choose a purchase time'})}
    intent=asyncio.run(classify_verified_question(Router(),question='Choose a purchase time',history=[],language='english',query_context={'_prashna_previous':{'original_question':'Will I find my wallet?'}}))
    assert intent['mode']=='ELECT_MUHURAT' and intent['reading_transition']=='natal'
    intent=apply_prashna_transition(intent,'Choose a purchase time',intent['query_context'])
    assert not intent.get('workflow_choice') and not intent['query_context'].get('prashna')


def test_agent_uses_election_menu_contract_streaming_and_audit(monkeypatch):
    import asyncio,json,openai
    from types import SimpleNamespace
    from chat.verified_muhurat import generate_muhurat_response,MUHURAT_CAPABILITIES
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    sent=[]; streamed=[]
    class Events:
        async def __aenter__(self): return self
        async def __aexit__(self,*args): return False
        def __aiter__(self):
            async def events(): yield SimpleNamespace(type='response.output_text.delta',delta='**Choose the calculated window.**')
            return events()
        async def get_final_response(self): return SimpleNamespace(usage=None,output_text='')
    class Responses:
        async def create(self,**kwargs):
            sent.append(kwargs)
            calls=[]
            if len(sent)==1: calls=[SimpleNamespace(type='function_call',name='get_instant_baseline',call_id='base',arguments='{}')]
            elif len(sent)==2: calls=[SimpleNamespace(type='function_call',name='get_deterministic_evidence',call_id='panchang',arguments=json.dumps({'capability_id':'election.panchang','parameters':{'start_date':'2026-09-07','time':'10:00'}}))]
            return SimpleNamespace(id=str(len(sent)),usage=None,output=calls)
        def stream(self,**kwargs): sent.append(kwargs); return Events()
    monkeypatch.setattr(openai,'AsyncOpenAI',lambda **kwargs:SimpleNamespace(responses=Responses()))
    birth={'name':'Native','date':'1990-01-01','time':'10:20','latitude':28.4595,'longitude':77.0266,'timezone':'Asia/Kolkata'}
    result=asyncio.run(generate_muhurat_response(question='Choose my vehicle purchase time',intent={'query_context':{'muhurat_request':REQUEST,'_question_received_at':'2026-09-06T00:00:00+00:00'}},birth=birth,history=[],language='english',response_style='technical',model_name='gpt-5.6-luna',stream_callback=lambda delta,full:streamed.append(full),calculation_callback=None))
    assert streamed==['**Choose the calculated window.**']
    assert set(sent[0]['tools'][1]['parameters']['properties']['capability_id']['enum'])==set(MUHURAT_CAPABILITIES)
    assert 'VERIFIED MUHURAT ELECTION CONTRACT' in sent[-1]['input'][-1]['content'][0]['text']
    assert 'AUTHORITATIVE CURRENT SEARCH RESULT' in sent[-1]['input'][-1]['content'][0]['text']
    assert 'matching_windows_found' in sent[-1]['input'][-1]['content'][0]['text']
    baseline=json.loads(sent[1]['input'][0]['output'])
    assert baseline['candidates'] and 'historical_timing_evidence' not in baseline
    assert result['information_rounds']['reading_mode']=='ELECT_MUHURAT'
    assert result['information_rounds']['events'][0]['calculator']=='election.muhurat'
    assert result['information_rounds']['events'][-1]['success'] is True

def test_unsupported_activity_does_not_collect_useless_location_details():
    result=prepare_muhurat_intent({'reading_type':'muhurat','muhurat_request':{'event_type':'marriage'}},'Choose a wedding date',{})
    assert result['status']=='READY' and not result.get('muhurat_setup')
    assert calculate_muhurat_tool('election.muhurat',result['query_context']['muhurat_request'],{})['status']=='unsupported'

@pytest.mark.parametrize('offset',range(7))
def test_choghadiya_day_and_night_weekday_sequence(offset):
    from datetime import date,timedelta
    from panchang.panchang_calculator import PanchangCalculator
    # Sunday first: published weekday tables, independent expected sequences.
    day_sequences=[['Udvega','Chara','Labha','Amrita','Kala','Shubha','Roga','Udvega'],
        ['Amrita','Kala','Shubha','Roga','Udvega','Chara','Labha','Amrita'],
        ['Roga','Udvega','Chara','Labha','Amrita','Kala','Shubha','Roga'],
        ['Labha','Amrita','Kala','Shubha','Roga','Udvega','Chara','Labha'],
        ['Shubha','Roga','Udvega','Chara','Labha','Amrita','Kala','Shubha'],
        ['Chara','Labha','Amrita','Kala','Shubha','Roga','Udvega','Chara'],
        ['Kala','Shubha','Roga','Udvega','Chara','Labha','Amrita','Kala']]
    night_first=['Shubha','Chara','Kala','Udvega','Amrita','Roga','Labha']
    output=PanchangCalculator().calculate_choghadiya((date(2026,9,6)+timedelta(days=offset)).isoformat(),28.4595,77.0266,'Asia/Kolkata')
    assert [row['name'] for row in output['day_choghadiya']]==day_sequences[offset]
    assert output['night_choghadiya'][0]['name']==night_first[offset]
    assert len(output['night_choghadiya'])==8
    assert output['night_choghadiya'][0]['name']==output['night_choghadiya'][-1]['name']

@pytest.mark.parametrize('weekday,rahu,yama,gulika',[
    (0,7.5,10.5,13.5),(1,15,9,12),(2,12,7.5,10.5),(3,13.5,6,9),
    (4,10.5,15,7.5),(5,9,13.5,6),(6,16.5,12,15)])
def test_published_daytime_exclusion_table(weekday,rahu,yama,gulika):
    from calculators.muhurat_calculator import RAHU_SEGMENTS,YAMAGANDA_SEGMENTS,GULIKA_SEGMENTS
    # A 06:00–18:00 solar day: reference times, not a mirror of dict implementation.
    assert 6+RAHU_SEGMENTS[weekday]*1.5==rahu
    assert 6+YAMAGANDA_SEGMENTS[weekday]*1.5==yama
    assert 6+GULIKA_SEGMENTS[weekday]*1.5==gulika


def test_planned_purchase_never_recommends_elapsed_date_or_time():
    engine=VerifiedMuhuratCalculator()
    result=engine.search({**REQUEST,'not_before_utc':'2026-09-08T00:00:00+00:00'})
    assert not result['candidates'] and result['rejection_counts']['elapsed_date']==1
    cutoff='2026-09-07T05:00:00+00:00'
    result=engine.search({**REQUEST,'not_before_utc':cutoff})
    assert all(datetime.fromisoformat(row['start_time'])>=datetime.fromisoformat(cutoff) for row in result['candidates'])
    result=engine.search({**REQUEST,'check_time':'09:30','not_before_utc':'2026-09-07T05:00:00+00:00'})
    assert not result['candidates'] and result['rejection_counts']['elapsed_fixed_time']==1

@pytest.mark.parametrize('style',['simple','technical'])
def test_current_answer_contract_does_not_treat_tool_rounds_as_previous_readings(style):
    contract=muhurat_contract(style)
    assert 'CURRENT ANSWER, NOT A RECAP' in contract
    assert 'not previous answers received by the user' in contract
    assert 'never recommend an elapsed window' in contract

@pytest.mark.parametrize('style',['simple','technical'])
def test_muhurat_voice_is_personal_and_interpretive_not_an_algorithm_report(style):
    contract=muhurat_contract(style)
    assert 'Speak as Tara in a warm, calm, personal consultation' in contract
    assert 'inventories of placements without interpretation' in contract
    assert 'Do not treat a bare placement as' in contract
    assert 'Warmth must not disguise uncertainty' in contract
    assert 'not a personal birth-chart assessment' in contract


def test_completed_no_match_is_not_service_unavailable():
    result=VerifiedMuhuratCalculator().search({**REQUEST,'excluded_dates':['2026-09-07']})
    assert result['status']=='completed' and result['errors']==[]
    assert result['result_meaning']=='search_completed_no_matching_windows'
    contract=muhurat_contract('technical')
    assert 'status=completed means the calculation ran successfully' in contract
    assert 'Failure of an optional supplementary tool does not invalidate' in contract
