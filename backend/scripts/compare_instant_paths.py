"""Live model timing comparison on a fictional chart; no user history or billing.

From backend: python scripts/compare_instant_paths.py --path both --output /tmp/instant-comparison.json
"""
import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
logging.getLogger().setLevel(logging.ERROR)
BIRTH = {'name':'Synthetic QA', 'date':'1990-01-01', 'time':'12:00:00',
         'latitude':28.6139, 'longitude':77.209, 'timezone':'UTC+5:30', 'place':'Delhi'}


async def compare(args):
    from chat.calculator_first import generate_calculator_first_response, LazyCalculators
    from utils.admin_settings import get_verified_chat_model
    import os
    model = os.getenv('INSTANT_CHAT_AGENT_MODEL') or get_verified_chat_model()
    context = {'client_now_iso':datetime.now(timezone.utc).isoformat(), 'timezone_name':'Asia/Kolkata'}
    results = []
    for path in (['calculator_first','baseline'] if args.path == 'both' else [args.path]):
        started = time.perf_counter()
        milestones = {}
        def progress(_trace): milestones.setdefault('first_progress_seconds', round(time.perf_counter()-started,3))
        def answer(_delta,_full): milestones.setdefault('first_answer_seconds', round(time.perf_counter()-started,3))
        try:
            if path == 'calculator_first':
                result = await generate_calculator_first_response(question=args.question,birth_data=BIRTH,history=[],
                    language='english',response_style='simple',query_context=context,model_name=model,
                    calculation_callback=progress,stream_callback=answer)
            else:
                from ai.intent_router import IntentRouter
                from ai.gemini_chat_analyzer import GeminiChatAnalyzer
                from chat.instant_chat_pipeline import generate_instant_chat_response
                intent = await IntentRouter().classify_instant_intent(args.question,[],language='english',force_ready=True,query_context=context)
                milestones['classification_seconds'] = round(time.perf_counter()-started,3)
                result = await generate_instant_chat_response(GeminiChatAnalyzer(),question=args.question,birth_data=BIRTH,
                    intent=intent,history=[],language='english',instant_conversation=True,
                    verified_calculation_callback=progress,stream_callback=answer)
            results.append({'path':path,'success':bool(result.get('success')),
                'wall_seconds':round(time.perf_counter()-started,3),**milestones,
                'model':result.get('chat_llm_model'),'token_usage':result.get('token_usage'),
                'experiment_metrics':result.get('experiment_metrics'),
                'answer':result.get('response'),
                'calculator_events':[{'calculator':e.get('calculator'),'success':e.get('success')}
                    for e in (result.get('information_rounds') or {}).get('events',[]) if e.get('kind')=='calculation']})
        except Exception as exc:
            # Provider errors can include credential-bearing URLs. Keep their type only.
            results.append({'path':path,'success':False,'wall_seconds':round(time.perf_counter()-started,3),'error_type':type(exc).__name__})
    calculators=LazyCalculators(BIRTH,context)
    chart=calculators.calculate('parashari.natal_foundation')['facts']['chart']
    dashas=calculators.calculate('parashari.dasha_timing')['facts']
    output={'question':args.question,'fictional_birth_data':BIRTH,'query_context':context,
        'reference_facts':{'Moon':chart['planets']['Moon'],'mahadasha':dashas['mahadasha']},
        'comparison':results,'accuracy_note':'These are sample answers and deterministic reference facts, not an astrological accuracy score.'}
    destination=Path(args.output).resolve();destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(output,ensure_ascii=False,indent=2,default=str))
    print(json.dumps({'output':str(destination),'results':[
        {key:value for key,value in row.items() if key not in {'answer','calculator_events','token_usage'}} for row in results]},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--path',choices=['calculator_first','baseline','both'],default='both')
    parser.add_argument('--question',default='Which sign and house is my Moon in, and what is my current Mahadasha?')
    parser.add_argument('--output',default='/tmp/instant-path-comparison.json')
    asyncio.run(compare(parser.parse_args()))
