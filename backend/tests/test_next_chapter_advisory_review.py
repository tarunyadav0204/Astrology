import asyncio
from copy import deepcopy
import json
from types import SimpleNamespace
import pytest
from test_next_chapter import dossier, narrative_for
from test_next_chapter_pipeline import Model
from next_chapter.briefs import build_briefs
from next_chapter.pipeline import Runner, validate_edit, validate_review, unavailable_review
from next_chapter.service import narrate_next_chapter
from next_chapter.validation import warning_sink


def review(report):
    return {'checked_period_ids': [p['period_id'] for p in report['periods']],
            'checked_chapter': True, 'issues': [], 'quality_notes': []}


def test_wrapped_review_and_editor_do_not_retry_or_discard_content(dossier):
    report = narrative_for(dossier)
    original = review(report)
    assert validate_review([original], report, build_briefs(dossier)) == original
    edit = {'chapter_throughline': 'A chapter', 'background_themes': [],
            'periods': [{'period_id': p['period_id'], 'distinctive_focus': 'Focus',
                        'revision_instruction': 'Direction'} for p in report['periods']]}
    assert validate_edit([edit], [p['period_id'] for p in report['periods']]) == edit


def test_bad_finding_logged_without_losing_valid_finding(dossier):
    report = narrative_for(dossier)
    check = review(report)
    check['issues'] = [
        {'section': 'pd_1 plan', 'kind': 'factual', 'quote': 'bad', 'correction': 'bad'},
        {'section': 'pd_1', 'kind': 'factual', 'quote': report['periods'][0]['summary'],
         'correction': 'A supported correction', 'fact_refs': []}]
    check['quality_notes'] = [{'section': 'plans', 'instruction': 'Invalid address'},
                              {'section': 'overview', 'instruction': 'Useful direction'}]
    before = deepcopy(check)
    warnings = []; token = warning_sink.set(warnings.append)
    try:
        result = validate_review(check, report, build_briefs(dossier))
    finally:
        warning_sink.reset(token)
    assert len(result['issues']) == 1 and result['issues'][0]['section'] == 'pd_1'
    assert result['quality_notes'] == [{'section': 'chapter', 'instruction': 'Useful direction'}]
    assert len(result['ignored_findings']) == 2
    assert any('known section' in w for w in warnings)
    assert check == before


@pytest.mark.parametrize('response', ['not json', None])
def test_optional_stage_retains_existing_content_and_records_usage(response):
    class Broken:
        async def generate_content_async(self, *args, **kwargs):
            if response is None:
                raise TimeoutError('provider unavailable')
            return SimpleNamespace(text=response, usage_metadata=SimpleNamespace(prompt_token_count=13, candidates_token_count=2))
    runner = Runner(Broken(), 'model', 'provider', 'en')
    original = {'periods': [{'summary': 'Already authored prose'}]}
    value = asyncio.run(runner.call('repair_0_pd_1', 'repair', {}, lambda x: x, fallback=original))
    assert value == original and value is not original
    assert len(runner.audit['calls']) == 1
    assert runner.audit['calls'][0]['advisory_fallback']
    assert runner.audit['validation_warnings']
    if response:
        assert runner.audit['calls'][0]['input_tokens'] == 13


@pytest.mark.parametrize('stage_kind', ['review', 'review_json', 'review_provider', 'edit', 'repair'])
def test_pipeline_completes_with_optional_stage_errors(dossier, stage_kind):
    class BadOptional(Model):
        async def generate_content_async(self, prompt, **kwargs):
            result = await super().generate_content_async(prompt, **kwargs)
            stage = prompt.split('\nSTAGE: ', 1)[1].split('\n')[0]
            if stage_kind in ('review_json', 'review_provider') and (stage.startswith('fact_review_') or stage == 'event_review'):
                if stage_kind == 'review_provider':
                    raise TimeoutError('review provider unavailable')
                result.text = 'not json'
            if stage_kind == 'edit' and stage == 'chapter_edit':
                result.text = '[{}]'
            if stage_kind == 'review' and (stage.startswith('fact_review_') or stage == 'event_review'):
                result.text = '[{"issues":[{"section":"report.periods"}],"quality_notes":null}]'
            if stage_kind == 'repair' and (stage.startswith('repair_') or stage == 'final_factual_patch'):
                result.text = 'not json'
            return result
    model = BadOptional(dossier, factual_error=stage_kind == 'repair')
    result = asyncio.run(narrate_next_chapter(dossier, model=model))
    assert len(result['report']['periods']) == len(dossier['periods'])
    assert result['audit']['validation_warnings']
    assert all(call['attempt'] == 0 for call in result['audit']['calls'])
    assert result['generation']['factual_review'] == 'warnings'
    if stage_kind.startswith('review'):
        assert result['audit']['reviews'][0]['checked_chapter'] is False
        assert result['audit']['reviews'][0]['checked_period_ids'] == []


def test_optional_malformed_json_resume_reuses_audit_without_paid_retry():
    class Broken:
        async def generate_content_async(self, *args, **kwargs):
            return SimpleNamespace(text='bad json', usage_metadata=SimpleNamespace(prompt_token_count=13, candidates_token_count=2))
    first = Runner(Broken(), 'model', 'provider', 'en')
    asyncio.run(first.call('fact_review_test', 'review', {}, lambda x: x, fallback=unavailable_review()))
    class NoCalls:
        async def generate_content_async(self, *args, **kwargs):
            raise AssertionError('Unexpected model call')
    resumed = Runner(NoCalls(), 'model', 'provider', 'en', resume_audit=first.audit)
    result = asyncio.run(resumed.call('fact_review_test', 'review', {}, lambda x: x, fallback=unavailable_review()))
    assert result['checked_chapter'] is False
    assert resumed.audit['calls'][0]['reused'] is True
    assert resumed.audit['calls'][0]['input_tokens'] == 0
    assert resumed.audit['calls'][0]['source_usage']['input_tokens'] == 13
    assert resumed.audit['validation_warnings']
