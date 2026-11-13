import asyncio
from copy import deepcopy
import pytest
from chat.chart_fact_audit import compare_claims, calculate_subject, snapshot_subject


def claim(kind, value, **fields):
    return {'quote': 'Chart claim.', 'subject_id': 'native', 'chart': 'D9',
            'reference_frame': 'ascendant', 'chart_scope': 'natal', 'claim_type': kind, 'asserted_value': value, **fields}


def fixture_calculator(subject, divisions):
    return {'D9': {'ascendant': 240.0, 'planets': {'Venus': {'longitude': 150.0}}},
            'D10': {'ascendant': 0.0, 'planets': {}}}


def check(c, subjects=None):
    return compare_claims({'claims': [c]}, 'Chart claim.', subjects or {'native': {}}, fixture_calculator)['fact_checks'][0]


@pytest.mark.parametrize('c,expected', [
    (claim('ascendant_sign', 'Scorpio'), 'Sagittarius'),
    (claim('lord_of_houses', [4, 11], planet='Venus', comparison='equals'), [6, 11]),
    (claim('house_lord', 'Mars', chart='D10', house=10), 'Saturn'),
    (claim('planet_house', 9, planet='Venus'), 10),
])
def test_known_wrong_claim_patterns(c, expected):
    result = check(c)
    assert result['status'] == 'mismatch'
    assert result['calculated_value'] == expected
    assert result['evidence_path']
    assert result['answer_span'] == {'start': 0, 'end': 12}


@pytest.mark.parametrize('c', [claim('ascendant_sign', 'Sagittarius'),
    claim('planet_sign', 'Virgo', planet='Venus'),
    claim('planet_house', 10, planet='Venus'),
    claim('lord_of_houses', [11], planet='Venus', comparison='contains'),
    claim('lord_of_houses', [11, 6], planet='Venus', comparison='equals')])
def test_correct_facts_do_not_raise_false_positives(c):
    assert check(c)['status'] == 'match'


@pytest.mark.parametrize('changes,status', [
    ({'subject_id': None}, 'ambiguous'), ({'chart': None}, 'ambiguous'),
    ({'subject_id': 'unknown'}, 'ambiguous'),
    ({'quote': 'invented quote'}, 'invalid_extraction'),
    ({'reference_frame': 'Karakamsha'}, 'unsupported'),
    ({'claim_type': 'kp_cusp_star_lord'}, 'unsupported'),
    ({'asserted_value': 8}, 'invalid_extraction'),
    ({'reference_frame': None}, 'unsupported'),
    ({'chart_scope': 'transit'}, 'unsupported')])
def test_unverifiable_claims_are_never_marked_correct(changes, status):
    assert check({**claim('ascendant_sign', 'Sagittarius'), **changes})['status'] == status


def test_two_subjects_are_calculated_separately():
    def calc(subject, divisions):
        return {'D9': {'ascendant': subject['ascendant'], 'planets': {}}}
    claims = [claim('ascendant_sign', 'Sagittarius'), claim('ascendant_sign', 'Sagittarius', subject_id='partner')]
    result = compare_claims({'claims': claims}, 'Chart claim.',
                            {'native': {'ascendant': 240}, 'partner': {'ascendant': 210}}, calc)
    assert result['counts'] == {'match': 1, 'mismatch': 1}


def test_failed_calculator_is_not_mismatch():
    def failed(*args):
        raise ValueError('missing birth time')
    result = compare_claims({'claims': [claim('ascendant_sign', 'Scorpio')]}, 'Chart claim.', {'native': {}}, failed)
    assert result['counts'] == {'calculation_failed': 1}
    assert 'missing birth time' in result['fact_checks'][0]['reason']


def test_real_calculator_regression_known_d9_chart():
    # Birth input from the previous D9 regression, with the original UTC+8 zone.
    subject = snapshot_subject({'date': '1963-02-17', 'time': '16:45', 'latitude': 23.15,
                                'longitude': 120.16, 'timezone': 'UTC+8'})
    before = deepcopy(subject)
    result = compare_claims({'claims': [claim('ascendant_sign', 'Scorpio'),
        claim('ascendant_sign', 'Sagittarius'),
        claim('lord_of_houses', [4, 11], planet='Venus', comparison='equals')]},
        'Chart claim.', {'native': subject})
    assert result['counts'] == {'mismatch': 2, 'match': 1}
    assert result['fact_checks'][0]['calculated_value'] == 'Sagittarius'
    assert subject == before
    assert result['replay']['calculated_charts']['native']['D9']['planets']


def test_malformed_envelope_is_audit_failure():
    with pytest.raises(ValueError):
        compare_claims({'claims': 'not a list'}, '', {})


def test_live_extractor_chart_id_and_nested_lordships_are_losslessly_resolved():
    c = claim('lord_of_houses', {'houses': [4, 11], 'comparison': 'contains'},
              planet='Venus', subject_id='123')
    result = check(c, {'native': {'chart_id': 123}})
    assert result['status'] == 'mismatch'
    assert result['calculated_value'] == [6, 11]
    assert result['claim'] == c  # Preserve original extractor output.
    assert len(result['normalizations']) == 2


def test_duplicate_chart_id_is_not_guessed_between_subjects():
    c = claim('ascendant_sign', 'Scorpio', subject_id='123')
    assert check(c, {'native': {'chart_id':123}, 'partner': {'chart_id':123}})['status'] == 'ambiguous'


@pytest.mark.parametrize('sign,status', [('Taurus', 'match'), ('Gemini', 'mismatch')])
def test_house_sign_claim_from_diksha_answer(sign, status):
    def calc(subject, divisions):
        return {'D1': {'ascendant': 120.0, 'planets': {}}}
    c = claim('house_sign', sign, chart='D1', house=10)
    result = compare_claims({'claims': [c]}, 'Chart claim.', {'native': {}}, calc)['fact_checks'][0]
    assert result['status'] == status
    assert result['calculated_value'] == 'Taurus'
    assert result['evidence_path'] == 'native.D1.houses.10.sign'


def test_house_sign_requires_valid_house():
    assert check(claim('house_sign', 'Taurus', house=13))['status'] == 'invalid_extraction'
