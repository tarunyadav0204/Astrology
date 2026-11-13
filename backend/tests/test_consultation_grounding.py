from copy import deepcopy
from ai.parallel_chat.consultation_grounding import consultation_subject, chart_role_authority
from ai.parallel_chat.fact_authority import calculated_fact_authority, fact_reading_basis


def chart(asc):
    return {'ascendant': asc * 30,
            'houses': [{'house_number': h, 'sign': (asc+h-1) % 12} for h in range(1, 13)],
            'planets': {'Venus': {'sign_name': 'Virgo', 'house': 10}}}


def test_inverse_lordships_separate_d1_d9_occupancy_and_preserve_calculations():
    ctx = {'d1_chart': chart(3), 'divisional_charts': {'d9_navamsa': {
        'division_number': 9, 'divisional_chart': chart(8)}}}
    original = deepcopy(ctx)
    facts = calculated_fact_authority(ctx)
    roles = chart_role_authority(facts)
    assert roles['D1']['planets']['Venus']['lord_of_houses'] == [4, 11]
    assert roles['D9']['planets']['Venus']['lord_of_houses'] == [6, 11]
    assert roles['D9']['planets']['Venus']['occupied_house'] == 10
    assert roles['D1']['ascendant_sign'] == 'Cancer'
    assert roles['D9']['ascendant_sign'] == 'Sagittarius'
    assert any('Lordships: D1 [4, 11]; D9 [6, 11]' in line for line in fact_reading_basis(facts))
    assert ctx == original


def test_default_self_router_cannot_reassign_named_chart_to_reader():
    ctx = {'birth_details': {'name': 'Selected Person'},
           'intent': {'evidence_plan': {'question_parts': [{'subject': 'self'}]}}}
    assert consultation_subject(ctx)['address_mode'] == 'named_chart'
    assert consultation_subject(ctx)['chart_name'] == 'Selected Person'
    ctx['birth_details']['relation'] = 'other'
    assert consultation_subject(ctx)['address_mode'] == 'named_chart'
    ctx['birth_details']['relation'] = 'self'
    assert consultation_subject(ctx)['address_mode'] == 'self'


def test_missing_birth_identity_does_not_guess_the_user():
    assert consultation_subject({})['address_mode'] == 'named_chart'
    assert chart_role_authority({'charts': {'D9': {'planets': {}}}})['D9']['planets'] == {}


def test_grounding_is_last_in_existing_branch_call_without_an_extra_call():
    import asyncio
    from ai.parallel_chat.orchestrator import _run_branch_json
    calls = []
    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            calls.append(prompt)
            return {'success': True, 'response': '{"analysis":"Conditional chart interpretation","bullets":[]}'}
    subject = consultation_subject({'birth_details': {'name': 'Selected Person'}})
    asyncio.run(_run_branch_json(Analyzer(), 'Generic template: address the reader.',
        {'consultation_subject': subject, 'history': [{'answer': 'An unsupported prior assertion'}]},
        False, 'parashari', critical=True))
    assert len(calls) == 1
    assert calls[0].index('FINAL SUBJECT AND EVIDENCE CHECK') > calls[0].index('An unsupported prior assertion')
    assert 'verify ZERO real-world private events' in calls[0]
    assert 'named_chart' in calls[0]


def test_chart_focused_task_does_not_require_unrelated_career_sections():
    from ai.parallel_chat.consultation_grounding import focused_branch_instruction, final_grounding_instruction
    for branch in ('parashari', 'jaimini', 'nakshatra'):
        prompt = focused_branch_instruction(branch, 'D9')
        assert 'chart-specific follow-up about D9' in prompt
        assert 'Do not start unrelated' in prompt
        assert 'Astrology cannot establish' in prompt
        assert 'Return only JSON' in prompt
    tail = final_grounding_instruction(consultation_subject({'birth_details': {'name': 'Other Person'}}))
    assert 'NEXT_ACTION_META must be type=none' in tail
    assert 'not a current transit' in tail.lower()


def test_caveat_cannot_be_followed_by_a_behavioral_accusation():
    from ai.parallel_chat.consultation_grounding import final_grounding_instruction
    prompt = final_grounding_instruction(consultation_subject({}))
    assert 'Calling such' in prompt and 'does not make them supported' in prompt
    assert 'NOT established by this chart' in prompt
