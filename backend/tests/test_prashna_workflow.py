import asyncio
import json
import pytest
from chat.prashna_workflow import apply_prashna_transition
from chat.verified_prashna import freeze_prashna
from chat.verified_chat_pipeline import classify_verified_question
from chat_history.clarification_cards import build_clarification_next_action
from datetime import datetime, timezone

PLACE = {'name':'Gurugram', 'latitude':28.4595, 'longitude':77.0266}
OLD = freeze_prashna(PLACE, datetime(2026,10,9,13,0,tzinfo=timezone.utc))
OLD['original_question'] = 'Will I find my lost wallet?'
NEW_TIME = '2026-10-09T15:00:00+00:00'

def route(transition, question='What about tomorrow?', **extra):
    return apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':transition,**extra}, question, {'_prashna_previous':OLD, '_question_received_at':NEW_TIME})

def test_same_concern_preserves_exact_chart_and_understands_reference():
    result=route('continue_prashna')
    assert result['query_context']['prashna']==OLD
    assert 'lost wallet' in result['resolved_question']
    assert 'What about tomorrow?' in result['resolved_question']

def test_changed_prashna_concern_gets_new_clock_not_old_question():
    result=route('new_prashna', 'Will my maid quit?')
    fixed=result['query_context']['prashna']
    assert fixed['submitted_at']==NEW_TIME
    assert fixed['original_question']=='Will my maid quit?'
    assert fixed['location']==OLD['location']
    assert OLD['original_question']=='Will I find my lost wallet?'

@pytest.mark.parametrize('extra', [{'reading_type':'chart_dasha_analysis'},{'mode':'PREDICT_DAILY'},{'route_action':'handoff'},{'route_action':'out_of_scope'},{'route_action':'ack'}])
def test_natal_and_non_analysis_routes_cannot_reuse_question_chart(extra):
    result=route('continue_prashna','Explain my D9',**extra)
    assert 'prashna' not in result['query_context']
    assert result['reading_transition']=='natal'
    assert result['resolved_question']=='Explain my D9'

def test_natal_switch_discards_old_clarification_chain_and_sticky_client_method():
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'natal'}, 'How is my career overall?',
        {'prashna':OLD, 'prashna_requested':True, 'prashna_choice':'prashna', 'prashna_location':PLACE, '_clarification_context':'Will I find my lost wallet? How is my career overall?'})
    assert not any(k in result['query_context'] for k in ('prashna','prashna_choice','prashna_location','prashna_requested'))
    assert result['resolved_question']=='How is my career overall?'

@pytest.mark.parametrize('transition',['clarify_workflow','none'])
def test_ambiguous_or_missing_router_decision_stops_for_scope_cards(transition):
    result=route(transition,'And that?')
    assert result['status']=='CLARIFY'
    assert 'prashna' not in result['query_context']
    cards=build_clarification_next_action(result,'And that?')
    assert cards['choice_kind']=='prashna_scope'
    assert [x['query_context']['prashna_workflow_choice'] for x in cards['options']]==['continue','new']

def test_city_change_requires_selection_and_does_not_reuse_city():
    result=route('new_prashna','Will I find my keys here?',requires_new_location=True)
    assert result['status']=='CLARIFY'
    assert 'prashna' not in result['query_context']
    assert build_clarification_next_action(result,'question')['options'][0]['id']=='prashna'

@pytest.mark.parametrize('decision,transition', [('natal','natal'),('continue','continue_prashna'),('new','natal')])
def test_scope_choices_do_not_reenter_identical_card_loop(decision,transition):
    qc={'_prashna_previous':OLD, '_question_received_at':NEW_TIME}
    qc.update({'prashna_choice':'natal'} if decision=='natal' else {'prashna_workflow_choice':decision})
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'none'},'And that?',qc)
    assert result['reading_transition']==transition
    assert not result.get('workflow_choice')
    if decision=='new': assert result['status']=='CLARIFY'

@pytest.mark.parametrize('transition',['natal','continue_prashna','new_prashna','clarify_workflow'])
def test_semantic_router_passes_latest_question_and_transition(transition):
    class Router:
        async def generate_text_from_prompt(self,prompt,**kwargs):
            assert 'LATEST question on EVERY turn' in prompt
            assert 'never the entire conversation' in prompt
            assert 'old clarification' in prompt or 'abandoned concern' in prompt
            assert 'QUESTION: Explain my D9' in prompt
            return {'success':True,'response':json.dumps({'reading_transition':transition,'resolved_question':'Explain my D9', 'answer_mode':'topic_reading','route_action':'answer','prashna_intent':'none'})}
    intent=asyncio.run(classify_verified_question(Router(),question='Explain my D9',history=[],language='english',query_context={'_prashna_previous':OLD}))
    assert intent['reading_transition']==transition
    assert intent['resolved_question']=='Explain my D9'


def test_explicit_natal_card_overrides_incorrect_model_continuation():
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'continue_prashna'},
        'Will I find my lost wallet?',{'_prashna_previous':OLD,'prashna_choice':'natal'})
    assert result['reading_transition']=='natal'
    assert 'prashna' not in result['query_context']


def test_confirmed_new_city_is_used_after_location_card():
    place={'name':'Mumbai','latitude':19.0760,'longitude':72.8777}
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'new_prashna','requires_new_location':True},
        'Will I find my keys?',{'_prashna_previous':OLD,'prashna_choice':'prashna','prashna_location':place,'_question_received_at':NEW_TIME})
    assert result['query_context']['prashna']['location']['name']=='Mumbai'
    assert result['query_context']['prashna']['submitted_at']==NEW_TIME


def test_missing_city_never_starts_question_chart_generation():
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'new_prashna'},
        'Will I find my keys?',{'_question_received_at':NEW_TIME})
    assert result['status']=='CLARIFY'
    assert 'prashna' not in result['query_context']
    assert build_clarification_next_action(result,'Will I find my keys?')['choice_kind']=='prashna_method'


def test_no_prashna_context_retains_regular_clarification_chain():
    result=apply_prashna_transition({'status':'READY','route_action':'answer','reading_transition':'none'},
        'Both together',{'_clarification_context':'Will I get promoted? Both responsibility and formal recognition together.'})
    assert 'formal recognition' in result['resolved_question']
    assert result['status']=='READY'
