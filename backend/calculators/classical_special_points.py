"""Classically sourced special points used by the professional chart workspace.

The calculator keeps unlike techniques in separate result groups.  It does not
blend their effects or turn their presence into a prediction.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

import swisseph as swe

from utils.timezone_service import parse_timezone_offset
from .chart_calculator import ChartCalculator, resolve_ayanamsha_mode, _SWISSEPH_CHART_LOCK


SIGN_NAMES = ChartCalculator.SIGN_NAMES
SIGN_LORDS = ('Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
              'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter')
NAKSHATRAS = (
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni',
    'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha',
    'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana',
    'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
)
NAKSHATRA_LORDS = ('Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter',
                    'Saturn', 'Mercury')
WEEKDAY_LORDS = ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn')
TIME_POINT_BY_LORD = {
    'Sun': 'Kala',
    'Mars': 'Mrityu',
    'Mercury': 'Ardhaprahara',
    'Jupiter': 'Yamaghantaka',
    'Saturn': 'Gulika',
}


class SpecialPointCalculationError(ValueError):
    """Raised when a required astronomical input cannot be calculated exactly."""


def _value(source: Any, key: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(key, default)
    return getattr(source, key, default)


def _nakshatra(longitude: float) -> Dict[str, Any]:
    lon = float(longitude) % 360.0
    span = 360.0 / 27.0
    index = min(26, int(lon / span))
    within = lon - index * span
    pada = min(4, int(within / (span / 4.0)) + 1)
    return {
        'nakshatra': NAKSHATRAS[index],
        'nakshatra_number': index + 1,
        'nakshatra_lord': NAKSHATRA_LORDS[index % 9],
        'pada': pada,
        'degree_in_nakshatra': round(within, 6),
    }


def _placement(longitude: float, ascendant: float) -> Dict[str, Any]:
    lon = float(longitude) % 360.0
    sign = int(lon / 30.0)
    asc_sign = int((float(ascendant) % 360.0) / 30.0)
    return {
        'longitude': round(lon, 6),
        'sign': sign,
        'sign_name': SIGN_NAMES[sign],
        'degree': round(lon % 30.0, 6),
        'house': ((sign - asc_sign) % 12) + 1,
        'sign_lord': SIGN_LORDS[sign],
        **_nakshatra(lon),
    }


def _next_solar_event(start_jd: float, latitude: float, longitude: float, event_flag: int) -> float:
    result, times = swe.rise_trans(
        float(start_jd),
        swe.SUN,
        event_flag | swe.BIT_DISC_CENTER,
        (float(longitude), float(latitude), 0.0),
        0.0,
        0.0,
        swe.FLG_SWIEPH,
    )
    if result < 0 or not times or not times[0]:
        raise SpecialPointCalculationError('Swiss Ephemeris could not determine the required sunrise or sunset')
    return float(times[0])


def _local_iso(jd: float, timezone_offset: float) -> str:
    year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
    utc = datetime(year, month, day) + timedelta(hours=float(hour))
    local = utc + timedelta(hours=float(timezone_offset))
    return local.replace(microsecond=0).isoformat(timespec='seconds')


def _ascendant_at(jd: float, latitude: float, longitude: float, sid_mode: int) -> float:
    swe.set_sid_mode(sid_mode)
    tropical_ascendant = swe.houses(float(jd), float(latitude), float(longitude), b'P')[1][0]
    ayanamsa = swe.get_ayanamsa_ut(float(jd))
    return (tropical_ascendant - ayanamsa - ChartCalculator.D1_CORRECTION) % 360.0


def _moon_longitude_and_speed(jd: float, sid_mode: int) -> Tuple[float, float]:
    with _SWISSEPH_CHART_LOCK:
        swe.set_sid_mode(sid_mode)
        values = swe.calc_ut(float(jd), swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED | swe.FLG_SWIEPH)[0]
    return (float(values[0]) - ChartCalculator.D1_CORRECTION) % 360.0, float(values[3])


def _sun_longitude(jd: float, sid_mode: int) -> float:
    """Return the Sun on the same sidereal/correction profile as the D1 chart."""
    with _SWISSEPH_CHART_LOCK:
        swe.set_sid_mode(sid_mode)
        values = swe.calc_ut(float(jd), swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)[0]
    return (float(values[0]) - ChartCalculator.D1_CORRECTION) % 360.0


class ClassicalSpecialPointsCalculator:
    """BPHS special points plus explicitly labelled later-tradition additions."""

    def __init__(
        self,
        chart_data: Dict[str, Any],
        birth_data: Any,
        d9_chart: Optional[Dict[str, Any]] = None,
        *,
        ayanamsha: str = 'lahiri',
    ) -> None:
        self.chart = chart_data or {}
        self.birth = birth_data
        self.d9 = d9_chart or {}
        self.ayanamsha_key, self.sid_mode = resolve_ayanamsha_mode(ayanamsha)
        self.ascendant = float(self.chart.get('ascendant'))
        self.sun_longitude = float((self.chart.get('planets') or {}).get('Sun', {}).get('longitude'))

    def _birth_jd(self) -> Tuple[float, float, date]:
        date_text = str(_value(self.birth, 'date', '')).split('T')[0]
        time_text = str(_value(self.birth, 'time', ''))
        if not date_text or not time_text:
            raise SpecialPointCalculationError('Birth date and time are required')
        year, month, day = (int(part) for part in date_text.split('-'))
        parts = [float(part) for part in time_text.split(':')]
        while len(parts) < 3:
            parts.append(0.0)
        local_hour = parts[0] + parts[1] / 60.0 + parts[2] / 3600.0
        latitude = float(_value(self.birth, 'latitude'))
        longitude = float(_value(self.birth, 'longitude'))
        offset = parse_timezone_offset(
            _value(self.birth, 'timezone', ''), latitude, longitude, for_date=date_text,
        )
        return swe.julday(year, month, day, local_hour - float(offset)), float(offset), date(year, month, day)

    def _day_night_frame(self) -> Dict[str, Any]:
        birth_jd, offset, civil_date = self._birth_jd()
        latitude = float(_value(self.birth, 'latitude'))
        longitude = float(_value(self.birth, 'longitude'))
        local_midnight_jd = swe.julday(civil_date.year, civil_date.month, civil_date.day, -offset)
        sunrise = _next_solar_event(local_midnight_jd - 1e-6, latitude, longitude, swe.CALC_RISE)
        sunset = _next_solar_event(local_midnight_jd - 1e-6, latitude, longitude, swe.CALC_SET)

        if sunrise <= birth_jd < sunset:
            period_start, period_end, is_day = sunrise, sunset, True
            weekday_date = civil_date
            cycle_sunrise = sunrise
        elif birth_jd < sunrise:
            previous_sunset = _next_solar_event(local_midnight_jd - 1.0, latitude, longitude, swe.CALC_SET)
            period_start, period_end, is_day = previous_sunset, sunrise, False
            weekday_date = civil_date - timedelta(days=1)
            cycle_sunrise = _next_solar_event(local_midnight_jd - 1.0, latitude, longitude, swe.CALC_RISE)
        else:
            next_sunrise = _next_solar_event(sunset + 1e-6, latitude, longitude, swe.CALC_RISE)
            period_start, period_end, is_day = sunset, next_sunrise, False
            weekday_date = civil_date
            cycle_sunrise = sunrise

        weekday_index = (weekday_date.weekday() + 1) % 7  # Sunday=0
        first_lord_index = weekday_index if is_day else (weekday_index + 4) % 7
        return {
            'birth_jd': birth_jd,
            'timezone_offset_hours': offset,
            'latitude': latitude,
            'longitude': longitude,
            'is_day_birth': is_day,
            'period_start_jd': period_start,
            'period_end_jd': period_end,
            'period_start_local': _local_iso(period_start, offset),
            'period_end_local': _local_iso(period_end, offset),
            'period_duration_hours': round((period_end - period_start) * 24.0, 6),
            'segment_duration_minutes': round((period_end - period_start) * 24.0 * 60.0 / 8.0, 6),
            'weekday': weekday_date.strftime('%A'),
            'weekday_lord': WEEKDAY_LORDS[weekday_index],
            'first_segment_lord': WEEKDAY_LORDS[first_lord_index],
            'first_lord_index': first_lord_index,
            'cycle_sunrise_jd': cycle_sunrise,
        }

    def solar_upagrahas(self) -> Dict[str, Any]:
        sun = self.sun_longitude % 360.0
        dhuma = (sun + 133.0 + 20.0 / 60.0) % 360.0
        vyatipata = (360.0 - dhuma) % 360.0
        parivesha = (vyatipata + 180.0) % 360.0
        indrachapa = (360.0 - parivesha) % 360.0
        upaketu = (indrachapa + 16.0 + 40.0 / 60.0) % 360.0
        formulas = {
            'Dhuma': 'Sun + 133°20′',
            'Vyatipata': '360° − Dhuma',
            'Parivesha': 'Vyatipata + 180°',
            'Indrachapa': '360° − Parivesha',
            'Upaketu': 'Indrachapa + 16°40′',
        }
        values = (('Dhuma', dhuma), ('Vyatipata', vyatipata), ('Parivesha', parivesha),
                  ('Indrachapa', indrachapa), ('Upaketu', upaketu))
        return {
            'points': [{**_placement(lon, self.ascendant), 'name': name, 'formula': formulas[name]} for name, lon in values],
            'calculation_basis': {
                'tradition': 'Brihat Parashara Hora Shastra',
                'reference': 'BPHS 3.61–65; house effects in BPHS 25.2–61',
                'ayanamsha': self.ayanamsha_key,
                'validation': 'Upaketu + 30° returns the Sun longitude',
                'closure_error_degrees': round(abs(((upaketu + 30.0 - sun + 180.0) % 360.0) - 180.0), 9),
            },
        }

    def time_upagrahas(self) -> Dict[str, Any]:
        frame = self._day_night_frame()
        segment_length = (frame['period_end_jd'] - frame['period_start_jd']) / 8.0
        rows = []
        saturn_segment = None
        for segment_index in range(7):
            lord = WEEKDAY_LORDS[(frame['first_lord_index'] + segment_index) % 7]
            if lord not in TIME_POINT_BY_LORD:
                continue
            name = TIME_POINT_BY_LORD[lord]
            start_jd = frame['period_start_jd'] + segment_index * segment_length
            end_jd = start_jd + segment_length
            ascendant = _ascendant_at(start_jd, frame['latitude'], frame['longitude'], self.sid_mode)
            row = {
                'name': name,
                'segment_lord': lord,
                'segment_number': segment_index + 1,
                'segment_start_local': _local_iso(start_jd, frame['timezone_offset_hours']),
                'segment_end_local': _local_iso(end_jd, frame['timezone_offset_hours']),
                'point_moment': 'segment_start',
                **_placement(ascendant, self.ascendant),
            }
            rows.append(row)
            if lord == 'Saturn':
                saturn_segment = (segment_index, start_jd, end_jd)

        if saturn_segment is None:
            raise SpecialPointCalculationError('Saturn segment was not found in the seven ruled portions')
        segment_index, start_jd, end_jd = saturn_segment
        gulika = next(row for row in rows if row['name'] == 'Gulika')
        rows.append({
            **gulika,
            'name': 'Mandi',
            'point_moment': 'same_as_gulika_bphs',
            'alias_of': 'Gulika',
        })
        return {
            'points': rows,
            'day_night_frame': {key: value for key, value in frame.items() if not key.endswith('_jd') and key != 'first_lord_index'},
            'calculation_basis': {
                'tradition': 'Brihat Parashara Hora Shastra',
                'reference': 'BPHS 3.66–70',
                'method': 'Actual local day or night divided into eight equal durations; ascendant at the start of the applicable planetary segment.',
                'mandi_method': 'BPHS identifies Mandi with Gulika, so both names carry the ascendant at the start of Saturn’s segment. Later differing conventions are not mixed into this result.',
                'ayanamsha': self.ayanamsha_key,
                'fallback_used': False,
            },
        }

    def pranapada(self) -> Dict[str, Any]:
        frame = self._day_night_frame()
        elapsed_days = (frame['birth_jd'] - frame['cycle_sunrise_jd']) % 1.0
        vighatis = elapsed_days * 3600.0
        time_arc = vighatis / 15.0
        sun_sign = int(self.sun_longitude / 30.0)
        modality = sun_sign % 3
        additional_arc = 0.0 if modality == 0 else 240.0 if modality == 1 else 120.0
        longitude = (time_arc + self.sun_longitude + additional_arc) % 360.0
        favorable_houses = {2, 4, 5, 9, 10, 11}
        result = _placement(longitude, self.ascendant)
        return {
            **result,
            'name': 'Pranapada Lagna',
            'sun_sign_modality': ('movable', 'fixed', 'dual')[modality],
            'vighatis_from_sunrise': round(vighatis, 6),
            'time_arc_degrees': round(time_arc, 6),
            'additional_arc_degrees': additional_arc,
            'classical_house_classification': 'favorable' if result['house'] in favorable_houses else 'unfavorable',
            'calculation_basis': {
                'tradition': 'Brihat Parashara Hora Shastra',
                'reference': 'BPHS 3.71–74; house effects in BPHS 25.74–85',
                'formula': 'Vighatis elapsed from sunrise ÷ 15, added to the Sun; add 240° for fixed Sun or 120° for dual Sun.',
                'ayanamsha': self.ayanamsha_key,
                'fallback_used': False,
            },
        }

    def _reference_planet_houses(self, reference_sign: int) -> list[Dict[str, Any]]:
        """Place the nine grahas by whole sign from a special-Lagna reference."""
        rows = []
        for planet in ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'):
            data = (self.chart.get('planets') or {}).get(planet)
            if not isinstance(data, Mapping):
                continue
            try:
                sign_value = data.get('sign')
                sign = int(sign_value if sign_value is not None else float(data['longitude']) // 30) % 12
            except (KeyError, TypeError, ValueError):
                continue
            rows.append({
                'planet': planet,
                'sign': sign,
                'sign_name': SIGN_NAMES[sign],
                'house_from_reference': ((sign - int(reference_sign)) % 12) + 1,
            })
        return rows

    def _lagna_row(
        self,
        *,
        key: str,
        name: str,
        longitude: float,
        precision: str,
        reference: str,
        formula: str,
        sunrise_local: Optional[str] = None,
        sunrise_sun_longitude: Optional[float] = None,
        elapsed_ghatis: Optional[float] = None,
        divisor_ghatis: Optional[float] = None,
    ) -> Dict[str, Any]:
        placement = _placement(longitude, self.ascendant)
        row = {
            **placement,
            'key': key,
            'name': name,
            'precision': precision,
            'planet_houses': self._reference_planet_houses(placement['sign']),
            'calculation_basis': {
                'tradition': 'Brihat Parashara Hora Shastra',
                'reference': reference,
                'formula': formula,
                'ayanamsha': self.ayanamsha_key,
                'fallback_used': False,
            },
        }
        if sunrise_local is not None:
            row['calculation_basis']['applicable_sunrise_local'] = sunrise_local
        if sunrise_sun_longitude is not None:
            row['calculation_basis']['sun_longitude_at_sunrise'] = round(sunrise_sun_longitude, 6)
        if elapsed_ghatis is not None:
            row['calculation_basis']['elapsed_ghatis'] = round(elapsed_ghatis, 6)
        if divisor_ghatis is not None:
            row['calculation_basis']['ghatis_per_sign'] = divisor_ghatis
        return row

    def special_lagnas(self, pranapada: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return the natal and source-audited special-Lagna worksheet.

        BPHS 5.2–6 makes Bhava, Hora and Ghatika Lagna continuous points:
        elapsed ghatis from the applicable sunrise are converted to zodiacal
        progress and added to the Sun's longitude at that sunrise.
        """
        frame = self._day_night_frame()
        elapsed_days = frame['birth_jd'] - frame['cycle_sunrise_jd']
        if elapsed_days < 0 or elapsed_days >= 1.5:
            raise SpecialPointCalculationError('Elapsed time from the applicable sunrise is outside the expected civil-day range')
        elapsed_ghatis = elapsed_days * 60.0
        sunrise_sun = _sun_longitude(frame['cycle_sunrise_jd'], self.sid_mode)
        sunrise_local = _local_iso(frame['cycle_sunrise_jd'], frame['timezone_offset_hours'])

        def timed(key: str, name: str, divisor: float, reference: str) -> Dict[str, Any]:
            longitude = (sunrise_sun + (elapsed_ghatis / divisor) * 30.0) % 360.0
            return self._lagna_row(
                key=key,
                name=name,
                longitude=longitude,
                precision='exact_longitude',
                reference=reference,
                formula=f'Sun at applicable local sunrise + (elapsed ghatis ÷ {divisor:g}) signs',
                sunrise_local=sunrise_local,
                sunrise_sun_longitude=sunrise_sun,
                elapsed_ghatis=elapsed_ghatis,
                divisor_ghatis=divisor,
            )

        natal = self._lagna_row(
            key='natal_lagna',
            name='Natal Lagna',
            longitude=self.ascendant,
            precision='exact_longitude',
            reference='Astronomical sidereal ascendant at birth',
            formula='Local sidereal-time ascendant for the recorded place and time',
        )
        bhava = timed('bhava_lagna', 'Bhava Lagna', 5.0, 'BPHS 5.2–3')
        hora = timed('hora_lagna', 'Hora Lagna', 2.5, 'BPHS 5.4–5')
        ghatika = timed('ghatika_lagna', 'Ghatika Lagna', 1.0, 'BPHS 5.6')

        pp = dict(pranapada or self.pranapada())
        pp.update({
            'key': 'pranapada_lagna',
            'name': 'Pranapada Lagna',
            'precision': 'exact_longitude',
            'planet_houses': self._reference_planet_houses(pp['sign']),
        })

        # Indu Lagna is deliberately kept separate from BPHS Chapter 5 and is
        # sign-only: the traditional Kala calculation supplies no exact degree.
        from .indu_lagna_calculator import InduLagnaCalculator
        indu_data = InduLagnaCalculator(self.chart).get_indu_lagna_data()
        indu_sign = int(indu_data['sign'])
        indu = {
            'key': 'indu_lagna',
            'name': 'Indu Lagna',
            'sign': indu_sign,
            'sign_name': SIGN_NAMES[indu_sign],
            'house': int(indu_data['house']),
            'sign_lord': SIGN_LORDS[indu_sign],
            'precision': 'sign_only',
            'exact_degree_available': False,
            'longitude_is_plotting_anchor': True,
            'planet_houses': self._reference_planet_houses(indu_sign),
            'calculation_basis': {
                'tradition': 'Uttara Kalamrita',
                'reference': 'Uttara Kalamrita 4.17; kept separate from BPHS Chapter 5',
                'formula': 'Add the Kalas of the ninth lords from Lagna and Moon; count the remainder from the Moon',
                'fallback_used': False,
            },
        }
        return {
            'points': [natal, bhava, hora, ghatika, pp, indu],
            'groups': {
                'birth_reference': ['natal_lagna'],
                'bphs_time_derived': ['bhava_lagna', 'hora_lagna', 'ghatika_lagna'],
                'other_classical_points': ['pranapada_lagna', 'indu_lagna'],
            },
            'calculation_basis': {
                'reference': 'BPHS Chapter 5.2–6 for Bhava, Hora and Ghatika Lagna',
                'sunrise_rule': 'For births before local sunrise, elapsed time is counted from the previous local sunrise.',
                'ayanamsha': self.ayanamsha_key,
                'fallback_used': False,
            },
        }

    def navamsa_64(self) -> Dict[str, Any]:
        payload = self.d9.get('divisional_chart', self.d9)
        planets = payload.get('planets') or {}
        ascendant = payload.get('ascendant')
        rows = []
        references: Iterable[Tuple[str, Optional[int]]] = (
            ('Moon', (planets.get('Moon') or {}).get('sign')),
            ('Lagna', int(float(ascendant) / 30.0) if ascendant is not None else None),
        )
        for reference, sign in references:
            if sign is None:
                continue
            source_sign = int(sign) % 12
            sensitive_sign = (source_sign + 3) % 12
            rows.append({
                'reference': reference,
                'd9_reference_sign': source_sign,
                'd9_reference_sign_name': SIGN_NAMES[source_sign],
                'sensitive_sign': sensitive_sign,
                'sensitive_sign_name': SIGN_NAMES[sensitive_sign],
                'sensitive_sign_lord': SIGN_LORDS[sensitive_sign],
                'derivation': 'Fourth sign from the reference in D9 (the 64th Navamsha)',
            })
        return {
            'references': rows,
            'calculation_basis': {
                'method': 'Fourth sign from the Moon and separately from the Lagna in D9.',
                'scope': 'Derived sensitive reference; it is not an event prediction by itself.',
            },
        }

    def abhukta_mula(self) -> Dict[str, Any]:
        """Evaluate BPHS Abhukta Mula by actual time around the Jyeshtha–Mula boundary."""
        birth_jd, offset, _ = self._birth_jd()
        boundary_jd = birth_jd
        for _ in range(8):
            longitude, speed = _moon_longitude_and_speed(boundary_jd, self.sid_mode)
            if abs(speed) < 1e-9:
                raise SpecialPointCalculationError('Moon speed is unavailable for Abhukta Mula calculation')
            signed_delta = ((longitude - 240.0 + 180.0) % 360.0) - 180.0
            boundary_jd -= signed_delta / speed
        boundary_longitude, _ = _moon_longitude_and_speed(boundary_jd, self.sid_mode)
        error = abs(((boundary_longitude - 240.0 + 180.0) % 360.0) - 180.0)
        if error > 1e-5:
            raise SpecialPointCalculationError('Jyeshtha–Mula boundary did not converge')

        # BPHS: final six ghatikas of Jyeshtha and first eight of Mula.
        window_start = boundary_jd - (6.0 * 24.0) / 1440.0
        window_end = boundary_jd + (8.0 * 24.0) / 1440.0
        active = window_start <= birth_jd < window_end
        phase = None
        if active:
            phase = 'last_six_ghatikas_of_jyeshtha' if birth_jd < boundary_jd else 'first_eight_ghatikas_of_mula'
        return {
            'is_active': active,
            'phase': phase,
            'moon_longitude': round(_moon_longitude_and_speed(birth_jd, self.sid_mode)[0], 6),
            'jyeshtha_mula_boundary_local': _local_iso(boundary_jd, offset),
            'window_start_local': _local_iso(window_start, offset),
            'window_end_local': _local_iso(window_end, offset),
            'calculation_basis': {
                'tradition': 'Brihat Parashara Hora Shastra',
                'reference': 'BPHS, Abhukta Mula birth chapter: last 6 ghatikas of Jyeshtha and first 8 ghatikas of Mula',
                'method': 'Actual Moon crossing of 240° sidereal longitude; one ghatika is 24 minutes.',
                'ayanamsha': self.ayanamsha_key,
                'textual_variants': 'Other authorities give narrower intervals. This result follows the stated BPHS recension and does not blend variants.',
                'fallback_used': False,
            },
        }

    def calculate(self) -> Dict[str, Any]:
        pranapada = self.pranapada()
        return {
            'version': 'classical-special-points/1.1.0',
            'solar_upagrahas': self.solar_upagrahas(),
            'time_upagrahas': self.time_upagrahas(),
            'pranapada': pranapada,
            'special_lagnas': self.special_lagnas(pranapada),
            'navamsa_64': self.navamsa_64(),
            'abhukta_mula': self.abhukta_mula(),
        }
