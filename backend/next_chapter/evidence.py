"""Natal condition and house combinations, without narrowing to one event."""
from itertools import combinations

from calculators.base_calculator import BaseCalculator
from calculators.vedic_graha_drishti import get_aspect_houses_for_planet
from charts.house_insight_service import build_natal_insight_bundle, RELATED_CHARTS
from charts.house_insight_worksheets import build_lord_worksheet
from prediction_engine.house_significations import HOUSE_COMBINATIONS, HOUSE_SIGNIFICATIONS


def aspect_numbers(planet):
    # Explicit report convention: nodes oppose only; conjunction is not an aspect.
    return (1, 7) if planet in {'Rahu', 'Ketu'} else get_aspect_houses_for_planet(planet)


def aspect_houses(planet, house):
    return [((house + number - 2) % 12) + 1
            for number in aspect_numbers(planet) if number != 1]


def ruled_houses(chart, planet):
    ascendant = int(chart['ascendant'] / 30)
    return [house for house in range(1, 13)
            if BaseCalculator.SIGN_LORDS[(ascendant + house - 1) % 12] == planet]


def build_foundation(birth, reference_date):
    bundle = build_natal_insight_bundle(birth, reference_date, node_aspects=(7,))
    chart = bundle['chart']
    houses = {}
    # Reuse the exact drawer records, excluding its current-day timing and summary.
    keys = ('house_num', 'sign_name', 'house_lord', 'significance', 'natal_assessment',
            'support_factors', 'stress_factors', 'lord_worksheet', 'argala',
            'points_in_house', 'chara_karakas_here', 'natural_karakas',
            'planet_conditions', 'related_varga', 'sav_givers', 'raw')
    for number, row in bundle['houses'].items():
        av = row.get('raw', {}).get('ashtakavarga') or {}
        if av.get('sav', {}).get('house_points') is None or not av.get('lord_bav'):
            raise ValueError(f'House {number} SAV/BAV foundation is incomplete')
        if int(number) in RELATED_CHARTS and not row.get('related_varga'):
            raise ValueError(f'House {number} related divisional worksheet is missing')
        houses[number] = {key: row.get(key) for key in keys}
        houses[number]['evidence_id'] = f'house_{number}'
        houses[number]['raw'] = {key: value for key, value in row['raw'].items()
                                 if key != 'activation_count'}
    planets = {}
    for planet, analysis in bundle['planets'].items():
        worksheet = build_lord_worksheet(lord=planet, lord_analysis=analysis,
            chart_data=chart, shadbala_data=bundle['shadbala'])
        if planet not in {'Rahu', 'Ketu'} and worksheet['shadbala_rupas'] is None:
            raise ValueError(f'{planet} Shadbala is unavailable')
        if planet in {'Rahu', 'Ketu'}:
            analysis = {**analysis, 'strength_analysis': {
                'applicability': 'not_applicable', 'shadbala_rupas': None}}
        planets[planet] = {'evidence_id': f'planet_{planet}',
            'longitude': chart['planets'][planet]['longitude'],
            'sign': chart['planets'][planet]['sign'],
            'house': chart['planets'][planet]['house'],
            'analysis': analysis, 'worksheet': worksheet}
    return {'source': 'ChartScreen house insight and planet worksheets',
            'houses': houses, 'planets': planets,
            'chart': {'ascendant': chart['ascendant'], 'houses': chart['houses'],
                      'planets': {name: chart['planets'][name] for name in planets}},
            'divisions': chart['divisions']}


def build_activation(chart, levels):
    """Keep each cause visible: direct occupation/lordship/aspect vs indirect links."""
    activations = []
    for level, planet in levels.items():
        row = chart['planets'][planet]
        for relation, houses in (
            ('occupation', [row['house']]), ('lordship', ruled_houses(chart, planet)),
            ('natal_aspect', aspect_houses(planet, row['house'])),
        ):
            for house in houses:
                activations.append({'level': level, 'planet': planet, 'house': house,
                                    'relation': relation, 'direct': True})
        sign_lord = BaseCalculator.SIGN_LORDS[row['sign']]
        nak_index = int((row['longitude'] % 360) / (360 / 27))
        nak_lord = ('Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury')[nak_index % 9]
        for relation, carrier in (('sign_dispositor', sign_lord), ('nakshatra_lord', nak_lord)):
            for house in sorted(set([chart['planets'][carrier]['house'], *ruled_houses(chart, carrier)])):
                activations.append({'level': level, 'planet': planet, 'house': house,
                    'relation': relation, 'via': carrier, 'direct': False})
    direct = {row['house'] for row in activations if row['direct']}
    focus = {row['house'] for row in activations if row['direct'] and row['level'] == 'PD'}
    relationships = []
    for (first_level, first), (second_level, second) in combinations(levels.items(), 2):
        a, b = chart['planets'][first], chart['planets'][second]
        relations = []
        if first == second:
            relations.append('same_planet')
        else:
            if a['house'] == b['house']: relations.append('conjunction')
            if b['house'] in aspect_houses(first, a['house']): relations.append('first_aspects_second')
            if a['house'] in aspect_houses(second, b['house']): relations.append('second_aspects_first')
            if BaseCalculator.SIGN_LORDS[a['sign']] == second: relations.append('first_disposed_by_second')
            if BaseCalculator.SIGN_LORDS[b['sign']] == first: relations.append('second_disposed_by_first')
            if {'first_disposed_by_second', 'second_disposed_by_first'} <= set(relations): relations.append('sign_exchange')
        relationships.append({'first_level': first_level, 'first_planet': first,
            'second_level': second_level, 'second_planet': second, 'relations': relations})
    return {
        'levels': levels, 'house_links': activations, 'direct_houses': sorted(direct),
        'pd_focus_houses': sorted(focus), 'relationships': relationships,
        'life_areas': [{'house': house, 'label': HOUSE_SIGNIFICATIONS[house].label,
            'significations': list(HOUSE_SIGNIFICATIONS[house].significations) + (['occult studies', 'astrology', 'hidden knowledge', 'insurance claim or payout'] if house == 8 else []),
            'body_significations': list(HOUSE_SIGNIFICATIONS[house].body_significations),
            'possibilities': list(HOUSE_SIGNIFICATIONS[house].manifestations)} for house in sorted(direct)],
        'house_combinations': [{'id': row.key, 'houses': list(row.relative_houses),
            'label': row.label, 'possibilities': list(row.manifestations),
            'pd_emphasis': bool(focus.intersection(row.relative_houses))}
            for row in HOUSE_COMBINATIONS if set(row.relative_houses) <= direct],
    }
