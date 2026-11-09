"""Small, traceable fact packets for interpretation, separate from drawer verdicts."""
from copy import deepcopy
from .service import narration_context
from .evidence import aspect_houses
from .synthesis import build_synthesis_space
from prediction_engine.house_significations import HOUSE_SIGNIFICATIONS


def build_briefs(dossier):
    context = narration_context(dossier)
    foundation = dossier['foundation']
    facts = {}
    for name, source in foundation['planets'].items():
        analysis = source['analysis']
        row = deepcopy(context['natal_summary']['planets'][name])
        # Preserve the drawer's actual condition parameters, not its heuristic
        # effect scores, canned predictions, or inconsistent duplicate geometry.
        for key in ('combustion', 'neecha_bhanga_source'):
            row.pop(key, None)
        row['functional_nature_details'] = analysis['dignity_analysis'].get('functional_nature_details')
        row['sign_lord_friendship'] = analysis.get('friendship_analysis', {}).get('friendship_matrix', {})
        row['gandanta'] = analysis.get('gandanta_analysis')
        row['aspects_received'] = [
            {'planet': other, 'from_house': r['house']}
            for other, r in foundation['planets'].items()
            if other != name and source['house'] in aspect_houses(other, r['house'])]
        facts[f'planet_{name}'] = {'kind': 'natal_planet', 'value': row}
    for number, row in foundation['houses'].items():
        facts[f'house_{number}'] = {'kind': 'natal_house', 'value': {
            'house': int(number), 'sign': row['sign_name'], 'lord': row['house_lord'],
            'significance': row['significance'],
            'significations': list(HOUSE_SIGNIFICATIONS[int(number)].significations) + (['occult studies', 'astrology', 'hidden knowledge', 'insurance claim or payout'] if int(number) == 8 else []),
            'body_significations': list(HOUSE_SIGNIFICATIONS[int(number)].body_significations),
            'argala': row['argala'],
            'points': row['points_in_house'], 'chara_karakas': row['chara_karakas_here']}}
        facts[f'av_{number}'] = {'kind': 'ashtakavarga', 'value': {
            'house': int(number), 'sign': row['sign_name'], **row['raw']['ashtakavarga']},
            'meaning': 'SAV is this natal house/sign total, not an event probability. lord_bav is the named lord only; givers are individual planet BAV contributions in this sign. Do not substitute SAV for BAV.'}
        if row['related_varga']:
            facts[f'varga_{number}'] = {'kind': 'divisional_worksheet', 'value': row['related_varga'],
                'scope': 'This is one relevant divisional HOUSE worksheet, not the full divisional chart or its ascendant. lord_house/lord_sign_name describe that house lord in this varga only.'}
    briefs = []
    for index, pd in enumerate(context['periods']):
        local_facts = dict(facts)
        for contact in pd['transits']['contacts']:
            local_facts[contact['id']] = {'kind': 'transit_contact', 'value': contact}
        for n, row in enumerate(pd['background_house_transits'], 1):
            local_facts[f"{pd['id']}_background_{n}"] = {'kind': 'transit_background', 'value': row}
        activation = pd['activation']
        relevant = {link['house'] for link in activation['house_links']}
        transit_houses = {n for row in pd['background_house_transits'] for n in [row['natal_house'], *row['aspected_natal_houses']]}
        relevant |= transit_houses
        synthesis_space = build_synthesis_space(pd, activation, local_facts)
        for window in synthesis_space['windows']:
            local_facts[window['id']] = {'kind': 'activation_window',
                'value': {k: window[k] for k in ('start_at', 'end_at', 'active_houses')},
                'evidence_refs': window['transit_source_ids'],
                'meaning': 'Concurrent activation interval, not an exact degree contact or promised event date.'}
        briefs.append({
            'period': {k: pd[k] for k in ('id', 'planet', 'start_at', 'end_at')},
            'synthesis_space': synthesis_space,
            'period_lord_transit_refs': [key for key, fact in local_facts.items() if fact['kind'] == 'transit_background' and fact['value']['transiting_planet'] in activation['levels'].values()],
            'activation': activation, 'change_from_previous_pd': pd['change_from_previous_pd'],
            'transit_activated_houses': sorted(transit_houses),
            'ad_transit_refs': [key for key, fact in local_facts.items() if fact['kind'] == 'transit_background' and fact['value']['is_antardasha_lord']],
            'house_coverage': [{'house_ref': f'house_{n}', **facts[f'house_{n}']['value'],
                                'natal_links': [link for link in activation['house_links'] if link['house'] == n],
                                'transit_refs': [key for key, fact in local_facts.items() if fact['kind'] == 'transit_background' and n in [fact['value']['natal_house'], *fact['value']['aspected_natal_houses']]]}
                               for n in sorted(relevant)],
            'previous_pd': context['periods'][index - 1]['planet'] if index else None,
            'av_to_consider': [f'av_{n}' for n in sorted(relevant)],
            'vargas_to_consider': [f'varga_{n}' for n in sorted(relevant) if f'varga_{n}' in facts],
            'facts': local_facts,
        })
    shared = {k: context[k] for k in ('native', 'spine', 'scope', 'chapter_activation')}
    # Keep the older engine's breadth and house-combination meanings, but do not
    # seed the model with its reusable sentence fragments. Live review showed
    # those fragments being copied as predictions across successive PDs.
    for key in ('life_area_catalog', 'combination_catalog'):
        shared[key] = {name: {k: v for k, v in row.items() if k != 'possibilities'}
                       for name, row in context[key].items()}
    # Merge only adjoining equal sign-level MD/AD-lord segments across PD boundaries.
    # The complete AD movement belongs before individual PD interpretations.
    chapter_segments = []
    for level, planet in context['chapter_activation']['levels'].items():
        segments = []
        for pd in briefs:
            for fact in pd['facts'].values():
                if fact['kind'] != 'transit_background' or fact['value']['transiting_planet'] != planet:
                    continue
                row = deepcopy(fact['value'])
                row['period_level'] = level
                if segments and segments[-1]['end_at'] == row['start_at'] and segments[-1]['sign_number'] == row['sign_number']:
                    segments[-1]['end_at'] = row['end_at']
                else:
                    segments.append(row)
        chapter_segments.extend(segments)
    chapter_facts = dict(facts)
    for i, row in enumerate(chapter_segments, 1):
        chapter_facts[f"{row['period_level'].lower()}_transit_{i}"] = {'kind': 'transit_background', 'value': row}
    chapter_houses = {link['house'] for link in context['chapter_activation']['house_links']}
    chapter_houses |= {n for row in chapter_segments for n in [row['natal_house'], *row['aspected_natal_houses']]}
    shared['antardasha_packet'] = {
        'activation': context['chapter_activation'],
        'transit_refs': [key for key, fact in chapter_facts.items() if fact['kind'] == 'transit_background'],
        'facts': {key: value for key, value in chapter_facts.items() if value['kind'] == 'transit_background'},
        'house_coverage': [{'house_ref': f'house_{n}', **facts[f'house_{n}']['value'],
                            'natal_links': [link for link in context['chapter_activation']['house_links'] if link['house'] == n]}
                           for n in sorted(chapter_houses)],
        'instruction': 'Develop the full supported AD event spectrum first. Distinguish direct AD links, MD background, dispositor links and transit-only topics. PDs refine timing; they must not be the only place concrete events appear.'}
    return {'chapter_facts': chapter_facts, 'shared': shared,
            'ascendant': {k: v for k, v in context['natal_summary'].items() if k != 'planets'},
            'facts': facts, 'periods': briefs}


def batch_packet(briefs, ids):
    selected = [pd for pd in briefs['periods'] if pd['period']['id'] in ids]
    # Shared natal facts occur once per request, not once per PD.
    priority = []
    for pd in selected:
        names = list(dict.fromkeys(pd['activation']['levels'].values()))
        conditions = {}
        for name in names:
            planet = briefs['facts'][f'planet_{name}']['value']
            conditions[name] = {key: planet.get(key) for key in (
                'house', 'ruled_houses', 'dignity', 'functional_nature_details', 'special_roles',
                'shadbala_rupas', 'meets_minimum', 'combust', 'retrograde', 'gandanta',
                'aspects_received', 'same_sign_companions')}
        pd_name = pd['period']['planet']
        bav = {}
        for house in pd['activation']['pd_focus_houses']:
            av = briefs['facts'][f'av_{house}']['value']
            bav[str(house)] = {'SAV': av['sav']['house_points'],
                'PD_planet_BAV': next((g['bindus'] for g in av.get('givers', []) if g['planet'] == pd_name), None)}
        priority.append({'period_id': pd['period']['id'], 'lords_to_reconcile': conditions,
                         'PD_planet': pd_name, 'PD_house_scores': bav,
                         'instruction': 'Reconcile these conditions before proposing outcomes. Own sign or strength does not erase functional challenges, special roles, or received aspects. Null node BAV is not zero. A higher SAV in a difficult house does not automatically mean smooth favorable outcomes.'})
    return {'priority_conditions': priority, **briefs['shared'], 'ascendant': briefs['ascendant'], 'natal_facts': briefs['facts'],
            'periods': [{**pd, 'facts': {k: v for k, v in pd['facts'].items() if k not in briefs['facts']}}
                        for pd in selected]}
