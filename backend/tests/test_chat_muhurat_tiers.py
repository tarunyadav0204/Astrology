"""Cross-tier election parity, no unrelated school work, streaming and accounting."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from chat.muhurat_workflow import prepare_chat_muhurat, generate_chat_muhurat
from chat.verified_muhurat import calculate_muhurat_tool

CITY={'name':'Delhi','latitude':28.6139,'longitude':77.209,'timezone':'Asia/Kolkata'}
REQUEST={'event_type':'festival_puja','festival_id':'diwali','start_date':'2026-01-01','end_date':'2026-12-31','location':CITY,'personalized':False}
INTENT={'mode':'ELECT_MUHURAT','query_context':{'muhurat_request':REQUEST,'_question_received_at':'2026-10-18T12:00:00+00:00'}}

class Writer:
    def __init__(self, fail_review=False): self.calls=[];self.fail_review=fail_review
    async def generate_text_from_prompt(self,prompt,**kwargs):
        self.calls.append((prompt,kwargs))
        await asyncio.sleep(0)
        if self.fail_review and kwargs['llm_log_tag'].endswith('ritual_review'): raise RuntimeError('review failed')
        if kwargs.get('stream_callback'): kwargs['stream_callback']('Answer','Answer')
        return {'success':True,'response':'Answer','chat_llm_provider':'test','chat_llm_model':'test-model',
                'token_usage':{'input_tokens':10,'output_tokens':2,'cached_tokens':3,'non_cached_input_tokens':7}}

@pytest.mark.parametrize('tier',['instant','standard','premium'])
def test_missing_city_uses_same_setup_and_keeps_tier(tier):
    i=prepare_chat_muhurat({'answer_mode':'dedicated_muhurat_flow','extracted_context':{'muhurat_event_type':'dusehra puja','festival_year':2026,'muhurat_personalized':True}},'Dussehra puja time',{},chat_tier=tier)
    assert i['status']=='CLARIFY' and i['mode']=='ELECT_MUHURAT'
    action=i['muhurat_setup']['options'][0]['query_context']
    assert action['muhurat_chat_tier']==tier and action['muhurat_request']['festival_id']=='dussehra'
    assert i['divisional_charts']==[] and i['needs_transits'] is False


def test_normal_question_does_not_inherit_previous_election():
    normal={'answer_mode':'topic_reading','mode':'ANALYZE_TOPIC_POTENTIAL'}
    assert prepare_chat_muhurat(normal,'Tell me about career',{'_muhurat_previous':REQUEST})==normal


def test_confirmed_setup_overrides_router_and_new_city_is_not_birthplace():
    i=prepare_chat_muhurat({'answer_mode':'topic_reading'},'Check selected puja details',{'muhurat_request':REQUEST},chat_tier='premium')
    assert i['status']=='READY'
    assert i['query_context']['muhurat_request']['location']['name']=='Delhi'


@pytest.mark.parametrize('parallel,premium',[(False,False),(True,False),(True,True)])
def test_all_tiers_use_identical_calculated_windows_and_record_all_calls(parallel,premium):
    writer=Writer();stream=[]
    result=asyncio.run(generate_chat_muhurat(writer,question='Diwali puja time',intent=INTENT,birth={},language='english',response_style='simple',parallel=parallel,premium_analysis=premium,stream_callback=lambda delta,full:stream.append(delta)))
    expected=calculate_muhurat_tool('election.muhurat',REQUEST,{})
    assert result['muhurat_evidence']['candidates']==expected['candidates']
    assert result['success'] and stream==['Answer']
    assert all(kwargs['premium_analysis']==premium for _,kwargs in writer.calls)
    stages=[kwargs['llm_log_tag'] for _,kwargs in writer.calls]
    assert stages==(['muhurat_ritual_review','muhurat_merge'] if parallel else ['muhurat_answer'])
    assert result['token_usage']['input_tokens']==10*len(stages)
    assert result['skip_verified_muhurat_charge'] is False
    if parallel: assert len(result['timing']['parallel_llm_usage']['stages'])==len(stages)


def test_personal_review_is_opt_in_and_parallel_avoids_all_school_setup(monkeypatch):
    import ai.parallel_chat.orchestrator as orchestrator
    def prohibited(*a,**k): raise AssertionError('Unrelated school setup executed')
    for name in ['_chart_focus_branch_plan','merged_context_to_agent_context','build_all_parallel_agent_payloads','plan_parallel_branches']:
        monkeypatch.setattr(orchestrator,name,prohibited)
    writer=Writer()
    personal={**INTENT,'query_context':{**INTENT['query_context'],'muhurat_request':{**REQUEST,'personalized':True}}}
    result=asyncio.run(orchestrator.run_parallel_chat_pipeline(writer,user_question='Diwali puja for my kundli',astrological_context={'intent':personal,'birth_details':{}},conversation_history=[],language='english',response_style='technical',user_context=None,premium_analysis=True,mode='ELECT_MUHURAT',total_request_start=0))
    assert result['success']
    assert {kw['llm_log_tag'] for _,kw in writer.calls}=={'muhurat_ritual_review','muhurat_personal_review','muhurat_merge'}
    assert result['token_usage']['input_tokens']==30


def test_failed_optional_review_does_not_invalidate_calculated_baseline():
    result=asyncio.run(generate_chat_muhurat(Writer(fail_review=True),question='Diwali puja',intent=INTENT,birth={},language='english',response_style='simple',parallel=True))
    assert result['success'] and result['muhurat_evidence']['candidates']


def test_incomplete_ritual_is_free_and_never_shifts_festival():
    intent={**INTENT,'query_context':{**INTENT['query_context'],'muhurat_request':{**REQUEST,'festival_id':'holika_dahan'}}}
    result=asyncio.run(generate_chat_muhurat(Writer(),question='Holika Dahan timing',intent=intent,birth={},language='english',response_style='simple',parallel=True))
    assert result['success'] and result['skip_verified_muhurat_charge'] is True
    assert result['next_action']=={'type':'none'}


def test_instant_dispatch_never_builds_legacy_graph_and_streams(monkeypatch):
    import chat.instant_chat_pipeline as pipeline
    def prohibited(*a,**k): raise AssertionError('Legacy Muhurat/graph work executed')
    monkeypatch.setattr(pipeline,'_instant_real_muhurat_evidence',prohibited)
    monkeypatch.setattr(pipeline,'get_instant_chat_model',lambda:'test-instant-model')
    monkeypatch.setattr(pipeline,'get_instant_chat_llm_provider',lambda:'test-provider')
    writer=Writer();stream=[]
    r=asyncio.run(pipeline.generate_instant_chat_response(writer,question='Diwali puja timing',birth_data={},intent=INTENT,history=[],stream_callback=lambda d,f:stream.append(d)))
    assert r['success'] and stream==['Answer']
    assert writer.calls[0][1]['model_name_override']=='test-instant-model'
    assert writer.calls[0][1]['provider_override']=='test-provider'


def test_standard_analyzer_dispatch_never_builds_normal_response_format(monkeypatch):
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    import utils.admin_settings as settings
    # Bypass service initialization: this route needs only text generation.
    analyzer=object.__new__(GeminiChatAnalyzer)
    writer=Writer()
    analyzer.generate_text_from_prompt=writer.generate_text_from_prompt
    monkeypatch.setattr(settings,'is_debug_logging_enabled',lambda:False)
    monkeypatch.setattr(settings,'get_chat_llm_provider',lambda:'test')
    monkeypatch.setattr(settings,'get_chat_llm_provider_premium',lambda:'test')
    r=asyncio.run(analyzer.generate_chat_response(user_question='Diwali puja timing',astrological_context={'intent':INTENT,'birth_details':{}},premium_analysis=True))
    assert r['success']
    assert all(kw['premium_analysis'] for _,kw in writer.calls)
    assert [kw['llm_log_tag'] for _,kw in writer.calls]==['muhurat_ritual_review','muhurat_merge']
