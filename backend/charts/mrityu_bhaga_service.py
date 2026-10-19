"""Auditable natal Mrityu Bhaga assessment and potential activation intervals.

Natal qualification has no orb. Transit conjunction orbs are an explicitly
chosen observation setting, not a classical severity rule. The span calendar
tracks passage through the *natal point's* sensitive arc, not the transiting
planet's own MB table. No risk scores or event predictions are manufactured.
"""
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math
from types import SimpleNamespace
from dateutil.relativedelta import relativedelta

from calculators.chart_calculator import ChartCalculator, resolve_ayanamsha_mode
from calculators.classical_mrityu_bhaga import analyze_chart_mrityu_bhaga
from calculators.classical_combustion import calculate_planet_combustion
from calculators.dasha_time import parse_birth_datetime
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.planetary_dignities_calculator import SIGN_NAMES, SIGN_LORDS
from calculators.vedic_graha_drishti import get_aspect_houses_for_planet
from calculators.shadbala_calculator import ShadbalaCalculator
from prediction_engine.transit_returns import (
    _strict_planet_state, _crosses_target, _refine_crossing, _refine_station,
    _angular_distance,
    _RETURN_SEQUENCE_GAPS,
)
from shared.dasha_calculator import DashaCalculator
from utils.timezone_service import get_iana_timezone

VERSION = 'mrityu-bhaga-workspace-v1'
CLASSICAL = ('Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu')
SLOW = ('Mars', 'Jupiter', 'Saturn', 'Rahu', 'Ketu')


def _stamp(value):
    return value.astimezone(timezone.utc).isoformat()


def _dms(value):
    # Truncate only the display's hundredth of an arcsecond; never round a
    # just-inside position into the next degree/sign/MB interval.
    ticks = math.floor((value % 30) * 360000)
    degree = ticks // 360000
    minute = (ticks % 360000) // 6000
    second = (ticks % 6000) / 100
    return f'{degree}° {minute:02d}′ {second:05.2f}″'


def _house(longitude, ascendant):
    return (int(longitude // 30) - int(ascendant // 30)) % 12 + 1


def _placement(chart, name):
    if name == 'Ascendant':
        return {'longitude': chart['ascendant'], 'house': 1}
    return chart['planets'].get(name) or (chart['planets'].get('Gulika') if name == 'Mandi' else {}) or {}


def natal_assessment(chart, birth=None):
    base = analyze_chart_mrityu_bhaga(chart)
    rows = []
    divisional = DivisionalChartCalculator(chart)
    divisions = {}
    strength = ShadbalaCalculator(chart, birth).calculate_shadbala() if birth else {}
    # These are corroborating placements, never a second MB test on mapped varga longitudes.
    for number in (9, 3, 30):
        payload = divisional.calculate_divisional_chart(number)
        divisions[f'D{number}'] = payload.get('divisional_chart', payload)
    for point, check in base['point_analysis'].items():
        data = _placement(chart, point)
        longitude = float(data['longitude']) % 360
        sign = int(longitude // 30)
        dispositor = SIGN_LORDS[sign]
        lord_data = chart['planets'][dispositor]
        related = []
        for name in CLASSICAL:
            if name == point:
                continue
            other = chart['planets'][name]
            number = (sign - int(float(other['longitude']) // 30)) % 12 + 1
            if number in get_aspect_houses_for_planet(name):
                related.append({'planet': name, 'relation': 'same_sign' if number == 1 else 'whole_sign_aspect', 'aspect_number': number})
        ruled = [h for h in range(1, 13) if SIGN_LORDS[(int(chart['ascendant'] // 30) + h - 1) % 12] == point]
        vargas = {}
        for label, division in divisions.items():
            placement = _placement(division, point)
            if placement.get('longitude') is not None:
                vargas[label] = {'sign': SIGN_NAMES[int(float(placement['longitude']) // 30)], 'house': _house(float(placement['longitude']), float(division['ascendant']))}
        rows.append({
            **check, 'longitude': longitude, 'position': f'{SIGN_NAMES[sign]} {_dms(longitude)}',
            'sign_name': SIGN_NAMES[sign], 'house': _house(longitude, chart['ascendant']),
            'houses_ruled': ruled, 'dispositor': dispositor,
            'dispositor_position': f"{SIGN_NAMES[int(float(lord_data['longitude']) // 30)]} {_dms(float(lord_data['longitude']))}",
            'dispositor_dignity': lord_data.get('dignity'),
            'dignity': data.get('dignity'), 'retrograde': data.get('retrograde'),
            'strength': strength.get(point), 'dispositor_strength': strength.get(dispositor),
            'nakshatra': data.get('nakshatra'), 'nakshatra_lord': data.get('nakshatra_lord'),
            'combustion': calculate_planet_combustion(point, data, chart['planets']['Sun']),
            'relationships': related, 'divisional_placements': vargas,
            'birth_time_sensitive': point in {'Ascendant', 'Mandi'},
            'distance_to_boundary_degrees': min(abs(longitude % 30 - check['degree_span_start']), abs(longitude % 30 - check['degree_span_end'])),
        })
    unavailable = []
    if _placement(chart, 'Mandi').get('longitude') is None:
        unavailable.append({'point': 'Gulika / Mandi', 'reason': (chart.get('upagraha_calculation') or {}).get('error') or 'Exact local day/night calculation unavailable'})
    return {'points': rows, 'affected_count': sum(r['is_mrityu_bhaga'] for r in rows),
            'unavailable_points': unavailable, 'complete': not unavailable,
            'table_key': base['table_key'], 'source': base['source'], 'degree_semantics': base['degree_semantics']}


def scan_contacts(planet, target, radius, start, end, state_at):
    """Station-split roots and clipped inside intervals, including no-exact near passes.

    Reuses the exact-return engine's strict state reader, crossing and station
    refiners. Six-hour screens (one hour for Moon) cannot traverse a whole
    revolution. Boundary and exact roots are independently refined to <=1s.
    """
    step = timedelta(hours=1 if planet == 'Moon' else 6)
    samples = []
    cursor = start
    while cursor < end:
        samples.append((cursor, *state_at(cursor, planet)))
        cursor = min(cursor + step, end)
    samples.append((end, *state_at(end, planet)))
    split = [samples[0]]
    for lo, hi in zip(samples, samples[1:]):
        if lo[2] * hi[2] < 0:
            station = _refine_station(lo[0], hi[0], planet, state_at)
            if lo[0] < station < hi[0]:
                split.append((station, *state_at(station, planet)))
        split.append(hi)
    roots = {key: [] for key in ('entry_edge', 'exact', 'exit_edge')}
    for key, angle in (('entry_edge', (target - radius) % 360), ('exact', target), ('exit_edge', (target + radius) % 360)):
        for lo, hi in zip(split, split[1:]):
            if _crosses_target(lo[1], hi[1], angle):
                at = _refine_crossing(lo[0], hi[0], planet, angle, state_at)
                if start <= at < end and (not roots[key] or abs(at - roots[key][-1]) > timedelta(seconds=2)):
                    roots[key].append(at)
    edges = sorted({start, end, *roots['entry_edge'], *roots['exit_edge']})
    intervals = []
    for left, right in zip(edges, edges[1:]):
        if right <= left or _angular_distance(state_at(left + (right-left)/2, planet)[0], target) > radius:
            continue
        if intervals and left - intervals[-1][1] <= timedelta(seconds=2):
            intervals[-1] = (intervals[-1][0], right)
        else:
            intervals.append((left, right))
    return [{'start_at': _stamp(left), 'end_at': _stamp(right),
             'clipped_start': left == start, 'clipped_end': right == end,
             'exact_passes': [{'at': _stamp(at), 'motion': 'retrograde' if state_at(at, planet)[1] < 0 else 'direct',
                               'residual_degrees': _angular_distance(state_at(at, planet)[0], target)}
                              for at in roots['exact'] if left - timedelta(seconds=1) <= at < right + timedelta(seconds=1)]}
            for left, right in intervals]


def dasha_timeline(birth, start, end, ayanamsha):
    clock = parse_birth_datetime(birth)
    if clock.tzinfo is None:
        raise ValueError('Birth timezone is required')
    if start < clock.astimezone(timezone.utc):
        raise ValueError('Activation dates must not precede birth')
    calc = DashaCalculator(ayanamsha)
    first = start.astimezone(clock.tzinfo).replace(tzinfo=None)
    finish = end.astimezone(clock.tzinfo).replace(tzinfo=None)
    # Keep the original birth balance and continue the shared planetary order.
    # Restarting a clipped birth balance every 120 calendar years would create
    # a gap between the ninth MD's end and the next artificial cycle origin.
    parents = calc.calculate_current_dashas(birth, clock.replace(tzinfo=None), strict=True)['maha_dashas']
    if not parents:
        raise ValueError('No authoritative Vimshottari birth balance')
    while parents[-1]['end'] + timedelta(seconds=1) < finish:
        previous = parents[-1]
        lord = calc.PLANET_ORDER[(calc.PLANET_ORDER.index(previous['planet'])+1)%9]
        left = previous['end'] + timedelta(seconds=1)
        right = left + relativedelta(years=calc.DASHA_PERIODS[lord])
        parents.append({'planet': lord, 'start': left, 'end': right-timedelta(seconds=1), 'years': calc.DASHA_PERIODS[lord]})
    rows = []
    to_utc = lambda value: _stamp(value.replace(tzinfo=clock.tzinfo))
    for md in parents:
        origin, md_start, _, md_transition = calc._maha_ad_timeline_start(md)
        if md_transition <= first or md_start >= finish:
            continue
        ads = calc.list_antardashas(md)
        raw_origins = {}
        cursor = origin
        index = calc.PLANET_ORDER.index(md['planet'])
        for i in range(9):
            lord = calc.PLANET_ORDER[(index+i)%9]
            raw_origins[lord] = cursor
            cursor += timedelta(days=calc.DASHA_PERIODS[md['planet']]*calc.DASHA_PERIODS[lord]/120*calc.YEAR_LEN)
        for ad_index, ad in enumerate(ads):
            ad_start, calculated_ad_end = calc._period_bounds(ad)
            # MD uses calendar years, so its final AD can have a small residual
            # against the solar-year subdivision. Assign that residual only to
            # the final child; preserve every earlier calculated transition.
            ad_end = md_transition if ad_index == len(ads)-1 else min(calculated_ad_end, md_transition)
            raw_ad = {'planet': ad['planet'], 'start': raw_origins[ad['planet']], 'end': ad_end}
            pds = calc.list_pratyantardashas(md, raw_ad)
            for pd_index, pd in enumerate(pds):
                pd_start, calculated_pd_end = calc._period_bounds(pd)
                pd_end = ad_end if pd_index == len(pds)-1 else min(calculated_pd_end, ad_end)
                left, right = max(first, md_start, ad_start, pd_start), min(finish, ad_end, pd_end)
                if left >= right:
                    continue
                rows.append({'start_at': to_utc(left), 'end_at': to_utc(right),
                             'lords': {'mahadasha': md['planet'], 'antardasha': ad['planet'], 'pratyantardasha': pd['planet']},
                             'parent_boundary_adjustment_seconds': (pd_end-calculated_pd_end).total_seconds()})
    rows.sort(key=lambda row: row['start_at'])
    if not rows or rows[0]['start_at'] != _stamp(start) or rows[-1]['end_at'] != _stamp(end):
        raise ValueError('Vimshottari calculation does not cover the requested range')
    for previous, current in zip(rows, rows[1:]):
        if previous['end_at'] != current['start_at']:
            raise ValueError('Vimshottari parent/child intervals do not form a continuous timeline')
    return rows


def _connections(point, lords):
    output = []
    for level, lord in lords.items():
        if lord == point['point']:
            relation = 'direct'
        elif lord == point['dispositor']:
            relation = 'dispositor'
        else:
            continue
        output.append({'level': level, 'lord': lord, 'relation': relation})
    return output


def build_workspace(birth, start_date, end_date, *, calendar=False, fast=False, aspects=False, orb=1.0, birth_time_minutes=0, study="mrityu_bhaga"):
    birth = dict(birth)
    for key in ('date', 'time', 'latitude', 'longitude'):
        if birth.get(key) is None or str(birth[key]).strip() == '':
            raise ValueError(f'Birth {key} is required')
    for key, limit in (('latitude', 90), ('longitude', 180)):
        birth[key] = float(birth[key])
        if not math.isfinite(birth[key]) or abs(birth[key]) > limit:
            raise ValueError(f'Invalid birth {key}')
    birth['date'] = str(birth['date'])[:10]
    birth['time'] = str(birth['time']).split('T')[-1][:8]
    timezone_inferred = birth.get('timezone') is None or str(birth['timezone']).strip() == ''
    if timezone_inferred:
        birth['timezone'] = get_iana_timezone(birth['latitude'], birth['longitude'])
    clock = parse_birth_datetime(birth)
    if clock.tzinfo is None:
        raise ValueError('Birth timezone is required')
    start = datetime.combine(start_date, datetime.min.time(), tzinfo=clock.tzinfo).astimezone(timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=clock.tzinfo).astimezone(timezone.utc)
    if start < clock.astimezone(timezone.utc):
        raise ValueError('Activation dates must not precede birth')
    if not 0 < (end_date-start_date).days + 1 <= 366:
        raise ValueError('Choose an inclusive range of 1–366 days')
    if start.year < 1800 or end > datetime(2400, 1, 1, tzinfo=timezone.utc):
        raise ValueError('Bundled ephemeris coverage is 1800–2399')
    if not math.isfinite(orb) or not .1 <= orb <= 3:
        raise ValueError('Transit conjunction orb must be between 0.1° and 3°')
    if birth_time_minutes not in (0, 5, 10, 15):
        raise ValueError('Birth-time comparison must be 0, 5, 10 or 15 minutes')
    profile = birth.get('calculation_profile') or {}
    ayanamsha, _ = resolve_ayanamsha_mode(profile.get('ayanamsha', birth.get('ayanamsha') or 'lahiri'))
    node = profile.get('node_type', 'mean')
    if node not in {'mean', 'true'}:
        raise ValueError('node_type must be mean or true')
    # Fail before generating a natal assessment if the bundled ephemeris is
    # missing. The older ChartCalculator can otherwise accept Swiss fallback.
    for planet in CLASSICAL:
        _strict_planet_state(clock.astimezone(timezone.utc), planet, ayanamsha=ayanamsha, node_type=node)
    # Recalculate D1 from birth data. Client-side D9, rotated or transit charts
    # must never accidentally become the natal assessment reference.
    chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**birth), ayanamsha=ayanamsha, node_type=node)
    if study == 'bhrigu_bindu':
        from charts.bhrigu_bindu_service import natal_assessment as assess_bindu, connections as bindu_connections
        assess = assess_bindu
        connect = bindu_connections
    elif study == 'mrityu_bhaga':
        assess = natal_assessment
        connect = _connections
    else:
        raise ValueError('Unknown chart study')
    natal = assess(chart, birth)
    sensitivity = []
    if birth_time_minutes:
        for delta in (-birth_time_minutes, 0, birth_time_minutes):
            shifted_clock = clock + timedelta(minutes=delta)
            shifted_birth = {**birth, 'date': shifted_clock.date().isoformat(), 'time': shifted_clock.strftime('%H:%M:%S')}
            shifted = chart if delta == 0 else ChartCalculator({}).calculate_chart(SimpleNamespace(**shifted_birth), ayanamsha=ayanamsha, node_type=node)
            if study == 'bhrigu_bindu':
                point = assess(shifted, shifted_birth)['points'][0]
                sensitivity.append({'offset_minutes': delta, 'birth_local': shifted_clock.isoformat(),
                                    'position': point['position'], 'house': point['house'],
                                    'nakshatra': point['nakshatra'], 'longitude': point['longitude']})
                continue
            check = analyze_chart_mrityu_bhaga(shifted)
            mandi = _placement(shifted, 'Mandi')
            sensitivity.append({'offset_minutes': delta, 'birth_local': shifted_clock.isoformat(),
                                'affected_points': [r['point'] for r in check['afflicted_points']],
                                'lagna_position': f"{SIGN_NAMES[int(shifted['ascendant']//30)]} {_dms(shifted['ascendant'])}",
                                'gulika_position': f"{SIGN_NAMES[int(mandi['longitude']//30)]} {_dms(mandi['longitude'])}" if mandi else None,
                                'point_checks': check['point_analysis']})
    affected = natal['points'] if study == 'bhrigu_bindu' else [p for p in natal['points'] if p['is_mrityu_bhaga']]
    dashas = dasha_timeline(birth, start, end, ayanamsha)
    dasha_rows = []
    for row in dashas:
        for point in affected:
            links = connect(point, row['lords'])
            if links:
                dasha_rows.append({**row, 'point': point['point'], 'connections': links})
    events = []
    if calendar and affected:
        @lru_cache(maxsize=150000)
        def state(at, planet):
            longitude, speed = _strict_planet_state(at, planet, ayanamsha=ayanamsha, node_type=node)
            # ChartCalculator applies a declared D1 longitude correction.
            # Use the same frame for transits rather than comparing a corrected
            # natal point with an uncorrected sky longitude.
            return (longitude - ChartCalculator.D1_CORRECTION) % 360, speed
        planets = CLASSICAL if fast else SLOW
        for point in affected:
            for planet in planets:
                angles = get_aspect_houses_for_planet(planet) if aspects and planet not in {'Rahu', 'Ketu'} else [1]
                for number in angles:
                    target = (point['longitude'] - (number-1)*30) % 360
                    modes = [('natal_contact', target, orb)]
                    if number == 1 and study == 'mrityu_bhaga':
                        modes.append(('natal_mb_span', point['sign']*30 + point['degree_span_start']+.5, .5))
                    for mode, center, radius in modes:
                        windows = scan_contacts(planet, center, radius, start, end, state)
                        for index, window in enumerate(windows, 1):
                            links = []
                            for row in dasha_rows:
                                if row['point'] == point['point'] and row['start_at'] < window['end_at'] and row['end_at'] > window['start_at']:
                                    links.append({**row, 'start_at': max(row['start_at'], window['start_at']), 'end_at': min(row['end_at'], window['end_at'])})
                            events.append({**window, 'id': f"{point['point']}:{planet}:{number}:{mode}:{window['start_at']}",
                                           'point': point['point'], 'planet': planet, 'kind': mode, 'aspect_number': number,
                                           'target_longitude': center, 'orb_degrees': radius if mode == 'natal_contact' else None,
                                           'dasha_overlaps': links, 'pass_number_in_range': index,
                                           'midpoint_only': mode == 'natal_mb_span'})
        events.sort(key=lambda r: (r['start_at'], r['point'], r['planet'], r['kind']))
        sequences = {}
        for event in events:
            key = (event['point'], event['planet'], event['kind'], event['aspect_number'])
            groups = sequences.setdefault(key, [])
            instant = datetime.fromisoformat(event['start_at'])
            if not groups or instant - datetime.fromisoformat(groups[-1][-1]['end_at']) > _RETURN_SEQUENCE_GAPS[event['planet']]:
                groups.append([])
            groups[-1].append(event)
        for groups in sequences.values():
            for sequence_number, group in enumerate(groups, 1):
                motions = ' → '.join(p['motion'] for row in group for p in row['exact_passes'])
                for window_number, row in enumerate(group, 1):
                    row['sequence_number_in_range'] = sequence_number
                    row['sequence_window_number'] = window_number
                    row['sequence_window_count'] = len(group)
                    row['sequence_motion'] = motions or 'No exact crossing in selected range'
        # Independent bodies only: span passage and longitude/aspect contact
        # from the same transiting planet must never inflate confluence.
        by_point = {}
        for event in events:
            by_point.setdefault(event['point'], []).append(event)
        for rows in by_point.values():
            for row in rows:
                row['concurrent_transits'] = sorted({
                    other['planet'] for other in rows
                    if other['planet'] != row['planet']
                    and other['start_at'] < row['end_at'] and other['end_at'] > row['start_at']
                })
    result = {'schema_version': VERSION, 'natal': natal, 'dasha_activations': dasha_rows,
            'natal_chart': {'ascendant': chart['ascendant'], 'houses': chart['houses'],
                            'planets': {name: {key: value for key, value in row.items() if key in {'longitude', 'sign', 'degree', 'house', 'retrograde', 'nakshatra'}} for name, row in chart['planets'].items()}},
            'birth_time_comparison': sensitivity,
            'events': events, 'calendar_calculated': calendar,
            'range': {'start_at': _stamp(start), 'end_at': _stamp(end), 'timezone': str(clock.tzinfo)},
            'audit': {'ayanamsha': ayanamsha, 'node_type': node, 'house_system': 'whole_sign_natal_lagna',
                      'birth_timezone': str(clock.tzinfo), 'timezone_inferred_from_coordinates': timezone_inferred,
                      'longitude_correction_degrees': -ChartCalculator.D1_CORRECTION,
                      'longitude_frame': 'Same ChartCalculator D1 correction applied to natal and transit longitudes',
                      'transit_planets': list(CLASSICAL if fast else SLOW), 'transit_orb_degrees': orb,
                      'ephemeris': 'Swiss Ephemeris data files; no analytic fallback for transit results',
                      'boundary_precision_seconds': 1, 'intervals': 'start inclusive, end exclusive; clipped to selected range',
                      'dasha_method': 'Shared Vimshottari birth balance, MD order and AD/PD enumerators; calendar-year MD and 365.25-day subperiod year. Final child ends at parent transition; birth-balance subdivisions retain their full origin. MD sequence continues from birth without restarting a clipped balance every 120 years.',
                      'natal_aspect_method': 'Canonical whole-sign graha drishti; the app’s selected natal nodal convention uses 5th, 7th and 9th aspects',
                      'aspect_method': 'Degree contacts at canonical Parashari aspect offsets; optional observational extension, not whole-sign entry timing. Nodal aspects excluded.',
                      'sources': [{'title': 'Jataka Parijata table and ordinal convention', 'url': 'https://saptarishisshop.com/mrithyu-bhaga-and-bcp-by-hemant-bhatt/'}],
                      'limits': ['Potential activation evidence, not a severity score or guaranteed event.',
                                 'Birth-time comparison samples the recorded time and selected endpoints; it does not establish stability throughout that interval.',
                                 'Span passage uses the natal point’s MB arc; its midpoint is not an exact natal contact.',
                                 'Divisional placements corroborate context; MB is tested only in D1.',
                                 'Lagna and Gulika/Mandi are sensitive to birth time. Other placements near a span boundary also need birth-time review.',
                                 'Pass numbering covers the selected range only; clipped intervals can continue outside it.']}}

    if study == 'bhrigu_bindu':
        result['schema_version'] = 'bhrigu-bindu-workspace-v1'
        result['dasha_timeline'] = dashas
        result['audit']['midpoint_method'] = 'Rahu + ((Moon - Rahu) modulo 360) / 2, normalized to 0–360 degrees'
        result['audit']['sources'] = [{'title': 'C. S. Patel, Predicting Through Navamsa and Nadi Astrology, pp. 107–110', 'url': 'https://ashramsofindia.com/wp-content/uploads/2023/09/Predicting-Through-Navamsa-and-Nadi-Astrology-by-Sivam-Sundaram.pdf'}]
        result['audit']['limits'] = [
            'Bhrigu Bindu is a calculated sensitive point, not a planet. No Shadbala, dignity or combustion is assigned to the point itself.',
            'Dasha links to Moon, Rahu, sign ruler and nakshatra ruler are contextual analytical links, not a separate classical Bhrigu Bindu dasha.',
            'Transit contacts are timing evidence, not a guaranteed event or a severity score.',
            'Contact distance is a selected observation setting, not a fixed classical rule.',
            'Optional degree aspects are separated from conjunctions; nodal aspects are excluded.',
            'Birth-time comparison samples only the recorded time and selected endpoints.',
            'Repeated pass sequences and concurrent bodies cover only the selected range; overlapping windows need not share one common instant.',
        ]
    return result
