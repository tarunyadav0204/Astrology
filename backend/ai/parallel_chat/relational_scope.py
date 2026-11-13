"""Apply the selected methods to every relational model input, including caches."""
from copy import deepcopy
from ai.parallel_chat.method_scope import (
    METHODS, USER_DATA_KEYS, filter_method_evidence, filter_method_instructions,
)


def relational_methods(branches):
    return {b.removesuffix('_relational') for b in branches} & set(METHODS)


def scoped_relational_instructions(text, methods):
    # Relational prompts contain long bullet blocks mixing multiple methods.
    # Remove individual directives, preserving unrelated question/safety rules.
    omitted = ['strongest 3-5 method confirmations']
    if 'nadi' not in methods:
        omitted += ['cross_chart_contacts', 'cross-chart contacts', 'cross_chart_contact_summary', 'relationship_tone_summary']
    return '\n'.join(filter_method_instructions(line, methods) for line in text.splitlines()
                     if not any(marker in line.lower() for marker in omitted))


def scoped_relational_evidence(value, methods):
    disabled = set(METHODS) - set(methods)
    extra = set()
    if 'nadi' in disabled:
        # These carry interpreted graha linkage themes, not just raw positions.
        extra |= {'cross_chart_contacts', 'cross_chart_contact_summary', 'relationship_tone_summary'}
    if 'nakshatra' in disabled:
        extra |= {'kuta_compatibility', 'nakshatra_flavor_native', 'nakshatra_flavor_partner'}
    def walk(item):
        if isinstance(item, dict):
            out = {}
            for key, val in item.items():
                k = str(key).lower()
                if k in USER_DATA_KEYS:
                    out[key] = deepcopy(val)
                elif k in extra or any(k == m or k.startswith(m + '_') or
                        (m == 'sudarshan' and k.startswith('sudarshana_')) for m in disabled):
                    continue
                else:
                    out[key] = walk(val)
            return out
        if isinstance(item, list):
            return [walk(v) for v in item]
        return deepcopy(item)
    return filter_method_evidence(walk(value), methods)


def relational_response_format(methods):
    names = ', '.join(METHODS[m] for m in METHODS if m in methods)
    return (
        '\nRELATIONAL OUTPUT FORMAT (overrides earlier method-count requirements):\n'
        'Answer the exact relationship question with Direct Answer, Main Evidence, '
        'supported Current Activation/Timing, Limits and Practical Guidance. '
        'Compare both people using only selected evidence. For behavioral questions, '
        'explain Core Nature and Interaction Pattern using the selected methods. '
        f'Method Cross-Checks may cite only: {names}. '
        'Use however many selected methods actually contributed, even only one; '
        'there is no minimum number of confirmations. Omit unavailable sections '
        'rather than filling them with another method.\n'
    )
