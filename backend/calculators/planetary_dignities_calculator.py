from .base_calculator import BaseCalculator
from .classical_combustion import calculate_chart_combustion
from .classical_functional_nature import calculate_functional_nature
from .classical_natural_nature import calculate_natural_nature
from .nakshatra_remedy_calculator import NakshatraRemedyCalculator
from .yogi_calculator import YogiCalculator
from marriage_matching.constants import NAKSHATRA_GANA, NAKSHATRA_NADI, NAKSHATRA_YONI
from vedic_predictions.config.nakshatra_data import NAKSHATRA_DATA
from vedic_predictions.config.planetary_dignity import NATURAL_ENEMIES, NATURAL_FRIENDS


SIGN_NAMES = (
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
)
SIGN_ABBR = ('Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi')
SIGN_LORDS = (
    'Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury',
    'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter',
)
NAKSHATRAS = (
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
)
NAKSHATRA_LORDS = (
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
    'Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury',
)
NAKSHATRA_NATURE_CLASSES = (
    'kshipra', 'ugra', 'mishra', 'dhruva', 'mridu', 'tikshna',
    'chara', 'kshipra', 'tikshna', 'ugra', 'ugra', 'dhruva',
    'kshipra', 'mridu', 'chara', 'mishra', 'mridu', 'tikshna',
    'tikshna', 'ugra', 'dhruva', 'chara', 'chara', 'chara',
    'ugra', 'dhruva', 'mridu',
)
PURUSHARTHAS = ('dharma', 'artha', 'kama', 'moksha')
VIMSHOTTARI_YEARS = {
    'Ketu': 7, 'Venus': 20, 'Sun': 6, 'Moon': 10, 'Mars': 7,
    'Rahu': 18, 'Jupiter': 16, 'Saturn': 19, 'Mercury': 17,
}
PLANET_ORDER = ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu', 'Gulika', 'Mandi')
TENANT_PLANETS = frozenset(('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'))
PLANET_ABBR = {
    'Lagna': 'Lg', 'Sun': 'Su', 'Moon': 'Mo', 'Mars': 'Ma', 'Mercury': 'Me',
    'Jupiter': 'Ju', 'Venus': 'Ve', 'Saturn': 'Sa', 'Rahu': 'Ra', 'Ketu': 'Ke',
    'Gulika': 'Gu', 'Mandi': 'Md', 'InduLagna': 'IL',
}
class PlanetaryDignitiesCalculator(BaseCalculator):
    """Extract planetary dignities calculation from planetary_dignities.py"""
    
    def __init__(self, chart_data=None):
        super().__init__(chart_data or {})
        
        self.EXALTATION_DATA = {
            'Sun': {'sign': 0, 'degree': 10}, 'Moon': {'sign': 1, 'degree': 3},
            'Mars': {'sign': 9, 'degree': 28}, 'Mercury': {'sign': 5, 'degree': 15},
            'Jupiter': {'sign': 3, 'degree': 5}, 'Venus': {'sign': 11, 'degree': 27},
            'Saturn': {'sign': 6, 'degree': 20}
        }
        
        self.DEBILITATION_DATA = {
            'Sun': {'sign': 6, 'degree': 10}, 'Moon': {'sign': 7, 'degree': 3},
            'Mars': {'sign': 3, 'degree': 28}, 'Mercury': {'sign': 11, 'degree': 15},
            'Jupiter': {'sign': 9, 'degree': 5}, 'Venus': {'sign': 5, 'degree': 27},
            'Saturn': {'sign': 0, 'degree': 20}
        }
        
        self.OWN_SIGNS = {
            'Sun': [4], 'Moon': [3], 'Mars': [0, 7], 'Mercury': [2, 5],
            'Jupiter': [8, 11], 'Venus': [1, 6], 'Saturn': [9, 10]
        }
        
        self.MOOLATRIKONA_DATA = {
            'Sun': {'sign': 4, 'start_degree': 0, 'end_degree': 20},
            'Moon': {'sign': 1, 'start_degree': 4, 'end_degree': 30},
            'Mars': {'sign': 0, 'start_degree': 0, 'end_degree': 12},
            'Mercury': {'sign': 5, 'start_degree': 16, 'end_degree': 20},
            'Jupiter': {'sign': 8, 'start_degree': 0, 'end_degree': 10},
            'Venus': {'sign': 6, 'start_degree': 0, 'end_degree': 15},
            'Saturn': {'sign': 10, 'start_degree': 0, 'end_degree': 20}
        }
        

    def calculate_planetary_dignities(self):
        """Calculate comprehensive planetary dignities"""
        planets = self.chart_data.get('planets', {})
        ascendant_sign = int(self.chart_data.get('ascendant', 0) / 30)
        dignities = {}
        combustion_rows = calculate_chart_combustion(self.chart_data)["planets"]
        
        for planet_name, planet_data in planets.items():
            if planet_name in ['Gulika', 'Mandi']:
                continue
            
            planet_sign = planet_data.get('sign', 0)
            planet_degree = planet_data.get('degree', 0)
            planet_longitude = planet_data.get('longitude', 0)
            is_retrograde = planet_data.get('retrograde', False)
            
            functional = calculate_functional_nature(ascendant_sign, planet_name)
            natural = calculate_natural_nature(self.chart_data, planet_name)
            dignity_info = {
                'planet': planet_name,
                'sign': planet_sign,
                'degree': round(planet_degree, 2),
                'dignity': self._calculate_dignity(planet_name, planet_sign, planet_degree),
                'functional_nature': functional['functional_nature'],
                'functional_nature_details': functional,
                'natural_nature': natural['nature'],
                'natural_nature_details': natural,
                'combustion_status': 'normal',
                'combustion': combustion_rows.get(planet_name),
                'retrograde': is_retrograde,
                'strength_multiplier': 1.0,
                'states': []
            }
            
            combustion = combustion_rows.get(planet_name) or {}
            dignity_info['combustion_status'] = 'combust' if combustion.get('is_combust') else 'normal'
            
            # Calculate strength multiplier
            dignity_info['strength_multiplier'] = self._calculate_strength_multiplier(dignity_info)
            dignity_info['states'] = self._compile_states(dignity_info)
            
            dignities[planet_name] = dignity_info
        
        return dignities

    @staticmethod
    def _normalise_longitude(value):
        try:
            return float(value) % 360.0
        except (TypeError, ValueError):
            return None

    @classmethod
    def _longitude_of(cls, row):
        if isinstance(row, (int, float)):
            return cls._normalise_longitude(row)
        if not isinstance(row, dict):
            return None
        longitude = cls._normalise_longitude(row.get('longitude'))
        if longitude is not None:
            return longitude
        try:
            return cls._normalise_longitude(int(row['sign']) * 30.0 + float(row['degree']))
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _degree_text(value):
        try:
            wrapped = float(value) % 30.0
        except (TypeError, ValueError):
            return '—'
        degrees = int(wrapped)
        minutes = int((wrapped - degrees) * 60.0)
        return f"{degrees}°{minutes:02d}'"

    @staticmethod
    def _nakshatra(longitude):
        span = 360.0 / 27.0
        pada_span = span / 4.0
        index = min(26, int((longitude % 360.0) / span))
        degree_in_nakshatra = (longitude % 360.0) - index * span
        return {
            'index': index,
            'name': NAKSHATRAS[index],
            'lord': NAKSHATRA_LORDS[index],
            'pada': min(4, int(degree_in_nakshatra / pada_span) + 1),
            'degree_in_nakshatra': round(degree_in_nakshatra, 8),
        }

    @staticmethod
    def _nakshatra_metadata(index):
        """Stable chart-reference metadata; interpretation remains outside this table."""
        number = int(index) + 1
        catalog = NAKSHATRA_DATA.get(number) or {}
        remedy = NakshatraRemedyCalculator.NAKSHATRA_DATA.get(NAKSHATRAS[index]) or {}
        return {
            'deity': catalog.get('deity') or remedy.get('devata'),
            'symbol': catalog.get('symbol'),
            'shakti': remedy.get('shakti'),
            'nature_class': NAKSHATRA_NATURE_CLASSES[index],
            'purushartha': PURUSHARTHAS[index % 4],
            'gana': NAKSHATRA_GANA.get(number),
            'nadi': NAKSHATRA_NADI.get(number),
            'yoni': NAKSHATRA_YONI.get(number),
            'sources': [
                'Taittiriya Brahmana — Nakshatra deities',
                'Brihat Samhita and the classical Muhurta tradition — Nakshatra action classes',
                'Traditional Ashtakoota tables — Gana, Nadi and Yoni',
            ],
        }

    @staticmethod
    def _pada_details(nakshatra, longitude):
        nak_span = 360.0 / 27.0
        pada_span = nak_span / 4.0
        degree_in_nakshatra = float(nakshatra['degree_in_nakshatra'])
        pada = int(nakshatra['pada'])
        start = (pada - 1) * pada_span
        end = pada * pada_span
        navamsa_sign = PlanetaryDignitiesCalculator._navamsa_sign(longitude)
        return {
            'number': pada,
            'start_degree_in_nakshatra': round(start, 8),
            'end_degree_in_nakshatra': round(end, 8),
            'degree_in_pada': round(degree_in_nakshatra - start, 8),
            'navamsa_sign': navamsa_sign,
            'navamsa_sign_name': SIGN_NAMES[navamsa_sign],
            'navamsa_lord': SIGN_LORDS[navamsa_sign],
            'purushartha': PURUSHARTHAS[(pada - 1) % 4],
        }

    @staticmethod
    def _vimshottari_birth_balance(nakshatra):
        lord = nakshatra['lord']
        span = 360.0 / 27.0
        elapsed = max(0.0, min(1.0, float(nakshatra['degree_in_nakshatra']) / span))
        total_years = VIMSHOTTARI_YEARS[lord]
        remaining_years = total_years * (1.0 - elapsed)
        return {
            'starting_lord': lord,
            'full_period_years': total_years,
            'elapsed_fraction': round(elapsed, 10),
            'remaining_fraction': round(1.0 - elapsed, 10),
            'remaining_years': round(remaining_years, 8),
            'remaining_days_approx': round(remaining_years * 365.25, 2),
            'method': 'Vimshottari balance from the untraversed portion of the natal Moon Nakshatra',
        }

    @staticmethod
    def _natural_relationship(planet, other):
        if planet not in NATURAL_FRIENDS or other not in NATURAL_FRIENDS:
            return {'key': 'traditionDependent', 'labelKey': 'traditionDependent', 'label': 'Tradition-dependent'}
        if planet == other:
            return {'key': 'self', 'labelKey': 'self', 'label': 'Own lord'}
        if other in NATURAL_FRIENDS[planet]:
            return {'key': 'friend', 'labelKey': 'friend', 'label': 'Natural friend'}
        if other in NATURAL_ENEMIES[planet]:
            return {'key': 'enemy', 'labelKey': 'enemy', 'label': 'Natural enemy'}
        return {'key': 'neutral', 'labelKey': 'neutral', 'label': 'Natural neutral'}

    @staticmethod
    def _navamsa_sign(longitude):
        sign = int(longitude / 30.0) % 12
        part = int((longitude % 30.0) / (30.0 / 9.0))
        if sign in {0, 3, 6, 9}:
            return (sign + part) % 12
        if sign in {1, 4, 7, 10}:
            return (sign + 8 + part) % 12
        return (sign + 4 + part) % 12

    @staticmethod
    def _dignity_display(planet, dignity):
        if planet in {'Rahu', 'Ketu', 'Gulika', 'Mandi'}:
            return {'key': 'notGraded', 'labelKey': 'notGraded', 'label': 'Not classically graded', 'short': '—'}
        rows = {
            'exalted': ('ex', 'exalted', 'Exalted', 'Ex'),
            'debilitated': ('db', 'debilitated', 'Debilitated', 'Db'),
            'moolatrikona': ('mt', 'moolatrikona', 'Moolatrikona', 'MT'),
            'own_sign': ('own', 'ownSign', 'Own sign', 'Own'),
        }
        key, label_key, label, short = rows.get(
            dignity, ('ordinary', 'ordinary', 'Ordinary dignity', '—')
        )
        return {'key': key, 'labelKey': label_key, 'label': label, 'short': short}

    @staticmethod
    def _dms(value):
        value = float(value) % 30.0
        degrees = int(value)
        minutes_float = (value - degrees) * 60.0
        minutes = int(minutes_float)
        seconds = round((minutes_float - minutes) * 60.0, 2)
        return {'degrees': degrees, 'minutes': minutes, 'seconds': seconds,
                'text': f'{degrees}°{minutes:02d}\'{seconds:05.2f}"'}

    @staticmethod
    def _circular_distance(first, second):
        return abs((float(first) - float(second) + 180.0) % 360.0 - 180.0)

    @staticmethod
    def _temporary_relationship(first_sign, second_sign):
        distance = ((int(second_sign) - int(first_sign)) % 12) + 1
        is_friend = distance in {2, 3, 4, 10, 11, 12}
        return {
            'key': 'temporaryFriend' if is_friend else 'temporaryEnemy',
            'labelKey': 'temporaryFriend' if is_friend else 'temporaryEnemy',
            'label': 'Temporary friend' if is_friend else 'Temporary enemy',
            'house_distance': distance,
        }

    @staticmethod
    def _compound_relationship(natural, temporary):
        natural_key = (natural or {}).get('key')
        temporary_friend = (temporary or {}).get('key') == 'temporaryFriend'
        if natural_key in {'self', 'friend'} and temporary_friend:
            key, label = 'greatFriend', 'Great friend'
        elif natural_key == 'enemy' and not temporary_friend:
            key, label = 'greatEnemy', 'Great enemy'
        elif natural_key in {'self', 'friend'} and not temporary_friend:
            key, label = 'neutral', 'Neutral'
        elif natural_key == 'enemy' and temporary_friend:
            key, label = 'neutral', 'Neutral'
        elif natural_key == 'neutral' and temporary_friend:
            key, label = 'friend', 'Friend'
        elif natural_key == 'neutral':
            key, label = 'enemy', 'Enemy'
        else:
            key, label = 'traditionDependent', 'Tradition-dependent'
        return {'key': key, 'labelKey': key, 'label': label}

    @staticmethod
    def _baladi_avastha(degree, sign):
        segment = min(4, int((float(degree) % 30.0) / 6.0))
        forward = ('bala', 'kumara', 'yuva', 'vriddha', 'mrita')
        key = forward[segment] if int(sign) % 2 == 0 else tuple(reversed(forward))[segment]
        strengths = {'bala': 25, 'kumara': 50, 'yuva': 100, 'vriddha': 50, 'mrita': 0}
        return {'key': key, 'labelKey': key, 'strength_percent': strengths[key],
                'method': 'BPHS Baladi Avastha; 6-degree divisions, reversed in even signs'}

    @staticmethod
    def _navatara(planet_nakshatra, moon_nakshatra):
        sequence = ('janma', 'sampat', 'vipat', 'kshema', 'pratyari',
                    'sadhaka', 'naidhana', 'mitra', 'paramaMitra')
        count = ((int(planet_nakshatra) - int(moon_nakshatra)) % 27) + 1
        key = sequence[(count - 1) % 9]
        return {'key': key, 'labelKey': key, 'count_from_birth_nakshatra': count,
                'cycle': ((count - 1) // 9) + 1}

    @staticmethod
    def _boundary_proximity(longitude):
        longitude = float(longitude) % 360.0
        degree = longitude % 30.0
        rashi_distance = min(degree, 30.0 - degree)
        nak_span = 360.0 / 27.0
        within_nak = longitude % nak_span
        nak_distance = min(within_nak, nak_span - within_nak)
        nak_index = min(26, int(longitude / nak_span))
        return {
            'rashi_degrees': round(rashi_distance, 6),
            'nakshatra_degrees': round(nak_distance, 6),
            'near_rashi_boundary': rashi_distance <= 1.0,
            'near_nakshatra_boundary': nak_distance <= 1.0,
            'degrees_from_nakshatra_start': round(within_nak, 6),
            'degrees_to_nakshatra_end': round(nak_span - within_nak, 6),
            'previous_nakshatra': NAKSHATRAS[(nak_index - 1) % 27],
            'next_nakshatra': NAKSHATRAS[(nak_index + 1) % 27],
        }

    @staticmethod
    def _gandanta(longitude):
        junctions = ((0.0, 'revatiAshwini'), (120.0, 'ashleshaMagha'),
                     (240.0, 'jyeshthaMula'))
        distance, key = min(
            ((abs((float(longitude) - point + 180.0) % 360.0 - 180.0), key)
             for point, key in junctions), key=lambda item: item[0]
        )
        return {'is_gandanta': distance <= (10.0 / 3.0), 'junction_key': key,
                'distance_degrees': round(distance, 6),
                'range_degrees_each_side': round(10.0 / 3.0, 6)}

    @staticmethod
    def _pushkara(sign, degree):
        # Two Pushkara Navamshas per sign.  Values are navamsha numbers within
        # the Rashi (1..9), as used by the existing classical degree service.
        element_map = {0: (7, 9), 1: (3, 5), 2: (6, 8), 3: (1, 3)}
        bhaga = (21, 14, 21, 7, 14, 24, 14, 11, 24, 21, 24, 23)[int(sign)]
        navamsa_number = min(9, int((float(degree) % 30.0) / (10.0 / 3.0)) + 1)
        distance = abs((float(degree) % 30.0) - bhaga)
        return {
            'is_pushkara_navamsa': navamsa_number in element_map[int(sign) % 4],
            'navamsa_number': navamsa_number,
            'is_pushkara_bhaga': distance <= 1.0,
            'pushkara_bhaga_degree': bhaga,
            'distance_from_pushkara_bhaga': round(distance, 6),
            'pushkara_bhaga_orb': 1.0,
        }

    def calculate_position_tables(self, condition_chart_data=None, dignities=None, birth_data=None):
        """Canonical placement tables consumed by the mobile Positions screen.

        ``chart_data`` supplies the chart being displayed.  ``condition_chart``
        supplies natal/transit conditions such as combustion and Neecha Bhanga,
        preserving the existing UI's deliberate selected-chart distinction.
        """
        chart = self.chart_data
        condition_chart = condition_chart_data if isinstance(condition_chart_data, dict) else chart
        dignities = dignities or self.calculate_planetary_dignities()
        condition_combustion = calculate_chart_combustion(condition_chart).get('planets', {})
        display_planets = chart.get('planets') if isinstance(chart.get('planets'), dict) else {}
        condition_planets = condition_chart.get('planets') if isinstance(condition_chart.get('planets'), dict) else {}
        ascendant = self._normalise_longitude(chart.get('ascendant'))
        lagna_sign = int(ascendant / 30.0) % 12 if ascendant is not None else 0
        bhav_planets = ((chart.get('bhav_chalit') or {}).get('planets') or {})
        moon_longitude = self._longitude_of(display_planets.get('Moon') or {})
        moon_nakshatra = self._nakshatra(moon_longitude)['index'] if moon_longitude is not None else None

        # Whole-sign Parashari aspects.  Node fifth/ninth aspects are omitted
        # because the user selected the conservative, non-debated convention.
        aspect_numbers = {
            'Sun': (7,), 'Moon': (7,), 'Mars': (4, 7, 8),
            'Mercury': (7,), 'Jupiter': (5, 7, 9), 'Venus': (7,),
            'Saturn': (3, 7, 10), 'Rahu': (7,), 'Ketu': (7,),
        }

        condition_rows = {}
        for p_name, p_data in condition_planets.items():
            if isinstance(p_data, dict):
                p_long = self._longitude_of(p_data)
                if p_long is not None:
                    condition_rows[p_name] = {
                        'data': p_data, 'longitude': p_long,
                        'sign': int(p_data.get('sign', p_long / 30.0)) % 12,
                    }

        display_rows = {}
        for p_name, p_data in display_planets.items():
            if isinstance(p_data, dict):
                p_long = self._longitude_of(p_data)
                if p_long is not None:
                    display_rows[p_name] = {
                        'data': p_data, 'longitude': p_long,
                        'sign': int(p_data.get('sign', p_long / 30.0)) % 12,
                    }

        def aspects_for(name, sign):
            cast = []
            for number in aspect_numbers.get(name, ()):
                target_sign = (sign + number - 1) % 12
                target_house = ((target_sign - lagna_sign) % 12) + 1
                targets = [p for p, item in display_rows.items()
                           if p != name and item['sign'] == target_sign]
                cast.append({'aspect_number': number, 'target_sign': target_sign,
                             'target_house': target_house, 'planets': targets})
            received = []
            for other, item in display_rows.items():
                if other == name:
                    continue
                hits = [n for n in aspect_numbers.get(other, ())
                        if (item['sign'] + n - 1) % 12 == sign]
                if hits:
                    received.append({'planet': other, 'aspect_numbers': hits,
                                     'from_house': int(item['data'].get('house') or ((item['sign'] - lagna_sign) % 12) + 1)})
            return {'cast': cast, 'received': received,
                    'method': 'Parashari whole-sign graha drishti; nodes use the seventh aspect only'}

        def conjunctions_for(name, longitude, sign):
            rows = []
            for other, item in display_rows.items():
                if other == name or item['sign'] != sign:
                    continue
                rows.append({'planet': other,
                             'separation_degrees': round(self._circular_distance(longitude, item['longitude']), 6)})
            return sorted(rows, key=lambda row: row['separation_degrees'])

        def relationship_bundle(name, other):
            natural = self._natural_relationship(name, other)
            if name == other:
                return {'natural': natural, 'temporary': None, 'compound': natural}
            first = display_rows.get(name)
            second = display_rows.get(other)
            if not first or not second or natural.get('key') == 'traditionDependent':
                return {'natural': natural, 'temporary': None,
                        'compound': {'key': 'traditionDependent', 'labelKey': 'traditionDependent', 'label': 'Tradition-dependent'}}
            temporary = self._temporary_relationship(first['sign'], second['sign'])
            return {'natural': natural, 'temporary': temporary,
                    'compound': self._compound_relationship(natural, temporary)}

        def row_for(name, data, *, is_lagna=False):
            longitude = self._longitude_of(data)
            if longitude is None:
                return None
            sign = int(longitude / 30.0) % 12 if is_lagna else int(data.get('sign', longitude / 30.0)) % 12
            degree = longitude % 30.0
            nakshatra = self._nakshatra(longitude)
            lord = SIGN_LORDS[sign]
            condition_data = condition_planets.get(name) if isinstance(condition_planets.get(name), dict) else data
            condition_longitude = self._longitude_of(condition_data)
            condition_sign = (
                int(condition_data.get('sign', condition_longitude / 30.0)) % 12
                if isinstance(condition_data, dict) and condition_longitude is not None else sign
            )
            dignity_key = (dignities.get(name) or {}).get('dignity') if not is_lagna else None
            combustion = condition_combustion.get(name) if not is_lagna else None
            bhav_row = bhav_planets.get(name) if isinstance(bhav_planets.get(name), dict) else None
            sign_relationships = None if is_lagna else relationship_bundle(name, lord)
            nak_relationships = None if is_lagna else relationship_bundle(name, nakshatra['lord'])
            speed = None if is_lagna else data.get('speed')
            motion = None
            if not is_lagna:
                if name in {'Rahu', 'Ketu'}:
                    motion = {'key': 'retrograde', 'speed_degrees_per_day': speed,
                              'near_station': False}
                elif speed is None:
                    motion = {'key': 'retrograde' if data.get('retrograde') else 'direct',
                              'speed_degrees_per_day': None, 'near_station': None}
                else:
                    motion = {'key': 'stationary' if abs(float(speed)) < 0.0001 else ('retrograde' if float(speed) < 0 else 'direct'),
                              'speed_degrees_per_day': round(float(speed), 8),
                              'near_station': abs(float(speed)) < 0.0001}
            exaltation = self.EXALTATION_DATA.get(name)
            debilitation = self.DEBILITATION_DATA.get(name)
            deep_point = None
            if exaltation and sign == exaltation['sign']:
                deep_point = {'type': 'exaltation', 'exact_degree': exaltation['degree'],
                              'distance_degrees': round(abs(degree - exaltation['degree']), 6)}
            elif debilitation and sign == debilitation['sign']:
                deep_point = {'type': 'debilitation', 'exact_degree': debilitation['degree'],
                              'distance_degrees': round(abs(degree - debilitation['degree']), 6)}
            sign_dispositor = display_rows.get(lord)
            nak_dispositor = display_rows.get(nakshatra['lord'])
            def dispositor_summary(dispositor_name, item):
                if not item:
                    return {'planet': dispositor_name, 'available': False}
                d_info = dignities.get(dispositor_name) or {}
                d_comb = condition_combustion.get(dispositor_name) or {}
                return {'planet': dispositor_name, 'available': True,
                        'house': int(item['data'].get('house') or ((item['sign'] - lagna_sign) % 12) + 1),
                        'sign': item['sign'], 'dignity': self._dignity_display(dispositor_name, d_info.get('dignity')),
                        'retrograde': bool(item['data'].get('retrograde')),
                        'combust': bool(d_comb.get('is_combust'))}
            return {
                'name': name,
                'abbr': PLANET_ABBR.get(name, name[:2]),
                'sign': sign,
                'sign_name': SIGN_NAMES[sign],
                'sign_abbr': SIGN_ABBR[sign],
                'sign_lord': lord,
                'sign_lord_abbr': PLANET_ABBR.get(lord, lord[:2]),
                'sign_lord_relationship': None if is_lagna else self._natural_relationship(name, lord),
                'house': 1 if is_lagna else int(data.get('house') or ((sign - lagna_sign) % 12) + 1),
                'longitude': round(longitude, 10),
                'degree': round(degree, 10),
                'degree_text': self._degree_text(degree),
                'degree_dms': self._dms(degree),
                'nakshatra_index': nakshatra['index'],
                'nakshatra': nakshatra['name'],
                'pada': nakshatra['pada'],
                'degree_in_nakshatra': nakshatra['degree_in_nakshatra'],
                'degree_in_nakshatra_dms': self._dms(nakshatra['degree_in_nakshatra']),
                'pada_details': self._pada_details(nakshatra, longitude),
                'nakshatra_metadata': self._nakshatra_metadata(nakshatra['index']),
                'nakshatra_lord': nakshatra['lord'],
                'nakshatra_lord_relationship': None if is_lagna else self._natural_relationship(name, nakshatra['lord']),
                'retrograde': False if is_lagna or name in {'Rahu', 'Ketu'} else bool(data.get('retrograde')),
                'combust': bool((combustion or {}).get('is_combust')),
                'combustion': combustion,
                'neecha_bhanga': bool((condition_data or {}).get('neecha_bhanga')) if isinstance(condition_data, dict) else False,
                'vargottama': bool(
                    not is_lagna
                    and condition_longitude is not None
                    and condition_sign == self._navamsa_sign(condition_longitude)
                ),
                'dignity': None if is_lagna else self._dignity_display(name, dignity_key),
                'rashi_house': 1 if is_lagna else int(data.get('house') or ((sign - lagna_sign) % 12) + 1),
                'bhava_chalit_house': 1 if is_lagna else (int(bhav_row.get('house')) if bhav_row and bhav_row.get('house') else None),
                'friendships': None if is_lagna else {'sign_lord': sign_relationships, 'nakshatra_lord': nak_relationships},
                'dispositors': None if is_lagna else {
                    'sign': dispositor_summary(lord, sign_dispositor),
                    'nakshatra': dispositor_summary(nakshatra['lord'], nak_dispositor),
                },
                'aspects': None if is_lagna else aspects_for(name, sign),
                'conjunctions': [] if is_lagna else conjunctions_for(name, longitude, sign),
                'baladi_avastha': None if is_lagna or name in {'Rahu', 'Ketu', 'Gulika', 'Mandi'} else self._baladi_avastha(degree, sign),
                'deep_point': deep_point,
                'motion': motion,
                'boundary_proximity': self._boundary_proximity(longitude),
                'gandanta': self._gandanta(longitude),
                'pushkara': None if is_lagna or name in {'Rahu', 'Ketu', 'Gulika', 'Mandi'} else self._pushkara(sign, degree),
                'navatara': None if is_lagna or moon_nakshatra is None else self._navatara(nakshatra['index'], moon_nakshatra),
                'vimshottari_birth_balance': self._vimshottari_birth_balance(nakshatra) if name == 'Moon' else None,
            }

        ascendant_row = row_for('Lagna', {'longitude': ascendant}, is_lagna=True) if ascendant is not None else None
        planet_rows = []
        for name in PLANET_ORDER:
            data = display_planets.get(name)
            if isinstance(data, dict):
                row = row_for(name, data)
                if row:
                    planet_rows.append(row)

        occupants = {house: [] for house in range(1, 13)}
        for row in planet_rows:
            if row['name'] not in TENANT_PLANETS:
                continue
            occupants[row['house']].append({
                'name': row['name'], 'retrograde': row['retrograde'],
                'combust': row['combust'],
            })

        planet_rows_by_name = {row['name']: row for row in planet_rows}

        def houses_owned_by(planet_name):
            return [
                house for house in range(1, 13)
                if SIGN_LORDS[(lagna_sign + house - 1) % 12] == planet_name
            ]

        def nakshatra_lord_state_for(row):
            lord_name = row['nakshatra_lord']
            lord_row = planet_rows_by_name.get(lord_name)
            if not lord_row:
                return {'planet': lord_name, 'available': False, 'houses_owned': houses_owned_by(lord_name)}
            dignity = dignities.get(lord_name) or {}
            return {
                'planet': lord_name,
                'available': True,
                'house': lord_row['house'],
                'sign': lord_row['sign'],
                'sign_name': lord_row['sign_name'],
                'nakshatra': lord_row['nakshatra'],
                'nakshatra_lord': lord_row['nakshatra_lord'],
                'houses_owned': houses_owned_by(lord_name),
                'dignity': lord_row['dignity'],
                'retrograde': lord_row['retrograde'],
                'combust': lord_row['combust'],
                'neecha_bhanga': lord_row['neecha_bhanga'],
                'vargottama': lord_row['vargottama'],
                'natural_nature': dignity.get('natural_nature'),
                'functional_nature': dignity.get('functional_nature'),
                'friendships': lord_row.get('friendships'),
                'motion': lord_row.get('motion'),
                'conjunctions': lord_row.get('conjunctions') or [],
                'aspects_received': ((lord_row.get('aspects') or {}).get('received') or []),
                'friendship_with_subject': row.get('nakshatra_lord_relationship'),
            }

        nakshatra_placements = []
        for row in ([ascendant_row] if ascendant_row else []) + [
            item for item in planet_rows if item['name'] in TENANT_PLANETS
        ]:
            placement = dict(row)
            placement['subject_type'] = 'lagna' if row['name'] == 'Lagna' else 'planet'
            placement['nakshatra_lord_state'] = nakshatra_lord_state_for(row)
            placement['special_roles'] = []
            nakshatra_placements.append(placement)

        yogi_role_status = {'status': 'unavailable', 'reason': 'natal_sun_moon_required'}
        yogi_sun = self._longitude_of(condition_planets.get('Sun') or {})
        yogi_moon = self._longitude_of(condition_planets.get('Moon') or {})
        if yogi_sun is not None and yogi_moon is not None:
            try:
                calculated_yogi = YogiCalculator._calculate_from_longitudes(yogi_sun, yogi_moon)
                yogi_point = calculated_yogi['yogi_point']
                avayogi_point = calculated_yogi['avayogi_point']
                yogi_details = YogiCalculator._nakshatra_details(yogi_point)
                avayogi_details = YogiCalculator._nakshatra_details(avayogi_point)
                role_planets = {
                    'yogi': yogi_details['nakshatra_lord'],
                    'duplicate_yogi': SIGN_LORDS[int(yogi_point / 30.0) % 12],
                    'avayogi': avayogi_details['nakshatra_lord'],
                }
                for placement in nakshatra_placements:
                    placement['special_roles'] = [
                        role for role, planet in role_planets.items()
                        if placement['name'] == planet
                    ]
                yogi_role_status = {
                    'status': 'available',
                    'calculation_basis': {
                        'version': 'classical-yogi/2.0.0',
                        'source': 'natal_chart_sidereal_longitudes',
                        'yogi_formula': 'Sun + Moon + 93°20′',
                        'avayogi_formula': 'Yogi point + 66°40′ (five nakshatras)',
                    },
                    'duplicate_yogi_avayogi_overlap': {
                        'is_active': role_planets['duplicate_yogi'] == role_planets['avayogi'],
                        'planet': role_planets['avayogi'] if role_planets['duplicate_yogi'] == role_planets['avayogi'] else None,
                    },
                }
            except Exception as exc:
                yogi_role_status = {'status': 'calculation_error', 'reason': str(exc)}

        def house_classifications(house):
            """Return overlapping classical house groups without grading them."""
            groups = []
            for key, houses in (
                ('kendra', {1, 4, 7, 10}),
                ('trikona', {1, 5, 9}),
                ('dusthana', {6, 8, 12}),
                ('upachaya', {3, 6, 10, 11}),
                ('panapara', {2, 5, 8, 11}),
                ('apoklima', {3, 6, 9, 12}),
                ('maraka', {2, 7}),
            ):
                if house in houses:
                    groups.append(key)
            return groups

        def professional_planet_state(row):
            if not row:
                return None
            dignity = dignities.get(row['name']) or {}
            return {
                'name': row['name'],
                'house': row['house'],
                'sign': row['sign'],
                'sign_name': row['sign_name'],
                'nakshatra': row['nakshatra'],
                'nakshatra_lord': row['nakshatra_lord'],
                'dignity': row['dignity'],
                'retrograde': row['retrograde'],
                'combust': row['combust'],
                'neecha_bhanga': row['neecha_bhanga'],
                'vargottama': row['vargottama'],
                'motion': row['motion'],
                'friendships': row['friendships'],
                'natural_nature': dignity.get('natural_nature'),
                'functional_nature': dignity.get('functional_nature'),
            }

        received_by_house = {house: [] for house in range(1, 13)}
        for planet_row in planet_rows:
            for aspect in (planet_row.get('aspects') or {}).get('cast', []):
                target_house = aspect.get('target_house')
                if target_house not in received_by_house:
                    continue
                received_by_house[target_house].append({
                    'planet': planet_row['name'],
                    'aspect_number': aspect['aspect_number'],
                    'from_house': planet_row['house'],
                    'dignity': planet_row['dignity'],
                    'retrograde': planet_row['retrograde'],
                    'combust': planet_row['combust'],
                    'natural_nature': (dignities.get(planet_row['name']) or {}).get('natural_nature'),
                    'functional_nature': (dignities.get(planet_row['name']) or {}).get('functional_nature'),
                })

        bhava_chalit_available = any(
            row.get('bhava_chalit_house') is not None for row in planet_rows
            if row['name'] in TENANT_PLANETS
        )
        bhava_chalit_occupants = {house: [] for house in range(1, 13)}
        bhava_chalit_changes = {house: [] for house in range(1, 13)}
        if bhava_chalit_available:
            for planet_row in planet_rows:
                if planet_row['name'] not in TENANT_PLANETS:
                    continue
                rashi_house = planet_row['rashi_house']
                chalit_house = planet_row.get('bhava_chalit_house') or rashi_house
                bhava_chalit_occupants[chalit_house].append(planet_row['name'])
                if rashi_house != chalit_house:
                    change = {
                        'planet': planet_row['name'],
                        'rashi_house': rashi_house,
                        'bhava_chalit_house': chalit_house,
                    }
                    bhava_chalit_changes[rashi_house].append(change)
                    bhava_chalit_changes[chalit_house].append(change)

        house_rows = []
        for index in range(12):
            house = index + 1
            supplied_house = (chart.get('houses') or [{}] * 12)[index] if len(chart.get('houses') or []) > index else {}
            sign = int(supplied_house.get('sign', (lagna_sign + index) % 12)) % 12
            lord = SIGN_LORDS[sign]
            lord_row = planet_rows_by_name.get(lord)
            house_rows.append({
                'house': house,
                'sign': sign,
                'sign_name': SIGN_NAMES[sign],
                'sign_abbr': SIGN_ABBR[sign],
                'lord': lord,
                'lord_abbr': PLANET_ABBR.get(lord, lord[:2]),
                'lord_house': lord_row['house'] if lord_row else None,
                'lord_dignity': lord_row['dignity'] if lord_row else None,
                'lord_combust': lord_row['combust'] if lord_row else False,
                'occupants': occupants[house],
                # Additive professional fields. Existing lightweight fields
                # above remain unchanged for older clients.
                'classifications': house_classifications(house),
                'lord_state': professional_planet_state(lord_row),
                'occupant_details': [
                    professional_planet_state(row)
                    for row in planet_rows
                    if row['name'] in TENANT_PLANETS and row['house'] == house
                ],
                'aspects_received': received_by_house[house],
                'bhava_chalit': {
                    'status': 'available' if bhava_chalit_available else 'unavailable',
                    'occupants': bhava_chalit_occupants[house],
                    'changes': bhava_chalit_changes[house],
                },
            })

        grouped = {}
        for row in ([ascendant_row] if ascendant_row else []) + planet_rows:
            index = row['nakshatra_index']
            group = grouped.setdefault(index, {
                'index': index, 'nakshatra': NAKSHATRAS[index],
                'lord': NAKSHATRA_LORDS[index], 'lord_abbr': PLANET_ABBR.get(NAKSHATRA_LORDS[index], NAKSHATRA_LORDS[index][:2]),
                'people': [],
            })
            group['people'].append({
                'name': row['name'], 'pada': row['pada'],
                'retrograde': row['retrograde'], 'retro': row['retrograde'],
                'combust': row['combust'],
            })

        indu_lagna = None
        if isinstance(display_planets.get('InduLagna'), dict):
            indu_lagna = row_for('InduLagna', display_planets['InduLagna'])

        # Graha Yuddha eligibility is displayed without an invented winner.
        war_planets = {'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'}
        wars = []
        for index, first in enumerate(planet_rows):
            if first['name'] not in war_planets:
                continue
            for second in planet_rows[index + 1:]:
                if second['name'] not in war_planets:
                    continue
                separation = self._circular_distance(first['longitude'], second['longitude'])
                if separation <= 1.0:
                    war = {'planet_1': first['name'], 'planet_2': second['name'],
                           'separation_degrees': round(separation, 6),
                           'winner': None, 'winner_status': 'notGraded',
                           'method': 'Classical Graha Yuddha eligibility: five non-luminary planets within one degree'}
                    wars.append(war)
                    first['graha_yuddha'] = war
                    second['graha_yuddha'] = war

        return {
            # Keep the established contract version: this release only adds
            # fields and the legacy tables remain byte-for-byte consumable.
            'schema_version': 'canonical-positions/2.0.0',
            'ayanamsha': 'Lahiri',
            'ascendant': ascendant_row,
            'planets': planet_rows,
            'houses': house_rows,
            'nakshatras': [grouped[index] for index in sorted(grouped)],
            'nakshatra_placements': nakshatra_placements,
            'nakshatra_special_role_status': yogi_role_status,
            'indu_lagna': indu_lagna,
            'graha_yuddha': wars,
        }
    
    def _calculate_dignity(self, planet, sign, degree=None):
        """Calculate planetary dignity"""
        if planet in ['Rahu', 'Ketu']:
            return self._calculate_rahu_ketu_dignity(planet, sign)
        
        # Moolatrikona is degree-bounded and must be resolved before the
        # broader exaltation/own-sign label in overlapping signs.
        if planet in self.MOOLATRIKONA_DATA:
            mool_data = self.MOOLATRIKONA_DATA[planet]
            if sign == mool_data['sign']:
                if degree is not None:
                    if mool_data['start_degree'] <= degree <= mool_data['end_degree']:
                        return 'moolatrikona'
                else:
                    return 'moolatrikona'

        if planet in self.EXALTATION_DATA:
            exalt_data = self.EXALTATION_DATA[planet]
            if sign == exalt_data['sign']:
                # Once an overlapping Moolatrikona range ends, the remainder
                # of an own sign stays own-sign rather than being flattened
                # into exaltation (notably Mercury in Virgo).
                mool_data = self.MOOLATRIKONA_DATA.get(planet)
                if (
                    mool_data and mool_data['sign'] == sign and degree is not None
                    and degree > mool_data['end_degree'] and sign in self.OWN_SIGNS.get(planet, [])
                ):
                    return 'own_sign'
                return 'exalted'

        if planet in self.DEBILITATION_DATA and sign == self.DEBILITATION_DATA[planet]['sign']:
            return 'debilitated'
        
        # Check own sign
        if planet in self.OWN_SIGNS:
            if sign in self.OWN_SIGNS[planet]:
                return 'own_sign'
        
        return 'neutral'
    
    def _calculate_rahu_ketu_dignity(self, planet, sign):
        """Calculate dignity for Rahu/Ketu"""
        if planet == 'Rahu':
            if sign in [2, 5, 6, 8, 11]:  # Gemini, Virgo, Libra, Sagittarius, Pisces
                return 'favorable'
            elif sign in [3, 4, 7]:  # Cancer, Leo, Scorpio
                return 'unfavorable'
        elif planet == 'Ketu':
            if sign in [8, 11, 7]:  # Sagittarius, Pisces, Scorpio
                return 'favorable'
            elif sign in [2, 5, 6]:  # Gemini, Virgo, Libra
                return 'unfavorable'
        return 'neutral'
    
    def _calculate_functional_nature(self, planet, ascendant_sign):
        """Compatibility wrapper for callers of the former private method."""
        return calculate_functional_nature(ascendant_sign, planet)['functional_nature']
    
    def _calculate_strength_multiplier(self, dignity_info):
        """Calculate overall strength multiplier"""
        multiplier = 1.0
        
        dignity_multipliers = {
            'exalted': 1.5, 'moolatrikona': 1.3, 'own_sign': 1.2,
            'favorable': 1.2, 'unfavorable': 0.8, 'debilitated': 0.6
        }
        multiplier *= dignity_multipliers.get(dignity_info['dignity'], 1.0)
        
        if dignity_info['functional_nature'] == 'benefic':
            multiplier *= 1.2
        
        # Combustion is preserved as structured classical evidence.  No
        # arbitrary numeric multiplier is claimed by the selected source.
        
        if dignity_info['retrograde'] and dignity_info['planet'] not in ['Jupiter', 'Venus']:
            multiplier *= 0.9
        
        return round(multiplier, 2)
    
    def _compile_states(self, dignity_info):
        """Compile all planetary states"""
        states = []
        
        if dignity_info['dignity'] != 'neutral':
            states.append(dignity_info['dignity'].title())
        
        if dignity_info['functional_nature'] == 'benefic':
            states.append('Functional Benefic')
        
        if dignity_info['combustion_status'] == 'combust':
            states.append('Combust')

        if dignity_info['retrograde']:
            states.append('Retrograde')
        
        return states


def attach_canonical_position_states(chart_data):
    """Attach canonical display states to an existing chart payload."""
    if not isinstance(chart_data, dict) or not isinstance(chart_data.get('planets'), dict):
        return chart_data
    calculator = PlanetaryDignitiesCalculator(chart_data)
    dignity_rows = calculator.calculate_planetary_dignities()
    positions = calculator.calculate_position_tables(chart_data, dignities=dignity_rows)
    canonical_by_planet = {row['name']: row for row in positions.get('planets', [])}
    for planet_name, planet_data in chart_data['planets'].items():
        if not isinstance(planet_data, dict):
            continue
        canonical = canonical_by_planet.get(planet_name)
        if not canonical:
            continue
        dignity = dignity_rows.get(planet_name) or {}
        planet_data['dignity'] = dignity.get('dignity')
        planet_data['vargottama'] = canonical.get('vargottama', False)
        planet_data['nakshatra'] = canonical.get('nakshatra')
        planet_data['nakshatra_pada'] = canonical.get('pada')
        planet_data['nakshatra_lord'] = canonical.get('nakshatra_lord')
    chart_data['canonical_positions_version'] = positions.get('schema_version')
    return chart_data
