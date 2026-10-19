from datetime import date, datetime, timedelta, timezone
import json
import pytest

from charts.mrityu_bhaga_service import scan_contacts, build_workspace, _connections
from prediction_engine.transit_returns import _angular_distance, _strict_planet_state

START = datetime(2026, 1, 1, tzinfo=timezone.utc)
BIRTH = dict(name='Synthetic', date='1990-01-01', time='12:00:00', latitude=28.6139, longitude=77.209, timezone='UTC+5:30')


def hours(at):
    return (at - START).total_seconds() / 3600


def dt(text):
    return datetime.fromisoformat(text)


def test_direct_crossing_wraps_zero_and_resolves_both_orb_edges():
    def state(at, planet):
        return (359 + hours(at)) % 360, 24
    rows = scan_contacts('Mercury', 0, .5, START, START + timedelta(hours=6), state)
    assert len(rows) == 1
    row = rows[0]
    assert abs((dt(row['start_at'])-START).total_seconds()-1800) <= 1
    assert abs((dt(row['end_at'])-START).total_seconds()-5400) <= 1
    assert abs((dt(row['exact_passes'][0]['at'])-START).total_seconds()-3600) <= 1
    assert row['exact_passes'][0]['motion'] == 'direct'


def test_retrograde_reentry_and_two_exact_roots_inside_one_screen_step():
    # Endpoints both outside, two roots around a station in one six-hour cell.
    def state(at, planet):
        h=hours(at)
        return (10 + (h-3)**2 - .5) % 360, 48*(h-3)
    rows = scan_contacts('Mercury', 10, .2, START, START+timedelta(hours=6), state)
    assert len(rows) == 2
    passes=[p for r in rows for p in r['exact_passes']]
    assert len(passes) == 2
    assert [p['motion'] for p in passes] == ['retrograde','direct']
    assert all(p['residual_degrees'] < .001 for p in passes)


def test_station_near_pass_is_retained_without_fabricating_exact_contact():
    def state(at, planet):
        h=hours(at)
        return 10 + (h-3)**2 + .25, 48*(h-3)
    rows=scan_contacts('Mercury',10,1,START,START+timedelta(hours=6),state)
    assert len(rows)==1
    assert rows[0]['exact_passes']==[]


def test_window_already_active_and_continuing_is_not_dropped():
    def state(at, planet): return 10.2, .001
    rows=scan_contacts('Saturn',10,1,START,START+timedelta(days=2),state)
    assert len(rows)==1
    assert rows[0]['clipped_start'] and rows[0]['clipped_end']
    assert not rows[0]['exact_passes']


def test_moon_short_window_is_not_lost_between_daily_samples():
    def state(at, planet): return (8 + hours(at)*.6)%360,14.4
    rows=scan_contacts('Moon',10,.1,START,START+timedelta(hours=12),state)
    assert len(rows)==1
    assert 1190 < (dt(rows[0]['end_at'])-dt(rows[0]['start_at'])).total_seconds() < 1210


def test_half_open_horizon_does_not_repeat_exact_contact_at_end():
    def state(at, planet): return 9+hours(at),24
    rows=scan_contacts('Mercury',10,1,START,START+timedelta(hours=1),state)
    assert rows[0]['exact_passes']==[]
    assert rows[0]['clipped_end']


def test_direct_and_dispositor_relationship_are_not_double_counted():
    point={'point':'Mercury','dispositor':'Mercury'}
    result=_connections(point,{'mahadasha':'Mercury'})
    assert result==[{'level':'mahadasha','lord':'Mercury','relation':'direct'}]


@pytest.mark.parametrize('changes', [dict(latitude=100),dict(longitude=float('nan')),dict(time=''),dict(timezone='nonsense')])
def test_invalid_birth_inputs_fail_explicitly(changes):
    with pytest.raises((ValueError,KeyError)):
        build_workspace({**BIRTH,**changes},date(2026,1,1),date(2026,2,1))


@pytest.mark.parametrize('start,end', [(date(2026,2,1),date(2026,1,1)),(date(2026,1,1),date(2027,1,2)),(date(1989,1,1),date(1989,2,1))])
def test_invalid_horizons_are_rejected(start,end):
    with pytest.raises(ValueError): build_workspace(BIRTH,start,end,calendar=True)


def test_real_ephemeris_workspace_matches_natal_and_preserves_audit():
    result=build_workspace(BIRTH,date(2026,10,18),date(2026,11,17),calendar=True,fast=True)
    assert result['natal']['affected_count']==1
    assert result['natal']['points'][0]['point']=='Ascendant'
    assert len(result['natal']['points'])==11
    assert result['calendar_calculated']
    assert result['events']
    assert result['range']['start_at']=='2026-10-17T18:30:00+00:00'
    assert result['audit']['node_type']=='mean'
    assert 'no analytic fallback' in result['audit']['ephemeris']
    for event in result['events']:
        assert dt(event['start_at']) < dt(event['end_at'])
        assert dt(result['range']['start_at']) <= dt(event['start_at'])
        assert dt(event['end_at']) <= dt(result['range']['end_at'])
        assert event['planet'] not in event['concurrent_transits']
        radius = .5 if event['kind']=='natal_mb_span' else event['orb_degrees']
        for key, clipped in [('start_at','clipped_start'),('end_at','clipped_end')]:
            if not event[clipped]:
                from calculators.chart_calculator import ChartCalculator
                lon,_=_strict_planet_state(dt(event[key]),event['planet'])
                lon=(lon-ChartCalculator.D1_CORRECTION)%360
                assert abs(_angular_distance(lon,event['target_longitude'])-radius) < .0003
        for exact in event['exact_passes']:
            lon,_=_strict_planet_state(dt(exact['at']),event['planet'])
            from calculators.chart_calculator import ChartCalculator
            lon = (lon - ChartCalculator.D1_CORRECTION) % 360
            assert _angular_distance(lon,event['target_longitude']) < .0003
        for overlap in event['dasha_overlaps']:
            assert event['start_at'] <= overlap['start_at'] < overlap['end_at'] <= event['end_at']
    json.dumps(result,allow_nan=False)


def test_true_nodes_and_alternate_ayanamsha_are_propagated():
    result=build_workspace({**BIRTH,'calculation_profile':{'ayanamsha':'raman','node_type':'true'}},date(2026,10,18),date(2026,10,25),calendar=True)
    assert result['audit']['ayanamsha']=='raman'
    assert result['audit']['node_type']=='true'
    assert result['audit']['longitude_correction_degrees']==.0006


def test_missing_gulika_is_reported_as_incomplete_not_a_negative_finding():
    from charts.mrityu_bhaga_service import natal_assessment
    from calculators.chart_calculator import ChartCalculator
    from types import SimpleNamespace
    chart=ChartCalculator({}).calculate_chart(SimpleNamespace(**BIRTH))
    chart['planets'].pop('Gulika')
    chart['planets'].pop('Mandi')
    chart['upagraha_calculation']={'success':False,'error':'Local sunrise unavailable'}
    result=natal_assessment(chart)
    assert result['complete'] is False
    assert result['unavailable_points']==[{'point':'Gulika / Mandi','reason':'Local sunrise unavailable'}]


def test_ephemeris_failure_does_not_become_empty_calendar(monkeypatch):
    from prediction_engine.errors import PredictionCalculationError
    def fail(*a,**kw): raise PredictionCalculationError('missing ephemeris')
    monkeypatch.setattr('charts.mrityu_bhaga_service._strict_planet_state',fail)
    with pytest.raises(PredictionCalculationError):
        build_workspace(BIRTH,date(2026,10,18),date(2026,11,17),calendar=True)


def test_birth_time_comparison_and_second_precision_are_preserved():
    result=build_workspace({**BIRTH,'time':'12:00:42'},date(2026,10,18),date(2026,11,17),birth_time_minutes=10)
    assert [r['offset_minutes'] for r in result['birth_time_comparison']]==[-10,0,10]
    assert result['birth_time_comparison'][1]['birth_local'].endswith('12:00:42+05:30')
    assert result['natal_chart']['ascendant'] is not None
    assert result['natal']['points'][0]['point']=='Ascendant'


def test_dasha_intervals_are_contiguous_across_actual_transitions():
    from charts.mrityu_bhaga_service import dasha_timeline
    rows=dasha_timeline(BIRTH,START,START+timedelta(days=365),'lahiri')
    assert len(rows)>1
    for previous,current in zip(rows,rows[1:]):
        assert previous['end_at']==current['start_at']
        assert current['start_at'] < current['end_at']
    assert rows[0]['start_at']==START.isoformat()
    assert rows[-1]['end_at']==(START+timedelta(days=365)).isoformat()


def test_workspace_http_contract_and_explicit_calculation_failure(monkeypatch):
    from fastapi import FastAPI
    import asyncio
    import httpx
    from charts.routes import router
    from auth import get_current_user
    app=FastAPI()
    app.include_router(router,prefix='/api')
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url="http://test") as client:
            response=await client.post('/api/mrityu-bhaga-workspace',json={'birth_data':BIRTH,'start_date':'2026-10-18','end_date':'2026-11-17'})
            assert response.status_code==403
            app.dependency_overrides[get_current_user]=lambda: object()
            response=await client.post('/api/mrityu-bhaga-workspace',json={'birth_data':BIRTH,'start_date':'2026-10-18','end_date':'2026-11-17'})
            assert response.status_code==200
            assert response.json()['natal']['affected_count']==1
            response=await client.post('/api/mrityu-bhaga-workspace',json={'birth_data':BIRTH,'start_date':'2026-10-18','end_date':'2028-11-17'})
            assert response.status_code==422
            from prediction_engine.errors import PredictionCalculationError
            def fail(*a,**kw): raise PredictionCalculationError('missing ephemeris')
            monkeypatch.setattr('charts.mrityu_bhaga_service._strict_planet_state',fail)
            response=await client.post('/api/mrityu-bhaga-workspace',json={'birth_data':BIRTH,'start_date':'2026-10-18','end_date':'2026-11-17','calendar':True})
            assert response.status_code==503
            assert 'no fallback' in response.json()['detail']
    asyncio.run(exercise())


@pytest.mark.parametrize('md_index',range(9))
def test_every_mahadasha_transition_including_cycle_continuation_has_no_gap(md_index):
    from charts.mrityu_bhaga_service import dasha_timeline
    from shared.dasha_calculator import DashaCalculator
    calc=DashaCalculator()
    md=calc.calculate_current_dashas(BIRTH,datetime(2026,1,1),strict=True)['maha_dashas'][md_index]
    transition=(md['end']+timedelta(seconds=1)).replace(tzinfo=timezone(timedelta(hours=5.5))).astimezone(timezone.utc)
    rows=dasha_timeline(BIRTH,transition-timedelta(days=2),transition+timedelta(days=2),'lahiri')
    assert rows[0]['lords']['mahadasha']==md['planet']
    assert rows[-1]['lords']['mahadasha']==calc.PLANET_ORDER[(calc.PLANET_ORDER.index(md['planet'])+1)%9]
    assert rows[0]['start_at']==(transition-timedelta(days=2)).isoformat()
    assert rows[-1]['end_at']==(transition+timedelta(days=2)).isoformat()
    for left,right in zip(rows,rows[1:]):
        assert left['end_at']==right['start_at']


def test_initial_birth_balance_subdivisions_cover_without_replaying_clipped_ad():
    from charts.mrityu_bhaga_service import dasha_timeline
    start=datetime(1990,1,2,tzinfo=timezone.utc)
    rows=dasha_timeline(BIRTH,start,start+timedelta(days=364),'lahiri')
    assert rows[0]['start_at']==start.isoformat()
    assert rows[-1]['end_at']==(start+timedelta(days=364)).isoformat()
    for left,right in zip(rows,rows[1:]):
        assert left['end_at']==right['start_at']
