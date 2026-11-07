import asyncio
import json
import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace
import pytest
from reel_studio import costs, routes, worker

@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / 'costs.sqlite'
    @contextmanager
    def connect():
        conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
        try: yield conn
        finally: conn.close()
    def execute(conn, sql, params=()):
        return conn.execute(sql.replace('%s', '?').replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY'), params)
    def ensure(conn):
        costs.ensure_tables(conn)
        execute(conn, '''CREATE TABLE IF NOT EXISTS reel_generation_costs (
            id INTEGER PRIMARY KEY, user_id INTEGER,run_id TEXT,stage TEXT,provider TEXT,
            units REAL, unit_cost_inr REAL,total_cost_inr REAL,metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    monkeypatch.setattr(costs, 'get_conn', connect)
    monkeypatch.setattr(costs, 'execute', execute)
    monkeypatch.setattr(routes, '_ensure_tables', ensure)
    monkeypatch.setattr(routes, 'get_conn', connect)
    monkeypatch.setattr(routes, 'execute', execute)
    with connect() as conn:
        ensure(conn)
        conn.commit()
    def events():
        with connect() as conn:
            return [(r[0], r[1], json.loads(r[2])) for r in conn.execute(
                'SELECT stage,total_cost_inr,metadata_json FROM reel_generation_costs ORDER BY id')]
    return events, connect

def test_image_includes_prompt_and_logo_input_cost():
    amount, parts = costs.price('image', 'gpt-image-2', {
        'input_tokens': 3000, 'input_tokens_details': {'text_tokens': 2000, 'image_tokens': 1000},
        'output_tokens': 200}, costs.DEFAULTS)
    assert amount == pytest.approx((2000*5+1000*8+200*30)/1e6*95)
    assert len(parts) == 3

def test_text_cache_and_reasoning_not_double_charged():
    amount, _ = costs.price('planning', 'gpt-5.6-luna', {
        'input_tokens': 1000, 'input_tokens_details': {'cached_tokens': 400},
        'output_tokens': 2000, 'output_tokens_details': {'reasoning_tokens': 1800}}, costs.DEFAULTS)
    assert amount == pytest.approx((600*.2+400*.02+2000*1.2)/1e6*95)

def test_omni_all_components_and_missing_usage():
    usage = {'total_input_tokens': 1378, 'total_thought_tokens': 339,
             'output_tokens_by_modality': [{'modality': 'video', 'tokens': 9655}]}
    amount, _ = costs.price('video', 'gemini-omni-1.1-flash', usage, costs.DEFAULTS)
    assert amount == pytest.approx((1378*1.5+339*9+9655*17.5)/1e6*95)
    assert costs.price('video', 'gemini-omni-1.1-flash', {}, costs.DEFAULTS)[0] is None
    assert costs.price('image', 'different-model', {}, costs.DEFAULTS)[0] is None

def test_partial_failure_keeps_completed_charges_and_uncertain_retry(ledger):
    events, connect = ledger
    with pytest.raises(RuntimeError):
        with costs.session(18, 'run-failure', planning=True):
            with pytest.raises(TimeoutError):
                with costs.attempt('image', 'gpt-image-2'): raise TimeoutError()
            with costs.attempt('tts', 'en-IN-Chirp-HD-O') as event:
                event.finish({'characters': 200})
                event.finish({'characters': 200})
            raise RuntimeError('A later scene failed')
    rows = events()
    assert [r[0] for r in rows] == ['compute', 'image', 'tts']
    assert rows[1][2]['state'] == 'uncertain'
    assert rows[2][1] == pytest.approx(200*30/1e6*95)
    with connect() as conn:
        assert conn.execute('SELECT status FROM reel_cost_runs').fetchone()[0] == 'planning_failed'

def test_parallel_context_and_success_survive_another_failure(ledger):
    events, _ = ledger
    async def work():
        async def one(index):
            await asyncio.sleep(index*.001)
            def paid():
                with costs.attempt('tts', 'hi-IN-Chirp-HD-O') as event:
                    if index == 1: raise TimeoutError()
                    event.finish({'characters': 100})
            await asyncio.to_thread(paid)
        return await asyncio.gather(*(one(i) for i in range(4)), return_exceptions=True)
    with costs.session(18, 'parallel'): results = asyncio.run(work())
    assert isinstance(results[1], TimeoutError)
    rows = [r for r in events() if r[0] == 'tts']
    assert len(rows) == 4
    assert sum(r[1] for r in rows) == pytest.approx(3*100*30/1e6*95)

def test_received_usage_kept_when_asset_is_invalid(ledger):
    events, _ = ledger
    with costs.session(18, 'invalid-asset'):
        with pytest.raises(ValueError):
            with costs.attempt('image', 'gpt-image-2') as event:
                event.finish({'input_tokens': 3, 'input_tokens_details': {'text_tokens': 1, 'image_tokens': 2}, 'output_tokens': 4}, 'req-test')
                raise ValueError('bad image bytes')
    assert events()[1][2]['request_id'] == 'req-test'
    assert events()[1][1] > 0

def test_new_rates_do_not_reprice_existing_run(ledger):
    _, connect = ledger
    with costs.session(18, 'snapshot'): pass
    with connect() as conn:
        conn.execute('INSERT INTO reel_cost_settings VALUES (1,?)', (json.dumps({**costs.DEFAULTS, 'usd_to_inr': 100}),))
        conn.commit()
    with costs.session(18, 'snapshot'): assert costs.CURRENT.get()[2]['usd_to_inr'] == 95
    with costs.session(18, 'new-run'): assert costs.CURRENT.get()[2]['usd_to_inr'] == 100

def test_complete_estimate_tax_fees_and_unknown_not_zero():
    config = {**costs.DEFAULTS, 'tax_percent': 18, 'payment_fee_percent': 2}
    result = costs.summarize([{'stage': 'image', 'total_inr': 100}], config, tracked=True)
    assert result['estimated_total_inr'] == 120.36
    assert result['cost_complete']
    assert result['actual_total_inr'] is None
    result = costs.summarize([{'stage': 'video', 'total_inr': None}], config, tracked=True)
    assert not result['cost_complete']
    assert 'video' in result['missing_costs'][0]
    assert not costs.summarize([], config, tracked=False)['cost_complete']

def test_cost_settings_reject_nonfinite_negative_and_missing():
    for value in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError): costs.validate_settings({**costs.DEFAULTS, 'tax_percent': value})
    with pytest.raises(ValueError): costs.validate_settings({})
    assert costs.validate_settings(costs.DEFAULTS) == costs.DEFAULTS

def test_tts_records_exact_cleaned_input(ledger, monkeypatch):
    events, _ = ledger
    sent = []
    class Client:
        def __init__(self, **_): pass
        def synthesize_speech(self, **kwargs):
            sent.append(kwargs['input'].text)
            assert kwargs['retry'] is None
            return SimpleNamespace(audio_content=b'audio')
    monkeypatch.setattr(worker.texttospeech, 'TextToSpeechClient', Client)
    monkeypatch.setattr(worker, '_get_google_credentials', lambda: None)
    monkeypatch.setattr(worker, '_build_voice_and_config', lambda *args: (None, None))
    monkeypatch.setattr(worker, '_segment_text_to_plain', lambda text: 'नमस्ते दुनिया।')
    with costs.session(18, 'tts-cleaned'):
        asyncio.run(worker._podcast_audio('## नमस्ते **दुनिया**', 'hi', 'hi-IN-Chirp-HD-O'))
    assert events()[1][2]['usage']['characters'] == len(sent[0])


def test_admin_includes_failed_planning_and_invoice_reconciliation(ledger):
    events, connect = ledger
    with costs.session(18, 'draft-without-job', planning=True):
        with costs.attempt('tts', 'en-IN-Chirp-HD-O') as event:
            event.finish({'characters': 100})
    costs.set_status('draft-without-job', 'planning_failed')
    with connect() as conn:
        conn.execute('''CREATE TABLE reel_render_jobs (id TEXT,user_id INTEGER,status TEXT,
            plan_json TEXT,created_at TIMESTAMP,updated_at TIMESTAMP)''')
        conn.commit()
    admin = SimpleNamespace(role='admin', userid=1)
    result = routes.admin_reel_runs(100, admin)
    assert len(result['runs']) == 1
    run = result['runs'][0]
    assert run['status'] == 'planning_failed'
    assert run['job_id'] is None
    assert run['actual_total_inr'] is None
    assert run['estimated_total_inr'] > 0
    assert not run['cost_complete']
    routes.reconcile_cost(run['run_id'], routes.CostReconciliation(total_inr=1.25, reference='Invoice allocation test'), admin)
    run = routes.admin_reel_runs(100, admin)['runs'][0]
    assert run['actual_total_inr'] == 1.25
    assert len(events()) == 2  # reconciliation never rewrites provider evidence
    with costs.session(18, 'draft-without-job'):
        with costs.attempt('tts', 'en-IN-Chirp-HD-O') as event:
            event.finish({'characters': 50})
    changed = routes.admin_reel_runs(100, admin)['runs'][0]
    assert changed['actual_total_inr'] is None
    assert any('reconcile again' in reason for reason in changed['missing_costs'])
    with pytest.raises(routes.HTTPException) as error:
        routes.get_cost_settings(SimpleNamespace(role='user', userid=18))
    assert error.value.status_code == 403


def test_real_image_provider_retry_metering(ledger, monkeypatch):
    import httpx
    from partner_profile.image_provider import OpenAIPartnerPortraitProvider
    events, _ = ledger
    monkeypatch.setenv('OPENAI_API_KEY', 'test-no-network')
    monkeypatch.setenv('PARTNER_PORTRAIT_IMAGE_MODEL', 'gpt-image-2')
    original_client = httpx.AsyncClient
    calls = []
    def handle(request):
        calls.append(request)
        if len(calls) == 1:
            raise httpx.ReadTimeout('test timeout')
        return httpx.Response(200, headers={'x-request-id': 'req-image-test'}, json={
            'data': [{'b64_json': 'aW1hZ2U='}], 'usage': {'input_tokens': 3,
            'input_tokens_details': {'text_tokens': 1, 'image_tokens': 2}, 'output_tokens': 4}})
    monkeypatch.setattr(httpx, 'AsyncClient', lambda **kw: original_client(**kw, transport=httpx.MockTransport(handle)))
    with costs.session(18, 'image-retry'):
        assert asyncio.run(worker._gpt_image('brief', logo=b'logo')) == b'image'
    rows = [r for r in events() if r[0] == 'image']
    assert len(rows) == 2
    assert rows[0][2]['state'] == 'uncertain'
    assert rows[1][2]['request_id'] == 'req-image-test'
    assert rows[1][1] > 0


def test_planner_and_repair_both_record_usage_before_validation(ledger, monkeypatch):
    import openai
    events, _ = ledger
    monkeypatch.setenv('OPENAI_API_KEY', 'test-no-network')
    monkeypatch.setenv('REEL_PLANNER_MODEL', 'gpt-5.6-luna')
    calls = []
    def create(**kwargs):
        calls.append(kwargs)
        beats = [{'type': 'chart_focus', 'narration': 'Learn through steady practice.',
                  'pause_after': 'short', 'visual_instruction': 'Show the supplied chart.',
                  'evidence_ids': [], 'focus_nodes': [], 'draw_edges': []} for _ in range(8)]
        if len(calls) == 1: beats[0]['narration'] = ''
        return SimpleNamespace(output_text=json.dumps({'beats': beats}), id=f'req-{len(calls)}',
                               usage={'input_tokens': 100, 'output_tokens': 200})
    def client(**kwargs):
        assert kwargs['max_retries'] == 0
        return SimpleNamespace(responses=SimpleNamespace(create=create))
    monkeypatch.setattr(openai, 'OpenAI', client)
    with costs.session(18, 'planner-repair', planning=True):
        routes._planned_beats('Learn steadily.', 'How?', [], {'visual_graph': {'nodes': [], 'edges': []}}, 'en', 90)
    assert [r[0] for r in events()] == ['compute', 'planning', 'plan_repair']
    assert all(r[1] > 0 for r in events()[1:])


def test_video_retry_retains_unknown_failed_attempt_and_success_usage(ledger, monkeypatch):
    import httpx
    import base64
    events, _ = ledger
    calls = []
    original_client = httpx.Client
    def handle(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(500, json={'error': {'code': 'api_error', 'message': 'Internal error encountered.'}})
        return httpx.Response(200, json={'output_video': {'data': base64.b64encode(b'clip').decode()},
            'usage': {'total_input_tokens': 100, 'total_thought_tokens': 5,
                      'output_tokens_by_modality': [{'modality': 'video', 'tokens': 9000}]}})
    monkeypatch.setattr(httpx, 'Client', lambda **kw: original_client(**kw, transport=httpx.MockTransport(handle)))
    monkeypatch.setenv('GEMINI_API_KEY', 'test-no-network')
    monkeypatch.setattr(worker.time, 'sleep', lambda _: None)
    with costs.session(18, 'video-retry'):
        assert worker._run_video('approved line', image=b'face')[0] == b'clip'
    rows = [r for r in events() if r[0] == 'video']
    assert len(rows) == 2
    assert rows[0][2]['state'] == 'uncertain'
    assert rows[0][2]['basis'] == 'unknown'
    assert rows[1][1] > 0
    assert [r[2]['retry'] for r in rows] == [0, 1]
