import asyncio
from copy import deepcopy
import json
import re
from types import SimpleNamespace

import pytest
from test_next_chapter import dossier, narrative_for
from next_chapter.briefs import build_briefs, batch_packet
from next_chapter.pipeline import (Runner, PipelineError, validate_review, validate_plans,
                                   validate_prose, validate_edit)
from next_chapter.service import narrate_next_chapter


class Model:
    def __init__(self, dossier, factual_error=False):
        self.dossier = dossier
        self.briefs = build_briefs(dossier)
        self.factual_error = factual_error
        self.stages = []
        self.active = 0
        self.peak = 0

    async def generate_content_async(self, prompt, **kwargs):
        stage = re.search(r'STAGE: ([^\n]+)', prompt)[1]
        self.stages.append(stage)
        assert 'SAV/BAV' in prompt and 'Neecha Bhanga' in prompt
        assert 'not a quota of events' in prompt
        assert 'PD-level possibilities' in prompt
        self.active += 1
        self.peak = max(self.peak, self.active)
        await asyncio.sleep(0.001)
        self.active -= 1
        data = json.loads(prompt.split('\nDATA:\n', 1)[1])
        if stage.startswith('plan_'):
            result = {'periods': []}
            for pd in data['periods']:
                ids = set(data['natal_facts']) | set(pd['facts'])
                planet = f"planet_{pd['period']['planet']}"
                result['periods'].append({'period_id': pd['period']['id'], 'distinctive_change': 'Changed lordship',
                    'evidence_review': {'ashtakavarga': {'refs': pd['av_to_consider'][:1], 'assessment': 'Mixed support'},
                        'divisional': {'refs': pd['vargas_to_consider'][:1], 'assessment': 'Specific worksheet, not whole chart'},
                        'mixed_conditions': 'Capacity and difficulty coexist'},
                    'themes': [{'theme': 'An agreement', 'circumstances': 'If relevant to your circumstances',
                        'possibilities': ['An agreement could be revised'], 'support_refs': [planet], 'pressure_refs': [],
                        'reasoning': 'Activated houses', 'timing_refs': [], 'timing_reasoning': 'Broad PD timing'}]})
            for result_row, pd in zip(result['periods'], data['periods']):
                space = pd['synthesis_space']
                source_id = space['constant_natal_source_ids'][0]
                source = space['sources'][source_id]
                result_row.update({
                    'activation_review': [{'level': level, 'natal_assessment': 'Natal route', 'transit_assessment': 'Transit route'} for level in pd['activation']['levels']],
                    'considered_houses': sorted({h for w in space['windows'] for h in w['active_houses']}),
                    'signification_review': [{'house': h, 'meanings_considered': 'Full meanings reviewed', 'supported_event_branches': 'Conditional events', 'excluded_or_background': 'No extra confirmed context'} for h in {h for w in space['windows'] for h in w['active_houses']}],
                    'combination_exploration': [{'houses': source['houses'], 'source_ids': [source_id],
                        'window_refs': [space['windows'][0]['id']], 'signification_link': 'Agreement relates to house meaning',
                        'decision': 'selected', 'theme': 'An agreement', 'reason': 'Observable agreement conditional on circumstances'}]})
        elif stage.startswith('coverage_'):
            result = {'periods': data['plans']}
        elif stage == 'chapter_spectrum':
            chapter = {k: v for k, v in narrative_for(self.dossier).items() if k != 'periods'}
            result = {'chapter': chapter, 'family_coverage': [{'period_id': p['period_id'], 'planned_theme': t['theme'], 'chapter_theme': chapter['antardasha_events'][0]['theme']} for p in data['plans'] for t in p['themes']]}
        elif stage == 'chapter_edit':
            result = {'chapter_throughline': 'An evolving chapter', 'background_themes': ['Resources'],
                      'periods': [{'period_id': p['id'], 'distinctive_focus': 'Different mechanism',
                                   'revision_instruction': 'Distinguish mechanism from recurring background'} for p in self.dossier['periods']]}
        elif stage.startswith('write_') or stage.startswith('repair_'):
            batch = [p['period']['id'] for p in data['evidence']['periods']]
            narrative = narrative_for(self.dossier)
            result = {k: v for k, v in narrative.items() if k != 'periods'} if stage == 'write_pd_1' else {}
            result['periods'] = [p for p in narrative['periods'] if p['period_id'] in batch]
            for p in result['periods']:
                p['manifestations'][0]['evidence_refs'] = p['manifestations'][0]['planet_refs']
                if self.factual_error and p['period_id'] == 'pd_8' and stage.startswith('write_'):
                    p['timing_explanation'] = 'Mars conjunction instead of aspect'
        elif stage == 'final_factual_patch':
            result = {'patches': [{'issue_index': i, 'replacement': issue['quote'] + ' (corrected)'} for i, issue in enumerate(data['issues'])]}
        elif stage.startswith('fact_review_') or stage == 'event_review':
            ids = [p['period_id'] for p in data['report']['periods']]
            result = {'checked_period_ids': ids, 'checked_chapter': True, 'issues': [], 'quality_notes': []}
            if self.factual_error and stage.startswith('fact_review_0') and 'pd_8' in ids:
                result['issues'] = [{'section': 'pd_8', 'kind': 'factual', 'quote': 'Mars conjunction instead of aspect',
                                     'fact_refs': ['planet_Mars'], 'correction': 'Use the supplied directed aspect'}]
        else:
            raise AssertionError(stage)
        return SimpleNamespace(text=json.dumps(result), usage_metadata=SimpleNamespace(
            prompt_token_count=100, candidates_token_count=20, thoughts_token_count=7, total_token_count=127))


def test_briefs_preserve_av_and_varga_scope_without_legacy_effect_scores(dossier):
    b = build_briefs(dossier)
    for n, row in dossier['foundation']['houses'].items():
        assert b['facts'][f'av_{n}']['value']['sav'] == row['raw']['ashtakavarga']['sav']
        if row['related_varga']:
            assert b['facts'][f'varga_{n}']['value'] == row['related_varga']
            assert 'not the full' in b['facts'][f'varga_{n}']['scope']
    for name, fact in b['facts'].items():
        if fact['kind'] == 'natal_planet':
            assert 'effect_score' not in json.dumps(fact)
            assert 'overall_strength_score' not in json.dumps(fact)
            assert 'Weak Shadbala (0.00' not in json.dumps(fact)
    packet = batch_packet(b, ['pd_8'])
    assert len(packet['periods']) == 1
    assert not set(packet['periods'][0]['facts']) & set(packet['natal_facts'])
    assert 'pd_1_contact_1' not in packet['periods'][0]['facts']
    for key in ('life_area_catalog', 'combination_catalog'):
        assert packet[key]
        assert all('possibilities' not in row and row['label'] for row in packet[key].values())
    assert any(area['possibilities'] for area in dossier['periods'][0]['activation']['life_areas'])


def test_staged_generation_retains_all_periods_limits_parallelism_and_accounts_usage(dossier):
    model = Model(dossier)
    saved = []
    result = asyncio.run(narrate_next_chapter(dossier, 'hi', model=model, audit_sink=saved.append))
    assert model.peak == 9
    assert len(model.stages) == 21  # 9 planners + 3 coverage reviews + editor + AD spectrum + 3 writers + event review + 3 factual reviews
    assert len(result['report']['periods']) == 9
    assert result['generation']['input_tokens'] == 2100
    assert result['generation']['output_tokens'] == 420
    assert result['generation']['thinking_tokens'] == 147
    assert result['generation']['manual_edits'] is False
    assert result['audit']['reviews'][-1]['issues'] == []
    assert saved[-1]['manual_edits'] is False
    assert len(saved[0]['calls']) == 1  # snapshots, not a mutable shared audit


def test_only_affected_period_is_repaired_then_entire_report_rechecked(dossier):
    model = Model(dossier, factual_error=True)
    result = asyncio.run(narrate_next_chapter(dossier, model=model))
    assert [s for s in model.stages if s.startswith('repair_')] == ['repair_0_pd_8']
    assert model.stages[-1].startswith('fact_review_1_')
    assert result['report']['periods'][7]['timing_explanation'] == 'Broad timing'
    assert result['generation']['provider_calls'] == 25
    assert result['generation']['input_tokens'] == 2500


@pytest.mark.parametrize('checkpoint_key', ['checkpoint_report', 'unreleased_report'])
def test_review_resume_preserves_repaired_text_only_with_matching_upstream_inputs(dossier, checkpoint_key):
    first = asyncio.run(narrate_next_chapter(dossier, model=Model(dossier, factual_error=True)))
    if checkpoint_key == 'unreleased_report':
        first['audit'][checkpoint_key] = first['audit'].pop('checkpoint_report')
    model = Model(dossier)
    resumed = asyncio.run(narrate_next_chapter(dossier, model=model, resume_audit=first['audit']))
    assert resumed['audit']['resumed_review_checkpoint'] is True
    assert resumed['report']['periods'][7]['timing_explanation'] == 'Broad timing'
    assert all(stage.startswith('fact_review_') or stage == 'event_review' for stage in model.stages)
    changed = deepcopy(dossier)
    changed['native']['name'] = 'Another native'
    fresh = asyncio.run(narrate_next_chapter(changed, model=Model(changed), resume_audit=first['audit']))
    assert not fresh['audit'].get('resumed_review_checkpoint')


def test_reviewer_cannot_repair_nonexistent_quote_or_use_subjective_rejection(dossier):
    report = narrative_for(dossier)
    b = build_briefs(dossier)
    check = {'checked_period_ids': [p['period_id'] for p in report['periods']], 'checked_chapter': True,
             'issues': [{'section': 'pd_1', 'kind': 'factual', 'quote': 'invented quotation',
                         'fact_refs': [], 'correction': 'Change it'}], 'quality_notes': []}
    with pytest.raises(ValueError, match='quote actual'):
        validate_review(check, report, b)
    check['issues'][0].update(quote='Period summary', kind='boring')
    with pytest.raises(ValueError, match='Subjective'):
        validate_review(check, report, b)
    check['issues'] = []
    check['checked_period_ids'] = check['checked_period_ids'][:-1]
    with pytest.raises(ValueError, match='whole report'):
        validate_review(check, report, b)


def test_reviewer_chapter_field_address_resolves_but_still_checks_quote(dossier):
    report = narrative_for(dossier)
    check = {'checked_period_ids': [p['period_id'] for p in report['periods']], 'checked_chapter': True,
             'issues': [{'section': 'overview', 'kind': 'factual', 'quote': report['overview'],
                         'fact_refs': [], 'correction': 'Use the supplied facts'}],
             'quality_notes': [{'section': 'antardasha_events', 'instruction': 'Clarify the supported alternatives'}]}
    result = validate_review(check, report, build_briefs(dossier))
    assert result['issues'][0]['section'] == 'chapter'
    assert result['quality_notes'][0]['section'] == 'chapter'
    assert check['issues'][0]['section'] == 'overview'
    check['issues'][0]['quote'] = 'An invented sentence which is absent'
    with pytest.raises(ValueError, match='quote actual'):
        validate_review(check, report, build_briefs(dossier))


def test_structural_repair_is_bounded_and_records_failed_usage():
    class Broken:
        async def generate_content_async(self, *_a, **_kw):
            return SimpleNamespace(text='{}', usage_metadata=SimpleNamespace(prompt_token_count=13, candidates_token_count=2))
    r = Runner(Broken(), 'model', 'provider', 'en')
    def validate(_):
        raise ValueError('Missing periods')
    with pytest.raises(PipelineError, match='remains invalid') as e:
        asyncio.run(r.call('plan', 'instruction', {}, validate))
    assert len(e.value.audit['calls']) == 2
    assert sum(c['input_tokens'] for c in e.value.audit['calls']) == 26
    assert all('validation_error' in c for c in e.value.audit['calls'])


def test_fact_refs_cannot_cross_periods_and_empty_prose_is_not_patched_with_fallback(dossier):
    b = build_briefs(dossier)
    n = narrative_for(dossier)
    n['periods'] = n['periods'][:1]
    n['periods'][0]['manifestations'][0]['evidence_refs'] = ['pd_9_contact_1']
    with pytest.raises(ValueError, match='evidence reference'):
        validate_prose(n, ['pd_1'], b, dossier)
    n['periods'][0]['manifestations'][0]['evidence_refs'] = ['planet_Sun']
    n['periods'][0]['summary'] = ''
    with pytest.raises(ValueError, match='explanation'):
        validate_prose(n, ['pd_1'], b, dossier)


def test_invalid_language_fails_before_model_request(dossier):
    model = Model(dossier)
    with pytest.raises(ValueError, match='Choose en or hi'):
        asyncio.run(narrate_next_chapter(dossier, 'xx', model=model))
    assert model.stages == []


def test_complete_alternative_json_wrappers_do_not_trigger_paid_regeneration(dossier):
    from next_chapter.pipeline import normalize_period_wrapper
    n = narrative_for(dossier)
    ids = [p['period_id'] for p in n['periods']]
    original = deepcopy(n)
    keyed = {k: v for k, v in n.items() if k != 'periods'} | {p['period_id']: p for p in n['periods']}
    assert normalize_period_wrapper(keyed, ids) == n
    assert normalize_period_wrapper(n['periods'], ids) == {'periods': n['periods']}
    assert normalize_period_wrapper({'section': n}, ids) == n
    partial = {'section': {'periods': n['periods'][:-1]}}
    assert normalize_period_wrapper(partial, ids) == partial
    ambiguous = {'section': n, 'periods': []}
    assert normalize_period_wrapper(ambiguous, ids) == ambiguous
    assert n == original
    # Missing, duplicated, extra or contradictory IDs are never guessed/discarded.
    assert normalize_period_wrapper(n['periods'][:-1], ids) == n['periods'][:-1]
    keyed['pd_1'] = {**keyed['pd_1'], 'period_id': 'pd_2'}
    assert normalize_period_wrapper(keyed, ids) == keyed
    extra = {**keyed, 'pd_10': {}}
    assert normalize_period_wrapper(extra, ids) == extra


def test_background_misfiled_as_contact_is_preserved_without_claiming_exact_trigger(dossier):
    b = build_briefs(dossier)
    n = narrative_for(dossier)
    n['periods'] = n['periods'][:1]
    item = n['periods'][0]['manifestations'][0]
    item['evidence_refs'] = ['planet_Sun']
    background = next(k for k, v in b['periods'][0]['facts'].items() if v['kind'] == 'transit_background')
    item['contact_refs'] = [background]
    original = deepcopy(n)
    result = validate_prose(n, ['pd_1'], b, dossier)
    normalized = result['periods'][0]['manifestations'][0]
    assert normalized['contact_refs'] == []
    assert background in normalized['evidence_refs']
    assert n == original
    item['contact_refs'] = ['pd_9_background_1']
    with pytest.raises(ValueError, match='contact_refs'):
        validate_prose(n, ['pd_1'], b, dossier)


def test_resume_reuses_only_exact_model_prompt_and_revalidates_outputs():
    class Counting:
        calls = 0
        async def generate_content_async(self, *_a, **_kw):
            self.calls += 1
            return SimpleNamespace(text='{"valid":true}', usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=2))
    model = Counting()
    def validate(x):
        if x != {'valid': True}:
            raise ValueError('Bad cached data')
        return x
    async def run():
        first = Runner(model, 'm', 'v', 'en')
        await first.call('stage', 'instruction', {'native': 'A'}, validate)
        resumed = Runner(model, 'm', 'v', 'en', resume_audit=first.audit)
        await resumed.call('stage', 'instruction', {'native': 'A'}, validate)
        assert model.calls == 1
        assert resumed.audit['calls'][0]['reused'] is True
        assert resumed.audit['calls'][0]['input_tokens'] == 0
        assert resumed.audit['calls'][0]['source_usage']['input_tokens'] == 10
        await resumed.call('stage', 'instruction', {'native': 'B'}, validate)
        assert model.calls == 2
        another_model = Runner(model, 'different-model', 'v', 'en', resume_audit=first.audit)
        await another_model.call('stage', 'instruction', {'native': 'A'}, validate)
        assert model.calls == 3
        broken = deepcopy(first.audit)
        broken['calls'][0]['raw_response'] = '{"valid":false}'
        revalidated = Runner(model, 'm', 'v', 'en', resume_audit=broken)
        await revalidated.call('stage', 'instruction', {'native': 'A'}, validate)
        assert model.calls == 4
    asyncio.run(run())


def test_material_quality_improvement_is_bounded_without_subjective_failure(dossier):
    class NeedsDepth(Model):
        async def generate_content_async(self, prompt, **kwargs):
            response = await super().generate_content_async(prompt, **kwargs)
            if 'STAGE: fact_review_' in prompt:
                value = json.loads(response.text)
                value['quality_notes'] = [] if 'pd_5' not in value['checked_period_ids'] else [{'section': 'pd_5', 'instruction': 'Explain how the relevant BAV and mixed lordship qualify this possibility.'}]
                response.text = json.dumps(value)
            return response
    model = NeedsDepth(dossier)
    result = asyncio.run(narrate_next_chapter(dossier, model=model))
    assert [s for s in model.stages if s.startswith('repair')] == ['repair_0_pd_5', 'repair_1_pd_5']
    assert model.stages[-1].startswith('fact_review_2_')
    assert result['generation']['factual_review'] == 'passed'
    assert result['audit']['reviews'][-1]['quality_notes']  # Honest advisory findings remain visible.


def test_unresolved_review_findings_are_recorded_without_failing_report(dossier):
    class CannotRepair(Model):
        async def generate_content_async(self, prompt, **kwargs):
            response = await super().generate_content_async(prompt, **kwargs)
            if 'STAGE: fact_review_' in prompt:
                value = json.loads(response.text)
                data = json.loads(prompt.split('\nDATA:\n', 1)[1])
                quote = next((p['timing_explanation'] for p in data['report']['periods'] if p['period_id'] == 'pd_1'), '')
                value['issues'] = [] if 'pd_1' not in value['checked_period_ids'] else [{'section': 'pd_1', 'kind': 'factual', 'quote': quote,
                                    'fact_refs': [], 'correction': 'Use the provided timing evidence correctly'}]
                response.text = json.dumps(value)
            return response
    model = CannotRepair(dossier)
    result = asyncio.run(narrate_next_chapter(dossier, model=model))
    assert result['generation']['factual_review'] == 'warnings'
    assert any(w['stage'] == 'fact_review_final' for w in result['audit']['validation_warnings'])
    assert [s for s in model.stages if s.startswith('repair')] == ['repair_0_pd_1', 'repair_1_pd_1']
    assert 'checkpoint_report' in result['audit']
    assert len(result['audit']['reviews']) == 4


def test_priority_briefs_surface_active_lord_conditions_and_correct_individual_bav(dossier):
    b = build_briefs(dossier)
    packet = batch_packet(b, [p['id'] for p in dossier['periods']])
    for priority, pd in zip(packet['priority_conditions'], dossier['periods']):
        assert set(priority['lords_to_reconcile']) == set(pd['activation']['levels'].values())
        for name, condition in priority['lords_to_reconcile'].items():
            assert condition['special_roles'] == dossier['foundation']['planets'][name]['worksheet']['special_roles']
        for house, points in priority['PD_house_scores'].items():
            raw = dossier['foundation']['houses'][house]['raw']['ashtakavarga']
            assert points['SAV'] == raw['sav']['house_points']
            assert points['PD_planet_BAV'] == next((g['bindus'] for g in raw['givers'] if g['planet'] == pd['planet']), None)


def test_ad_spectrum_and_transit_axis_are_exposed_without_canned_predictions(dossier):
    b = build_briefs(dossier)
    assert 'teeth' in b['facts']['house_2']['value']['body_significations']
    assert {'astrology', 'occult studies', 'insurance claim or payout'} <= set(b['facts']['house_8']['value']['significations'])
    chapter = b['shared']['antardasha_packet']
    segments = [chapter['facts'][ref]['value'] for ref in chapter['transit_refs']]
    assert segments[0]['start_at'] == dossier['spine']['antardasha']['start_at']
    assert segments[-1]['end_at'] == dossier['spine']['antardasha']['end_at']
    for level in ('MD', 'AD'):
        own = [s for s in segments if s['period_level'] == level]
        assert own and all(a['end_at'] == z['start_at'] for a, z in zip(own, own[1:]))
        assert all(s['transiting_planet'] == b['shared']['chapter_activation']['levels'][level] for s in own)
    for pd in b['periods']:
        assert pd['ad_transit_refs'] and pd['house_coverage']
        for ref in pd['ad_transit_refs']:
            assert pd['facts'][ref]['value']['is_antardasha_lord']


def test_structured_ad_events_and_all_transit_segments_are_required(dossier):
    b = build_briefs(dossier)
    report = narrative_for(dossier)
    for p in report['periods']:
        p['manifestations'][0]['evidence_refs'] = p['manifestations'][0]['planet_refs']
    ids = [p['period_id'] for p in report['periods']]
    assert validate_prose(report, ids, b, dossier, headers=True)
    bad = deepcopy(report)
    bad['antardasha_events'] = []
    with pytest.raises(ValueError, match='event spectrum'):
        validate_prose(bad, ids, b, dossier, headers=True)
    bad = deepcopy(report)
    bad['periods'][0]['transit_story'] = []
    with pytest.raises(ValueError, match='transit explanation'):
        validate_prose(bad, ids, b, dossier, headers=True)
    bad = deepcopy(report)
    bad['antardasha_events'][0]['evidence_refs'] = ['invented']
    with pytest.raises(ValueError, match='evidence reference'):
        validate_prose(bad, ids, b, dossier, headers=True)


def test_preview_places_ad_events_and_transits_before_pd_breakdown(dossier):
    from next_chapter.preview import render_preview
    text = render_preview(dossier, {'report': narrative_for(dossier), 'language': 'en'})
    assert text.index('Possible events across this Antardasha') < text.index("id='period-1'")
    assert text.index('Mahadasha and Antardasha transits') < text.index("id='period-1'")
    assert text.count('Mahadasha, Antardasha and Pratyantardasha transits') == 9


def test_event_review_routes_specificity_feedback_into_targeted_repairs(dossier):
    class EventModel(Model):
        async def generate_content_async(self, prompt, **kwargs):
            response = await super().generate_content_async(prompt, **kwargs)
            if '\nSTAGE: event_review\n' in prompt:
                result = json.loads(response.text)
                result['quality_notes'] = [{'section': 'pd_1', 'instruction': 'Replace generic topic fragments with observable conditional events.'}]
                response.text = json.dumps(result)
            return response
    model = EventModel(dossier)
    result = asyncio.run(narrate_next_chapter(dossier, model=model))
    assert [stage for stage in model.stages if stage.startswith('repair_')] == ['repair_0_pd_1']
    assert result['audit']['event_review']['quality_notes'][0]['section'] == 'pd_1'
    assert result['audit']['reviews'][-1]['issues'] == []


def test_editorial_summary_strings_are_preserved_as_advisory_notes(dossier):
    from next_chapter.pipeline import validate_event_review
    report = narrative_for(dossier)
    source = {'checked_period_ids': [p['period_id'] for p in report['periods']], 'checked_chapter': True,
              'issues': ['Specificity is missing.'], 'quality_notes': [{'section': 'antardasha_events', 'instruction': 'Use observable changes.'}]}
    original = deepcopy(source)
    result = validate_event_review(source, report, build_briefs(dossier))
    assert source == original
    assert result['issues'] == []
    assert all(n['section'] == 'chapter' for n in result['quality_notes'])
    assert result['quality_notes'][-1]['instruction'] == 'Specificity is missing.'
    source['quality_notes'][0]['section'] = 'unknown'
    with pytest.raises(ValueError, match='known section'):
        validate_event_review(source, report, build_briefs(dossier))


def test_final_fact_patch_changes_only_quoted_text_in_its_section(dossier):
    from next_chapter.pipeline import apply_factual_patches
    original = narrative_for(dossier)
    issues = [{'section': 'pd_7', 'quote': 'Broad timing'}]
    fixed = apply_factual_patches(original, issues, {'patches': [{'issue_index': 0, 'replacement': 'An exact seventh aspect, not a conjunction'}]})
    assert original['periods'][6]['timing_explanation'] == 'Broad timing'
    for i in range(9):
        if i != 6:
            assert fixed['periods'][i] == original['periods'][i]
    assert fixed['periods'][6]['manifestations'] == original['periods'][6]['manifestations']
    assert fixed['antardasha_events'] == original['antardasha_events']
    with pytest.raises(ValueError, match='Unknown or duplicate'):
        apply_factual_patches(original, issues, {'patches': [{'issue_index': 1, 'replacement': 'Invented'}]})
    with pytest.raises(ValueError, match='change'):
        apply_factual_patches(original, issues, {'patches': [{'issue_index': 0, 'replacement': 'Broad timing'}]})


def test_ad_only_transit_story_cannot_hide_md_or_pd_transits(dossier):
    b = build_briefs(dossier)
    report = narrative_for(dossier)
    for pd in report['periods']:
        pd['manifestations'][0]['evidence_refs'] = pd['manifestations'][0]['planet_refs']
    target = next(p for p in b['periods'] if set(p['period_lord_transit_refs']) - set(p['ad_transit_refs']))
    row = next(p for p in report['periods'] if p['period_id'] == target['period']['id'])
    row['transit_story'] = [{'evidence_refs': target['ad_transit_refs'], 'explanation': 'AD only'}]
    with pytest.raises(ValueError, match='omitted'):
        validate_prose(report, [p['period_id'] for p in report['periods']], b, dossier, headers=True)


def test_resume_reuses_exact_successful_structural_repair():
    class Repairable:
        def __init__(self):
            self.calls = 0
        async def generate_content_async(self, *_args, **_kwargs):
            self.calls += 1
            if self.calls > 2:
                raise AssertionError('Already repaired response should be reused')
            return SimpleNamespace(text=json.dumps({'answer': 'valid'} if self.calls == 2 else {}),
                usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=5))
    def validate(value):
        if value.get('answer') != 'valid':
            raise ValueError('Missing answer')
        return value
    model = Repairable()
    first = Runner(model, 'same-model', 'provider', 'en')
    assert asyncio.run(first.call('stage', 'instruction', {}, validate)) == {'answer': 'valid'}
    resumed = Runner(model, 'same-model', 'provider', 'en', resume_audit=first.audit)
    assert asyncio.run(resumed.call('stage', 'instruction', {}, validate)) == {'answer': 'valid'}
    assert model.calls == 2
    assert resumed.audit['calls'][0]['reused'] is True
    assert resumed.audit['calls'][0]['source_usage']['input_tokens'] == 10

    again = Runner(model, 'same-model', 'provider', 'en', resume_audit=resumed.audit)
    assert asyncio.run(again.call('stage', 'instruction', {}, validate)) == {'answer': 'valid'}
    assert model.calls == 2


def test_planner_resolves_known_activation_citation_but_rejects_invented_one(dossier):
    from next_chapter.pipeline import RULES
    b = build_briefs(dossier)
    packet = batch_packet(b, ['pd_1'])
    model = Model(dossier)
    response = asyncio.run(model.generate_content_async(RULES + '\nSTAGE: plan_pd_1\nDATA:\n' + json.dumps(packet)))
    plan = json.loads(response.text)
    source_id = packet['periods'][0]['synthesis_space']['constant_natal_source_ids'][0]
    expected = packet['periods'][0]['synthesis_space']['sources'][source_id]['evidence_ref']
    plan['periods'][0]['themes'][0]['support_refs'] = [source_id]
    checked = validate_plans(plan, ['pd_1'], b)
    assert checked['periods'][0]['themes'][0]['support_refs'] == [expected]
    plan['periods'][0]['themes'][0]['support_refs'] = ['pd_1_natal_invented']
    with pytest.raises(ValueError, match='unknown evidence'):
        validate_plans(plan, ['pd_1'], b)


def test_whole_ad_spectrum_omission_is_advisory(dossier):
    class MissingFamily(Model):
        async def generate_content_async(self, prompt, **kwargs):
            response = await super().generate_content_async(prompt.split('\nRepair only this stage.', 1)[0], **kwargs)
            if '\nSTAGE: chapter_spectrum\n' in prompt:
                value = json.loads(response.text)
                value['family_coverage'].pop()
                response.text = json.dumps(value)
            return response
    result = asyncio.run(narrate_next_chapter(dossier, model=MissingFamily(dossier)))
    assert any(w['stage'] == 'chapter_spectrum' for w in result['audit']['validation_warnings'])


def test_preview_exposes_all_period_lord_activation_tables(dossier):
    from next_chapter.preview import render_preview
    text = render_preview(dossier)
    assert text.count("class='activation-evidence'") == 9
    assert 'Natal occupation' in text and 'Natal lordship' in text and 'Transit aspects' in text
    assert 'Venus · Mahadasha' in text
    assert 'Sun · Antardasha' in text


def test_coverage_warnings_do_not_repair_or_fail_customer_report(dossier):
    class IncompleteCoverage(Model):
        async def generate_content_async(self, prompt, **kwargs):
            response = await super().generate_content_async(prompt, **kwargs)
            stage = re.search(r'STAGE: ([^\n]+)', prompt)[1]
            value = json.loads(response.text)
            if stage.startswith('plan_'):
                for row in value['periods']:
                    row['considered_houses'] = []
            elif stage == 'chapter_spectrum':
                value['family_coverage'] = []
            response.text = json.dumps(value)
            return response
    model = IncompleteCoverage(dossier)
    result = asyncio.run(narrate_next_chapter(dossier, 'en', model=model))
    assert len(result['report']['periods']) == 9
    warnings = result['audit']['validation_warnings']
    assert any(w['stage'] == 'plan_pd_2' and 'activated houses' in w['message'] for w in warnings)
    assert any(w['stage'] == 'chapter_spectrum' for w in warnings)
    assert len([s for s in model.stages if s.startswith('plan_')]) == 9
    assert result['generation']['validation_warning_count'] == len(warnings)
