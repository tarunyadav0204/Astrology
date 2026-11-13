import asyncio
import json
import sys
from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from chat import answer_evidence_audit as audit


@pytest.fixture
def storage(monkeypatch):
    writes = []
    @contextmanager
    def connection():
        yield SimpleNamespace(commit=lambda: None)
    monkeypatch.setattr(audit, 'get_conn', connection)
    monkeypatch.setattr(audit, 'execute', lambda conn, sql, params=None: writes.append((sql, params)))
    return writes


def fake_model(monkeypatch, text=None, failure=False):
    prompts = []
    class Model:
        async def generate_text_from_prompt(self, prompt, **kwargs):
            prompts.append(prompt)
            return {'success': not failure, 'error': 'test unavailable' if failure else None,
                    'response': text, 'chat_llm_provider': 'test', 'chat_llm_model': 'test'}
    monkeypatch.setitem(sys.modules, 'ai.gemini_chat_analyzer', SimpleNamespace(GeminiChatAnalyzer=Model))
    return prompts


def test_full_answer_and_birth_snapshot_retained():
    answer = 'Long answer. ' * 1000 + 'D9 ascendant is Scorpio.'
    subjects = {'native': {'birth': {'name': 'Native'}, 'chart_id': 10}}
    brief = audit.build_evidence_brief(question='D9?', answer=answer, intent={}, result={},
                                     chat_tier='standard', audit_subjects=subjects)
    assert brief['answer'] == answer
    assert brief['subjects'] == subjects


def test_extraction_then_calculator_result_saved_for_admin(monkeypatch, storage):
    from chat.chart_fact_audit import snapshot_subject
    answer = 'D9 ascendant is Scorpio.'
    extraction = {'claims': [{'quote': answer, 'subject_id': 'native', 'chart': 'D9',
        'chart_scope': 'natal', 'reference_frame': 'ascendant', 'claim_type': 'ascendant_sign',
        'asserted_value': 'Scorpio'}]}
    prompts = fake_model(monkeypatch, json.dumps(extraction))
    subjects = {'native': snapshot_subject({'name': 'Native', 'date': '1963-02-17',
        'time': '16:45', 'latitude': 23.15, 'longitude': 120.16, 'timezone': 'UTC+8'})}
    brief = {'answer': answer, 'subjects': subjects, 'calculated_context': {'SECRET_EXPECTED_FACT': 'Sagittarius'}}
    asyncio.run(audit.run_answer_evidence_audit(91, brief))
    saved = next(params for sql, params in storage if 'UPDATE chat_answer_evidence_audits' in sql)
    report = json.loads(saved[1])
    assert saved[0] == 'completed'
    assert report['counts'] == {'mismatch': 1}
    assert report['fact_checks'][0]['calculated_value'] == 'Sagittarius'
    assert report['replay']['subjects'] == subjects
    assert report['calculator_fingerprints']
    assert 'SECRET_EXPECTED_FACT' not in prompts[0]
    assert all('chat_messages' not in sql or 'REFERENCES' in sql for sql, _ in storage)


@pytest.mark.parametrize('text,failure', [('not json', False), ('{"claims":"bad"}', False), (None, True)])
def test_audit_failure_is_saved_without_rejecting_answer(monkeypatch, storage, text, failure):
    fake_model(monkeypatch, text, failure)
    asyncio.run(audit.run_answer_evidence_audit(91, {'answer': 'Already delivered', 'subjects': {}}))
    saved = next(params for sql, params in storage if 'UPDATE chat_answer_evidence_audits' in sql)
    assert saved[0] == 'failed'
    assert all('UPDATE chat_messages' not in sql and 'credit_transactions' not in sql for sql, _ in storage)


def test_scheduling_does_not_wait_for_extractor(monkeypatch, storage):
    calls = []
    async def run(message_id, brief):
        calls.append(message_id)
    monkeypatch.setattr(audit, 'run_answer_evidence_audit', run)
    monkeypatch.setattr(audit, 'audit_enabled', lambda: True)
    async def scenario():
        audit.schedule_answer_evidence_audit(message_id=9, question='q', answer='a', intent={}, result={}, chat_tier='instant')
        assert calls == []
        await asyncio.sleep(0)
        assert calls == [9]
    asyncio.run(scenario())


def test_evidence_endpoint_requires_admin():
    from chat_history.admin_routes import router, require_admin
    endpoint = next(r for r in router.routes if r.path == '/admin/chat/evidence-audit/{message_id}')
    assert any(d.call is require_admin for d in endpoint.dependant.dependencies)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        require_admin(SimpleNamespace(role='user'))
    assert exc.value.status_code == 403
