"""Read-only snapshot replay: legacy versus parallel two-chart Flash, no chat billing writes.

python benchmark_relational_context.py SNAPSHOT OUTPUT_DIR legacy|parallel
Snapshots contain private chart data; keep outputs outside the repository.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import time
from dotenv import load_dotenv

MODEL = 'models/gemini-3-flash-preview'


async def main():
    load_dotenv(Path(__file__).parent / '.env')
    snapshot = json.loads(Path(sys.argv[1]).read_text())
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True); out.chmod(0o700)
    variant = sys.argv[3]
    os.environ['ASTRO_PARALLEL_CHAT'] = '0'
    os.environ['ASTRO_PARALLEL_RELATIONAL_CHAT'] = '0'
    os.environ['ASTRO_PARALLEL_CRITICAL_TIMEOUT_S'] = '120'
    os.environ['ASTRO_PARALLEL_BRANCH_TIMEOUT_S'] = '120'
    os.environ['ASTRO_PARALLEL_CHAT_CONTEXT_CACHE'] = '1'
    os.environ['PGOPTIONS'] = '-c default_transaction_read_only=on'
    from utils import admin_settings as settings
    settings.get_gemini_chat_model = lambda: MODEL
    settings.get_gemini_premium_model = lambda: MODEL
    settings.get_gemini_relational_model = lambda: MODEL
    settings.get_chat_llm_provider = lambda: 'gemini'
    settings.get_chat_llm_provider_premium = lambda: 'gemini'
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    from ai.parallel_chat import relational_orchestrator as pipeline
    from ai.parallel_chat.relational_payloads import build_relational_evidence_spine
    from ai.parallel_chat.fact_authority import calculated_fact_authority
    calls, cache_events = [], []

    def dump(name, value):
        (out / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str))

    dump('manifest', {'variant': variant, 'model': MODEL, 'question': snapshot['question'],
                     'answer_id': snapshot['answer_id'], 'snapshot_note': snapshot['snapshot_note']})
    dump('calculated_facts', {p: calculated_fact_authority(snapshot['context'][p]) for p in ('native', 'partner')})
    dump('relational_evidence', build_relational_evidence_spine(snapshot['context'], snapshot['question']))
    analyzer = GeminiChatAnalyzer()
    original_generate = analyzer.generate_text_from_prompt
    original_cache = pipeline._create_gemini_parallel_cache
    original_delete = pipeline._delete_parallel_cache
    original_branch = pipeline._run_branch_json

    async def generate(prompt, **kwargs):
        index = len(calls)
        row = {'tag': kwargs.get('llm_log_tag'), 'prompt_chars': len(prompt), 'model': kwargs.get('model_name_override')}
        calls.append(row); dump(f'call_{index}_input', {'prompt': prompt})
        start = time.monotonic()
        result = await original_generate(prompt, **kwargs)
        row.update(elapsed_s=time.monotonic()-start, success=result.get('success'), usage=result.get('token_usage'))
        dump(f'call_{index}_result', result); dump('calls', calls)
        return result

    async def cache(**kwargs):
        dump('shared_context', kwargs['cache_payload'])
        result = await original_cache(**kwargs)
        resource = result[0]
        measured = int(getattr(getattr(resource, 'usage_metadata', None), 'total_token_count', 0) or 0)
        cache_events.append({'created_monotonic': time.monotonic(), 'active': bool(result[1]),
                             'estimated_setup_tokens': result[3], 'measured_setup_tokens': measured})
        dump('cache', cache_events)
        return result

    async def delete(resource, **kwargs):
        await original_delete(resource, **kwargs)
        if cache_events:
            cache_events[-1]['lifetime_seconds'] = time.monotonic()-cache_events[-1]['created_monotonic']
            dump('cache', cache_events)

    async def branch(analyzer, static, payload, premium, label, **kwargs):
        dump('branch_'+label, {'instructions': static, 'payload': payload})
        return await original_branch(analyzer, static, payload, premium, label, **kwargs)

    analyzer.generate_text_from_prompt = generate
    pipeline._create_gemini_parallel_cache = cache
    pipeline._delete_parallel_cache = delete
    pipeline._run_branch_json = branch
    start = time.time()
    if variant == 'parallel':
        result = await pipeline.run_parallel_relational_chat_pipeline(analyzer,
            user_question=snapshot['question'], astrological_context=snapshot['context'],
            conversation_history=snapshot['history'], language='english', response_style='technical',
            user_context=None, premium_analysis=True, mode='birth', total_request_start=start)
    else:
        original_prompt = analyzer._create_chat_prompt
        def prompt(*args, **kwargs):
            text = original_prompt(*args, **kwargs); dump('call_0_input', {'prompt': text}); return text
        analyzer._create_chat_prompt = prompt
        result = await analyzer.generate_chat_response(snapshot['question'], snapshot['context'],
            conversation_history=snapshot['history'], premium_analysis=True, response_style='technical',
            language='english', user_id=152)
        calls.append({'tag':'legacy_flash', 'model':MODEL, 'success':result.get('success'),
                      'usage':result.get('token_usage'), 'elapsed_s':time.time()-start})
        dump('calls', calls); dump('call_0_result', result)
    dump('answer', result)
    dump('run', {'elapsed_s':time.time()-start, 'success': result.get('success'), 'model_calls':len(calls)})
    print(json.dumps({'variant':variant,'id':snapshot['answer_id'],'success':result.get('success'),'calls':len(calls)}))


if __name__ == '__main__':
    asyncio.run(main())
