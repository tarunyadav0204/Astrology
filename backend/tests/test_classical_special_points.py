from types import SimpleNamespace

import pytest

from calculators.chart_calculator import ChartCalculator
from calculators.classical_mrityu_bhaga import evaluate_mrityu_bhaga
from calculators.classical_special_points import ClassicalSpecialPointsCalculator
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.jaimini_point_calculator import JaiminiPointCalculator


@pytest.fixture(scope='module')
def sample():
    birth = SimpleNamespace(
        date='1990-04-23', time='06:15:30', latitude=13.0827,
        longitude=80.2707, timezone='Asia/Kolkata',
    )
    chart = ChartCalculator({}).calculate_chart(birth)
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)
    return birth, chart, ClassicalSpecialPointsCalculator(chart, birth, d9).calculate()


def test_chart_uses_exact_upagraha_path_without_fallback(sample):
    _, chart, result = sample
    audit = chart['upagraha_calculation']
    assert audit['success'] is True
    assert audit['calculation_basis']['fallback_used'] is False
    assert chart['planets']['Gulika']['longitude'] == pytest.approx(
        next(row['longitude'] for row in result['time_upagrahas']['points'] if row['name'] == 'Gulika')
    )


def test_solar_upagraha_sequence_closes_back_to_sun(sample):
    _, chart, result = sample
    rows = {row['name']: row for row in result['solar_upagrahas']['points']}
    assert result['solar_upagrahas']['calculation_basis']['closure_error_degrees'] == 0
    assert (rows['Upaketu']['longitude'] + 30) % 360 == pytest.approx(chart['planets']['Sun']['longitude'])


def test_time_upagraha_uses_actual_segment_and_bphs_mandi_alias(sample):
    _, _, result = sample
    time_result = result['time_upagrahas']
    rows = {row['name']: row for row in time_result['points']}
    assert time_result['day_night_frame']['is_day_birth'] is True
    assert rows['Gulika']['point_moment'] == 'segment_start'
    assert rows['Mandi']['point_moment'] == 'same_as_gulika_bphs'
    assert rows['Mandi']['alias_of'] == 'Gulika'
    assert rows['Gulika']['longitude'] == rows['Mandi']['longitude']


def test_pranapada_and_both_64th_navamsa_references_are_returned(sample):
    _, _, result = sample
    assert result['pranapada']['calculation_basis']['fallback_used'] is False
    assert {row['reference'] for row in result['navamsa_64']['references']} == {'Moon', 'Lagna'}


def test_bphs_special_lagnas_use_sunrise_and_their_stated_ghati_rates(sample):
    _, _, result = sample
    worksheet = result['special_lagnas']
    rows = {row['key']: row for row in worksheet['points']}
    expected_divisors = {
        'bhava_lagna': 5.0,
        'hora_lagna': 2.5,
        'ghatika_lagna': 1.0,
    }
    for key, divisor in expected_divisors.items():
        row = rows[key]
        basis = row['calculation_basis']
        expected = (
            basis['sun_longitude_at_sunrise']
            + (basis['elapsed_ghatis'] / divisor) * 30.0
        ) % 360.0
        assert row['longitude'] == pytest.approx(expected, abs=3e-6)
        assert basis['ghatis_per_sign'] == divisor
        assert basis['fallback_used'] is False


def test_special_lagna_precision_is_not_invented(sample):
    _, _, result = sample
    rows = {row['key']: row for row in result['special_lagnas']['points']}
    assert rows['hora_lagna']['precision'] == 'exact_longitude'
    assert rows['hora_lagna']['nakshatra']
    assert rows['indu_lagna']['precision'] == 'sign_only'
    assert rows['indu_lagna']['exact_degree_available'] is False
    assert 'nakshatra' not in rows['indu_lagna']
    assert len(rows['ghatika_lagna']['planet_houses']) == 9


def test_pre_sunrise_special_lagnas_use_previous_local_sunrise():
    birth = SimpleNamespace(
        date='1990-04-23', time='04:15:30', latitude=13.0827,
        longitude=80.2707, timezone='Asia/Kolkata',
    )
    chart = ChartCalculator({}).calculate_chart(birth)
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)
    result = ClassicalSpecialPointsCalculator(chart, birth, d9).calculate()
    hora = next(row for row in result['special_lagnas']['points'] if row['key'] == 'hora_lagna')
    assert hora['calculation_basis']['applicable_sunrise_local'].startswith('1990-04-22')
    assert 0 < hora['calculation_basis']['elapsed_ghatis'] < 60


def test_legacy_hora_and_ghatika_keys_delegate_to_canonical_sunrise_calculation(sample):
    birth, chart, result = sample
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)
    points = JaiminiPointCalculator(chart, d9, 'Saturn', birth_data=birth).calculate_jaimini_points()
    canonical = {row['key']: row for row in result['special_lagnas']['points']}

    for key in ('hora_lagna', 'ghatika_lagna'):
        assert points[key]['available'] is True
        assert points[key]['longitude'] == canonical[key]['longitude']
        assert points[key]['sign_id'] == canonical[key]['sign']
        assert points[key]['calculation_basis']['fallback_used'] is False


def test_abhukta_mula_uses_actual_boundary_time(sample):
    _, _, result = sample
    row = result['abhukta_mula']
    assert row['calculation_basis']['fallback_used'] is False
    assert 'last 6 ghatikas' in row['calculation_basis']['reference']
    assert row['window_start_local'] < row['jyeshtha_mula_boundary_local'] < row['window_end_local']


def test_mrityu_bhaga_is_planet_by_sign_and_ordinal_degree():
    # The selected classical table gives the Sun's 20th degree in Aries and
    # the Moon's 8th degree in Aries. These are distinct one-degree spans.
    assert evaluate_mrityu_bhaga('Sun', 19.5)['is_mrityu_bhaga'] is True
    assert evaluate_mrityu_bhaga('Sun', 7.5)['is_mrityu_bhaga'] is False
    moon = evaluate_mrityu_bhaga('Moon', 7.5)
    assert moon['is_mrityu_bhaga'] is True
    assert moon['degree_span_start'] == 7
    assert moon['degree_span_end'] == 8
