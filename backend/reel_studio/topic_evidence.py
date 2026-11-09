"""Calculated, topic-scoped worksheets for curated reels; no model astrology math."""
from datetime import datetime, timezone

from charts.house_insight_service import (
    build_natal_insight_bundle, _birth_obj, _normalize_chart_data,
    _collect_house_factors, _build_natal_evidence_ledger, SIGN_LORDS,
)
from calculators.house_analyzer import HouseAnalyzer
from calculators.divisional_chart_calculator import DivisionalChartCalculator
from calculators.classical_jaimini import ClassicalJaiminiCalculator
from calculators.nakshatra_calculator import NakshatraCalculator
from calculators.nadi_linkage_calculator import NadiLinkageCalculator

EVIDENCE_VERSION = 'topic-worksheets-v1'
# These are interpretive scopes, not fixed predictions. Every finding below is
# calculated from the owned native's chart, including the dynamically selected lords.
TOPIC_SCOPES = {
    'know_me': {
        'houses': {1: 'self-expression', 2: 'speech and values', 3: 'communication',
                   4: 'emotional comfort', 7: 'relating to others', 8: 'trust and vulnerability', 12: 'privacy'},
        'planets': ['Moon', 'Mercury', 'Venus', 'Mars'], 'karakas': ['AK', 'DK'],
        'padas': [1, 7], 'vargas': {9: [1, 7]},
    },
    'love_me': {
        'houses': {2: 'shared values', 4: 'emotional security', 5: 'affection',
                   7: 'partnership', 8: 'trust and intimacy', 12: 'private connection'},
        'planets': ['Moon', 'Venus', 'Mars', 'Jupiter'], 'karakas': ['AK', 'DK'],
        'padas': [7, 12], 'vargas': {9: [1, 4, 7, 12]},
    },
    'real_me': {
        'houses': {1: 'outward expression', 2: 'spoken expression', 3: 'social communication',
                   4: 'private emotional needs', 10: 'public conduct'},
        'planets': ['Sun', 'Moon', 'Mercury', 'Saturn'], 'karakas': ['AK'],
        'padas': [1], 'vargas': {9: [1]},
    },
    'superpower': {
        'houses': {1: 'personal agency', 3: 'practised skills', 5: 'creative intelligence',
                   9: 'learning and judgment', 10: 'applied ability', 11: 'collaboration'},
        'planets': ['Mercury', 'Mars', 'Jupiter', 'Sun', 'Saturn'], 'karakas': ['AK', 'AmK'],
        'padas': [1, 10], 'vargas': {9: [1, 5, 9], 10: [1, 10]},
    },
    'career': {
        'houses': {2: 'income and communication', 3: 'initiative and skills', 6: 'service and competition',
                   9: 'advanced learning', 10: 'professional responsibility', 11: 'networks and gains'},
        'planets': ['Sun', 'Mercury', 'Saturn', 'Jupiter', 'Mars'], 'karakas': ['AK', 'AmK'],
        'padas': [1, 10], 'vargas': {9: [1, 9], 10: [1, 6, 10, 11]},
    },
}


def _pick(row, keys):
    return {key: row[key] for key in keys if key in row}


def _house(row):
    # Exclude point-in-time activation, generic health/body parts and unrelated
    # vargas (e.g. D7 must not turn a creativity reading into a children prediction).
    return _pick(row, ('house_num', 'chart_name', 'sign_name', 'house_lord',
        'natal_assessment', 'support_factors', 'stress_factors', 'lord_worksheet',
        'argala', 'planet_conditions', 'sav_givers'))


def _planet(row):
    result = _pick(row, ('basic_info', 'dignity_analysis', 'strength_analysis',
        'house_position_analysis', 'friendship_analysis', 'special_lordships',
        'conjunctions', 'combustion_status', 'retrograde_analysis',
        'aspects_received', 'gandanta_analysis', 'overall_assessment'))
    if row.get('basic_info', {}).get('planet') in ('Rahu', 'Ketu'):
        result.pop('strength_analysis', None)
        result.pop('overall_assessment', None)
        result['shadbala_applicability'] = 'Not defined for nodes; absence is not weakness.'
    return result


def build_topic_evidence(birth, topic):
    scope = TOPIC_SCOPES[topic]
    profile = birth.get('calculation_profile')
    bundle = build_natal_insight_bundle(
        birth, datetime.now(timezone.utc).date().isoformat(), profile, node_aspects=(7,))
    natal, houses, analyses = bundle['chart'], bundle['houses'], bundle['planets']
    varga_calc = DivisionalChartCalculator(natal)
    divisional = {division: _normalize_chart_data(varga_calc.calculate_divisional_chart(division))
                  for division in scope['vargas']}
    jaimini = ClassicalJaiminiCalculator(natal, divisional[9]).calculate()
    scheme = jaimini['karaka_schemes']['seven']
    roles = [row for row in scheme['rows'] if row['karaka_code'] in scope['karakas']]
    selected = set(scope['planets'])
    selected.update(houses[str(h)]['house_lord'] for h in scope['houses'])
    selected.update(row['planet'] for row in roles)
    stars = NakshatraCalculator(chart_data=natal).calculate_nakshatra_positions()
    evidence = []

    def add(identifier, purpose, findings):
        evidence.append({'id': identifier, 'purpose': purpose, 'findings': findings})

    for house, purpose in scope['houses'].items():
        findings = _house(houses[str(house)])
        if not findings.get('sav_givers'):
            findings['sav_availability'] = 'Unavailable; do not infer a score or strength from missing data.'
        add(f'd1.house.{house}', purpose, findings)

    # Resolve both dispositors and their actual calculated conditions, rather than
    # expecting the writing model to derive strength from a longitude or star name.
    for planet in sorted(selected):
        row = _planet(analyses[planet])
        star = stars[planet]
        sign_lord = SIGN_LORDS[int(natal['planets'][planet]['longitude'] // 30)]
        row['nakshatra'] = star
        row['dispositors'] = {
            kind: {'planet': lord, 'condition': _pick(_planet(analyses[lord]),
                ('basic_info', 'dignity_analysis', 'strength_analysis', 'combustion_status', 'special_lordships', 'shadbala_applicability'))}
            for kind, lord in [('sign_lord', sign_lord), ('nakshatra_lord', star['nakshatra_lord'])]
        }
        row['vargottama_d1_d9'] = (
            int(natal['planets'][planet]['longitude'] // 30) ==
            int(divisional[9]['planets'][planet]['longitude'] // 30))
        if planet in ('Rahu', 'Ketu'):
            row.pop('strength_analysis', None)
            row['shadbala_applicability'] = 'Not defined for nodes; absence is not weakness.'
        add(f'd1.planet.{planet}', 'Topic significator, selected house lord or Jaimini karaka', row)

    for division, relevant_houses in scope['vargas'].items():
        chart = divisional[division]
        analyzer = HouseAnalyzer(chart, _birth_obj(birth), shadbala_chart_data=natal, node_aspects=(7,))
        chart_id = 'navamsa' if division == 9 else 'dashamsa'
        for house in relevant_houses:
            result = _collect_house_factors(birth, chart, house, chart_id, None,
                shadbala_chart_data=natal, analyzer=analyzer, calculation_profile=profile)
            result = _house(result)
            # Varga longitudes are symbolic: do not infer a physical nakshatra,
            # retrograde state or independent Shadbala measurement from them.
            worksheet = result.get('lord_worksheet') or {}
            lord = worksheet.get('planet')
            for field in ('nakshatra', 'nakshatra_lord', 'degree', 'retrograde'):
                worksheet.pop(field, None)
            if lord in analyses:
                worksheet['natal_condition'] = _pick(analyses[lord], ('combustion_status', 'retrograde_analysis'))
            result.pop('sav_givers', None)
            # Only structural varga evidence; do not carry over the drawer's
            # longitude-derived stars, gandanta, special points or D1 SAV-by-sign
            # as though they were independently measured in the divisional chart.
            allowed = {'dignity', 'placement', 'occupant', 'aspect', 'combustion', 'shadbala', 'house_type', 'argala'}
            for field in ('support_factors', 'stress_factors'):
                result[field] = [factor for factor in result.get(field, []) if factor.get('category') in allowed]
            result['natal_assessment'] = _build_natal_evidence_ledger(
                result['support_factors'], result['stress_factors'])
            worksheet.pop('special_roles', None)
            worksheet.pop('neecha_bhanga', None)
            worksheet.pop('neecha_bhanga_conditions', None)
            worksheet.pop('neecha_bhanga_source', None)
            add(f'd{division}.house.{house}',
                'Relationship/inner-strength corroboration' if division == 9 else 'Professional expression', result)
        for role in roles:
            name = role['planet']
            condition = analyzer.planet_analyzer.analyze_planet(name)
            add(f'd{division}.karaka.{role["karaka_code"]}', 'Divisional condition of the topic karaka',
                {'planet': name, 'position': _pick(condition['basic_info'], ('sign_name', 'house')),
                 'dignity': condition['dignity_analysis']})

    add('jaimini.karakas', 'Self, partnership or vocation according to the selected topic',
        {'scheme': 'seven', 'roles': roles, 'tie_groups': scheme['tie_groups'],
         'is_unambiguous': scheme['is_unambiguous']})
    padas = [row for row in jaimini['arudha_padas'] if row['house'] in scope['padas']]
    relevant_signs = {row['sign_id'] for row in padas} | {row['sign_id'] for row in roles}
    for pada in padas:
        sign = pada['sign_id']
        lord = SIGN_LORDS[sign]
        add(f'jaimini.arudha.{pada["house"]}', 'Public image, relationship image or professional image',
            {**pada, 'lord_condition': _planet(analyses[lord]),
             'occupants': [name for name, data in natal['planets'].items()
                           if name in analyses and int(data['longitude'] // 30) == sign]})
    add('jaimini.rashi_drishti', 'Calculated sign aspects; distinct from graha drishti',
        [row for row in jaimini['rashi_drishti'] if row['sign_id'] in relevant_signs])
    add('jaimini.karakamsha', 'AK Navamsa reference; not an independent duplicate of Swamsha',
        jaimini['svamsha_karakamsha']['seven'])

    links = NadiLinkageCalculator(natal).get_nadi_links()
    for planet in scope['planets']:
        link = links[planet]
        connections = []
        for relation, targets in link['connections'].items():
            for target in sorted(targets):
                condition = analyses[target]
                ruled = [int(h) for h, data in houses.items() if data['house_lord'] == target]
                occupied = condition['basic_info']['house']
                overlap = sorted(set([occupied, *ruled]) & set(scope['houses']))
                if overlap or target in selected:
                    connections.append({'relationship': relation, 'planet': target,
                        'natal_occupied_house': occupied, 'natal_ruled_houses': ruled,
                        'topic_connections': {str(h): scope['houses'][h] for h in overlap},
                        'condition': _pick(condition, ('dignity_analysis', 'combustion_status', 'special_lordships'))})
        add(f'nadi.{planet}', 'BNN connections of the topic significator',
            {'planet': planet, 'virtual_position_rules': link['sign_info'], 'connections': connections})

    return {
        'version': EVIDENCE_VERSION, 'topic': topic,
        'calculation_sources': ['ChartScreen house worksheets', 'PlanetAnalyzer', 'NakshatraCalculator',
            'DivisionalChartCalculator', 'ClassicalJaiminiCalculator', 'NadiLinkageCalculator'],
        'conventions': {
            'graha_node_aspects': [7], 'chara_karakas': 'seven; tied ranks are disclosed, not certain',
            'nadi': 'BNN trine/2/12/7 links include exchange and retrograde virtual positions. These are NOT node 5/9 graha aspects or physical natal placements.',
            'vargas': 'D9 corroborates inner strength/relationships; D10 professional expression. Shadbala and physical combustion belong to D1.',
            'scope': 'Evergreen topic reading. No event dates or transit timing. Calculated astrological evidence is not empirical proof of personal traits.',
        },
        'evidence': evidence,
    }
