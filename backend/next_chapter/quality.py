"""Observable report diagnostics, not a score for predicting real-life events."""
from collections import Counter
from itertools import combinations
import re


def report_diagnostics(report):
    rows = []
    texts = {}
    for pd in report['periods']:
        possibilities = [s for item in pd['manifestations'] for s in item['possibilities']]
        text = ' '.join(possibilities)
        tokens = re.findall(r'\w+', text.lower(), re.UNICODE)
        texts[pd['period_id']] = set(zip(tokens, tokens[1:], tokens[2:], tokens[3:]))
        refs = set(r for item in pd['manifestations'] for r in item.get('evidence_refs', []))
        rows.append({'period_id': pd['period_id'], 'theme_count': len(pd['manifestations']),
                     'possibility_count': len(possibilities),
                     'declared_av_refs': sorted(r for r in refs if r.startswith('av_')),
                     'declared_varga_refs': sorted(r for r in refs if r.startswith('varga_'))})
    overlap = []
    for (a, left), (b, right) in combinations(texts.items(), 2):
        overlap.append({'periods': [a, b], 'shared_four_word_phrases': len(left & right),
                        'jaccard': round(len(left & right) / max(1, len(left | right)), 4)})
    exact = Counter(s.strip().casefold() for pd in report['periods'] for item in pd['manifestations'] for s in item['possibilities'])
    return {'periods': rows, 'repeated_verbatim_possibilities': sum(n - 1 for n in exact.values() if n > 1),
            'highest_lexical_overlap': sorted(overlap, key=lambda r: r['jaccard'], reverse=True)[:5],
            'interpretation': 'References are declared evidence use, not proof of sound interpretation. Lexical overlap measures repeated wording, not semantic duplication or prediction accuracy.'}
