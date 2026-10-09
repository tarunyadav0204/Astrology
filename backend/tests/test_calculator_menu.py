import json
import pytest
from chat.calculator_menu import EXTRA_CALCULATORS, CalculatorParameters, run_calculator, validate_parameters, compact_result
from chat.conflict_contract import strictify_schema, MAX_ROUNDS, validate_turn
from chat.verified_chat_pipeline import CAPABILITY_REGISTRY

BIRTH=dict(name='Synthetic',date='1990-01-01',time='12:00:00',latitude=28.6139,longitude=77.2090,timezone='UTC+5:30',place='Delhi',gender='male')
LOCATION=dict(name='Delhi',latitude=28.6139,longitude=77.2090,timezone='UTC+5:30')
PARAMS=dict(start_date='2027-01-01',end_date='2027-02-01',houses=[10],signs=[10],planets=['Sun','Mars'],year=2027,location=LOCATION,topic='career',cities=[LOCATION],event_type='business')

@pytest.mark.parametrize('capability', list(EXTRA_CALCULATORS))
def test_registered_adapter_returns_json_facts_from_real_chart(capability):
    assert capability in CAPABILITY_REGISTRY
    result = run_calculator(capability, BIRTH, PARAMS)
    assert result['calculator'] == capability
    assert 'facts' in result
    json.dumps(result)
    if capability == 'annual.varshphal':
        assert set(result['facts']['chart']) == {'ascendant','planets'}
    if capability == 'yogas.general':
        from calculators.chart_calculator import ChartCalculator
        from calculators.yoga_calculator import YogaCalculator
        from types import SimpleNamespace
        chart=ChartCalculator({}).calculate_chart(SimpleNamespace(**BIRTH))
        assert result['facts'] == compact_result(YogaCalculator(SimpleNamespace(**BIRTH),chart).calculate_all_yogas())
    if capability == 'dasha.shoola':
        assert all(row['start_date'] < PARAMS['end_date'] and row['end_date'] > PARAMS['start_date'] for row in result['facts']['all_periods'])

@pytest.mark.parametrize('capability', ['dasha.yogini','annual.varshphal','annual.tajika','annual.nakshatra','jaimini.rashi_strength','strength.house','election.panchang','election.muhurat','election.navatara','location.analysis'])
def test_required_parameters_cannot_be_guessed(capability):
    with pytest.raises(ValueError): validate_parameters(capability,{})

def test_shared_menu_accepts_many_calculators_in_one_round():
    requests=[dict(answer_id=1,capabilities=[c],parameters=PARAMS) for c in EXTRA_CALCULATORS]
    turn=validate_turn(dict(action='calculate',calculations=requests),[1,2],0,{})
    assert len(turn.calculations)==len(EXTRA_CALCULATORS)
    assert MAX_ROUNDS==8

def test_strict_tool_schema_resolves_nested_refs_and_requires_nullable_fields():
    schema=strictify_schema(CalculatorParameters.model_json_schema())
    def check(node):
        if isinstance(node,dict):
            assert '$ref' not in node
            if node.get('type')=='object':
                assert node['additionalProperties'] is False
                assert set(node['required'])==set(node['properties'])
            for child in node.values(): check(child)
        elif isinstance(node,list):
            for child in node: check(child)
    check(schema)

def test_compact_facts_preserve_rules_and_all_rows_without_client_prose():
    assert compact_result({'prediction':'long answer','rows':[{'evidence':i,'description':'prose'} for i in range(100)]}) == {'rows':[{'evidence':i} for i in range(100)]}


def test_model_can_override_deterministic_divisional_choice():
    from chat.verified_chat_pipeline import _calculate_requested_capabilities
    result=_calculate_requested_capabilities(BIRTH,['parashari.divisional_confirmation'],{}, {'intent_summary':{'category':'career'}}, {'divisions':[7,24]})
    assert set(result['parashari.divisional_confirmation']) == {'D7','D24'}
