import sys

sys.path.insert(0, 'backend')

from reports.models import BirthInput


def test_birth_input_normalizes_mobile_iso_timestamp_to_calendar_date():
    birth = BirthInput(
        name='Auckland native',
        date='2006-04-15T04:26:51.191Z',
        time='16:30:00',
        place='Auckland, New Zealand',
        latitude=-36.8509,
        longitude=174.7645,
        timezone='Pacific/Auckland',
    )

    assert birth.date == '2006-04-15'
    assert birth.place == 'Auckland, New Zealand'
    assert birth.latitude == -36.8509
    assert birth.longitude == 174.7645
