"""Directed Rahu-to-Moon Bhrigu Bindu assessment using the shared exact transit engine."""
from datetime import datetime, timezone
from calculators.sniper_points_calculator import bhrigu_bindu_longitude
from event_prediction.house_significations import HOUSE_SIGNIFICATIONS
from calculators.shadbala_calculator import ShadbalaCalculator
from calculators.planetary_dignities_calculator import SIGN_NAMES, SIGN_LORDS
from calculators.classical_combustion import calculate_planet_combustion
from calculators.vedic_graha_drishti import get_aspect_houses_for_planet
from charts.mrityu_bhaga_service import _dms, _house, CLASSICAL

NAKSHATRAS = ('Ashwini Bharani Krittika Rohini Mrigashira Ardra Punarvasu Pushya Ashlesha Magha Purva_Phalguni Uttara_Phalguni Hasta Chitra Swati Vishakha Anuradha Jyeshtha Mula Purva_Ashadha Uttara_Ashadha Shravana Dhanishta Shatabhisha Purva_Bhadrapada Uttara_Bhadrapada Revati').split()
NAK_LORDS = ('Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury')


def natal_assessment(chart, birth=None):
    # Keep full precision for crossings; the existing public calculator rounds
    # only its display payload and remains backward compatible.
    moon = float(chart['planets']['Moon']['longitude']) % 360
    rahu = float(chart['planets']['Rahu']['longitude']) % 360
    longitude = bhrigu_bindu_longitude(moon, rahu)
    sign = int(longitude // 30)
    nak = min(26, int(longitude / (360 / 27)))
    house = _house(longitude, chart['ascendant'])
    lord = SIGN_LORDS[sign]
    lord_data = chart['planets'][lord]
    strengths = ShadbalaCalculator(chart, birth).calculate_shadbala() if birth else {}
    planet_context = {}
    asc_sign = int(chart['ascendant'] // 30)
    for name in CLASSICAL:
        row = chart['planets'][name]
        planet_context[name] = {
            'house': _house(float(row['longitude']), chart['ascendant']),
            'houses_ruled': [h for h in range(1,13) if SIGN_LORDS[(asc_sign+h-1)%12] == name],
            'dignity': row.get('dignity'), 'strength': strengths.get(name),
            'position': f"{SIGN_NAMES[int(float(row['longitude']) // 30)]} {_dms(float(row['longitude']))}",
        }
    relations = []
    for name in CLASSICAL:
        position = float(chart['planets'][name]['longitude']) % 360
        number = (sign - int(position // 30)) % 12 + 1
        if number == 1 or number in get_aspect_houses_for_planet(name):
            distance = abs((position - longitude + 180) % 360 - 180)
            relations.append({'planet': name, 'relation': 'same_sign' if number == 1 else 'whole_sign_aspect', 'aspect_number': number, 'separation_degrees': distance})
    point = {'point': 'Bhrigu Bindu', 'longitude': longitude, 'position': f'{SIGN_NAMES[sign]} {_dms(longitude)}',
             'sign_name': SIGN_NAMES[sign], 'house': house,
             'house_themes': [theme.replace('_', ' ') for theme in HOUSE_SIGNIFICATIONS[house]['primary']],
             'dispositor': lord, 'dispositor_position': f"{SIGN_NAMES[int(float(lord_data['longitude']) // 30)]} {_dms(float(lord_data['longitude']))}",
             'dispositor_dignity': lord_data.get('dignity'), 'dispositor_strength': strengths.get(lord),
             'dispositor_combustion': calculate_planet_combustion(lord, lord_data, chart['planets']['Sun']),
             'dispositor_retrograde': lord_data.get('retrograde'),
             'nakshatra': NAKSHATRAS[nak].replace('_', ' '), 'nakshatra_lord': NAK_LORDS[nak % 9],
             'pada': min(4, int((longitude - nak * (360 / 27)) / (360 / 108)) + 1),
             'planet_context': planet_context, 'relationships': relations, 'moon_longitude': moon, 'rahu_longitude': rahu,
             'moon_position': f'{SIGN_NAMES[int(moon // 30)]} {_dms(moon)}',
             'rahu_position': f'{SIGN_NAMES[int(rahu // 30)]} {_dms(rahu)}',
             'forward_arc_degrees': (moon - rahu) % 360}
    return {'points': [point], 'complete': True, 'unavailable_points': [],
            'source': 'C. S. Patel, Predicting Through Navamsa and Nadi Astrology, pp. 107–108',
            'degree_semantics': 'Half the forward zodiacal distance from Rahu to Moon, added to Rahu. Not the shorter-arc midpoint.'}


def connections(point, lords):
    roles = {'Moon': ['moon'], 'Rahu': ['rahu']}
    roles.setdefault(point['dispositor'], []).append('sign_ruler')
    roles.setdefault(point['nakshatra_lord'], []).append('nakshatra_ruler')
    return [{'level': level, 'lord': lord, 'relation': 'context', 'roles': roles[lord]}
            for level, lord in lords.items() if lord in roles]


FOCUS_HOUSES = {
    'general': (), 'career': (2,6,10,11), 'marriage': (2,7,11),
    'family': (2,4,5), 'finances': (2,5,8,11), 'education': (4,5,9),
    'property': (4,11,12), 'health': (1,6,8,12), 'travel': (3,9,12),
}


def contact_status(longitude, speed, target):
    """Direction refers to distance from the fixed natal contact target now."""
    delta = (longitude-target+180) % 360-180
    distance = abs(delta)
    if distance < 1/3600:
        direction = 'At exact contact'
    elif abs(distance-180) < 1/3600:
        direction = 'Opposite the contact target'
    elif abs(speed) < 1e-6:
        direction = 'Stationary'
    else:
        direction = 'Approaching' if delta*speed < 0 else 'Moving away'
    return {'distance_degrees': distance, 'direction': direction,
            'motion': 'stationary' if abs(speed) < 1e-6 else 'retrograde' if speed < 0 else 'direct', 'speed_degrees_per_day': speed}


def focus_evidence(point, planet, focus):
    houses = FOCUS_HOUSES[focus]
    rows = []
    if point['house'] in houses:
        rows.append(f"Bhrigu Bindu occupies natal house {point['house']}")
    names = list(dict.fromkeys([planet, point['dispositor'], point['nakshatra_lord'], 'Moon', 'Rahu',
                               *[r['planet'] for r in point['relationships']]]))
    roles = {}
    roles.setdefault(point['dispositor'], []).append('BB sign ruler')
    roles.setdefault(point['nakshatra_lord'], []).append('BB nakshatra ruler')
    for name in names:
        body = point['planet_context'][name]
        reasons = []
        if body['house'] in houses:
            reasons.append(f"occupies natal house {body['house']}")
        ruled = [h for h in body['houses_ruled'] if h in houses]
        if ruled:
            reasons.append('rules natal house ' + ', '.join(map(str, ruled)))
        if reasons:
            role = 'transiting planet’s natal role' if name == planet else ', '.join(roles.get(name, ['BB-associated planet']))
            condition = str(body.get('dignity') or 'condition unavailable').replace('_', ' ')
            strength = body.get('strength')
            if strength:
                condition += f"; {strength.get('total_rupas')} rupas, {strength.get('required_percent')}% of required strength"
            rows.append(f"{name} ({role}): " + '; '.join(reasons) + f". Natal condition: {condition}")
    return rows


def build_workspace(birth, start_date, end_date, *, focus='general', chart_at=None, as_of=None, **kwargs):
    from charts.mrityu_bhaga_service import build_workspace as shared_workspace, _stamp
    from prediction_engine.transit_returns import _strict_planet_state
    from calculators.chart_calculator import ChartCalculator
    if focus not in FOCUS_HOUSES:
        raise ValueError('Unknown consultation focus')
    if chart_at is not None:
        chart_at = datetime.fromisoformat(chart_at.replace('Z','+00:00')) if isinstance(chart_at,str) else chart_at
        if chart_at.tzinfo is None:
            raise ValueError('Transit chart time must include a timezone')
    data = shared_workspace(birth, start_date, end_date, **kwargs, study='bhrigu_bindu')
    point = data['natal']['points'][0]
    audit = data['audit']
    now = as_of or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Contact reference time must include a timezone')
    def state(at, planet):
        longitude, speed = _strict_planet_state(at, planet, ayanamsha=audit['ayanamsha'], node_type=audit['node_type'])
        return (longitude-ChartCalculator.D1_CORRECTION)%360, speed
    current = {name: state(now, name) for name in CLASSICAL}
    data['contact_reference_at'] = _stamp(now)
    data['consultation_focus'] = {'key':focus, 'houses':list(FOCUS_HOUSES[focus]),
        'method':'Selected whole-sign house themes, natal occupancy and sign rulership. Analytical relevance links; not an event score or a classical Bhrigu Bindu rule.',
        'natal_evidence':focus_evidence(point, point['dispositor'], focus) if focus != 'general' else []}
    for event in data['events']:
        longitude, speed = current[event['planet']]
        event['current_contact'] = {**contact_status(longitude,speed,event['target_longitude']),
                                    'as_of':data['contact_reference_at'],
                                    'within_selected_orb':abs((longitude-event['target_longitude']+180)%360-180) <= event['orb_degrees']}
        event['focus_evidence'] = focus_evidence(point,event['planet'],focus) if focus != 'general' else []
        context = []
        for row in data['dasha_timeline']:
            if row['start_at'] >= event['end_at'] or row['end_at'] <= event['start_at']:
                continue
            links = []
            for level,lord in row['lords'].items():
                natal = point['planet_context'][lord]
                houses = sorted(set([natal['house'],*natal['houses_ruled']]) & set(FOCUS_HOUSES[focus]))
                if houses:
                    links.append({'level':level,'lord':lord,'houses':houses})
            if links:
                context.append({'start_at':max(row['start_at'],event['start_at']),
                                'end_at':min(row['end_at'],event['end_at']),'connections':links})
        event['focus_dasha_overlaps'] = context
    # The selected snapshot uses natal houses with actual transit positions at
    # the requested instant, not the transit-date Ascendant or midnight sky.
    if chart_at is not None:
        if not datetime.fromisoformat(data['range']['start_at']) <= chart_at < datetime.fromisoformat(data['range']['end_at']):
            raise ValueError('Transit chart time must be within the selected calendar range')
        chart = data['natal_chart']
        planets = {}
        for name in CLASSICAL:
            longitude,speed = state(chart_at,name)
            nak = min(26,int(longitude/(360/27)))
            planets[name] = {'longitude':longitude,'degree':longitude%30,'sign':int(longitude//30),
                             'house':_house(longitude,chart['ascendant']),'retrograde':speed<0,
                             'nakshatra':NAKSHATRAS[nak].replace('_',' ')}
        data['selected_transit'] = {'at':_stamp(chart_at), 'frame':'Transit planets over fixed natal whole-sign houses',
                                  'chart':{'ascendant':chart['ascendant'],'houses':chart['houses'],'planets':planets},
                                  'bb_position':point['position'], 'bb_house':point['house']}
    data['audit']['orb_preset'] = 'C. S. Patel ±100 arcminutes (±1°40′), p. 110' if abs(audit['transit_orb_degrees']-5/3) < 1e-9 else 'Selected observation distance'
    data['audit']['focus_method'] = data['consultation_focus']['method']
    data['audit']['contact_direction_method'] = 'Instantaneous change of angular separation from each fixed contact target at the displayed UTC reference time; not a promise of a future crossing.'
    return data
