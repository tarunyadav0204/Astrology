"""Select the upcoming AD using the same Vimshottari clock as ChartScreen."""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from shared.dasha_calculator import DashaCalculator
from utils.timezone_service import get_iana_timezone


def select_next_antardasha(birth, as_of, *, calculator=None, selection="next"):
    if selection not in ("current", "next"):
        raise ValueError("selection must be current or next")
    if as_of.tzinfo is None:
        raise ValueError('as_of must include a timezone')
    if calculator is None:
        # Pin the same bundled data-file ephemeris used by ChartScreen BEFORE
        # calculating the dasha balance. Otherwise a fresh CLI process may use
        # Moshier until its first chart/transit call and change dates on retry.
        from prediction_engine.transit_returns import _strict_planet_state
        _strict_planet_state(as_of, 'Moon')
        calculator = DashaCalculator()
    zone = ZoneInfo(get_iana_timezone(birth['latitude'], birth['longitude']))
    # Shared dasha boundaries are local wall-clock values, not UTC timestamps.
    local_now = as_of.astimezone(zone).replace(tzinfo=None)
    if local_now < datetime.fromisoformat(f"{birth['date']}T{birth['time']}"):
        raise ValueError('as_of must be on or after birth')
    result = calculator.calculate_current_dashas(birth, local_now, strict=True)
    mahas = sorted(result['maha_dashas'], key=lambda row: calculator._period_bounds(row)[0])
    current = None
    upcoming = None
    for maha in mahas:
        antars = calculator.list_antardashas(maha)
        if antars:
            # Calendar-year MD length can exceed its 365.25-day AD sum by a
            # few hours. The final AD runs until the actual MD transition.
            # Keep the correction explicit rather than leaving an uncovered gap.
            _, md_end = calculator._period_bounds(maha)
            _, last_end = calculator._period_bounds(antars[-1])
            transition = md_end + timedelta(seconds=1)
            adjustment = (transition - last_end).total_seconds()
            if abs(adjustment) > 86400:
                raise ValueError('Antardasha subdivisions do not match their Mahadasha')
            if adjustment:
                antars[-1] = {**antars[-1], '_end_dt': transition,
                    'parent_boundary_adjustment_seconds': adjustment}
        for antar in antars:
            start, end = calculator._period_bounds(antar)
            if start <= local_now < end:
                current = (maha, antar)
            elif start > local_now and current is not None:
                upcoming = (maha, antar)
                break
        if upcoming:
            break
    if not current or (selection == "next" and not upcoming):
        raise ValueError('The shared Vimshottari calculator has no complete upcoming Antardasha')

    def serialize(row, level, start=None, end=None):
        raw_start, raw_end = calculator._period_bounds(row)
        # MD stores transition minus one second; AD and PD store the transition.
        raw_end += timedelta(seconds=1) if level == 'MD' else timedelta(0)
        start, end = start or raw_start, end or raw_end
        return {'planet': row['planet'], 'level': level,
                'start_at': start.replace(tzinfo=zone).isoformat(),
                'end_at': end.replace(tzinfo=zone).isoformat(),
                **({'parent_boundary_adjustment_seconds': row['parent_boundary_adjustment_seconds']}
                   if row.get('parent_boundary_adjustment_seconds') else {})}

    maha, antar = current if selection == "current" else upcoming
    ad_start, ad_end = calculator._period_bounds(antar)
    pds = calculator.list_pratyantardashas(maha, antar)
    if len(pds) != 9:
        raise ValueError('Upcoming Antardasha must contain all nine Pratyantardashas')
    periods = []
    previous_end = ad_start
    for index, pd in enumerate(pds):
        start, end = calculator._period_bounds(pd)
        if abs((start - previous_end).total_seconds()) > 1:
            raise ValueError('Pratyantardasha boundaries contain a gap or overlap')
        # Calendar-year MDs and 365.25-day subdivisions can differ by <1 day.
        # Preserve the AD boundary shown by the app; close the last PD at it.
        if index == len(pds) - 1:
            end = ad_end
        if end <= start or end > ad_end:
            raise ValueError('Pratyantardasha falls outside its Antardasha')
        periods.append({'id': f'pd_{index + 1}', **serialize(pd, 'PD', start, end)})
        previous_end = end
    return {
        'as_of': as_of.astimezone(timezone.utc).isoformat(),
        'timezone': str(zone), 'boundary_convention': '[start_at, end_at)',
        'selection': selection + '_antardasha',
        'mahadasha_changes': current[0]['planet'] != maha['planet'],
        'current_mahadasha': serialize(current[0], 'MD'),
        'current_antardasha': serialize(current[1], 'AD'),
        'next_mahadasha': serialize(upcoming[0], 'MD') if upcoming else None,
        'next_antardasha': serialize(upcoming[1], 'AD') if upcoming else None,
        'mahadasha': serialize(maha, 'MD'),
        'antardasha': serialize(antar, 'AD'),
        'pratyantardashas': periods,
        'date_basis': 'Shared Vimshottari calculator; astronomical contact precision does not imply event certainty.',
    }
