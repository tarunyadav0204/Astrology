from types import SimpleNamespace

import pytest

from calculators.chart_calculator import ChartCalculator
from calculators.classical_shadbala import (
    calculate_classical_shadbala,
    get_aspect_value,
)
from calculators.divisional_chart_calculator import DivisionalChartCalculator


PLANETS = ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')


@pytest.fixture(scope='module')
def parashara_light_result():
    # Parashara's Light 7.0.3 public sample: Chennai, 23 Apr 1990 06:15 IST.
    birth = SimpleNamespace(
        date='1990-04-23', time='06:15:00', timezone='UTC+5:30',
        latitude=13.0833333333, longitude=80.2833333333,
    )
    chart = ChartCalculator({}).calculate_chart(birth, node_type='true')
    chart['divisions'] = DivisionalChartCalculator(chart).calculate_all_divisional_charts()
    return calculate_classical_shadbala(birth, chart)


def test_sthana_components_match_parasharas_light(parashara_light_result):
    expected = {
        'Sun': (59.63, 112.50, 30, 60, 15),
        'Moon': (41.86, 142.50, 30, 15, 0),
        'Mars': (56.72, 86.25, 30, 30, 15),
        'Mercury': (12.93, 127.50, 15, 60, 0),
        'Jupiter': (52.31, 90.00, 15, 15, 0),
        'Venus': (48.99, 123.75, 15, 30, 15),
        'Saturn': (36.17, 157.50, 0, 60, 0),
    }
    keys = ('uccha_bala', 'saptavargaja_bala', 'ojha_yugma_bala',
            'kendradi_bala', 'drekkana_bala')
    for planet, values in expected.items():
        actual = parashara_light_result[planet]['detailed_breakdown']['sthana_components']
        assert tuple(actual[key] for key in keys) == pytest.approx(values, abs=0.01)


def test_dig_and_drik_match_parasharas_light(parashara_light_result):
    expected_dig = (29.18, 20.72, 49.53, 56.85, 40.81, 15.84, 34.29)
    expected_drik = (-11.12, 19.14, 46.68, -16.36, -27.10, 36.74, 18.51)
    for index, planet in enumerate(PLANETS):
        components = parashara_light_result[planet]['components']
        assert components['dig_bala'] == pytest.approx(expected_dig[index], abs=0.01)
        assert components['drik_bala'] == pytest.approx(expected_drik[index], abs=0.01)


def test_kala_rows_match_reference_with_declination_rounding_tolerance(parashara_light_result):
    expected = (126.54, 188.42, 125.14, 222.02, 160.43, 64.17, 136.57)
    for index, planet in enumerate(PLANETS):
        actual = parashara_light_result[planet]['components']['kala_bala']
        assert actual == pytest.approx(expected[index], abs=0.40)


def test_sun_and_moon_chesta_use_classical_ayana_and_paksha(parashara_light_result):
    assert parashara_light_result['Sun']['components']['chesta_bala'] == pytest.approx(46.17, abs=0.40)
    assert parashara_light_result['Moon']['components']['chesta_bala'] == pytest.approx(10.10, abs=0.01)


def test_classical_minimum_ratios_and_relative_ranks(parashara_light_result):
    expected_minimums = {
        'Sun': 390, 'Moon': 360, 'Mars': 300, 'Mercury': 420,
        'Jupiter': 390, 'Venus': 330, 'Saturn': 300,
    }
    for planet, minimum in expected_minimums.items():
        row = parashara_light_result[planet]
        assert row['minimum_required_points'] == minimum
        assert row['minimum_required_rupas'] == pytest.approx(minimum / 60.0, abs=0.01)
        assert row['required_ratio'] == pytest.approx(row['total_points'] / minimum, abs=0.01)
        assert row['meets_minimum'] is (row['required_ratio'] >= 1.0)

    ranked = sorted(
        PLANETS,
        key=lambda planet: (
            -(parashara_light_result[planet]['total_points'] /
              parashara_light_result[planet]['minimum_required_points']),
            planet,
        ),
    )
    assert [parashara_light_result[planet]['relative_rank'] for planet in ranked] == list(range(1, 8))


def test_directed_aspect_does_not_fold_the_arc():
    # Saturn's third-house aspect and a reverse-direction arc are not equivalent.
    forward = get_aspect_value('Saturn', 0.0, 60.0)
    reverse = get_aspect_value('Saturn', 60.0, 0.0)
    assert forward == pytest.approx(60.0)
    assert reverse == pytest.approx(0.0)


def test_missing_varga_fails_instead_of_fabricating_neutral_points():
    birth = SimpleNamespace(
        date='1990-04-23', time='06:15:00', timezone='UTC+5:30',
        latitude=13.0833333333, longitude=80.2833333333,
    )
    chart = ChartCalculator({}).calculate_chart(birth, node_type='true')
    chart['divisions'] = {'D1': {name: {'sign': row['sign'], 'house': row['house']}
                                 for name, row in chart['planets'].items()}}
    with pytest.raises(ValueError, match='Saptavargaja requires'):
        calculate_classical_shadbala(birth, chart)
