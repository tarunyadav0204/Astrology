"""Local-only timing probe: real router/calculators/LLM, fictional birth chart.

Run from backend: .venv/bin/python scripts/instant_chat_timing_probe.py
Open the CRA development app with ?instantChatProbe=1. No user account, billing,
production chat records, or real birth details are used. Never mount in main.py.
"""
from __future__ import annotations
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ai.intent_router import IntentRouter
from ai.gemini_chat_analyzer import GeminiChatAnalyzer
from calculators.chart_calculator import ChartCalculator
from chat.instant_chat_pipeline import generate_instant_chat_response
from scripts.evaluate_instant_chat_v2 import SYNTHETIC_QA_CHART
from utils.response_transport import visible_instant_stream_text

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3001', 'http://127.0.0.1:3001'], allow_methods=['GET'], allow_headers=['*'])
chart = ChartCalculator({}).calculate_chart(SimpleNamespace(**SYNTHETIC_QA_CHART))
last_trace = {}

@app.get('/fixture')
async def fixture():
    return {'name': 'Synthetic QA', 'chart': chart}

@app.get('/trace')
async def trace():
    return last_trace

@app.get('/stream')
async def stream(question: str = 'How is my career looking over the next six months?'):
    async def events():
        global last_trace
        started = time.perf_counter()
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()
        timeline = []
        def send(kind, **data):
            event = {'type': kind, 'seconds': round(time.perf_counter() - started, 3), **data}
            timeline.append({key:value for key,value in event.items() if key not in {'content','preview','result'}})
            loop.call_soon_threadsafe(queue.put_nowait, event)
        def preview(value):
            send('preview', preview=value)
            return True
        def chunk(delta, full):
            visible = visible_instant_stream_text(full)
            if visible:
                send('content_delta', content=visible, chars=len(visible))
        async def run():
            global last_trace
            try:
                send('started')
                intent = await IntentRouter().classify_instant_intent(question, [], language='english', force_ready=True)
                send('intent_ready', language=intent.get('response_language'), script=intent.get('response_script'))
                result = await generate_instant_chat_response(GeminiChatAnalyzer(), question=question,
                    birth_data=SYNTHETIC_QA_CHART, intent=intent, history=[], language='english',
                    preview_callback=preview, stream_callback=chunk)
                send('completed', content=result.get('response') or '', preview=result.get('instant_preview'), success=result.get('success'))
                last_trace = {'question':question,'events':timeline,'timing':result.get('timing'),
                              'answer':result.get('response'), 'preview':result.get('instant_preview')}
            except Exception as exc:
                # Provider exceptions can contain credential-bearing URLs.
                send('error', error=type(exc).__name__)
                last_trace = {'question':question,'events':timeline,'error':type(exc).__name__}
        task = asyncio.create_task(run())
        try:
            while True:
                item = await queue.get()
                yield 'data: ' + json.dumps(item, ensure_ascii=False, default=str) + '\n\n'
                if item['type'] in {'completed','error'}:
                    break
        finally:
            await task
    return StreamingResponse(events(), media_type='text/event-stream', headers={'Cache-Control':'no-cache'})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8767, log_level='warning')
