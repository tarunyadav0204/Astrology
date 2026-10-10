"""Astronomical regression fixtures and legacy mundane integration contracts."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest
import swisseph as swe
from calculators.mundane.astronomy import chart_at, julian, position, _SWISSEPH_CHART_LOCK
from calculators.mundane.ingress_calculator import IngressCalculator
from calculators.mundane.lunation_calculator import LunationCalculator
from calculators.mundane.outer_planet_calculator import OuterPlanetCalculator
from calculators.mundane.nav_nayak_calculator import NavNayakCalculator
from calculators.mundane.geodetic_calculator import GeodeticCalculator
from calculators.mundane.mundane_yoga_calculator import MundaneYogaCalculator
from calculators.mundane.sports_scorecard import SportsMundaneScorecard
from calculators.mundane.mundane_context_builder import MundaneContextBuilder

# USNO published Universal Time, rounded to nearest minute:
# https://aa.usno.navy.mil/calculated/moon/phases?year=2026
USNO_2026 = [
 ('Full Moon','01-03T10:03'), ('New Moon','01-18T19:52'), ('Full Moon','02-01T22:09'),
 ('New Moon','02-17T12:01'), ('Full Moon','03-03T11:38'), ('New Moon','03-19T01:23'),
 ('Full Moon','04-02T02:12'), ('New Moon','04-17T11:52'), ('Full Moon','05-01T17:23'),
 ('New Moon','05-16T20:01'), ('Full Moon','05-31T08:45'), ('New Moon','06-15T02:54'),
 ('Full Moon','06-29T23:56'), ('New Moon','07-14T09:43'), ('Full Moon','07-29T14:36'),
 ('New Moon','08-12T17:37'), ('Full Moon','08-28T04:18'), ('New Moon','09-11T03:27'),
 ('Full Moon','09-26T16:49'), ('New Moon','10-10T15:50'), ('Full Moon','10-26T04:12'),
 ('New Moon','11-09T07:02'), ('Full Moon','11-24T14:53'), ('New Moon','12-09T00:52'),
 ('Full Moon','12-24T01:28')]

@pytest.fixture(scope='module')
def lunations():
    return LunationCalculator().calculate_lunations(datetime(2026,1,1),datetime(2027,1,1),28.6,77.2)


def test_all_phases_agree_with_independent_usno_times(lunations):
    assert len(lunations) == len(USNO_2026)
    for actual, (kind, stamp) in zip(lunations, USNO_2026):
        assert actual['type'] == kind
        assert abs((datetime.fromisoformat(actual['datetime']) - datetime.fromisoformat('2026-'+stamp)).total_seconds()) < 60
        assert {'chart','paksha','nakshatra','valid_until','sun_longitude','moon_longitude'} <= actual.keys()


def test_near_phase_not_skipped_and_half_open_boundary(lunations):
    first = datetime.fromisoformat(lunations[0]['datetime'])
    calculator = LunationCalculator()
    rows = calculator.calculate_lunations(first-timedelta(minutes=15),first+timedelta(minutes=15),0,0)
    assert len(rows)==1 and rows[0]['type']=='Full Moon'
    # Use a bound clearly before the root; no outside-horizon result.
    assert not calculator.calculate_lunations(first-timedelta(minutes=15),first-timedelta(seconds=1),0,0)
    assert calculator.calculate_lunations(first,first,0,0)==[]


def test_valid_until_is_actual_next_syzygy(lunations):
    for index, row in enumerate(lunations[:-1]):
        assert row['valid_until']==lunations[index+1]['datetime']
    assert datetime.fromisoformat(lunations[-1]['valid_until']).year==2027


@pytest.mark.parametrize('latitude', [0,28.6,70])
def test_chart_uses_sidereal_ascendant_and_whole_sign(latitude):
    dt=datetime(2026,4,14,4,2,40)
    result=chart_at(dt,latitude,77.2)
    jd=julian(dt)
    with _SWISSEPH_CHART_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        tropical=swe.houses_ex(jd,latitude,77.2,b'W')[1][0]
        ayanamsa=swe.get_ayanamsa_ex_ut(jd,swe.FLG_SWIEPH)[1]
    assert abs(((result['ascendant']-(tropical-ayanamsa)+180)%360)-180)<1e-5
    for row in result['planets'].values():
        assert row['house']==(row['sign']-int(result['ascendant']/30))%12+1


def test_aware_times_and_seconds_represent_same_instant():
    local=datetime(2026,1,1,0,15,42,123456,tzinfo=ZoneInfo('Asia/Kolkata'))
    assert julian(local)==julian(local.astimezone(timezone.utc))
    assert 41.99 < (julian(local)-julian(local.replace(second=0)))*86400 < 42.01


def test_ingresses_occur_in_requested_year_and_cross_target():
    result=IngressCalculator().calculate_yearly_ingresses(2026,28.6,77.2)
    assert datetime.fromisoformat(result['ingresses']['Capricorn']['datetime']).month==1
    for name, target in [('Aries',0),('Cancer',90),('Libra',180),('Capricorn',270)]:
        row=result['ingresses'][name]
        dt=datetime.fromisoformat(row['datetime'])
        assert dt.year==2026
        before=position(julian(dt-timedelta(seconds=1)),swe.SUN)[0]
        after=position(julian(dt+timedelta(seconds=1)),swe.SUN)[0]
        assert (before-target+180)%360-180<0
        assert (after-target+180)%360-180>0
        assert {'datetime','sun_longitude','sign'} <= row.keys()


@pytest.mark.parametrize('body,name', [(swe.URANUS,'Uranus'),(swe.NEPTUNE,'Neptune'),(swe.PLUTO,'Pluto')])
def test_outer_speed_matches_finite_difference(body,name):
    dt=datetime(2026,10,10)
    row=OuterPlanetCalculator().calculate_outer_planets(dt,0,0)[name]
    # Independent tropical longitude motion has effectively the same sign.
    jd=julian(dt)
    before=swe.calc_ut(jd-.05,body,swe.FLG_SWIEPH)[0][0]
    after=swe.calc_ut(jd+.05,body,swe.FLG_SWIEPH)[0][0]
    rate=((after-before+180)%360-180)/.1
    assert row['speed']!=0 and row['is_retrograde']==(rate<0)
    assert abs(rate-row['speed']) < .001


def test_sidereal_profile_not_inherited_from_external_caller():
    swe.set_sid_mode(swe.SIDM_RAMAN)
    first=chart_at(datetime(2026,1,1),28.6,77.2)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    second=chart_at(datetime(2026,1,1),28.6,77.2)
    assert first==second


def test_eclipse_identity_and_visibility(lunations):
    eclipses=[row for row in lunations if row.get('eclipse_visibility',{}).get('is_eclipse')]
    assert [(row['type'], row['datetime'][:10]) for row in eclipses]==[
        ('New Moon','2026-02-17'),('Full Moon','2026-03-03'),('New Moon','2026-08-12'),('Full Moon','2026-08-28')]
    # August 28 lunar eclipse is below Delhi's horizon, despite global magnitude.
    august=next(row for row in eclipses if row['datetime'][:10]=='2026-08-28')
    assert august['eclipse_visibility']['visible_from_location'] is False


def test_annual_lords_do_not_fabricate_king_or_rotation():
    calc=NavNayakCalculator()
    assert calc.calculate_nav_nayak(datetime(2026,4,14))['mantri'] is None
    result=calc.calculate_nav_nayak(datetime(2026,4,14,4),latitude=28.6,longitude=77.2)
    assert result['mantri']=='Mars' and result['raja'] is None
    assert len(result['nav_nayak'])==10
    assert all(row['lord'] is None for key,row in result['nav_nayak'].items() if key!='mantri')


@pytest.mark.parametrize('name,direction', [('Krittika','Central'),('Rohini','Central'),('Mrigashira','Central'),
 ('Ardra','East'),('Pushya','East'),('Revati','Northeast'),('Bharani','Northeast')])
def test_classical_kurma_triplet_directions(name,direction):
    row=GeodeticCalculator().get_affected_regions(name)
    assert row['direction']==direction
    assert row['regional_mapping_basis'].startswith('modern_editorial')


def test_yoga_candidates_exclude_luminaries_nodes_and_include_all_five_pairs():
    calc=MundaneYogaCalculator()
    chart={'planets':{name:{'longitude':10} for name in ['Sun','Moon','Rahu','Ketu','Mars','Mercury','Jupiter','Venus','Saturn']}}
    rows=calc._check_graha_yuddha(chart)
    assert len(rows)==10
    assert all(set(row['planets']) <= {'Mars','Mercury','Jupiter','Venus','Saturn'} for row in rows)
    assert all(row['winner'] is None for row in rows)


def test_yoga_angles_wrap_and_missing_longitudes_not_zero():
    calc=MundaneYogaCalculator()
    assert calc._check_inflation_yoga({'planets':{'Venus':{'longitude':359},'Rahu':{'longitude':1}}})
    assert calc._check_revolution_yoga({'planets':{'Uranus':{'longitude':350},'Pluto':{'longitude':80}}})
    assert not calc._check_graha_yuddha({'planets':{'Mars':{'house':1},'Mercury':{'house':1}}})
    assert not calc._check_war_yoga({'planets':{'Mars':{'house':1},'Saturn':{'house':1}}})


def test_string_and_object_nakshatras_and_no_fake_vedha():
    calc=MundaneYogaCalculator()
    first=calc.analyze_chart({'planets':{'Mars':{'longitude':40,'nakshatra':'Rohini'}}})
    second=calc.analyze_chart({'planets':{'Mars':{'longitude':40,'nakshatra':{'name':'Rohini'}}}})
    assert first==second
    assert all(row['impact_type']=='direct' for row in first['commodity_impacts'])
    geo=GeodeticCalculator()
    assert geo.analyze_planetary_impact({'name':'Mars','nakshatra':'Rohini'})['direction']=='Central'


def test_national_record_missing_time_not_default_midnight(monkeypatch):
    from calculators.mundane import nation_chart_service as service
    monkeypatch.setattr(service,'get_nation_foundation',lambda name: {'date':'2000-01-01','lat':0,'lon':0,'timezone':0})
    with pytest.raises(ValueError,match='missing time'):
        service.get_nation_birth_dict_for_dasha('Example')


def test_sports_tie_no_first_team_bias_and_hora_has_full_inputs():
    card=SportsMundaneScorecard()
    chart=chart_at(datetime(2026,1,1,18),0,0)
    # Equal, empty national data and controlled equal strengths.
    card._score_side=lambda **kwargs: __import__('calculators.mundane.sports_scorecard',fromlist=['SideResult']).SideResult(kwargs['entity'],kwargs['side_house'], 'Mars',5,[])
    result=card.build(entities=['A','B'],event_chart=chart,event_panchang=None,entity_charts={},locational_analysis={},latitude=0,longitude=0,event_date='2026-01-01',event_time='18:00',timezone_offset=0)
    assert result['available'] and result['edge']['predicted_winner'] is None
    assert result['edge']['result_type']=='balanced'
    assert result['edge']['confidence_percent']==50
    assert result['calibration']=='unvalidated_heuristic_not_probability'
    assert card._day_lord_from_panchang(None)==''
    assert card._is_friend('Mercury','Moon') is False
    assert card._is_friend('Moon','Mercury') is True


def test_context_rollover_capital_coordinates_and_exact_sports_sides():
    result=MundaneContextBuilder().build_mundane_context('India',2026,28.6139,77.209,category='sports',event_date='2026-01-01',event_time='00:15:42',entities=['USA','India'])
    assert result['event_datetime_utc']=='2025-12-31T18:45:42Z'
    assert result['locational_analysis']['USA']['coordinates']=={'lat':38.9072,'lon':-77.0369}
    assert result['locational_analysis']['USA']['datetime_utc']==result['event_datetime_utc']
    assert [row['entity'] for row in result['sports_scorecard']['sides']]==['USA','India']
    assert result['entity_charts']['India']['foundation']['reliability']=='unverified_foundation_record'
    assert result['outer_planets_datetime_utc']==result['event_datetime_utc']


@pytest.mark.parametrize('stamp,time,expected', [('2026-01-15','12:00:00',-5),('2026-07-15','12:00:00',-4)])
def test_event_offset_uses_event_date_dst(stamp,time,expected):
    result=MundaneContextBuilder().build_mundane_context('USA',2026,38.9072,-77.0369,event_date=stamp,event_time=time)
    assert result['event_location']['timezone_offset']==expected


def test_nonexistent_dst_time_is_missing_evidence_not_wrong_chart():
    result=MundaneContextBuilder().build_mundane_context('USA',2026,38.9072,-77.0369,event_date='2026-03-08',event_time='02:30:00')
    assert 'event_chart' not in result
    assert result['event_chart_status']['available'] is False


def test_legacy_prompt_receives_corrected_calculation_contract():
    from ai.output_schema import build_final_prompt
    result=MundaneContextBuilder().build_mundane_context('India',2026,28.6,77.2,event_date='2026-01-01',event_time='12:00:00')
    result['analysis_type']='mundane'
    prompt=build_final_prompt('Assess this event',result,[],'english','detailed',{},False)
    assert 'legacy heuristic index' in prompt
    assert 'Aries ingress supplies only the Minister' in prompt
    assert 'No ambiguity' not in prompt and 'No "maybes"' not in prompt


def test_host_country_does_not_replace_competing_sides():
    result=MundaneContextBuilder().build_mundane_context('India',2026,28.6,77.2,category='sports',event_date='2026-01-01',event_time='12:00',entities=['USA','Canada'])
    assert result['entities_involved'][0]=='India'
    assert [row['entity'] for row in result['sports_scorecard']['sides']]==['USA','Canada']


def test_missing_match_time_does_not_score_assumed_noon():
    result=MundaneContextBuilder().build_mundane_context('India',2026,28.6,77.2,category='sports',event_date='2026-01-01',entities=['India','USA'])
    assert result['event_time_assumed'] is True
    assert result['sports_scorecard']['available'] is False


def test_shared_chart_preserves_seconds_and_legacy_fields():
    from calculators.chart_calculator import ChartCalculator
    from types import SimpleNamespace
    chart=ChartCalculator({}).calculate_chart(SimpleNamespace(date='2026-01-01',time='12:00:42',latitude=28.6,longitude=77.2,timezone=0))
    jd=julian(datetime(2026,1,1,12,0,42))
    expected=(position(jd,swe.MOON)[0]-ChartCalculator.D1_CORRECTION)%360
    assert abs(chart['planets']['Moon']['longitude']-expected)<1e-7
    assert {'planets','houses','ascendant','ayanamsa'} <= chart.keys()


def test_shared_dasha_birth_moon_evaluates_seconds(monkeypatch):
    from shared.dasha_calculator import DashaCalculator
    calls=[]
    real=swe.calc_ut
    def capture(jd,body,*args):
        if body==swe.MOON: calls.append(jd)
        return real(jd,body,*args)
    monkeypatch.setattr(swe,'calc_ut',capture)
    result=DashaCalculator().calculate_current_dashas({'date':'2000-01-01','time':'12:00:42','latitude':0,'longitude':0,'timezone':0},datetime(2026,1,1),strict=True)
    assert any(abs(jd-julian(datetime(2000,1,1,12,0,42)))<1e-8 for jd in calls)
    assert {'mahadasha','antardasha','maha_dashas'} <= result.keys()
