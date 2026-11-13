"""Run one real Standard pipeline and capture context sizes without chat billing writes."""
import asyncio
import csv
import json
import os
from pathlib import Path
import time

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

OUT = Path(os.getenv('CONTEXT_BENCHMARK_OUT', '/tmp/astroroshni-standard-context-baseline'))
OUT.mkdir(parents=True, exist_ok=True)
os.chmod(OUT, 0o700)
ROWS = []


def dump(name, value):
    (OUT / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def measure(stage, value, path='$'):
    encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'), default=str)
    ROWS.append({'stage': stage, 'path': path, 'type': type(value).__name__,
                 'chars': len(encoded), 'utf8_bytes': len(encoded.encode()),
                 'items': len(value) if isinstance(value, (dict, list)) else ''})
    if isinstance(value, dict):
        for key, child in value.items():
            measure(stage, child, f'{path}.{key}')
    elif isinstance(value, list):
        for i, child in enumerate(value):
            measure(stage, child, f'{path}[{i}]')


async def main():
    from partner_profile.routes import _load_birth_data, _calculate_chart
    from ai.intent_router import IntentRouter
    from chat.chat_context_builder import ChatContextBuilder
    from chat_history.routes import _requested_period_from_intent
    from ai.gemini_chat_analyzer import GeminiChatAnalyzer
    from ai.parallel_chat import orchestrator as o

    question = os.getenv('CONTEXT_BENCHMARK_QUESTION', 'What career fields and work roles suit me best according to my birth chart?')
    chart_id = int(os.getenv('CONTEXT_BENCHMARK_CHART_ID', '10309'))
    user_id = int(os.getenv('CONTEXT_BENCHMARK_USER_ID', '18'))
    replay = os.getenv('CONTEXT_BENCHMARK_REPLAY')
    birth = _load_birth_data(user_id, chart_id)
    intent = (json.loads((Path(replay) / 'intent.json').read_text()) if replay else
              await IntentRouter().classify_intent(question, d1_chart=_calculate_chart(birth)))
    dump('intent', intent)
    if intent.get('status') != 'READY':
        raise RuntimeError('Router did not return READY: ' + str(intent.get('status')))
    ctx = (json.loads((Path(replay) / 'builder.json').read_text()) if replay else
           ChatContextBuilder().build_complete_context(
               birth, question, requested_period=_requested_period_from_intent(intent), intent_result=intent))
    ctx['analysis_type'] = 'birth'
    # Replay the exact recorded evidence and router decision for a controlled
    # context experiment, avoiding date/router drift between comparisons.
    replay = os.getenv('CONTEXT_BENCHMARK_REPLAY')
    if replay:
        ctx = json.loads((Path(replay) / 'builder.json').read_text())
        intent = ctx['intent']
        dump('intent', intent)
    measure('builder', ctx)
    dump('builder', ctx)
    original_branch = o._run_branch_json
    original_cache = o._create_gemini_parallel_cache
    calls = []

    async def branch(analyzer, static_instruction, payload, premium_analysis, branch_label, **kwargs):
        measure(branch_label, payload)
        dump('branch_' + branch_label, {'instructions': static_instruction, 'payload': payload,
             'runtime': {k: v for k, v in kwargs.items() if k != 'model_override'}})
        return await original_branch(analyzer, static_instruction, payload, premium_analysis, branch_label, **kwargs)

    async def cache(**kwargs):
        label = kwargs['cache_label']
        measure(label, kwargs['cache_payload'])
        dump(label, kwargs['cache_payload'])
        result = await original_cache(**kwargs)
        dump(label + '_status', {'active': bool(result[1]), 'setup_chars': result[2], 'setup_tokens': result[3]})
        return result

    o._run_branch_json = branch
    o._create_gemini_parallel_cache = cache
    analyzer = GeminiChatAnalyzer()
    original_generate = analyzer.generate_text_from_prompt

    async def generate(prompt, **kwargs):
        if os.getenv('CONTEXT_BENCHMARK_TIMEOUT_S'):
            kwargs['request_timeout_s'] = float(os.environ['CONTEXT_BENCHMARK_TIMEOUT_S'])
        tag = kwargs.get('llm_log_tag') or 'untagged'
        index = len(calls)
        row = {'tag': tag, 'prompt_chars': len(prompt), 'prompt_utf8_bytes': len(prompt.encode()),
               'model': kwargs.get('model_name_override'), 'cached': bool(kwargs.get('model_override')),
               'use_gemini_rest': kwargs.get('use_gemini_rest', False),
               'thinking_level': kwargs.get('gemini_thinking_level')}
        calls.append(row)
        dump(f'call_{index}_{tag}_input', {'prompt': prompt})
        started = time.monotonic()
        try:
            result = await original_generate(prompt, **kwargs)
            row['elapsed_s'] = round(time.monotonic() - started, 2)
            row['metrics'] = {k: v for k, v in result.items() if k not in ('response',)}
            dump(f'call_{index}_{tag}_result', result)
            return result
        finally:
            dump('calls', calls)

    analyzer.generate_text_from_prompt = generate
    try:
        result = await analyzer.generate_chat_response(question, ctx, conversation_history=[],
            premium_analysis=False, user_id=user_id, response_style='technical')
        dump('answer', result)
    finally:
        with (OUT / 'object_sizes.csv').open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(ROWS[0]))
            writer.writeheader()
            writer.writerows(ROWS)
        dump('manifest', {'question': question, 'chart_id': chart_id, 'tier': 'standard',
             'history': [], 'flags': {k: os.getenv(k) for k in ('ASTRO_PARALLEL_CHAT', 'ASTRO_PARALLEL_AGENT_CONTEXT')},
             'root_sizes': [r for r in ROWS if r['path'] == '$']})
        print('BENCHMARK_OUTPUT', OUT, flush=True)


if __name__ == '__main__':
    asyncio.run(main())
