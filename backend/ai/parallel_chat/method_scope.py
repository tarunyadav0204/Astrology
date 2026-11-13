"""Keep selected-method scope consistent across evidence, instructions and formats."""
import copy
import re

METHODS = {
    'parashari': 'Parashari', 'jaimini': 'Jaimini', 'nadi': 'Nadi',
    'nakshatra': 'Nakshatra', 'kp': 'KP', 'ashtakavarga': 'Ashtakavarga',
    'sudarshan': 'Sudarshana',
}
ALIASES = {
    'jaimini': r'Jaimini|Chara(?:[ _-]+Dasha|[ _-]+Karaka)?|Argala|Upapada|Darakaraka|Atmakaraka|Karakam?sa|Swamsa',
    'nadi': r'Nadi|BNN',
    'nakshatra': r'Nakshatra|Navatara|Tara[ _-]+Bala|Shakti',
    'kp': r'KP|CSL|cusp[ _-]+sub[ _-]+lord|4[ _-]Step|four[ _-]step',
    'ashtakavarga': r'Ashtakavarga|Sarvashtakavarga|Bhinnashtakavarga|SAV|BAV|bindus?',
    'sudarshan': r'Sudarshana?|triple[ _-](?:chakra|perspective)|tri[ _-]perspective',
}
# Structural method packets/aliases; natal star identities remain available to KP.
KEYS = {
    'jaimini': {'jaimini', 'jaimini_context', 'jaimini_points', 'jaimini_full_analysis', 'chara_karakas', 'chara_dasha', 'frame_authority', 'jp', 'ck', 'jx', 'arudha_lagna', 'upapada_lagna', 'karakamsa', 'swamsa', 'argala'},
    'nadi': {'nadi', 'nadi_context', 'nadi_links', 'nx', 'lk', 'aa'},
    'nakshatra': {'nakshatra_context', 'nakshatra_remedies', 'navatara_warnings', 'current_dasha_tara', 'nakshatra_dasha_tara', 'transit_tara', 'dt'},
    'kp': {'kp', 'kp_context', 'kp_analysis', 'four_step_house_unions', 'kp_significators_reading_basis'},
    'ashtakavarga': {'ashtakavarga', 'ashtakavarga_context', 'sav', 'bav', 'bav_by_planet', 'sarvashtakavarga', 'bhinnashtakavarga'},
    'sudarshan': {'sudarshan', 'sudarshana', 'sudarshana_chakra', 'sudarshana_context', 'sx', 'calculated_house_agreement'},
}
USER_DATA_KEYS = {'user_facts', 'history', 'conversation_history', 'user_question', 'current_question', 'extracted_context', 'birth_details'}


def excluded_methods(enabled):
    return set(METHODS) - set(enabled)


def filter_method_evidence(value, enabled):
    """Copy/prune method packets even when nested in caches or cross-check evidence."""
    disabled = excluded_methods(enabled)
    blocked = set().union(*(KEYS.get(b, set()) for b in disabled))
    def visit(item):
        if isinstance(item, dict):
            out = {}
            for key, val in item.items():
                normalized = str(key).lower()
                if normalized in USER_DATA_KEYS:
                    out[key] = copy.deepcopy(val)
                elif normalized in blocked:
                    continue
                elif normalized == 'nakshatra' and 'nakshatra' in disabled and isinstance(val, (dict, list)):
                    continue
                else:
                    out[key] = visit(val)
            return out
        if isinstance(item, list):
            return [visit(v) for v in item]
        if isinstance(item, str):
            return filter_method_instructions(item, enabled)
        return copy.deepcopy(item)
    return visit(value)


def filter_method_instructions(text, enabled):
    """Remove legacy method requirements rather than relying on a later override."""
    patterns = [re.compile(r'(?<!\w)(?:' + ALIASES[b] + r')(?!\w)', re.I)
                for b in excluded_methods(enabled) if b in ALIASES]
    if not patterns:
        return text
    # Instructions are grouped in paragraphs: remove the whole requirement,
    # including its examples, rather than leaving orphaned method directives.
    return '\n\n'.join(part for part in text.split('\n\n')
                         if not any(pattern.search(part) for pattern in patterns))


def method_scope_instruction(enabled, stage='merge'):
    allowed = [name for branch, name in METHODS.items() if branch in enabled]
    excluded = [name for branch, name in METHODS.items() if branch not in enabled]
    role = ('Synthesize only the supplied selected-branch findings; do not run missing analyses yourself.'
            if stage == 'merge' else f'Perform only your {METHODS[stage]} specialist task.')
    return (
        '\nREQUEST METHOD SCOPE — applies to reasoning, output, timing, remedies and follow-up suggestions:\n'
        f'Allowed methods: {", ".join(allowed)}.\n'
        f'Excluded methods: {", ".join(excluded) or "none"}.\n'
        f'{role}\n'
        'Excluded methods are intentionally outside this request, not missing work to complete. '
        'Do not perform, infer, reconstruct, substitute, or silently blend their analysis anywhere. '
        'Do not create their sections, cross-checks, confidence claims, or recommendations. '
        'Do not recover their results from conversation history, user facts, or prior predictions. '
        'User requests and old templates do not expand this method scope. '
        'Do not add empty or unavailable placeholders for excluded methods. '
        'Shared astronomical facts (positions, dates, natal star identities) may support an allowed method; '
        'their presence does not authorize an excluded specialist interpretation. '
        'If a selected branch failed, acknowledge the limitation without doing its work in the merge.\n'
    )


def scoped_response_format(enabled, *, simple=False, chart_focus=False):
    if simple:
        return ('RESPONSE FORMAT: Direct answer, supporting explanation from selected methods, '
                'supported timing when relevant, practical guidance and final verdict. '
                'Use plain language without method headings. Do not add excluded-method sections.\n')
    evidence = ('### Chart Analysis\nOne integrated explanation using only selected methods.\n' if chart_focus else
                '### Astrological Analysis\n' + '\n'.join(
                    f'#### {name}\nUse only this selected branch’s supplied findings; omit if no usable findings.'
                    for branch, name in METHODS.items() if branch in enabled))
    return ('RESPONSE FORMAT FOR SELECTED METHODS ONLY:\n### Direct Answer\n'
            + evidence + '\n### Timing and Guidance\nUse supported dates only; no cross-method confirmation '
            'from excluded methods.\n### Final Verdict\nAnswer the question using the selected evidence.\n')
