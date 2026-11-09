"""Concurrent activation evidence; the model, not a fixed event table, synthesizes events."""
from datetime import datetime
from itertools import combinations


def build_synthesis_space(period, activation, facts):
    sources = {}
    prefix = period['id']
    for i, link in enumerate(activation['house_links'], 1):
        sources[f'{prefix}_natal_{i}'] = {
            **link, 'basis': 'natal', 'houses': [link['house']],
            'evidence_ref': f"planet_{link.get('via', link['planet'])}"}
    for ref, fact in facts.items():
        if fact['kind'] != 'transit_background':
            continue
        row = fact['value']
        levels = [level for level, name in activation['levels'].items()
                  if name == row['transiting_planet']]
        sources[ref] = {'basis': 'transit', 'levels': levels, 'background_only': not bool(levels),
            'planet': row['transiting_planet'], 'evidence_ref': ref,
            'start_at': row['start_at'], 'end_at': row['end_at'],
            'occupation_house': row['natal_house'],
            'aspect_houses': row['aspected_natal_houses'],
            'houses': sorted({row['natal_house'], *row['aspected_natal_houses']})}
    start, end = (datetime.fromisoformat(period[k]) for k in ('start_at', 'end_at'))
    transits = {ref: row for ref, row in sources.items() if row['basis'] == 'transit'}
    natal = [ref for ref, row in sources.items() if row['basis'] == 'natal']
    boundaries = sorted({start, end, *(max(start, min(end, datetime.fromisoformat(row[k])))
        for row in transits.values() for k in ('start_at', 'end_at'))})
    windows = []
    candidate_sets = {2: set(), 3: set()}
    for left, right in zip(boundaries, boundaries[1:]):
        active = [ref for ref, row in transits.items()
                  if datetime.fromisoformat(row['start_at']) <= left
                  and datetime.fromisoformat(row['end_at']) >= right]
        # Every active lord must have calculated occupancy throughout the interval.
        covered = {level for ref in active for level in sources[ref]['levels']}
        if covered != set(activation['levels']):
            raise ValueError(f'Missing period-lord transit coverage in {prefix}: {left.isoformat()}')
        direct = sorted({n for ref in natal for n in sources[ref]['houses'] if sources[ref]['direct']})
        transit_houses = sorted({n for ref in active if not sources[ref]['background_only'] for n in sources[ref]['houses']})
        houses = sorted(set(direct) | set(transit_houses))
        for size in candidate_sets:
            candidate_sets[size].update(combinations(houses, size))
        windows.append({'id': f'{prefix}_window_{len(windows) + 1}',
            'start_at': left.isoformat(), 'end_at': right.isoformat(),
            'transit_source_ids': active, 'background_source_ids': [ref for ref in active if sources[ref]['background_only']], 'direct_natal_houses': direct,
            'transit_houses': transit_houses, 'active_houses': houses})
    return {'sources': sources, 'constant_natal_source_ids': natal, 'windows': windows,
        'candidate_pairs': [list(c) for c in sorted(candidate_sets[2])],
        'candidate_triples': [list(c) for c in sorted(candidate_sets[3])],
        'instruction': 'Pairs/triples are an exhaustive concurrent search space, NOT predictions or meaningful combinations by themselves. Explore all for natural event links, plus coherent larger clusters and single-house branches. Indirect natal sources remain separate and must be named as indirect. background_only transit sources can reinforce an active period-lord route but do not become MD/AD/PD activations or independent core-house candidates. Select events using carriers, natal promise, condition and overlapping windows; never mix transit sources from disjoint windows. Repeated MD/AD/PD roles of one planet are one physical transit, not independent confirmations.'}


def validate_exploration(row, brief):
    space = brief['synthesis_space']
    sources = space['sources']
    expected_houses = {h for w in space['windows'] for h in w['active_houses']}
    review = row.get('activation_review')
    if not isinstance(review, list) or {r.get('level') for r in review if isinstance(r, dict)} != set(brief['activation']['levels']):
        raise ValueError('Assess natal and transit activation for every MD/AD/PD level')
    for r in review:
        if not all(isinstance(r.get(k), str) and r[k].strip() for k in ('natal_assessment', 'transit_assessment')):
            raise ValueError('Missing natal/transit assessment')
    if set(row.get('considered_houses', [])) != expected_houses:
        raise ValueError(f'Explore all concurrently activated houses; expected {sorted(expected_houses)}')
    meanings = row.get('signification_review')
    if not isinstance(meanings, list) or {r.get('house') for r in meanings if isinstance(r, dict)} != expected_houses:
        raise ValueError(f'Review significations of every activated house before selecting events: one signification_review row for each house {sorted(expected_houses)}, including background-only houses')
    for r in meanings:
        if not all(isinstance(r.get(k), str) and r[k].strip() for k in ('meanings_considered', 'supported_event_branches', 'excluded_or_background')):
            raise ValueError('Explain signification coverage and exclusions')
    ledger = row.get('combination_exploration')
    if not isinstance(ledger, list) or not ledger:
        raise ValueError('Missing meaningful house-combination exploration')
    windows = {w['id']: w for w in space['windows']}
    themes = {t['theme'] for t in row['themes']}
    selected_themes = set()
    for item in ledger:
        if not isinstance(item, dict) or item.get('decision') not in {'selected', 'merged', 'not_supported', 'background', 'rejected'}:
            raise ValueError('Invalid combination exploration decision')
        houses, refs, win_refs = item.get('houses'), item.get('source_ids'), item.get('window_refs')
        if not isinstance(houses, list) or not houses or any(type(h) is not int or not 1 <= h <= 12 for h in houses):
            raise ValueError('Invalid combination houses')
        if not isinstance(refs, list) or not refs or any(ref not in sources for ref in refs):
            raise ValueError(f'Unknown activation source in combination {refs}; valid source IDs: {list(sources)}')
        if not isinstance(win_refs, list) or not win_refs or any(ref not in windows for ref in win_refs):
            raise ValueError('Unknown concurrent window in combination')
        if all(sources[ref].get('background_only', False) for ref in refs):
            raise ValueError('An event route needs active period-lord evidence, not only background transits')
        missing = set(houses) - {h for ref in refs for h in sources[ref]['houses']}
        if missing:
            # Resolve a missing citation only from calculated direct period-lord
            # activations that exist throughout every requested window. This does
            # not invent a house, change timing or write an event. Keep provenance.
            common = set(space['constant_natal_source_ids'])
            common |= set.intersection(*(set(windows[ref]['transit_source_ids']) for ref in win_refs))
            additions = sorted(ref for ref in common
                if missing.intersection(sources[ref]['houses'])
                and (sources[ref].get('direct') is True or
                     (sources[ref]['basis'] == 'transit' and not sources[ref].get('background_only'))))
            if not missing <= {h for ref in additions for h in sources[ref]['houses']}:
                raise ValueError(f'Combination houses lack cited activation sources: {sorted(missing)}')
            item['resolved_source_ids'] = additions
            item['source_ids'] = refs = list(dict.fromkeys([*refs, *additions]))
        for ref in win_refs:
            available = set(space['constant_natal_source_ids']) | set(windows[ref]['transit_source_ids'])
            if not set(refs) <= available:
                raise ValueError(f'Combination mixes nonconcurrent transit activations: sources {refs}, window {ref}; available transit sources {windows[ref]["transit_source_ids"]}')
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in ('signification_link', 'reason')):
            raise ValueError('Explain selected significations and event support or exclusion')
        if item['decision'] in {'selected', 'merged'}:
            if item.get('theme') not in themes:
                if item['decision'] == 'merged':
                    # A discarded/merged candidate label is editorial metadata.
                    # Keep the discrepancy visible to coverage review without
                    # rejecting an otherwise fully traced set of selected themes.
                    item['mapping_warning'] = 'Merged candidate label is not a final theme; review coverage and merge destination.'
                    continue
                raise ValueError(f'Selected combination theme {item.get("theme")!r} must exactly match one of {sorted(themes)}')
            selected_themes.add(item['theme'])
    if selected_themes != themes:
        raise ValueError('Every planned theme needs a traceable combination route')
