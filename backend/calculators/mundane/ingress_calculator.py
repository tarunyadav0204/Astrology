"""Lahiri sidereal solar ingresses occurring within a civil UTC year."""
from datetime import datetime
import swisseph as swe
from calculators.mundane.astronomy import chart_at, forward_crossing, from_julian, julian, position, validate_location


class IngressCalculator:
    def calculate_yearly_ingresses(self, year, latitude, longitude):
        validate_location(latitude, longitude)
        ingresses = {name: self._find_ingress(year, degree, latitude, longitude)
                     for name, degree in [('Aries', 0), ('Cancer', 90), ('Libra', 180), ('Capricorn', 270)]}
        return {'year': year, 'ingresses': ingresses,
                'aries_ingress_chart': self._calculate_ingress_chart(ingresses['Aries'], latitude, longitude),
                'calculation_basis': {'timezone': 'UTC', 'zodiac': 'sidereal', 'ayanamsha': 'lahiri'}}

    def _find_ingress(self, year, target_longitude, latitude, longitude):
        start = julian(datetime(year, 1, 1))
        jd = forward_crossing(start, lambda t: position(t, swe.SUN)[0], target_longitude, max_days=366)
        dt = from_julian(jd)
        if dt.year != year:
            raise ValueError('Ingress lies outside requested calendar year')
        return {'datetime': dt.isoformat(), 'sun_longitude': round(position(jd, swe.SUN)[0], 6),
                'sign': self._get_sign_name(int(target_longitude / 30)), 'timezone': 'UTC',
                'datetime_utc': dt.isoformat() + 'Z'}

    def _calculate_ingress_chart(self, ingress_data, latitude, longitude):
        return {**chart_at(datetime.fromisoformat(ingress_data['datetime']), latitude, longitude),
                'datetime': ingress_data['datetime']}

    def _calculate_house(self, planet_long, ascendant):
        return (int((planet_long % 360) / 30) - int((ascendant % 360) / 30)) % 12 + 1

    def _get_sign_name(self, sign_num):
        return ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra',
                'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'][sign_num % 12]
