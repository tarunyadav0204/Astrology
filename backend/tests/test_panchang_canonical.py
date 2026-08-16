import sys
from datetime import datetime

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


def test_iso_datetime_date_is_normalized_for_daily_and_birth_panchang():
    iso_date = '2006-04-15T04:26:51.191Z'
    calculator = PanchangCalculator()

    daily = calculator.calculate_panchang(iso_date, *LOCATION)
    birth = calculator.calculate_birth_panchang({
        'date': iso_date,
        'time': '16:30:00',
        'latitude': -36.8509,
        'longitude': 174.7645,
        'timezone': 'Pacific/Auckland',
    })

    assert set(daily) >= {'tithi', 'vara', 'nakshatra', 'yoga', 'karana'}
    assert set(birth) >= {'tithi', 'vara', 'nakshatra', 'yoga', 'karana'}


def test_auckland_sunrise_stays_on_requested_local_calendar_day():
    timings = PanchangCalculator().get_local_sunrise_sunset(
        '2006-04-15T04:26:51.191Z',
        -36.8509,
        174.7645,
        'Pacific/Auckland',
    )

    assert datetime.fromisoformat(timings['sunrise']).date().isoformat() == '2006-04-15'
    assert datetime.fromisoformat(timings['sunset']).date().isoformat() == '2006-04-15'
