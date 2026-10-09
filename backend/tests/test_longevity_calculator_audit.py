"""Formula, boundary and missing-input checks; never fitted to death outcomes."""
from datetime import datetime, timedelta, timezone
import math
import pytest
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.shoola_dasha_calculator import ShoolaDashaCalculator
from calculators.yogini_dasha_calculator import YoginiDashaCalculator
from calculators.sniper_points_calculator import SniperPointsCalculator
from calculators.dasha_time import parse_birth_datetime
from calculators.chara_dasha_calculator import CharaDashaCalculator


def chart(asc=35, moon=76):
    names = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    planets = {name: {'longitude': (i * 37 + 2) % 360, 'sign': int((i * 37 + 2) % 360 / 30), 'house': 1, 'degree': 2} for i, name in enumerate(names)}
    planets['Moon'].update(longitude=moon, sign=int(moon / 30))
    return {'ascendant': asc, 'planets': planets}


def test_shoola_even_start_is_forward_and_has_contiguous_ads():
    calc = ShoolaDashaCalculator(chart())
    calc._determine_stronger_sign = lambda a, b: a
    birth = {'date': '2000-01-01', 'time': '13:14:15', 'timezone': '5.5'}
    result = calc.calculate_shoola_dasha(birth, focus_date=datetime(2002, 1, 1))
    assert [p['sign_id'] for p in result['all_periods'][:3]] == [1, 2, 3]
    assert result['direction'] == 'Forward'
    assert result['method'] == 'standard_shoola_9_years_forward'
    assert datetime.fromisoformat(result['all_periods'][0]['start_iso']) == parse_birth_datetime(birth)
    md = result['all_periods'][0]
    ads = md['antardashas']
    assert len(ads) == 12
    assert ads[0]['start_iso'] == md['start_iso']
    assert ads[-1]['end_iso'] == md['end_iso']
    assert all(a['end_iso'] == b['start_iso'] for a, b in zip(ads, ads[1:]))
    boundary = datetime.fromisoformat(md['end_iso'])
    assert calc.calculate_shoola_dasha(birth, focus_date=boundary)['current_period']['order'] == 2


@pytest.mark.parametrize('invalid', ['bad', '2000-02-30', ''])
def test_invalid_birth_is_not_substituted_with_today(invalid):
    with pytest.raises(ValueError):
        YoginiDashaCalculator().get_full_timeline({'date': invalid}, 20)


def test_yogini_both_balance_and_regular_md_boundaries_select_next_period():
    calc = YoginiDashaCalculator()
    birth = {'date': '2000-01-01', 'time': '12:34:56', 'timezone': '5.5'}
    origin = parse_birth_datetime(birth)
    balance = calc._calculate_birth_dasha_balance(6, origin)
    first = calc.calculate_current_yogini(birth, 6, balance['end_date'])
    idx = (calc._get_index_by_name(balance['name']) + 1) % 8
    assert first['mahadasha']['name'] == calc.YOGINIS[idx]['name']
    second_end = balance['end_date'] + timedelta(days=calc.YOGINIS[idx]['years'] * calc.year_length)
    assert calc.calculate_current_yogini(birth, 6, second_end)['mahadasha']['name'] == calc.YOGINIS[(idx + 1) % 8]['name']
    absolute = balance['end_date'].astimezone(timezone.utc)
    assert calc.calculate_current_yogini(birth, 6, absolute) == first


def test_yogini_birth_balance_ads_are_clipped_from_full_md_origin():
    calc = YoginiDashaCalculator()
    birth = {'date': '2000-01-01', 'time': '12:00:00', 'timezone': 'UTC'}
    start = parse_birth_datetime(birth)
    balance = calc._calculate_birth_dasha_balance(6, start)
    result = calc.get_periods_in_range(birth, 6, start, balance['end_date'])
    row = result['periods'][0]
    assert row['antardashas'][0]['start_iso'] == start.isoformat()
    assert row['antardashas'][-1]['end_iso'] == balance['end_date'].isoformat()
    # At birth the active AD is determined by elapsed MD, not restarted at birth.
    active = calc.calculate_current_yogini(birth, 6, start)
    assert row['antardashas'][0]['name'] == active['antardasha']['name']


@pytest.mark.parametrize('longitude,expected', [(70, 6), (229, 1), (0, 0), (30, 8), (60, 4)])
def test_d8_named_modality_formula(longitude, expected):
    # PVR 6.2.8 example 15 contains a typo in its final Mercury sentence;
    # its stated formula and worked count both yield Libra for Gemini 10 degrees.
    result = DivisionalChartCalculator(chart(moon=longitude)).calculate_divisional_chart(8)
    assert result['divisional_chart']['planets']['Moon']['sign'] == expected
    assert result['method'].startswith('pvr_ashtamsa')


@pytest.mark.parametrize('division,longitude,expected', [(5, 6, 10), (5, 36, 5), (6, 71, 2), (6, 229, 9), (11, 71, 2), (11, 229, 11)])
def test_other_previously_generic_divisions_have_explicit_rules(division, longitude, expected):
    result = DivisionalChartCalculator(chart(moon=longitude)).calculate_divisional_chart(division)
    assert result['divisional_chart']['planets']['Moon']['sign'] == expected


@pytest.mark.parametrize('longitude,expected_sign,expected_degree', [(2.5,0,15), (6,10,6), (14,8,15), (33.0,1,18), (38.5,5,15)])
def test_d30_unequal_parts_scale_with_their_own_width(longitude, expected_sign, expected_degree):
    result = DivisionalChartCalculator(chart(moon=longitude)).calculate_divisional_chart(30)['divisional_chart']['planets']['Moon']
    assert result['sign'] == expected_sign
    assert result['degree'] == pytest.approx(expected_degree)


def test_unsupported_division_fails_instead_of_generic_fallback():
    with pytest.raises(ValueError):
        DivisionalChartCalculator(chart()).calculate_divisional_chart(13)


@pytest.mark.parametrize('division', [3, 8, 9, 30, 60])
def test_near_boundary_never_rolls_into_a_different_sign(division):
    value = math.nextafter(30, 0)
    result = DivisionalChartCalculator(chart(asc=value, moon=value)).calculate_divisional_chart(division)['divisional_chart']
    assert int(result['ascendant'] / 30) == result['houses'][0]['sign']
    assert 0 <= result['planets']['Moon']['degree'] < 30


def test_sensitive_points_keep_d1_transit_sector_separate_from_varga_sign():
    d1 = chart(asc=15, moon=15)
    calc = DivisionalChartCalculator(d1)
    points = SniperPointsCalculator(d1, calc.calculate_divisional_chart(3), calc.calculate_divisional_chart(9))
    kharesh = points.calculate_kharesh_point()
    navamsa = points.calculate_64th_navamsa()
    assert kharesh['danger_sign'] == 'Pisces'
    assert kharesh['d1_sector']['start_longitude'] == 220
    assert navamsa['d1_sector']['start_longitude'] == pytest.approx(223 + 1 / 3)
    assert kharesh['coordinate_frame'] == 'D3_mapped_sign'
    assert navamsa['coordinate_frame'] == 'D9_mapped_sign'
    assert points.calculate_lagna_64th_navamsa()['reference'] == 'Lagna'


def test_missing_placements_are_unavailable_instead_of_aries():
    points = SniperPointsCalculator({'ascendant': 15, 'planets': {}}, {'ascendant': 120}, {'planets': {'Moon': {}}})
    assert points.calculate_kharesh_point().get('error')
    assert points.calculate_64th_navamsa().get('error')
    with pytest.raises(ValueError):
        CharaDashaCalculator(chart())._get_planet_sign('Unknown')


def test_nonclassical_bodies_do_not_change_chara_or_shoola_strength():
    d1 = chart()
    before = CharaDashaCalculator(d1)._count_planets_in_sign(1)
    shoola_before = ShoolaDashaCalculator(d1)._count_planets_in_sign(1)
    d1['planets']['Uranus'] = {'sign': 1}
    assert CharaDashaCalculator(d1)._count_planets_in_sign(1) == before
    assert ShoolaDashaCalculator(d1)._count_planets_in_sign(1) == shoola_before


def test_verified_points_tool_never_includes_legacy_undated_forecasts(monkeypatch):
    from chat.calculator_menu import run_calculator
    def forbidden(*args):
        raise AssertionError('Natal evidence must not invoke an undated transit forecast')
    monkeypatch.setattr(SniperPointsCalculator, '_calculate_bhrigu_bindu_transits', forbidden)
    birth = dict(date='1990-01-01', time='12:00:00', latitude=28.6139, longitude=77.209, timezone='5.5')
    result = run_calculator('points.sniper', birth)['facts']
    assert result['bhrigu_bindu']['upcoming_transits']['status'] == 'not_requested'


def test_sensitive_sector_mapping_agrees_across_all_d3_and_d9_parts():
    for division, ordinal in [(3, 22), (9, 64)]:
        width = 30 / division
        for sector in range(12 * division):
            origin = sector * width + width / 2
            target = (origin + (ordinal - 1) * width) % 360
            source_varga = DivisionalChartCalculator(chart(asc=origin)).calculate_divisional_chart(division)['divisional_chart']
            target_varga = DivisionalChartCalculator(chart(asc=target)).calculate_divisional_chart(division)['divisional_chart']
            offset = 7 if division == 3 else 3
            assert int(target_varga['ascendant'] / 30) == (int(source_varga['ascendant'] / 30) + offset) % 12
            bounds = SniperPointsCalculator._physical_sector(origin, division, ordinal)['d1_sector']
            assert bounds['start_longitude'] <= target < bounds['end_longitude']


def test_verified_chara_keeps_birth_time_and_filters_requested_range():
    from chat.verified_chat_pipeline import _calculate_requested_capabilities
    birth = dict(date='1990-01-01', time='13:14:15', latitude=28.6139, longitude=77.209, timezone='5.5')
    result = _calculate_requested_capabilities(birth, ['jaimini.chara_dasha'], {}, {}, {'start_date': '2027-01-01', 'end_date': '2027-02-01'})['jaimini.chara_dasha']
    assert result['system'] == 'Jaimini Chara Dasha (K.N. Rao)'
    assert result['periods']
    for md in result['periods']:
        assert datetime.fromisoformat(md['start_iso']).time().isoformat() == '13:14:15'
        assert datetime.fromisoformat(md['start_iso']) < datetime(2027, 2, 1, tzinfo=timezone.utc)
        assert datetime.fromisoformat(md['end_iso']) > datetime(2027, 1, 1, tzinfo=timezone.utc)


def test_yogini_api_preserves_client_shape_with_exact_subperiods():
    import asyncio
    from yogini_dasha_routes import get_yogini_dasha, YoginiDashaRequest
    result = asyncio.run(get_yogini_dasha(YoginiDashaRequest(date='2000-01-01',time='13:14:15',latitude=28.6139,longitude=77.209,target_date='2000-01-02')))
    current = result['current']['mahadasha']
    row = next(row for row in result['timeline'] if row['start'] == current['start'] and row['end'] == current['end'])
    assert row['sub_periods'][0]['start_iso'] == row['start_iso']
    assert row['sub_periods'][-1]['end_iso'] == row['end_iso']
    assert 0 <= result['current']['progress'] <= 100


def test_longevity_transit_snapshot_honors_profile():
    from longevity.calculator import LongevityCalculator
    from calculators.chart_calculator import ChartCalculator
    from types import SimpleNamespace
    birth = dict(date='1990-01-01',time='13:14:15',latitude=28.6139,longitude=77.209,timezone='5.5',calculation_profile={'ayanamsha':'raman','node_type':'true'})
    d1 = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth),ayanamsha='raman',node_type='true')
    result = LongevityCalculator(birth,d1)._transit_activation(datetime(2026,10,9))
    assert result['status'] == 'completed'
    assert result['ayanamsha'] == 'raman'
    assert result['node_type'] == 'true'
