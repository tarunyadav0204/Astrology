"""Deduplicate model-facing D1 data without mutating calculator evidence."""
import copy


def compact_shared_d1(chart):
    if not isinstance(chart, dict):
        return chart
    out = copy.deepcopy(chart)
    planets = out.get('planets') or {}
    combustion = out.get('combustion') or {}
    repeated = combustion.get('planets')
    if isinstance(repeated, dict) and repeated and all(
        p in planets and planets[p].get('combustion') == row for p, row in repeated.items()
    ):
        combustion.pop('planets')
    removed_source = False
    for name, row in planets.items():
        burn = row.get('combustion')
        if isinstance(burn, dict):
            if combustion.get('source') and burn.get('source') == combustion['source']:
                burn.pop('source')
                removed_source = True
            if burn.get('planet') == name:
                burn.pop('planet')
        if 'pada' in row and row.get('nakshatra_pada') == row['pada']:
            row.pop('pada')
    if removed_source:
        combustion['source_scope'] = 'This source applies to every planets.*.combustion row.'
    aspects = out.get('graha_drishti_by_house') or {}
    for i, house in enumerate(out.get('houses') or [], 1):
        if 'graha_drishti' in house and house['graha_drishti'] == aspects.get(str(i)):
            house.pop('graha_drishti')
    chalit = out.get('bhav_chalit')
    if isinstance(chalit, dict) and isinstance(chalit.get('planets'), dict):
        overrides = {}
        for name, row in chalit['planets'].items():
            original = chart.get('planets', {}).get(name, {})
            differences = {k: v for k, v in row.items() if k not in original or original[k] != v}
            if differences:
                overrides[name] = differences
        chalit['planets'] = overrides
        notes = ['Inherit D1 planet fields; these are Chalit overrides.']
        if chalit.get('cusps') == [h.get('longitude') for h in out.get('houses', [])] and 'cusps' in chalit:
            chalit.pop('cusps')
            notes.append('Cusps equal houses[].longitude.')
        if 'ascendant' in chalit and chalit['ascendant'] == out.get('ascendant'):
            chalit.pop('ascendant')
            notes.append('Ascendant is D1 ascendant.')
        houses = out.get('houses') or []
        if houses and chalit.get('ascendant_sign_name') == houses[0].get('sign_name'):
            chalit.pop('ascendant_sign_name', None)
        chalit['inheritance'] = ' '.join(notes)
    delivery = out.get('planet_result_delivery') or {}
    removed_timing = False
    for name, row in (delivery.get('planets') or {}).items():
        if row.get('planet') == name:
            row.pop('planet')
        if row.get('timing') == {'activation_planet': name, 'rule': 'judge_in_dasha_and_transit_context'}:
            row.pop('timing')
            removed_timing = True
    if removed_timing:
        delivery['timing_rule'] = 'Each keyed planet is its activation_planet; judge_in_dasha_and_transit_context.'
    return out


def compact_calculation_audits(chart):
    """Keep interpretive results, strip duplicate rule text and intermediate clock traces."""
    out = copy.deepcopy(chart)
    for row in (out.get('neecha_bhanga') or {}).values():
        conditions = row.get('conditions_met') or []
        for condition in conditions:
            if condition.get('description') == condition.get('condition'):
                condition.pop('description', None)
        matched = [c.get('rule_id') for c in conditions]
        if row.get('matched_rule_ids') == matched:
            row.pop('matched_rule_ids')
        # Matched tests repeat each condition's identity, reference and verdict.
        evaluated = row.get('rules_evaluated')
        if isinstance(evaluated, list):
            by_id = {c.get('rule_id'): c for c in conditions}
            row['rules_evaluated'] = [r for r in evaluated if not (
                r.get('matched') is True and r.get('applicable') is True
                and r.get('rule_id') in by_id
                and r.get('reference') == by_id[r['rule_id']].get('reference'))]
            row['matched_conditions_policy'] = 'conditions_met are applicable matched tests; rules_evaluated contains remaining tests.'
    upagraha = out.get('upagraha_calculation')
    if isinstance(upagraha, dict):
        for row in upagraha.get('points', []):
            for key in ('segment_start_local', 'segment_end_local'):
                row.pop(key, None)
        frame = upagraha.get('day_night_frame')
        if isinstance(frame, dict):
            upagraha['day_night_frame'] = {k: v for k, v in frame.items()
                if k in ('is_day_birth', 'weekday', 'weekday_lord', 'first_segment_lord')}
    # D1 division duplicates the planet positions; retain other divisional results.
    divisions = out.get('divisions') or {}
    d1 = divisions.get('D1')
    planets = out.get('planets') or {}
    if isinstance(d1, dict) and all(p in planets and all(planets[p].get(k) == v for k, v in row.items())
                                   for p, row in d1.items()):
        divisions.pop('D1')
    return out
