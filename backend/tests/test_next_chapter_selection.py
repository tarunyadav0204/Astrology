"""Current/next selections share the same real period boundaries."""
from datetime import datetime, timedelta, timezone

from next_chapter.periods import select_next_antardasha

BIRTH = {'name': 'Selection test', 'date': '1990-04-23', 'time': '06:15:00',
         'timezone': 'Asia/Kolkata', 'latitude': 13.0833333333, 'longitude': 80.2833333333,
         'place': 'Chennai'}


def test_current_selection_contains_today_and_all_nine_contiguous_pds():
    now = datetime(2026, 11, 8, tzinfo=timezone.utc)
    current = select_next_antardasha(BIRTH, now, selection='current')
    upcoming = select_next_antardasha(BIRTH, now, selection='next')
    assert current['selection'] == 'current_antardasha'
    assert current['antardasha'] == upcoming['current_antardasha']
    assert current['next_antardasha'] == upcoming['antardasha']
    assert current['next_mahadasha'] == upcoming['mahadasha']
    assert current['mahadasha'] == current['current_mahadasha']
    assert datetime.fromisoformat(current['antardasha']['start_at']) <= now < datetime.fromisoformat(current['antardasha']['end_at'])
    pds = current['pratyantardashas']
    assert len(pds) == 9
    assert pds[0]['start_at'] == current['antardasha']['start_at']
    assert pds[-1]['end_at'] == current['antardasha']['end_at']
    assert all(a['end_at'] == b['start_at'] for a,b in zip(pds,pds[1:]))


def test_next_becomes_current_at_boundary_without_changing_saved_period_identity():
    now = datetime(2026, 11, 8, tzinfo=timezone.utc)
    upcoming = select_next_antardasha(BIRTH, now)
    boundary = datetime.fromisoformat(upcoming['antardasha']['start_at'])
    before = select_next_antardasha(BIRTH, boundary-timedelta(seconds=1), selection='current')
    after = select_next_antardasha(BIRTH, boundary, selection='current')
    assert before['antardasha']['start_at'] != after['antardasha']['start_at']
    assert after['antardasha'] == upcoming['antardasha']
    assert after['pratyantardashas'] == upcoming['pratyantardashas']
