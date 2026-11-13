import copy
import json
import pytest
from chat.llm_chart_normalization import normalize_chart_evidence, llm_json_dumps, SIGNS


@pytest.mark.parametrize('sign', range(12))
def test_raw_wheels_and_flat_divisions_are_named_without_shifting_houses(sign):
    raw = {'ascendant': sign * 30 + 27.07858,
           'planets': {'Mars': {'sign': sign, 'house': 1, 'degree_in_sign': 8}},
           'houses': [{'sign': sign, 'house_number': 1}],
           'divisions': {'D9': {'Mars': {'sign': sign, 'house': 1}}}}
    before = copy.deepcopy(raw)
    out = normalize_chart_evidence(raw)
    assert out['ascendant_sign_name'] == SIGNS[sign]
    assert out['ascendant_sign_number'] == sign + 1
    assert out['planets']['Mars'] == {'sign': SIGNS[sign], 'house': 1, 'degree_in_sign': 8}
    assert out['divisions']['D9']['Mars'] == {'sign': SIGNS[sign], 'house': 1}
    assert out['houses'][0]['house_number'] == 1
    assert raw == before
    assert normalize_chart_evidence(out) == out


def test_compact_one_based_geometry_and_authority_are_preserved():
    raw = {'L': {'s': 9, 'd': 8, 'nm': 'Sagittarius'},
           'P': [['Mars', 241, 9, 'Sagittarius', 1]],
           'authority': {'sign_numbering': '1=Aries through 12=Pisces; sign numbers are not houses',
                         'special_lagnas': {'UL': {'sign': 9, 'natal_house': 1}, 'AL': {'sign': 12}}},
           'muntha': {'sign': 9, 'house': 12}}
    out = normalize_chart_evidence(raw)
    assert out['L'] == raw['L'] and out['P'] == raw['P']
    assert out['authority']['special_lagnas']['UL']['sign'] == 'Sagittarius'
    assert out['authority']['special_lagnas']['AL']['sign'] == 'Pisces'
    assert out['muntha'] == {'sign': 'Sagittarius', 'house': 12}
    assert normalize_chart_evidence(out) == out


def test_named_sign_longitude_and_native_ids_are_unambiguous():
    out = normalize_chart_evidence({'sign': 9, 'longitude': 267.0, 'house': 1,
                                   'reference_sign_id': 8, 'ascendant_sign': 8})
    assert out['sign'] == out['ascendant_sign'] == out['reference_sign_name'] == 'Sagittarius'
    assert out['reference_sign_number'] == 9
    assert 'reference_sign_id' not in out
    assert normalize_chart_evidence({'sign': 9, 'sign_name': 'Sagittarius'})['sign'] == 'Sagittarius'


def test_av_and_jaimini_sign_maps_not_house_maps():
    raw = {'D1': {'S': list(range(12)), 'B': {'Mars': list(range(12))},
                  'Ho': {'1': {'z': 9, 'zn': 'Sagittarius', 's': 8, 'B': {'Mars': 3}}}},
           'sarvashtakavarga': {'0': 20, '8': 32, '11': 25, 'total_bindus': 337},
           'sign_aspects': {'8': [2, 5, 11]},
           'raw_sign_order': {'sav': list(range(12)), 'signs': list(SIGNS)}}
    out = normalize_chart_evidence(raw)
    assert out['D1']['S']['Sagittarius'] == 8
    assert out['D1']['B']['Mars']['Sagittarius'] == 8
    assert out['D1']['Ho'] == raw['D1']['Ho']
    assert out['sarvashtakavarga']['Sagittarius'] == 32
    assert out['sign_aspects']['Sagittarius'] == ['Gemini', 'Virgo', 'Pisces']
    assert out['raw_sign_order']['sav']['Sagittarius'] == 8
    assert normalize_chart_evidence(out) == out


def test_user_statements_and_non_sign_numbers_are_not_rewritten():
    raw = {'user_facts': {'sign': 8}, 'history': [{'sign': 8}],
           'degree_in_sign': 8, 'ascendant_degree_in_sign': 8,
           'house': 0, 'nakshatra_index': 8, 'in_own_sign': True}
    assert normalize_chart_evidence(raw) == raw


@pytest.mark.parametrize('module', ['ai.parallel_chat.orchestrator', 'ai.parallel_chat.relational_orchestrator', 'ai.gemini_context_cache'])
def test_actual_parallel_and_cache_serializers(module):
    import importlib
    serialize = importlib.import_module(module)._json_compact
    out = json.loads(serialize({'d9': {'ascendant': 267.0, 'planets': {'Mars': {'sign': 8, 'house': 1}}}}))
    assert out['d9']['ascendant_sign_name'] == 'Sagittarius'
    assert out['d9']['planets']['Mars']['sign'] == 'Sagittarius'
    assert 'chart_coordinate_convention' in out


@pytest.mark.parametrize('speech', [False, True])
def test_instant_and_speech_actual_composer_boundary(speech):
    from chat.instant_chat_pipeline import _build_instant_composer_prompt_v3
    packet = {'evidence': {'chart_facts': {'D9': {'ascendant_sign': 8, 'planets': {'Mars': {'sign': 8, 'house': 1}}}}}}
    before = copy.deepcopy(packet)
    prompt = _build_instant_composer_prompt_v3('Analyze D9', packet, 'english', speech_mode=speech)
    assert '"ascendant_sign":"Sagittarius"' in prompt
    assert '"sign":8' not in prompt
    assert packet == before


def test_tool_result_serialization_keeps_calculations_raw():
    # Same imported serializer used by both Responses and Sarvam tool loops.
    from chat.verified_chat_pipeline import llm_json_dumps as serialize
    raw = {'calculator': 'parashari.divisional_confirmation', 'D9': {'ascendant': 267, 'planets': {'Mars': {'sign': 8, 'house': 1}}}}
    out = json.loads(serialize(raw))
    assert out['D9']['ascendant_sign_name'] == 'Sagittarius'
    assert raw['D9']['planets']['Mars']['sign'] == 8


def test_legacy_standard_premium_and_mundane_prompt_boundary():
    from ai.output_schema import build_final_prompt
    for premium, kind in [(False, 'birth'), (True, 'birth'), (False, 'mundane'), (False, 'synastry')]:
        context = {'analysis_type': kind, 'd1_chart': {'divisions': {'D9': {'Mars': {'sign': 8, 'house': 1}}}},
                   'divisional_charts': {'d9_navamsa': {'divisional_chart': {'ascendant': 267}}}}
        prompt = build_final_prompt('Analyze D9', context, [], 'english', 'technical', None, premium_analysis=premium)
        assert '"sign": "Sagittarius"' in prompt
        assert '"ascendant_sign_name": "Sagittarius"' in prompt
        assert context['d1_chart']['divisions']['D9']['Mars']['sign'] == 8


def test_bounded_verified_tool_preview_is_normalized_before_truncation():
    from chat.verified_chat_pipeline import _json_limit, _compact_sarvam_tool_payload
    raw = {'D9': {'ascendant_sign': 8}, 'padding': 'x' * 5000}
    for out in [_json_limit(raw, 1000), _compact_sarvam_tool_payload(raw, 1000)]:
        serialized = llm_json_dumps(out)
        assert 'Sagittarius' in serialized
        assert 'ascendant_sign\\": 8' not in serialized
    assert raw['D9']['ascendant_sign'] == 8


def test_real_divisional_calculator_keeps_native_indices():
    from calculators.divisional_chart_calculator import DivisionalChartCalculator
    chart = {'ascendant': 109.67539778277906, 'planets': {
        'Mars': {'longitude': 106.76, 'sign': 3, 'house': 1}}}
    d9 = DivisionalChartCalculator(chart).calculate_divisional_chart(9)
    before = copy.deepcopy(d9)
    out = json.loads(llm_json_dumps(d9))['divisional_chart']
    assert out['ascendant_sign_name'] == 'Sagittarius'
    assert out['ascendant_sign_number'] == 9
    assert d9 == before
    assert d9['divisional_chart']['houses'][0]['sign'] == 8


def test_obsolete_calculator_legend_is_replaced_only_for_model():
    raw = {'sarvashtakavarga_key_legend': 'Each key is a ZODIAC SIGN index: 0=Aries',
           'sarvashtakavarga': {'0': 31, '8': 32}}
    out = normalize_chart_evidence(raw)
    assert '0=Aries' not in out['sarvashtakavarga_key_legend']
    assert out['sarvashtakavarga']['Sagittarius'] == 32
    assert '0=Aries' in raw['sarvashtakavarga_key_legend']
