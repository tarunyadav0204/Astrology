import copy
import pytest
from ai.parallel_chat.method_scope import (
    METHODS, filter_method_evidence, filter_method_instructions,
    method_scope_instruction, scoped_response_format,
)
from ai.output_schema import get_response_schema_for_mode
from ai.parallel_chat.prompt_blocks import build_merge_role_preamble
from chat.system_instruction_config import build_merge_synthesis_instruction


def test_filters_nested_calculations_but_keeps_basic_facts_and_user_history():
    data = {'charts': {'D1': {'houses': {'7': {'sign': 'Aries', 'SAV': 19, 'BAV_by_planet': {'Mars': 0}}}}},
            'kp': {'cusp_lords': {'7': 'Jupiter'}}, 'sudarshana': {'house_agreement': [3]},
            'jaimini': {'frame_authority': [1]}, 'nadi': {'LK': [1]},
            'nakshatra_dasha_tara': [1], 'nested': {'school_judgments': {'kp': 'KP confirms', 'parashari': 'Saturn period'}},
            'planets': {'Moon': {'nakshatra': 'Shravana', 'house': 4}},
            'user_facts': {'preferences': ['Asked about KP']}, 'history': ['Previous KP answer'],
            'response_format': {'mandatory_sections': 'ALWAYS include Nakshatra Insights'}}
    before = copy.deepcopy(data)
    out = filter_method_evidence(data, ['parashari'])
    assert data == before
    assert out['charts']['D1']['houses']['7'] == {'sign': 'Aries'}
    for key in ('kp', 'sudarshana', 'jaimini', 'nadi', 'nakshatra_dasha_tara'):
        assert key not in out
    assert out['nested']['school_judgments'] == {'parashari': 'Saturn period'}
    assert out['planets']['Moon']['nakshatra'] == 'Shravana'
    assert out['user_facts'] == data['user_facts']
    assert out['history'] == data['history']
    assert out['response_format']['mandatory_sections'] == ''


@pytest.mark.parametrize('disabled', [b for b in METHODS if b != 'parashari'])
def test_output_template_contains_only_selected_method_headings(disabled):
    enabled = [b for b in METHODS if b != disabled]
    template = scoped_response_format(enabled)
    assert f'#### {METHODS[disabled]}\n' not in template
    for b in enabled:
        assert f'#### {METHODS[b]}\n' in template
    guard = method_scope_instruction(enabled)
    assert 'Do not perform, infer, reconstruct, substitute, or silently blend' in guard
    assert 'conversation history' in guard


def test_legacy_merge_mandates_removed_not_just_overridden():
    old = '\n\n'.join([get_response_schema_for_mode('DEFAULT', premium_analysis=False),
                         build_merge_role_preamble(), build_merge_synthesis_instruction()])
    filtered = filter_method_instructions(old, ['parashari'])
    for phrase in ('Ashtakavarga', 'Jaimini', 'KP Stellar', 'Nadi Interpretation', 'Nakshatra Insights', 'Sudarshana', 'SAV', 'BAV'):
        assert phrase not in filtered
    assert 'Direct Answer' in scoped_response_format(['parashari'])


def test_all_methods_enabled_preserves_existing_material():
    data = {'kp': {'x': 1}, 'charts': {'SAV': 5}, 'sudarshana': {}}
    assert filter_method_evidence(data, METHODS) == data
    text = 'MANDATORY Ashtakavarga\nSAV and BAV\n\nJaimini'
    assert filter_method_instructions(text, METHODS) == text

@pytest.mark.parametrize('agent_context', [False, True])
@pytest.mark.parametrize('cached', [False, True])
def test_pipeline_scopes_actual_branch_cache_and_merge_prompts(monkeypatch, agent_context, cached):
    import asyncio
    import time
    from ai.parallel_chat import orchestrator as p
    from utils import admin_settings as settings

    monkeypatch.setattr(settings, 'get_setting', lambda key: None)
    monkeypatch.setattr(p, 'get_parallel_branch_enabled', lambda premium: {b: b == 'parashari' for b in METHODS})
    monkeypatch.setattr(p, 'is_parallel_branch_planner_enabled', lambda: False)
    monkeypatch.setattr(p, 'parallel_agent_context_enabled', lambda: agent_context)
    monkeypatch.setattr(p, 'parallel_branch_stagger_s', lambda: 0)
    if agent_context:
        # Supply deterministic agent packets; chart calculation is not under test.
        monkeypatch.setattr(p, 'merged_context_to_agent_context', lambda *args, **kwargs: {})
        monkeypatch.setattr(p, 'build_all_parallel_agent_payloads', lambda *args, **kwargs: {
            b: {'jaimini': {}, 'sudarshana_chakra': {'marker': 'secret AV packet'}, 'user_question': 'Test'}
            for b in METHODS
        })
    captures = {'branches': [], 'cache': []}
    async def cache(**kwargs):
        captures['cache'].append(kwargs['cache_payload'])
        return None, object() if cached else None, 0, 0
    async def branch(analyzer, static, payload, premium, label, **kwargs):
        captures['branches'].append((label, static, payload))
        return {'status': 'ok', 'analysis': 'D1 evidence.', 'bullets': []}, {'branch': label, 'success': True}
    monkeypatch.setattr(p, '_create_gemini_parallel_cache', cache)
    monkeypatch.setattr(p, '_run_branch_json', branch)
    class CapturedMerge(Exception):
        pass
    class Analyzer:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            captures['merge'] = prompt
            raise CapturedMerge()
    context = {
        'intent': {'mode': 'DEFAULT', 'category': 'general'},
        'birth_details': {'name': 'Test'},
        'ascendant_info': {'sign_name': 'Aries', 'exact_degree_in_sign': 0},
        'd1_chart': {'planets': {}, 'houses': []},
        'ashtakavarga': {'excluded_marker': 'secret AV packet'},
        'sudarshana_chakra': {}, 'kp_analysis': {},
        'response_format': {'mandatory_sections': 'MANDATORY Ashtakavarga and Nakshatra Insights'},
    }
    with pytest.raises(CapturedMerge):
        asyncio.run(p.run_parallel_chat_pipeline(
            Analyzer(), user_question='Tell me about my chart', astrological_context=context,
            conversation_history=[], language='english', response_style='technical', user_context=None,
            premium_analysis=False, mode='DEFAULT', total_request_start=time.time(),
        ))
    assert [r[0] for r in captures['branches']] == ['parashari']
    # Subject/provenance survives both legacy/agent payloads and cache hit/fallback.
    for _, instructions, payload in captures['branches']:
        assert payload['consultation_subject']['address_mode'] == 'named_chart'
        assert 'chart_role_authority' in payload
        assert 'Astrology cannot establish' in instructions
    for cached_payload in captures['cache']:
        assert cached_payload['consultation_subject']['chart_name'] == 'Test'
        assert 'chart_role_authority' in cached_payload
    assert 'CONSULTATION_SUBJECT_JSON' in captures['merge']
    assert 'CHART_ROLE_AUTHORITY_JSON' in captures['merge']
    assert 'user already tapped the Remedies CTA' not in captures['merge']
    assert 'Do not offer a personal remedy' in captures['merge']
    assert 'Astrology cannot establish' in captures['merge']
    assert 'secret AV packet' not in str(captures)
    assert 'REQUEST METHOD SCOPE' in captures['branches'][0][1]
    prompt = captures['merge']
    assert 'RESPONSE FORMAT FOR SELECTED METHODS ONLY' in prompt
    assert '#### Parashari' in prompt
    assert '#### The Jaimini View' not in prompt
    assert '#### Ashtakavarga' not in prompt
    assert 'MANDATORY Ashtakavarga' not in prompt
    assert '"nakshatra_dasha_tara"' not in prompt
    assert '"kp":' not in prompt
    assert '"sudarshana":' not in prompt
    assert '"jaimini":' not in prompt
    assert 'Do not recover their results from conversation history' in prompt


def test_planner_capabilities_and_json_example_do_not_request_disabled_methods():
    from ai.parallel_chat.branch_planner import _planner_prompt
    text = _planner_prompt(user_question='Career?', language='english', context_summary={},
                           allowed_branches=['parashari', 'jaimini'])
    assert 'jaimini:' in text
    assert '"jaimini"' in text
    for branch in ('kp', 'nadi', 'nakshatra', 'ashtakavarga', 'sudarshan'):
        assert f'"{branch}"' not in text
        assert f'- {branch}:' not in text
    assert 'Never compensate for an excluded method' in text
