import copy

from ai.parallel_chat.shared_d1_compaction import compact_shared_d1
from ai.parallel_chat.prompt_blocks import build_parashari_branch_static_agent


def test_dedup_preserves_disagreements_and_chalit_overrides():
    burn = {'planet': 'Venus', 'source': {'work': 'source'}, 'is_combust': True}
    chart = {'planets': {'Venus': {'house': 8, 'combustion': burn}},
             'combustion': {'source': {'work': 'source'}, 'planets': {'Venus': copy.deepcopy(burn)}},
             'houses': [{'longitude': 10, 'graha_drishti': ['Venus']}],
             'graha_drishti_by_house': {'1': ['Venus']},
             'bhav_chalit': {'planets': {'Venus': {'house': 7}}, 'cusps': [11]}}
    original = copy.deepcopy(chart)
    out = compact_shared_d1(chart)
    assert chart == original
    assert out['bhav_chalit']['planets']['Venus']['house'] == 7
    assert out['bhav_chalit']['cusps'] == [11]
    assert out['planets']['Venus']['combustion']['is_combust'] is True
    assert out['combustion']['source'] == burn['source']
    assert 'planets' not in out['combustion']
    chart['combustion']['planets']['Venus']['is_combust'] = False
    assert compact_shared_d1(chart)['combustion']['planets']['Venus']['is_combust'] is False


def test_prompt_retains_relative_and_timing_rules_when_applicable():
    ctx = {'intent': {'category': 'career', 'evidence_plan': {'question_parts': [{'subject': 'self'}]}}}
    scoped = build_parashari_branch_static_agent('career', context=ctx)
    assert '[PC-1]' not in scoped
    assert '[BHAVAM-1]' not in scoped
    assert '[DASHA-DATES]' in scoped
    assert '[AVAYOGI-EFFECT-POLICY]' in scoped
    ctx['intent']['evidence_plan']['question_parts'].append({'subject': 'mother'})
    ctx.update(lifespan_timing_evidence={'candidate_windows': []}, kota_chakra={'present': True},
               classical_rule_matches={'matches': [1]}, daily_prediction_spine={'present': True})
    expanded = build_parashari_branch_static_agent('career', context=ctx)
    for text in ('[BHAVAM-1]', '[KOTA-CHAKRA]', '# CLASSICAL RULE MATCHES',
                 'When `lifespan_timing_evidence` is present:', 'If `px.src="day"`'):
        assert text in expanded


def test_audit_compaction_keeps_unmatched_tests_and_all_point_positions():
    from ai.parallel_chat.shared_d1_compaction import compact_calculation_audits
    chart = {'neecha_bhanga': {'Mars': {'conditions_met': [
        {'rule_id': 'r1', 'condition': 'Moon in kendra', 'description': 'Moon in kendra', 'reference': 'ref'}],
        'matched_rule_ids': ['r1'], 'rules_evaluated': [
            {'rule_id': 'r1', 'matched': True, 'applicable': True, 'reference': 'ref'},
            {'rule_id': 'r2', 'matched': False, 'applicable': True}]}},
        'upagraha_calculation': {'points': [{'name': 'Gulika', 'house': 12, 'longitude': 318.09,
            'segment_start_local': 'audit timestamp'}]}}
    result = compact_calculation_audits(chart)
    assert result['neecha_bhanga']['Mars']['rules_evaluated'][0]['rule_id'] == 'r2'
    assert result['neecha_bhanga']['Mars']['conditions_met'][0]['condition'] == 'Moon in kendra'
    assert result['upagraha_calculation']['points'][0] == {'name': 'Gulika', 'house': 12, 'longitude': 318.09}
    assert 'description' in chart['neecha_bhanga']['Mars']['conditions_met'][0]
