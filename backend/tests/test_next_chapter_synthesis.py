from copy import deepcopy

import pytest

from next_chapter.synthesis import build_synthesis_space, validate_exploration


def fixture():
    period = {'id': 'pd_test', 'start_at': '2026-01-01T00:00:00+00:00', 'end_at': '2026-03-01T00:00:00+00:00'}
    activation = {'levels': {'MD': 'Saturn', 'AD': 'Rahu', 'PD': 'Rahu'},
        'house_links': [
            {'level': 'MD', 'planet': 'Saturn', 'relation': 'occupation', 'house': 2, 'direct': True},
            {'level': 'AD', 'planet': 'Rahu', 'relation': 'natal_aspect', 'house': 8, 'direct': True},
            {'level': 'PD', 'planet': 'Rahu', 'relation': 'sign_dispositor', 'via': 'Sun', 'house': 9, 'direct': False}]}
    def fact(planet, house, aspects, start, end):
        return {'kind': 'transit_background', 'value': {'transiting_planet': planet,
            'natal_house': house, 'aspected_natal_houses': aspects, 'start_at': start, 'end_at': end}}
    start, end, split = period['start_at'], period['end_at'], '2026-02-01T00:00:00+00:00'
    facts = {'saturn_before': fact('Saturn', 9, [11, 3, 6], start, split),
             'saturn_after': fact('Saturn', 10, [12, 4, 7], split, end),
             'rahu': fact('Rahu', 8, [2], start, end),
             'other_background': fact('Jupiter', 1, [5, 7, 9], start, end)}
    return period, activation, facts


def test_concurrent_space_retains_sources_without_combining_disjoint_transits():
    p, a, f = fixture()
    space = build_synthesis_space(p, a, f)
    assert len(space['windows']) == 2
    assert space['windows'][0]['end_at'] == space['windows'][1]['start_at']
    assert space['sources']['rahu']['levels'] == ['AD', 'PD']
    assert space['sources']['other_background']['background_only'] is True
    assert space['sources']['other_background']['levels'] == []
    assert 5 not in space['windows'][0]['active_houses']
    assert [3, 11] in space['candidate_pairs']  # Not restricted to fixed legacy combinations.
    assert [3, 12] not in space['candidate_pairs']  # Never concurrent in this test.
    assert [2, 3, 11] in space['candidate_triples']
    assert space['sources']['pd_test_natal_3']['direct'] is False
    assert space['sources']['pd_test_natal_3']['via'] == 'Sun'


def test_missing_active_lord_coverage_fails_instead_of_inventing_transits():
    p, a, f = fixture()
    del f['saturn_after']
    with pytest.raises(ValueError, match='Missing period-lord transit coverage'):
        build_synthesis_space(p, a, f)


def plan_and_brief():
    p, a, f = fixture()
    space = build_synthesis_space(p, a, f)
    brief = {'synthesis_space': space, 'activation': a}
    row = {'themes': [{'theme': 'Learning and publishing'}],
        'activation_review': [{'level': l, 'natal_assessment': 'Natal evidence', 'transit_assessment': 'Transit evidence'} for l in a['levels']],
        'considered_houses': sorted({h for w in space['windows'] for h in w['active_houses']}),
        'signification_review': [{'house': h, 'meanings_considered': 'All meanings', 'supported_event_branches': 'Candidate events', 'excluded_or_background': 'Needs context'} for h in {h for w in space['windows'] for h in w['active_houses']}],
        'combination_exploration': [{'houses': [3, 9], 'source_ids': ['saturn_before'],
            'window_refs': ['pd_test_window_1'], 'decision': 'selected', 'theme': 'Learning and publishing',
            'signification_link': 'Writing combines with advanced learning', 'reason': 'A distinct conditional event'}]}
    return row, brief


def test_exploration_rejects_wrong_windows_and_unjustified_house_or_theme():
    row, brief = plan_and_brief()
    validate_exploration(row, brief)
    bad = deepcopy(row)
    bad['combination_exploration'][0]['window_refs'] = ['pd_test_window_2']
    with pytest.raises(ValueError, match='nonconcurrent'):
        validate_exploration(bad, brief)
    bad = deepcopy(row)
    bad['combination_exploration'][0]['houses'] = [4, 9]
    with pytest.raises(ValueError, match='lack cited'):
        validate_exploration(bad, brief)
    bad = deepcopy(row)
    bad['themes'].append({'theme': 'Unexplained theme'})
    with pytest.raises(ValueError, match='Every planned theme'):
        validate_exploration(bad, brief)


def test_every_level_and_house_must_be_considered():
    row, brief = plan_and_brief()
    row['activation_review'].pop()
    with pytest.raises(ValueError, match='every MD/AD/PD'):
        validate_exploration(row, brief)
    row, brief = plan_and_brief()
    row['considered_houses'].pop()
    with pytest.raises(ValueError, match='all concurrently'):
        validate_exploration(row, brief)


def test_missing_citation_resolves_only_from_real_concurrent_direct_sources():
    row, brief = plan_and_brief()
    route = row['combination_exploration'][0]
    route['houses'] = [3, 8, 9]
    validate_exploration(row, brief)
    assert route['resolved_source_ids']
    assert 'rahu' in route['resolved_source_ids']
    assert route['window_refs'] == ['pd_test_window_1']
    assert route['signification_link'] == 'Writing combines with advanced learning'
