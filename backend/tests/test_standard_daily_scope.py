"""A date mention or a model's Daily label is not a one-day forecast request."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from datetime import datetime
import pytest
from ai.intent_router import apply_standard_daily_scope_guard, apply_transit_timing_guards

QUESTION='Mujhe kuch janana h mera tretment private hospital se chal raha h jo thora mahanga h doctor theek h ..ur hmne apna budget bhi bana liya h ..but dar ye ab mahadev se yahi prathana h ki delivery ache se ho jaye koi ur problem na ho ..wahi mujhe Janana h ki meri delivery me koi bhi problem to nhi hogi mai ur mera baby dono safe to rahenge. Ur delivery normal hogi ya c section plzz ache se bataye pasari jamini kepi ur nadi padati ke anusar details me'

def proposed_daily(**extra):
    return {'mode':'PREDICT_DAILY','category':'health','daily_intent_confirmed':True,
        'dasha_as_of':'2026-10-18','analysis_type':'DAILY_PREDICTION',
        'extracted_context':{'specific_date':'2026-10-18','specific_date_basis':'relative_user_day'},
        'transit_request':{'startYear':2026,'endYear':2026,'yearMonthMap':{'2026':['October']}},**extra}


def test_reported_delivery_question_cannot_become_daily_from_saved_router_flags():
    r=proposed_daily()
    apply_standard_daily_scope_guard(r,QUESTION)
    apply_transit_timing_guards(r,QUESTION,current_year=2026,now=datetime(2026,10,18,14,16))
    assert r['mode']=='ANALYZE_TOPIC_POTENTIAL'
    assert r['daily_intent_confirmed'] is False
    assert 'dasha_as_of' not in r and 'transit_request' not in r
    assert 'specific_date' not in r['extracted_context']

@pytest.mark.parametrize('question,reference',[
    ('Aaj ka din kaisa rahega?','Aaj'),
    ('आज का दिन कैसा रहेगा?','आज'),
    ('How will my interview go today?','today'),
    ('What about tomorrow?','tomorrow'),
    ('Demain, comment se passera mon entretien ?','Demain'),
    ('2026-10-18 ko mera din kaisa rahega?','2026-10-18'),
])
def test_genuine_day_request_keeps_daily_in_every_language(question,reference):
    r=proposed_daily(daily_scope_evidence={'source':'current_question','scope':'one_day_forecast',
        'request_quote':question,'day_reference':reference})
    apply_standard_daily_scope_guard(r,question)
    assert r['mode']=='PREDICT_DAILY' and r['daily_scope_validated']

@pytest.mark.parametrize('patch',[
    {'source':'history'}, {'source':'message_timestamp'}, {'request_quote':'Aaj ka din kaisa rahega?'},
    {'scope':'background_date'}, {'day_reference':'today'},
])
def test_ambient_or_ungrounded_date_cannot_confirm_daily(patch):
    evidence={'source':'current_question','scope':'one_day_forecast','request_quote':QUESTION,'day_reference':'ab'}
    evidence.update(patch)
    r=proposed_daily(daily_scope_evidence=evidence)
    apply_standard_daily_scope_guard(r,QUESTION)
    assert r['mode']!='PREDICT_DAILY'


def test_explicit_false_confirmation_is_not_overruled_by_mode_label():
    q='Aaj ka din kaisa rahega?'
    r=proposed_daily(daily_intent_confirmed=False,daily_scope_evidence={'source':'current_question','scope':'one_day_forecast','request_quote':q,'day_reference':'Aaj'})
    apply_standard_daily_scope_guard(r,q)
    assert r['mode']!='PREDICT_DAILY'


def test_no_date_daily_label_cannot_survive_timing_guard():
    r={'mode':'PREDICT_DAILY','category':'health','extracted_context':{}}
    apply_transit_timing_guards(r,QUESTION,current_year=2026,now=datetime(2026,10,18))
    assert r['mode']!='PREDICT_DAILY'


def test_router_provided_broader_event_mode_is_preserved_when_daily_rejected():
    r=proposed_daily(non_daily_mode='LIFESPAN_EVENT_TIMING')
    apply_standard_daily_scope_guard(r,QUESTION)
    assert r['mode']=='LIFESPAN_EVENT_TIMING' and r['answer_mode']=='event_prediction'


def test_daily_reducer_cannot_fabricate_today_when_no_date_was_resolved():
    from daily.daily_context_reducer import reduce_daily_context
    with pytest.raises(ValueError,match='explicitly resolved target date'):
        reduce_daily_context({'intent':{'mode':'PREDICT_DAILY'}},user_question=QUESTION)


def test_bad_daily_flags_cannot_promote_a_broader_mode_after_scope_guard():
    r=proposed_daily(mode='ANALYZE_TOPIC_POTENTIAL')
    apply_standard_daily_scope_guard(r,QUESTION)
    apply_transit_timing_guards(r,QUESTION,current_year=2026,now=datetime(2026,10,18))
    assert r['mode']=='ANALYZE_TOPIC_POTENTIAL' and r['daily_intent_confirmed'] is False


def test_grounded_request_can_still_promote_broader_router_mode_to_daily():
    q='How will my interview go today?'
    r=proposed_daily(mode='ANALYZE_TOPIC_POTENTIAL',daily_scope_evidence={'source':'current_question','scope':'one_day_forecast','request_quote':q,'day_reference':'today'})
    apply_standard_daily_scope_guard(r,q)
    apply_transit_timing_guards(r,q,current_year=2026,now=datetime(2026,10,18))
    assert r['mode']=='PREDICT_DAILY'


def test_standard_router_finalization_rejects_reported_saved_daily_classification():
    from ai.intent_router import IntentRouter
    r=proposed_daily(status='READY',divisional_charts=['D1','D7','D9'])
    output=IntentRouter.__new__(IntentRouter)._finalize_router_result(r,user_question=QUESTION,
        current_year=2026,current_month='October',resolved_now=datetime(2026,10,18,14,16),
        normalized_query_context={},include_chart_insights=False)
    assert output['mode']!='PREDICT_DAILY'
    assert output['daily_scope_validated'] is False
    assert output.get('dasha_as_of') is None
