import sys
import swisseph as swe

sys.path.insert(0, 'backend')

from panchang.muhurat_calculator import MuhuratCalculator
from calculators.muhurat_calculator import MuhuratCalculator as RichMuhuratCalculator


def test_muhurat_window_panchak_overlap_is_marked():
    calculator = MuhuratCalculator()
    sunrise = swe.julday(2026, 7, 30, 0.0)
    muhurtas, _ = calculator._build_day_muhurtas(
        sunrise,
        12.0,
        [1, 2],
        'test',
        'UTC+0',
        0.0,
        0.0,
        [(sunrise, sunrise + 0.02)],
    )

    assert muhurtas[0]['panchak'] is True
    assert muhurtas[0]['panchak_warning']
    assert muhurtas[1]['panchak'] is False


def test_muhurat_response_exposes_panchak_status():
    result = MuhuratCalculator().calculate_vehicle_muhurat(
        '2026-07-30', 28.6139, 77.2090, 'Asia/Kolkata'
    )
    assert set(result['panchak']) == {'is_panchak', 'name', 'reason', 'intervals'}
    assert all('panchak' in window for window in result['muhurtas'])


def test_rich_vehicle_panchak_status_uses_correct_local_day_boundaries():
    status = RichMuhuratCalculator()._panchak_status(
        '2026-08-01', 28.6139, 77.2090, 'Asia/Kolkata'
    )
    assert status['is_panchak'] is True
    assert status['intervals']


def test_rich_vehicle_rejects_panchak_in_strict_mode():
    result = RichMuhuratCalculator().calculate_vehicle_muhurat(
        '2026-08-01', '2026-08-01', 28.6139, 77.2090, None, 'Asia/Kolkata'
    )
    assert result['recommendations'] == []
    assert any('Panchak is active' in reason for reason in result['rejected_dates'][0]['reasons'])
