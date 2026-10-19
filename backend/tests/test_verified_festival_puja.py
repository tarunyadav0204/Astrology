"""Independent published examples + intake/isolation/precision regressions."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta
import pytest
from festivals.verified_puja import VerifiedFestivalCalculator, coverage_catalog, resolve_festival, _state, _dt
from festivals.festival_data import HINDU_FESTIVALS
from chat.verified_muhurat import prepare_muhurat_intent, calculate_muhurat_tool, muhurat_contract, MuhuratRequest
from calculators.verified_muhurat_calculator import julian

DELHI = {'name':'Delhi','latitude':28.6139,'longitude':77.209,'timezone':'Asia/Kolkata'}

def request(festival, start='2026-01-01', end='2026-12-31', **extras):
    return {'event_type':'festival_puja','festival_id':festival,'start_date':start,'end_date':end,'location':DELHI,**extras}

@pytest.mark.parametrize('text,key', [('dusehra puja','dussehra'),('दशहरा पूजा','dussehra'),('Deepavali','diwali'),('Chaitra Navratri','chaitra_navratri'),('Maha Shivaratri','maha_shivratri'),('Ganesh Chaturthi','ganesh_chaturthi')])
def test_festival_aliases(text,key):
    assert resolve_festival(text)==key

# Drik Panchang city pages, 2026 Delhi. Tolerances account for ephemeris,
# displayed minute rounding and geographic differences within Delhi.
@pytest.mark.parametrize('festival,day,start,end', [
    ('dussehra','2026-10-20','13:14','15:30'),
    ('diwali','2026-11-08','17:54','19:50'),
    ('ganesh_chaturthi','2026-09-14','11:02','13:31'),
    ('vasant_panchami','2026-01-23','07:13','12:33'),
])
def test_published_delhi_2026_windows(festival,day,start,end):
    result=calculate_muhurat_tool('election.muhurat',request(festival),{})
    assert result['status']=='completed'
    assert len(result['candidates'])==1
    window=result['candidates'][0]
    assert window['date']==day
    for key,expected in [('start',start),('end',end)]:
        actual=datetime.fromisoformat(window[key])
        reference=datetime.fromisoformat(day+'T'+expected+'+05:30')
        assert abs((actual-reference).total_seconds())<120
    assert result['sources']


def test_nishita_crosses_civil_midnight_without_clipping():
    r=VerifiedFestivalCalculator().search(request('maha_shivratri'))
    w=r['candidates'][0]
    assert w['date']=='2026-02-15'
    assert w['start'].startswith('2026-02-16T00:')
    assert w['end'].startswith('2026-02-16T01:')
    assert datetime.fromisoformat(w['end'])-datetime.fromisoformat(w['start'])>timedelta(minutes=45)


def test_single_day_range_cannot_hide_neighboring_date_priority():
    assert VerifiedFestivalCalculator().search(request('dussehra','2026-10-21','2026-10-21'))['candidates']==[]
    assert VerifiedFestivalCalculator().search(request('dussehra','2026-10-20','2026-10-20'))['candidates']


def test_unimplemented_rites_and_traditions_not_substituted():
    for extras in ({'ritual':'Durga Visarjan'},{'tradition':'Bengali immersion'}):
        r=VerifiedFestivalCalculator().search(request('dussehra',**extras))
        assert r['status']=='partial' and not r['candidates']
        assert r['coverage']=='panchang_only' and r['tithi_intervals']
    r=VerifiedFestivalCalculator().search(request('holika_dahan'))
    assert not r['candidates'] and r['status']=='partial' # Bhadra not implemented; no fake evening window.


def test_polar_sun_failure_is_partial_not_synthetic_sunrise():
    r=VerifiedFestivalCalculator().search(request('ganesh_chaturthi',location={**DELHI,'latitude':89,'longitude':0,'timezone':'UTC'}))
    assert r['status']=='partial' and not r['candidates'] and r['errors']


def test_every_catalog_entry_has_explicit_coverage_and_synced_client_catalogs():
    catalog=coverage_catalog()
    assert {x['id'] for x in catalog}==set(HINDU_FESTIVALS)
    root=Path(__file__).resolve().parents[2]
    for client in ['frontend','astroroshni_mobile']:
        assert json.loads((root/client/'src/data/festivalPujaCatalog.json').read_text())==catalog
    for festival in HINDU_FESTIVALS:
        r=VerifiedFestivalCalculator().search(request(festival,'2026-10-01','2026-10-31'))
        assert r['status'] in {'completed','partial'}
        if r['coverage']=='panchang_only': assert not r['candidates']


def test_missing_city_asks_setup_with_trusted_year_and_roman_hindi():
    i=prepare_muhurat_intent({'reading_type':'muhurat','response_language':'Hindi in Latin script','muhurat_request':{'event_type':'dusehra puja','personalized':True}},'Meri kundli ke hisab se dusehra puja ka samay kya hona chahiye',{'_question_received_at':'2026-10-18T16:15:31+00:00'})
    assert i['status']=='CLARIFY'
    draft=i['muhurat_setup']['muhurat_request']
    assert draft['festival_id']=='dussehra' and draft['festival_year']==2026
    assert 'location' not in draft
    assert draft['allowed_start']=='00:00' and draft['allowed_end']=='23:59'
    assert 'shehar' in i['clarification_question']


def test_personal_checks_separate_and_do_not_move_ritual():
    birth={'date':'1990-01-01','time':'10:20','latitude':28.45,'longitude':77.02,'timezone':'Asia/Kolkata'}
    general=VerifiedFestivalCalculator().search(request('diwali'))
    personal=VerifiedFestivalCalculator().search(request('diwali',personalized=True),birth)
    assert [(w['start'],w['end']) for w in general['candidates']]==[(w['start'],w['end']) for w in personal['candidates']]
    assert personal['candidates'][0]['personal_checks'][0]['method']=='Midpoint Moon comparison only'
    assert 'VERIFIED FESTIVAL PUJA CONTRACT' in muhurat_contract('technical',request('diwali'))


def test_future_cutoff_and_availability_cannot_move_festival():
    r=VerifiedFestivalCalculator().search(request('diwali',not_before_utc='2026-11-09T00:00:00+00:00'))
    assert not r['candidates']
    r=VerifiedFestivalCalculator().search(request('diwali',allowed_start='08:00',allowed_end='12:00'))
    assert not r['candidates']


def test_tithi_boundaries_are_actual_changes_not_daily_samples():
    r=VerifiedFestivalCalculator().search(request('diwali'))
    span=r['tithi_intervals'][0]
    a,b=map(datetime.fromisoformat,[span['start'],span['end']])
    assert _state(julian(a-timedelta(seconds=2)))==29
    assert _state(julian(a+timedelta(seconds=2)))==30
    assert _state(julian(b-timedelta(seconds=2)))==30
    assert _state(julian(b+timedelta(seconds=2)))==1


def test_date_bounds_and_unknown_festival_rejected():
    for patch in ({'festival_id':'not-real'},{'end_date':'2027-01-02'}):
        with pytest.raises(ValueError): MuhuratRequest.model_validate(request('diwali',**patch))


def test_ambiguous_festival_names_require_selection():
    assert resolve_festival('Diwali or Dussehra') is None


def test_router_preserves_roman_hindi_despite_english_ui():
    import asyncio
    from chat.verified_chat_pipeline import classify_verified_question
    class Router:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            assert 'Hindi in Latin script' in prompt
            return {'success':True,'response':json.dumps({'reading_type':'muhurat','muhurat_transition':'new',
                'answer_mode':'topic_reading','category':'general','route_action':'answer',
                'muhurat_request':{'event_type':'dusehra puja','personalized':True},
                'response_language':'Hindi in Latin script','resolved_question':'Meri kundli ke hisab se dusehra puja ka samay kya hona chahiye'})}
    intent=asyncio.run(classify_verified_question(Router(),question='Meri kundli ke hisab se dusehra puja ka samay kya hona chahiye',history=[],language='english',query_context={}))
    assert intent['response_language']=='Hindi in Latin script'
    assert intent['reading_type']=='muhurat'


def test_incomplete_ritual_explanation_is_flagged_no_charge(monkeypatch):
    import asyncio
    import chat.verified_chat_pipeline as pipeline
    from chat.verified_muhurat import generate_muhurat_response
    async def agent(**kwargs): return {'success':True,'response':'Calculated tithi; ritual rules are incomplete.'}
    monkeypatch.setattr(pipeline,'run_verified_calculator_agent',agent)
    r=asyncio.run(generate_muhurat_response(question='Holika dahan time',intent={'query_context':{'muhurat_request':request('holika_dahan'),'_question_received_at':'2026-01-01T00:00:00+00:00'}},birth={},history=[],language='english',response_style='technical',model_name='test',stream_callback=None,calculation_callback=None))
    assert r['skip_verified_muhurat_charge'] is True
    assert r['next_action']=={'type':'none'} # Never shift an annual festival by 30 days.

@pytest.mark.parametrize('ritual',['Aparajita puja','Aparajita Pooja','aparajita_puja','Shami puja','Aparajita/Shami puja','अपराजिता पूजा','शमी पूजा'])
def test_gurgaon_dussehra_ritual_aliases_do_not_downgrade_coverage(ritual):
    r=VerifiedFestivalCalculator().search(request('dussehra',ritual=ritual,location={**DELHI,'name':'Gurgaon','latitude':28.4595,'longitude':77.0266}))
    assert r['status']=='completed' and r['coverage']=='ritual_window'
    assert r['candidates'][0]['date']=='2026-10-20'
    assert r['candidates'][0]['start'].startswith('2026-10-20T13:14:')
    assert r['coverage_reason'] is None

@pytest.mark.parametrize('ritual',['Durga Visarjan','Exact Vijaya Muhurat','Aparajita puja and Durga Visarjan'])
def test_other_dussehra_rites_remain_distinct(ritual):
    r=VerifiedFestivalCalculator().search(request('dussehra',ritual=ritual))
    assert r['coverage']=='panchang_only' and not r['candidates']
    assert 'explicitly requested ritual' in r['coverage_reason']


def test_gurgaon_dussehra_rahu_overlap_has_practical_non_overlapping_portion():
    r=VerifiedFestivalCalculator().search(request('dussehra',ritual='Aparajita puja',location={**DELHI,'name':'Gurgaon','latitude':28.4595,'longitude':77.0266}))
    window=r['candidates'][0];overlay=window['rahu_kaal']
    assert overlay['status']=='calculated' and overlay['overlaps_ritual_window']
    rahu=overlay['intervals'][0]
    assert rahu['start'].startswith('2026-10-20T14:57:')
    assert rahu['end'].startswith('2026-10-20T16:22:')
    outside=overlay['windows_outside_rahu_kaal']
    assert len(outside)==1
    assert outside[0]['start']==window['start']
    assert outside[0]['end']==rahu['start']
    # Keep the broad traditional window; Rahu avoidance is an additional overlay.
    assert window['end'].startswith('2026-10-20T15:31:')
    assert datetime.fromisoformat('2026-10-20T14:23:02+05:30') < datetime.fromisoformat(outside[0]['end'])


def test_rahu_overlay_subtracts_both_sides_or_complete_overlap():
    from festivals.verified_puja import rahu_kaal_overlay
    from zoneinfo import ZoneInfo
    place={**DELHI,'name':'Gurgaon','latitude':28.4595,'longitude':77.0266};zone=ZoneInfo('Asia/Kolkata')
    dt=lambda t:datetime.fromisoformat('2026-10-20T'+t+'+05:30')
    split=rahu_kaal_overlay(dt('14:00'),dt('17:00'),place,zone)
    assert len(split['windows_outside_rahu_kaal'])==2
    full=rahu_kaal_overlay(dt('15:00'),dt('16:00'),place,zone)
    assert full['overlaps_ritual_window'] and full['windows_outside_rahu_kaal']==[]
    clean=rahu_kaal_overlay(dt('13:30'),dt('14:30'),place,zone)
    assert not clean['overlaps_ritual_window'] and len(clean['windows_outside_rahu_kaal'])==1

@pytest.mark.parametrize('clock,inside',[('14:23',False),('15:00',True)])
def test_fixed_puja_time_is_explicitly_checked_against_rahu_kaal(clock,inside):
    r=VerifiedFestivalCalculator().search(request('dussehra',check_time=clock,location={**DELHI,'latitude':28.4595,'longitude':77.0266}))
    assert r['candidates'][0]['rahu_kaal']['checked_time']['within_rahu_kaal'] is inside


def test_practical_puja_minutes_stay_inside_the_calculated_rahu_avoiding_portion():
    r=VerifiedFestivalCalculator().search(request('dussehra',location={**DELHI,'latitude':28.4595,'longitude':77.0266}))
    overlay=r['candidates'][0]['rahu_kaal'];practical=overlay['practical_windows'][0]
    raw=overlay['windows_outside_rahu_kaal'][0]
    assert practical['start']=='2026-10-20T13:15+05:30'
    assert practical['end']=='2026-10-20T14:57+05:30'
    assert datetime.fromisoformat(practical['start'])>=datetime.fromisoformat(raw['start'])
    assert datetime.fromisoformat(practical['end'])<=datetime.fromisoformat(raw['end'])
