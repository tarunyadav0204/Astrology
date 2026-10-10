"""Shared UTC/Lahiri primitives. Legacy naive datetimes mean UTC.

Use the chart calculator's lock because Swiss Ephemeris sidereal settings are
mutable. Returned sign indexes remain zero-based and houses remain one-based.
"""
from datetime import datetime, timedelta, timezone
import math
import swisseph as swe
from calculators.chart_calculator import _SWISSEPH_CHART_LOCK

FLAGS = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


def utc_naive(value):
    if value.tzinfo is not None:
        value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def julian(value):
    value = utc_naive(value)
    hour = value.hour + value.minute / 60 + (value.second + value.microsecond / 1e6) / 3600
    return swe.julday(value.year, value.month, value.day, hour)


def from_julian(jd):
    year, month, day, hour = swe.revjul(jd)
    return datetime(year, month, day) + timedelta(hours=hour)


def position(jd, planet):
    with _SWISSEPH_CHART_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.calc_ut(jd, planet, FLAGS)[0]


def validate_location(latitude, longitude):
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError('Latitude must be between -90 and 90')
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError('Longitude must be between -180 and 180')


def chart_at(value, latitude, longitude):
    validate_location(latitude, longitude)
    jd = julian(value)
    with _SWISSEPH_CHART_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        # Whole sign works at polar latitudes where Placidus is undefined.
        ascendant = swe.houses_ex(jd, latitude, longitude, b'W', swe.FLG_SIDEREAL)[1][0]
        planets = {}
        for name, body in {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
                           'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
                           'Venus': swe.VENUS, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}.items():
            pos = position(jd, body)
            planets[name] = planet_row(pos, ascendant)
        rahu = position(jd, swe.MEAN_NODE)
        planets['Ketu'] = planet_row(((rahu[0] + 180) % 360, -rahu[1], rahu[2], rahu[3]), ascendant)
    return {'ascendant': round(ascendant, 6), 'planets': planets,
            'calculation_basis': {'zodiac': 'sidereal', 'ayanamsha': 'lahiri',
                                  'house_system': 'whole_sign', 'node_type': 'mean', 'timezone': 'UTC'}}


def planet_row(pos, ascendant):
    lon = pos[0] % 360
    return {'longitude': round(lon, 6), 'latitude': round(pos[1], 6),
            'sign': int(lon / 30), 'house': (int(lon / 30) - int(ascendant / 30)) % 12 + 1,
            'speed': round(pos[3], 6), 'is_retrograde': pos[3] < 0}


def forward_crossing(start_jd, angle, target, *, max_days, step=1.0):
    """Bracket a forward angular crossing, then bisect to <0.1 seconds.

    angle must increase monotonically over this short interval (Sun longitude
    or Moon-minus-Sun elongation). Unwrap each small step, including 360→0.
    """
    initial = angle(start_jd) % 360
    remaining = (target - initial) % 360
    if remaining < 1e-8 or 360 - remaining < 1e-8:
        return start_jd
    left, travelled, previous = start_jd, 0.0, initial
    while left < start_jd + max_days:
        right = min(left + step, start_jd + max_days)
        current = angle(right) % 360
        delta = (current - previous + 180) % 360 - 180
        if delta <= 0:
            raise ValueError('Expected a forward angular motion')
        if travelled + delta >= remaining:
            needed = remaining - travelled
            origin = previous
            lo, hi = left, right
            for _ in range(40):
                mid = (lo + hi) / 2
                advance = (angle(mid) - origin) % 360
                if advance >= needed:
                    hi = mid
                else:
                    lo = mid
                if hi - lo < 0.1 / 86400:
                    break
            return hi
        travelled += delta
        left, previous = right, current
    raise ValueError('No angular crossing within search bounds')
