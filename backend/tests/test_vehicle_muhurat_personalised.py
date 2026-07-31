import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from calculators.muhurat_calculator import MuhuratCalculator


def test_vehicle_context_derives_personalised_fourth_house():
    calculator = MuhuratCalculator()
    context = calculator._build_natal_context({
        'date': '1980-04-02',
        'time': '14:55',
        'latitude': 29.15,
        'longitude': 75.72,
        'timezone': 'Asia/Kolkata',
    })

    assert context is not None
    assert context['fourth_sign'] == (context['asc_sign'] + 3) % 12
    assert context['fourth_lord'] is not None
    assert context['moon_sign'] in range(12)


def test_angular_distance_wraps_across_zero():
    assert MuhuratCalculator._angular_distance(359.0, 1.0) == 2.0


def test_vehicle_result_exposes_score_and_reasons():
    calculator = MuhuratCalculator()
    result = calculator.calculate_vehicle_muhurat(
        '2026-09-28', '2026-09-28', 28.6139, 77.2090, 10, 'Asia/Kolkata',
        birth_data={
            'date': '1980-04-02',
            'time': '14:55',
            'latitude': 29.15,
            'longitude': 75.72,
            'timezone': 'Asia/Kolkata',
        },
    )

    assert result['dates_found'] >= 0
    for day in result['recommendations']:
        for slot in day['slots']:
            assert isinstance(slot['score'], int)
            assert 0 <= slot['score'] <= 100
            assert slot['reasons']
            assert slot['positives']
            assert slot['cautions']
            assert slot['score_breakdown']
            assert slot['rationale']


def test_unfavourable_chandra_bala_is_reported_as_caution_not_silent_veto():
    calculator = MuhuratCalculator()
    context = calculator._build_natal_context({
        'date': '1980-04-02', 'time': '14:55', 'latitude': 29.15,
        'longitude': 75.72, 'timezone': 'Asia/Kolkata',
    })
    # 2026-08-09 has an otherwise evaluable Libra/Capricorn election slot;
    # Chandra Bala must remain visible as a caution rather than discard it.
    result = calculator.calculate_vehicle_muhurat(
        '2026-08-09', '2026-08-09', 28.6139, 77.2090, 15, 'Asia/Kolkata',
        birth_data={
            'date': '1980-04-02', 'time': '14:55', 'latitude': 29.15,
            'longitude': 75.72, 'timezone': 'Asia/Kolkata',
        },
    )
    assert result['recommendations']
    assert any('Chandra Bala is unfavourable' in reason for reason in result['recommendations'][0]['slots'][0]['cautions'])
