from datetime import date, datetime
import asyncio
import json
import pytest
from charts.bhrigu_bindu_service import build_workspace, natal_assessment, connections
from calculators.sniper_points_calculator import bhrigu_bindu_longitude, SniperPointsCalculator
from prediction_engine.transit_returns import _angular_distance, _strict_planet_state
from calculators.chart_calculator import ChartCalculator

BIRTH = dict(name='Synthetic', date='1990-01-01', time='12:00:42', latitude=28.6139, longitude=77.209, timezone='UTC+5:30')


def test_natal_matches_shared_calculation_without_rounding_and_not_a_planet():
    data = build_workspace(BIRTH, date(2026,10,18), date(2026,11,17))
    chart = data['natal_chart']
    point = data['natal']['points'][0]
    expected = bhrigu_bindu_longitude(chart['planets']['Moon']['longitude'], chart['planets']['Rahu']['longitude'])
    assert point['longitude'] == expected
    public = SniperPointsCalculator(chart, {}, {}).calculate_bhrigu_bindu(False)
    assert round(expected, 2) == public['longitude']
    assert point['house'] == public['house']
    assert point['nakshatra'] == public['nakshatra']
    assert point['pada'] == public['pada']
    assert 'strength' not in point and 'dignity' not in point and 'combustion' not in point
    assert point['dispositor_strength']
    assert not data['events'] and not data['calendar_calculated']
    assert data['audit']['node_type'] == 'mean'
    json.dumps(data, allow_nan=False)


def test_birth_time_endpoints_have_real_positions_and_preserve_seconds():
    data = build_workspace(BIRTH, date(2026,10,18), date(2026,11,17), birth_time_minutes=10)
    rows = data['birth_time_comparison']
    assert [r['offset_minutes'] for r in rows] == [-10,0,10]
    assert rows[0]['longitude'] != rows[2]['longitude']
    assert rows[1]['longitude'] == data['natal']['points'][0]['longitude']
    assert ':42' in rows[1]['birth_local']


def test_dasha_roles_preserve_multiple_reasons_without_duplicate_level():
    point = {'dispositor': 'Moon', 'nakshatra_lord': 'Rahu'}
    rows = connections(point, {'mahadasha':'Moon','antardasha':'Rahu','pratyantardasha':'Venus'})
    assert len(rows) == 2
    assert rows[0]['roles'] == ['moon','sign_ruler']
    assert rows[1]['roles'] == ['rahu','nakshatra_ruler']
    assert all(r['relation'] == 'context' for r in rows)


@pytest.mark.parametrize('profile', [{'ayanamsha':'lahiri','node_type':'mean'}, {'ayanamsha':'raman','node_type':'true'}])
def test_precise_calendar_uses_profile_and_has_only_bindu_contacts(profile):
    data = build_workspace({**BIRTH, 'calculation_profile':profile}, date(2026,10,18), date(2026,11,17), calendar=True, fast=True, aspects=True, orb=.5)
    assert data['events']
    assert data['audit']['ayanamsha'] == profile['ayanamsha']
    assert data['audit']['node_type'] == profile['node_type']
    point = data['natal']['points'][0]
    for event in data['events']:
        assert event['kind'] == 'natal_contact'
        assert event['point'] == 'Bhrigu Bindu'
        assert event['start_at'] < event['end_at']
        assert event['planet'] not in event['concurrent_transits']
        assert event['aspect_number'] == 1 or event['planet'] not in {'Rahu','Ketu'}
        assert _angular_distance(event['target_longitude'], (point['longitude']-(event['aspect_number']-1)*30)%360) < 1e-9
        for crossing in event['exact_passes']:
            longitude, speed = _strict_planet_state(datetime.fromisoformat(crossing['at']), event['planet'], ayanamsha=profile['ayanamsha'], node_type=profile['node_type'])
            longitude = (longitude - ChartCalculator.D1_CORRECTION) % 360
            assert _angular_distance(longitude, event['target_longitude']) < .001
        for overlap in event['dasha_overlaps']:
            assert event['start_at'] <= overlap['start_at'] < overlap['end_at'] <= event['end_at']
            assert overlap['connections']


def test_bindu_route_auth_validation_and_no_ephemeris_fallback(monkeypatch):
    from fastapi import FastAPI
    import httpx
    from charts.routes import router
    from auth import get_current_user
    from prediction_engine.errors import PredictionCalculationError
    app = FastAPI()
    app.include_router(router, prefix='/api')
    body = {'birth_data': BIRTH, 'start_date':'2026-10-18','end_date':'2026-11-17'}
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as client:
            assert (await client.post('/api/bhrigu-bindu-workspace', json=body)).status_code == 403
            app.dependency_overrides[get_current_user] = lambda: object()
            response = await client.post('/api/bhrigu-bindu-workspace', json=body)
            assert response.status_code == 200
            assert response.json()['schema_version'] == 'bhrigu-bindu-workspace-v1'
            focused = await client.post('/api/bhrigu-bindu-workspace', json={**body,'focus':'career','orb_degrees':5/3,'chart_at':'2026-10-21T13:39:57+05:30'})
            assert focused.status_code == 200
            assert focused.json()['consultation_focus']['key'] == 'career'
            assert focused.json()['selected_transit']['at'] == '2026-10-21T08:09:57+00:00'
            invalid = await client.post('/api/bhrigu-bindu-workspace', json={**body,'focus':'unknown'})
            assert invalid.status_code == 422

            assert (await client.post('/api/bhrigu-bindu-workspace', json={**body,'end_date':'2028-01-01'})).status_code == 422
            assert (await client.post('/api/bhrigu-bindu-workspace', json={**body,'orb_degrees':0})).status_code == 422
            def fail(*args, **kwargs):
                raise PredictionCalculationError('Missing ephemeris')
            monkeypatch.setattr('charts.mrityu_bhaga_service._strict_planet_state', fail)
            response = await client.post('/api/bhrigu-bindu-workspace', json={**body,'calendar':True})
            assert response.status_code == 503
            assert 'no fallback' in response.json()['detail']
    asyncio.run(exercise())


@pytest.mark.parametrize('longitude,speed,target,direction', [
    (359,1,0,'Approaching'),(1,1,0,'Moving away'),
    (1,-1,0,'Approaching'),(359,-1,0,'Moving away'),
    (0,1,0,'At exact contact'),(1,0,0,'Stationary'),
    (180,1,0,'Opposite the contact target'),
])
def test_contact_direction_handles_wrap_retrograde_and_station(longitude,speed,target,direction):
    from charts.bhrigu_bindu_service import contact_status
    row = contact_status(longitude,speed,target)
    assert row['direction'] == direction
    assert row['distance_degrees'] == min(abs(longitude-target),360-abs(longitude-target))


@pytest.mark.parametrize('profile', [{'ayanamsha':'lahiri','node_type':'mean'}, {'ayanamsha':'raman','node_type':'true'}])
def test_patels_preset_focus_and_exact_instant_transit_snapshot(profile):
    from datetime import timezone
    at = datetime(2026,10,21,8,9,57,tzinfo=timezone.utc)
    data = build_workspace({**BIRTH,'calculation_profile':profile},date(2026,10,18),date(2026,11,17),calendar=True,fast=True,focus='career',orb=5/3,chart_at=at,as_of=at)
    assert '100 arcminutes' in data['audit']['orb_preset']
    assert data['consultation_focus']['houses'] == [2,6,10,11]
    snapshot = data['selected_transit']
    assert datetime.fromisoformat(snapshot['at']) == at
    assert snapshot['chart']['ascendant'] == data['natal_chart']['ascendant']
    assert snapshot['chart']['houses'] == data['natal_chart']['houses']
    assert set(snapshot['chart']['planets']) == {'Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'}
    for name,row in snapshot['chart']['planets'].items():
        expected,_ = _strict_planet_state(at,name,ayanamsha=profile['ayanamsha'],node_type=profile['node_type'])
        assert _angular_distance(row['longitude'],(expected-ChartCalculator.D1_CORRECTION)%360) < 1e-9
    for event in data['events']:
        current = event['current_contact']
        assert current['as_of'] == at.isoformat()
        assert isinstance(event['focus_evidence'],list)
        assert current['distance_degrees'] == pytest.approx(_angular_distance(snapshot['chart']['planets'][event['planet']]['longitude'],event['target_longitude']))
        for overlap in event['focus_dasha_overlaps']:
            assert event['start_at'] <= overlap['start_at'] < overlap['end_at'] <= event['end_at']
            for connection in overlap['connections']:
                assert set(connection['houses']) <= {2,6,10,11}


def test_focus_explains_both_topics_without_hiding_contacts():
    a = build_workspace(BIRTH,date(2026,10,18),date(2026,11,17),calendar=True,fast=True,focus='career')
    b = build_workspace(BIRTH,date(2026,10,18),date(2026,11,17),calendar=True,fast=True,focus='marriage')
    assert [r['id'] for r in a['events']] == [r['id'] for r in b['events']]
    assert a['consultation_focus']['natal_evidence'] != b['consultation_focus']['natal_evidence']
    assert all('score' not in r for r in a['events'])


@pytest.mark.parametrize('extra', [{'focus':'bad'}, {'chart_at':'2026-10-20T00:00:00'}, {'chart_at':'2027-10-20T00:00:00Z'}])
def test_invalid_focus_or_snapshot_time_is_rejected(extra):
    with pytest.raises(ValueError):
        build_workspace(BIRTH,date(2026,10,18),date(2026,11,17),**extra)
