import swisseph as swe
from typing import Dict, Any, List
from datetime import datetime, timedelta
from calculators.mundane.astronomy import (chart_at, forward_crossing, from_julian, julian, position, utc_naive, validate_location)

class LunationCalculator:
    """Calculates exact New Moons and Full Moons for monthly trend forecasting"""
    
    def calculate_lunations(self, start_date, end_date, latitude, longitude):
        """All new/full moons in [start, end). Naive datetimes are UTC."""
        start_date, end_date = utc_naive(start_date), utc_naive(end_date)
        if end_date < start_date:
            raise ValueError('End must not precede start')
        validate_location(latitude, longitude)
        lunations = []
        current = start_date
        while current < end_date:
            candidates = [self._find_next_syzygy(current, phase, latitude, longitude) for phase in (0, 180)]
            next_event = min(candidates, key=lambda row: row['datetime'])
            moment = datetime.fromisoformat(next_event['datetime'])
            if moment >= end_date:
                break
            lunations.append(next_event)
            current = moment + timedelta(seconds=1)
        # The actual next syzygy closes the half-cycle, not an arbitrary 14 days.
        for index, row in enumerate(lunations):
            if index + 1 < len(lunations):
                row['valid_until'] = lunations[index + 1]['datetime']
            else:
                next_phase = 180 if row['type'] == 'New Moon' else 0
                next_jd = self._syzygy_jd(datetime.fromisoformat(row['datetime']) + timedelta(seconds=1), next_phase)
                row['valid_until'] = from_julian(next_jd).isoformat()
        return lunations

    def _syzygy_jd(self, start_date, target_diff):
        return forward_crossing(julian(start_date),
            lambda jd: (position(jd, swe.MOON)[0] - position(jd, swe.SUN)[0]) % 360,
            target_diff, max_days=32)

    def _find_next_syzygy(self, start_date, target_diff, latitude, longitude):
        jd = self._syzygy_jd(start_date, target_diff)
        moment = from_julian(jd)
        sun, moon = position(jd, swe.SUN)[0], position(jd, swe.MOON)[0]
        kind = 'New Moon' if target_diff == 0 else 'Full Moon'
        out = {'type': kind, 'datetime': moment.isoformat(), 'datetime_utc': moment.isoformat() + 'Z',
               'timezone': 'UTC', 'sun_longitude': round(sun, 6), 'moon_longitude': round(moon, 6),
               'nakshatra': self._get_nakshatra(moon), 'chart': self._calculate_lunation_chart(moment, latitude, longitude),
               'paksha': 'Shukla' if target_diff == 0 else 'Krishna',
               'valid_until': from_julian(self._syzygy_jd(moment + timedelta(seconds=1), 180 if target_diff == 0 else 0)).isoformat()}
        eclipse = self._get_eclipse_visibility(jd, latitude, longitude, kind)
        if eclipse:
            out['eclipse_visibility'] = eclipse
        return out

    def _calculate_lunation_chart(self, dt, latitude, longitude):
        return chart_at(dt, latitude, longitude)

    def _calculate_house(self, planet_long: float, ascendant: float) -> int:
        asc_sign = int(ascendant / 30)
        planet_sign = int(planet_long / 30)
        return ((planet_sign - asc_sign) % 12) + 1
    
    def _get_nakshatra(self, longitude: float) -> Dict[str, Any]:
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        nakshatra_span = 360 / 27
        nak_index = int(longitude / nakshatra_span)
        pada = int((longitude % nakshatra_span) / (nakshatra_span / 4)) + 1
        
        return {
            'name': nakshatras[nak_index % 27],
            'pada': pada
        }

    def _get_eclipse_visibility(self, jd, lat, lon, lunation_type):
        """Global event identity plus local visibility over all eclipse phases."""
        geopos = (float(lon), float(lat), 0.0)
        try:
            solar = lunation_type == 'New Moon'
            global_result = (swe.sol_eclipse_when_glob(jd - 1, swe.FLG_SWIEPH) if solar
                             else swe.lun_eclipse_when(jd - 1, swe.FLG_SWIEPH))
            if global_result[0] <= 0 or abs(global_result[1][0] - jd) > 1.5:
                return {}
            local_result = (swe.sol_eclipse_when_loc(jd - 1, geopos, swe.FLG_SWIEPH) if solar
                            else swe.lun_eclipse_when_loc(jd - 1, geopos, swe.FLG_SWIEPH))
            visible = bool(local_result[0] > 0 and abs(local_result[1][0] - global_result[1][0]) < 1)
            attr = local_result[2] if visible else ()
            magnitude = (attr[8] if solar else max(attr[0], attr[1])) if attr else 0.0
            return {'is_eclipse': True, 'eclipse_type': 'solar' if solar else 'lunar',
                    'visible_from_location': visible, 'magnitude_at_location': round(magnitude, 4),
                    'magnitude_kind': 'solar' if solar else 'maximum_of_umbral_and_penumbral',
                    'maximum_datetime_utc': from_julian(global_result[1][0]).isoformat() + 'Z',
                    'note': 'Visibility is evaluated across the local eclipse phases, including rise/set.'}
        except swe.Error as exc:
            return {'available': False, 'reason': 'eclipse_calculation_failed'}
