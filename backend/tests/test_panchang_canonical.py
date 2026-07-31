import sys

sys.path.insert(0, 'backend')

from panchang.panchang_calculator import PanchangCalculator
from calculators.panchang_calculator import PanchangCalculator as LegacyPanchangCalculator


LOCATION = (28.6139, 77.2090, 'Asia/Kolkata')


def test_canonical_daily_reference_returns_complete_five_limbs():
    calculator = PanchangCalculator()
    result = calculator.calculate_panchang('2026-07-30', *LOCATION)

    assert set(result) >= {'tithi', 'vara', 'nakshatra', 'yoga', 'karana'}
    assert result['tithi']['start_time'] != result['tithi']['end_time']
    assert 1 <= result['nakshatra']['pada'] <= 4
    assert result['karana']['name']


def test_birth_reference_is_preserved_through_compatibility_facade():
    birth = {
        'date': '1980-04-02',
        'time': '14:55:00',
        'latitude': 29.15,
        'longitude': 75.72,
        'timezone': 'Asia/Kolkata',
    }
    canonical = PanchangCalculator().calculate_birth_panchang(birth)
    legacy = LegacyPanchangCalculator().calculate_birth_panchang(birth)

    assert canonical['tithi']['name'] == legacy['tithi']['name']
    assert canonical['nakshatra']['name'] == legacy['nakshatra']['name']
    assert canonical['karana']['name'] == legacy['karana']['name']
