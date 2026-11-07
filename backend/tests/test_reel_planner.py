import copy
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from reel_studio.routes import _planned_beats
from reel_studio.planning import validate_scene_count
from reel_studio.presenter import validate_presenter_beats


def plan(count=8):
    return [{'type': 'opening' if i == 0 else 'closing' if i == count - 1 else 'chart_focus',
             'narration': 'Build your career through steady learning.', 'pause_after': 'short',
             'visual_instruction': 'Show the supplied chart with its existing placements.',
             'evidence_ids': ['claim_1'], 'focus_nodes': [], 'draw_edges': []} for i in range(count)]


def planner(monkeypatch, responses):
    calls = []
    import openai
    def create(**kwargs):
        calls.append(kwargs)
        payload = responses[len(calls)-1]
        return SimpleNamespace(output_text=json.dumps(payload if isinstance(payload, dict) else {'beats': payload}))
    monkeypatch.setenv('OPENAI_API_KEY', 'test-no-network')
    monkeypatch.setattr(openai, 'OpenAI', lambda **_: SimpleNamespace(responses=SimpleNamespace(create=create)))
    def run(presenter=False):
        return _planned_beats('Build your career through steady learning.', 'What helps my career?',
                              [{'id': 'claim_1', 'text': 'Build steadily.'}],
                              {'visual_graph': {'nodes': [{'id': 'natal.d1.house.1'}], 'edges': []}},
                              'hi', 90, presenter)
    return calls, run


def test_optional_annotations_and_scene_target_do_not_fail_customer(monkeypatch):
    candidate = plan(11)  # Outside the short-reel editorial target, still renderable.
    candidate[1]['evidence_ids'] = []
    candidate[2]['focus_nodes'] = ['unknown-annotation']
    candidate[2]['draw_edges'] = ['unknown-edge']
    calls, run = planner(monkeypatch, [candidate])
    result = run()
    assert len(result) == 11
    assert result[2]['draw_edges'] == []
    assert result[1]['narration'] == candidate[1]['narration']
    assert len(calls) == 1
    validate_scene_count(result)  # Same rule used in the renderer after charging.
    fields = calls[0]['text']['format']['schema']['properties']['beats']['items']['properties']
    assert 'chart_focus' in fields['type']['enum']
    assert fields['evidence_ids']['items']['enum'] == ['claim_1']
    assert fields['focus_nodes']['items']['enum'] == ['natal.d1.house.1']
    assert fields['draw_edges']['maxItems'] == 0


def test_repair_gets_original_candidate_and_all_render_errors(monkeypatch):
    bad = plan()
    bad[1]['narration'] = ''
    bad[2]['visual_instruction'] = ''
    bad[3]['narration'] = 'Keep this distinctive explanation unchanged.'
    good = copy.deepcopy(bad)
    good[1]['narration'] = 'Keep learning through practical projects.'
    good[2]['visual_instruction'] = 'Show the supplied chart.'
    calls, run = planner(monkeypatch, [bad, good])
    result = run()
    repair = calls[1]['input']
    assert 'Beat 2 has no narration.' in repair
    assert 'Beat 3 has no visual direction.' in repair
    assert 'Keep this distinctive explanation unchanged.' in repair
    assert 'REJECTED CANDIDATE' in repair
    assert result[3]['narration'] == bad[3]['narration']


def test_presenter_does_not_reject_unicode_character_count(monkeypatch):
    # Characters are not a speech-duration measure. This previously failed at 101.
    line = 'व्यावसायिक विशेषज्ञता आत्मविश्वासपूर्ण निर्णयों और दीर्घकालिक प्रतिबद्धताओं से विकसित होगी।'
    line = line.replace('विशेषज्ञता', 'विशेषज्ञतापूर्णक्षमताएँ')
    assert len(line) > 100 and len(line.split()) <= 10
    candidate = plan()
    candidate[0]['narration'] = candidate[-1]['narration'] = line
    calls, run = planner(monkeypatch, [candidate])
    beats = run(presenter=True)
    validate_presenter_beats(beats)
    assert len(calls) == 1
    assert beats[0]['end_seconds'] == 5
    assert beats[-1]['end_seconds'] - beats[-1]['start_seconds'] == 5


def test_presenter_repair_identifies_both_long_lines(monkeypatch):
    bad = plan()
    bad[0]['narration'] = 'This introduction has too many spoken words to fit naturally into five seconds.'
    bad[-1]['narration'] = 'This closing also has too many spoken words for a calm five second take.'
    good_lines = {'opening': ['Explore', 'your', 'career', 'with', 'your', 'chart.'],
                  'closing': ['Build', 'your', 'career', 'through', 'steady', 'learning.']}
    calls, run = planner(monkeypatch, [bad, good_lines])
    result = run(presenter=True)
    assert calls[1]['text']['format']['name'] == 'reel_presenter_lines'
    assert bad[0]['narration'] in calls[1]['input']
    assert bad[-1]['narration'] in calls[1]['input']
    assert result[0]['narration'] == ' '.join(good_lines['opening'])
    assert result[1]['narration'] == bad[1]['narration']
    assert len(result) == len(bad)
    assert calls[1]['text']['format']['schema']['properties']['opening']['maxItems'] == 10


def test_unusable_narration_still_errors_without_replacement(monkeypatch):
    bad = plan()
    bad[1]['narration'] = ''
    calls, run = planner(monkeypatch, [bad, bad])
    with pytest.raises(HTTPException) as error:
        run()
    assert error.value.status_code == 503
    assert len(calls) == 2
