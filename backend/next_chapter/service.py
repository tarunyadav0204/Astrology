"""Auditable next-AD dossier; optional LLM interpretation uses computed evidence."""
from time import monotonic
from zoneinfo import ZoneInfo

from prediction_engine.contracts import BirthChartInput
from . import ENGINE_VERSION
from .evidence import build_activation, build_foundation
from .periods import select_next_antardasha
from .transits import build_pd_transits, make_state_reader, utc


def build_next_chapter(birth_data, as_of, *, life_context='', selection='next'):
    birth = BirthChartInput.from_mapping(birth_data).to_calculator_dict()
    started = monotonic()
    spine = select_next_antardasha(birth, as_of, selection=selection)
    foundation = build_foundation(birth, spine['antardasha']['start_at'][:10])
    chart = foundation['chart']
    background = {'MD': spine['mahadasha']['planet'], 'AD': spine['antardasha']['planet']}
    state_at = make_state_reader()
    periods = []
    previous_focus = set()
    for pd in spine['pratyantardashas']:
        levels = {**background, 'PD': pd['planet']}
        activation = build_activation(chart, levels)
        focus = set(activation['pd_focus_houses'])
        periods.append({**pd, 'activation': activation,
            'change_from_previous_pd': {
                'newly_emphasized_houses': sorted(focus - previous_focus),
                'no_longer_pd_emphasized_houses': sorted(previous_focus - focus),
                'continuing_pd_houses': sorted(focus & previous_focus)},
            'transits': build_pd_transits(chart, pd, levels, state_at)})
        previous_focus = focus
    return {'engine_version': ENGINE_VERSION, 'status': 'calculated',
        'native': {'name': birth['name'], 'gender': birth['gender'],
                   'birth_date': birth['date'], 'life_context': life_context},
        'spine': spine, 'foundation': foundation,
        'chapter_activation': build_activation(chart, background), 'periods': periods,
        'calculation_seconds': round(monotonic() - started, 3),
        'scope': {
            'node_aspects': 'Seventh aspect only; fifth/ninth excluded. Conjunctions and dispositors are separate relationships.',
            'implemented': ['Vimshottari MD/AD/PD', 'ChartScreen natal worksheets',
                'house combinations', 'MD/AD/PD natal relationships',
                'transit house and nakshatra intervals', 'degree contacts to active natal lords',
                'Sun triggers', 'Jupiter/Saturn/node background', 'retrograde repeat passes'],
            'not_calculated': ['KP cusp sub-lord events', 'Chara Dasha periods',
                               'Nadi-specific timing rules', 'event probabilities'],
            'interpretation': 'Several possible manifestations can share the same house activation. Astronomical precision is not certainty about a life event.',
        }}


def narration_context(dossier):
    """Remove duplicate chart/UI detail; retain all condition factors and exact contacts."""
    foundation = dossier['foundation']
    zone = ZoneInfo(dossier['spine']['timezone'])

    def local_timestamps(value):
        if isinstance(value, list):
            return [local_timestamps(item) for item in value]
        if isinstance(value, dict):
            return {key: utc(item).astimezone(zone).isoformat()
                    if key in {'start_at', 'end_at', 'at'} and isinstance(item, str)
                    else local_timestamps(item) for key, item in value.items()}
        return value
    houses = {key: {k: row[k] for k in (
        'evidence_id', 'house_num', 'sign_name', 'house_lord', 'significance',
        'support_factors', 'stress_factors', 'argala', 'points_in_house',
        'chara_karakas_here', 'natural_karakas', 'related_varga')}
        | {'ashtakavarga': row['raw']['ashtakavarga']} for key, row in foundation['houses'].items()}
    planets = {key: {'evidence_id': row['evidence_id'], 'worksheet': row['worksheet'],
        'analysis': {k: v for k, v in row['analysis'].items() if k not in {'basic_info', 'overall_assessment'}}}
        for key, row in foundation['planets'].items()}
    for row in houses.values():
        for key in ('support_factors', 'stress_factors'):
            row[key] = [factor['label'] for factor in row[key]]
    # Put repeated vocabulary in a catalog once. Keep the full evidence file for audit.
    life_areas, combinations = {}, {}
    def activation_context(activation):
        for area in activation['life_areas']:
            life_areas[str(area['house'])] = area
        for combination in activation['house_combinations']:
            combinations[combination['id']] = {k: v for k, v in combination.items() if k != 'pd_emphasis'}
        return {key: value for key, value in activation.items() if key not in {'life_areas', 'house_combinations'}} | {
            'house_combinations': [{'id': row['id'], 'pd_emphasis': row['pd_emphasis']}
                                  for row in activation['house_combinations']]}
    chapter = activation_context(dossier['chapter_activation'])
    periods = []
    for pd in dossier['periods']:
        transits = local_timestamps(pd['transits'])
        for contact in transits['contacts']:
            number = contact['aspect_from_planet']
            relation = ('conjunction / same longitude' if number == 1 else
                        f'{number}th graha drishti / directed aspect')
            contact['reading_label'] = (
                f"Transiting {contact['transiting_planet']} → natal {contact['natal_planet']}: "
                f"{relation}; local window {contact['start_at'][:10]} to {contact['end_at'][:10]}.")
        # Column-oriented occupancy is lossless and avoids repeating long field names.
        occupancy = transits.pop('house_occupancy')
        columns = list(occupancy[0]) if occupancy else []
        transits['house_occupancy'] = {'columns': columns,
            'rows': [[row[column] for column in columns] for row in occupancy]}
        # Surface sign-level changes in readable records. The detailed occupancy
        # table remains available, but nakshatra splits must not hide slow moves.
        background = []
        for planet in dict.fromkeys(('Jupiter', 'Saturn', 'Rahu', 'Ketu', *pd['activation']['levels'].values())):
            segments = []
            for segment in occupancy:
                if segment['transiting_planet'] != planet:
                    continue
                row = {key: segment[key] for key in ('start_at', 'end_at',
                    'transiting_planet', 'sign_number', 'natal_house', 'aspected_natal_houses')}
                if segments and segments[-1]['end_at'] == row['start_at'] and segments[-1]['sign_number'] == row['sign_number']:
                    segments[-1]['end_at'] = row['end_at']
                else:
                    segments.append(row)
            for row in segments:
                # Keep house-axis evidence explicit even when the degree contact
                # lies outside this PD. House opposition is not an exact return.
                row['relations_to_natal'] = [
                    {'natal_planet': name, 'natal_house': natal['house'],
                     'relation': 'same_sign' if natal['sign'] + 1 == row['sign_number'] else 'whole_sign_aspect',
                     'aspect_from_planet': (natal['house'] - row['natal_house']) % 12 + 1}
                    for name, natal in foundation['chart']['planets'].items()
                    if natal['sign'] + 1 == row['sign_number'] or natal['house'] in row['aspected_natal_houses']]
                row['is_antardasha_lord'] = planet == dossier['spine']['antardasha']['planet']
            background.extend(segments)
        periods.append({**pd, 'activation': activation_context(pd['activation']),
            'background_house_transits': background, 'transits': transits})
    chart = foundation['chart']
    from .evidence import aspect_houses, ruled_houses
    from calculators.chart_calculator import ChartCalculator
    natal_summary = {
        'ascendant_sign': ChartCalculator.SIGN_NAMES[int(chart['ascendant'] / 30)],
        'ascendant_degree_in_sign': chart['ascendant'] % 30,
        'planets': {name: {**row['worksheet'], 'ruled_houses': ruled_houses(chart, name),
            'aspected_houses': aspect_houses(name, row['house']),
            'same_sign_companions': [{'planet': other,
                'separation_degrees': round(abs(row['longitude'] - other_row['longitude']), 3)}
                for other, other_row in foundation['planets'].items()
                if other != name and row['sign'] == other_row['sign']]}
            for name, row in foundation['planets'].items()},
        'authority': 'These are canonical D1 placements, lordships and whole-sign aspects. Same-sign conjunction does not mean a close degree conjunction.'}
    return {**{key: dossier[key] for key in ('native', 'spine', 'scope')},
            'natal_summary': natal_summary,
            'chapter_activation': chapter, 'periods': periods,
            'life_area_catalog': life_areas, 'combination_catalog': combinations,
            'foundation': {'houses': houses, 'planets': planets}}


def attach_narration(dossier, narrative):
    from .validation import warn
    """Validate structure/references only; do not gate possibilities through event scoring."""
    if not isinstance(narrative, dict):
        raise ValueError('Next Chapter narration must be an object')
    # Some otherwise complete responses put the closing paragraph in a final
    # singleton object in periods. Move that existing text; never synthesize it
    # or discard a real period to make a malformed response pass.
    rows = narrative.get('periods')
    if ('closing' not in narrative and isinstance(rows, list) and len(rows) == 10
            and isinstance(rows[-1], dict) and set(rows[-1]) == {'closing'}
            and isinstance(rows[-1]['closing'], str) and rows[-1]['closing'].strip()):
        narrative = {**narrative, 'closing': rows[-1]['closing'], 'periods': rows[:-1]}
    for key in ('title', 'overview', 'mahadasha_context', 'antardasha_themes', 'closing'):
        if not isinstance(narrative.get(key), str) or not narrative[key].strip():
            raise ValueError(f'Next Chapter narration is missing {key}')
    rows = narrative.get('periods')
    if not isinstance(rows, list) or [row.get('period_id') for row in rows if isinstance(row, dict)] != [pd['id'] for pd in dossier['periods']]:
        raise ValueError('Narration must cover each of the nine PDs in order')
    periods = []
    for row, pd in zip(rows, dossier['periods']):
        if not all(isinstance(row.get(key), str) and row[key].strip() for key in (
            'summary', 'what_changes', 'timing_explanation', 'conditions_and_cautions')):
            raise ValueError(f"Narration is missing the explanation for {pd['id']}")
        manifestations = row.get('manifestations')
        if not isinstance(manifestations, list) or not manifestations:
            raise ValueError(f"Narration is missing possibilities for {pd['id']}")
        contacts = {item['id']: item for item in pd['transits']['contacts']}
        valid_refs = {'house_refs': {f"house_{link['house']}" for link in pd['activation']['house_links']} |
                      {f'house_{n}' for row in pd['transits']['house_occupancy']
                       for n in [row['natal_house'], *row['aspected_natal_houses']]},
                      'planet_refs': {f'planet_{n}' for n in dossier['foundation']['planets']},
                      'contact_refs': set(contacts)}
        enriched = []
        for item in manifestations:
            if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key].strip()
                for key in ('theme', 'why', 'practical_guidance')):
                raise ValueError('A manifestation is missing its explanation')
            possibilities = item.get('possibilities')
            if not isinstance(possibilities, list) or not possibilities or not all(isinstance(p, str) and p.strip() for p in possibilities):
                raise ValueError('A manifestation has no possible outcomes')
            for key, allowed in valid_refs.items():
                refs = item.get(key)
                if not isinstance(refs, list) or not all(isinstance(ref, str) and ref in allowed for ref in refs):
                    warn(f'Unknown {key} in {pd["id"]}')
                    item = {**item, key: [r for r in refs if isinstance(r, str)] if isinstance(refs, list) else []}
            if not item['house_refs'] or not item['planet_refs']:
                warn('A manifestation needs natal house and planet evidence')
            zone = ZoneInfo(dossier['spine']['timezone'])
            enriched.append({**item, 'timing_basis': 'transit_contacts' if item['contact_refs'] else 'pratyantardasha',
                'timing_windows': [{**contacts[ref],
                    'local_start_at': utc(contacts[ref]['start_at']).astimezone(zone).isoformat(),
                    'local_end_at': utc(contacts[ref]['end_at']).astimezone(zone).isoformat()}
                    for ref in dict.fromkeys(item['contact_refs']) if ref in contacts]})
        periods.append({**row, 'start_at': pd['start_at'], 'end_at': pd['end_at'],
            'planet': pd['planet'], 'manifestations': enriched})
    return {**narrative, 'periods': periods}


async def narrate_next_chapter(dossier, language='en', *, model=None, audit_sink=None, resume_audit=None):
    from .pipeline import generate
    if model is None:
        from ai.analysis_llm_backend import build_next_chapter_llm_model
        model, model_id, vendor = build_next_chapter_llm_model()
    else:
        model_id, vendor = 'injected', 'test'
    return await generate(dossier, language, model, model_id, vendor, audit_sink=audit_sink, resume_audit=resume_audit)
