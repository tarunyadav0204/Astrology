import asyncio
import copy
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import httpx
from fastapi import FastAPI

from calculators.ashtakavarga import AshtakavargaCalculator
from charts.house_insight_service import build_house_insight
from next_chapter.evidence import build_foundation
from next_chapter.periods import select_next_antardasha
from next_chapter.preview import render_preview
from next_chapter.service import (
    attach_narration, build_next_chapter, narrate_next_chapter, narration_context,
)
from next_chapter.transits import contact_windows, reinforcement_windows, utc
from prediction_engine.transit_returns import _strict_planet_state
from shared.dasha_calculator import DashaCalculator
from zoneinfo import ZoneInfo

BIRTH = {'name': 'Test native', 'date': '1990-04-23', 'time': '06:15:00',
    'timezone': 'Asia/Kolkata', 'latitude': 13.0833333333, 'longitude': 80.2833333333,
    'place': 'Chennai'}
AS_OF = datetime(2026, 11, 8, tzinfo=timezone.utc)


@pytest.fixture(scope='module')
def dossier():
    return build_next_chapter(BIRTH, AS_OF)


def test_selects_upcoming_ad_and_all_pds_without_replacing_current_md(dossier):
    spine = dossier['spine']
    assert spine['current_mahadasha']['planet'] == spine['mahadasha']['planet'] == 'Venus'
    assert spine['current_antardasha']['planet'] == 'Venus'
    assert spine['antardasha']['planet'] == 'Sun'
    assert not spine['mahadasha_changes']
    pds = spine['pratyantardashas']
    assert len(pds) == 9
    assert pds[0]['start_at'] == spine['antardasha']['start_at']
    assert pds[-1]['end_at'] == spine['antardasha']['end_at']
    assert all(a['end_at'] == b['start_at'] for a, b in zip(pds, pds[1:]))
    assert len({pd['planet'] for pd in pds}) == 9


def test_last_ad_selects_first_ad_of_new_md_and_boundary_is_half_open(dossier):
    end = datetime.fromisoformat(dossier['spine']['mahadasha']['end_at'])
    spine = select_next_antardasha(BIRTH, end - timedelta(days=30))
    assert spine['current_antardasha']['planet'] == 'Ketu'
    assert spine['mahadasha_changes']
    assert spine['mahadasha']['planet'] == spine['antardasha']['planet'] == 'Sun'
    boundary = datetime.fromisoformat(spine['antardasha']['start_at'])
    at_boundary = select_next_antardasha(BIRTH, boundary)
    assert at_boundary['current_antardasha']['planet'] == 'Sun'
    assert at_boundary['antardasha']['planet'] == 'Moon'
    assert not at_boundary['mahadasha_changes']


def test_birth_balance_and_clocks_are_not_silently_faked():
    near_birth = select_next_antardasha(BIRTH, datetime(1990, 4, 24, tzinfo=timezone.utc))
    assert len(near_birth['pratyantardashas']) == 9
    with pytest.raises(ValueError, match='timezone'):
        select_next_antardasha(BIRTH, AS_OF.replace(tzinfo=None))
    with pytest.raises(ValueError, match='after birth'):
        select_next_antardasha(BIRTH, datetime(1980, 1, 1, tzinfo=timezone.utc))
    class FailedCalculator:
        def calculate_current_dashas(self, *_args, **kwargs):
            assert kwargs['strict'] is True
            raise RuntimeError('Unavailable ephemeris')
    with pytest.raises(RuntimeError, match='ephemeris'):
        select_next_antardasha(BIRTH, AS_OF, calculator=FailedCalculator())


def test_foundation_matches_house_drawer_and_uses_sign_to_house_mapping(dossier):
    foundation = dossier['foundation']
    chart = foundation['chart']
    av = AshtakavargaCalculator(BIRTH, chart).calculate_sarvashtakavarga()
    total = 0
    for number, row in foundation['houses'].items():
        house_index = int(number) - 1
        sign = chart['houses'][house_index]['sign']
        points = row['raw']['ashtakavarga']['sav']['house_points']
        assert points == av['sarvashtakavarga'][str(sign)]
        assert row['sav_givers']['total'] == points
        assert {r['planet'] for r in row['sav_givers']['givers']} <= set(av['individual_charts'])
        bav = row['raw']['ashtakavarga']['lord_bav']
        assert bav['house_points'] == av['individual_charts'][row['house_lord']]['bindus'][sign]
        total += points
        assert 'timing' not in row and 'activation_factors' not in row
    assert total == av['total_bindus'] == 337
    drawer = build_house_insight(BIRTH, 10, transit_date=dossier['spine']['antardasha']['start_at'][:10])
    for key in ('lord_worksheet', 'argala', 'related_varga'):
        assert foundation['houses']['10'][key] == drawer[key]
    for node in ('Rahu', 'Ketu'):
        assert foundation['planets'][node]['analysis']['strength_analysis']['shadbala_rupas'] is None


def test_leo_house_scores_are_not_misread_as_sign_numbers():
    birth = {**BIRTH, 'time': '14:15:00'}
    foundation = build_foundation(birth, '2026-11-08')
    chart = foundation['chart']
    assert chart['houses'][0]['sign'] == 4
    sav = AshtakavargaCalculator(birth, chart).calculate_sarvashtakavarga()
    for house, row in foundation['houses'].items():
        sign = (4 + int(house) - 1) % 12
        assert row['raw']['ashtakavarga']['sav']['house_points'] == sav['sarvashtakavarga'][str(sign)]


def test_next_chapter_uses_same_ephemeris_before_and_after_other_chart_calls():
    import swisseph as swe
    birth = {**BIRTH, 'date': '1980-04-02', 'time': '14:55:00',
             'latitude': 29.15, 'longitude': 75.72}
    swe.set_ephe_path('/nonexistent/ephemeris')
    first = select_next_antardasha(birth, AS_OF)
    build_foundation(birth, '2026-11-08')
    second = select_next_antardasha(birth, AS_OF)
    assert first == second


def test_full_venus_ad_is_not_truncated_to_one_year():
    spine = select_next_antardasha(BIRTH, datetime(2025, 10, 1, tzinfo=timezone.utc))
    assert spine['mahadasha_changes']
    assert spine['antardasha']['planet'] == 'Venus'
    assert (utc(spine['antardasha']['end_at']) - utc(spine['antardasha']['start_at'])).days > 1200
    assert spine['pratyantardashas'][-1]['end_at'] == spine['antardasha']['end_at']


def test_last_hours_before_md_change_are_not_an_uncovered_gap():
    select_next_antardasha(BIRTH, AS_OF)  # Initialize the chart's data-file ephemeris.
    calculator = DashaCalculator()
    mahas = calculator.calculate_current_dashas(BIRTH, datetime(2026, 11, 8), strict=True)['maha_dashas']
    moon = next(row for row in mahas if row['planet'] == 'Moon')
    instant = (moon['end'] - timedelta(minutes=1)).replace(tzinfo=ZoneInfo('Asia/Kolkata'))
    spine = select_next_antardasha(BIRTH, instant)
    assert spine['current_mahadasha']['planet'] == 'Moon'
    assert spine['current_antardasha']['planet'] == 'Sun'
    assert spine['current_antardasha']['parent_boundary_adjustment_seconds'] == 43200
    assert spine['mahadasha']['planet'] == spine['antardasha']['planet'] == 'Mars'
    assert spine['current_antardasha']['end_at'] == spine['antardasha']['start_at']


def test_house_combination_alternatives_are_kept_and_pd_emphasis_changes(dossier):
    assert len({tuple(pd['activation']['pd_focus_houses']) for pd in dossier['periods']}) > 1
    for pd in dossier['periods']:
        a = pd['activation']
        assert a['levels']['PD'] == pd['planet']
        assert a['relationships']
        assert any(not link['direct'] for link in a['house_links'])
        for combination in a['house_combinations']:
            assert set(combination['houses']) <= set(a['direct_houses'])
            assert len(combination['possibilities']) >= 2
    assert 'event_probabilities' not in dossier


def test_narration_exposes_natal_facts_and_lossless_slow_house_changes(dossier):
    context = narration_context(dossier)
    for name, summary in context['natal_summary']['planets'].items():
        assert summary['house'] == dossier['foundation']['planets'][name]['house']
        assert name not in {c['planet'] for c in summary['same_sign_companions']}
    for pd, source in zip(context['periods'], dossier['periods']):
        for planet in ('Jupiter', 'Saturn', 'Rahu', 'Ketu'):
            merged = [s for s in pd['background_house_transits'] if s['transiting_planet'] == planet]
            assert utc(merged[0]['start_at']) == utc(pd['start_at'])
            assert utc(merged[-1]['end_at']) == utc(pd['end_at'])
            assert dt_offset(merged[0]['start_at']) == dt_offset(pd['start_at'])
            assert all(a['end_at'] == b['start_at'] and a['sign_number'] != b['sign_number']
                       for a, b in zip(merged, merged[1:]))
            for row in source['transits']['house_occupancy']:
                if row['transiting_planet'] == planet:
                    containing = [s for s in merged if utc(s['start_at']) <= utc(row['start_at'])
                                  and utc(s['end_at']) >= utc(row['end_at'])]
                    assert len(containing) == 1
                    assert containing[0]['natal_house'] == row['natal_house']
                    assert containing[0]['aspected_natal_houses'] == row['aspected_natal_houses']


def dt_offset(value):
    return datetime.fromisoformat(value).utcoffset()


def test_narration_contact_dates_are_local_without_changing_instants(dossier):
    context = narration_context(dossier)
    for source, supplied in zip(dossier['periods'], context['periods']):
        for original, localized in zip(source['transits']['contacts'], supplied['transits']['contacts']):
            assert utc(original['start_at']) == utc(localized['start_at'])
            assert dt_offset(localized['start_at']) == timedelta(hours=5, minutes=30)
            if original['aspect_from_planet'] != 1:
                assert 'directed aspect' in localized['reading_label']
                assert 'conjunction' not in localized['reading_label']
            for a, b in zip(original['exact_passes'], localized['exact_passes']):
                assert utc(a['at']) == utc(b['at'])
                assert dt_offset(b['at']) == timedelta(hours=5, minutes=30)


def test_planet_drawer_aspects_match_chart_convention_and_exclude_outer_planets():
    from calculators.planet_analyzer import PlanetAnalyzer
    from calculators.vedic_graha_drishti import GRAHA_HOUSE_ASPECTS
    analyzer = PlanetAnalyzer.__new__(PlanetAnalyzer)
    for planet, aspects in GRAHA_HOUSE_ASPECTS.items():
        for house in range(1, 13):
            assert analyzer._get_aspect_houses(planet, house) == [
                (house + number - 2) % 12 + 1 for number in aspects if number != 1]
    assert analyzer._get_aspect_houses('Rahu', 2) == [6, 8, 10]
    assert 4 not in analyzer._get_aspect_houses('Rahu', 2)
    for planet in ('Uranus', 'Neptune', 'Pluto'):
        assert analyzer._get_aspect_houses(planet, 5) == []


def test_exact_crossing_handles_zodiac_wrap_and_clips_orb_to_period():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    def state(at, _planet):
        days = (at - start).total_seconds() / 86400
        return (358 + days) % 360, 1.0
    windows = contact_windows('Sun', 0, start, start + timedelta(days=4), state)
    window, = windows
    assert utc(window['start_at']) == start + timedelta(days=1)
    assert utc(window['end_at']) == start + timedelta(days=3)
    assert utc(window['exact_passes'][0]['at']) == start + timedelta(days=2)
    assert not window['clipped_start'] and not window['clipped_end']
    clipped, = contact_windows('Sun', 0, start + timedelta(days=1.5), start + timedelta(days=2.5), state)
    assert clipped['clipped_start'] and clipped['clipped_end']


def test_station_splits_two_hidden_degree_crossings_and_near_miss_is_not_exact():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    def station(at, _planet):
        hours = (at - start).total_seconds() / 3600
        return 100.1 - (hours - 3) ** 2 / 10, -4.8 * (hours - 3)
    windows = contact_windows('Mercury', 100, start, start + timedelta(hours=6), station, orb=0.02)
    passes = [p for window in windows for p in window['exact_passes']]
    assert [p['motion'] for p in passes] == ['direct', 'retrograde']
    assert len(windows) == 2
    def near_miss(at, planet):
        longitude, speed = station(at, planet)
        return longitude - 0.6, speed
    near = contact_windows('Mercury', 100, start, start + timedelta(hours=6), near_miss)
    assert near and not any(row['exact_passes'] for row in near)


def test_same_transit_planet_is_not_counted_as_multiple_reinforcements():
    contacts = [{'id': str(n), 'start_at': '2026-01-01T00:00:00+00:00',
        'end_at': '2026-01-03T00:00:00+00:00', 'transiting_planet': 'Sun'} for n in range(2)]
    assert reinforcement_windows(contacts) == []
    contacts.append({**contacts[0], 'id': '2', 'transiting_planet': 'Jupiter'})
    assert reinforcement_windows(contacts)[0]['transiting_planets'] == ['Jupiter', 'Sun']


def test_real_contacts_are_inside_pd_and_exact_to_ephemeris(dossier):
    count = 0
    for pd in dossier['periods']:
        for contact in pd['transits']['contacts']:
            assert utc(pd['start_at']) <= utc(contact['start_at']) < utc(contact['end_at']) <= utc(pd['end_at'])
            target = (contact['natal_longitude'] - (contact['aspect_from_planet'] - 1) * 30) % 360
            for exact in contact['exact_passes']:
                lon, _ = _strict_planet_state(utc(exact['at']), contact['transiting_planet'])
                assert abs((lon - target + 180) % 360 - 180) < 0.0003
                count += 1
    assert count > 0
    assert any(c['is_sun_trigger'] for pd in dossier['periods'] for c in pd['transits']['contacts'])
    assert all(pd['transits']['house_occupancy'] for pd in dossier['periods'])


def narrative_for(dossier):
    from next_chapter.briefs import build_briefs
    b = build_briefs(dossier)
    return {'title': 'Chapter', 'overview': 'Overview', 'mahadasha_context': 'Background',
        'antardasha_themes': 'Themes', 'closing': 'Closing',
        'antardasha_events': [{'theme': 'AD event', 'circumstances': 'If relevant', 'possibilities': ['An agreement may be signed'], 'why': 'Natal support', 'timing': 'During the AD', 'evidence_refs': ['house_2']}],
        'antardasha_transits': [{'evidence_refs': b['shared']['antardasha_packet']['transit_refs'], 'explanation': 'The AD lord changes houses'}],
        'periods': [
            {'period_id': pd['id'], 'summary': 'Period summary', 'what_changes': 'Different focus',
             'timing_explanation': 'Broad timing', 'conditions_and_cautions': 'Mixed conditions',
             'transit_story': [{'evidence_refs': next(p['period_lord_transit_refs'] for p in b['periods'] if p['period']['id'] == pd['id']), 'explanation': 'AD transit and natal axis'}],
             'manifestations': [{'theme': 'Theme', 'possibilities': ['One possibility', 'Another possibility'],
                'why': 'Natal condition', 'house_refs': [f"house_{pd['activation']['direct_houses'][0]}"],
                'planet_refs': [f"planet_{pd['planet']}"], 'contact_refs': [], 'practical_guidance': 'Guidance'}]}
            for pd in dossier['periods']]}


def test_narration_keeps_all_pds_attaches_dates_and_rejects_invented_references(dossier):
    narrative = narrative_for(dossier)
    report = attach_narration(dossier, narrative)
    assert len(report['periods']) == 9
    assert report['periods'][0]['start_at'] == dossier['periods'][0]['start_at']
    assert report['periods'][0]['manifestations'][0]['timing_basis'] == 'pratyantardasha'
    bad = copy.deepcopy(narrative)
    bad['periods'][0]['manifestations'][0]['contact_refs'] = ['invented']
    with pytest.raises(ValueError, match='contact_refs'):
        attach_narration(dossier, bad)
    bad['periods'] = bad['periods'][:8]
    with pytest.raises(ValueError, match='nine PDs'):
        attach_narration(dossier, bad)


def test_misnested_closing_is_relocated_without_inventing_or_dropping_content(dossier):
    narrative = narrative_for(dossier)
    narrative['periods'].append({'closing': narrative.pop('closing')})
    original = copy.deepcopy(narrative)
    report = attach_narration(dossier, narrative)
    assert report['closing'] == 'Closing' and len(report['periods']) == 9
    assert narrative == original
    narrative['periods'][-1]['period_id'] = 'pd_10'
    with pytest.raises(ValueError, match='closing'):
        attach_narration(dossier, narrative)


def test_html_preview_escapes_model_and_native_text(dossier):
    dirty = {**dossier, 'native': {**dossier['native'], 'name': '<script>bad()</script>'}}
    page = render_preview(dirty)
    assert '<script>' not in page and '&lt;script&gt;' in page
    assert page.count('Pratyantardasha</h2>') == 9


@pytest.mark.asyncio
async def test_admin_preview_requires_ownership_and_never_calls_model_by_default(monkeypatch, dossier):
    import next_chapter.routes as routes
    import prediction_engine.routes as prediction_routes
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(role='user', userid=7)
    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test')
    assert (await client.post('/next-chapter/preview', json={'birth_chart_id': 1})).status_code == 403
    app.dependency_overrides[routes.get_current_user] = lambda: SimpleNamespace(role='admin', userid=7)
    seen = []
    def owned(chart_id, user_id):
        seen.append((chart_id, user_id))
        return BIRTH
    monkeypatch.setattr(prediction_routes, '_load_owned_birth_chart', owned)
    monkeypatch.setattr(routes, 'build_next_chapter', lambda *_a, **_kw: dossier)
    async def unexpected(*_args):
        raise AssertionError('Default preview must not spend provider credits')
    monkeypatch.setattr(routes, 'narrate_next_chapter', unexpected)
    result = await client.post('/next-chapter/preview', json={'birth_chart_id': 4, 'as_of': AS_OF.isoformat()})
    assert result.status_code == 200
    assert result.json()['narration'] is None
    assert seen == [(4, 7)]
    assert (await client.post('/next-chapter/preview', json={'birth_chart_id': 4, 'as_of': '2026-11-08T00:00:00'})).status_code == 422
    await client.aclose()


def test_next_chapter_nodes_use_only_opposition_in_all_calculated_layers(dossier):
    from next_chapter.evidence import aspect_houses
    from calculators.planet_analyzer import PlanetAnalyzer
    from calculators.aspect_calculator import AspectCalculator
    assert aspect_houses('Rahu', 2) == [8]
    assert aspect_houses('Ketu', 8) == [2]
    default = PlanetAnalyzer.__new__(PlanetAnalyzer)
    assert default._get_aspect_houses('Rahu', 2) == [6, 8, 10]
    default.node_aspects = (7,)
    assert default._get_aspect_houses('Rahu', 2) == [8]
    chart = dossier['foundation']['chart']
    aspects = AspectCalculator(chart, node_aspects=(7,))
    for name in ('Rahu', 'Ketu'):
        origin = chart['planets'][name]['house']
        opposite = (origin + 5) % 12 + 1
        for h in range(1, 13):
            assert (name in aspects.get_aspecting_planets(h)) == (h == opposite)
        for planet in dossier['foundation']['planets'].values():
            received = planet['analysis']['aspects_received']['aspects']
            assert (name in [a['aspecting_planet'] for a in received]) == (planet['house'] == opposite)
    for pd in dossier['periods']:
        for c in pd['transits']['contacts']:
            if c['transiting_planet'] in {'Rahu', 'Ketu'}:
                assert c['aspect_from_planet'] in (1, 7)
        for s in pd['transits']['house_occupancy']:
            if s['transiting_planet'] in {'Rahu', 'Ketu'}:
                assert s['aspected_natal_houses'] == [(s['natal_house'] + 5) % 12 + 1]
        for link in pd['activation']['house_links']:
            if link['planet'] in {'Rahu', 'Ketu'} and link['relation'] == 'aspect':
                assert link['house'] == (chart['planets'][link['planet']]['house'] + 5) % 12 + 1
